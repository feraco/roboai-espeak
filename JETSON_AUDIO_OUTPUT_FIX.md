# Jetson Audio Output Fix - No Sound from Agent

Copy and paste each section into your Jetson terminal.

---

## Section 1: Check Current Audio Setup

```bash
# Check PulseAudio output devices
pactl list sinks short

# Check default output
pactl get-default-sink

# List all audio devices
aplay -l

# Test speaker with tone
speaker-test -t wav -c 2 -l 1
```

---

## Section 2: Check Agent Logs for Audio Errors

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
