import logging
import os
import time
import typing as T

import openai
from pydantic import BaseModel

from llm import LLM, LLMConfig
from llm.function_schemas import convert_function_calls_to_actions
from llm.output_model import CortexOutputModel
from providers.llm_history_manager import LLMHistoryManager

R = T.TypeVar("R", bound=BaseModel)


class GeminiLLM(LLM[R]):
    """
    Google Gemini LLM implementation using OpenAI-compatible API.

    Handles authentication and response parsing for Gemini endpoints.

    Parameters
    ----------
    config : LLMConfig
        Configuration object containing API settings. If not provided, defaults
        will be used.
    available_actions : list[AgentAction], optional
        List of available actions for function call generation. If provided.
    """

    def __init__(
        self,
        config: LLMConfig = LLMConfig(),
        available_actions: T.Optional[T.List] = None,
    ):
        """
        Initialize the DeepSeek LLM instance.
        """
        super().__init__(config, available_actions)

        # Get API key from environment if not provided in config
        api_key = config.api_key or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("Google API key not found. Set GOOGLE_API_KEY environment variable or provide api_key in config.")
        
        if not config.model:
            self._config.model = "gemini-2.5-flash"

        # Note: This would need to be updated to use Google's actual Gemini API
        # For now, keeping the OpenAI-compatible interface but with direct Google endpoint
        self._client = openai.AsyncOpenAI(
            base_url=config.base_url or "https://generativelanguage.googleapis.com/v1beta",
            api_key=api_key,
        )

        # Initialize history manager
        self.history_manager = LLMHistoryManager(self._config, self._client)
        
        # Store system context (set by cortex)
        self._system_context: T.Optional[str] = None
    
    def set_system_context(self, system_context: str) -> None:
        """
        Set the static system context that will be sent as a system message.
        
        Parameters
        ----------
        system_context : str
            The static system prompt, governance, examples, and actions
        """
        self._system_context = system_context
        logging.info("Gemini LLM: System context set (%d chars)", len(system_context))

    @LLMHistoryManager.update_history()
    async def ask(self, prompt: str, messages: T.List[T.Dict[str, str]]) -> R | None:
        """
        Execute LLM query and parse response

        Parameters
        ----------
        prompt : str
            The input prompt to send to the model.
        messages : List[Dict[str, str]]
            List of message dictionaries to send to the model.

        Returns
        -------
        R or None
            Parsed response matching the output_model structure, or None if
            parsing fails.
        """
        try:
            logging.debug(f"Gemini LLM input: {prompt}")
            logging.debug(f"Gemini LLM messages: {messages}")

            self.io_provider.llm_start_time = time.time()
            self.io_provider.set_llm_prompt(prompt)

            formatted_messages = [
                {"role": msg.get("role", "user"), "content": msg.get("content", "")}
                for msg in messages
            ]
            formatted_messages.append({"role": "user", "content": prompt})

            response = await self._client.chat.completions.create(
                model=self._config.model or "gemini-2.0-flash-exp",
                messages=T.cast(T.Any, formatted_messages),
                tools=T.cast(T.Any, self.function_schemas),
                tool_choice="auto",
                timeout=self._config.timeout,
            )

            message = response.choices[0].message
            self.io_provider.llm_end_time = time.time()

            if message.tool_calls:
                logging.info(f"Received {len(message.tool_calls)} function calls")
                logging.info(f"Function calls: {message.tool_calls}")

                function_call_data = [
                    {
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        }
                    }
                    for tc in message.tool_calls
                ]

                actions = convert_function_calls_to_actions(function_call_data)

                result = CortexOutputModel(actions=actions)
                logging.info(f"OpenAI LLM function call output: {result}")
                return T.cast(R, result)

            return None
        except Exception as e:
            logging.error(f"Gemini API error: {e}")
            return None
