import asyncio
import logging

from actions.orchestrator import ActionOrchestrator
from backgrounds.orchestrator import BackgroundOrchestrator
from fuser import Fuser
from inputs.orchestrator import InputOrchestrator
from providers.io_provider import IOProvider
from providers.sleep_ticker_provider import SleepTickerProvider
from runtime.single_mode.config import RuntimeConfig
from simulators.orchestrator import SimulatorOrchestrator


class CortexRuntime:
    """
    The main entry point for the OM1 agent runtime environment.

    The CortexRuntime orchestrates communication between memory, fuser,
    actions, and manages inputs/outputs. It controls the agent's execution
    cycle and coordinates all major subsystems.

    Parameters
    ----------
    config : RuntimeConfig
        Configuration object containing all runtime settings including
        agent inputs, cortex LLM settings, and execution parameters.
    """

    config: RuntimeConfig
    fuser: Fuser
    action_orchestrator: ActionOrchestrator
    simulator_orchestrator: SimulatorOrchestrator
    background_orchestrator: BackgroundOrchestrator
    sleep_ticker_provider: SleepTickerProvider

    def __init__(self, config: RuntimeConfig):
        """
        Initialize the CortexRuntime with provided configuration.

        Parameters
        ----------
        config : RuntimeConfig
            Configuration object for the runtime.
        """
        self.config = config

        logging.debug(f"Cortex runtime config: {config}")
        self.fuser = Fuser(config)
        self.action_orchestrator = ActionOrchestrator(config)
        self.simulator_orchestrator = SimulatorOrchestrator(config)
        self.background_orchestrator = BackgroundOrchestrator(config)
        self.sleep_ticker_provider = SleepTickerProvider()
        self.io_provider = IOProvider()
        
        # Set static system context on the LLM (only done once at initialization)
        if hasattr(config.cortex_llm, 'set_system_context'):
            system_context = self.fuser.get_system_context()
            config.cortex_llm.set_system_context(system_context)
            logging.info("System context set on LLM (%d chars) - will be cached/reused", len(system_context))

    async def run(self) -> None:
        """
        Start the runtime's main execution loop.

        This method initializes input listeners and begins the cortex
        processing loop, running them concurrently.

        Returns
        -------
        None
        """
        input_listener_task = await self._start_input_listeners()
        cortex_loop_task = asyncio.create_task(self._run_cortex_loop())

        simulator_start = self._start_simulator_task()
        action_start = self._start_action_task()
        background_start = self._start_background_task()

        await asyncio.gather(
            input_listener_task,
            cortex_loop_task,
            simulator_start,
            action_start,
            background_start,
        )

    async def _start_input_listeners(self) -> asyncio.Task:
        """
        Initialize and start input listeners.

        Creates an InputOrchestrator for the configured agent inputs
        and starts listening for input events.

        Returns
        -------
        asyncio.Task
            Task handling input listening operations.
        """
        input_orchestrator = InputOrchestrator(self.config.agent_inputs)
        input_listener_task = asyncio.create_task(input_orchestrator.listen())
        return input_listener_task

    async def _start_simulator_task(self) -> asyncio.Future:
        return self.simulator_orchestrator.start()

    async def _start_action_task(self) -> asyncio.Future:
        return self.action_orchestrator.start()

    async def _start_background_task(self) -> asyncio.Future:
        return self.background_orchestrator.start()

    async def _run_cortex_loop(self) -> None:
        """
        Execute the main cortex processing loop.

        Runs continuously, managing the sleep/wake cycle and triggering
        tick operations at the configured frequency.

        Returns
        -------
        None
        """
        while True:
            if not self.sleep_ticker_provider.skip_sleep:
                await self.sleep_ticker_provider.sleep(1 / self.config.hertz)
            await self._tick()
            self.sleep_ticker_provider.skip_sleep = False

    async def _tick(self) -> None:
        """
        Execute a single tick of the cortex processing cycle.
        Enhanced with structured I/O logging for debugging.
        """
        import datetime
        
        # Timestamp for this tick
        tick_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # collect all the latest inputs
        finished_promises, _ = await self.action_orchestrator.flush_promises()

        # Combine those inputs into a suitable prompt
        prompt = self.fuser.fuse(self.config.agent_inputs, finished_promises)
        
        # Skip if fuser returns None (no actionable input)
        if prompt is None:
            return
        
        # Skip if no valid input (don't waste LLM tokens on empty prompts)
        if not prompt or prompt.strip() == "":
            if finished_promises:  # If we had input but fusion failed
                logging.warning(f"{tick_time} | No prompt after fusion. Finished promises: {finished_promises}")
            return
            
        # Check if this is the same as the last prompt to prevent repeats
        last_prompt = self.io_provider.llm_prompt
        if prompt == last_prompt:
            logging.debug(f"{tick_time} | Skipping duplicate prompt")
            return

        # === STRUCTURED INPUT LOGGING ===
        logging.info("=" * 70)
        logging.info(f"{tick_time} | 📥 INPUT CYCLE START")
        logging.info("=" * 70)
        
        # Log each input type separately
        for agent_input in self.config.agent_inputs:
            buffer_content = agent_input.formatted_latest_buffer()
            if buffer_content:
                input_type = agent_input.__class__.__name__
                logging.info(f"{tick_time} | INPUT({input_type}): {buffer_content.strip()}")
        
        # Log the full prompt
        logging.info(f"{tick_time} | INPUT(Combined Prompt):\n{prompt}\n")

        # === LLM PROCESSING ===
        try:
            output = await self.config.cortex_llm.ask(prompt)
            if output is None:
                logging.error(f"{tick_time} | ❌ OUTPUT(LLM): No response from LLM")
                return

            # === STRUCTURED OUTPUT LOGGING ===
            logging.info("=" * 70)
            logging.info(f"{tick_time} | 📤 OUTPUT CYCLE START")
            logging.info("=" * 70)
            logging.info(f"{tick_time} | OUTPUT(LLM): {output}")
            
        except Exception as e:
            logging.error("=" * 70)
            logging.error(f"{tick_time} | ❌ LLM ERROR")
            logging.error("=" * 70)
            logging.error(f"{tick_time} | Error during LLM processing: {e}", exc_info=True)
            return

        # Trigger the simulators
        await self.simulator_orchestrator.promise(output.actions)

        # Filter and sanitize TTS actions
        sanitized_actions = []
        for a in output.actions:
            if a.type == 'speak':
                # Handle both dict (with language) and string (legacy) values
                if isinstance(a.value, dict):
                    sentence = a.value.get('sentence', '')
                    language = a.value.get('language', 'en')
                else:
                    sentence = str(a.value or '')
                    language = 'en'
                
                # Remove NO ACTIONS
                if sentence.strip().upper() == 'NO ACTIONS':
                    logging.debug(f"{tick_time} | Filtered out 'NO ACTIONS' response")
                    continue
                if not sentence.strip():
                    logging.warning(f"{tick_time} | Empty TTS sentence: {a.value}")
                    continue
                    
                logging.info(f"{tick_time} | OUTPUT(TTS): [{language}] {sentence[:100]}...")
            sanitized_actions.append(a)

        # Trigger the actions
        await self.action_orchestrator.promise(sanitized_actions)
        
        logging.info("=" * 70)
        logging.info(f"{tick_time} | ✅ CYCLE COMPLETE")
        logging.info("=" * 70 + "\n")

        # Ensure ASR buffer is cleared after each tick for continuous listening
        from inputs.plugins.local_asr import LocalASRInput
        for agent_input in self.config.agent_inputs:
            if isinstance(agent_input, LocalASRInput):
                agent_input.messages.clear()
                logging.debug(f"{tick_time} | Cleared ASR buffer for {agent_input}")
