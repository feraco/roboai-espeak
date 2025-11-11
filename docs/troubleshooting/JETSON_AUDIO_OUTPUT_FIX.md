# Jetson Audio Output Fix - No Sound from Agent

## Problem Summary

After running PulseAudio troubleshooting commands, the audio routing layer broke but **hardware still works**. The solution is to bypass PulseAudio and use **direct ALSA output**.

---

## Quick Diagnosis

```bash
# Check if hardware is detected (should show USB2.0 Device as card 0)
aplay -l

# Expected output:
# card 0: Device [USB2.0 Device], device 0: USB Audio [USB Audio]
```

If you see your USB speaker in `aplay -l`, the hardware is fine! Continue below.

---

## Solution 1: Test Direct ALSA Playback (Recommended)

This bypasses PulseAudio entirely and uses ALSA directly.

```bash
cd ~/roboai-espeak

# Test USB speaker with direct ALSA
speaker-test -D plughw:0,0 -c 2 -t wav -l 1

# If you hear sound, hardware works! Continue to Solution 2.
# If no sound, try unplugging/replugging USB speaker and test again.
```

---

## Solution 2: Configure Agent for Direct ALSA Output

The `astra_vein_receptionist.json5` config has been updated to use:

```json5
"play_command": "aplay -D plughw:0,0"  // Direct ALSA to card 0, device 0
```

This bypasses PulseAudio completely.

### Test TTS with Direct ALSA

```bash
cd ~/roboai-espeak

# Generate test audio with Piper
echo "This is a test of direct ALSA audio output" | \
  piper --model ./piper_voices/en_US-kristin-medium.onnx \
  --output_file test_alsa.wav

# Play via ALSA (should hear speech)
aplay -D plughw:0,0 test_alsa.wav
```

**Heard audio?** ✅ Continue to Solution 3  
**No audio?** ❌ USB speaker hardware is faulty

---

## Solution 3: Restart Agent with Fixed Config

```bash
# Clear cached device config
rm -f ~/roboai-espeak/device_config.yaml

# Restart agent service
sudo systemctl restart astra_agent

# Watch logs for successful audio playback
sudo journalctl -u astra_agent -f | grep -i "playing\|audio\|speak"
```

**Expected successful log output:**

```
INFO - Selected input device: 2 (USB PnP Sound Device)
INFO - 🔊 Playing audio with command: aplay -D plughw:0,0 /path/to/audio.wav
INFO - ✅ Audio playback completed
```

---

## Solution 4: Fix Microphone Input Device

If microphone auto-detection fails, manually specify the device number:

```bash
# Find your USB microphone device number
cd ~/roboai-espeak
python3 test_microphone.py

# Look for output like:
# Device 2: USB PnP Sound Device (maxInputChannels: 1) ✅ MICROPHONE

# Edit config to use that device number
nano config/astra_vein_receptionist.json5

# Change:
"input_device": null,  // Auto-detect
# To:
"input_device": 2,     // Use device 2 (USB PnP Sound Device)

# Save and restart
sudo systemctl restart astra_agent
```

---

## Solution 5: If PulseAudio Still Needed (Optional)

If you absolutely need PulseAudio working (not recommended for Jetson):

```bash
# Complete PulseAudio reset
pulseaudio --kill
pkill -9 pulseaudio
rm -rf ~/.config/pulse
rm -rf ~/.pulse*

# Verify user is in audio group
groups | grep audio

# If not in audio group:
sudo usermod -aG audio unitree

# Reboot to clean state
sudo reboot

# After reboot, test PulseAudio
pulseaudio --start
pactl list sinks short
```

**Note:** Direct ALSA (Solution 2) is more reliable for embedded/robot systems than PulseAudio.

---

## Troubleshooting: No Audio Devices Found

If `aplay -l` shows no USB devices:

```bash
# 1. Unplug ALL USB audio devices
# 2. Wait 10 seconds
# 3. Plug USB speaker back in

# Watch kernel messages
sudo dmesg -w

# You should see:
# usb X-X: new full-speed USB device
# usb X-X: New USB device found, idVendor=XXXX, idProduct=XXXX

# 4. Check ALSA again
aplay -l

# 5. If still not found, reboot
sudo reboot
```

---

## Verification Checklist

✅ **Hardware detected**: `aplay -l` shows `card 0: Device [USB2.0 Device]`  
✅ **Speaker test works**: `speaker-test -D plughw:0,0` produces sound  
✅ **Piper TTS works**: `aplay -D plughw:0,0 test_alsa.wav` plays speech  
✅ **Agent config updated**: `play_command: "aplay -D plughw:0,0"`  
✅ **Microphone detected**: `python3 test_microphone.py` shows USB PnP Sound Device  
✅ **Agent running**: `sudo systemctl status astra_agent` shows `active (running)`  
✅ **Audio playback logs**: `journalctl -u astra_agent` shows "Playing audio" and "Audio playback completed"

---

## Why Direct ALSA Instead of PulseAudio?

**Advantages of Direct ALSA for Jetson/Robot Deployments:**

1. ✅ **Lower latency** - No audio server middleware
2. ✅ **More reliable** - Fewer moving parts to break
3. ✅ **Simpler troubleshooting** - Direct hardware access
4. ✅ **Better for embedded** - Less overhead, lower CPU usage
5. ✅ **Works when PulseAudio broken** - Independent audio path

**PulseAudio advantages** (not needed for robot):
- Multiple simultaneous audio streams
- Network audio streaming
- Per-application volume control

For a single-purpose robot agent, **direct ALSA is the better choice**.

---

## Summary

**Root cause:** PulseAudio daemon crashed/failed to start  
**Hardware status:** ✅ Working (verified with `aplay -l`)  
**Solution:** Bypass PulseAudio, use direct ALSA output  
**Config change:** `play_command: "aplay -D plughw:0,0"`  
**Result:** Agent speaks through USB speaker without PulseAudio

---

## Quick Commands Reference

```bash
# Check hardware
aplay -l

# Test speaker
speaker-test -D plughw:0,0 -c 2 -t wav -l 1

# Test TTS
echo "test" | piper --model ./piper_voices/en_US-kristin-medium.onnx --output_file test.wav
aplay -D plughw:0,0 test.wav

# Find microphone device
python3 test_microphone.py

# Restart agent
sudo systemctl restart astra_agent

# Watch logs
sudo journalctl -u astra_agent -f
```

---

## Section 2: Check Agent Logs for Audio Errors (Legacy)

```bash
# Stop the service and check logs
sudo systemctl stop astra_agent
sudo journalctl -u astra_agent -n 100 | grep -i "audio\|speak\|playing\|error"
```

---

## Section 3: Test Agent Manually (See if Audio Works)

```bash
# Run agent manually to test
cd /home/unitree/roboai-espeak
uv run src/run.py astra_vein_receptionist

# Speak to it and watch for TTS output
# Press Ctrl+C to stop when done testing
```

---

## Section 4: Fix Audio Output in Service File

```bash
cd /home/unitree/roboai-espeak

# Stop the service
sudo systemctl stop astra_agent

# Backup the current service file
sudo cp /etc/systemd/system/astra_agent.service /etc/systemd/system/astra_agent.service.backup

# Create updated service file with audio fixes
cat > astra_agent_fixed.service << 'EOF'
[Unit]
Description=Astra Vein Receptionist AI Agent
After=network-online.target ollama.service sound.target pulseaudio.service
Wants=network-online.target ollama.service

[Service]
Type=simple
User=unitree
Group=unitree
WorkingDirectory=/home/unitree/roboai-espeak
Environment="PATH=/home/unitree/.local/bin:/usr/local/bin:/usr/bin:/bin"
Environment="DISPLAY=:0"
Environment="XAUTHORITY=/home/unitree/.Xauthority"
Environment="DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus"
Environment="PULSE_SERVER=unix:/run/user/1000/pulse/native"
Environment="XDG_RUNTIME_DIR=/run/user/1000"
Environment="SKIP_AUDIO_VALIDATION=true"
Environment="PULSE_RUNTIME_PATH=/run/user/1000/pulse"

# Wait for system to be fully ready (including audio)
ExecStartPre=/bin/sleep 20

# Ensure PulseAudio is running
ExecStartPre=/bin/bash -c "pulseaudio --check || pulseaudio --start"

# Ensure Ollama is running
ExecStartPre=/bin/bash -c "systemctl is-active ollama || sudo systemctl start ollama"
ExecStartPre=/bin/sleep 5

# Test Ollama model before starting
ExecStartPre=/bin/bash -c "timeout 20 ollama run llama3.1:8b 'Reply OK' || exit 1"

# Clear stale audio configs
ExecStartPre=/bin/bash -c "cd /home/unitree/roboai-espeak && rm -f device_config.yaml"

# Verify audio output is available
ExecStartPre=/bin/bash -c "pactl list sinks short || true"

# Start agent
ExecStart=/home/unitree/.local/bin/uv run /home/unitree/roboai-espeak/src/run.py astra_vein_receptionist

# Restart on failure
Restart=on-failure
RestartSec=10

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=astra-agent

[Install]
WantedBy=multi-user.target
EOF

# Install the fixed service
sudo cp astra_agent_fixed.service /etc/systemd/system/astra_agent.service

# Reload systemd
sudo systemctl daemon-reload

# Enable auto-start
sudo systemctl enable astra_agent

# Start the service
sudo systemctl start astra_agent

# Check status
sudo systemctl status astra_agent
```

---

## Section 5: Watch Live Logs

```bash
# Watch logs in real-time (Ctrl+C to exit)
sudo journalctl -u astra_agent -f

# In another terminal, speak to the agent and watch for:
# - "Speaking: [your response]"
# - "Playing audio file: ..."
# - Any audio errors
```

---

## Section 6: If Still No Audio - Set Default Output Device

```bash
# List all output devices
pactl list sinks short

# Example output:
# 0   alsa_output.usb-...   module-alsa-card.c   s16le 2ch 48000Hz   RUNNING
# 1   alsa_output.platform-...   module-alsa-card.c   s16le 2ch 48000Hz   IDLE

# Set the USB speaker as default (use the name from above, usually the USB one)
pactl set-default-sink alsa_output.usb-C-Media_Electronics_Inc._USB_PnP_Sound_Device-00.analog-stereo

# Or if you see a number, use that:
pactl set-default-sink 0

# Verify it's set
pactl get-default-sink

# Test speaker again
speaker-test -t wav -c 2 -l 1

# Restart service
sudo systemctl restart astra_agent
```

---

## Section 7: Nuclear Reset (If Everything Else Fails)

```bash
# Stop everything
sudo systemctl stop astra_agent
pkill -9 -f "src/run.py"

# Restart audio system
pulseaudio --kill
sleep 2
pulseaudio --start

# Clear all configs
cd /home/unitree/roboai-espeak
rm -f device_config.yaml

# Test Piper TTS directly
echo "Hello, this is a test" | piper --model ./piper_voices/en_US-kristin-medium.onnx --output_file test.wav
aplay test.wav

# If that works, restart service
sudo systemctl restart astra_agent
sudo journalctl -u astra_agent -f
```

---

## Section 8: Verify Auto-Start on Boot

```bash
# Check if enabled
sudo systemctl is-enabled astra_agent

# Should show: enabled

# Test reboot (optional)
sudo reboot

# After reboot, check status
sudo systemctl status astra_agent
```

---

## Quick Diagnostic Commands (Run Anytime)

```bash
# Check service status
sudo systemctl status astra_agent

# View last 50 log lines
sudo journalctl -u astra_agent -n 50

# Check audio devices
pactl list sinks short
aplay -l

# Check if PulseAudio is running
pulseaudio --check && echo "PulseAudio running" || echo "PulseAudio NOT running"

# Test speaker
speaker-test -t wav -c 2 -l 1

# Restart service
sudo systemctl restart astra_agent
```

---

## Expected Working Output in Logs

When everything works, you should see:
```
INFO - LocalASRInput: Transcription: "hello how are you"
INFO - Speaking: "Hello! I'm doing well, thank you. How can I help you at Astra Vein Treatment Center today?"
INFO - Playing audio file: audio_output/response_XXXXX.wav
```

If you see the "Speaking" line but NOT "Playing audio file", the TTS is working but playback is failing.
