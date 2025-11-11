# Quick Deployment Guide - Jetson Orin

## 🚀 Deploy All Fixes + Optimizations

Run these commands on your Jetson to get everything working:

```bash
# 1. Navigate to project
cd ~/Downloads/roboai-espeak/roboai-espeak-main

# 2. Pull all latest fixes
git pull origin main

# 3. Nuclear reset (fixes all issues)
pkill -9 -f python
sudo systemctl restart ollama
sleep 5
rm device_config.yaml camera_config.yaml
python diagnostics_audio.py

# 4. Test agent manually (verify everything works)
uv run src/run.py astra_vein_receptionist
```

**Test it for a few minutes, then Ctrl+C to stop.**

---

## ⚙️ Install Auto-Start (After Manual Test Passes)

```bash
# 1. Stop any running agent
pkill -f "src/run.py"

# 2. Remove old service if exists
sudo systemctl stop astra_agent 2>/dev/null || true
sudo systemctl disable astra_agent 2>/dev/null || true
sudo rm /etc/systemd/system/astra_agent.service 2>/dev/null || true

# 3. Install new service with fixes
./install_autostart.sh

# When prompted "Would you like to start the agent now?", type: y
```

---

## 📊 Verify Auto-Start Works

```bash
# Check service status
sudo systemctl status astra_agent

# Should show:
# ● astra_agent.service - Astra Vein Receptionist AI Agent
#      Loaded: loaded (/etc/systemd/system/astra_agent.service; enabled)
#      Active: active (running) since...

# View live logs
sudo journalctl -u astra_agent -f

# You should see:
# ✅ Ollama is running
# ✅ Using 2 channel(s)
# ✅ Audio validation PASSED
# === ASR INPUT === (when you speak)
# === LLM OUTPUT === (agent responses)
```

---

## 🧪 Test Performance Improvements

### Before (old config):
- User speaks → ~13 seconds → Agent responds

### After (new config):
- User speaks → **~8 seconds** → Agent responds

**Test it:**
1. Say "Hello, can you hear me?"
2. Time how long until agent responds
3. Should be **much faster** than before

---

## 🔄 Reboot Test (Critical!)

After installing auto-start, test that it works on boot:

```bash
# Reboot the Jetson
sudo reboot

# After reboot, wait 30 seconds, then check:
sudo systemctl status astra_agent

# Should automatically be running!
```

---

## ⚡ What Got Optimized

| Component | Speed Improvement |
|-----------|-------------------|
| **ASR (Whisper)** | 10x faster (tiny model) |
| **Audio Chunks** | 1s faster (2s vs 3s) |
| **LLM** | 30% faster (less history, fewer tokens) |
| **Vision** | 3x more responsive (10s vs 30s) |
| **TTS** | 12% faster speech |
| **Total** | **~5 seconds faster** per interaction |

---

## 🛠️ Troubleshooting After Update

### Agent still slow?
```bash
# Check Ollama is using correct model
ollama list
# Should show: llama3.1:8b

# Check agent is using optimized config
grep -A5 "model_size" config/astra_vein_receptionist.json5
# Should show: "tiny"

grep "hertz" config/astra_vein_receptionist.json5
# Should show: hertz: 2
```

### Auto-start not working?
```bash
# Check service logs for errors
sudo journalctl -u astra_agent -n 100

# Common issues:
# - Wrong path: Check WorkingDirectory in service file
# - Ollama not running: sudo systemctl start ollama
# - Audio device busy: pkill -9 -f python
```

### Still getting channel errors?
```bash
# Make sure you pulled the stereo fix
git log --oneline | head -5
# Should show: "fix: support stereo USB microphones"

# Clear audio config and regenerate
rm device_config.yaml
python diagnostics_audio.py
```

---

## 📋 Service Management Cheat Sheet

```bash
# Start agent
sudo systemctl start astra_agent

# Stop agent
sudo systemctl stop astra_agent

# Restart agent
sudo systemctl restart astra_agent

# Check status
sudo systemctl status astra_agent

# View logs (last 50 lines)
sudo journalctl -u astra_agent -n 50

# View logs (live follow)
sudo journalctl -u astra_agent -f

# Disable auto-start
sudo systemctl disable astra_agent

# Enable auto-start
sudo systemctl enable astra_agent

# Check if service is enabled
systemctl is-enabled astra_agent
```

---

## ✅ Success Checklist

After deployment, verify:

- [ ] Agent responds in ~8 seconds (was ~13s)
- [ ] Language switching works (English, Spanish, Russian)
- [ ] Vision detects faces every 10 seconds
- [ ] No "Invalid number of channels" errors
- [ ] No "Ollama API error" messages
- [ ] Auto-start service enabled: `systemctl is-enabled astra_agent`
- [ ] Service starts on boot (test with reboot)
- [ ] Logs show clean startup: `sudo journalctl -u astra_agent -n 50`

---

## 🎯 Expected Log Output (Success)

```
Nov 06 13:30:00 ubuntu-desktop systemd[1]: Starting Astra Vein Receptionist AI Agent...
Nov 06 13:30:15 ubuntu-desktop astra-agent: ✅ Ollama is running
Nov 06 13:30:15 ubuntu-desktop astra-agent: LocalASRInput: Using 2 channel(s)
Nov 06 13:30:16 ubuntu-desktop astra-agent: ✅ Input device configured: 4 - USB PnP Sound Device
Nov 06 13:30:16 ubuntu-desktop astra-agent: ✅ Audio validation PASSED - starting agent
Nov 06 13:30:20 ubuntu-desktop astra-agent: === ASR INPUT ===
Nov 06 13:30:20 ubuntu-desktop astra-agent: [LANG:en] Hello, can you hear me?
Nov 06 13:30:25 ubuntu-desktop astra-agent: === LLM OUTPUT ===
Nov 06 13:30:25 ubuntu-desktop astra-agent: {"actions":[{"type":"speak","value":{"sentence":"Yes, I can hear you!","language":"en"}}]}
Nov 06 13:30:27 ubuntu-desktop astra-agent: ✅ Audio played successfully with aplay
```

---

## 📞 If Something Breaks

Run the nuclear reset again:

```bash
cd ~/Downloads/roboai-espeak/roboai-espeak-main
pkill -9 -f python
sudo systemctl stop ollama
sudo systemctl start ollama
sleep 5
rm device_config.yaml
python diagnostics_audio.py
uv run src/run.py astra_vein_receptionist
```

---

**Quick Links:**
- Full Guide: [JETSON_QUICK_FIX.md](JETSON_QUICK_FIX.md)
- Performance Details: [PERFORMANCE_OPTIMIZATIONS.md](PERFORMANCE_OPTIMIZATIONS.md)
- Complete Install Guide: [INSTALL_AND_RUN.md](INSTALL_AND_RUN.md)

**Deployment Date:** 2025-11-06  
**Version:** Optimized + Auto-Start Fixed
