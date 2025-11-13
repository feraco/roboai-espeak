# Jetson Autostart Deployment Guide - Astra Vein Receptionist

Complete guide for deploying the Astra Vein receptionist agent with robust device detection on Jetson Orin Nano.

## Overview

This deployment ensures:
- ✅ RealSense camera 4 detection (with wait timeout)
- ✅ USB audio devices detection (microphone + speaker)
- ✅ PulseAudio defaults set automatically
- ✅ Device persistence across reboots
- ✅ G1 arm gesture integration
- ✅ Multi-language TTS support (English, Spanish, Russian)

## Prerequisites

### Hardware
- Jetson Orin Nano (tested with JetPack 5.x/6.x)
- Intel RealSense D435i camera (connected via USB 3.0)
- USB PnP Sound Device (microphone)
- USB 2.0 Speaker (audio output)
- Unitree G1 humanoid robot (optional, for arm gestures)

### Software
- Ubuntu 20.04 or 22.04 (JetPack)
- Python 3.8+
- uv package manager
- Ollama with llama3.1:8b model
- RealSense SDK installed (see `INSTALL_REALSENSE_JETSON.md`)

## Installation Steps

### 1. Clone and Setup Repository

```bash
# SSH to Jetson
ssh unitree@192.168.123.18

# Clone repository (if not already done)
cd ~/
git clone https://github.com/feraco/roboai-espeak.git roboai-feature-multiple-agent-configurations
cd roboai-feature-multiple-agent-configurations

# Install dependencies
uv sync
```

### 2. Install RealSense Camera

Follow the complete guide: `documentation/setup/INSTALL_REALSENSE_JETSON.md`

Quick verification:
```bash
v4l2-ctl --list-devices | grep -A 5 RealSense
# Should show /dev/video4 (or another index)
```

### 3. Configure Audio Devices

```bash
# List audio input devices (microphone)
pactl list short sources

# List audio output devices (speaker)
pactl list short sinks

# Test microphone
python3 test_microphone.py

# Verify USB devices are detected:
# - USB PnP Sound Device (input)
# - USB 2.0 Speaker (output)
```

### 4. Install Ollama and LLM Model

```bash
# Install Ollama (if not already installed)
curl -fsSL https://ollama.com/install.sh | sh

# Pull llama3.1:8b model
ollama pull llama3.1:8b

# Verify model
ollama list | grep llama3.1
```

### 5. Configure Agent

The config `config/astra_vein_receptionist_arm.json5` should have:

```json5
{
  name: "astra_vein_receptionist_arm",
  hertz: 1,
  
  // LLM Configuration (CPU-only for thermal management)
  cortex_llm: {
    type: "OllamaLLM",
    config: {
      model: "llama3.1:8b",
      base_url: "http://localhost:11434",
      timeout: 40,
      num_gpu: 0,  // ← CPU-only to avoid thermal throttling
      history_length: 3,
      temperature: 0.7
    }
  },
  
  // Unitree G1 connection
  unitree_ethernet: "eno1",  // ← Your Ethernet interface name
  
  // Inputs
  agent_inputs: [
    {
      type: "LocalASRInput",
      config: {
        input_device: null,  // ← Auto-detect USB microphone
        // ... other settings
      }
    },
    {
      type: "FaceEmotionCapture",
      config: {
        camera_index: 4,  // ← RealSense RGB camera (verify with v4l2-ctl)
        poll_interval: 60.0,
        timeout: 5
      }
    }
  ],
  
  // Actions
  agent_actions: [
    {
      name: "speak",
      llm_label: "speak",
      connector: "piper_tts",
      config: {
        model: "en_US-kristin-medium",
        model_es: "es_ES-davefx-medium",
        model_ru: "ru_RU-dmitri-medium",
        play_command: "paplay"  // ← USB 2.0 Speaker
      }
    },
    {
      name: "arm_g1",
      llm_label: "arm_movement",
      connector: "unitree_sdk",  // ← Uses G1 SDK (mock_print for Mac)
      config: {}
    }
  ]
}
```

**Verify Ethernet Interface:**
```bash
ip link show | grep -E "^[0-9]+:"
# Look for "eno1", "eth0", "enp*", etc.
# Update unitree_ethernet in config if different
```

### 6. Test Agent Manually

```bash
# Test without autostart first
uv run src/run.py astra_vein_receptionist_arm

# Expected startup logs:
# - FaceEmotionCapture using camera index 4
# - LocalASRInput: Using saved audio config - device 1 (USB PnP Sound Device)
# - Speak action using USB 2.0 Speaker
# - G1 arm action client connected

# Test face detection (look at camera)
# Test voice (say "Hello")
# Test gestures (say "wave hello")
```

### 7. Install Robust Autostart

```bash
# Run the installer script
bash scripts/installers/install_astra_autostart_robust.sh

# The installer will:
# 1. Make pre-start checks executable
# 2. Test device detection
# 3. Stop old service
# 4. Install new service file
# 5. Enable autostart
# 6. Start the service

# Watch logs
sudo journalctl -u astra_agent -f
```

**Expected Pre-Start Output:**
```
==========================================
Astra Agent Pre-Start Checks
==========================================
⏳ Waiting for RealSense camera 4...
✅ RealSense camera 4 ready
⏳ Waiting for USB PnP Sound Device (microphone)...
✅ USB microphone ready
⏳ Waiting for USB 2.0 Speaker...
✅ USB speaker ready
🔧 Setting audio defaults...
✅ Default microphone: alsa_input.usb-C-Media_Electronics_Inc._USB_PnP_Sound_Device
✅ Default speaker: alsa_output.usb-Generic_USB2.0_Speaker
✅ Pre-start checks complete
==========================================
```

### 8. Test Autostart After Reboot

```bash
# Reboot Jetson
sudo reboot

# After reboot (wait ~2 minutes for full startup)
ssh unitree@192.168.123.18

# Check service status
sudo systemctl status astra_agent

# Should show: "active (running)"

# Check logs
sudo journalctl -u astra_agent -n 200

# Verify device detection
sudo journalctl -u astra_agent | grep -E "(camera|microphone|speaker|RealSense|USB)"
```

## System Architecture

### Service Files

**`deployment/astra_vein_autostart.service`** - Systemd service
- Runs as user `unitree`
- Executes pre-start checks before agent start
- Restarts on failure (10s delay)
- CPU quota: 80%, Memory limit: 2G

**`deployment/astra_pre_start_checks.sh`** - Device detection script
- Waits up to 60s for each device (RealSense, mic, speaker)
- Sets PulseAudio defaults via `pactl`
- Deletes `device_config.yaml` to force re-detection
- Logs all detection steps

### Code Components

**`src/inputs/plugins/webcam_to_face_emotion.py`** - Face detection
- Now reads `camera_index` from config (fixed hardcoded bug)
- Uses DeepFace for emotion analysis
- Logs selected camera index at startup

**`src/fuser/__init__.py`** - Prompt orchestration
- Proactive greeting system (greets once per 5 minutes)
- Returns empty actions for vision-only scenarios (no announcement)
- Combines all input buffers into unified LLM prompt

**`src/actions/arm_g1/`** - Arm gesture system
- Interface: 8 gestures (idle, high_wave, heart, clap, high_five, shake_hand, left_kiss, right_kiss)
- SDK Connector: Maps to G1ArmActionClient (DDS communication)
- Mock Connector: Console printing for Mac testing

## Management Commands

### Service Control

```bash
# Check status
sudo systemctl status astra_agent

# View logs (live)
sudo journalctl -u astra_agent -f

# View recent logs
sudo journalctl -u astra_agent -n 100

# Restart agent
sudo systemctl restart astra_agent

# Stop agent
sudo systemctl stop astra_agent

# Disable autostart
sudo systemctl disable astra_agent

# Re-enable autostart
sudo systemctl enable astra_agent
```

### Debugging Commands

```bash
# Check RealSense detection
v4l2-ctl --list-devices | grep -A 5 RealSense

# Test camera manually
python3 -c "import cv2; cap=cv2.VideoCapture(4); print('Camera 4:', cap.isOpened())"

# Check PulseAudio sources (microphone)
pactl list short sources | grep USB

# Check PulseAudio sinks (speaker)
pactl list short sinks | grep USB

# View pre-start check logs
sudo journalctl -u astra_agent | grep "Pre-Start" -A 20

# Check device config persistence
cat device_config.yaml

# Monitor thermal status (Jetson)
tegrastats

# Check Ollama running
pgrep ollama || echo "Ollama not running"
```

### Update Deployment

```bash
# Pull latest code
cd ~/roboai-feature-multiple-agent-configurations
git pull origin main
uv sync

# Restart service to apply changes
sudo systemctl restart astra_agent

# Watch startup
sudo journalctl -u astra_agent -f
```

## Troubleshooting

### Camera Not Detected

**Symptom:** Pre-start checks timeout waiting for RealSense
```
⚠️  Timeout waiting for RealSense camera
```

**Solutions:**
```bash
# 1. Verify camera connected
lsusb | grep Intel

# 2. Check dmesg for errors
dmesg | grep -i realsense

# 3. Reinstall RealSense SDK
# See documentation/setup/INSTALL_REALSENSE_JETSON.md

# 4. Try different USB 3.0 port

# 5. Update camera index in config if it changed
v4l2-ctl --list-devices | grep -A 10 RealSense
# Update camera_index in config/astra_vein_receptionist_arm.json5
```

### Audio Devices Not Detected

**Symptom:** Pre-start checks can't find USB devices
```
⚠️  Timeout waiting for USB microphone
⚠️  Timeout waiting for USB speaker
```

**Solutions:**
```bash
# 1. List all audio devices
pactl list short sources  # Microphone
pactl list short sinks     # Speaker

# 2. Check USB connections
lsusb

# 3. Restart PulseAudio
pulseaudio -k
pulseaudio --start

# 4. Set defaults manually
MIC=$(pactl list short sources | grep "USB_PnP" | awk '{print $2}' | head -n1)
SPEAKER=$(pactl list short sinks | grep "USB_2.0" | awk '{print $2}' | head -n1)
pactl set-default-source "$MIC"
pactl set-default-sink "$SPEAKER"

# 5. Update device names in pre-start script if different
nano deployment/astra_pre_start_checks.sh
```

### LLM Timeouts

**Symptom:** "No output from LLM" errors

**Solutions:**
```bash
# 1. Check thermal throttling
tegrastats
# If GPU temp > 80°C, ensure num_gpu: 0 in config

# 2. Verify Ollama running
systemctl status ollama
# Or: pgrep ollama

# 3. Test LLM manually
ollama run llama3.1:8b "Say hello"

# 4. Increase timeout in config
# cortex_llm.config.timeout: 40  (or higher)

# 5. Check CPU usage
htop
# Ensure system not overloaded
```

### Arm Gestures Not Working

**Symptom:** Agent doesn't perform arm movements

**Possible causes:**
1. **G1 not connected** - Check `unitree_ethernet` config matches your interface
2. **LLM not generating arm_movement actions** - Check system_prompt_examples
3. **DDS communication issues** - Verify G1 SDK connection

**Solutions:**
```bash
# 1. Verify Ethernet interface
ip link show | grep eno1  # Or your interface name

# 2. Test G1 connection
# (Requires G1-specific testing tools)

# 3. Check logs for arm action attempts
sudo journalctl -u astra_agent | grep -i "arm"

# 4. Use Mac demo config for testing (mock connector)
# See config/astra_vein_arm_demo_mac.json5
```

### Service Won't Start After Reboot

**Symptom:** `systemctl status astra_agent` shows "failed" or "inactive"

**Solutions:**
```bash
# 1. Check service logs
sudo journalctl -u astra_agent -n 100

# 2. Verify paths in service file
cat /etc/systemd/system/astra_agent.service
# Ensure paths are absolute and correct

# 3. Test pre-start script manually
bash deployment/astra_pre_start_checks.sh

# 4. Reload systemd daemon
sudo systemctl daemon-reload
sudo systemctl enable astra_agent
sudo systemctl start astra_agent

# 5. Check file permissions
ls -la deployment/astra_pre_start_checks.sh
# Should be executable (chmod +x)
```

## Performance Tuning

### Thermal Management (Jetson)

```json5
// config/astra_vein_receptionist_arm.json5
cortex_llm: {
  config: {
    num_gpu: 0,  // ← Force CPU-only (prevents GPU thermal throttling)
    timeout: 40,  // ← Longer timeout for CPU inference
  }
}
```

Monitor thermals:
```bash
tegrastats
# Watch GPU_TEMP - should stay < 80°C
```

### Resource Limits

The systemd service includes:
- `CPUQuota=80%` - Max 80% CPU usage
- `MemoryLimit=2G` - Max 2GB RAM
- `Nice=-10` - Higher priority than normal processes

Adjust in `deployment/astra_vein_autostart.service` if needed.

### Polling Intervals

```json5
// Face detection frequency
{
  type: "FaceEmotionCapture",
  config: {
    poll_interval: 60.0,  // ← Check every 60s (reduce for faster response)
  }
}
```

Lower values = faster detection but higher CPU usage.

## File Locations

```
roboai-feature-multiple-agent-configurations/
├── config/
│   └── astra_vein_receptionist_arm.json5  ← Main config
├── deployment/
│   ├── astra_vein_autostart.service       ← Systemd service
│   └── astra_pre_start_checks.sh          ← Device detection script
├── scripts/installers/
│   └── install_astra_autostart_robust.sh  ← Installation script
├── documentation/
│   ├── setup/
│   │   └── INSTALL_REALSENSE_JETSON.md    ← RealSense installation
│   └── deployment/
│       └── JETSON_AUTOSTART_GUIDE.md      ← This file
└── src/
    ├── fuser/__init__.py                  ← Prompt orchestration
    ├── inputs/plugins/
    │   ├── webcam_to_face_emotion.py      ← Face detection
    │   └── local_asr.py                   ← Voice input
    └── actions/
        ├── speak/                         ← TTS output
        └── arm_g1/                        ← G1 arm gestures
```

## Support

If issues persist:
1. Collect full logs: `sudo journalctl -u astra_agent --no-pager > astra_logs.txt`
2. Check hardware connections (USB 3.0 for camera, USB for audio)
3. Verify all prerequisites installed
4. Test components individually (camera, microphone, speaker, LLM)

## References

- [RealSense Installation Guide](./documentation/setup/INSTALL_REALSENSE_JETSON.md)
- [Project Quickstart](../../QUICKSTART.md)
- [Config Guide](../guides/CONFIG_GUIDE.md)
