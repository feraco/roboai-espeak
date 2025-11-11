# Astra Vein Receptionist - Audio Configuration Guide

## Overview

The Astra Vein Receptionist agent uses a robust audio configuration system that automatically detects and configures audio devices across macOS and Linux (Jetson Orin) platforms.

## Quick Start

### 1. Run Audio Diagnostics

Before starting the agent, run diagnostics to verify your audio configuration:

```bash
python3 diagnostics_audio.py
```

This will:
- Detect all audio devices
- Auto-select USB PnP Sound Device (microphone) and USB 2.0 Speaker
- Test microphone input (2-second recording)
- Save configuration to `device_config.yaml`
- Display detailed diagnostic information

### 2. Start the Agent with Diagnostics

Use the startup script for automatic diagnostics and agent launch:

```bash
python3 start_astra_agent.py
```

Or use the standard method:

```bash
uv run src/run.py astra_vein_receptionist
```

## Audio Device Configuration

### Target Devices

**Input (Microphone):** USB PnP Sound Device
- Auto-detected by name across platforms
- Sample rate: 48000 Hz (macOS), 16000 Hz (Linux)
- Used for speech recognition (Faster-Whisper)

**Output (Speaker):** USB 2.0 Speaker
- Auto-detected by name
- Sample rate: 22050 Hz (Piper TTS)
- Note: On Jetson, this device may incorrectly show input channels - the system handles this automatically

### Configuration Files

**`device_config.yaml`** - Persistent device configuration
- Saved after first detection
- Platform-specific (separate configs for macOS/Linux)
- Contains device IDs, names, and sample rates
- Regenerate by running diagnostics with `--force` flag

**`config/astra_vein_receptionist.json5`** - Agent configuration
- `input_device: null` - Triggers auto-detection by name
- Or specify device ID: `input_device: 2`
- Sample rate and other audio parameters

## Platform-Specific Notes

### macOS

**Permissions:**
- System Settings → Privacy & Security → Microphone
- Enable microphone access for Terminal.app

**USB Devices:**
- USB PnP Sound Device typically uses 48000 Hz sample rate
- Auto-detected as device 2 (may vary)

**Testing:**
```bash
python3 test_microphone.py
```

### Linux (Jetson Orin)

**Permissions:**
- User must be in `audio` group: `sudo usermod -a -G audio $USER`
- May need to restart session after adding

**ALSA Configuration:**
- List devices: `arecord -l`
- USB PnP Sound Device typically shows as card 1, device 0
- USB 2.0 Speaker may incorrectly show input channels (handled automatically)

**PulseAudio:**
- List sources: `pactl list short sources`
- Check default: `pactl info`

**Testing:**
```bash
python3 test_microphone.py
arecord -d 3 -f cd test.wav  # 3-second test recording
```

## Troubleshooting

### No Input Detected

**Symptoms:**
```
WARNING - Fuser: No input detected in buffers: [None]
INFO - === INPUT STATUS ===
No input detected
```

**Solutions:**

1. **Run diagnostics:**
   ```bash
   python3 diagnostics_audio.py
   ```

2. **Check USB connection:**
   - Unplug and replug USB PnP Sound Device
   - Verify with `arecord -l` (Linux) or System Settings (macOS)

3. **Check permissions:**
   - macOS: Enable Terminal in Microphone privacy settings
   - Linux: Add user to audio group, restart session

4. **Force device detection:**
   - Edit `config/astra_vein_receptionist.json5`
   - Set `input_device: 2` (or appropriate device ID)
   - Get ID from diagnostics output

5. **Check sample rate:**
   - macOS USB devices often need 48000 Hz
   - Jetson works with 16000 Hz
   - Diagnostics auto-selects optimal rate

6. **Test microphone directly:**
   ```bash
   python3 -c "
   import sounddevice as sd
   import numpy as np
   
   print('Recording 5 seconds...')
   recording = sd.rec(int(5 * 48000), samplerate=48000, channels=1, device=2)
   sd.wait()
   print(f'Max amplitude: {np.max(np.abs(recording)):.4f}')
   "
   ```

### Wrong Device Selected

**Symptoms:**
```
INFO - LocalASRInput: auto-selected input device 1 (iPhone Microphone)
```

**Solutions:**

1. **Use audio config system:**
   - Removes `device_config.yaml`
   - Run `python3 diagnostics_audio.py`
   - System will detect USB PnP Sound Device by name

2. **Or specify device explicitly:**
   - Edit `config/astra_vein_receptionist.json5`
   - Set `input_device: 2` (your USB PnP device ID)

### Jetson-Specific: Speaker Shows as Input

**Expected behavior:**
```
WARNING - ⚠️  Jetson quirk: USB 2.0 Speaker shows as input device 1
INFO - ✅ Override: Using device 1 as OUTPUT - USB 2.0 Speaker
```

This is handled automatically by the audio configuration system. No action needed.

### Low RMS Level / Quiet Mic

**Symptoms:**
```
❌ Microphone test FAILED (RMS too low: 0.0003 < 0.001)
```

**Solutions:**

1. **Increase amplification:**
   Edit `config/astra_vein_receptionist.json5`:
   ```json5
   "amplify_audio": 5.0,  // Increase from 3.0
   ```

2. **Adjust VAD threshold:**
   ```json5
   "silence_threshold": 0.01,  // Decrease from 0.02 (more sensitive)
   ```

3. **Check system volume:**
   - macOS: System Settings → Sound → Input → Input Level
   - Linux: `alsamixer` - adjust capture level

## Audio System Architecture

### Components

1. **`src/utils/audio_config.py`** - Device detection and configuration
   - Auto-detects devices by name (USB PnP Sound Device, USB 2.0 Speaker)
   - Handles platform differences (macOS 48kHz, Linux 16kHz)
   - Tests microphone with RMS level verification
   - Saves/loads persistent configuration

2. **`src/inputs/plugins/local_asr.py`** - Speech recognition input
   - Uses audio_config for device selection
   - Falls back to manual detection if needed
   - Supports Faster-Whisper (offline) and OpenAI Whisper (cloud)
   - Multi-language support (English, Spanish, Russian)

3. **`diagnostics_audio.py`** - Standalone diagnostics tool
   - Lists all audio devices
   - Platform-specific tests (arecord, pactl)
   - Microphone recording test
   - Configuration validation

4. **`start_astra_agent.py`** - Integrated startup script
   - Runs diagnostics automatically
   - Verifies configuration
   - Starts agent only if devices configured correctly

### Data Flow

```
USB PnP Sound Device (Hardware)
    ↓
sounddevice library (Python)
    ↓
audio_config.py (Device Selection)
    ↓
local_asr.py (Speech Recognition)
    ↓
Faster-Whisper (ASR Engine)
    ↓
Fuser (Prompt Generation)
    ↓
Ollama LLM (llama3.2:3b)
    ↓
Piper TTS (Multi-language)
    ↓
USB 2.0 Speaker (Hardware)
```

## Configuration Reference

### Audio Config (device_config.yaml)

```yaml
platform: darwin  # or linux
input_device: 2
input_name: USB PnP Sound Device
output_device: 3
output_name: USB 2.0 Speaker
sample_rate: 48000
```

### Agent Config (astra_vein_receptionist.json5)

```json5
{
  agent_inputs: [
    {
      type: "LocalASRInput",
      config: {
        engine: "faster-whisper",
        model_size: "base",
        input_device: null,      // Auto-detect by name
        sample_rate: 16000,      // Override if needed
        amplify_audio: 3.0,
        silence_threshold: 0.02,
        vad_filter: true
      }
    }
  ]
}
```

## Verification Checklist

- [ ] `diagnostics_audio.py` runs without errors
- [ ] Input device shows as "USB PnP Sound Device"
- [ ] Output device shows as "USB 2.0 Speaker" (if available)
- [ ] Microphone test passes (RMS > 0.001)
- [ ] `device_config.yaml` created successfully
- [ ] Agent starts without "No input detected" warnings
- [ ] Audio recording shows non-zero RMS in logs
- [ ] TTS plays through USB 2.0 Speaker
- [ ] Vision detection works (face/emotion)
- [ ] Full INPUT → LLM → OUTPUT cycle completes

## Support

For persistent issues:

1. **Check logs:** Structured logging shows each INPUT/OUTPUT cycle
2. **Test hardware:** Use system tools (Audio MIDI Setup, alsamixer)
3. **Verify USB:** Try different USB ports
4. **Platform differences:** macOS and Jetson use different sample rates
5. **Update firmware:** USB audio devices may need firmware updates

## See Also

- `.github/copilot-instructions.md` - Developer guide
- `test_microphone.py` - Hardware testing script
- `documentation/troubleshooting/` - Platform-specific guides
