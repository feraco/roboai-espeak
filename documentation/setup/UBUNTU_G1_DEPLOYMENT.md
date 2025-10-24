# 🤖 Complete Ubuntu G1 Deployment Guide

## 🎯 Overview

This guide provides **step-by-step instructions with troubleshooting** to deploy the Astra Vein receptionist agent on your Unitree G1 robot running Ubuntu 22.04.

Each step includes:
- ✅ Success indicators
- ❌ Common problems
- 🔧 Troubleshooting solutions

## 📋 Prerequisites

- Unitree G1 robot with Ubuntu 22.04
- SSH access to G1: `ssh unitree@<g1-ip-address>`
- Internet connection (WiFi or Ethernet)
- Sudo privileges

## 🚀 Quick Start (For Experienced Users)

### On Your G1 Robot (via SSH)

```bash
# 1. Clone repository
cd ~
git clone https://github.com/feraco/roboai-espeak.git
cd roboai-espeak

# 2. Install system dependencies
sudo apt update
sudo apt install -y python3-pip python3-venv git wget curl \
    alsa-utils v4l-utils portaudio19-dev python3-pyaudio \
    libopencv-dev python3-opencv

# 3. Install uv (Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc

# 4. Install Python dependencies
uv sync

# 5. Setup Piper TTS
./setup_piper_ubuntu.sh

# 6. Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 7. Start Ollama service
sudo systemctl start ollama
sudo systemctl enable ollama

# 8. Pull AI models
ollama pull llama3.1:8b
ollama pull llava-llama3

# 9. Run hardware check
python3 check_g1_hardware.py

# 10. If all checks pass, run the agent
uv run src/run.py astra_vein_receptionist
```

---

## 📦 Detailed Installation Steps (With Troubleshooting)


## 📦 Detailed Installation Steps (With Troubleshooting)

---

### 📥 STEP 1: System Dependencies

**What you're doing:** Installing core system packages needed for audio, video, and Python development.

```bash
sudo apt update
sudo apt install -y \
    python3-pip \
    python3-venv \
    git \
    wget \
    curl \
    build-essential \
    alsa-utils \
    v4l-utils \
    portaudio19-dev \
    python3-pyaudio \
    libopencv-dev \
    python3-opencv \
    ffmpeg
```

#### ✅ Success Indicators:
```
Reading package lists... Done
Building dependency tree... Done
The following NEW packages will be installed:
  alsa-utils v4l-utils portaudio19-dev...
0 upgraded, 15 newly installed, 0 to remove
```

#### ❌ Common Problems:

**Problem:** "Unable to locate package"
```
E: Unable to locate package python3-pyaudio
```

**Solution:**
```bash
# Update package lists
sudo apt update

# If still failing, try universe repository
sudo add-apt-repository universe
sudo apt update

# Try again
sudo apt install -y python3-pyaudio
```

---

**Problem:** "dpkg was interrupted"
```
E: dpkg was interrupted, you must manually run 'sudo dpkg --configure -a'
```

**Solution:**
```bash
sudo dpkg --configure -a
sudo apt --fix-broken install
sudo apt update
# Try again
```

#### 🧪 Test This Step:
```bash
# Verify audio tools
arecord --version
aplay --version

# Verify video tools
v4l2-ctl --version

# Verify Python
python3 --version  # Should be 3.10+
pip3 --version
```

---

### 📦 STEP 2: Install UV Package Manager

**What you're doing:** Installing `uv`, a fast Python package manager that replaces pip/venv.

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc  # Or restart terminal
```

#### ✅ Success Indicators:
```
info: downloading uv...
info: installed uv to /home/unitree/.cargo/bin/uv
```

#### ❌ Common Problems:

**Problem:** `uv: command not found` after install

**Solution:**
```bash
# Reload shell config
source ~/.bashrc

# If still not found, manually add to PATH
echo 'export PATH="$HOME/.cargo/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# Or restart terminal
exit
# SSH back in
```

#### 🧪 Test This Step:
```bash
uv --version  # Should show version 0.4+
which uv       # Should show /home/unitree/.cargo/bin/uv
```

---

### 📁 STEP 3: Clone and Setup Project

**What you're doing:** Downloading the roboai code and installing Python dependencies.

```bash
cd ~
git clone https://github.com/feraco/roboai-espeak.git
cd roboai-espeak

# Install Python dependencies
uv sync
```

#### ✅ Success Indicators:
```
Cloning into 'roboai-espeak'...
Receiving objects: 100%...
Resolved 127 packages in 3.2s
Installed 127 packages in 15.4s
```

#### ❌ Common Problems:

**Problem:** "Permission denied (publickey)"
```
git@github.com: Permission denied (publickey).
fatal: Could not read from remote repository.
```

**Solution:**
```bash
# Use HTTPS instead
git clone https://github.com/feraco/roboai-espeak.git
```

---

**Problem:** `uv sync` fails with "No such file or directory"

**Solution:**
```bash
# Make sure you're in the project directory
cd ~/roboai-espeak
pwd  # Should show /home/unitree/roboai-espeak

# Verify pyproject.toml exists
ls -la pyproject.toml

# Try again
uv sync
```

#### 🧪 Test This Step:
```bash
# Verify installation
ls ~/roboai-espeak/src/
# Should see: actions/ connectors/ inputs/ outputs/ memory/ etc.

# Check Python packages
uv pip list | grep -E "(pyaudio|opencv|faster-whisper)"
```

---

### 🎵 STEP 4: Setup Piper TTS

**What you're doing:** Installing Piper text-to-speech engine and voices.

```bash
./setup_piper_ubuntu.sh
```

#### ✅ Success Indicators:
```
🎵 Piper TTS Setup for Ubuntu
==================================================
✅ Detected architecture: aarch64
📥 Downloading Piper...
✅ Piper installed to ~/.local/share/piper/piper
📥 Downloading voice: en_US-ryan-medium...
✅ Voice installed
🧪 Testing Piper...
✅ Piper TTS setup complete!
```

#### ❌ Common Problems:

**Problem:** "setup_piper_ubuntu.sh: Permission denied"

**Solution:**
```bash
chmod +x setup_piper_ubuntu.sh
./setup_piper_ubuntu.sh
```

---

**Problem:** Download fails
```
curl: (6) Could not resolve host: github.com
```

**Solution:**
```bash
# Check internet connection
ping -c 3 github.com

# If DNS issue, use Google DNS
echo "nameserver 8.8.8.8" | sudo tee -a /etc/resolv.conf

# Try again
./setup_piper_ubuntu.sh
```

---

**Problem:** Voice not found after install

**Solution:**
```bash
# Check installation directory
ls -la ~/.local/share/piper/voices/

# If empty, manually download voice
mkdir -p ~/.local/share/piper/voices/en/en_US/ryan/medium/
cd ~/.local/share/piper/voices/en/en_US/ryan/medium/

# Download voice files
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/ryan/medium/en_US-ryan-medium.onnx
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/ryan/medium/en_US-ryan-medium.onnx.json
```

#### 🧪 Test This Step:
```bash
# Test Piper directly
echo "Hello from Piper" | piper \
    --model ~/.local/share/piper/voices/en/en_US/ryan/medium/en_US-ryan-medium.onnx \
    --output_file test.wav

# Play the audio
aplay test.wav

# Should hear "Hello from Piper"
```

---

### 🧠 STEP 5: Install Ollama

**What you're doing:** Installing Ollama to run the LLM (Large Language Model) locally.

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh
```

#### ✅ Success Indicators:
```
>>> Installing ollama to /usr/local/bin...
>>> Creating ollama user...
>>> Adding ollama user to video group...
>>> Installing ollama service...
>>> Ollama installed successfully!
```

#### ❌ Common Problems:

**Problem:** Install script fails

**Solution:**
```bash
# Try manual installation
wget https://ollama.com/download/ollama-linux-arm64
sudo chmod +x ollama-linux-arm64
sudo mv ollama-linux-arm64 /usr/local/bin/ollama

# Create service
sudo useradd -r -s /bin/false -m -d /usr/share/ollama ollama
```

#### 🧪 Test This Step:
```bash
which ollama  # Should show /usr/local/bin/ollama
ollama --version
```

---

### 🚀 STEP 6: Start Ollama Service

**⚠️ CRITICAL STEP:** Ollama must be running for the agent to work!

```bash
# Start Ollama service
sudo systemctl start ollama

# Enable auto-start on boot
sudo systemctl enable ollama
```

#### ✅ Success Indicators:
```bash
# Check status
sudo systemctl status ollama
```

Should show:
```
● ollama.service - Ollama Service
     Loaded: loaded
     Active: active (running) since...
     Main PID: 12345
```

#### ❌ Common Problems:

**Problem:** Service fails to start
```
Job for ollama.service failed because the control process exited with error code.
```

**Solution:**
```bash
# Check detailed error
journalctl -u ollama -n 50

# Common issue: Port already in use
sudo lsof -i :11434
# Kill conflicting process or reboot

# Restart service
sudo systemctl restart ollama
```

---

**Problem:** "Failed to connect to Ollama" later when running agent

**Solution:**
```bash
# Verify Ollama is running
sudo systemctl status ollama

# If not active, start it
sudo systemctl start ollama

# Test connection
curl http://localhost:11434/api/tags

# Should return JSON with list of models
```

#### 🧪 Test This Step:
```bash
# Verify service is running
sudo systemctl is-active ollama  # Should print "active"

# Test API endpoint
curl http://localhost:11434/api/tags

# Should return: {"models":[]}
```

---

### 📚 STEP 7: Download AI Models

**What you're doing:** Downloading the language models Ollama will use.

```bash
# Download LLM (required for conversation) - ~4.7 GB
ollama pull llama3.1:8b

# Download Vision model (required for compliments) - ~4.5 GB
ollama pull llava-llama3
```

#### ✅ Success Indicators:
```
pulling manifest
pulling 8eeb52dfb3bb... 100% ▕████████████▏ 4.7 GB
pulling 73b313b5552d... 100% ▕████████████▏ 1.5 KB
verifying sha256 digest
success
```

#### ❌ Common Problems:

**Problem:** "Error: could not connect to ollama server"

**Solution:**
```bash
# Ollama service not running!
sudo systemctl status ollama

# Start it
sudo systemctl start ollama

# Try again
ollama pull llama3.1:8b
```

---

**Problem:** Download very slow or times out

**Solution:**
```bash
# Check disk space (models are ~9 GB total)
df -h /

# If low on space, clean up
sudo apt clean
sudo apt autoremove

# Check internet speed
speedtest-cli  # Or visit fast.com

# Try downloading one at a time with retries
ollama pull llama3.1:8b
# Wait for completion, then:
ollama pull llava-llama3
```

---

**Problem:** "Error: model not found"

**Solution:**
```bash
# Check exact model names available
curl https://ollama.com/api/tags | jq '.models[].name'

# Or try alternative models
ollama pull llama3:8b        # Alternative
ollama pull llava:latest     # Alternative vision model
```

#### 🧪 Test This Step:
```bash
# List installed models
ollama list

# Expected output:
NAME                ID              SIZE    MODIFIED
llama3.1:8b         abc123...       4.7 GB  2 minutes ago
llava-llama3        def456...       4.5 GB  1 minute ago

# Test LLM
ollama run llama3.1:8b "Say hello"
# Should respond with greeting

# Test Vision (requires image)
ollama run llava-llama3 "What's in this image?" /path/to/image.jpg
```

---

### ✅ STEP 8: Hardware Check

**What you're doing:** Validating that all hardware components work before running the agent.

```bash
python3 check_g1_hardware.py
```

#### ✅ Success Indicators:

```bash
sudo apt update
sudo apt install -y \
    python3-pip \
    python3-venv \
    git \
    wget \
    curl \
    build-essential \
    alsa-utils \
    v4l-utils \
    portaudio19-dev \
    python3-pyaudio \
    libopencv-dev \
    python3-opencv \
    ffmpeg
```

**What this installs:**
- `python3-*`: Python and development tools
- `alsa-utils`: Audio tools (arecord, aplay)
- `v4l-utils`: Video for Linux utilities
- `portaudio19-dev`: Audio I/O library
- `libopencv-dev`: Computer vision library
- `ffmpeg`: Media processing

### Step 2: Install UV Package Manager

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc  # Or restart terminal
```

Verify:
```bash
uv --version
```

### Step 3: Clone and Setup Project

```bash
cd ~
git clone https://github.com/feraco/roboai-espeak.git
cd roboai-espeak

# Install Python dependencies
uv sync
```

### Step 4: Setup Piper TTS

```bash
./setup_piper_ubuntu.sh
```

This script will:
- Download Piper for your architecture (x86_64 or aarch64)
- Install to `~/.local/share/piper/`
- Download `en_US-ryan-medium` voice
- Add piper to PATH
- Test the installation

**Verify Piper works:**
```bash
echo "Hello world" | piper \
    --model ~/.local/share/piper/voices/en/en_US/ryan/medium/en_US-ryan-medium.onnx \
    --output_file test.wav
aplay test.wav
```

### Step 5: Install Ollama

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Start Ollama service
sudo systemctl start ollama
sudo systemctl enable ollama

# Verify it's running
ollama list
```

### Step 6: Download AI Models

```bash
# Download LLM (required)
ollama pull llama3.1:8b

# Download Vision model (required for compliments)
ollama pull llava-llama3

# Verify models
ollama list
```

**Expected output:**
```
NAME                ID              SIZE    MODIFIED
llama3.1:8b         abc123...       4.7 GB  2 minutes ago
llava-llama3        def456...       4.5 GB  1 minute ago
```


#### ✅ Success Indicators:

```
🤖 G1 HARDWARE STARTUP CHECK
==================================================

🎤 MICROPHONE:
  ✅ OK - USB2.0 Device
     Device: hw:0,0
     Sample rate: 16000 Hz
     PyAudio index: 0

🔊 SPEAKER:
  ✅ OK - 1 output device(s) found
     Default device working

📷 CAMERA:
  ✅ OK - Camera at /dev/video0
     Resolution: 640x480
     FPS: 30

🧠 OLLAMA LLM:
  ✅ OK - Ollama running at http://localhost:11434
     Models: llama3.1:8b

👁️  OLLAMA VISION:
  ✅ OK - Vision model available: llava-llama3

🎵 PIPER TTS:
  ✅ OK - Piper voices found
     Path: /home/unitree/.local/share/piper/voices
     Voice: en_US-ryan-medium.onnx

==================================================
✅ ALL SYSTEMS GO - Ready to start agent
==================================================
```

#### ❌ Common Problems:

**Problem:** ❌ Microphone check fails
```
🎤 MICROPHONE:
  ❌ FAIL - No working audio input device found
```

**Solution:**
```bash
# List audio devices
arecord -l

# Should see USB device like:
# card 0: Device [USB2.0 Device], device 0
# card 1: Camera [UVC Camera], device 0

# Test manually
arecord -D hw:0,0 -f S16_LE -r 16000 -c 1 -d 3 test_mic.wav
aplay test_mic.wav

# If permissions issue:
sudo usermod -a -G audio $USER
# Logout and login again
```

---

**Problem:** ❌ Camera check fails
```
📷 CAMERA:
  ❌ FAIL - No camera found
```

**Solution:**
```bash
# List video devices
ls -la /dev/video*

# Should see /dev/video0, /dev/video1, etc.

# Test with v4l2
v4l2-ctl --list-devices

# Test with Python
python3 -c "
import cv2
cap = cv2.VideoCapture(0)
print('Camera opened:', cap.isOpened())
cap.release()
"

# If permissions issue:
sudo usermod -a -G video $USER
sudo chmod 666 /dev/video0
# Logout and login again
```

---

**Problem:** ❌ Ollama check fails
```
🧠 OLLAMA LLM:
  ❌ FAIL - Ollama not running
```

**Solution:**
```bash
# THIS IS THE MOST COMMON ISSUE!
# Ollama service must be started

# Start service
sudo systemctl start ollama

# Verify it's running
sudo systemctl status ollama

# Test manually
curl http://localhost:11434/api/tags

# If port in use:
sudo lsof -i :11434
# Kill other process or reboot

# Enable auto-start
sudo systemctl enable ollama

# Run check again
python3 check_g1_hardware.py
```

---

**Problem:** ❌ Models not found
```
🧠 OLLAMA LLM:
  ✅ OK - Ollama running
  ❌ FAIL - Missing model: llama3.1:8b
```

**Solution:**
```bash
# Download missing models
ollama pull llama3.1:8b
ollama pull llava-llama3

# Verify they're installed
ollama list

# Run check again
python3 check_g1_hardware.py
```

---

**Problem:** ❌ Piper check fails
```
🎵 PIPER TTS:
  ❌ FAIL - Piper voices not found
```

**Solution:**
```bash
# Re-run setup
./setup_piper_ubuntu.sh

# Or check manually
ls -la ~/.local/share/piper/voices/

# Test Piper
echo "test" | piper \
    --model ~/.local/share/piper/voices/en/en_US/ryan/medium/en_US-ryan-medium.onnx \
    --output_file test.wav
aplay test.wav
```

#### 🧪 What This Checks:
- ✅ Microphone hardware and sample rate compatibility
- ✅ Speaker/audio output device
- ✅ Camera accessibility and OpenCV functionality
- ✅ **Ollama service is running** (critical!)
- ✅ Required AI models are downloaded
- ✅ Piper TTS installation and voice files
- ✅ PyAudio device index mapping

**DO NOT PROCEED** until all checks show ✅ OK!

---

### 🚀 STEP 9: Test Run Agent

**What you're doing:** Starting the receptionist agent for the first time.

```bash
uv run src/run.py astra_vein_receptionist
```

#### ✅ Success Indicators:

```
2024-10-24 14:32:10 - INFO - Loading agent config: astra_vein_receptionist
2024-10-24 14:32:12 - INFO - Initializing Ollama LLM connector...
2024-10-24 14:32:12 - INFO - Testing Ollama connection: http://localhost:11434
2024-10-24 14:32:13 - INFO - ✅ Ollama connected successfully
2024-10-24 14:32:13 - INFO - Available models: ['llama3.1:8b', 'llava-llama3']
2024-10-24 14:32:14 - INFO - Initializing camera...
2024-10-24 14:32:15 - INFO - Camera opened: /dev/video0
2024-10-24 14:32:16 - INFO - Initializing adaptive ASR input...
2024-10-24 14:32:17 - INFO - Audio device auto-detected: hw:0,0 (USB2.0 Device)
2024-10-24 14:32:17 - INFO - Sample rate: 16000 Hz
2024-10-24 14:32:18 - INFO - Initializing Piper TTS...
2024-10-24 14:32:18 - INFO - Voice path: /home/unitree/.local/share/piper/voices/en/en_US/ryan/medium/en_US-ryan-medium.onnx
2024-10-24 14:32:19 - INFO - Agent started successfully
2024-10-24 14:32:20 - INFO - [VISION] Analyzing camera frame...
2024-10-24 14:32:22 - INFO - [VISION] Person detected: wearing blue shirt
2024-10-24 14:32:23 - INFO - [TTS] Playing: "Hello and welcome to Astra Vein Treatment Center! I love that blue shirt! I'm Iris..."
```

**You should hear:** The greeting through the speakers.

#### ❌ Common Problems:

**Problem:** "Failed to connect to Ollama"
```
ERROR - Could not connect to Ollama at http://localhost:11434
ERROR - Connection refused
```

**Solution:**
```bash
# Ollama not running!
sudo systemctl start ollama

# Verify
curl http://localhost:11434/api/tags

# Try agent again
uv run src/run.py astra_vein_receptionist
```

---

**Problem:** "Invalid sample rate" errors
```
ERROR - [Errno -9997] Invalid sample rate
```

**Solution:**
```bash
# Audio device mismatch
# Run diagnostic
python3 -m src.audio_system_fixer

# Use recommended device from output
# Config will auto-detect, but you can manually specify in config:
# "input_device": 0  # Use device number from diagnostic
```

---

**Problem:** Camera fails to open
```
ERROR - Cannot open camera at /dev/video0
```

**Solution:**
```bash
# Check camera
ls -la /dev/video0

# Fix permissions
sudo chmod 666 /dev/video0

# Check if another process is using it
sudo lsof /dev/video0

# Kill other process if needed
sudo kill <PID>

# Try agent again
```

---

**Problem:** "Model not found: llama3.1:8b"
```
ERROR - Model llama3.1:8b not found in Ollama
```

**Solution:**
```bash
# Download missing model
ollama pull llama3.1:8b

# Verify
ollama list

# Try agent again
uv run src/run.py astra_vein_receptionist
```

---

**Problem:** No audio output
```
INFO - [TTS] Playing: "Hello and welcome..."
# But nothing is heard
```

**Solution:**
```bash
# Test speaker
speaker-test -t wav -c 2

# Test Piper directly
echo "test audio" | piper \
    --model ~/.local/share/piper/voices/en/en_US/ryan/medium/en_US-ryan-medium.onnx \
    --output_file test.wav
aplay test.wav

# Check volume
alsamixer
# Press F6 to select sound card
# Use arrow keys to adjust volume

# Check default audio device
aplay -L | grep default
```

#### 🧪 Test Interaction:

Once agent is running, try these:

```
👤 You: "What are your hours?"
🤖 Agent: "We're open Monday through Friday, 8 AM to 5 PM, and Saturdays from 9 AM to 1 PM. Would you like to schedule an appointment?"

👤 You: "Where are you located?"
🤖 Agent: "We have four convenient locations: Brooklyn on Avenue U, Bronx on East Tremont, Queens in Astoria, and Manhattan. Which area works best for you?"

👤 You: "Tell me about the doctor."
🤖 Agent: "Dr. Bolotin is board-certified in Diagnostic and Interventional Radiology and practices at our Brooklyn and Bronx offices. He's highly experienced in minimally invasive vein treatments."
```

**Press Ctrl+C** to stop the agent.

---

### 🔧 STEP 10: Configuration (Optional)


### 🔧 STEP 10: Configuration (Optional)

**What you're doing:** Customizing settings if auto-detection doesn't work perfectly.

#### Audio Configuration

The config now uses auto-detection, but you can override:

```bash
# Edit config
nano config/astra_vein_receptionist.json5
```

Find the audio section:
```json5
{
  "config": {
    "input_device": 0,        // Change to device number from check_g1_hardware.py
    "sample_rate": 16000,     // Usually 16000 works best
    "play_command": null      // null = auto-detect (aplay on Linux)
  }
}
```

#### Test Audio Changes:
```bash
# After editing config, test with:
uv run src/run.py astra_vein_receptionist

# Listen for greeting
# Press Ctrl+C if it works
```

#### Ethernet Interface (For Unitree SDK)

If you want arm gesture control:

```bash
# Find your Ethernet interface
ip addr show | grep "state UP"
# Look for: eno1, eth0, enp1s0, etc.

# Edit config
nano config/astra_vein_receptionist.json5
```

Change:
```json5
{
  unitree_ethernet: "eno1"  // Change to YOUR interface name
}
```

---

## ✅ DEPLOYMENT CHECKLIST

Before deploying to production, verify each item:

### Hardware
- [ ] **Microphone**: `arecord -D hw:0,0 -f S16_LE -r 16000 -c 1 -d 3 test.wav` works
- [ ] **Speaker**: `aplay test.wav` produces clear audio
- [ ] **Camera**: `python3 -c "import cv2; print(cv2.VideoCapture(0).isOpened())"` prints `True`

### Software
- [ ] **Ollama Service**: `sudo systemctl status ollama` shows `active (running)` ⚠️ CRITICAL
- [ ] **LLM Model**: `ollama list` shows `llama3.1:8b`
- [ ] **Vision Model**: `ollama list` shows `llava-llama3`
- [ ] **Piper TTS**: `ls ~/.local/share/piper/voices/en/en_US/ryan/medium/` shows `.onnx` files
- [ ] **Python Packages**: `uv pip list | grep -E "(pyaudio|opencv|faster-whisper)"` shows packages

### System Checks
- [ ] **Hardware Check**: `python3 check_g1_hardware.py` - ALL ✅ GREEN
- [ ] **Test Run**: `uv run src/run.py astra_vein_receptionist` starts without errors
- [ ] **Audio Output**: Greeting is heard clearly through speakers
- [ ] **Voice Recognition**: Agent responds when you speak
- [ ] **Vision**: Agent gives camera-based compliments

### Performance
- [ ] **Response Time**: Agent responds within 2-3 seconds
- [ ] **Audio Quality**: No crackling, distortion, or echo
- [ ] **Vision Accuracy**: Compliments are appropriate

---

## 🔄 Auto-Start on Boot (Production Setup)

Once everything works reliably, set up auto-start:

```bash
./setup_g1_autostart.sh
```

This creates a systemd service that:
- ✅ Starts automatically on boot
- ✅ Restarts on failure (3 times)
- ✅ Runs as your user
- ✅ Logs to system journal
- ✅ Ensures Ollama is running first

### Control the Service:

```bash
# Check status
sudo systemctl status roboai-astra-vein

# View live logs
journalctl -u roboai-astra-vein -f

# Stop service
sudo systemctl stop roboai-astra-vein

# Start service
sudo systemctl start roboai-astra-vein

# Restart service
sudo systemctl restart roboai-astra-vein

# Disable auto-start
sudo systemctl disable roboai-astra-vein

# Re-enable auto-start
sudo systemctl enable roboai-astra-vein
```

### Troubleshoot Auto-Start:

```bash
# If service fails to start after boot:

# Check logs
journalctl -u roboai-astra-vein -n 100

# Common issue: Ollama not ready yet
# Solution: Service waits for Ollama, but check:
sudo systemctl status ollama

# If Ollama not enabled on boot:
sudo systemctl enable ollama

# Reboot and test
sudo reboot
```

---

## 🐛 Common Issues & Solutions

### Issue 1: "Ollama Connection Refused"

**Symptoms:**
```
ERROR - Could not connect to Ollama at http://localhost:11434
ConnectionRefusedError: [Errno 111] Connection refused
```

**Root Cause:** Ollama service is not running

**Solution:**
```bash
# Start Ollama
sudo systemctl start ollama

# Verify it's running
sudo systemctl status ollama

# Test connection
curl http://localhost:11434/api/tags

# Enable auto-start
sudo systemctl enable ollama

# If port conflict:
sudo lsof -i :11434
# Kill conflicting process or reboot
```

---

### Issue 2: "Invalid Sample Rate"

**Symptoms:**
```
ERROR - [Errno -9997] Invalid sample rate
OSError: [Errno -9997] Invalid sample rate
```

**Root Cause:** Audio device doesn't support requested sample rate

**Solution:**
```bash
# Run audio diagnostic
python3 -m src.audio_system_fixer

# Output will show best device and sample rate:
# ✅ Best input device: hw:0,0 (USB2.0 Device) - Score: 100
#    Supported rates: [16000, 22050, 44100, 48000]

# Config auto-detects, but verify:
nano config/astra_vein_receptionist.json5
# Set input_device to recommended device number
```

---

### Issue 3: Camera "Device or Resource Busy"

**Symptoms:**
```
ERROR - Cannot open camera at /dev/video0
cv2.error: (-2:Unspecified error) VIDIOC_STREAMON: Device or resource busy
```

**Root Cause:** Another process is using the camera

**Solution:**
```bash
# Find process using camera
sudo lsof /dev/video0

# Output shows:
# COMMAND   PID  USER   FD   TYPE
# python   1234 unitree  5u   CHR

# Kill the process
sudo kill 1234

# Or reboot if unclear
sudo reboot
```

---

### Issue 4: No Audio Output (Silent)

**Symptoms:**
```
INFO - [TTS] Playing: "Hello and welcome..."
# But nothing is heard
```

**Root Cause:** Wrong audio device, muted, or volume too low

**Solution:**
```bash
# Check volume
alsamixer
# Press F6 to select sound card
# Use arrow keys to increase volume
# Press M to unmute if needed

# Test speaker
speaker-test -t wav -c 2

# List audio devices
aplay -L

# Test Piper directly
echo "test" | piper \
    --model ~/.local/share/piper/voices/en/en_US/ryan/medium/en_US-ryan-medium.onnx \
    --output_file test.wav
aplay test.wav

# If using HDMI audio, set default:
sudo nano /etc/asound.conf
# Add:
pcm.!default {
    type hw
    card 0
}
ctl.!default {
    type hw
    card 0
}
```

---

### Issue 5: "Model Not Found"

**Symptoms:**
```
ERROR - Model llama3.1:8b not found in Ollama
```

**Root Cause:** Models not downloaded or Ollama can't find them

**Solution:**
```bash
# Check Ollama is running
sudo systemctl status ollama

# List downloaded models
ollama list

# If empty, download:
ollama pull llama3.1:8b
ollama pull llava-llama3

# If models exist but not detected:
# Check Ollama model directory
ls -la ~/.ollama/models/

# Restart Ollama
sudo systemctl restart ollama

# Try again
ollama list
```

---

### Issue 6: Agent Starts but Doesn't Respond to Speech

**Symptoms:**
- Agent starts successfully
- Greeting plays
- But doesn't respond when you talk

**Root Cause:** Microphone not working or wrong device selected

**Solution:**
```bash
# Test microphone
arecord -D hw:0,0 -f S16_LE -r 16000 -c 1 -d 5 test_mic.wav
# Speak for 5 seconds
aplay test_mic.wav
# You should hear yourself

# If silent, try different device:
arecord -l  # List all devices
arecord -D hw:1,0 -f S16_LE -r 16000 -c 1 -d 5 test_mic2.wav
aplay test_mic2.wav

# Update config with working device
nano config/astra_vein_receptionist.json5
# Change input_device to working device number

# Check permissions
groups $USER
# Should include "audio"

# If not:
sudo usermod -a -G audio $USER
# Logout and login
```

---

### Issue 7: Python Import Errors

**Symptoms:**
```
ModuleNotFoundError: No module named 'pyaudio'
ModuleNotFoundError: No module named 'faster_whisper'
```

**Root Cause:** Dependencies not installed properly

**Solution:**
```bash
# Reinstall dependencies
cd ~/roboai-espeak
uv sync

# If using venv instead of uv:
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run with uv (recommended):
uv run src/run.py astra_vein_receptionist
```

---

## 📊 Performance Optimization

### For Jetson Orin (with CUDA/GPU)

If your G1 has NVIDIA Jetson Orin, enable GPU acceleration:

```bash
# Check CUDA availability
python3 -c "import torch; print('CUDA:', torch.cuda.is_available())"
```

If `True`, edit config:
```json5
{
  "config": {
    "device": "cuda",           // Use GPU
    "compute_type": "float16",  // Fast GPU mode
    "model_size": "small.en"    // Larger model possible with GPU
  }
}
```

### For CPU-Only (or Slow Performance)

Use smaller models:
```json5
{
  "config": {
    "device": "cpu",
    "compute_type": "int8",     // Fast CPU mode
    "model_size": "tiny.en"     // Smallest, fastest model
  }
}
```

Download smaller Ollama model:
```bash
ollama pull llama3:8b  # Or even smaller:
ollama pull phi3:mini
```

---

## 📱 Web Control Panel (Optional)

Set up browser-based control:

```bash
./setup_robostore_ai.sh
```

Access at: `http://<g1-ip-address>:8000`

Features:
- Start/stop agent
- View live status
- Check logs
- Update configuration
- Restart services

---

## 🌐 WiFi Hotspot Setup (Optional)

Create a WiFi network hosted by the G1:

```bash
./setup_g1_hotspot.sh
```

Network details:
- **SSID**: `G1-Receptionist`
- **Password**: `astra2024`
- **IP**: `192.168.50.1`

Connect devices to this network to access web panel without router.

---

## 🎓 System Architecture

```
G1 Robot (Ubuntu 22.04 / Jetson Orin NX)
│
├── 🎤 Audio Input Pipeline
│   ├── USB Microphone (hw:0,0) - 16000 Hz
│   ├── ALSA (arecord/aplay)
│   ├── PyAudio (device index mapping)
│   └── Faster-Whisper ASR (speech-to-text)
│
├── 📷 Vision Pipeline
│   ├── USB Camera (/dev/video0)
│   ├── OpenCV (frame capture)
│   └── Ollama Vision (llava-llama3) - compliments
│
├── 🧠 Language Model
│   ├── Ollama Server (localhost:11434) ⚠️ Must be running!
│   ├── llama3.1:8b (conversation)
│   └── Custom medical receptionist prompts
│
├── 🔊 Audio Output Pipeline
│   ├── Piper TTS (en_US-ryan-medium.onnx)
│   ├── WAV file generation
│   └── aplay (ALSA playback)
│
└── 🤖 Robot Control (Optional)
    ├── Unitree SDK
    ├── Ethernet connection (eno1)
    └── Arm gestures (wave, point, etc.)
```

---

## 📚 Related Documentation

- **`G1_AUDIO_AUTO_FIX.md`** - Deep dive into audio auto-detection
- **`G1_HARDWARE_TESTING.md`** - Manual hardware testing commands
- **`G1_ARM_INTEGRATION_GUIDE.md`** - Robot arm gesture programming
- **`FASTER_WHISPER_INSTALL.md`** - ASR installation and optimization
- **`check_g1_hardware.py`** - Hardware validation script
- **`test_g1_hardware.sh`** - Interactive testing suite

---

## 🆘 Still Having Issues?

### Debug Mode

Run with verbose logging:
```bash
uv run src/run.py astra_vein_receptionist --debug
```

### Collect Diagnostic Information

```bash
# Generate full diagnostic report
./generate_diagnostic_report.sh

# Or manually:
echo "=== System Info ===" > diagnostic.txt
uname -a >> diagnostic.txt
python3 --version >> diagnostic.txt
echo "" >> diagnostic.txt

echo "=== Ollama Status ===" >> diagnostic.txt
sudo systemctl status ollama >> diagnostic.txt
ollama list >> diagnostic.txt
echo "" >> diagnostic.txt

echo "=== Audio Devices ===" >> diagnostic.txt
arecord -l >> diagnostic.txt
aplay -l >> diagnostic.txt
echo "" >> diagnostic.txt

echo "=== Video Devices ===" >> diagnostic.txt
ls -la /dev/video* >> diagnostic.txt
v4l2-ctl --list-devices >> diagnostic.txt
echo "" >> diagnostic.txt

echo "=== Hardware Check ===" >> diagnostic.txt
python3 check_g1_hardware.py >> diagnostic.txt

# Share diagnostic.txt for support
```

### Contact Support

- GitHub Issues: https://github.com/feraco/roboai-espeak/issues
- Include `diagnostic.txt` in your report
- Mention your G1 model and Ubuntu version

---

## 🎉 Success Indicators

Your G1 is production-ready when:

✅ **Hardware check** - All green, no errors  
✅ **Ollama running** - `sudo systemctl status ollama` shows active  
✅ **Models downloaded** - `ollama list` shows llama3.1:8b and llava-llama3  
✅ **Audio clear** - Greeting plays with good quality  
✅ **Speech recognition works** - Agent responds to questions  
✅ **Vision working** - Agent gives appropriate compliments  
✅ **Response time good** - < 3 seconds to respond  
✅ **Stable operation** - Runs for hours without crashes  
✅ **Auto-start enabled** - Works after reboot  

---

## 🚀 Next Steps

1. **Test extensively** - Try different questions, accents, volumes
2. **Train staff** - Show them how to restart if needed
3. **Monitor logs** - Check `journalctl -u roboai-astra-vein -f` daily
4. **Backup config** - `cp config/astra_vein_receptionist.json5 config/astra_vein_receptionist.json5.backup`
5. **Document custom changes** - Keep notes on any modifications
6. **Set up remote access** - SSH keys for maintenance
7. **Plan updates** - Schedule monthly `git pull` and `uv sync`

---

## 💡 Pro Tips

- **Ollama is critical** - If agent fails, first check: `sudo systemctl status ollama`
- **USB mics are best** - More reliable than built-in camera mics
- **Test after reboot** - Ensure auto-start works before deploying
- **Keep models updated** - `ollama pull llama3.1:8b` periodically
- **Monitor disk space** - Models use ~10 GB
- **Set static IP** - Makes reconnection easier
- **Label devices** - Physical label on G1 with IP and SSH credentials
- **Battery backup** - UPS recommended for graceful shutdowns

---

**Enjoy your AI-powered medical receptionist!** 🤖💙