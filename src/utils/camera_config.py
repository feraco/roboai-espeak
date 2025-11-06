"""
Camera device configuration and management.

Handles automatic detection of Intel RealSense D435i and other cameras,
with persistent configuration storage.
"""

import logging
import subprocess
from pathlib import Path
from typing import Optional, Tuple

import yaml


class CameraConfig:
    """Manages camera device configuration."""
    
    CONFIG_FILE = Path("camera_config.yaml")
    
    # Target camera
    TARGET_CAMERA = "Intel(R) RealSense(TM) Depth Camera 435i"
    
    def __init__(self):
        """Initialize camera configuration."""
        self.camera_index: Optional[int] = None
        self.camera_name: str = "Unknown"
        self.width: int = 640
        self.height: int = 480
        
    def detect_camera(self) -> Optional[int]:
        """
        Detect Intel RealSense camera.
        
        Returns
        -------
        Optional[int]
            Camera device index, or None if not found
        """
        logging.info("🔍 Detecting camera devices...")
        
        # Method 1: Try v4l2-ctl (Linux)
        camera_index = self._detect_v4l2()
        if camera_index is not None:
            return camera_index
        
        # Method 2: Try OpenCV enumeration (fallback)
        camera_index = self._detect_opencv()
        if camera_index is not None:
            return camera_index
        
        logging.warning("⚠️  No Intel RealSense camera detected")
        return None
    
    def _detect_v4l2(self) -> Optional[int]:
        """Detect camera using v4l2-ctl (Linux)."""
        try:
            result = subprocess.run(
                ["v4l2-ctl", "--list-devices"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode != 0:
                logging.debug("v4l2-ctl not available")
                return None
            
            # Parse output for Intel RealSense
            lines = result.stdout.split('\n')
            current_device = None
            
            for i, line in enumerate(lines):
                # Check if this is the RealSense camera
                if "Intel" in line and "RealSense" in line:
                    current_device = line.strip()
                    logging.info(f"✅ Found: {current_device}")
                    
                    # Next line should have /dev/video*
                    if i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        if "/dev/video" in next_line:
                            # Extract index from /dev/video0, /dev/video1, etc.
                            import re
                            match = re.search(r'/dev/video(\d+)', next_line)
                            if match:
                                index = int(match.group(1))
                                self.camera_index = index
                                self.camera_name = current_device
                                logging.info(f"✅ Camera index: {index}")
                                return index
            
            return None
            
        except Exception as e:
            logging.debug(f"v4l2 detection failed: {e}")
            return None
    
    def _detect_opencv(self) -> Optional[int]:
        """Detect camera using OpenCV enumeration."""
        try:
            import cv2
            
            # Try first 10 camera indices
            for i in range(10):
                try:
                    cap = cv2.VideoCapture(i)
                    if cap.isOpened():
                        # Try to get camera name (works on some platforms)
                        backend = cap.getBackendName()
                        
                        # Read a test frame
                        ret, frame = cap.read()
                        cap.release()
                        
                        if ret and frame is not None:
                            logging.info(f"✅ Found camera at index {i} (backend: {backend})")
                            self.camera_index = i
                            self.camera_name = f"Camera {i} ({backend})"
                            return i
                except Exception:
                    continue
            
            return None
            
        except ImportError:
            logging.debug("OpenCV not available for camera detection")
            return None
    
    def test_camera(self) -> Tuple[bool, str]:
        """
        Test camera by capturing a frame.
        
        Returns
        -------
        Tuple[bool, str]
            (success, message)
        """
        if self.camera_index is None:
            return False, "No camera index configured"
        
        try:
            import cv2
            
            logging.info(f"🎥 Testing camera {self.camera_index}...")
            
            cap = cv2.VideoCapture(self.camera_index)
            
            if not cap.isOpened():
                return False, f"Cannot open camera {self.camera_index}"
            
            # Get properties
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            
            logging.info(f"   Resolution: {width}x{height}")
            logging.info(f"   FPS: {fps}")
            
            # Try to read frame
            ret, frame = cap.read()
            cap.release()
            
            if not ret or frame is None:
                return False, "Cannot capture frame from camera"
            
            self.width = width
            self.height = height
            
            logging.info(f"✅ Camera test PASSED")
            return True, f"Camera working: {width}x{height} @ {fps} FPS"
            
        except Exception as e:
            return False, f"Camera test failed: {e}"
    
    def save_config(self):
        """Save camera configuration to YAML file."""
        config = {
            "camera_index": self.camera_index,
            "camera_name": self.camera_name,
            "width": self.width,
            "height": self.height,
        }
        
        with open(self.CONFIG_FILE, 'w') as f:
            yaml.dump(config, f)
        
        logging.info(f"💾 Camera config saved to: {self.CONFIG_FILE}")
    
    def load_config(self) -> bool:
        """
        Load camera configuration from YAML file.
        
        Returns
        -------
        bool
            True if config loaded successfully
        """
        if not self.CONFIG_FILE.exists():
            return False
        
        try:
            with open(self.CONFIG_FILE, 'r') as f:
                config = yaml.safe_load(f)
            
            self.camera_index = config.get("camera_index")
            self.camera_name = config.get("camera_name", "Unknown")
            self.width = config.get("width", 640)
            self.height = config.get("height", 480)
            
            logging.info(f"📂 Loaded camera config: {self.camera_name} (index {self.camera_index})")
            return True
            
        except Exception as e:
            logging.error(f"❌ Error loading camera config: {e}")
            return False


def get_camera_config(force_detect: bool = False) -> CameraConfig:
    """
    Get camera configuration (load from file or detect).
    
    Parameters
    ----------
    force_detect : bool
        Force camera detection even if config exists
        
    Returns
    -------
    CameraConfig
        Camera configuration object
    """
    config = CameraConfig()
    
    # Try to load existing config
    if not force_detect and config.load_config():
        # Verify camera still works
        success, message = config.test_camera()
        if success:
            logging.info("✅ Camera configuration validated")
            return config
        else:
            logging.warning(f"⚠️  Saved camera not working: {message}")
            logging.info("🔄 Re-detecting camera...")
    
    # Detect camera
    camera_index = config.detect_camera()
    
    if camera_index is not None:
        # Test camera
        success, message = config.test_camera()
        if success:
            config.save_config()
            logging.info("✅ Camera configured successfully")
        else:
            logging.error(f"❌ Camera test failed: {message}")
    else:
        logging.warning("⚠️  No camera detected")
    
    return config
