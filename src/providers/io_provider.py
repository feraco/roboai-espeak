import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Dict, Optional

from .singleton import singleton


@dataclass
class Input:
    """
    A dataclass representing an input with an optional timestamp.

    Parameters
    ----------
    input : str
        The input value.
    timestamp : float, optional
        The timestamp associated with the input (default is None).
    """

    input: str
    timestamp: Optional[float] = None


@singleton
class IOProvider:
    """
    A thread-safe singleton class for managing inputs, timestamps, and LLM-related data.

    This class provides synchronized access to input storage and various timing metrics
    using thread locks for safe concurrent access.
    """

    def __init__(self):
        """
        Initialize the IOProvider with thread lock and empty storage.
        """
        self._lock: threading.Lock = threading.Lock()

        self._inputs: Dict[str, str] = {}
        self._input_timestamps: Dict[str, float] = {}

        self._fuser_system_prompt: Optional[str] = None
        self._fuser_inputs: Optional[str] = None
        self._fuser_available_actions: Optional[str] = None
        self._fuser_start_time: Optional[float] = None
        self._fuser_end_time: Optional[float] = None

        self._llm_prompt: Optional[str] = None
        self._llm_start_time: Optional[float] = None
        self._llm_end_time: Optional[float] = None

        self._mode_transition_input: Optional[str] = None

        # Additional variables storage
        self._variables: Dict[str, Any] = {}

    @property
    def inputs(self) -> Dict[str, Input]:
        """
        Get all inputs with their timestamps.

        Returns
        -------
        Dict[str, Input]
            Dictionary mapping input keys to Input objects.
        """
        with self._lock:
            result = {}
            for name, value in self._inputs.items():
                timestamp = self._input_timestamps.get(name)
                if timestamp is not None:
                    result[name] = Input(input=value, timestamp=timestamp)
                else:
                    result[name] = Input(input=value)
            return result

    def add_input(self, key: str, value: str, timestamp: Optional[float]) -> None:
        """
        Add an input with optional timestamp.

        Parameters
        ----------
        key : str
            The input identifier.
        value : str
            The input value.
        timestamp : float, optional
            The timestamp for the input.
        """
        with self._lock:
            self._inputs[key] = value
            if timestamp is not None:
                self._input_timestamps[key] = timestamp
            else:
                self._input_timestamps[key] = time.time()

    def remove_input(self, key: str) -> None:
        """
        Remove an input and its timestamp.

        Parameters
        ----------
        key : str
            The input identifier to remove.
        """
        with self._lock:
            self._inputs.pop(key, None)
            self._input_timestamps.pop(key, None)

    def add_input_timestamp(self, key: str, timestamp: float) -> None:
        """
        Add a timestamp for an existing input.

        Parameters
        ----------
        key : str
            The input identifier.
        timestamp : float
            The timestamp to add.
        """
        with self._lock:
            self._input_timestamps[key] = timestamp

    def get_input_timestamp(self, key: str) -> Optional[float]:
        """
        Get the timestamp for a specific input.

        Parameters
        ----------
        key : str
            The input identifier.

        Returns
        -------
        float or None
            The timestamp if it exists, None otherwise.
        """
        with self._lock:
            return self._input_timestamps.get(key)

    @property
    def fuser_system_prompt(self) -> Optional[str]:
        """
        Get the fuser system prompt.
        """
        with self._lock:
            return self._fuser_system_prompt

    @fuser_system_prompt.setter
    def fuser_system_prompt(self, value: Optional[str]) -> None:
        """
        Set the fuser system prompt.
        """
        with self._lock:
            self._fuser_system_prompt = value

    def set_fuser_system_prompt(self, value: Optional[str]) -> None:
        """
        Alternative method to set fuser system prompt.
        """
        with self._lock:
            self._fuser_system_prompt = value

    @property
    def fuser_inputs(self) -> Optional[str]:
        """
        Get the fuser inputs.
        """
        with self._lock:
            return self._fuser_inputs

    @fuser_inputs.setter
    def fuser_inputs(self, value: Optional[str]) -> None:
        """
        Set the fuser inputs.
        """
        with self._lock:
            self._fuser_inputs = value

    def set_fuser_inputs(self, value: Optional[str]) -> None:
        """
        Alternative method to set fuser inputs.
        """
        with self._lock:
            self._fuser_inputs = value

    @property
    def fuser_available_actions(self) -> Optional[str]:
        """
        Get the fuser available actions.
        """
        with self._lock:
            return self._fuser_available_actions

    @fuser_available_actions.setter
    def fuser_available_actions(self, value: Optional[str]) -> None:
        """
        set the fuser available actions.
        """
        with self._lock:
            self._fuser_available_actions = value

    def set_fuser_available_actions(self, value: Optional[str]) -> None:
        """
        Alternative method to set fuser available actions.
        """
        with self._lock:
            self._fuser_available_actions = value

    @property
    def fuser_start_time(self) -> Optional[float]:
        """
        Get the fuser start time.
        """
        with self._lock:
            return self._fuser_start_time

    @fuser_start_time.setter
    def fuser_start_time(self, value: Optional[float]) -> None:
        """
        Set the fuser start time.
        """
        with self._lock:
            self._fuser_start_time = value

    def set_fuser_start_time(self, value: Optional[float]) -> None:
        """
        Alternative method to set fuser start time.
        """
        with self._lock:
            self._fuser_start_time = value

    @property
    def fuser_end_time(self) -> Optional[float]:
        """
        Get the fuser end time.
        """
        with self._lock:
            return self._fuser_end_time

    @fuser_end_time.setter
    def fuser_end_time(self, value: Optional[float]) -> None:
        """
        Set the fuser end time.
        """
        with self._lock:
            self._fuser_end_time = value

    def set_fuser_end_time(self, value: Optional[float]) -> None:
        """
        Alternative method to set fuser end time.
        """
        with self._lock:
            self._fuser_end_time = value

    @property
    def llm_prompt(self) -> Optional[str]:
        """
        Get the LLM prompt.
        """
        with self._lock:
            return self._llm_prompt

    @llm_prompt.setter
    def llm_prompt(self, value: Optional[str]) -> None:
        """
        Set the LLM prompt.
        """
        with self._lock:
            self._llm_prompt = value

    def set_llm_prompt(self, value: Optional[str]) -> None:
        """
        Alternative method to set LLM prompt.
        """
        with self._lock:
            self._llm_prompt = value

    def clear_llm_prompt(self) -> None:
        """C
        lear the LLM prompt.
        """
        with self._lock:
            self._llm_prompt = None

    @property
    def llm_start_time(self) -> Optional[float]:
        """
        Get the LLM processing start time.
        """
        with self._lock:
            return self._llm_start_time

    @llm_start_time.setter
    def llm_start_time(self, value: Optional[float]) -> None:
        """
        Set the LLM processing start time.
        """
        with self._lock:
            self._llm_start_time = value

    def set_llm_start_time(self, value: Optional[float]) -> None:
        """
        Alternative method to set LLM start time.
        """
        with self._lock:
            self._llm_start_time = value

    @property
    def llm_end_time(self) -> Optional[float]:
        """
        Get the LLM processing end time.
        """
        with self._lock:
            return self._llm_end_time

    @llm_end_time.setter
    def llm_end_time(self, value: Optional[float]) -> None:
        """
        Set the LLM processing end time.
        """
        with self._lock:
            self._llm_end_time = value

    def add_dynamic_variable(self, key: str, value: Any) -> None:
        """
        Add a dynamic variable to the provider.

        Parameters
        ----------
        key : str
            The variable key.
        value : Any
            The variable value.
        """
        with self._lock:
            self._variables[key] = value

    def get_dynamic_variable(self, key: str) -> Any:
        """
        Get a dynamic variable from the provider.

        Parameters
        ----------
        key : str
            The variable key.

        Returns
        -------
        Any
            The variable value.
        """
        with self._lock:
            return self._variables.get(key)

    def add_mode_transition_input(self, input_text: str) -> None:
        """
        Add input text that triggered a mode transition.

        Parameters
        ----------
        input_text : str
            The input text that caused the mode transition.
        """
        with self._lock:
            if self._mode_transition_input is None:
                self._mode_transition_input = input_text
            else:
                self._mode_transition_input = (
                    self._mode_transition_input + " " + input_text
                )

    @contextmanager
    def mode_transition_input(self):
        """
        Context manager for providing mode transition input that automatically resets after use.

        Yields
        ------
        Optional[str]
            The current mode transition input text.
        """
        try:
            with self._lock:
                current_input = self._mode_transition_input
            yield current_input
        finally:
            self.delete_mode_transition_input()

    def get_mode_transition_input(self) -> Optional[str]:
        """
        Get the stored mode transition input text.

        Returns
        -------
        Optional[str]
            The stored mode transition input text, or None if not set.
        """
        with self._lock:
            return self._mode_transition_input

    def delete_mode_transition_input(self) -> None:
        """
        Clear the stored mode transition input text.
        """
        with self._lock:
            self._mode_transition_input = None

    def add_output(self, key: str, value: str, timestamp: Optional[float] = None) -> None:
        """
        Add an output record for tracking purposes.
        
        This method is provided for compatibility but currently just logs the output.
        It can be extended in the future to store outputs for analytics or debugging.

        Parameters
        ----------
        key : str
            The output identifier (e.g., "TTS", "Action")
        value : str
            The output value
        timestamp : float, optional
            The timestamp for the output (defaults to current time)
        """
        if timestamp is None:
            timestamp = time.time()
        
        # For now, just log the output. This can be extended to store outputs if needed
        # logging.debug(f"Output recorded - {key}: {value[:50]}{'...' if len(value) > 50 else ''}")
        pass
