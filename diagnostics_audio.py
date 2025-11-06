#!/usr/bin/env python3
"""
System diagnostics script for Astra Vein Receptionist agent.

Run this before starting the agent to ensure proper configuration:
- Audio devices (microphone, speaker)
- Camera (Intel RealSense D435i)
- Ollama LLM service

For Jetson Orin, includes low-level ALSA/PulseAudio verification.
"""

import sys
import platform
import subprocess
import re
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from utils.audio_config import get_audio_config
from utils.camera_config import get_camera_config


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


def check_ollama():
    """Check Ollama status and manage service."""
    print("\n" + "="*70)
    print("🤖 OLLAMA LLM SERVICE")
    print("="*70)
    
    # Check system memory first
    print("\n📊 System Memory Check:")
    stdout, stderr, code = run_command("free -h")
    if code == 0:
        lines = stdout.split('\n')
        for line in lines[:2]:  # Show header and Mem line
            print(f"   {line}")
    
    # Check if Ollama is running
    stdout, stderr, code = run_command("ollama list")
    
    if code != 0:
        print("\n❌ Ollama not running or not installed")
        print("\n💡 To install Ollama:")
        print("   curl -fsSL https://ollama.ai/install.sh | sh")
        return False
    
    print("\n✅ Ollama is running")
    
    # List installed models
    print("\n📋 Installed models:")
    print(stdout)
    
    # Check for required model
    has_model = "llama3.1:8b" in stdout
    if has_model:
        print("✅ Required model llama3.1:8b is installed")
    else:
        print("⚠️  Required model llama3.1:8b NOT found")
        print("   Install with: ollama pull llama3.1:8b")
    
    # Check Ollama service status
    print("\n🔍 Checking Ollama service status...")
    stdout, stderr, code = run_command("systemctl status ollama --no-pager -l", timeout=5)
    if code == 0:
        # Look for errors in recent logs
        if "500" in stdout or "499" in stdout or "Load failed" in stdout:
            print("⚠️  Ollama service has errors:")
            for line in stdout.split('\n'):
                if any(err in line for err in ["500", "499", "Load failed", "error", "ERROR"]):
                    print(f"   {line.strip()}")
            print("\n   💡 This indicates model loading issues - will clear cache and restart")
    
    # Clear Ollama cache and runtime data
    print("\n🧹 Clearing Ollama cache and runtime data...")
    
    # Stop Ollama
    print("   1. Stopping Ollama service...")
    run_command("sudo systemctl stop ollama", timeout=15)
    import time
    time.sleep(2)  # Give it time to stop
    
    # Kill any remaining ollama processes
    print("   2. Ensuring all Ollama processes stopped...")
    run_command("sudo pkill -9 ollama", timeout=5)
    time.sleep(1)
    
    # Clear cache and runtime directories
    cache_locations = [
        Path.home() / ".ollama" / "cache",
        Path.home() / ".ollama" / "tmp",
        Path("/tmp") / "ollama*",
        Path("/usr/share/ollama/.ollama/cache") if Path("/usr/share/ollama/.ollama").exists() else None
    ]
    
    for cache_dir in cache_locations:
        if cache_dir is None:
            continue
        if "*" in str(cache_dir):
            # Wildcard pattern
            print(f"   3. Clearing: {cache_dir}")
            run_command(f"rm -rf {cache_dir}", timeout=10)
        elif cache_dir.exists():
            print(f"   3. Clearing: {cache_dir}")
            run_command(f"rm -rf {cache_dir}/*", timeout=10)
    
    print("   ✅ Cache and runtime data cleared")
    
    # Clear systemd failed state if exists
    print("   4. Resetting systemd state...")
    run_command("sudo systemctl reset-failed ollama", timeout=5)
    
    # Restart Ollama
    print("   5. Starting Ollama service...")
    stdout, stderr, code = run_command("sudo systemctl start ollama", timeout=15)
    
    if code == 0:
        time.sleep(3)  # Wait for service to fully start
        
        # Verify it's actually running
        stdout, stderr, code = run_command("systemctl is-active ollama", timeout=5)
        if code == 0 and "active" in stdout:
            print("   ✅ Ollama restarted successfully")
            
            # Test model loading if model exists
            if has_model:
                print("\n🧪 Testing model loading...")
                print("   Sending test prompt to verify model loads correctly...")
                stdout, stderr, code = run_command(
                    'ollama run llama3.1:8b "Hi" --verbose',
                    timeout=30
                )
                if code == 0:
                    print("   ✅ Model loads and responds correctly")
                else:
                    print(f"   ⚠️  Model test failed: {stderr}")
                    print("   This may indicate insufficient memory or corrupted model")
                    print("   Try: ollama pull llama3.1:8b  (to re-download)")
            
            return True
        else:
            print(f"   ⚠️  Ollama service not active: {stdout}")
            return False
    else:
        print(f"   ❌ Ollama restart failed: {stderr}")
        print("\n💡 Manual troubleshooting:")
        print("   1. Check logs: sudo journalctl -u ollama -n 50")
        print("   2. Check memory: free -h")
        print("   3. Try manual start: ollama serve")
        print("   4. Re-pull model: ollama pull llama3.1:8b")
        return False


def check_camera():
    """Check camera configuration."""
    print("\n" + "="*70)
    print("📷 CAMERA CONFIGURATION")
    print("="*70)
    
    try:
        camera_config = get_camera_config(force_detect=True)
        
        if camera_config.camera_index is not None:
            print(f"✅ Camera detected: {camera_config.camera_name}")
            print(f"   Index: {camera_config.camera_index}")
            print(f"   Resolution: {camera_config.width}x{camera_config.height}")
            return True
        else:
            print("⚠️  No camera detected")
            print("   Intel RealSense D435i is recommended for face detection")
            return False
            
    except Exception as e:
        print(f"❌ Camera check failed: {e}")
        return False


def main():
    """Run system diagnostics."""
    print("\n" + "="*70)
    print("🎙️  ASTRA VEIN RECEPTIONIST - SYSTEM DIAGNOSTICS")
    print("="*70 + "\n")
    
    # Check Ollama first (clear cache and restart)
    print("🔧 Step 1: Ollama LLM Service")
    ollama_ok = check_ollama()
    
    # Check camera
    print("\n🔧 Step 2: Camera Detection")
    camera_ok = check_camera()
    
    # Run Jetson-specific diagnostics if on Linux
    print("\n🔧 Step 3: Audio System")
    if platform.system() == "Linux":
        jetson_ok = jetson_diagnostics()
        if not jetson_ok:
            print("\n❌ Jetson audio diagnostics failed - fix issues before continuing")
    
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
