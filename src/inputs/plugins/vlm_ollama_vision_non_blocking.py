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
        "VLMOllamaVisionNonBlocking requires OpenCV and NumPy. Please install opencv-python-headless (or opencv-python) and numpy."
    ) from exc

from inputs.base import SensorConfig
from inputs.base.loop import FuserInput
from providers.io_provider import IOProvider


@dataclass
class Message:
    timestamp: float
    message: str


class VLMOllamaVisionNonBlocking(FuserInput[np.ndarray]):
    """
    Capture camera frames and ask an Ollama vision model for a short description.
    
    NON-BLOCKING VERSION: Opens and closes camera for each capture to avoid
    holding exclusive locks that can conflict with audio devices on the same
    USB interface (common with webcams that have built-in microphones).
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

        self._last_analysis_ts = 0.0

    def _capture_single_frame(self) -> Optional[np.ndarray]:
        """
        Open camera, capture one frame, then immediately release.
        
        This avoids holding the camera device open continuously, which can
        cause conflicts with audio devices on the same USB interface.
        """
        cap = None
        try:
            cap = cv2.VideoCapture(self.camera_index)
            if not cap.isOpened():
                logging.warning(
                    "VLMOllamaVisionNonBlocking could not open camera index %s", 
                    self.camera_index
                )
                return None

            # Sometimes first frame is black, try up to 3 times
            frame = None
            for _ in range(3):
                ret, frame = cap.read()
                if ret and frame is not None:
                    break
                time.sleep(0.1)
            
            if not ret or frame is None:
                logging.debug("VLMOllamaVisionNonBlocking failed to capture frame")
                return None

            return frame
            
        except Exception as e:
            logging.warning(f"VLMOllamaVisionNonBlocking camera error: {e}")
            return None
        finally:
            # ALWAYS release the camera immediately
            if cap is not None:
                cap.release()

    async def _poll(self) -> Optional[np.ndarray]:
        await asyncio.sleep(self.poll_interval)
        return self._capture_single_frame()

    async def _describe_frame(self, frame: np.ndarray) -> Optional[str]:
        ok, buffer = cv2.imencode(".jpg", frame)
        if not ok:
            logging.debug("VLMOllamaVisionNonBlocking failed to encode frame")
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
                            "VLMOllamaVisionNonBlocking request failed %s: %s",
                            response.status,
                            text,
                        )
                        return None

                    result = await response.json()
        except aiohttp.ClientError as exc:
            logging.warning("VLMOllamaVisionNonBlocking network error: %s", exc)
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
