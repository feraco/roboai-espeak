import asyncio
import base64
import logging
import time
from dataclasses import dataclass
from typing import Optional

import aiohttp

try:
    import cv2
    import numpy as np
except ImportError as exc:  # pragma: no cover - optional dependency guard
    raise ImportError(
        "VLMOllamaVision requires OpenCV and NumPy. Please install opencv-python-headless (or opencv-python) and numpy."
    ) from exc

from inputs.base import SensorConfig
from inputs.base.loop import FuserInput
from providers.io_provider import IOProvider


@dataclass
class Message:
    timestamp: float
    message: str


class VLMOllamaVision(FuserInput[np.ndarray]):
    """
    Capture camera frames and ask an Ollama vision model for a short description.
    """

    def __init__(self, config: SensorConfig = SensorConfig()):
        super().__init__(config)

        self.io_provider = IOProvider()
        self.messages: list[Message] = []

        self.base_url = getattr(self.config, "base_url", "http://localhost:11434")
        self.model = getattr(self.config, "model", "llava-llama3")
        self.prompt = getattr(
            self.config,
            "prompt",
            "Describe what the camera sees focusing on the person's clothing or notable items in one friendly sentence.",
        )
        self.poll_interval = float(getattr(self.config, "poll_interval", 2.0))
        self.analysis_interval = float(getattr(self.config, "analysis_interval", 6.0))
        self.timeout = float(getattr(self.config, "timeout", 25.0))
        self.camera_index = int(getattr(self.config, "camera_index", 0))

        self.descriptor_for_LLM = getattr(self.config, "descriptor", "Vision")

        self.cap: Optional[cv2.VideoCapture] = None
        self._ensure_camera()

        self._last_analysis_ts = 0.0

    def _ensure_camera(self) -> None:
        if self.cap is not None:
            return

        cap = cv2.VideoCapture(self.camera_index)
        if not cap.isOpened():
            logging.warning(
                "VLMOllamaVision could not open camera index %s", self.camera_index
            )
            return

        self.cap = cap
        logging.info("VLMOllamaVision attached to camera index %s", self.camera_index)

    async def _poll(self) -> Optional[np.ndarray]:
        await asyncio.sleep(self.poll_interval)

        if self.cap is None:
            self._ensure_camera()
            return None

        ret, frame = self.cap.read()
        if not ret:
            logging.debug("VLMOllamaVision dropped a frame")
            return None

        return frame

    async def _describe_frame(self, frame: np.ndarray) -> Optional[str]:
        ok, buffer = cv2.imencode(".jpg", frame)
        if not ok:
            logging.debug("VLMOllamaVision failed to encode frame")
            return None

        image_bytes = buffer.tobytes()
        image_b64 = base64.b64encode(image_bytes).decode("utf-8")

        payload = {
            "model": self.model,
            "prompt": self.prompt,
            "images": [image_b64],
            "stream": False,
        }

        timeout = aiohttp.ClientTimeout(total=self.timeout)
        url = f"{self.base_url}/api/generate"

        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(url, json=payload) as response:
                    if response.status != 200:
                        text = await response.text()
                        logging.warning(
                            "VLMOllamaVision request failed %s: %s",
                            response.status,
                            text,
                        )
                        return None

                    result = await response.json()
        except aiohttp.ClientError as exc:
            logging.warning("VLMOllamaVision network error: %s", exc)
            return None

        return result.get("response")

    async def _raw_to_text(self, raw_input: Optional[np.ndarray]) -> Optional[Message]:
        if raw_input is None:
            return None

        now = time.time()
        if now - self._last_analysis_ts < self.analysis_interval:
            return None

        description = await self._describe_frame(raw_input)
        if not description:
            return None

        self._last_analysis_ts = now
        return Message(timestamp=now, message=description.strip())

    async def raw_to_text(self, raw_input: Optional[np.ndarray]):
        pending_message = await self._raw_to_text(raw_input)
        if pending_message is not None:
            self.messages.append(pending_message)

    def formatted_latest_buffer(self) -> Optional[str]:
        if not self.messages:
            return None

        latest_message = self.messages[-1]

        result = f"""
INPUT: {self.descriptor_for_LLM}
// START
{latest_message.message}
// END
"""

        self.io_provider.add_input(
            self.descriptor_for_LLM,
            latest_message.message,
            latest_message.timestamp,
        )
        self.messages = []
        return result

    def __del__(self):  # pragma: no cover - destructor guard
        if self.cap is not None:
            self.cap.release()
            self.cap = None
