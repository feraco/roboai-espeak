import logging
import time
import typing as T

import openai
from pydantic import BaseModel

from llm import LLM, LLMConfig
from llm.function_schemas import convert_function_calls_to_actions
from llm.output_model import CortexOutputModel
from providers.llm_history_manager import LLMHistoryManager

R = T.TypeVar("R", bound=BaseModel)


class XAILLM(LLM[R]):
    """
    XAI LLM implementation using OpenAI-compatible API.

    Handles authentication and response parsing for XAI endpoints.

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

        if not config.api_key:
            raise ValueError("config file missing api_key")
        if not config.model:
            self._config.model = "grok-4-latest"

        self._client = openai.AsyncOpenAI(
            base_url=config.base_url or "https://api.openmind.org/api/core/xai",
            api_key=config.api_key,
        )

        # Initialize history manager
        self.history_manager = LLMHistoryManager(self._config, self._client)

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
            logging.debug(f"XAI LLM input: {prompt}")
            logging.debug(f"XAI LLM messages: {messages}")

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
            logging.error(f"XAI API error: {e}")
            return None
