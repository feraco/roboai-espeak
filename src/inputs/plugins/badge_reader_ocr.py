#!/usr/bin/env python3
"""
Badge Reader OCR Input Plugin
Uses OCR (pytesseract) to detect and read ID badges/name tags
Lightweight alternative to VLM - uses minimal memory
"""

import asyncio
import logging
import time
import re
from collections import deque
from dataclasses import dataclass
from queue import Empty, Queue
from typing import Deque, Optional, Set, List

import cv2
import numpy as np

from inputs.base import SensorConfig
from inputs.base.loop import FuserInput
from providers.io_provider import IOProvider

# Try to import pytesseract
try:
    import pytesseract
    PYTESSERACT_AVAILABLE = True
except ImportError as import_err:
    PYTESSERACT_AVAILABLE = False
    logging.warning(f"pytesseract not available - badge reader will not work: {import_err}")


@dataclass
class Message:
    timestamp: float
    message: str


class BadgeReaderOCR(FuserInput[cv2.typing.MatLike]):
    """
    Lightweight badge reader using OCR for intelligent badge detection.
    Detects name badges/ID cards and extracts person names.
    Much more memory efficient than VLM-based approaches.
    """

    def __init__(self, config: SensorConfig = SensorConfig()):
        super().__init__(config)

        if not PYTESSERACT_AVAILABLE:
            raise ImportError("pytesseract is required for BadgeReaderOCR. Install with: uv add pytesseract")

        # Camera configuration
        self.camera_index = getattr(config, "camera_index", 0)
        self.poll_interval = getattr(config, "poll_interval", 5.0)  # Check every 5 seconds
        self.greeting_cooldown = getattr(config, "greeting_cooldown", 60.0)  # Greet same person every 60s

        # Buffer configuration
        self.buffer_size = getattr(config, "buffer_size", 5)
        self.descriptor = getattr(config, "descriptor", "Badge Reader - OCR")

        # OCR configuration
        self.confidence_threshold = getattr(config, "confidence_threshold", 0.5)
        self.preprocess_quality = getattr(config, "preprocess_quality", "medium")  # low, medium, high

        # State management
        self.cap = None
        self.io_provider = IOProvider()
        self.messages: Deque[Message] = deque(maxlen=self.buffer_size)
        self.last_poll_time = 0.0  # Track when we last polled the camera
        
        # Track detected people to avoid duplicate greetings
        self.detected_people: dict[str, float] = {}  # name -> last_seen_timestamp
        
        # Name patterns to look for
        self._name_patterns = [
            r'\b([A-Z][a-z]+)\s+([A-Z][a-z]+)\b',  # First Last
            r'\b([A-Z][A-Z]+)\s+([A-Z][A-Z]+)\b',  # ALL CAPS names
        ]
        
        # Common badge text to ignore (lowercase for comparison)
        # CRITICAL: Only greet if we detect an ACTUAL PERSON'S NAME
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
            'conference', 'event', 'attendee', 'speaker', 'vendor', 'exhibitor'
        }
        
        logging.info(
            f"BadgeReaderOCR initialized: camera={self.camera_index}, "
            f"interval={self.poll_interval}s, quality={self.preprocess_quality}"
        )
        
        # Initialize camera immediately
        self._initialize_camera()

    def _initialize_camera(self):
        """Initialize camera (called during __init__)"""
        try:
            logging.info(f"🎥 Initializing badge reader camera {self.camera_index}...")
            self.cap = cv2.VideoCapture(self.camera_index)
            if not self.cap.isOpened():
                logging.error(f"❌ Failed to open camera {self.camera_index}")
                return

            # Set camera properties
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.cap.set(cv2.CAP_PROP_FPS, 15)

            logging.info(f"✅ Badge reader camera {self.camera_index} initialized and ready")
        except Exception as e:
            logging.error(f"❌ Failed to initialize badge reader camera: {e}")

    def __del__(self):
        """Release camera on cleanup"""
        if hasattr(self, 'cap') and self.cap:
            self.cap.release()
            logging.debug("Badge reader camera released")

    async def _poll(self) -> Optional[cv2.typing.MatLike]:
        """Poll camera for new frames (respects poll_interval)"""
        # CRITICAL: Always yield to event loop to prevent blocking audio processing
        await asyncio.sleep(0.1)
        
        # Check if enough time has passed since last poll
        current_time = time.time()
        time_since_last_poll = current_time - self.last_poll_time
        
        if time_since_last_poll < self.poll_interval:
            # Not time to poll yet - return None without capturing
            return None
        
        # Update last poll time
        self.last_poll_time = current_time
        
        if not self.cap or not self.cap.isOpened():
            logging.warning("Badge reader: Camera not available for polling")
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
        """
        Process video frame with OCR to detect badges and extract names.

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
            logging.info("🔍 Processing frame for badge detection...")
            
            # Preprocess image for better OCR
            processed = self._preprocess_image(raw_input)
            
            # Extract text using OCR
            logging.info("🤖 Running OCR on frame...")
            text = pytesseract.image_to_string(processed, config='--psm 6')
            
            if text.strip():
                logging.info(f"📝 OCR detected text: {text.strip()}")
                
                # Extract names from text
                names = self._extract_names(text)
                
                if names:
                    # Use the first detected name
                    name = names[0]
                    
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
                    
                    # Create greeting trigger message - tells LLM to greet this person
                    # Extract first name only (e.g., "John Smith" -> "John")
                    first_name = name.split()[0] if " " in name else name
                    message = f"BADGE DETECTED: Greet {first_name}. Say: 'Hi {first_name}, my name is Lex' and introduce yourself."
                    
                    logging.info(f"✅ Badge detected: {name} - triggering greeting")
                    return Message(timestamp=current_time, message=message)
                
            return None

        except Exception as e:
            logging.error(f"Badge reader processing error: {e}", exc_info=True)
            return None

    async def raw_to_text(self, raw_input: cv2.typing.MatLike):
        """
        Convert raw input to processed text and manage message buffer.

        Parameters
        ----------
        raw_input : cv2.typing.MatLike
            Raw video frame from camera
        """
        pending_message = await self._raw_to_text(raw_input)

        if pending_message is not None:
            self.messages.append(pending_message)
            logging.info(f"✅ Added message to buffer: {pending_message.message}")

    def _preprocess_image(self, frame: np.ndarray) -> np.ndarray:
        """Preprocess image for better OCR accuracy"""
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Use center region (where badges typically are)
        h, w = gray.shape
        roi = gray[h//4:3*h//4, w//4:3*w//4]
        
        if self.preprocess_quality == "low":
            # Basic thresholding only
            _, processed = cv2.threshold(roi, 127, 255, cv2.THRESH_BINARY)
            
        elif self.preprocess_quality == "high":
            # Advanced preprocessing
            # Resize if too small
            if roi.shape[0] < 150 or roi.shape[1] < 150:
                scale = max(150 / roi.shape[0], 150 / roi.shape[1])
                new_w = int(roi.shape[1] * scale)
                new_h = int(roi.shape[0] * scale)
                roi = cv2.resize(roi, (new_w, new_h), interpolation=cv2.INTER_CUBIC)
            
            # Enhance contrast
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(roi)
            
            # Bilateral filter to reduce noise while keeping edges
            filtered = cv2.bilateralFilter(enhanced, 9, 75, 75)
            
            # Adaptive threshold
            processed = cv2.adaptiveThreshold(
                filtered, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY, 11, 2
            )
            
            # Morphological operations
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
            processed = cv2.morphologyEx(processed, cv2.MORPH_CLOSE, kernel)
            
        else:  # medium (default)
            # Balance between speed and accuracy
            # Slight blur to reduce noise
            blurred = cv2.GaussianBlur(roi, (3, 3), 0)
            
            # Adaptive threshold
            processed = cv2.adaptiveThreshold(
                blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY, 11, 2
            )
            
            # Light cleanup
            kernel = np.ones((2, 2), np.uint8)
            processed = cv2.morphologyEx(processed, cv2.MORPH_CLOSE, kernel)
        
        return processed

    def _extract_names(self, text: str) -> List[str]:
        """Extract potential names from OCR text"""
        names = []
        
        # Clean up text
        text = re.sub(r'[^\w\s]', ' ', text)
        text = ' '.join(text.split())  # Normalize whitespace
        
        # Try each name pattern
        for pattern in self._name_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                if match.lastindex and match.lastindex >= 2:
                    # Extract first and last name
                    first = match.group(1)
                    last = match.group(2)
                    name = f"{first} {last}"
                    
                    # Validate and clean name
                    cleaned_name = self._validate_name(name)
                    if cleaned_name:
                        names.append(cleaned_name)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_names = []
        for name in names:
            name_lower = name.lower()
            if name_lower not in seen:
                seen.add(name_lower)
                unique_names.append(name)
        
        return unique_names

    def _validate_name(self, name: str) -> Optional[str]:
        """
        Validate that detected text is DEFINITELY a person's name on a badge.
        CRITICAL: Only return name if we're confident it's an actual person's name.
        """
        if not name or len(name) < 3:
            return None
            
        # Convert to title case
        name = name.title().strip()
        
        # Split into words
        words = name.split()
        if len(words) < 2:  # Need at least first and last name
            logging.debug(f"Name validation failed: {name} (need at least 2 words)")
            return None
        
        # Check each word
        for word in words:
            # Each word must be 2+ characters
            if len(word) < 2:
                logging.debug(f"Name validation failed: {name} (word too short: {word})")
                return None
            
            # Check if it's in ignore list (NOT a person's name)
            if word.lower() in self._ignore_words:
                logging.debug(f"Name validation failed: {name} (contains non-name word: {word})")
                return None
            
            # CRITICAL: Must start with capital letter (proper name)
            if not word[0].isupper():
                logging.debug(f"Name validation failed: {name} (not capitalized: {word})")
                return None
            
            # CRITICAL: Rest of word should be lowercase (proper name format)
            if not word[1:].islower():
                # Allow all-caps if it's a short name (e.g., "JO LEE")
                if not (word.isupper() and len(word) <= 4):
                    logging.debug(f"Name validation failed: {name} (improper case: {word})")
                    return None
        
        # CRITICAL: Check if name looks like actual person name patterns
        # Common patterns: "John Smith", "Mary Jane Doe", etc.
        if len(words) > 4:
            logging.debug(f"Name validation failed: {name} (too many words: {len(words)})")
            return None
        
        # Additional check: avoid common non-name phrases
        name_lower = name.lower()
        non_name_phrases = ['event staff', 'team member', 'support crew', 'front desk']
        for phrase in non_name_phrases:
            if phrase in name_lower:
                logging.debug(f"Name validation failed: {name} (contains non-name phrase: {phrase})")
                return None
        
        logging.info(f"✅ Name validation PASSED: {name} - confirmed as person's name")
        return name
        
        # Avoid common false positives
        name_lower = name.lower()
        if any(bad in name_lower for bad in ['test', 'sample', 'example', 'expires', 'issued']):
            return None
        
        return name

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
