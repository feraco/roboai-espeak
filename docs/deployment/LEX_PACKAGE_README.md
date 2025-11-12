# Lex Channel Chief Agent - Installation Guide

Complete installation guide for Lex agent on Jetson/Ubuntu ARM64.

---

## 🚀 Quick Install (Recommended) - COMPLETE SETUP

### **Step 1: Install Hardware Configuration Service (REQUIRED FIRST)**

This configures audio/video devices on every boot:

```bash
cd ~/roboai-espeak
git pull origin main
sudo bash scripts/installers/install_hardware_setup.sh
```

**What this does:**
- ✅ Auto-detects USB microphone and speaker
- ✅ Creates `/etc/asound.conf` with correct defaults
- ✅ Sets speaker volume to 100%, unmutes all channels
- ✅ Configures microphone capture
- ✅ Sets camera permissions
- ✅ Runs on every boot BEFORE agent starts

---

### **Step 2: Install Lex Agent Service**

```bash
cd ~/roboai-espeak
bash scripts/installers/install_lex_service_robust.sh
```

**What this does:**
- ✅ Installs Lex as systemd service
- ✅ Enables auto-start on boot
- ✅ Comprehensive pre-start hardware checks
- ✅ Validates Ollama + llama3.1:8b model
- ✅ Checks Piper TTS and voice models
- ✅ Starts Lex agent immediately

---

### **Step 3: Verify Installation**

```bash
# Check hardware setup
sudo systemctl status roboai-hardware-setup
cat /etc/roboai-devices.conf

# Check Lex agent
sudo systemctl status lex_agent

# Watch live logs
sudo journalctl -u lex_agent -f
```

---

## 📋 Expected Output

### Hardware Setup Service:
```
[HW-Setup] ✅ USB Microphone detected: card 1, device 0
[HW-Setup] ✅ USB Speaker detected: card 0, device 0
[HW-Setup] ✅ ALSA config written to /etc/asound.conf
[HW-Setup] ✅ Speaker unmuted and volume set to 100%
[HW-Setup] ✅ Camera permissions set: /dev/video0
```

### Lex Agent Service:
```
[LexPreStart] ✅ USB microphone detected
[LexPreStart] ✅ USB speaker detected
[LexPreStart] ✅ Camera detected
[LexPreStart] ✅ Ollama is responsive
[LexPreStart] ✅ Model llama3.1:8b is available
[LexPreStart] ✅ Piper TTS is installed
[LexPreStart] ✅ All critical checks passed!
INFO - 🔊 Playing audio with command: aplay -D plughw:0,0
INFO - Badge reader camera initialized
```

---

## 🔧 Update Existing Installation

```bash
cd ~/roboai-espeak
git pull origin main

# Reinstall hardware service (if updated)
sudo bash scripts/installers/install_hardware_setup.sh

# Reinstall Lex service
bash scripts/installers/install_lex_service_robust.sh

# Restart services
sudo systemctl restart roboai-hardware-setup
sudo systemctl restart lex_agent
```

---

## 📦 Alternative: Build .deb Package

### Step 1: Prepare Package (On Mac)

```bash
# On your Mac
cd /path/to/roboai-espeak
./build_lex_deb.sh
```

This creates `lex_package/lex-agent_1.0.0_arm64/` with all files.

### Step 2: Copy to Jetson

```bash
# Copy package folder and build script
scp -r lex_package build_deb_on_jetson.sh unitree@JETSON_IP:~/
```

### Step 3: Build on Jetson

```bash
# SSH to Jetson
ssh unitree@JETSON_IP

# Build the .deb
bash build_deb_on_jetson.sh
```

### Step 4: Install

```bash
# Install the package
sudo dpkg -i lex_package/lex-agent_1.0.0_arm64.deb

# Fix any missing dependencies
sudo apt install -f -y

# Check status
sudo systemctl status lex-agent
```

## What Gets Installed

- **Application**: `/opt/roboai-lex/` (all source code)
- **Service**: `/etc/systemd/system/lex-agent.service` (auto-start on boot)
- **Command**: `/usr/local/bin/lex-agent` (run manually)
- **Dependencies**: Ollama, Piper TTS, UV, Python packages

## Post-Installation

The package automatically:
1. Installs UV package manager
2. Installs and starts Ollama
3. Downloads llama3.1:8b model (~4.7 GB)
4. Installs Piper TTS
5. Downloads English and Russian TTS voices
6. Installs Python dependencies
7. Enables and starts lex-agent service

## Service Management

```bash
# Check hardware setup service
sudo systemctl status roboai-hardware-setup
sudo journalctl -u roboai-hardware-setup

# Check Lex agent service
sudo systemctl status lex_agent
sudo journalctl -u lex_agent -f

# Restart services
sudo systemctl restart roboai-hardware-setup  # Re-detect hardware
sudo systemctl restart lex_agent              # Restart agent

# Stop/start
sudo systemctl stop lex_agent
sudo systemctl start lex_agent

# Disable auto-start
sudo systemctl disable lex_agent
```

---

## 🔍 Troubleshooting

### No Audio Output

```bash
# Check hardware setup ran
sudo systemctl status roboai-hardware-setup
cat /etc/roboai-devices.conf

# Check ALSA config
cat /etc/asound.conf

# Test speaker directly
aplay -D plughw:0,0 /usr/share/sounds/alsa/Front_Center.wav

# Re-run hardware setup
sudo systemctl restart roboai-hardware-setup
```

### Badge Reader Not Working

```bash
# Check camera permissions
ls -l /dev/video*

# Test camera
python3 scripts/testing/test_camera_vision.py

# Check logs for badge detection
sudo journalctl -u lex_agent | grep -i badge
```

### Ollama Not Responding

```bash
# Check Ollama service
sudo systemctl status ollama

# Check model is downloaded
ollama list | grep llama3.1:8b

# Download model if missing
ollama pull llama3.1:8b
```

---

## Manual Run (Without Service)

```bash
# Stop service first
sudo systemctl stop lex_agent

# Run manually for debugging
cd ~/roboai-espeak
uv run src/run.py lex_channel_chief
```

---

## ✅ Health Check Checklist

Run these commands to verify everything is working:

```bash
# 1. Hardware setup service
sudo systemctl is-active roboai-hardware-setup  # Should show: active

# 2. Device configuration exists
test -f /etc/roboai-devices.conf && echo "✅ Device config found" || echo "❌ Missing"

# 3. ALSA config exists
test -f /etc/asound.conf && echo "✅ ALSA config found" || echo "❌ Missing"

# 4. Lex agent running
sudo systemctl is-active lex_agent  # Should show: active

# 5. Ollama responsive
curl -s http://localhost:11434/api/tags | grep llama3.1 && echo "✅ Ollama OK" || echo "❌ Ollama issue"

# 6. Camera accessible
test -e /dev/video0 && echo "✅ Camera found" || echo "❌ No camera"

# 7. Check recent logs for errors
sudo journalctl -u lex_agent --since "5 minutes ago" | grep -i error
```

---

## 🎯 Installation Order Summary

**CRITICAL: Install in this order!**

1. **Hardware Service** → Configures devices on boot
2. **Lex Agent Service** → Depends on hardware service
3. **Verify** → Check logs and status

---

## Updating

```bash
# Stop service
sudo systemctl stop lex-agent

# Update code
cd /opt/roboai-lex
git pull origin main
uv sync

# Restart service
sudo systemctl restart lex-agent
```

## Uninstall

```bash
# Remove package
sudo apt remove lex-agent

# Purge all files (including /opt/roboai-lex)
sudo apt purge lex-agent

# Optional: Remove Ollama
sudo systemctl stop ollama
sudo systemctl disable ollama
sudo rm /usr/local/bin/ollama
sudo rm -rf ~/.ollama
```

## Troubleshooting

### Package Installation Fails

```bash
# Check for missing dependencies
sudo apt install -f

# View detailed error
sudo dpkg -i lex-agent_1.0.0_arm64.deb
```

### Service Won't Start

```bash
# Check logs
sudo journalctl -u lex-agent -n 100

# Common issues:
# 1. Ollama not running: sudo systemctl start ollama
# 2. Model not downloaded: ollama pull llama3.1:8b
# 3. UV not in PATH: export PATH="$HOME/.local/bin:$PATH"
```

### Audio Issues

```bash
# Test microphone
cd /opt/roboai-lex
python3 test_microphone.py

# Test camera
python3 test_camera.py

# Restart audio
pulseaudio --kill && sleep 2 && pulseaudio --start
```

## Package Contents

```
lex-agent_1.0.0_arm64/
├── DEBIAN/
│   ├── control          # Package metadata
│   ├── postinst         # Post-install script (downloads models, starts service)
│   ├── prerm            # Pre-remove script (stops service)
│   └── postrm           # Post-remove script (cleanup)
├── opt/roboai-lex/      # Application files
│   ├── src/             # Source code
│   ├── config/          # Agent configurations
│   ├── docs/            # Knowledge base
│   └── ...
├── etc/systemd/system/
│   └── lex-agent.service  # Systemd service
└── usr/local/bin/
    └── lex-agent        # Convenience command
```

## Files

- `build_lex_deb.sh` - Prepare package structure (run on Mac)
- `build_deb_on_jetson.sh` - Build .deb file (run on Jetson)
- `install_lex_jetson.sh` - All-in-one installer (easiest method)
- `LEX_PACKAGE_README.md` - This file

## Support

- GitHub: https://github.com/feraco/roboai-espeak
- Issues: https://github.com/feraco/roboai-espeak/issues
