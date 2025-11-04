# Jetson Complete Setup Guide - From Scratch to Running Lex

## Prerequisites
- Jetson Nano/Orin/Xavier with Ubuntu 20.04/22.04
- At least 8GB RAM recommended
- Internet connection
- SSH access or direct terminal access

---

## Part 1: System Preparation

### Step 1: Update System

```bash
# Update package lists
sudo apt update && sudo apt upgrade -y

# Install essential build tools
sudo apt install -y build-essential git curl wget python3-pip python3-dev

# Install system dependencies
sudo apt install -y \
    libportaudio2 \
    portaudio19-dev \
    ffmpeg \
    alsa-utils \
    pulseaudio \
    libsndfile1 \
    v4l-utils \
    libjpeg-dev \
    zlib1g-dev \
    libpng-dev
```

### Step 2: Install UV Package Manager

```bash
# Install UV (modern Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Add UV to PATH (add to ~/.bashrc for persistence)
export PATH="$HOME/.cargo/bin:$PATH"
source $HOME/.cargo/env

# Verify installation
uv --version
# Should show: uv x.x.x
```

### Step 3: Install Ollama

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Verify Ollama is running
sudo systemctl status ollama
# Should show: active (running)

# If not running:
sudo systemctl start ollama
sudo systemctl enable ollama

# Test Ollama
curl http://localhost:11434/api/tags
# Should return: {"models":[]}
```

---

## Part 2: Clone and Setup Project

### Step 1: Clone Repository

```bash
# Navigate to home directory
cd ~

# Clone the repository
git clone https://github.com/feraco/roboai-espeak.git

# Or if you have a different repo name:
git clone <your-repo-url> roboai-feature-multiple-agent-configurations

# Navigate into project
cd roboai-feature-multiple-agent-configurations
```

### Step 2: Setup Python Environment with UV

```bash
# Sync all dependencies (this creates virtual environment automatically)
uv sync

# This will:
# - Create .venv directory
# - Install all packages from pyproject.toml
# - Setup Python environment

# Wait for completion (may take 5-10 minutes on Jetson)
```

### Step 3: Install Ollama Model

```bash
# Pull the lightweight model for Jetson
ollama pull gemma2:2b

# Wait for download (about 1.6GB)
# Progress bar will show download status

# Verify model is installed
ollama list
# Should show:
# NAME            ID          SIZE      MODIFIED
# gemma2:2b       xyz123      1.6 GB    X seconds ago
```

---

## Part 3: Configure Hardware

### Step 1: Test Camera

```bash
# List available cameras
v4l2-ctl --list-devices

# Test camera 0
ffmpeg -f v4l2 -list_formats all -i /dev/video0

# Capture test image
ffmpeg -f v4l2 -i /dev/video0 -frames 1 test.jpg

# View available cameras for Python
uv run python3 << EOF
import cv2
for i in range(5):
    cap = cv2.VideoCapture(i)
    if cap.isOpened():
        print(f"Camera {i}: Available")
        cap.release()
    else:
        print(f"Camera {i}: Not available")
EOF
```

**Note the working camera index** (usually 0 or 1)

### Step 2: Test Microphone

```bash
# List audio input devices
arecord -l

# Example output:
# card 1: Device [USB Audio Device], device 0: USB Audio [USB Audio]
#   Subdevices: 1/1

# Test recording (3 seconds)
arecord -D hw:1,0 -d 3 -f cd test.wav

# Play back to verify
aplay test.wav

# Test with Python
uv run python3 << EOF
import sounddevice as sd
print("Available audio devices:")
print(sd.query_devices())
EOF
```

**Note the working device index**

### Step 3: Test Piper TTS

```bash
# Check if Piper is available
which piper

# If not found, install:
# Download Piper (ARM64 version for Jetson)
wget https://github.com/rhasspy/piper/releases/download/v1.2.0/piper_arm64.tar.gz
tar -xzf piper_arm64.tar.gz
sudo mv piper /usr/local/bin/
sudo chmod +x /usr/local/bin/piper

# Test Piper
echo "Hello, this is a test" | piper \
  --model piper_voices/en_US-ryan-medium.onnx \
  --output_file test_speech.wav

# Play the output
aplay test_speech.wav
```

---

## Part 4: Configure Lex Channel Chief

### Step 1: Update Camera Index (if needed)

```bash
# Edit config file
nano config/lex_channel_chief.json5

# Find the FaceEmotionCapture section:
# Change camera_index if your camera is not at index 0
{
  type: "FaceEmotionCapture", 
  config: {
    camera_index: 0,  // Change to 1, 2, etc. if needed
    poll_interval: 30.0,
    descriptor: "Face Detection with Emotion Recognition"
  }
}

# Save: Ctrl+O, Enter
# Exit: Ctrl+X
```

### Step 2: Update Microphone Device (if needed)

```bash
# Edit config file (if you need to specify microphone device)
nano config/lex_channel_chief.json5

# Find LocalASRInput section and add input_device:
{
  type: "LocalASRInput",
  config: {
    engine: "faster-whisper",
    model_size: "tiny.en",
    device: "cpu",
    input_device: null,  // Change to device index if needed (e.g., 0, 1, 2)
    // ... rest of config
  }
}

# Save and exit
```

---

## Part 5: Run Lex Channel Chief

### Method 1: Direct Run with UV

```bash
# Navigate to project directory
cd ~/roboai-feature-multiple-agent-configurations

# Run Lex Channel Chief
uv run src/run.py lex_channel_chief
```

**You should see:**
```
INFO - LocalASRInput: auto-selected input device 0
INFO - Loaded Faster-Whisper model: tiny.en
INFO - Found cam(0)
INFO - Ollama LLM: System context set
INFO - Starting OM1 with standard configuration: lex_channel_chief
```

### Method 2: Activate Environment First

```bash
# Navigate to project directory
cd ~/roboai-feature-multiple-agent-configurations

# Activate UV environment
source .venv/bin/activate

# Run agent
python src/run.py lex_channel_chief

# Deactivate when done
deactivate
```

### Method 3: Use Helper Script

Create `~/run_lex.sh`:

```bash
#!/bin/bash
cd ~/roboai-feature-multiple-agent-configurations
uv run src/run.py lex_channel_chief
```

Make executable:
```bash
chmod +x ~/run_lex.sh
```

Run anytime:
```bash
~/run_lex.sh
```

---

## Part 6: Verify Everything Works

### Test 1: Voice Interaction

1. **Run Lex**: `uv run src/run.py lex_channel_chief`
2. **Wait for**: "Loaded Faster-Whisper model"
3. **Speak into microphone**: "Hello Lex"
4. **You should see**:
   ```
   INFO - === ASR INPUT ===
   [LANG:en] Hello Lex
   INFO - === LLM OUTPUT ===
   {"actions": [{"type": "speak", ...}]}
   INFO - Piper TTS synthesis successful
   INFO - Audio played successfully
   ```
5. **You should hear**: Lex's voice responding

### Test 2: Vision Detection

1. **Position yourself** in front of the camera
2. **Wait 30 seconds** (or whatever poll_interval you set)
3. **You should see**:
   ```
   INFO - EmotionCapture: I see a person. Their emotion is happy.
   INFO - === INPUT STATUS ===
   Voice: No | Vision: Yes | Language: en
   INFO - === LLM OUTPUT ===
   {"actions": [{"type": "speak", "value": {"sentence": "What a sharp professional look..."}}]}
   ```
4. **You should hear**: Lex greeting you with compliment + introduction + photo request

### Test 3: Memory Usage

```bash
# In another terminal, check memory while Lex is running
free -h

# Should see approximately:
# Total: 8GB
# Used: ~3-4GB (with Lex running)
# Free: ~4-5GB

# Check Ollama memory
ps aux | grep ollama | grep -v grep
# Should show gemma2:2b process using ~1.6GB
```

---

## Part 7: Troubleshooting

### Issue: "No output from LLM"

```bash
# Stop Lex
pkill -f lex_channel_chief

# Fix Ollama (see JETSON_OLLAMA_FIX.md for details)
sudo systemctl stop ollama
sleep 3
rm -rf ~/.ollama/models/*
sudo systemctl start ollama
sleep 5
ollama pull gemma2:2b

# Test Ollama
curl -X POST http://localhost:11434/api/generate -d '{
  "model": "gemma2:2b",
  "prompt": "Hello",
  "stream": false
}'

# Should return JSON with response

# Restart Lex
cd ~/roboai-feature-multiple-agent-configurations
uv run src/run.py lex_channel_chief
```

### Issue: Camera not detected

```bash
# Check camera permissions
sudo usermod -a -G video $USER

# Reboot
sudo reboot

# After reboot, test again
v4l2-ctl --list-devices
```

### Issue: Microphone not working

```bash
# Check microphone permissions
sudo usermod -a -G audio $USER

# Set default audio device
pactl list short sources

# Reboot
sudo reboot

# Test recording
arecord -d 3 test.wav
aplay test.wav
```

### Issue: UV command not found

```bash
# Add UV to PATH permanently
echo 'export PATH="$HOME/.cargo/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# Verify
uv --version
```

### Issue: Out of memory

```bash
# Use even smaller model
ollama rm gemma2:2b
ollama pull llama3.2:1b

# Update config to use llama3.2:1b
nano config/lex_channel_chief.json5
# Change: model: "llama3.2:1b"

# Increase vision polling interval
# Change: poll_interval: 60.0  (check every minute)

# Clear system cache
sudo sync
sudo sh -c 'echo 3 > /proc/sys/vm/drop_caches'
```

---

## Part 8: Auto-Start on Boot (Optional)

### Create Systemd Service

```bash
# Create service file
sudo nano /etc/systemd/system/lex-channel-chief.service
```

**Content:**
```ini
[Unit]
Description=Lex Channel Chief AI Agent
After=network.target ollama.service
Requires=ollama.service

[Service]
Type=simple
User=jetson
WorkingDirectory=/home/jetson/roboai-feature-multiple-agent-configurations
Environment="PATH=/home/jetson/.cargo/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
ExecStart=/home/jetson/.cargo/bin/uv run src/run.py lex_channel_chief
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

**Activate:**
```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service (start on boot)
sudo systemctl enable lex-channel-chief.service

# Start service now
sudo systemctl start lex-channel-chief.service

# Check status
sudo systemctl status lex-channel-chief.service

# View logs
sudo journalctl -u lex-channel-chief.service -f
```

**Control Commands:**
```bash
# Start Lex
sudo systemctl start lex-channel-chief.service

# Stop Lex
sudo systemctl stop lex-channel-chief.service

# Restart Lex
sudo systemctl restart lex-channel-chief.service

# Check status
sudo systemctl status lex-channel-chief.service

# View live logs
sudo journalctl -u lex-channel-chief.service -f

# Disable auto-start
sudo systemctl disable lex-channel-chief.service
```

---

## Part 9: Running Different Agents

### List Available Agents

```bash
# View all config files
ls -la config/*.json5

# Common agents:
# - lex_channel_chief.json5
# - local_agent.json5
# - unitree_g1_humanoid.json5
# - voice_only_greeter.json5
```

### Run Different Agent

```bash
# Activate environment
cd ~/roboai-feature-multiple-agent-configurations

# Run specific agent
uv run src/run.py <config_name>

# Examples:
uv run src/run.py local_agent
uv run src/run.py voice_only_greeter
uv run src/run.py lightweight_face_greeter
```

### Switch Default Agent in Systemd

```bash
# Edit service file
sudo nano /etc/systemd/system/lex-channel-chief.service

# Change ExecStart line:
ExecStart=/home/jetson/.cargo/bin/uv run src/run.py <different_config>

# Reload and restart
sudo systemctl daemon-reload
sudo systemctl restart lex-channel-chief.service
```

---

## Part 10: Maintenance

### Update Project

```bash
cd ~/roboai-feature-multiple-agent-configurations

# Pull latest changes
git pull origin main

# Update dependencies
uv sync

# Restart service if running
sudo systemctl restart lex-channel-chief.service
```

### Monitor Performance

```bash
# CPU/Memory usage
htop

# GPU usage (if applicable)
tegrastats

# Ollama status
sudo systemctl status ollama

# Check running processes
ps aux | grep -E "lex_channel_chief|ollama"

# Disk usage
df -h
```

### Clean Up

```bash
# Remove old audio outputs
rm -rf audio_output/*.wav

# Clear Python cache
find . -type d -name __pycache__ -exec rm -rf {} +
find . -type f -name "*.pyc" -delete

# Clear UV cache (if needed)
uv cache clean
```

---

## Quick Reference Card

### Essential Commands

```bash
# Start Lex manually
cd ~/roboai-feature-multiple-agent-configurations
uv run src/run.py lex_channel_chief

# Start Lex as service
sudo systemctl start lex-channel-chief.service

# Stop Lex
pkill -f lex_channel_chief
# OR
sudo systemctl stop lex-channel-chief.service

# Check Ollama
curl http://localhost:11434/api/tags
ollama list

# View logs
tail -f /var/log/syslog | grep -i lex
# OR
sudo journalctl -u lex-channel-chief.service -f

# Test camera
ffmpeg -f v4l2 -i /dev/video0 -frames 1 test.jpg

# Test microphone
arecord -d 3 test.wav && aplay test.wav

# Check memory
free -h

# Update project
cd ~/roboai-feature-multiple-agent-configurations
git pull
uv sync
```

### Default Paths

```
Project: ~/roboai-feature-multiple-agent-configurations
Configs: ~/roboai-feature-multiple-agent-configurations/config/
Audio Output: ~/roboai-feature-multiple-agent-configurations/audio_output/
UV Environment: ~/roboai-feature-multiple-agent-configurations/.venv/
Ollama Models: ~/.ollama/models/
Service File: /etc/systemd/system/lex-channel-chief.service
```

---

## Memory Optimization Summary

| Component | Memory Usage | Optimization |
|-----------|--------------|--------------|
| gemma2:2b | ~1.6 GB | Use llama3.2:1b (1GB) if needed |
| faster-whisper tiny.en | ~75 MB | Smallest Whisper model |
| DeepFace + TensorFlow | ~200-300 MB | Disable vision if not needed |
| System overhead | ~500 MB | - |
| **Total** | **~2.5 GB** | **Leaves 5.5GB free on 8GB Jetson** |

---

## Support

If you encounter issues:

1. Check logs: `sudo journalctl -u lex-channel-chief.service -f`
2. Test Ollama: `curl http://localhost:11434/api/tags`
3. Test camera: `v4l2-ctl --list-devices`
4. Test microphone: `arecord -d 3 test.wav`
5. Check memory: `free -h`

For persistent issues, see `deployment/JETSON_OLLAMA_FIX.md`

---

## Success Checklist

- [ ] System updated and dependencies installed
- [ ] UV package manager installed and working
- [ ] Ollama installed and running
- [ ] Repository cloned
- [ ] UV environment synced (`uv sync`)
- [ ] Ollama model downloaded (`ollama pull gemma2:2b`)
- [ ] Camera tested and working
- [ ] Microphone tested and working
- [ ] Lex runs successfully
- [ ] Voice interaction works
- [ ] Vision detection works (if camera enabled)
- [ ] (Optional) Systemd service configured
- [ ] (Optional) Auto-start on boot enabled

🎉 **Congratulations! Lex Channel Chief is ready!**
