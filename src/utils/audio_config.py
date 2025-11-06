"""
Audio device configuration and management.

Handles cross-platform audio device detection and selection,
with persistent configuration storage.
"""

import logging
import platform
import subprocess
from pathlib import Path
from typing import Optional, Tuple

import sounddevice as sd
import yaml


class AudioConfig:
    """Manages audio device configuration across platforms."""
    
    CONFIG_FILE = Path("device_config.yaml")
    
    # Target device names
    TARGET_INPUT = "USB PnP Sound Device"
    TARGET_OUTPUT = "USB 2.0 Speaker"
    
    def __init__(self):
        """Initialize audio configuration."""
        self.platform = platform.system().lower()
        self.input_device: Optional[int] = None
        self.output_device: Optional[int] = None
        self.input_name: str = "Unknown"
        self.output_name: str = "Unknown"
        self.sample_rate: int = 16000
        
    def detect_devices(self) -> Tuple[Optional[int], Optional[int]]:
        """
        Detect and select audio devices by name.
        
        Returns
        -------
        Tuple[Optional[int], Optional[int]]
            (input_device_id, output_device_id)
        """
        logging.info("🔍 Detecting audio devices...")
        
        try:
            # On Linux, ensure we're using PulseAudio, not ALSA directly
            if self.platform == "linux":
                try:
                    # Check if PulseAudio is available
                    result = subprocess.run(
                        ["pactl", "info"],
                        capture_output=True,
                        text=True,
                        timeout=2
                    )
                    if result.returncode == 0:
                        # Set sounddevice to use pulse hostapi
                        import os
                        os.environ['SDL_AUDIODRIVER'] = 'pulse'
                        logging.info("✅ Using PulseAudio backend")
                except Exception as e:
                    logging.warning(f"⚠️  PulseAudio check failed: {e}")
            
            devices = sd.query_devices()
            
            input_dev = None
            output_dev = None
            
            # Find devices by name
            for idx, dev in enumerate(devices):
                name = dev['name']
                max_in = dev['max_input_channels']
                max_out = dev['max_output_channels']
                
                logging.debug(f"Device {idx}: {name} (in:{max_in}, out:{max_out})")
                
                # Find input device
                if self.TARGET_INPUT.lower() in name.lower() and max_in > 0:
                    input_dev = idx
                    self.input_name = name
                    logging.info(f"✅ Found input device: {idx} - {name}")
                    
                # Find output device
                if self.TARGET_OUTPUT.lower() in name.lower() and max_out > 0:
                    output_dev = idx
                    self.output_name = name
                    logging.info(f"✅ Found output device: {idx} - {name}")
            
            # Handle Jetson quirk: USB 2.0 Speaker may show input channels
            if self.platform == "linux" and output_dev is None:
                for idx, dev in enumerate(devices):
                    name = dev['name']
                    if self.TARGET_OUTPUT.lower() in name.lower():
                        output_dev = idx
                        self.output_name = name
                        logging.warning(f"⚠️  Jetson quirk: USB 2.0 Speaker shows as input device {idx}")
                        logging.info(f"✅ Override: Using device {idx} as OUTPUT - {name}")
            
            self.input_device = input_dev
            self.output_device = output_dev
            
            # Determine optimal sample rate
            if input_dev is not None:
                device_info = devices[input_dev]
                default_sr = int(device_info.get('default_samplerate', 16000))
                
                # On Linux, check PulseAudio for actual sample rate
                if self.platform == "linux":
                    pulse_sr = self._get_pulseaudio_sample_rate(self.input_name)
                    if pulse_sr:
                        self.sample_rate = pulse_sr
                        logging.info(f"📊 Using PulseAudio sample rate: {self.sample_rate} Hz")
                    else:
                        # Test sample rates for Linux/Jetson
                        self.sample_rate = self._test_sample_rate(input_dev, [48000, 16000, 44100], default_sr)
                        logging.info(f"📊 Selected sample rate via testing: {self.sample_rate} Hz")
                else:  # macOS
                    # macOS USB mics often prefer 48000
                    self.sample_rate = self._test_sample_rate(input_dev, [48000, 44100, 16000], default_sr)
                    logging.info(f"📊 Selected sample rate: {self.sample_rate} Hz")
            
            return input_dev, output_dev
            
        except Exception as e:
            logging.error(f"❌ Error detecting devices: {e}", exc_info=True)
            return None, None
    
    def _test_sample_rate(self, device: int, rates: list, default: int) -> int:
        """Test which sample rate works for the device."""
        for rate in rates:
            try:
                sd.check_input_settings(device=device, samplerate=rate, channels=1)
                logging.debug(f"✅ Sample rate {rate} Hz works")
                return rate
            except Exception as e:
                logging.debug(f"❌ Sample rate {rate} Hz failed: {e}")
                continue
        logging.warning(f"⚠️  All sample rate tests failed, using default: {default} Hz")
        return default
    
    def _get_pulseaudio_sample_rate(self, device_name: str) -> Optional[int]:
        """Get sample rate from PulseAudio for a specific device."""
        try:
            result = subprocess.run(
                ["pactl", "list", "short", "sources"],
                capture_output=True,
                text=True,
                timeout=2
            )
            
            if result.returncode != 0:
                return None
            
            # Parse output for device and sample rate
            # Format: index name driver sample_spec ...
            for line in result.stdout.strip().split('\n'):
                if 'C-Media_Electronics_Inc._USB_PnP_Sound_Device' in line or 'USB_PnP_Sound_Device' in line:
                    parts = line.split()
                    if len(parts) >= 4:
                        # Extract sample rate from spec like "s16le 1ch 48000Hz"
                        spec = parts[3]
                        import re
                        match = re.search(r'(\d+)Hz', spec)
                        if match:
                            rate = int(match.group(1))
                            logging.info(f"📊 PulseAudio reports {rate} Hz for {device_name}")
                            return rate
            
            return None
            
        except Exception as e:
            logging.debug(f"Could not query PulseAudio sample rate: {e}")
            return None
    
    def print_diagnostics(self):
        """Print comprehensive audio diagnostics."""
        logging.info("=" * 60)
        logging.info("🎤 AUDIO DEVICE DIAGNOSTICS")
        logging.info("=" * 60)
        
        # Platform info
        logging.info(f"Platform: {platform.system()} {platform.release()}")
        logging.info(f"Machine: {platform.machine()}")
        
        # List all devices
        try:
            devices = sd.query_devices()
            logging.info(f"\n📋 Available Audio Devices ({len(devices)} total):")
            logging.info("-" * 60)
            
            for idx, dev in enumerate(devices):
                marker = ""
                if idx == self.input_device:
                    marker = " ← INPUT SELECTED"
                elif idx == self.output_device:
                    marker = " ← OUTPUT SELECTED"
                    
                logging.info(
                    f"{idx:2d}. {dev['name'][:40]:40s} "
                    f"(in:{dev['max_input_channels']:2d}, out:{dev['max_output_channels']:2d})"
                    f"{marker}"
                )
            
            logging.info("-" * 60)
            
        except Exception as e:
            logging.error(f"❌ Error listing devices: {e}")
        
        # Selected devices
        logging.info("\n🎯 Selected Configuration:")
        logging.info(f"  Input:  Device {self.input_device} - {self.input_name}")
        logging.info(f"  Output: Device {self.output_device} - {self.output_name}")
        logging.info(f"  Sample Rate: {self.sample_rate} Hz")
        
        # Warnings
        if self.input_device is None:
            logging.error("❌ WARNING: No input device selected!")
        if self.output_device is None:
            logging.warning("⚠️  WARNING: No output device selected!")
        
        # Linux-specific diagnostics
        if self.platform == "linux":
            self._linux_diagnostics()
        
        logging.info("=" * 60)
    
    def _linux_diagnostics(self):
        """Run Linux-specific audio diagnostics."""
        logging.info("\n🐧 Linux Audio Diagnostics:")
        logging.info("-" * 60)
        
        try:
            # Run arecord -l
            result = subprocess.run(
                ['arecord', '-l'],
                capture_output=True,
                text=True,
                timeout=5
            )
            logging.info("arecord -l output:")
            for line in result.stdout.split('\n'):
                if line.strip():
                    logging.info(f"  {line}")
        except Exception as e:
            logging.warning(f"Could not run arecord: {e}")
        
        try:
            # Check for PulseAudio
            result = subprocess.run(
                ['pactl', 'list', 'short', 'sources'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                logging.info("\nPulseAudio sources:")
                for line in result.stdout.split('\n')[:5]:  # First 5 lines
                    if line.strip():
                        logging.info(f"  {line}")
        except Exception:
            pass  # PulseAudio may not be installed
    
    def test_microphone(self, duration: float = 2.0) -> Tuple[bool, float]:
        """
        Test microphone by recording audio and checking RMS level.
        
        Parameters
        ----------
        duration : float
            Recording duration in seconds
            
        Returns
        -------
        Tuple[bool, float]
            (success, rms_level)
        """
        if self.input_device is None:
            logging.error("❌ No input device configured for testing")
            return False, 0.0
        
        try:
            logging.info(f"🎤 Testing microphone (device {self.input_device})...")
            logging.info(f"   Recording {duration}s at {self.sample_rate} Hz - SPEAK NOW!")
            
            import numpy as np
            
            recording = sd.rec(
                int(duration * self.sample_rate),
                samplerate=self.sample_rate,
                channels=1,
                device=self.input_device
            )
            sd.wait()
            
            # Calculate RMS
            rms = float(np.sqrt(np.mean(recording**2)))
            max_amplitude = float(np.max(np.abs(recording)))
            
            logging.info(f"   Max amplitude: {max_amplitude:.4f}")
            logging.info(f"   RMS level: {rms:.4f}")
            
            # Threshold for detection
            MIN_RMS = 0.001
            
            if rms > MIN_RMS:
                logging.info(f"✅ Microphone test PASSED (RMS: {rms:.4f})")
                return True, rms
            else:
                logging.error(f"❌ Microphone test FAILED (RMS too low: {rms:.4f} < {MIN_RMS})")
                logging.error("   Check: Is microphone unmuted? Is it selected in system settings?")
                return False, rms
                
        except Exception as e:
            logging.error(f"❌ Microphone test failed: {e}", exc_info=True)
            return False, 0.0
    
    def save_config(self):
        """Save configuration to YAML file."""
        try:
            config = {
                'platform': self.platform,
                'input_device': self.input_device,
                'input_name': self.input_name,
                'output_device': self.output_device,
                'output_name': self.output_name,
                'sample_rate': self.sample_rate,
            }
            
            with open(self.CONFIG_FILE, 'w') as f:
                yaml.dump(config, f, default_flow_style=False)
            
            logging.info(f"💾 Saved audio config to {self.CONFIG_FILE}")
            
        except Exception as e:
            logging.warning(f"Could not save config: {e}")
    
    def load_config(self) -> bool:
        """
        Load configuration from YAML file.
        
        Returns
        -------
        bool
            True if config loaded successfully
        """
        try:
            if not self.CONFIG_FILE.exists():
                return False
            
            with open(self.CONFIG_FILE, 'r') as f:
                config = yaml.safe_load(f)
            
            # Only load if platform matches
            if config.get('platform') == self.platform:
                self.input_device = config.get('input_device')
                self.input_name = config.get('input_name', 'Unknown')
                self.output_device = config.get('output_device')
                self.output_name = config.get('output_name', 'Unknown')
                self.sample_rate = config.get('sample_rate', 16000)
                
                logging.info(f"📂 Loaded audio config from {self.CONFIG_FILE}")
                return True
            else:
                logging.warning(f"Config platform mismatch: {config.get('platform')} != {self.platform}")
                return False
                
        except Exception as e:
            logging.warning(f"Could not load config: {e}")
            return False


def get_audio_config(force_detect: bool = False) -> AudioConfig:
    """
    Get audio configuration, loading from file or detecting devices.
    
    Parameters
    ----------
    force_detect : bool
        Force device detection even if config file exists
        
    Returns
    -------
    AudioConfig
        Configured audio settings
    """
    config = AudioConfig()
    
    # Try to load existing config
    if not force_detect and config.load_config():
        logging.info("Using saved audio configuration")
    else:
        # Detect devices
        config.detect_devices()
        config.save_config()
    
    # Print diagnostics
    config.print_diagnostics()
    
    # Test microphone
    if config.input_device is not None:
        success, rms = config.test_microphone(duration=2.0)
        if not success:
            logging.error("⚠️  MICROPHONE TEST FAILED - Audio input may not work!")
    
    return config
