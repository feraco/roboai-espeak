# Jetson Orin Quick Setup Guide

## Initial Setup (One-Time)

```bash
# 1. Clone repository
git clone https://github.com/feraco/roboai-espeak.git
cd roboai-espeak

# 2. Install UV package manager
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.cargo/env

# 3. Install dependencies
uv sync

# 4. Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh
ollama pull llama3.1:8b

# 5. Download TTS voices
./download_piper_voices.sh

# 6. Run system diagnostics
python diagnostics_audio.py
```

## Enable Auto-Start on Boot

```bash
# Install systemd service
./install_autostart.sh

# The agent will now start automatically on boot!
```

## Service Management

```bash
# Start agent
sudo systemctl start astra_agent

# Stop agent
sudo systemctl stop astra_agent

# Restart agent
sudo systemctl restart astra_agent

# Check status
sudo systemctl status astra_agent

# View live logs
sudo journalctl -u astra_agent -f

# View last 100 lines of logs
sudo journalctl -u astra_agent -n 100

# Disable auto-start
sudo systemctl disable astra_agent

# Re-enable auto-start
sudo systemctl enable astra_agent
```

## Manual Run (Without Auto-Start)

```bash
# Run diagnostics first
python diagnostics_audio.py

# Start agent manually
uv run src/run.py astra_vein_receptionist
```

## What Happens on Boot

1. **System boots** → waits 10 seconds for services
2. **Ollama cache cleared** → fresh LLM state
3. **Ollama restarted** → ensures service is ready
4. **Diagnostics run** → verifies audio, camera, Ollama
5. **Agent starts** → begins listening for input
6. **Auto-restart** → if agent crashes, restarts after 10s

## Troubleshooting

### Check if service is running
```bash
sudo systemctl status astra_agent
```

### View logs
```bash
# Live logs (press Ctrl+C to exit)
sudo journalctl -u astra_agent -f

# Last 50 lines
sudo journalctl -u astra_agent -n 50
```

### Manually clear Ollama cache
```bash
sudo systemctl stop ollama
rm -rf ~/.ollama/cache/*
sudo systemctl start ollama
```

### Audio issues
```bash
# Run full diagnostics
python diagnostics_audio.py

# Test microphone
parecord --device=alsa_input.usb-C-Media_Electronics_Inc._USB_PnP_Sound_Device-00.analog-mono test.wav

# Check PulseAudio
pactl list short sources
pactl get-default-source
```

### Camera issues
```bash
# List cameras
v4l2-ctl --list-devices

# Test camera (replace 6 with your camera index)
python -c "import cv2; cap = cv2.VideoCapture(6); print('Camera OK' if cap.isOpened() else 'Camera FAIL'); cap.release()"
```

### Update to latest code
```bash
cd ~/roboai-espeak
sudo systemctl stop astra_agent
git pull origin main
uv sync
sudo systemctl start astra_agent
```

## Configuration Files

- **Audio**: `device_config.yaml` (auto-generated)
- **Camera**: `camera_config.yaml` (auto-generated)
- **Agent**: `config/astra_vein_receptionist.json5` (edit to customize)
- **Service**: `/etc/systemd/system/astra_agent.service`

## Performance Tips

- **Use 16000 Hz sample rate** for audio on Jetson (not 48000)
- **llama3.1:8b is required** for reliable JSON output
- **Clear Ollama cache** if responses get slow/weird
- **Check logs regularly** to catch issues early
