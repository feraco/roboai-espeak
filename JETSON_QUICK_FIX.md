# Jetson Orin Quick Fix Guide

## 🚨 Agent Not Working? Run This First:

```bash
# ONE-LINE NUCLEAR FIX (fixes 99% of issues)
pkill -9 -f python; sudo systemctl restart ollama; sleep 3; cd ~/Downloads/roboai-espeak/roboai-espeak-main && git pull origin main && rm device_config.yaml && python diagnostics_audio.py
```

Then start the agent:
```bash
uv run src/run.py astra_vein_receptionist
```

---

## 🔍 Error → Fix Lookup Table

| Error Message | Quick Fix |
|---------------|-----------|
| **"Ollama API error"** | `sudo systemctl restart ollama && ollama run llama3.1:8b "test"` |
| **"No response from LLM"** / **"OUTPUT(LLM): No response"** | `./fix_ollama.sh` OR `sudo systemctl restart ollama` |
| **"LLM validation failed"** | Model corrupted or not downloaded → `ollama pull llama3.1:8b` |
| **"Model test timed out"** | Not enough RAM or model too large → Try `llama3.2:3b` |
| **"Invalid number of channels [PaErrorCode -9998]"** | `git pull origin main && rm device_config.yaml && python diagnostics_audio.py` |
| **"Device unavailable [PaErrorCode -9985]"** | `pkill -9 -f python && pulseaudio --kill && pulseaudio --start` |
| **Garbage/hallucinated speech text** | Same as "Invalid channels" (audio corruption) |
| **Agent stuck/frozen** | `pkill -9 -f python && sudo systemctl restart ollama` |

---

## 🛠️ Complete Reset (Nuclear Option)

When nothing else works:

```bash
# 1. Kill everything
pkill -9 -f python
sudo systemctl stop ollama
pulseaudio --kill
sleep 3

# 2. Update code
cd ~/Downloads/roboai-espeak/roboai-espeak-main
git pull origin main

# 3. Clear ALL caches
rm device_config.yaml camera_config.yaml
rm -rf ~/.ollama/cache
sudo rm -rf /usr/share/ollama/.ollama/cache
sudo rm -rf /tmp/ollama*

# 4. Restart services
sudo systemctl start ollama
sleep 5
pulseaudio --start

# 5. Verify + regenerate configs
ollama run llama3.1:8b "Test"
python diagnostics_audio.py

# 6. Start fresh
uv run src/run.py astra_vein_receptionist
```

---

## 📋 Pre-Start Checklist

Before running the agent, verify these:

```bash
# ✅ Ollama running?
systemctl status ollama
ollama list  # Should show llama3.1:8b

# ✅ USB mic connected?
lsusb | grep -i audio
arecord -l  # Should show "USB PnP Sound Device"

# ✅ No processes using mic?
fuser -v /dev/snd/*  # Should be empty

# ✅ PulseAudio running?
pactl list short sources  # Should show USB device

# ✅ Audio config exists?
ls -lh device_config.yaml  # Should exist and be recent
```

---

## 🎯 Daily Startup Routine (Recommended)

```bash
# Morning startup sequence (run this once per boot)
cd ~/Downloads/roboai-espeak/roboai-espeak-main

# 1. Update code (if working on multiple machines)
git pull origin main

# 2. Restart services
sudo systemctl restart ollama
pulseaudio --kill && pulseaudio --start
sleep 3

# 3. Verify system
python diagnostics_audio.py

# 4. Start agent
uv run src/run.py astra_vein_receptionist
```

---

## 🔧 Maintenance Commands

```bash
# View agent logs in real-time
tail -f logs/agent_*.log

# View Ollama logs
sudo journalctl -u ollama -f

# Check Ollama memory usage
free -h
ps aux | grep ollama

# Test mic recording manually
arecord -D hw:1,0 -f S16_LE -r 16000 -c 2 -d 3 test.wav && aplay test.wav

# Clear only Ollama cache (if model acting weird)
sudo systemctl stop ollama
sudo rm -rf /usr/share/ollama/.ollama/cache
sudo systemctl start ollama
ollama pull llama3.1:8b  # Re-download if needed
```

---

## 📞 When to Ask for Help

If after running the complete reset you still see:
1. Continuous "Device unavailable" errors
2. Ollama returns empty responses
3. Speech transcription is always gibberish
4. Agent crashes immediately on startup

Then collect this info:
```bash
# Gather diagnostic info
uname -a > debug_info.txt
lsusb >> debug_info.txt
arecord -l >> debug_info.txt
pactl list short sources >> debug_info.txt
systemctl status ollama >> debug_info.txt
python diagnostics_audio.py >> debug_info.txt 2>&1
tail -100 logs/agent_*.log >> debug_info.txt
```

And share `debug_info.txt` with your support channel.

---

## ✅ Success Indicators

You'll know everything is working when you see:

```
✅ Ollama is running
✅ Required model llama3.1:8b is installed
✅ Model loads and responds correctly
✅ Found input device: USB PnP Sound Device
✅ Using 2 channel(s)  ← Stereo detection working
✅ Audio validation PASSED - starting agent

=== ASR INPUT ===
[LANG:en] Hello, can you hear me?  ← Clean transcription

=== LLM OUTPUT ===
{"actions": [{"type": "speak", ...}]}  ← Proper JSON response

Piper TTS speaking in en: Yes, I can hear you clearly!  ← TTS working
Audio played successfully with aplay  ← Speaker working
```

---

**Quick Links:**
- Full Guide: [INSTALL_AND_RUN.md](INSTALL_AND_RUN.md)
- Audio Troubleshooting: [JETSON_ORIN_AUDIO_GUIDE.md](documentation/troubleshooting/JETSON_ORIN_AUDIO_GUIDE.md)
- Configuration: [CONFIG_GUIDE.md](documentation/guides/CONFIG_GUIDE.md)

**Last Updated:** 2025-11-06  
**Tested On:** Jetson Orin, Ubuntu 20.04, USB PnP Sound Device
