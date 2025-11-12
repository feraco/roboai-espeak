# G1 Badge Reader Setup Guide
## Complete Installation and Configuration Instructions

This guide provides step-by-step instructions for installing and configuring the EasyOCR badge reader on the Unitree G1 humanoid robot with robust autostart service.

---

## Prerequisites

- Unitree G1 humanoid robot with Ubuntu
- Intel RealSense depth camera (D435/D455)
- SSH access to the robot
- Internet connection for downloading dependencies

---

## Complete Setup Process

### Step 1: SSH into G1

```bash
ssh unitree@192.168.123.18  # (or your G1's IP address)
# Password: 123
```

---

### Step 2: Pull Latest Code

```bash
cd ~/roboai-espeak
git pull origin main
```

**Expected output:**
```
Updating files...
Fast-forward
 src/inputs/plugins/badge_reader_easyocr.py | 347 ++++++++++++++++++
 src/fuser/__init__.py                      |  17 +-
 config/badge_reader_test_mac.json5         |  73 ++++
 ...
```

---

### Step 3: Install Dependencies

```bash
# Install EasyOCR for badge text recognition
uv add easyocr

# Sync all project dependencies
uv sync
```

**Note:** EasyOCR will download required models on first use (~10 seconds load time).

---

### Step 4: Install RealSense SDK

```bash
# Check if already installed
dpkg -l | grep realsense

# If NOT installed, install it:
sudo apt-get update
sudo apt-get install -y python3-pyrealsense2 librealsense2-utils

# Verify installation
realsense-viewer  # Should open viewer window
# Press Ctrl+C to exit
```

**Troubleshooting:**
- If `realsense-viewer` doesn't open, check USB connection
- Ensure camera is plugged into USB 3.0 port (blue port)
- Try: `lsusb | grep Intel` to confirm camera detected

---

### Step 5: Test RealSense Camera

```bash
cd ~/roboai-espeak

# Test with simple auto-detect script
python3 scripts/testing/test_realsense_badge_simple.py
```

**Interactive Test:**
- Camera preview window will open
- Write name on paper: **JOHN SMITH** (both first and last name)
- Hold badge in green box area
- Press **SPACE** to test OCR
- Press **'q'** to quit

**What to expect:**
```
✅ Found 1 RealSense device(s)
📷 Device: Intel RealSense D435
🚀 Starting pipeline with default configuration...
✅ Pipeline started with 4 stream(s):
   RGB: 1920x1080 @ 30fps
🔄 Loading EasyOCR model...
✅ EasyOCR ready (GPU enabled)!
```

**If you get "couldn't resolve requests" error:**
```bash
# Close any apps using camera
pkill realsense-viewer

# Check USB connection
lsusb | grep Intel
# Should see: "Intel Corp. Intel(R) RealSense(TM) Depth Camera"

# Try different USB port (must be USB 3.0)
```

---

### Step 6: Find Correct Camera Index

```bash
# List all available cameras with their indices
python3 scripts/testing/list_cameras.py
```

**Example output:**
```
Scanning cameras...
Camera 0: 640x480 ✅ (Depth/IR)
Camera 1: 640x480 ✅ (Depth/IR)
Camera 2: 640x480 ✅ (Depth/IR)
Camera 3: 1920x1080 ✅ (RGB) ← Use this one!
Camera 4: 1920x1080 ✅ (RGB alternate)

Summary:
- Found 5 working cameras
- Recommended RGB camera: 3 (1920x1080)
```

**Note the RGB camera number** (usually 3 or 4) - you'll need this for the config.

---

### Step 7: Update Lex Config for Badge Reader

```bash
# Open Lex configuration file
nano config/lex_channel_chief.json5

# Or if using different config:
# nano config/unitree_g1_humanoid.json5
```

**Add the badge reader input** to the `agent_inputs` array:

```json5
agent_inputs: [
  // Keep all existing inputs (ASR, GPS, battery, etc.)...
  
  // ADD this badge reader at the end:
  {
    type: "BadgeReaderEasyOCR",
    config: {
      camera_index: 3,           // Use the RGB camera number from Step 6
      poll_interval: 8.0,         // Check for badges every 8 seconds
      greeting_cooldown: 90.0,    // Don't re-greet same person for 90 seconds
      min_confidence: 0.75,       // Require 75%+ OCR confidence
      use_realsense: true,        // IMPORTANT: Use RealSense RGB stream
      realsense_width: 1920,      // RGB resolution
      realsense_height: 1080,
      realsense_fps: 30
    }
  }
],
```

**Save and exit:**
- Press `Ctrl+X`
- Press `Y` to confirm
- Press `Enter` to save

---

### Step 8: Update System Prompts

```bash
# Still in the config file
nano config/lex_channel_chief.json5
```

**Update `system_prompt_examples`** to include badge greeting examples:

```json5
system_prompt_examples: """
EXAMPLE 1 - Badge Detection:
INPUT: BADGE DETECTED: Greet John Smith. Say: 'Hi John, my name is Lex!'
OUTPUT: Speak: {'sentence': 'Hi John, my name is Lex! Welcome to the conference!', 'language': 'en'}

EXAMPLE 2 - Voice question:
INPUT: Voice: "What can you do?"
OUTPUT: Speak: {'sentence': 'I can greet people, answer questions, and help with navigation!', 'language': 'en'}

EXAMPLE 3 - Multiple inputs:
INPUT: Voice: "Hello" | BADGE DETECTED: Greet Sarah Johnson
OUTPUT: Speak: {'sentence': 'Hi Sarah! Great to meet you! How can I help today?', 'language': 'en'}
""",
```

**Optional: Update system prompt base** to mention badge reading capability:

```json5
system_prompt_base: """You are Lex, a friendly humanoid robot assistant at a conference.

Your capabilities:
- Greet people by reading their name badges
- Answer questions about the venue and schedule
- Provide directions and assistance
- Engage in natural conversation

You have these sensors:
- Badge reader (detects and reads name badges)
- Speech recognition (hears what people say)
- Vision (can see people and objects)
- GPS and navigation

Be warm, professional, and helpful!""",
```

**Save and exit:** `Ctrl+X`, `Y`, `Enter`

---

### Step 9: Test Badge Reader Manually (Before Service)

**Important:** Test manually first to ensure everything works before installing as a service.

```bash
# Run agent manually
cd ~/roboai-espeak
uv run src/run.py lex_channel_chief  # or your config name
```

**Test with a badge:**
1. Write on paper with dark marker:
   ```
   JOHN SMITH
   ```
   - Use LARGE CAPITAL LETTERS (1+ inch tall)
   - Both first AND last name required
   - Dark marker on white paper

2. Hold paper in front of camera (center of view)

3. Keep steady for 3-5 seconds

**Watch for these log messages:**
```
✅ Badge reader camera 3 initialized and ready
   Resolution: 1920x1080
📸 Badge reader captured frame: (1080, 1920, 3)
🤖 Running EasyOCR on frame...
📝 OCR detected: 'JOHN' (confidence: 0.98)
📝 OCR detected: 'SMITH' (confidence: 0.95)
✅ Name validation PASSED: John Smith - confirmed as person's name
✅ Badge detected: John Smith - triggering greeting
✅ Added message to buffer: BADGE DETECTED: Greet John Smith...

=== INPUT STATUS ===
Voice: No | Vision: No | Badge: Yes | Language: en

=== USER PROMPT ===
You have detected someone's badge with their name on it.
Follow the instructions in the badge input carefully...

[LLM generates response]
🔊 Playing audio...
✅ Audio playback completed
```

**If working correctly, you should hear:** "Hi John, my name is Lex! Welcome to the conference!"

**Press Ctrl+C to stop** when test is successful.

---

### Step 10: Install Robust Autostart Service

Once manual testing works, install the service for automatic startup on boot.

```bash
cd ~/roboai-espeak

# Stop any existing service
sudo systemctl stop lex_agent 2>/dev/null || true

# Install ROBUST autostart service
bash scripts/installers/install_lex_service_robust.sh
```

**Expected output:**
```
🚀 Installing Lex Agent ROBUST Service with Hardware Checks...
🛑 Stopping existing lex_agent service (if running)...
🔧 Making scripts executable...
📋 Installing ROBUST service file...
🔄 Reloading systemd...
✅ Service reloaded
🚀 Enabling auto-start...
✅ Service enabled
▶️  Starting service...
✅ Lex agent service started!

✅ LEX AGENT ROBUST SERVICE INSTALLED!

The service includes:
  - Hardware validation before start
  - Automatic Ollama startup
  - Retry logic on failures
  - Comprehensive logging

Service Commands:
  sudo systemctl status lex_agent      # Check status
  sudo systemctl start lex_agent       # Start service
  sudo systemctl restart lex_agent     # Restart service
  sudo systemctl stop lex_agent        # Stop service
  sudo journalctl -u lex_agent -f      # View logs
```

**What makes it "robust":**
- Runs `lex_pre_start_checks_robust.sh` before starting
- Validates camera, microphone, speakers availability
- Ensures Ollama is running
- Checks Python environment
- Automatic restart on failure (10 second delay)
- Better error logging and diagnostics

---

### Step 11: Verify Service is Running

```bash
# Check service status
sudo systemctl status lex_agent
```

**Expected output:**
```
● lex_agent.service - Lex AI Agent
     Loaded: loaded (/etc/systemd/system/lex_agent.service; enabled)
     Active: active (running) since Wed 2025-11-12 10:30:15 EST; 2min ago
   Main PID: 12345 (python3)
      Tasks: 8 (limit: 38312)
     Memory: 1.2G
     CGroup: /system.slice/lex_agent.service
             └─12345 python3 -m uv run src/run.py lex_channel_chief

Nov 12 10:30:15 g1-robot systemd[1]: Started Lex AI Agent.
Nov 12 10:30:18 g1-robot python3[12345]: ✅ Hardware checks passed
Nov 12 10:30:20 g1-robot python3[12345]: ✅ Badge reader initialized
```

**If status shows "failed":**
```bash
# View error logs
sudo journalctl -u lex_agent -n 50
```

---

### Step 12: Monitor Logs and Test Badge Reader

```bash
# Watch logs in real-time
sudo journalctl -u lex_agent -f
```

**Look for startup sequence:**
```
Nov 12 10:30:15 Starting Lex agent...
Nov 12 10:30:16 ✅ Hardware checks: PASSED
Nov 12 10:30:17 🔄 Loading Ollama llama3.1:8b...
Nov 12 10:30:18 ✅ LLM ready
Nov 12 10:30:19 🎥 Initializing badge reader camera 3...
Nov 12 10:30:20 ✅ Badge reader camera 3 initialized and ready
Nov 12 10:30:20    Resolution: 1920x1080
Nov 12 10:30:21 🔄 Loading EasyOCR model (one-time, ~10 seconds)...
Nov 12 10:30:31 ✅ EasyOCR ready!
Nov 12 10:30:31 🚀 Agent ready and listening...
```

**Hold badge in front of camera** and watch for:
```
Nov 12 10:31:05 📸 Badge reader captured frame: (1080, 1920, 3)
Nov 12 10:31:05 🤖 Running EasyOCR on frame...
Nov 12 10:31:06 📝 OCR detected: 'SARAH' (confidence: 0.96)
Nov 12 10:31:06 📝 OCR detected: 'JOHNSON' (confidence: 0.93)
Nov 12 10:31:06 ✅ Name validation PASSED: Sarah Johnson
Nov 12 10:31:06 ✅ Badge detected: Sarah Johnson - triggering greeting
Nov 12 10:31:07 Badge: Yes | Voice: No | Vision: No
Nov 12 10:31:08 🔊 Playing audio: "Hi Sarah, my name is Lex! Welcome!"
Nov 12 10:31:10 ✅ Audio playback completed
```

---

### Step 13: Filter Logs for Badge Activity

```bash
# Watch only badge-related logs
sudo journalctl -u lex_agent -f | grep -E "Badge|OCR|detected|Name validation"

# Or for full greeting pipeline
sudo journalctl -u lex_agent -f | grep -E "Badge|OCR|Fuser|LLM|speak"
```

---

## Service Management Commands

```bash
# View service status
sudo systemctl status lex_agent

# Start service
sudo systemctl start lex_agent

# Stop service
sudo systemctl stop lex_agent

# Restart service (after config changes)
sudo systemctl restart lex_agent

# Disable auto-start on boot
sudo systemctl disable lex_agent

# Enable auto-start on boot
sudo systemctl enable lex_agent

# View recent logs (last 100 lines)
sudo journalctl -u lex_agent -n 100

# View logs in real-time
sudo journalctl -u lex_agent -f

# View logs since last boot
sudo journalctl -u lex_agent -b

# View logs from specific time
sudo journalctl -u lex_agent --since "10 minutes ago"
sudo journalctl -u lex_agent --since "2025-11-12 10:00:00"
```

---

## Updating Code After Service Installed

When you make changes to the code or configuration:

```bash
# 1. Navigate to repo
cd ~/roboai-espeak

# 2. Pull latest changes from GitHub
git pull origin main

# 3. Update dependencies if needed
uv sync

# 4. Restart service to apply changes
sudo systemctl restart lex_agent

# 5. Watch logs to verify restart
sudo journalctl -u lex_agent -f
```

**Quick update command (one-liner):**
```bash
cd ~/roboai-espeak && git pull && uv sync && sudo systemctl restart lex_agent
```

---

## Troubleshooting

### Camera Not Found

**Symptoms:**
- "Failed to initialize camera"
- "Camera 3 could not be opened"

**Solutions:**
```bash
# Check RealSense connection
rs-enumerate-devices -c

# List all cameras
python3 scripts/testing/list_cameras.py

# Test RealSense specifically
python3 scripts/testing/test_realsense_badge_simple.py

# Check USB connection
lsusb | grep Intel
# Should see: "Intel Corp. Intel(R) RealSense(TM) Depth Camera"

# Try different USB 3.0 port (blue port)
```

---

### EasyOCR Not Loading

**Symptoms:**
- "Failed to load EasyOCR"
- "CUDA error" or "GPU not available"

**Solutions:**
```bash
# Check GPU status
nvidia-smi  # Should show GPU info

# Reinstall EasyOCR with GPU support
cd ~/roboai-espeak
uv remove easyocr
uv add easyocr

# Restart service
sudo systemctl restart lex_agent

# Check if CPU fallback works
# Edit config and add: gpu: false to badge reader config
```

---

### Service Won't Start

**Symptoms:**
- `systemctl status lex_agent` shows "failed"
- Service immediately stops after starting

**Solutions:**
```bash
# View detailed error logs
sudo journalctl -u lex_agent -n 100 --no-pager

# Common issues:
# 1. Config file syntax error
#    Fix: Validate JSON5 syntax in config file

# 2. Missing dependencies
#    Fix: cd ~/roboai-espeak && uv sync

# 3. Camera/hardware not available
#    Fix: Run hardware checks manually

# Test manually to see errors
cd ~/roboai-espeak
uv run src/run.py lex_channel_chief
# Watch for error messages

# If manual test works but service doesn't:
# Check service file permissions
sudo ls -la /etc/systemd/system/lex_agent.service
```

---

### OCR Not Detecting Names

**Symptoms:**
- "No high-confidence text detected"
- Only detecting one word instead of both names
- Low confidence scores (<0.70)

**Solutions:**

**1. Test camera view:**
```bash
# Stop service temporarily
sudo systemctl stop lex_agent

# Test with diagnostic script
python3 scripts/testing/test_realsense_badge_simple.py
```

**2. Improve badge presentation:**
- Write **LARGER** letters (2+ inch tall)
- Use **DARK marker** on **WHITE paper**
- Write **BOTH first AND last name**
- Hold in **CENTER** of camera view (green box)
- Keep **steady** for 3-5 seconds
- Ensure **good lighting** (no shadows on text)
- Try **printing** text instead of handwriting

**3. Adjust OCR settings:**
```bash
nano config/lex_channel_chief.json5

# Lower confidence threshold for testing:
min_confidence: 0.65,  # Was 0.75

# Save and restart
sudo systemctl restart lex_agent
```

**4. Test different badge formats:**
```
✅ GOOD:
JOHN SMITH
SARAH JOHNSON
MICHAEL BROWN

❌ BAD:
John (only first name)
j.smith (lowercase/abbreviated)
Dr. John Smith (title confuses OCR)
```

---

### Service Not Auto-Starting on Boot

**Symptoms:**
- Service works when started manually
- Doesn't start automatically after reboot

**Solutions:**
```bash
# Check if service is enabled
sudo systemctl is-enabled lex_agent
# Should output: "enabled"

# If not enabled, enable it:
sudo systemctl enable lex_agent

# Reboot to test
sudo reboot

# After reboot, check if running:
sudo systemctl status lex_agent
```

---

### Hardware Check Fails During Installation

**Symptoms:**
- Installation script reports camera/mic/speaker not found
- Service fails to start with hardware errors

**Solutions:**
```bash
# Run hardware checks manually
cd ~/roboai-espeak

# Test camera
python3 -c "import cv2; cap = cv2.VideoCapture(0); print('Camera OK' if cap.isOpened() else 'Camera FAIL'); cap.release()"

# Test microphone
arecord -l
# Should list audio devices

# Test speakers
speaker-test -t wav -c 2 -l 1
# Should play test sound

# If all hardware tests pass, force install:
bash scripts/installers/install_lex_service_robust.sh
# Answer 'y' to continue despite warnings
```

---

## Complete Reinstall (Nuclear Option)

If everything is broken and you need to start fresh:

```bash
# 1. Stop and disable service
sudo systemctl stop lex_agent
sudo systemctl disable lex_agent

# 2. Remove service file
sudo rm /etc/systemd/system/lex_agent.service

# 3. Reload systemd
sudo systemctl daemon-reload

# 4. Clean up repo
cd ~/roboai-espeak
git fetch origin
git reset --hard origin/main

# 5. Remove virtual environment
rm -rf .venv

# 6. Reinstall dependencies
uv sync

# 7. Reinstall service
bash scripts/installers/install_lex_service_robust.sh

# 8. Verify
sudo systemctl status lex_agent
sudo journalctl -u lex_agent -f
```

---

## Service File Location and Configuration

**Service file path:**
```
/etc/systemd/system/lex_agent.service
```

**View service configuration:**
```bash
sudo cat /etc/systemd/system/lex_agent.service
```

**Edit service file (advanced):**
```bash
sudo nano /etc/systemd/system/lex_agent.service

# After editing, reload and restart:
sudo systemctl daemon-reload
sudo systemctl restart lex_agent
```

---

## What Happens on Boot

With robust autostart installed, this is the boot sequence:

1. **System boots** → systemd initializes
2. **lex_agent.service activates** → runs pre-start checks
3. **Hardware validation:**
   - Camera accessible?
   - Microphone detected?
   - Speakers working?
   - Ollama installed?
4. **Ollama started** (if not already running)
5. **Python environment validated**
6. **Lex agent starts:**
   - Loads configuration
   - Initializes inputs (ASR, badge reader, GPS, etc.)
   - Connects to LLM
7. **Badge reader initializes:**
   - Opens RealSense camera
   - Loads EasyOCR model (~10 seconds)
   - Starts polling for badges
8. **Agent ready** → listening for badges, voice, etc.
9. **On failure** → automatic restart after 10 seconds

**Check boot logs:**
```bash
sudo journalctl -u lex_agent -b
```

---

## Quick Reference Card

```bash
# === UPDATE CODE + RESTART ===
cd ~/roboai-espeak && git pull && uv sync && sudo systemctl restart lex_agent

# === VIEW LOGS ===
sudo journalctl -u lex_agent -f                    # Real-time
sudo journalctl -u lex_agent -n 100                # Last 100 lines
sudo journalctl -u lex_agent -f | grep Badge      # Badge activity only

# === SERVICE CONTROL ===
sudo systemctl status lex_agent                    # Check status
sudo systemctl start lex_agent                     # Start
sudo systemctl stop lex_agent                      # Stop
sudo systemctl restart lex_agent                   # Restart
sudo systemctl enable lex_agent                    # Enable auto-start
sudo systemctl disable lex_agent                   # Disable auto-start

# === TESTING ===
python3 scripts/testing/test_realsense_badge_simple.py   # Test camera + OCR
python3 scripts/testing/list_cameras.py                  # List cameras

# === MANUAL RUN (for debugging) ===
sudo systemctl stop lex_agent                      # Stop service first
cd ~/roboai-espeak
uv run src/run.py lex_channel_chief               # Run manually
# Press Ctrl+C when done
sudo systemctl start lex_agent                     # Restart service
```

---

## Badge Presentation Tips

For best OCR accuracy:

**✅ DO:**
- Use **CAPITAL LETTERS**
- Write **LARGE** (2+ inch tall)
- Use **dark marker** on **white paper**
- Include **both FIRST and LAST name**
- Hold in **center** of camera view
- Keep **steady** for 3-5 seconds
- Ensure **good lighting**
- **Print** text when possible

**❌ DON'T:**
- Use lowercase letters
- Write too small
- Include titles (Dr., Mr., Mrs.)
- Use abbreviations
- Only write first name
- Hold at angle
- Write with light-colored pen
- Have shadows on text

**Example formats that work well:**
```
JOHN SMITH
SARAH JOHNSON
MICHAEL BROWN

or on two lines:
FREDERICK
FERACO
```

---

## Configuration Reference

**Badge Reader Config Options:**

```json5
{
  type: "BadgeReaderEasyOCR",
  config: {
    camera_index: 3,              // Camera device number (from list_cameras.py)
    poll_interval: 8.0,            // Seconds between badge checks (default: 8.0)
    greeting_cooldown: 90.0,       // Seconds before re-greeting same person (default: 90.0)
    min_confidence: 0.75,          // Minimum OCR confidence 0.0-1.0 (default: 0.75)
    use_realsense: true,           // Use RealSense SDK vs OpenCV (default: false)
    realsense_width: 1920,         // RGB stream width (default: 1920)
    realsense_height: 1080,        // RGB stream height (default: 1080)
    realsense_fps: 30,             // RGB stream FPS (default: 30)
    gpu: true,                     // Use GPU for EasyOCR (default: true)
    min_words: 2,                  // Minimum words in name (default: 2)
    max_words: 4                   // Maximum words in name (default: 4)
  }
}
```

---

## Support and Additional Resources

**Test Scripts:**
- `scripts/testing/test_realsense_badge_simple.py` - Simple camera + OCR test
- `scripts/testing/test_realsense_badge_ubuntu.py` - Advanced RealSense test
- `scripts/testing/list_cameras.py` - List all cameras
- `scripts/testing/quick_badge_test.py` - Quick OCR test

**Configuration Examples:**
- `config/badge_reader_test_mac.json5` - Mac development config
- `config/lex_channel_chief.json5` - Production Lex config
- `config/unitree_g1_humanoid.json5` - G1 robot config

**Service Files:**
- `systemd_services/lex_agent_robust.service` - Robust service config
- `scripts/lex_pre_start_checks_robust.sh` - Pre-start hardware checks

**Documentation:**
- `README.md` - Project overview
- `documentation/guides/CONFIG_GUIDE.md` - Configuration guide
- `.github/copilot-instructions.md` - Developer instructions

---

## Success Checklist

- [ ] SSH access to G1 working
- [ ] Latest code pulled from GitHub
- [ ] EasyOCR installed (`uv add easyocr`)
- [ ] RealSense SDK installed (`python3-pyrealsense2`)
- [ ] Camera test successful (`test_realsense_badge_simple.py`)
- [ ] RGB camera index identified (`list_cameras.py`)
- [ ] Config updated with badge reader input
- [ ] System prompts include badge examples
- [ ] Manual test successful (heard greeting)
- [ ] Robust service installed
- [ ] Service status shows "active (running)"
- [ ] Logs show badge reader initialized
- [ ] Live badge test successful
- [ ] Service auto-starts on boot

---

**Setup Complete!** Your G1 robot is now ready to greet conference attendees by reading their name badges. 🎉🤖

For questions or issues, check the Troubleshooting section or review the logs with `sudo journalctl -u lex_agent -f`.
