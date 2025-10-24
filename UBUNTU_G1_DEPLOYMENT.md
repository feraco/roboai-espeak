# 🤖 Complete Ubuntu G1 Deployment Guide

## 🎯 Overview

This guide provides step-by-step instructions to deploy the Astra Vein receptionist agent on your Unitree G1 robot running Ubuntu 22.04.

## 📋 Prerequisites

- Unitree G1 robot with Ubuntu 22.04
- SSH access to G1
- Internet connection
- Sudo privileges

## 🚀 Quick Start

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

# 7. Pull AI models
ollama pull llama3.1:8b
ollama pull llava-llama3

# 8. Run hardware check
python3 check_g1_hardware.py

# 9. If all checks pass, run the agent
uv run src/run.py astra_vein_receptionist
```

## 📦 Detailed Installation Steps

### Step 1: System Dependencies

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

### Step 7: Hardware Check

```bash
python3 check_g1_hardware.py
```

**Expected output:**
```
🤖 G1 HARDWARE STARTUP CHECK
==================================================

🎤 MICROPHONE:
  ✅ OK - USB2.0 Device
     Device: hw:0,0
     Sample rate: 16000 Hz

🔊 SPEAKER:
  ✅ OK - 1 output device(s) found

📷 CAMERA:
  ✅ OK - Camera at /dev/video0

🧠 OLLAMA LLM:
  ✅ OK - Ollama running
     Models: llama3.1:8b, llava-llama3

👁️  OLLAMA VISION:
  ✅ OK - Vision model available: llava-llama3

🎵 PIPER TTS:
  ✅ OK - Piper voices found
     Path: /home/unitree/.local/share/piper/voices

✅ ALL SYSTEMS GO - Ready to start agent
```

### Step 8: Test Run

```bash
uv run src/run.py astra_vein_receptionist
```

**What should happen:**
1. Agent starts and loads models
2. Camera opens (you should see log messages)
3. "Hello and welcome..." greeting plays through speakers
4. Agent listens for speech input
5. Responds to questions about the medical practice

**Test it:**
- Say "What are your hours?"
- Say "Where are you located?"
- Say "Tell me about the doctor"

Press `Ctrl+C` to stop.

## 🔧 Configuration

### Audio Configuration

The config now uses auto-detection:

```json5
{
  "config": {
    "input_device": 0,        // USB mic (auto-detected)
    "sample_rate": 16000,     // Auto-adjusted
    "play_command": null      // aplay (auto-detected)
  }
}
```

### Manual Audio Testing

```bash
# Test microphone
arecord -D hw:0,0 -f S16_LE -r 16000 -c 1 -d 3 test.wav
aplay test.wav

# Test camera
python3 -c "import cv2; cap=cv2.VideoCapture(0); print('Camera OK:', cap.isOpened()); cap.release()"

# Test Ollama
ollama run llama3.1:8b "Hello"
```

### Ethernet Interface

Update in config if needed:

```json5
{
  unitree_ethernet: "eno1"  // Change to your interface
}
```

Find your interface:
```bash
ip addr show | grep "state UP"
```

## 🔄 Auto-Start on Boot

Once everything works, set up auto-start:

```bash
./setup_g1_autostart.sh
```

This creates a systemd service that:
- Starts automatically on boot
- Restarts on failure
- Runs as your user
- Logs to system journal

**Control the service:**
```bash
# Check status
sudo systemctl status roboai-astra-vein

# View logs
journalctl -u roboai-astra-vein -f

# Stop/start
sudo systemctl stop roboai-astra-vein
sudo systemctl start roboai-astra-vein

# Disable auto-start
sudo systemctl disable roboai-astra-vein
```

## 📱 Web Control Panel (Optional)

Set up the web interface for non-technical users:

```bash
./setup_robostore_ai.sh
```

Access at: `http://g1-ip-address:8000`

## 🌐 Hotspot Setup (Optional)

Create a WiFi hotspot on the G1:

```bash
./setup_g1_hotspot.sh
```

Connect to: **G1-Receptionist** (password: `astra2024`)

## 🐛 Troubleshooting

### Audio Issues

**Problem:** "Invalid sample rate" errors

**Solution:**
```bash
# Run diagnostic
python3 check_g1_hardware.py

# Test manually
arecord -l  # List devices
arecord -D hw:0,0 -f S16_LE -r 16000 -c 1 -d 3 test.wav
```

### Camera Issues

**Problem:** Camera not accessible

**Solution:**
```bash
# Check camera
ls -la /dev/video0

# Fix permissions
sudo chmod 666 /dev/video0

# Add user to video group
sudo usermod -a -G video $USER
# Logout and login again
```

### Ollama Issues

**Problem:** Ollama not responding

**Solution:**
```bash
# Check service
sudo systemctl status ollama

# Restart service
sudo systemctl restart ollama

# Check logs
journalctl -u ollama -f
```

### Piper TTS Issues

**Problem:** Voice not found

**Solution:**
```bash
# Re-run setup
./setup_piper_ubuntu.sh

# Test directly
echo "test" | piper \
    --model ~/.local/share/piper/voices/en/en_US/ryan/medium/en_US-ryan-medium.onnx \
    --output_file test.wav
```

### Import Errors

**Problem:** Module not found errors

**Solution:**
```bash
# Reinstall dependencies
cd ~/roboai-espeak
uv sync

# Or use venv
uv run src/run.py astra_vein_receptionist
```

## 📊 Performance Tuning

### For Jetson Orin (with CUDA)

Update config:
```json5
{
  "config": {
    "device": "cuda",
    "compute_type": "float16",
    "model_size": "small.en"
  }
}
```

### For CPU-Only

Use smaller models:
```json5
{
  "config": {
    "device": "cpu",
    "compute_type": "int8",
    "model_size": "tiny.en"
  }
}
```

## 📋 Pre-Deployment Checklist

- [ ] All system dependencies installed
- [ ] UV package manager working
- [ ] Piper TTS installed and tested
- [ ] Ollama running with models
- [ ] `check_g1_hardware.py` - all GREEN
- [ ] Audio input/output tested
- [ ] Camera working
- [ ] Test run successful
- [ ] Ethernet interface configured
- [ ] Auto-start configured (if desired)
- [ ] Web panel configured (if desired)
- [ ] Hotspot configured (if desired)

## 🎓 Architecture Overview

```
G1 Robot (Ubuntu 22.04)
├── Audio Input (USB Mic / Camera Mic)
│   └── PyAudio + ALSA
│       └── Faster-Whisper ASR
├── Camera (USB / Built-in)
│   └── OpenCV
│       └── Ollama Vision (llava-llama3)
├── LLM Brain
│   └── Ollama (llama3.1:8b)
│       └── Custom prompts for medical receptionist
├── Audio Output
│   └── Piper TTS (en_US-ryan-medium)
│       └── ALSA (aplay)
└── Robot Control (if enabled)
    └── Unitree SDK (arm gestures)
        └── Ethernet connection to robot
```

## 📚 Related Documentation

- `G1_AUDIO_AUTO_FIX.md` - Audio system auto-detection guide
- `G1_HARDWARE_TESTING.md` - Manual hardware testing commands
- `G1_ARM_INTEGRATION_GUIDE.md` - Arm gesture control guide
- `FASTER_WHISPER_INSTALL.md` - ASR installation details

## 🆘 Getting Help

If you encounter issues:

1. **Check logs:**
   ```bash
   journalctl -u roboai-astra-vein -f
   ```

2. **Run diagnostics:**
   ```bash
   python3 check_g1_hardware.py
   python3 -m src.audio_system_fixer
   ```

3. **Test components individually:**
   - Microphone: `arecord -D hw:0,0 -f S16_LE -r 16000 -c 1 -d 3 test.wav`
   - Speaker: `aplay test.wav`
   - Camera: `python3 -c "import cv2; print(cv2.VideoCapture(0).isOpened())"`
   - Ollama: `ollama list`
   - Piper: `echo "test" | piper --model ~/.local/share/piper/voices/en/en_US/ryan/medium/en_US-ryan-medium.onnx --output_file test.wav`

## 🎉 Success!

Once everything is working, your G1 should:
- ✅ Automatically start on boot
- ✅ Greet patients with camera-based compliments
- ✅ Respond to voice questions accurately
- ✅ Use arm gestures for emphasis (if enabled)
- ✅ Run 24/7 reliably

Enjoy your AI-powered medical receptionist! 🤖