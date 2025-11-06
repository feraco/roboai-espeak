"""
Audio validation utilities for agent startup.

Ensures microphone is working before starting the agent runtime.
"""

import logging
import platform
import subprocess
import re
from pathlib import Path

logger = logging.getLogger(__name__)


def quick_mic_test(device_index=None, duration=1, threshold=0.01):
    """
    Quick microphone test to verify audio input is working.
    
    Parameters
    ----------
    device_index : int, optional
        Audio device index to test. If None, uses system default.
    duration : float
        Recording duration in seconds
    threshold : float
        Minimum RMS threshold to consider audio valid
        
    Returns
    -------
    bool
        True if microphone is working, False otherwise
    """
    try:
        import sounddevice as sd
        import numpy as np
        
        logger.info(f"Testing microphone (device {device_index}, {duration}s)...")
        
        # Record audio
        recording = sd.rec(
            int(duration * 16000),
            samplerate=16000,
            channels=1,
            device=device_index,
            dtype='float32'
        )
        sd.wait()
        
        # Analyze audio
        rms = np.sqrt(np.mean(recording**2))
        max_amp = np.max(np.abs(recording))
        
        logger.debug(f"Audio test results: RMS={rms:.4f}, Max={max_amp:.4f}")
        
        if rms < threshold and max_amp < threshold:
            logger.warning(f"⚠️  No audio detected (RMS={rms:.4f}, Max={max_amp:.4f})")
            logger.warning("   Microphone may be muted or not working")
            return False
        
        logger.info(f"✅ Microphone test passed (RMS={rms:.4f})")
        return True
        
    except Exception as e:
        logger.error(f"❌ Microphone test failed: {e}")
        return False


def check_alsa_device_exists():
    """
    Check if ALSA detects a USB audio device (Jetson Orin).
    
    Returns
    -------
    tuple[bool, str | None]
        (success, hw_device_string) e.g., (True, "hw:1,0")
    """
    if platform.system() != "Linux":
        return True, None  # Not applicable
    
    try:
        result = subprocess.run(
            ["arecord", "-l"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode != 0:
            logger.warning("⚠️  arecord command failed - ALSA may not be available")
            return False, None
        
        # Parse for USB Audio Device
        usb_pattern = r'card (\d+):.*USB.*device (\d+):'
        matches = re.findall(usb_pattern, result.stdout, re.IGNORECASE)
        
        if matches:
            card, device = matches[0]
            hw_device = f"hw:{card},{device}"
            logger.info(f"✅ Found ALSA USB device: {hw_device}")
            return True, hw_device
        else:
            logger.warning("⚠️  No USB audio device found in arecord output")
            logger.debug(f"arecord output:\n{result.stdout}")
            return False, None
            
    except FileNotFoundError:
        logger.debug("arecord not found - not on Linux or ALSA not installed")
        return True, None  # Not fatal if not on Linux
    except Exception as e:
        logger.error(f"❌ Error checking ALSA devices: {e}")
        return False, None


def check_pulseaudio_default_source():
    """
    Check if PulseAudio has a valid default source (Jetson Orin).
    
    Returns
    -------
    tuple[bool, str | None]
        (success, default_source_name)
    """
    if platform.system() != "Linux":
        return True, None  # Not applicable
    
    try:
        result = subprocess.run(
            ["pactl", "get-default-source"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode != 0:
            logger.warning("⚠️  PulseAudio not running or pactl failed")
            return False, None
        
        source = result.stdout.strip()
        
        if not source:
            logger.warning("⚠️  No default PulseAudio source set")
            return False, None
        
        logger.info(f"✅ PulseAudio default source: {source}")
        
        # Warn if not USB
        if 'usb' not in source.lower():
            logger.warning(f"⚠️  Default source '{source}' is not USB device")
            logger.warning("   Consider setting USB mic as default:")
            logger.warning("   pactl set-default-source alsa_input.usb-<YourDevice>-00.mono-fallback")
        
        return True, source
        
    except FileNotFoundError:
        logger.debug("pactl not found - PulseAudio not installed")
        return True, None  # Not fatal
    except Exception as e:
        logger.error(f"❌ Error checking PulseAudio: {e}")
        return False, None


def validate_audio_before_start(device_index=None, skip_test=False):
    """
    Comprehensive audio validation before agent startup.
    
    This should be called before starting the agent runtime to ensure
    the microphone is working properly.
    
    Parameters
    ----------
    device_index : int, optional
        Audio device index to test
    skip_test : bool
        Skip the actual recording test (for headless environments)
        
    Returns
    -------
    bool
        True if audio is valid, False otherwise
    """
    logger.info("=" * 70)
    logger.info("🎙️  PRE-START AUDIO VALIDATION")
    logger.info("=" * 70)
    
    validation_passed = True
    
    # Step 1: Check ALSA (Linux/Jetson only)
    if platform.system() == "Linux":
        alsa_ok, hw_device = check_alsa_device_exists()
        if not alsa_ok:
            logger.error("❌ ALSA device check failed")
            logger.error("   Run 'diagnostics_audio.py' for detailed diagnostics")
            validation_passed = False
        
        # Step 2: Check PulseAudio (Linux/Jetson only)
        pulse_ok, source = check_pulseaudio_default_source()
        if not pulse_ok:
            logger.warning("⚠️  PulseAudio check failed - may affect audio routing")
            # Not fatal, continue
    
    # Step 3: Quick microphone test
    if not skip_test:
        mic_ok = quick_mic_test(device_index, duration=1, threshold=0.005)
        if not mic_ok:
            logger.error("❌ Microphone test failed - no audio input detected")
            logger.error("   Possible causes:")
            logger.error("   - Microphone is muted in alsamixer")
            logger.error("   - USB device not plugged in or not recognized")
            logger.error("   - Wrong device selected in configuration")
            logger.error("   - Permissions issue (add user to 'audio' group)")
            logger.error("\n   Run 'python diagnostics_audio.py' for detailed diagnostics")
            validation_passed = False
    else:
        logger.info("ℹ️  Skipping microphone test (skip_test=True)")
    
    logger.info("=" * 70)
    
    if validation_passed:
        logger.info("✅ Audio validation PASSED - starting agent")
    else:
        logger.error("❌ Audio validation FAILED - cannot start agent")
        logger.error("   Fix audio issues before starting")
    
    logger.info("=" * 70)
    
    return validation_passed


def log_audio_troubleshooting_tips():
    """Log common troubleshooting tips for audio issues."""
    logger.info("\n" + "=" * 70)
    logger.info("🔧 AUDIO TROUBLESHOOTING TIPS")
    logger.info("=" * 70)
    
    if platform.system() == "Linux":
        logger.info("\nJetson Orin / Linux:")
        logger.info("  1. Check USB connection: lsusb | grep -i audio")
        logger.info("  2. Check ALSA devices: arecord -l")
        logger.info("  3. Check mixer levels: alsamixer (F6 → USB card, F4 → capture)")
        logger.info("  4. Test recording: arecord -D hw:1,0 -f cd test.wav")
        logger.info("  5. Check PulseAudio: pactl list short sources")
        logger.info("  6. Restart PulseAudio: pulseaudio --kill && pulseaudio --start")
        logger.info("  7. Add to audio group: sudo usermod -aG audio $USER")
    else:
        logger.info("\nmacOS:")
        logger.info("  1. Check device list: python test_microphone.py")
        logger.info("  2. Check permissions: System Settings → Privacy → Microphone")
        logger.info("  3. Check Audio MIDI Setup app")
        logger.info("  4. Try different USB ports")
        logger.info("  5. Restart audio service: sudo killall coreaudiod")
    
    logger.info("\nGeneral:")
    logger.info("  1. Run diagnostics: python diagnostics_audio.py")
    logger.info("  2. Check config file: device_config.yaml")
    logger.info("  3. Test with: python test_microphone.py")
    logger.info("  4. Verify USB device is recognized by OS")
    logger.info("  5. Try a different USB microphone")
    
    logger.info("=" * 70 + "\n")
