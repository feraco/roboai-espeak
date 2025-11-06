# Jetson Orin Audio Setup & Troubleshooting Guide

## Quick Start - Audio Verification

### 1. Run Comprehensive Diagnostics

```bash
python diagnostics_audio.py
```

This will automatically run:
- ✅ ALSA device detection
- ✅ Kernel audio message check
- ✅ ALSA mixer level verification
- ✅ PulseAudio configuration check
- ✅ Live recording tests (ALSA + PulseAudio)
- ✅ Audio signal analysis (RMS/amplitude)

### 2. Start Agent (with automatic audio validation)

```bash
uv run src/run.py astra_vein_receptionist
```

The agent will automatically:
1. Check for ALSA USB devices
2. Verify PulseAudio default source
3. Run a quick microphone test
4. **Abort if audio validation fails**

To skip validation (not recommended):
```bash
SKIP_AUDIO_VALIDATION=true uv run src/run.py astra_vein_receptionist
```

---

## Common Jetson Orin Audio Issues & Fixes

| Issue | Symptoms | Fix |
|-------|----------|-----|
| **USB mic not detected after boot** | `arecord -l` doesn't show USB device | Plug in USB mic **before** booting, or: `sudo systemctl restart pulseaudio` |
| **Microphone muted in ALSA** | Recording is silent, RMS < 100 | Run `alsamixer`, press F6 (USB card), F4 (capture controls), M (unmute Mic/Capture) |
| **Low audio levels** | RMS < 500, very quiet | In `alsamixer`: increase Capture and Mic to 70%+ |
| **Wrong sample rate** | `Requested sample rate not supported` errors | Use 16000 Hz for Jetson Orin (Whisper/Piper compatible) |
| **PulseAudio not running** | `pactl` commands fail | `killall pulseaudio && pulseaudio --start` |
| **Wrong default source** | Recording from wrong device | `pactl set-default-source alsa_input.usb-<YourDevice>-00.mono-fallback` |
| **Permission denied /dev/snd** | `[Errno 13] Permission denied` | `sudo usermod -aG audio $USER` then logout/login |
| **PipeWire interfering** | Audio routing conflicts | Disable PipeWire or adapt with `pw-cli` |
| **No sound in Docker** | Container can't access audio | Add `--device /dev/snd` and mount `/run/user/1000/pulse` |

---

## Step-by-Step Troubleshooting

### Check 1: Is the USB mic recognized by the system?

```bash
lsusb | grep -i audio
```

**Expected output:**
```
Bus 001 Device 003: ID 0d8c:013c C-Media Electronics Inc. CM108 Audio Controller
```

**If not found:**
- Unplug and replug USB microphone
- Try a different USB port
- Reboot with USB mic plugged in
- Check USB cable is not damaged

### Check 2: Does ALSA see the device?

```bash
arecord -l
```

**Expected output:**
```
card 1: USB [USB Audio Device], device 0: USB Audio [USB Audio]
  Subdevices: 1/1
  Subdevice #0: subdevice #0
```

**Note the card and device numbers** - in this example: `hw:1,0`

**If not found:**
```bash
# Check kernel messages for USB audio
sudo dmesg | grep -i audio

# Restart ALSA
sudo alsa force-reload
```

### Check 3: Are mixer levels correct?

```bash
alsamixer
```

**In alsamixer:**
1. Press **F6** → Select your USB Audio Device (card 1)
2. Press **F4** → Show capture controls
3. Check for **MM** (double muted) or **M--** (single muted) indicators
4. Press **M** to unmute (should show **00** or **L R**)
5. Use **↑↓** arrow keys to increase levels to **70%+**
6. Press **Esc** to exit

**Or check programmatically:**
```bash
# Show all mixer controls for card 1
amixer -c 1 scontents

# Look for lines with [off] or low percentages like [30%]
```

### Check 4: Can you record with ALSA?

```bash
# Record 3 seconds (adjust hw:1,0 to your card:device from Check 2)
arecord -D hw:1,0 -f cd -d 3 /tmp/test.wav

# Play it back
aplay /tmp/test.wav
```

**If silent or no audio:**
- Go back to Check 3 (mixer levels)
- Try a different USB port
- Test with a different microphone

### Check 5: Is PulseAudio configured correctly?

```bash
# Check if PulseAudio is running
pactl info

# List available audio sources
pactl list short sources
```

**Expected output (sources):**
```
0   alsa_output.usb-...monitor    module-alsa-card.c    s16le 2ch 48000Hz   IDLE
1   alsa_input.usb-...mono-fallback   module-alsa-card.c    s16le 1ch 16000Hz   RUNNING
```

**Check default source:**
```bash
pactl get-default-source
```

**Expected:** Should show your USB device (contains "usb" in name)

**If wrong default source:**
```bash
# Set USB mic as default (replace with your device name from list)
pactl set-default-source alsa_input.usb-C_Media_Electronics_Inc._USB_PnP_Sound_Device-00.mono-fallback
```

### Check 6: Can you record with PulseAudio?

```bash
# Record 3 seconds from default source
timeout 3 parecord --format=s16le --rate=16000 --channels=1 /tmp/pulse_test.wav

# Play it back
aplay /tmp/pulse_test.wav
```

**If silent:**
- Check PulseAudio volume: `pavucontrol` (GUI) or `pactl list sources`
- Restart PulseAudio: `pulseaudio --kill && pulseaudio --start`
- Check that the correct source is selected

### Check 7: Python sounddevice test

```python
import sounddevice as sd
import numpy as np

# List all devices
print(sd.query_devices())

# Record 3 seconds (adjust device number)
print("Recording... SPEAK NOW!")
recording = sd.rec(int(3 * 16000), samplerate=16000, channels=1, device=1)
sd.wait()

# Analyze
rms = np.sqrt(np.mean(recording**2))
max_amp = np.max(np.abs(recording))
print(f"RMS: {rms:.4f}, Max: {max_amp:.4f}")

if rms > 0.01:
    print("✅ Audio captured!")
else:
    print("❌ No audio detected")
```

---

## Advanced Diagnostics

### Check for sample rate support

```bash
# Test different sample rates on hw:1,0
for rate in 8000 11025 16000 22050 32000 44100 48000; do
    echo -n "Testing ${rate} Hz... "
    arecord -D hw:1,0 -f cd -r $rate -d 1 /dev/null 2>&1 && echo "✅ OK" || echo "❌ FAIL"
done
```

**Jetson Orin typically supports:** 48000, 44100, 32000, 22050, 16000, 11025, 8000

### Check PulseAudio logs

```bash
# View PulseAudio logs
journalctl --user -u pulseaudio -n 100

# Or if running in foreground:
pulseaudio --kill
pulseaudio -vvv  # Very verbose output
```

### Check for device conflicts

```bash
# See what's using the audio device
sudo lsof /dev/snd/*

# Kill any conflicting processes
sudo fuser -k /dev/snd/*
```

### Test with different audio backends

```python
import sounddevice as sd

# Try different HostAPIs
print(sd.query_hostapis())

# Force ALSA (backend 0)
sd.default.hostapi = 0
print(sd.query_devices())
```

---

## Configuration Best Practices for Jetson Orin

### Recommended `astra_vein_receptionist.json5` settings:

```json5
{
  agent_inputs: [
    {
      type: "LocalASRInput",
      config: {
        engine: "faster-whisper",
        model_size: "base",           // Better multi-language support
        device: "cpu",
        compute_type: "int8",         // Fastest on Jetson
        sample_rate: 16000,           // Recommended for Jetson
        chunk_duration: 3.0,
        silence_threshold: 0.02,
        min_audio_length: 1.0,
        vad_filter: true,
        input_device: null,           // Let audio_config auto-detect
        amplify_audio: 3.0,           // Increase if mic is quiet
        
        // Multi-language support
        detect_language: true,
        supported_languages: ["en", "es", "ru"],
        default_language: "en"
      }
    }
  ]
}
```

### System-level optimizations:

```bash
# Add user to audio group (required for /dev/snd access)
sudo usermod -aG audio $USER

# Set CPU governor to performance (better latency)
echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor

# Increase audio buffer size if experiencing dropouts
echo "default-fragments = 8" | sudo tee -a /etc/pulse/daemon.conf
echo "default-fragment-size-msec = 5" | sudo tee -a /etc/pulse/daemon.conf
sudo systemctl restart pulseaudio
```

---

## Docker Deployment

### Dockerfile additions for audio:

```dockerfile
# Install audio dependencies
RUN apt-get update && apt-get install -y \
    alsa-utils \
    pulseaudio \
    pulseaudio-utils \
    libportaudio2 \
    && rm -rf /var/lib/apt/lists/*

# Add user to audio group
RUN usermod -aG audio $USER
```

### Docker run command:

```bash
docker run -it --rm \
  --device /dev/snd \
  --group-add audio \
  -v /run/user/1000/pulse:/run/user/1000/pulse \
  -e PULSE_SERVER=unix:/run/user/1000/pulse/native \
  your-image:latest
```

---

## Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `SKIP_AUDIO_VALIDATION` | `false` | Skip pre-start audio validation (not recommended) |
| `SKIP_AUDIO_TEST` | `false` | Skip recording test, only check device presence |
| `PULSE_SERVER` | (auto) | PulseAudio server address (for Docker) |

---

## Automated Startup Script for Jetson

Create `/usr/local/bin/start_astra_agent.sh`:

```bash
#!/bin/bash

# Jetson Orin - Astra Vein Agent Startup Script

set -e

echo "🤖 Starting Astra Vein Agent on Jetson Orin"
echo "=========================================="

# Navigate to project directory
cd /home/jetson/roboai-espeak  # Adjust path

# Check if USB mic is plugged in
if ! lsusb | grep -qi "audio"; then
    echo "❌ USB microphone not detected!"
    echo "   Please plug in USB PnP Sound Device"
    exit 1
fi

# Restart PulseAudio to ensure clean state
echo "🔄 Restarting PulseAudio..."
pulseaudio --kill 2>/dev/null || true
sleep 1
pulseaudio --start

# Run diagnostics
echo "🔍 Running audio diagnostics..."
python diagnostics_audio.py

if [ $? -ne 0 ]; then
    echo "❌ Audio diagnostics failed!"
    exit 1
fi

# Start agent
echo "🚀 Starting agent..."
uv run src/run.py astra_vein_receptionist

```

Make it executable:
```bash
sudo chmod +x /usr/local/bin/start_astra_agent.sh
```

Create systemd service `/etc/systemd/system/astra-agent.service`:

```ini
[Unit]
Description=Astra Vein Receptionist Agent
After=network.target sound.target

[Service]
Type=simple
User=jetson
WorkingDirectory=/home/jetson/roboai-espeak
ExecStart=/usr/local/bin/start_astra_agent.sh
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable astra-agent.service
sudo systemctl start astra-agent.service

# Check status
sudo systemctl status astra-agent.service

# View logs
sudo journalctl -u astra-agent.service -f
```

---

## Quick Reference Commands

```bash
# Audio device detection
lsusb | grep -i audio                    # USB devices
arecord -l                               # ALSA capture devices
aplay -l                                 # ALSA playback devices
pactl list short sources                 # PulseAudio sources

# Recording tests
arecord -D hw:1,0 -f cd -d 3 test.wav   # ALSA test
timeout 3 parecord test.wav              # PulseAudio test
python test_microphone.py                # Python test

# Mixer control
alsamixer                                # Interactive mixer
amixer -c 1 scontents                   # Show all controls
amixer -c 1 set 'Capture' 80%           # Set capture level

# PulseAudio management
pactl info                               # Server info
pactl get-default-source                 # Current default
pactl set-default-source <name>          # Set default
pulseaudio --kill && pulseaudio --start  # Restart

# Diagnostics
python diagnostics_audio.py              # Comprehensive check
sudo dmesg | grep -i audio              # Kernel messages
journalctl --user -u pulseaudio -n 50   # PulseAudio logs

# Agent startup
uv run src/run.py astra_vein_receptionist                 # Normal start
SKIP_AUDIO_VALIDATION=true uv run src/run.py ...          # Skip validation
```

---

## Getting Help

If you're still experiencing issues after following this guide:

1. **Collect diagnostic information:**
   ```bash
   python diagnostics_audio.py > audio_diagnostics.log 2>&1
   ```

2. **Include system information:**
   ```bash
   uname -a                          # Kernel version
   cat /etc/os-release               # OS version
   lsusb                             # USB devices
   arecord -l                        # Audio devices
   pactl list short sources          # PulseAudio config
   ```

3. **Check agent logs:**
   ```bash
   # Look for lines containing "audio", "device", "sample rate"
   grep -i "audio\|device\|sample" logs/agent.log
   ```

4. **Open an issue** with:
   - Output from `diagnostics_audio.py`
   - System information from above
   - Relevant agent log excerpts
   - Description of what you expected vs. what happened

---

## Additional Resources

- **ALSA Documentation**: https://www.alsa-project.org/wiki/Main_Page
- **PulseAudio Documentation**: https://www.freedesktop.org/wiki/Software/PulseAudio/
- **Jetson Orin Developer Guide**: https://developer.nvidia.com/embedded/jetson-orin
- **Project README**: `../README.md`
- **Audio Configuration Guide**: `AUDIO_CONFIG.md`
- **Quickstart**: `documentation/setup/QUICKSTART.md`
