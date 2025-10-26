import logging
import time
import typing as T

from actions import describe_action
from inputs.base import Sensor
from providers.io_provider import IOProvider
from runtime.single_mode.config import RuntimeConfig


class Fuser:
    """
    Combines multiple agent inputs into a single formatted prompt.

    Responsible for integrating system prompts, input streams, action descriptions,
    and command prompts into a coherent format for LLM processing.

    Parameters
    ----------
    config : RuntimeConfig
        Runtime configuration containing system prompts and agent actions.

    Attributes
    ----------
    config : RuntimeConfig
        Runtime configuration settings.
    io_provider : IOProvider
        Provider for handling I/O data and timing.
    """

    def __init__(self, config: RuntimeConfig):
        """
        Initialize the Fuser with runtime configuration.

        Parameters
        ----------
        config : RuntimeConfig
            Runtime configuration object.
        """
        self.config = config
        self.io_provider = IOProvider()
        
        # Pre-build static system context (only done once)
        self._system_context = self._build_system_context()
    
    def _build_system_context(self) -> str:
        """
        Build the static system context that doesn't change between requests.
        This includes the base prompt, governance, examples, and action descriptions.
        
        Returns
        -------
        str
            The static system context string
        """
        system_prompt = "BASIC CONTEXT:\n" + self.config.system_prompt_base + "\n"
        system_prompt += "\nLAWS:\n" + self.config.system_governance
        
        if self.config.system_prompt_examples:
            system_prompt += "\n\nEXAMPLES:\n" + self.config.system_prompt_examples
        
        # Add action descriptions
        actions_fused = ""
        for action in self.config.agent_actions:
            desc = describe_action(
                action.name, action.llm_label, action.exclude_from_prompt
            )
            if desc:
                actions_fused += desc + "\n\n"
        
        if actions_fused:
            system_prompt += f"\n\nAVAILABLE ACTIONS:\n{actions_fused}"
        
        return system_prompt
    
    def get_system_context(self) -> str:
        """
        Get the pre-built system context.
        
        Returns
        -------
        str
            The static system context
        """
        return self._system_context

    def fuse(self, inputs: list[Sensor], finished_promises: list[T.Any]) -> T.Optional[str]:
        """
        Combine only the dynamic inputs into a user prompt.
        
        The static system context (base prompt, governance, examples, actions) 
        is now separated and should be sent as a system message by the LLM.

        Parameters
        ----------
        inputs : list[Sensor]
            List of agent input objects containing latest input buffers.
        finished_promises : list[Any]
            List of completed promises from previous actions.

        Returns
        -------
        str or None
            User prompt containing only the dynamic inputs, or None if no actionable input
        """
        # Record the timestamp of the input
        self.io_provider.fuser_start_time = time.time()

        input_strings = [input.formatted_latest_buffer() for input in inputs]
        inputs_fused = " ".join([s for s in input_strings if s is not None])
        
        # Check for voice vs vision input separately
        has_voice_input = False
        has_vision_input = False
        
        for input_str in input_strings:
            if input_str and "Voice" in input_str and input_str.strip():
                has_voice_input = True
            if input_str and "Vision" in input_str and input_str.strip():
                has_vision_input = True
        
        if not inputs_fused.strip():
            logging.warning(f"Fuser: No input detected in buffers: {input_strings}")
            logging.info("=== INPUT STATUS ===\nNo input detected")
            inputs_fused = "<no input detected>"
        else:
            logging.info("=== INPUT STATUS ===\nVoice: %s | Vision: %s", 
                        "Yes" if has_voice_input else "No",
                        "Yes" if has_vision_input else "No")
            logging.info("=== INPUTS ===\n%s", inputs_fused.strip())

        # Check if we have blockchain-based governance override
        if "Universal Laws" in inputs_fused:
            logging.info("Universal Laws detected in input - blockchain governance active")

        # Create engaging prompts based on input type
        if not has_voice_input and has_vision_input:
            # Vision only - encourage describing what's seen like a curious receptionist
            question_prompt = """No one is speaking to you right now, but you can see what's happening.

As a curious and friendly receptionist:
- Describe what you observe in the waiting room
- Welcome anyone you see arriving
- Comment on interesting details you notice
- Offer help if someone looks like they need it
- Keep it brief (1-2 sentences) and welcoming

What do you see? Actions:"""
        elif has_voice_input:
            # Voice input - prioritize answering their question
            question_prompt = "Someone is speaking to you. Focus on answering their question professionally and helpfully. Actions:"
        else:
            # No input at all - return None to skip this cycle
            return None
        
        user_prompt = f"CURRENT INPUTS:\n{inputs_fused}\n\n{question_prompt}"

        logging.info("=== USER PROMPT (Dynamic Only) ===\n%s", user_prompt)
        logging.debug("=== SYSTEM CONTEXT (Static, sent separately) ===\n%s", self._system_context)

        # Record for IO provider
        self.io_provider.set_fuser_system_prompt(self._system_context)
        self.io_provider.set_fuser_inputs(inputs_fused)

        # Record the timestamp of the output
        self.io_provider.fuser_end_time = time.time()

        return user_prompt
