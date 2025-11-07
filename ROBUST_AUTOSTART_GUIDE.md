# Robust Auto-Start Installation for Jetson

This creates an intelligent auto-start system that:
- ✅ Waits for USB microphone to be detected (up to 60s)
- ✅ Waits for USB speaker and sets it as default (up to 60s)
- ✅ Validates Ollama is running and responsive
- ✅ Tests Ollama model responds to prompts
- ✅ Auto-restarts Ollama if corrupted
- ✅ Optionally clears Ollama cache if needed
- ✅ Logs all checks for debugging
- ✅ Auto-restarts agent on failure

---

## Installation on Jetson

Copy these 3 files to your Jetson and run:

```bash
cd ~/roboai-espeak

# Copy these files from your Mac to Jetson:
# - pre_start_checks.sh
# - astra_agent_robust.service  
# - install_robust_autostart.sh

# Or pull from git if you push them
git pull origin main

# Make installation script executable
chmod +x install_robust_autostart.sh

# Run installation
bash install_robust_autostart.sh
```

---

## What It Does

### Pre-Start Checks (pre_start_checks.sh)

**1. Microphone Detection (60s timeout)**
- Searches for USB PnP Sound Device
- Retries every 2 seconds
- Logs device info when found
- Continues anyway if not found (agent has internal fallback)

**2. Speaker Detection (60s timeout)**
- Searches for USB speaker
- Ensures PulseAudio is running
- Sets USB speaker as default output
- Logs PulseAudio sink name
- Continues anyway if not found

**3. Ollama Service Check**
- Verifies Ollama service is running
- Auto-starts if stopped
- Tests responsiveness with `ollama list`
- Restarts Ollama if not responding
- Optional: Clears cache if corrupted (uncomment in script)

**4. Ollama Model Test**
- Checks if llama3.1:8b exists
- Sends test prompt: "Reply OK"
- Verifies model responds within 20s
- Fails startup if model broken

---

## Logs and Debugging

### View Pre-Start Checks

```bash
# See what hardware was detected
sudo journalctl -u astra_agent -n 100 | grep PreStart

# Example output:
# [PreStart] INFO: Waiting for USB microphone...
# [PreStart] ✅ USB microphone detected: card 1: Device [USB PnP Sound Device]
# [PreStart] INFO: Waiting for USB speaker...
# [PreStart] ✅ USB speaker detected: card 1: Device [USB2.0 Device]
# [PreStart] ✅ Set default audio output to: alsa_output.usb-Generic...
# [PreStart] INFO: Checking Ollama service...
# [PreStart] ✅ Ollama service is running
# [PreStart] ✅ Model 'llama3.1:8b' is available
# [PreStart] ✅ Model 'llama3.1:8b' responds correctly
# [PreStart] ✅ All pre-start checks completed!
```

### View Full Logs

```bash
# Watch live logs
sudo journalctl -u astra_agent -f

# View last 100 lines
sudo journalctl -u astra_agent -n 100

# View logs since last boot
sudo journalctl -u astra_agent -b
```

### Check Service Status

```bash
# Quick status
sudo systemctl status astra_agent

# Check if enabled for auto-start
sudo systemctl is-enabled astra_agent

# Check if running
sudo systemctl is-active astra_agent
```

---

## Manual Controls

```bash
# Start
sudo systemctl start astra_agent

# Stop
sudo systemctl stop astra_agent

# Restart
sudo systemctl restart astra_agent

# Disable auto-start
sudo systemctl disable astra_agent

# Enable auto-start
sudo systemctl enable astra_agent

# View configuration
cat /etc/systemd/system/astra_agent.service
```

---

## Troubleshooting

### Agent Won't Start

```bash
# Check logs for specific error
sudo journalctl -u astra_agent -n 50

# Common issues:
# - Microphone timeout: Check USB cable, replug device
# - Speaker timeout: Check USB cable, verify aplay -l shows device
# - Ollama not responding: sudo systemctl restart ollama
# - Model not found: ollama pull llama3.1:8b
```

### Test Pre-Start Checks Manually

```bash
cd ~/roboai-espeak
bash pre_start_checks.sh

# This will show exactly what the service sees
```

### Hardware Not Detected

```bash
# List USB devices
lsusb

# List audio devices
arecord -l
aplay -l

# Check PulseAudio
pactl list sinks short

# If devices not showing, replug USB and wait 10s
```

### Ollama Issues

```bash
# Check Ollama service
systemctl status ollama

# Test Ollama
ollama list
ollama run llama3.1:8b "test"

# If broken, restart
sudo systemctl restart ollama
sleep 5
ollama pull llama3.1:8b
```

---

## Advanced: Enable Ollama Cache Clearing

If Ollama frequently gets corrupted, enable automatic cache clearing:

```bash
# Edit pre-start checks
nano ~/roboai-espeak/pre_start_checks.sh

# Find this line (around line 115):
# rm -rf ~/.ollama/models/manifests/registry.ollama.ai/library/llama3.1/* 2>/dev/null || true

# Uncomment it (remove the #):
rm -rf ~/.ollama/models/manifests/registry.ollama.ai/library/llama3.1/* 2>/dev/null || true

# Save and restart service
sudo systemctl restart astra_agent
```

---

## Testing Auto-Start

```bash
# Test without rebooting
sudo systemctl stop astra_agent
sleep 2
sudo systemctl start astra_agent

# Watch logs to see hardware detection
sudo journalctl -u astra_agent -f

# You should see:
# [PreStart] INFO: Waiting for USB microphone...
# [PreStart] ✅ USB microphone detected
# [PreStart] ✅ USB speaker detected
# [PreStart] ✅ Ollama is responsive
# [PreStart] ✅ Model responds correctly
# [PreStart] ✅ All pre-start checks completed!
```

---

## What Happens on Boot

1. **T+0s**: System boots, Jetson starts services
2. **T+10s**: Agent service starts, waits 10s for system stabilization
3. **T+20s**: Pre-start checks begin:
   - Microphone detection (up to 60s)
   - Speaker detection (up to 60s)
   - Ollama validation (up to 30s)
   - Model test (up to 20s)
4. **T+30-180s**: Agent starts after all checks pass
5. **Running**: Agent listens and responds

If any check fails after max timeout:
- Audio issues: Continues anyway (has internal fallback)
- Ollama issues: Service fails, will retry in 15s (up to 3 times)

---

## Success Indicators

When everything is working:

```bash
$ sudo systemctl status astra_agent

● astra_agent.service - Astra Vein Receptionist AI Agent with Hardware Detection
     Loaded: loaded (/etc/systemd/system/astra_agent.service; enabled; vendor preset: enabled)
     Active: active (running) since ...
   Main PID: 1234 (uv)
      Tasks: 15
     Memory: 500M
     
# Logs show:
# [PreStart] ✅ All pre-start checks completed!
# INFO - LocalASRInput: Using device 1 (USB PnP Sound Device)
# INFO - Starting OM1 with standard configuration: astra_vein_receptionist
# INFO - ✅ LLM validation PASSED
```

Perfect! The agent is listening and ready. 🎯
