#!/usr/bin/env python3
"""
Badge Reader using EasyOCR - Better for handwriting and varied text
Drop-in replacement for BadgeReaderOCR using pytesseract
"""

import asyncio
import logging
import time
import re
from collections import deque
from dataclasses import dataclass
from typing import Deque, Optional, List

import cv2
import numpy as np

from inputs.base import SensorConfig
from inputs.base.loop import FuserInput
from providers.io_provider import IOProvider

# Try to import easyocr
try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError as import_err:
    EASYOCR_AVAILABLE = False
    logging.warning(f"easyocr not available - badge reader will not work: {import_err}")


@dataclass
class Message:
    timestamp: float
    message: str


class BadgeReaderEasyOCR(FuserInput[cv2.typing.MatLike]):
    """
    Badge reader using EasyOCR for intelligent badge detection.
    Better than pytesseract for handwritten text and varied fonts.
    """

    def __init__(self, config: SensorConfig = SensorConfig()):
        super().__init__(config)

        if not EASYOCR_AVAILABLE:
            raise ImportError("easyocr is required for BadgeReaderEasyOCR. Install with: pip install easyocr")

        # Camera configuration
        self.camera_index = getattr(config, "camera_index", 0)
        self.poll_interval = getattr(config, "poll_interval", 5.0)
        self.greeting_cooldown = getattr(config, "greeting_cooldown", 60.0)

        # Buffer configuration
        self.buffer_size = getattr(config, "buffer_size", 5)
        self.descriptor = getattr(config, "descriptor", "Badge Reader - EasyOCR")

        # OCR configuration
        self.confidence_threshold = getattr(config, "confidence_threshold", 0.5)
        self.min_confidence = getattr(config, "min_confidence", 0.7)  # Minimum confidence for text detection

        # State management
        self.cap = None
        self.io_provider = IOProvider()
        self.messages: Deque[Message] = deque(maxlen=self.buffer_size)
        self.last_poll_time = 0.0
        
        # Track detected people
        self.detected_people: dict[str, float] = {}
        
        # Common badge text to ignore (lowercase for comparison)
        self._ignore_words = {
            'visitor', 'guest', 'staff', 'employee', 'id', 'badge', 'card',
            'security', 'access', 'authorized', 'personnel', 'company',
            'corp', 'inc', 'llc', 'ltd', 'department', 'dept', 'division',
            'manager', 'director', 'president', 'ceo', 'cto', 'cfo',
            'hospital', 'medical', 'center', 'clinic', 'doctor', 'nurse',
            'administrator', 'admin', 'supervisor', 'coordinator', 'name',
            'expires', 'issued', 'valid', 'photo', 'signature', 'first',
            'last', 'middle', 'title', 'position', 'role', 'location',
            'building', 'floor', 'room', 'suite', 'office', 'phone',
            'email', 'website', 'address', 'street', 'city', 'state',
            'zip', 'code', 'barcode', 'number', 'date', 'time', 'lexful',
            'conference', 'event', 'attendee', 'speaker', 'vendor', 'exhibitor',
            'teacher', 'student', 'professor', 'instructor', 'welcome'
        }
        
        logging.info(f"BadgeReaderEasyOCR initializing: camera={self.camera_index}")
        
        # Initialize EasyOCR reader
        logging.info("🔄 Loading EasyOCR model (one-time, takes ~10 seconds)...")
        self.reader = easyocr.Reader(['en'], gpu=False, verbose=False)
        logging.info("✅ EasyOCR model loaded")
        
        # Initialize camera
        self._initialize_camera()
        
        # Log final camera status
        if self.cap and self.cap.isOpened():
            logging.info("✅ BadgeReaderEasyOCR fully initialized - camera ready")
        else:
            logging.error("❌ BadgeReaderEasyOCR initialized but CAMERA FAILED")
            logging.error("   Badge detection will not work!")
            logging.error(f"   Check: camera {self.camera_index} is available")
            logging.error(f"   Try: python3 scripts/testing/list_cameras.py")

    def _initialize_camera(self):
        """Initialize camera"""
        try:
            logging.info(f"🎥 Initializing badge reader camera {self.camera_index}...")
            
            # Release any existing capture first
            if hasattr(self, 'cap') and self.cap is not None:
                self.cap.release()
                time.sleep(0.5)
            
            self.cap = cv2.VideoCapture(self.camera_index)
            if not self.cap.isOpened():
                logging.error(f"❌ Failed to open camera {self.camera_index}")
                logging.error(f"   Try closing other apps using the camera")
                logging.error(f"   Or check camera permissions in System Preferences")
                self.cap = None
                return

            # Set camera properties
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
            self.cap.set(cv2.CAP_PROP_FPS, 15)
            
            # Test read to verify camera works
            ret, test_frame = self.cap.read()
            if not ret:
                logging.error(f"❌ Camera {self.camera_index} opened but cannot read frames")
                self.cap.release()
                self.cap = None
                return

            logging.info(f"✅ Badge reader camera {self.camera_index} initialized and ready")
            logging.info(f"   Resolution: {test_frame.shape[1]}x{test_frame.shape[0]}")
            
        except Exception as e:
            logging.error(f"❌ Failed to initialize badge reader camera: {e}")
            self.cap = None

    def __del__(self):
        """Release camera on cleanup"""
        if hasattr(self, 'cap') and self.cap:
            self.cap.release()

    async def _poll(self) -> Optional[cv2.typing.MatLike]:
        """Poll camera for new frames"""
        await asyncio.sleep(0.1)
        
        current_time = time.time()
        time_since_last_poll = current_time - self.last_poll_time
        
        if time_since_last_poll < self.poll_interval:
            return None
        
        self.last_poll_time = current_time
        
        if not self.cap or not self.cap.isOpened():
            logging.warning("Badge reader: Camera not available")
            return None

        try:
            ret, frame = self.cap.read()
            if not ret:
                logging.warning("Failed to read frame from badge reader camera")
                return None

            logging.info(f"📸 Badge reader captured frame: {frame.shape}")
            return frame

        except Exception as e:
            logging.error(f"Badge reader polling error: {e}")
            return None

    async def _raw_to_text(self, raw_input: cv2.typing.MatLike) -> Optional[Message]:
        """Process video frame with EasyOCR to detect badges and extract names"""
        if raw_input is None:
            return None

        try:
            logging.info("🔍 Processing frame for badge detection with EasyOCR...")
            
            # Get center region (where badges typically are)
            h, w = raw_input.shape[:2]
            roi = raw_input[h//4:3*h//4, w//4:3*w//4]
            
            # Run EasyOCR
            logging.info("🤖 Running EasyOCR on frame...")
            results = self.reader.readtext(roi)
            
            if not results:
                logging.info("No text detected in frame")
                return None
            
            # Extract text with confidence above threshold
            detected_texts = []
            for bbox, text, confidence in results:
                if confidence >= self.min_confidence:
                    detected_texts.append(text)
                    logging.info(f"📝 OCR detected: '{text}' (confidence: {confidence:.2f})")
            
            if not detected_texts:
                logging.info("No high-confidence text detected")
                return None
            
            # Combine all detected text
            combined_text = " ".join(detected_texts)
            
            # Extract names
            names = self._extract_names(combined_text)
            
            if names:
                name = names[0]
                
                # Check cooldown
                current_time = time.time()
                
                if name in self.detected_people:
                    last_seen = self.detected_people[name]
                    time_since = current_time - last_seen
                    
                    if time_since < self.greeting_cooldown:
                        logging.info(f"Skipping greeting for {name} (last seen {time_since:.1f}s ago)")
                        return None
                
                # Update last seen
                self.detected_people[name] = current_time
                
                # Create greeting message
                first_name = name.split()[0] if " " in name else name
                message = f"BADGE DETECTED: Greet {first_name}. Say: 'Hi {first_name}, my name is Lex' and introduce yourself."
                
                logging.info(f"✅ Badge detected: {name} - triggering greeting")
                return Message(timestamp=current_time, message=message)
            
            return None

        except Exception as e:
            logging.error(f"Badge reader processing error: {e}", exc_info=True)
            return None

    async def raw_to_text(self, raw_input: cv2.typing.MatLike):
        """Convert raw input to processed text and manage message buffer"""
        pending_message = await self._raw_to_text(raw_input)

        if pending_message is not None:
            self.messages.append(pending_message)
            logging.info(f"✅ Added message to buffer: {pending_message.message}")

    def _extract_names(self, text: str) -> List[str]:
        """Extract potential names from OCR text"""
        names = []
        
        # Clean up text
        text = re.sub(r'[^\w\s]', ' ', text)
        text = ' '.join(text.split())
        
        # Look for name patterns
        patterns = [
            r'\b([A-Z][a-z]+)\s+([A-Z][a-z]+)\b',  # First Last
            r'\b([A-Z][A-Z]+)\s+([A-Z][A-Z]+)\b',  # ALL CAPS
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                if match.lastindex and match.lastindex >= 2:
                    first = match.group(1)
                    last = match.group(2)
                    name = f"{first} {last}"
                    
                    cleaned_name = self._validate_name(name)
                    if cleaned_name:
                        names.append(cleaned_name)
        
        # Remove duplicates
        seen = set()
        unique_names = []
        for name in names:
            name_lower = name.lower()
            if name_lower not in seen:
                seen.add(name_lower)
                unique_names.append(name)
        
        return unique_names

    def _validate_name(self, name: str) -> Optional[str]:
        """Validate that detected text is a person's name"""
        if not name or len(name) < 3:
            return None
            
        name = name.title().strip()
        words = name.split()
        
        if len(words) < 2:
            logging.debug(f"Name validation failed: {name} (need at least 2 words)")
            return None
        
        for word in words:
            if len(word) < 2:
                logging.debug(f"Name validation failed: {name} (word too short: {word})")
                return None
            
            if word.lower() in self._ignore_words:
                logging.debug(f"Name validation failed: {name} (contains non-name word: {word})")
                return None
            
            if not word[0].isupper():
                logging.debug(f"Name validation failed: {name} (not capitalized: {word})")
                return None
            
            if not word[1:].islower():
                if not (word.isupper() and len(word) <= 4):
                    logging.debug(f"Name validation failed: {name} (improper case: {word})")
                    return None
        
        if len(words) > 4:
            logging.debug(f"Name validation failed: {name} (too many words: {len(words)})")
            return None
        
        logging.info(f"✅ Name validation PASSED: {name} - confirmed as person's name")
        return name

    def formatted_latest_buffer(self) -> str:
        """Return formatted buffer for LLM prompt"""
        if not self.messages:
            return ""

        latest = self.messages[-1]
        
        return f"""INPUT: {self.descriptor}
// START
{latest.message}
// END"""

    def get_detected_people(self) -> list[str]:
        """Get list of people detected in the current session"""
        return list(self.detected_people.keys())

    def reset_detections(self) -> None:
        """Reset detected people history"""
        self.detected_people.clear()
        logging.info("Badge reader detections reset")
