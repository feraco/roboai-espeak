#!/usr/bin/env python3
"""
Ultra-lightweight face detection plugin using only OpenCV
No external models or AI - just Haar cascades (built into OpenCV)
"""

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Optional

import cv2

from inputs.base import SensorConfig
from inputs.base.loop import FuserInput
from providers.io_provider import IOProvider


@dataclass
class Message:
    timestamp: float
    message: str


class UltraLightFaceDetection(FuserInput[cv2.typing.MatLike]):
    """
    Ultra-lightweight face detection using only OpenCV Haar cascades.
    No AI models, no external dependencies - just basic computer vision.
    Memory usage: <50MB
    """

    def __init__(self, config: SensorConfig = SensorConfig()):
        super().__init__(config)
        
        self.camera_index = config.get("camera_index", 0)
        self.poll_interval = config.get("poll_interval", 3.0)
        self.descriptor = config.get("descriptor", "Ultra Light Face Detection")
        
        # Load OpenCV's built-in face cascade (no download needed)
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        
        self.cap = None
        self.io_provider = IOProvider()
        self.messages = []
        self.last_detection_time = 0
        self.cooldown_period = 5.0  # Don't spam detections
        
        logging.info(f"UltraLightFaceDetection initialized for camera {self.camera_index}")

    async def _start(self):
        """Initialize camera"""
        try:
            self.cap = cv2.VideoCapture(self.camera_index)
            if not self.cap.isOpened():
                logging.error(f"Could not open camera {self.camera_index}")
                return
                
            logging.info(f"UltraLightFaceDetection camera {self.camera_index} opened successfully")
            
        except Exception as e:
            logging.error(f"Error starting UltraLightFaceDetection: {e}")

    async def _stop(self):
        """Release camera"""
        if self.cap:
            self.cap.release()
            logging.info("UltraLightFaceDetection camera released")

    async def _poll(self) -> Optional[cv2.typing.MatLike]:
        """Poll camera for face detection"""
        if not self.cap or not self.cap.isOpened():
            return None
            
        try:
            ret, frame = self.cap.read()
            if not ret:
                logging.warning("Failed to read frame from camera")
                return None
                
            # Convert to grayscale for face detection
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Detect faces
            faces = self.face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(30, 30)
            )
            
            current_time = time.time()
            
            # If faces detected and not in cooldown
            if len(faces) > 0 and (current_time - self.last_detection_time) > self.cooldown_period:
                self.last_detection_time = current_time
                logging.info(f"UltraLightFaceDetection: Detected {len(faces)} face(s)")
                return frame
                
            return None
            
        except Exception as e:
            logging.error(f"Error in UltraLightFaceDetection polling: {e}")
            return None

    async def _raw_to_text(self, frame: cv2.typing.MatLike) -> str:
        """Convert detection to text description"""
        if frame is not None:
            # Simple face detection message
            return "Face detected - person present"
        return ""

    def formatted_latest_buffer(self) -> str:
        """Return formatted buffer for LLM prompt"""
        if self.messages:
            latest = self.messages[-1]
            return f"""INPUT: {self.descriptor}
// START
{latest.message}
// END"""
        return ""