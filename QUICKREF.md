# Astra Vein Receptionist - Quick Reference

## 🚀 Quick Start (macOS)

```bash
# 1. Run diagnostics
python3 diagnostics_audio.py

# 2. Start agent
uv run src/run.py astra_vein_receptionist
```

## 🚀 Quick Start (Jetson)

```bash
# 1. Update code
cd ~/roboai-espeak
git pull origin main
uv sync

# 2. Run diagnostics (first time)
python3 diagnostics_audio.py

# 3. Start agent
uv run src/run.py astra_vein_receptionist
```

## 📊 What to Expect

### Diagnostics Output
```
✅ Input device configured: 1 - USB PnP Sound Device
✅ Output device configured: 3 - USB 2.0 Speaker
📊 Sample rate: 48000 Hz
💾 Config saved to: device_config.yaml
```

### Agent Startup
```
INFO - LocalASRInput: Using saved audio config - device 1 (USB PnP Sound Device)
INFO - LocalASRInput: Using sample rate 48000 Hz
INFO - Loaded Faster-Whisper model: base
INFO - Found en voice model: ./piper_voices/en_US-kristin-medium.onnx
INFO - Found es voice model: ./piper_voices/es_ES-davefx-medium.onnx
INFO - Found ru voice model: ./piper_voices/ru_RU-dmitri-medium.onnx
INFO - Starting OM1 with standard configuration: astra_vein_receptionist
```

### Running Agent Logs
```
======================================================================
2025-11-06 20:15:03 | 📥 INPUT CYCLE START
======================================================================
2025-11-06 20:15:03 | INPUT(LocalASRInput): Voice INPUT
// START
[LANG:en] How are office hours?
// END

2025-11-06 20:15:03 | INPUT(FaceEmotionCapture): Visible: 1 person (emotion: happy)

======================================================================
2025-11-06 20:15:04 | 📤 OUTPUT CYCLE START
======================================================================
2025-11-06 20:15:04 | OUTPUT(LLM): ...
2025-11-06 20:15:04 | OUTPUT(TTS): [en] Monday to Friday, 9 AM to 6 PM. Closed weekends.
======================================================================
2025-11-06 20:15:04 | ✅ CYCLE COMPLETE
======================================================================
```

## ⚠️ Troubleshooting

### Problem: "No input detected"

**Quick Fix:**
```bash
# 1. Check USB connection
# 2. Run diagnostics
python3 diagnostics_audio.py

# 3. If device not found:
#    - Unplug and replug USB mic
#    - Check System Settings → Privacy → Microphone (macOS)
#    - Run diagnostics again
```

### Problem: Wrong device selected

**Quick Fix:**
```bash
# Delete saved config and re-detect
rm device_config.yaml
python3 diagnostics_audio.py
```

### Problem: Low volume / RMS too low

**Quick Fix:**
Edit `config/astra_vein_receptionist.json5`:
```json5
"amplify_audio": 5.0,         // Increase from 3.0
"silence_threshold": 0.01,    // Decrease from 0.02 (more sensitive)
```

## 📁 Key Files

- **`device_config.yaml`** - Saved audio configuration (auto-generated)
- **`config/astra_vein_receptionist.json5`** - Agent configuration
- **`diagnostics_audio.py`** - Run this to test audio setup
- **`AUDIO_CONFIG.md`** - Complete audio configuration guide
- **`AUDIT_SUMMARY.md`** - Full details of all changes

## 🔧 Useful Commands

```bash
# Test microphone
python3 test_microphone.py

# Force device re-detection
rm device_config.yaml && python3 diagnostics_audio.py

# View only INPUT/OUTPUT logs
uv run src/run.py astra_vein_receptionist 2>&1 | grep -E "INPUT|OUTPUT|CYCLE"

# Save all logs to file
uv run src/run.py astra_vein_receptionist 2>&1 | tee agent.log
```

## 🎯 Success Indicators

- ✅ Diagnostics show USB PnP Sound Device found
- ✅ Agent logs show "Using saved audio config - device X"
- ✅ INPUT logs show voice transcription
- ✅ OUTPUT logs show TTS sentences
- ✅ No "No input detected" warnings

## 💡 Tips

- **Multi-language**: Say "Can you speak Spanish?" to switch languages
- **Vision**: Agent sees faces and emotions via camera
- **Offline**: No internet required (Faster-Whisper + Ollama + Piper)
- **Cross-platform**: Same commands work on macOS and Jetson

## 📚 More Help

- See `AUDIO_CONFIG.md` for detailed troubleshooting
- See `AUDIT_SUMMARY.md` for technical architecture
- See `.github/copilot-instructions.md` for development patterns
