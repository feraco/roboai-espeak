#!/usr/bin/env python3
"""
Badge Reader VLM Input Plugin
Uses Vision Language Model to detect and read ID badges/name tags
Outputs detected names to trigger personalized greetings
"""

import asyncio
import logging
import time
import base64
import io
from collections import deque
from dataclasses import dataclass
from queue import Empty, Queue
from typing import Deque, Optional, Set

import cv2
import numpy as np
import requests

from inputs.base import SensorConfig
from inputs.base.loop import FuserInput
from providers.io_provider import IOProvider


@dataclass
class Message:
    timestamp: float
    message: str


class BadgeReaderVLM(FuserInput[cv2.typing.MatLike]):
    """
    Badge reader using Vision Language Model for intelligent badge detection.
    Detects name badges/ID cards and extracts person names.
    """

    def __init__(self, config: SensorConfig = SensorConfig()):
        super().__init__(config)

        # Camera configuration
        self.camera_index = getattr(config, "camera_index", 0)
        self.poll_interval = getattr(config, "poll_interval", 5.0)  # Check every 5 seconds
        self.greeting_cooldown = getattr(config, "greeting_cooldown", 60.0)  # Greet same person every 60s

        # VLM configuration
        self.vlm_model = getattr(config, "vlm_model", "llava:7b")
        self.vlm_base_url = getattr(config, "vlm_base_url", "http://localhost:11434")
        self.temperature = getattr(config, "temperature", 0.1)

        # Buffer configuration
        self.buffer_size = getattr(config, "buffer_size", 5)
        self.descriptor = getattr(config, "descriptor", "Badge Reader - VLM")

        # State management
        self.cap = None
        self.io_provider = IOProvider()
        self.messages: Deque[Message] = deque(maxlen=self.buffer_size)
        
        # Track detected people to avoid duplicate greetings
        self.detected_people: dict[str, float] = {}  # name -> last_seen_timestamp
        
        logging.info(
            f"BadgeReaderVLM initialized: camera={self.camera_index}, "
            f"interval={self.poll_interval}s, model={self.vlm_model}"
        )

    async def _start(self):
        """Initialize camera"""
        try:
            self.cap = cv2.VideoCapture(self.camera_index)
            if not self.cap.isOpened():
                logging.error(f"Failed to open camera {self.camera_index}")
                return

            # Set camera properties
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.cap.set(cv2.CAP_PROP_FPS, 15)

            logging.info(f"Badge reader camera {self.camera_index} initialized")
        except Exception as e:
            logging.error(f"Failed to initialize badge reader camera: {e}")

    async def _stop(self):
        """Release camera"""
        if self.cap:
            self.cap.release()
            logging.info("Badge reader camera released")

    async def _poll(self) -> Optional[cv2.typing.MatLike]:
        """Poll camera for new frames"""
        if not self.cap or not self.cap.isOpened():
            return None

        try:
            ret, frame = self.cap.read()
            if not ret:
                logging.warning("Failed to read frame from badge reader camera")
                return None

            return frame

        except Exception as e:
            logging.error(f"Badge reader polling error: {e}")
            return None

    async def _raw_to_text(self, raw_input: cv2.typing.MatLike) -> Optional[Message]:
        """
        Process video frame with VLM to detect badges and extract names.

        Parameters
        ----------
        raw_input : cv2.typing.MatLike
            Input video frame

        Returns
        -------
        Message
            Message containing detected person's name if found
        """
        if raw_input is None:
            return None

        try:
            # Encode frame to base64 for VLM API
            image_base64 = self._encode_frame_to_base64(raw_input)

            # Ask VLM to detect and read badges
            prompt = """Look at this image carefully. Is there an ID badge, name tag, or name card visible?

If you see a badge or name tag with a person's name:
- Extract the FULL NAME (first and last name if visible)
- Respond with ONLY: "DETECTED: [Full Name]"
- Example: "DETECTED: John Smith"

If you see a person but NO badge/name is visible:
- Respond with ONLY: "NO_BADGE"

If you see NO person at all:
- Respond with ONLY: "EMPTY"

Be precise. Only respond with one of the three formats above."""

            # Call VLM API
            response = self._call_vlm_api(image_base64, prompt)

            if response:
                logging.info(f"Badge reader VLM response: {response}")
                
                # Parse response
                name = self._parse_vlm_response(response)
                
                if name:
                    # Check if we should greet this person (cooldown check)
                    current_time = time.time()
                    
                    if name in self.detected_people:
                        last_seen = self.detected_people[name]
                        time_since = current_time - last_seen
                        
                        if time_since < self.greeting_cooldown:
                            logging.info(
                                f"Skipping greeting for {name} "
                                f"(last seen {time_since:.1f}s ago)"
                            )
                            return None
                    
                    # Update last seen time
                    self.detected_people[name] = current_time
                    
                    # Create greeting message
                    message = f"I see {name} is here. Their badge says {name}."
                    
                    logging.info(f"✅ Badge detected: {name}")
                    return Message(timestamp=current_time, message=message)
                
            return None

        except Exception as e:
            logging.error(f"Badge reader processing error: {e}", exc_info=True)
            return None

    def _encode_frame_to_base64(self, frame: cv2.typing.MatLike) -> str:
        """Encode OpenCV frame to base64 for API transmission"""
        try:
            # Convert BGR to RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Encode as JPEG
            _, buffer = cv2.imencode('.jpg', rgb_frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            
            # Convert to base64
            image_base64 = base64.b64encode(buffer.tobytes()).decode('utf-8')
            
            return image_base64
            
        except Exception as e:
            logging.error(f"Frame encoding error: {e}")
            raise

    def _call_vlm_api(self, image_base64: str, prompt: str) -> Optional[str]:
        """Call Ollama VLM API"""
        try:
            url = f"{self.vlm_base_url}/api/generate"
            
            payload = {
                "model": self.vlm_model,
                "prompt": prompt,
                "images": [image_base64],
                "stream": False,
                "options": {
                    "temperature": self.temperature,
                    "num_predict": 50,  # Keep response short
                }
            }

            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()

            result = response.json()
            return result.get("response", "").strip()

        except requests.exceptions.Timeout:
            logging.error("VLM API timeout")
            return None
        except requests.exceptions.RequestException as e:
            logging.error(f"VLM API error: {e}")
            return None
        except Exception as e:
            logging.error(f"Unexpected VLM API error: {e}")
            return None

    def _parse_vlm_response(self, response: str) -> Optional[str]:
        """Parse VLM response to extract detected name"""
        response = response.strip()
        
        # Check for "DETECTED: Name" format
        if response.startswith("DETECTED:"):
            name = response.replace("DETECTED:", "").strip()
            
            # Basic validation
            if name and len(name) > 1 and len(name) < 50:
                # Clean up common OCR artifacts
                name = name.replace('"', '').replace("'", '')
                
                # Verify it looks like a name (letters and spaces only)
                if all(c.isalpha() or c.isspace() for c in name):
                    return name.title()  # Capitalize properly
        
        return None

    def formatted_latest_buffer(self) -> str:
        """Return formatted buffer for LLM prompt"""
        if not self.messages:
            return ""

        # Get the latest detected name
        latest = self.messages[-1]
        
        return f"""INPUT: {self.descriptor}
// START
{latest.message}
// END"""

    def get_detected_people(self) -> list[str]:
        """Get list of people detected in the current session"""
        return list(self.detected_people.keys())

    def reset_detections(self) -> None:
        """Reset detected people history (for testing)"""
        self.detected_people.clear()
        logging.info("Badge reader detections reset")
