#!/usr/bin/env python3
"""
Audio diagnostics script for Astra Vein Receptionist agent.

Run this before starting the agent to ensure proper audio device configuration.

For Jetson Orin, includes low-level ALSA/PulseAudio verification.
"""

import sys
import platform
import subprocess
import re
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils.audio_config import get_audio_config


def run_command(cmd, timeout=5):
    """Run a shell command and return output."""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.stdout, result.stderr, result.returncode
    except subprocess.TimeoutExpired:
        return "", "Command timed out", -1
    except Exception as e:
        return "", str(e), -1


def check_alsa_devices():
    """Check ALSA devices on Linux (Jetson Orin)."""
    print("\n" + "="*70)
    print("🔍 ALSA DEVICE DETECTION (Low-Level)")
    print("="*70)
    
    # List all capture devices
    stdout, stderr, code = run_command("arecord -l")
    
    if code != 0:
        print("⚠️  arecord not available (not on Linux or ALSA not installed)")
        return None
    
    print("\n📋 Available capture devices:")
    print(stdout)
    
    # Parse for USB Audio Device
    usb_device_pattern = r'card (\d+):.*USB.*device (\d+):'
    matches = re.findall(usb_device_pattern, stdout, re.IGNORECASE)
    
    if matches:
        card, device = matches[0]
        hw_string = f"hw:{card},{device}"
        print(f"\n✅ Found USB Audio Device: {hw_string}")
        return hw_string
    else:
        print("\n⚠️  No USB Audio Device found in arecord output")
        return None


def check_kernel_audio():
    """Check kernel audio messages on Linux."""
    print("\n" + "="*70)
    print("🔍 KERNEL AUDIO MESSAGES")
    print("="*70)
    
    stdout, stderr, code = run_command("sudo dmesg | grep -i audio | tail -20")
    
    if code != 0:
        print("⚠️  Cannot access dmesg (need sudo or not on Linux)")
        return
    
    if stdout.strip():
        print("\n📋 Recent audio kernel messages:")
        print(stdout)
    else:
        print("ℹ️  No recent audio kernel messages")


def test_alsa_recording(hw_device, duration=2):
    """Test ALSA recording with arecord."""
    print("\n" + "="*70)
    print(f"🎤 TESTING ALSA RECORDING ({duration}s)")
    print("="*70)
    
    if not hw_device:
        print("⚠️  No ALSA device specified, skipping test")
        return False
    
    test_file = "/tmp/alsa_test.wav"
    
    print(f"\n🎙️  Recording {duration}s from {hw_device}...")
    print("SPEAK NOW!")
    
    stdout, stderr, code = run_command(
        f"arecord -D {hw_device} -f cd -d {duration} {test_file}",
        timeout=duration + 5
    )
    
    if code != 0:
        print(f"❌ Recording failed: {stderr}")
        return False
    
    print("✅ Recording complete!")
    
    # Check file size
    try:
        import os
        size = os.path.getsize(test_file)
        print(f"📊 File size: {size} bytes")
        
        if size < 1000:
            print("⚠️  File size very small - may be silent")
            return False
        
        # Analyze audio with numpy if available
        try:
            import wave
            import numpy as np
            
            with wave.open(test_file, 'rb') as wf:
                frames = wf.readframes(wf.getnframes())
                audio = np.frombuffer(frames, dtype=np.int16)
                
                max_amp = np.max(np.abs(audio))
                rms = np.sqrt(np.mean(audio.astype(float)**2))
                
                print(f"📊 Max amplitude: {max_amp}")
                print(f"📊 RMS level: {rms:.2f}")
                
                if rms < 100:
                    print("⚠️  RMS very low - check mixer levels or mic mute")
                    return False
                else:
                    print("✅ Audio signal detected!")
                    return True
                    
        except ImportError:
            print("ℹ️  NumPy not available for audio analysis")
            return True
            
    except Exception as e:
        print(f"⚠️  Error analyzing recording: {e}")
        return False


def check_alsamixer_levels(hw_device):
    """Check ALSA mixer levels."""
    print("\n" + "="*70)
    print("🎚️  ALSA MIXER LEVELS")
    print("="*70)
    
    if not hw_device:
        print("⚠️  No ALSA device specified, skipping mixer check")
        return
    
    # Extract card number
    card_match = re.search(r'hw:(\d+)', hw_device)
    if not card_match:
        print("⚠️  Cannot parse card number from device")
        return
    
    card = card_match.group(1)
    
    # Get mixer controls
    stdout, stderr, code = run_command(f"amixer -c {card} scontents")
    
    if code != 0:
        print(f"⚠️  Cannot read mixer: {stderr}")
        print("\n💡 TIP: Run 'alsamixer' manually:")
        print(f"   1. Press F6 → select card {card} (USB Audio)")
        print("   2. Press F4 to show capture controls")
        print("   3. Unmute 'Mic' and 'Capture' with M key")
        print("   4. Raise levels to 70% or higher")
        return
    
    print(f"\n📋 Mixer controls for card {card}:")
    
    # Parse for capture controls
    muted_controls = []
    low_volume_controls = []
    
    for line in stdout.split('\n'):
        if 'Capture' in line or 'Mic' in line:
            print(f"  {line}")
            if '[off]' in line:
                control_match = re.search(r"Simple mixer control '([^']+)'", line)
                if control_match:
                    muted_controls.append(control_match.group(1))
            
            # Check for low volume levels
            vol_match = re.search(r'\[(\d+)%\]', line)
            if vol_match and int(vol_match.group(1)) < 50:
                control_match = re.search(r"Simple mixer control '([^']+)'", line)
                if control_match:
                    low_volume_controls.append(control_match.group(1))
    
    if muted_controls:
        print(f"\n⚠️  MUTED controls detected: {', '.join(muted_controls)}")
        print("   Run 'alsamixer' and press M to unmute")
    
    if low_volume_controls:
        print(f"\n⚠️  LOW volume controls: {', '.join(low_volume_controls)}")
        print("   Increase levels in 'alsamixer' to 70% or higher")
    
    if not muted_controls and not low_volume_controls:
        print("\n✅ Mixer levels look good!")


def check_pulseaudio():
    """Check PulseAudio configuration."""
    print("\n" + "="*70)
    print("🔊 PULSEAUDIO CONFIGURATION")
    print("="*70)
    
    # Check if PulseAudio is running
    stdout, stderr, code = run_command("pactl info")
    
    if code != 0:
        print("⚠️  PulseAudio not running or not available")
        print("   Start with: pulseaudio --start")
        return None
    
    print("✅ PulseAudio is running")
    
    # List sources
    stdout, stderr, code = run_command("pactl list short sources")
    
    if code != 0:
        print(f"⚠️  Cannot list sources: {stderr}")
        return None
    
    print("\n📋 Available audio sources:")
    print(stdout)
    
    # Get default source
    stdout, stderr, code = run_command("pactl get-default-source")
    
    if code == 0:
        default_source = stdout.strip()
        print(f"\n✅ Default source: {default_source}")
        
        # Check if it's a USB device
        if 'usb' not in default_source.lower():
            print("⚠️  Default source is not a USB device!")
            print("\n💡 To set USB mic as default:")
            print("   pactl list short sources  # Find your USB device name")
            print("   pactl set-default-source alsa_input.usb-<YourDevice>-00.mono-fallback")
        
        return default_source
    else:
        print("⚠️  Cannot get default source")
        return None


def test_pulseaudio_recording(duration=2):
    """Test PulseAudio recording."""
    print("\n" + "="*70)
    print(f"🎤 TESTING PULSEAUDIO RECORDING ({duration}s)")
    print("="*70)
    
    # Get default source
    stdout, stderr, code = run_command("pactl get-default-source")
    
    if code != 0:
        print("⚠️  Cannot get default source, skipping test")
        return False
    
    source = stdout.strip()
    test_file = "/tmp/pulse_test.wav"
    
    print(f"\n🎙️  Recording {duration}s from {source}...")
    print("SPEAK NOW!")
    
    # Use parecord for recording
    stdout, stderr, code = run_command(
        f"timeout {duration + 1} parecord --device={source} --format=s16le --rate=16000 --channels=1 {test_file}",
        timeout=duration + 5
    )
    
    if code not in [0, 124]:  # 124 is timeout exit code (expected)
        print(f"❌ Recording failed: {stderr}")
        return False
    
    print("✅ Recording complete!")
    
    # Check file
    try:
        import os
        size = os.path.getsize(test_file)
        print(f"📊 File size: {size} bytes")
        
        if size < 1000:
            print("⚠️  File size very small - PulseAudio routing may be broken")
            return False
        else:
            print("✅ PulseAudio capture working!")
            return True
            
    except Exception as e:
        print(f"⚠️  Error checking file: {e}")
        return False


def show_jetson_fixes_table():
    """Display common Jetson Orin audio fixes."""
    print("\n" + "="*70)
    print("🔧 COMMON JETSON ORIN AUDIO FIXES")
    print("="*70)
    
    fixes = [
        ("USB mic not detected after boot", "Plug in BEFORE boot or: sudo systemctl restart pulseaudio"),
        ("No sound in Docker", "Add: --device /dev/snd and mount /run/user/1000/pulse"),
        ("Wrong sample rate errors", "Use 16000 Hz for Whisper/Piper on Jetson"),
        ("PipeWire interfering", "Disable PipeWire or use: pw-cli"),
        ("Permission denied /dev/snd", "Add user to 'audio' group: sudo usermod -aG audio $USER"),
        ("Mic muted in ALSA", "Run 'alsamixer', press F6 (USB card), F4 (capture), M (unmute)"),
        ("Low audio levels", "In alsamixer: increase Capture and Mic to 70%+"),
        ("PulseAudio won't start", "killall pulseaudio && pulseaudio --start"),
    ]
    
    print("\n{:<35} | {}".format("ISSUE", "FIX"))
    print("-" * 70)
    for issue, fix in fixes:
        print("{:<35} | {}".format(issue, fix))


def jetson_diagnostics():
    """Run comprehensive Jetson Orin audio diagnostics."""
    print("\n" + "="*70)
    print("🤖 JETSON ORIN AUDIO DIAGNOSTICS")
    print("="*70)
    
    # Check if we're on Linux
    if platform.system() != "Linux":
        print("ℹ️  Not on Linux - skipping Jetson-specific diagnostics")
        return True
    
    # Step 1: Check kernel messages
    check_kernel_audio()
    
    # Step 2: Detect ALSA devices
    hw_device = check_alsa_devices()
    
    # Step 3: Check mixer levels
    if hw_device:
        check_alsamixer_levels(hw_device)
    
    # Step 4: Test ALSA recording
    alsa_ok = False
    if hw_device:
        alsa_ok = test_alsa_recording(hw_device, duration=2)
    
    # Step 5: Check PulseAudio
    default_source = check_pulseaudio()
    
    # Step 6: Test PulseAudio recording
    pulse_ok = False
    if default_source:
        pulse_ok = test_pulseaudio_recording(duration=2)
    
    # Step 7: Show fixes table
    show_jetson_fixes_table()
    
    # Final verdict
    print("\n" + "="*70)
    print("📊 JETSON DIAGNOSTICS SUMMARY")
    print("="*70)
    
    if alsa_ok and pulse_ok:
        print("✅ All audio tests PASSED!")
        print("   Agent should work correctly with microphone input.")
        return True
    elif alsa_ok and not pulse_ok:
        print("⚠️  ALSA works but PulseAudio has issues")
        print("   Agent may work, but check PulseAudio routing")
        return True
    elif not alsa_ok and pulse_ok:
        print("⚠️  PulseAudio works but ALSA test failed")
        print("   This is unusual - check mixer levels")
        return True
    else:
        print("❌ Audio tests FAILED")
        print("   Fix issues above before starting agent")
        return False


def main():
    """Run audio diagnostics."""
    print("\n" + "="*70)
    print("🎙️  ASTRA VEIN RECEPTIONIST - AUDIO DIAGNOSTICS")
    print("="*70 + "\n")
    
    # Run Jetson-specific diagnostics if on Linux
    if platform.system() == "Linux":
        jetson_ok = jetson_diagnostics()
        if not jetson_ok:
            print("\n❌ Jetson diagnostics failed - fix issues before continuing")
    
    # Force device detection
    config = get_audio_config(force_detect=True)
    
    print("\n" + "="*70)
    print("📋 DIAGNOSTIC SUMMARY")
    print("="*70)
    
    if config.input_device is not None:
        print(f"✅ Input device configured: {config.input_device} - {config.input_name}")
    else:
        print("❌ NO INPUT DEVICE FOUND!")
        print("   Expected: USB PnP Sound Device")
        print("   Action: Check USB connections and permissions")
    
    if config.output_device is not None:
        print(f"✅ Output device configured: {config.output_device} - {config.output_name}")
    else:
        print("⚠️  No output device found")
        print("   Expected: USB 2.0 Speaker")
    
    print(f"\n📊 Sample rate: {config.sample_rate} Hz")
    print(f"💾 Config saved to: {config.CONFIG_FILE}")
    
    print("\n" + "="*70)
    print("🚀 NEXT STEPS")
    print("="*70)
    
    if config.input_device is None:
        print("❌ Cannot start agent without input device!")
        print("\nTroubleshooting:")
        print("1. Connect USB PnP Sound Device microphone")
        print("2. Check system audio permissions")
        print("3. On macOS: System Settings → Privacy → Microphone → Enable Terminal")
        print("4. Run this diagnostic again")
        return 1
    else:
        print("✅ Audio configuration complete!")
        print("\nStart the agent with:")
        print("  uv run src/run.py astra_vein_receptionist")
        return 0


if __name__ == "__main__":
    sys.exit(main())
