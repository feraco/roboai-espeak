import asyncio
import functools
import logging
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, List, Optional, TypeVar, Union

import openai

from llm import LLMConfig

from .io_provider import IOProvider

R = TypeVar("R")


@dataclass
class ChatMessage:
    role: str
    content: str


ACTION_MAP = {
    "emotion": "**** felt: {}.",
    "speak": "**** said: {}",
    "move": "**** performed this motion: {}.",
}


class LLMHistoryManager:
    def __init__(
        self,
        config: LLMConfig,
        client: Union[openai.AsyncClient, openai.OpenAI],
        system_prompt: str = "You are a helpful assistant that summarizes a succession of events and interactions accurately and concisely. You are watching a robot named **** interact with people and the world. Your goal is to help **** remember what the robot felt, saw, and heard, and how the robot responded to those inputs.",
        summary_command: str = "\nConsidering the new information, write an updated summary of the situation for ****. Emphasize information that **** needs to know to respond to people and situations in the best possible and most compelling way.",
    ):
        self.client = client

        # configuration
        self.config = config
        self.agent_name = self.config.agent_name
        self.system_prompt = (
            system_prompt.replace("****", self.agent_name)
            if self.agent_name
            else system_prompt
        )
        self.summary_command = (
            summary_command.replace("****", self.agent_name)
            if self.agent_name
            else summary_command
        )

        # frame index
        self.frame_index = 0

        # task executor
        self._summary_task: Optional[asyncio.Task] = None

        # history buffer
        self.history: List[ChatMessage] = []

        # io provider
        self.io_provider = IOProvider()

    async def summarize_messages(self, messages: List[ChatMessage]) -> ChatMessage:
        """
        Summarize a list of messages using the OpenAI API.
        Returns a new message containing the summary.
        """
        try:
            if not messages:
                logging.warning("No messages to summarize")
                return ChatMessage(role="system", content="No history to summarize")

            logging.debug(f"All raw info: {messages} len{len(messages)}")

            summary_prompt = ""

            if len(messages) == 4:
                # the normal case - previous summary and new data
                # the previous summary
                summary_prompt += f"{messages[0].content}\n"
                # actions - already part of the summary - no need to add
                # summary_prompt += f"{messages[1].content}\n"
                summary_prompt += "\nNow, the following new information has arrived. "
                summary_prompt += f"{messages[2].content}\n"
                summary_prompt += f"{messages[3].content}\n"
            else:
                for msg in messages:
                    summary_prompt += f"{msg.content}\n"

            summary_prompt += self.summary_command

            # insert actual robot name
            summary_prompt = (
                summary_prompt.replace("****", self.agent_name)
                if self.agent_name
                else summary_prompt
            )

            logging.info(f"Information to summarize:\n{summary_prompt}")

            # Set timeout for API call
            timeout = 10.0  # seconds
            response = await asyncio.wait_for(
                self.client.chat.completions.create(  # type: ignore
                    model=self.config.model or "gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": summary_prompt},
                    ],
                ),
                timeout=timeout,
            )

            if not response or not response.choices:
                logging.error("Invalid API response format")
                return ChatMessage(
                    role="system", content="Error: Received invalid response from API"
                )

            summary = response.choices[0].message.content
            return ChatMessage(role="assistant", content=f"Previously, {summary}")

        except asyncio.TimeoutError:
            logging.error(f"API request timed out after {timeout} seconds")
            return ChatMessage(role="system", content="Error: API request timed out")
        except openai.APIError as e:
            logging.error(f"OpenAI API error: {e}")
            return ChatMessage(
                role="system", content=f"Error: API service unavailable: {str(e)}"
            )
        except Exception as e:
            logging.error(f"Error summarizing messages: {type(e).__name__}: {e}")
            return ChatMessage(role="system", content="Error summarizing state")

    async def start_summary_task(self, messages: List[ChatMessage]):
        """
        Start a new task to summarize the messages.
        """
        if not messages:
            logging.warning("No messages to summarize in start_summary_task")
            return

        try:
            if self._summary_task and not self._summary_task.done():
                logging.info("Previous summary task still running")
                return

            messages_copy = messages.copy()
            self._summary_task = asyncio.create_task(
                self.summarize_messages(messages_copy)
            )

            def callback(task):
                try:
                    if task.cancelled():
                        logging.warning("Summary task was cancelled")
                        return

                    summary_message = task.result()
                    if summary_message.role == "assistant":
                        messages.clear()
                        messages.append(summary_message)
                        logging.info("Successfully summarized the state")
                    elif (
                        summary_message.role == "system"
                        and "Error" in summary_message.content
                    ):
                        logging.error(
                            f"Summarization failed: {summary_message.content}"
                        )
                        messages.pop(0) if messages else None
                        messages.pop(0) if messages else None
                    else:
                        logging.warning(f"Unexpected summary result: {summary_message}")
                except asyncio.CancelledError:
                    logging.warning("Summary task callback cancelled")
                except Exception as e:
                    logging.error(
                        f"Error in summary task callback: {type(e).__name__}: {e}"
                    )
                    messages.pop(0) if messages else None
                    messages.pop(0) if messages else None

            self._summary_task.add_done_callback(callback)

        except asyncio.CancelledError:
            logging.warning("Summary task creation cancelled")
        except Exception as e:
            logging.error(f"Error starting summary task: {type(e).__name__}: {e}")
            messages.pop(0) if messages else None
            messages.pop(0) if messages else None

    def get_messages(self) -> List[dict]:
        """
        Get messages in format required by OpenAI API.
        """
        return [{"role": msg.role, "content": msg.content} for msg in self.history]

    @staticmethod
    def update_history():
        def decorator(func: Callable[..., Awaitable[R]]) -> Callable[..., Awaitable[R]]:
            @functools.wraps(func)
            async def wrapper(self: Any, prompt: str, *args, **kwargs) -> R:

                if self._config.history_length == 0:
                    response = await func(self, prompt, [], *args, **kwargs)
                    self.history_manager.frame_index += 1
                    return response

                self.agent_name = self._config.agent_name

                cycle = self.history_manager.frame_index
                logging.debug(f"LLM Tasking cycle debug tracker: {cycle}")

                formatted_inputs = f"{self.agent_name} sensed the following: "
                for input_type, input_info in self.io_provider.inputs.items():
                    logging.debug(f"LLM: {input_type}")
                    logging.debug(f"LLM: {input_info}")
                    formatted_inputs += f"{input_type}. {input_info.input} | "

                # formatted_inputs = f"**** sensed the following: {" | ".join(f"{input_type}: {input_info.input}" for input_type, input_info in self.io_provider.inputs.items())}"

                formatted_inputs = formatted_inputs.replace("..", ".")
                formatted_inputs = formatted_inputs.replace("  ", " ")

                inputs = ChatMessage(role="user", content=formatted_inputs)

                logging.debug(f"Inputs: {inputs}")
                self.history_manager.history.append(inputs)

                messages = self.history_manager.get_messages()
                logging.debug(f"messages:\n{messages}")
                # this advances the frame index
                response = await func(self, prompt, messages, *args, **kwargs)
                logging.debug(f"Response to parse:\n{response}")

                if response is not None:

                    action_message = (
                        "Given that information, **** took these actions: "
                        + (
                            " | ".join(
                                ACTION_MAP[action.type.lower()].format(
                                    action.value if action.value else ""
                                )
                                for action in response.actions  # type: ignore
                                if action.type.lower() in ACTION_MAP
                            )
                        )
                    )

                    action_message = action_message.replace("****", self.agent_name)

                    self.history_manager.history.append(
                        ChatMessage(role="user", content=action_message)
                    )

                    if (
                        self.history_manager.config.history_length > 0
                        and len(self.history_manager.history)
                        > self.history_manager.config.history_length
                    ):
                        await self.history_manager.start_summary_task(
                            self.history_manager.history
                        )

                self.history_manager.frame_index += 1

                return response

            return wrapper

        return decorator
