# Deployment Checklist - macOS to Jetson Orin

Use this checklist to ensure smooth deployment from macOS development to Jetson Orin production.

## 📋 Pre-Deployment (macOS)

### 1. Code Quality Checks
- [ ] Run linting: `ruff check src/`
- [ ] Run tests: `uv run pytest`
- [ ] Check for syntax errors: `python -m py_compile src/**/*.py`
- [ ] Verify configurations are valid JSON5: `python -c "import json5; json5.load(open('config/astra_vein_receptionist.json5'))"`

### 2. Audio System Verification
- [ ] Run diagnostics: `python diagnostics_audio.py`
- [ ] Verify device_config.yaml generated correctly
- [ ] Test microphone: `python test_microphone.py`
- [ ] Test agent locally: `uv run src/run.py astra_vein_receptionist`
- [ ] Test language switching (Spanish, Russian, English)

### 3. Git Preparation
- [ ] Run cleanup script: `./git_cleanup.sh`
- [ ] Review changes: `git status`
- [ ] Check .gitignore is up to date
- [ ] Verify no .venv, .uv, or device_config.yaml tracked: `git ls-files | grep -E "(\.venv|\.uv|device_config)"`
- [ ] Commit changes: `git add . && git commit -m "update: agent improvements"`

### 4. Documentation Check
- [ ] INSTALL_AND_RUN.md is up to date
- [ ] Configuration changes documented in commit message
- [ ] Known issues documented if any

### 5. Push to GitHub
- [ ] Push to main: `git push origin main`
- [ ] Verify GitHub shows latest changes
- [ ] Check GitHub Actions (if configured) pass

---

## 🚀 Deployment (Jetson Orin)

### 1. Pull Latest Code
```bash
cd ~/roboai-espeak  # Or your deployment directory
git fetch origin
git status  # Check for local changes
git pull origin main
```

### 2. Rebuild Environment
```bash
# Clean previous environment (if needed)
rm -rf .venv .uv

# Install dependencies (ARM64 optimized)
uv sync

# Verify installation
uv pip list | grep -E "(torch|whisper|sounddevice)"
```

### 3. Hardware Verification
```bash
# Check USB devices
lsusb | grep -i audio

# Run comprehensive audio diagnostics
python diagnostics_audio.py

# Expected checks:
# ✅ ALSA device detection (hw:1,0)
# ✅ PulseAudio configuration
# ✅ ALSA recording test (RMS > 100)
# ✅ PulseAudio recording test
# ✅ Mixer levels (not muted, > 50%)
```

### 4. System Configuration
```bash
# Add user to audio group (if not already)
sudo usermod -aG audio $USER
# Then logout/login or: newgrp audio

# Check PulseAudio default source
pactl get-default-source
# Should show USB device (contains "usb")

# If wrong, set default:
# pactl set-default-source alsa_input.usb-<YourDevice>-00.mono-fallback

# Check mixer levels (unmute and increase)
alsamixer
# F6 → USB card, F4 → capture, M → unmute, ↑ to 70%+
```

### 5. LLM Setup
```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# If not running, start it
ollama serve &

# Verify model is installed
ollama list | grep llama3.1:8b

# If missing, pull it
ollama pull llama3.1:8b
```

### 6. Test Run
```bash
# Test with validation
uv run src/run.py astra_vein_receptionist

# If validation fails, check diagnostics:
python diagnostics_audio.py > audio_diag.log 2>&1
cat audio_diag.log

# Skip validation temporarily (debugging only):
# SKIP_AUDIO_VALIDATION=true uv run src/run.py astra_vein_receptionist
```

### 7. Monitor & Test
```bash
# In another terminal, monitor logs
tail -f logs/agent_*.log

# Test interactions:
# - Say "Hello" (should respond in English)
# - Say "Can you speak Spanish?" (should switch to Spanish)
# - Say "What are your office hours?" (should respond in Spanish)
# - Say "Can you speak English?" (should switch back)

# Check TTS output logs:
# Should see: OUTPUT(TTS): [en] ... or [es] ... or [ru] ...
```

---

## 🔧 Troubleshooting

### Audio Not Working
```bash
# Step 1: Check USB connection
lsusb | grep -i audio

# Step 2: Check ALSA
arecord -l  # Should show USB device

# Step 3: Test ALSA recording
arecord -D hw:1,0 -f cd -d 3 test.wav
aplay test.wav  # Should hear your voice

# Step 4: Check mixer
alsamixer  # Unmute and increase levels

# Step 5: Check PulseAudio
pactl list short sources
pactl get-default-source

# Step 6: Restart PulseAudio
pulseaudio --kill && pulseaudio --start

# Step 7: Run diagnostics again
python diagnostics_audio.py
```

### Agent Crashes on Startup
```bash
# Check logs
tail -50 logs/agent_*.log

# Common issues:
# - "No valid microphone input detected"
#   → Run python diagnostics_audio.py
#   → Check mixer levels (alsamixer)

# - "Ollama connection failed"
#   → Check: curl http://localhost:11434/api/tags
#   → Start: ollama serve &

# - "Model not found"
#   → Pull: ollama pull llama3.1:8b

# - "Module not found"
#   → Rebuild: rm -rf .venv && uv sync
```

### Language Switching Not Working
```bash
# Check logs for LLM output
grep "language" logs/agent_*.log

# Should see: 'language': 'en' or 'es' or 'ru'

# If missing language field:
# - Verify using llama3.1:8b (not llama3.2:3b)
# - Check config: grep "model" config/astra_vein_receptionist.json5

# If TTS doesn't switch:
# - Verify voices exist: ls -lh piper_voices/*.onnx
# - Should have: en_US-kristin-medium.onnx, es_ES-davefx-medium.onnx, ru_RU-dmitri-medium.onnx
```

---

## ✅ Post-Deployment Verification

### Functional Tests
- [ ] Agent starts without errors
- [ ] Microphone captures audio (check logs: "Detected language")
- [ ] LLM generates responses (check logs: "LLM OUTPUT")
- [ ] TTS produces audio (check logs: "Piper TTS synthesis successful")
- [ ] Audio plays through speaker
- [ ] Language switching works (en → es → ru → en)
- [ ] Vision input detected (if camera connected)

### Performance Tests
- [ ] Response latency < 10 seconds (mic input → audio output)
- [ ] CPU usage reasonable (< 80% sustained)
- [ ] No memory leaks (check over 1 hour: `htop`)
- [ ] No audio dropouts or stuttering

### Stability Tests
- [ ] Runs for 1 hour without crashes
- [ ] Handles silence correctly (no false triggers)
- [ ] Recovers from temporary audio issues
- [ ] Logs don't fill disk (check: `du -sh logs/`)

---

## 📊 Monitoring (Production)

### System Monitoring
```bash
# CPU/Memory
htop

# Disk usage
df -h
du -sh logs/

# Process status
ps aux | grep "run.py"

# Audio devices (verify USB still connected)
lsusb | grep -i audio

# PulseAudio status
pactl info
```

### Log Monitoring
```bash
# Real-time monitoring
tail -f logs/agent_*.log

# Error checking
grep -i error logs/agent_*.log
grep -i warning logs/agent_*.log

# Audio issues
grep -i "no input\|muted\|device" logs/agent_*.log

# Language switching
grep "language.*es\|language.*ru" logs/agent_*.log
```

### Periodic Checks (Daily)
```bash
# Log rotation (if logs get too large)
cd logs && gzip agent_$(date -d "yesterday" +%Y%m%d)_*.log

# Check disk space
df -h | grep -E "/$|/home"

# Verify Ollama still running
curl -s http://localhost:11434/api/tags > /dev/null && echo "✅ Ollama OK" || echo "❌ Ollama DOWN"

# Check agent process
pgrep -f "run.py astra" && echo "✅ Agent running" || echo "❌ Agent stopped"
```

---

## 🔄 Rollback Procedure (If Issues Occur)

### Quick Rollback
```bash
# Check previous commit
git log --oneline -5

# Rollback to previous version
git checkout <previous-commit-hash>

# Rebuild environment
rm -rf .venv .uv
uv sync

# Restart agent
uv run src/run.py astra_vein_receptionist
```

### Emergency Bypass
```bash
# Skip audio validation (temporary)
SKIP_AUDIO_VALIDATION=true uv run src/run.py astra_vein_receptionist

# Use older model if llama3.1:8b has issues
# Edit config: model: "llama3.2:3b"  (less reliable but faster)
```

---

## 📝 Deployment Notes Template

**Date**: _______________  
**Deployed By**: _______________  
**Git Commit**: _______________  
**Jetson IP**: _______________  

**Changes Deployed**:
- [ ] Configuration updates
- [ ] Code changes
- [ ] Documentation updates
- [ ] Bug fixes

**Tests Performed**:
- [ ] Audio diagnostics passed
- [ ] Agent startup successful
- [ ] Language switching tested
- [ ] 1-hour stability test

**Issues Encountered**:
_______________________________________________
_______________________________________________

**Resolution**:
_______________________________________________
_______________________________________________

**Performance Notes**:
- Response latency: ______ seconds
- CPU usage: ______ %
- Memory usage: ______ MB

**Sign-off**: ✅ Production Ready | ⚠️ Issues | ❌ Rollback Required

---

## 🔗 Quick Reference Links

- **Installation Guide**: [INSTALL_AND_RUN.md](INSTALL_AND_RUN.md)
- **Jetson Audio Guide**: [documentation/troubleshooting/JETSON_ORIN_AUDIO_GUIDE.md](documentation/troubleshooting/JETSON_ORIN_AUDIO_GUIDE.md)
- **Language Switching**: [LANGUAGE_SWITCHING_FIX.md](LANGUAGE_SWITCHING_FIX.md)
- **Audio Config**: [AUDIO_CONFIG.md](AUDIO_CONFIG.md)
- **Implementation Status**: [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md)

---

**Remember**: Always test on Jetson after deployment. macOS behavior ≠ Jetson behavior!
