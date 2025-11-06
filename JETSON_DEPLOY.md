# Deploying Astra Agent from Mac to Jetson

## Overview

This guide covers deploying the enhanced Astra Vein Receptionist agent from your Mac development environment to the Jetson Orin production robot.

## Prerequisites

### On Mac (Development)
- ✅ Agent tested and working with USB PnP Sound Device
- ✅ `device_config.yaml` generated (platform-specific, won't transfer)
- ✅ All changes committed to git

### On Jetson (Production)
- USB PnP Sound Device connected
- USB 2.0 Speaker connected (optional)
- Ollama installed with llama3.2:3b model
- Piper TTS voices installed
- Git repository cloned to `~/roboai-espeak`

## Step-by-Step Deployment

### 1. Commit Changes on Mac

```bash
cd ~/Downloads/roboai-feature-multiple-agent-configurations

# Check status
git status

# Add new files
git add src/utils/audio_config.py
git add diagnostics_audio.py
git add start_astra_agent.py
git add AUDIO_CONFIG.md
git add AUDIT_SUMMARY.md
git add QUICKREF.md
git add JETSON_DEPLOY.md

# Add modified files
git add src/inputs/plugins/local_asr.py
git add src/inputs/plugins/webcam_to_face_emotion.py
git add src/runtime/single_mode/cortex.py
git add config/astra_vein_receptionist.json5

# Commit
git commit -m "Add audio config system, vision grounding, and structured logging

- Added audio_config.py for smart device detection by name
- Enhanced local_asr.py to use audio configuration
- Added diagnostics_audio.py for startup testing
- Updated vision plugin for grounded observations
- Enhanced cortex logging with structured INPUT/OUTPUT cycles
- Updated system prompt with vision grounding rules
- Added comprehensive documentation
"

# Push to GitHub
git push origin main
```

### 2. Deploy to Jetson

```bash
# SSH into Jetson
ssh unitree@<jetson-ip>

# Navigate to project
cd ~/roboai-espeak

# Pull latest changes
git pull origin main

# Update dependencies (if needed)
uv sync

# Run diagnostics to configure audio
python3 diagnostics_audio.py
```

### 3. Expected Diagnostics Output (Jetson)

```
======================================================================
🎙️  ASTRA VEIN RECEPTIONIST - AUDIO DIAGNOSTICS
======================================================================

🔍 Detecting audio devices...
✅ Found input device: 1 - USB PnP Sound Device
⚠️  Jetson quirk: USB 2.0 Speaker shows as input device 1
✅ Override: Using device 1 as OUTPUT - USB 2.0 Speaker
📊 Selected sample rate: 16000 Hz

📋 Available Audio Devices (3 total):
------------------------------------------------------------
 0. USB2.0 Device                                (in: 0, out: 2)
 1. USB PnP Sound Device                         (in: 1, out: 0) ← INPUT SELECTED
 2. default                                      (in:38, out:38)
------------------------------------------------------------

🎯 Selected Configuration:
  Input:  Device 1 - USB PnP Sound Device
  Output: Device 0 - USB 2.0 Speaker
  Sample Rate: 16000 Hz

🐧 Linux Audio Diagnostics:
------------------------------------------------------------
arecord -l output:
  card 1: Device [USB PnP Sound Device], device 0: USB Audio [USB Audio]

🎤 Testing microphone (device 1)...
   Recording 2.0s at 16000 Hz - SPEAK NOW!
   Max amplitude: 0.0842
   RMS level: 0.0123
✅ Microphone test PASSED (RMS: 0.0123)

======================================================================
📋 DIAGNOSTIC SUMMARY
======================================================================
✅ Input device configured: 1 - USB PnP Sound Device
✅ Output device configured: 0 - USB 2.0 Speaker
📊 Sample rate: 16000 Hz
💾 Config saved to: device_config.yaml
```

### 4. Verify Generated Config

```bash
cat device_config.yaml
```

Expected:
```yaml
input_device: 1
input_name: USB PnP Sound Device
output_device: 0
output_name: USB 2.0 Speaker
platform: linux
sample_rate: 16000
```

### 5. Start the Agent

```bash
uv run src/run.py astra_vein_receptionist
```

### 6. Verify Agent Startup Logs

Look for these key messages:

```
INFO - LocalASRInput: Using saved audio config - device 1 (USB PnP Sound Device)
INFO - LocalASRInput: Using sample rate 16000 Hz
INFO - Loaded Faster-Whisper model: base
INFO - Found en voice model: ./piper_voices/en_US-kristin-medium.onnx
INFO - System context set on LLM (7124 chars) - will be cached/reused
INFO - Starting OM1 with standard configuration: astra_vein_receptionist
```

### 7. Test Full Cycle

**Say something to the microphone** (e.g., "What are your office hours?")

**Expected log output:**
```
======================================================================
2025-11-06 04:35:15 | 📥 INPUT CYCLE START
======================================================================
2025-11-06 04:35:15 | INPUT(LocalASRInput): Voice INPUT
// START
[LANG:en] What are your office hours?
// END

2025-11-06 04:35:15 | INPUT(FaceEmotionCapture): No discernible objects.

======================================================================
2025-11-06 04:35:16 | 📤 OUTPUT CYCLE START
======================================================================
2025-11-06 04:35:16 | OUTPUT(LLM): <Action objects>
2025-11-06 04:35:16 | OUTPUT(TTS): [en] Monday to Friday, 9 AM to 6 PM. Closed weekends.
======================================================================
2025-11-06 04:35:16 | ✅ CYCLE COMPLETE
======================================================================
```

**Listen for TTS output** through USB 2.0 Speaker

## Troubleshooting Deployment Issues

### Issue: "No input detected" on Jetson

**Diagnosis:**
```bash
# Check USB devices
lsusb | grep -i audio

# Check ALSA
arecord -l

# Check permissions
groups  # Should include 'audio'

# Re-run diagnostics
python3 diagnostics_audio.py
```

**Fix:**
```bash
# Add user to audio group (if not already)
sudo usermod -a -G audio unitree

# Restart session
# Log out and log back in, or:
newgrp audio

# Re-run diagnostics
python3 diagnostics_audio.py
```

### Issue: Sample rate mismatch

**Symptom:** Device detected but recording fails

**Fix:**
The audio_config system auto-detects the best sample rate. If issues persist:

1. Check `device_config.yaml` shows correct sample rate (16000 for Jetson)
2. Force re-detection: `rm device_config.yaml && python3 diagnostics_audio.py`
3. Test manually:
   ```bash
   arecord -D hw:1,0 -f cd -d 3 test.wav
   aplay test.wav
   ```

### Issue: Speaker quirk on Jetson

**Expected behavior:** You should see this warning:
```
⚠️  Jetson quirk: USB 2.0 Speaker shows as input device 1
✅ Override: Using device 1 as OUTPUT - USB 2.0 Speaker
```

This is normal and handled automatically.

### Issue: Vision camera not working

**Diagnosis:**
```bash
# Check camera
ls -l /dev/video*

# Test with OpenCV
python3 test_camera.py
```

**Fix:**
```bash
# Add user to video group
sudo usermod -a -G video unitree

# Restart session
```

## Platform Differences

| Feature | macOS | Jetson Linux |
|---------|-------|--------------|
| Sample Rate | 48000 Hz | 16000 Hz |
| Device Detection | Works automatically | Works automatically |
| Permissions | System Preferences | audio group membership |
| Speaker Quirk | No | Yes (handled automatically) |
| ALSA Tools | Not available | arecord, aplay available |
| Default Device | Works | May need explicit selection |

## Verification Checklist

After deployment to Jetson:

- [ ] Git pull completed successfully
- [ ] `uv sync` completed without errors
- [ ] `diagnostics_audio.py` finds USB PnP Sound Device
- [ ] `device_config.yaml` created with platform: linux
- [ ] Microphone test passes (RMS > 0.001)
- [ ] Agent starts without errors
- [ ] Voice input detected (no "No input detected" warnings)
- [ ] LLM responds appropriately
- [ ] TTS plays through USB 2.0 Speaker
- [ ] Full INPUT → OUTPUT cycle completes
- [ ] Logs show structured format with timestamps

## Rollback Procedure

If issues occur:

```bash
# On Jetson
cd ~/roboai-espeak

# Check current commit
git log -1

# Rollback to previous version
git fetch origin
git reset --hard <previous-commit-hash>

# Or reset to origin/main
git reset --hard origin/main

# Clean generated files
rm device_config.yaml

# Restart from step 2
```

## Production Deployment

### Option 1: Manual Start

```bash
ssh unitree@<jetson-ip>
cd ~/roboai-espeak
uv run src/run.py astra_vein_receptionist
```

### Option 2: Systemd Service (Recommended)

Create `/etc/systemd/system/astra-agent.service`:

```ini
[Unit]
Description=Astra Vein Receptionist Agent
After=network.target

[Service]
Type=simple
User=unitree
WorkingDirectory=/home/unitree/roboai-espeak
ExecStartPre=/usr/bin/python3 /home/unitree/roboai-espeak/diagnostics_audio.py
ExecStart=/home/unitree/.cargo/bin/uv run src/run.py astra_vein_receptionist
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable astra-agent
sudo systemctl start astra-agent
sudo systemctl status astra-agent
```

View logs:
```bash
sudo journalctl -u astra-agent -f
```

## Support

For deployment issues:
1. Check `AUDIO_CONFIG.md` for detailed audio troubleshooting
2. Review `AUDIT_SUMMARY.md` for architecture details
3. Compare Mac and Jetson `device_config.yaml` files
4. Test hardware with `test_microphone.py` and `test_camera.py`
5. Check systemd logs if using service deployment

## Success Indicators

✅ **Deployment successful if:**
- Agent starts without errors
- Structured logs show INPUT → OUTPUT cycles
- Voice recognition works (transcription appears in logs)
- TTS plays through speaker
- Vision detection works (if camera present)
- No "No input detected" warnings
- Sample rate matches platform (16000 Hz on Jetson)

Happy deploying! 🚀
