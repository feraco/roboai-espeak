# Jetson Orin Quick Start

## 🚀 One-Command Setup

```bash
# Automated setup (recommended)
chmod +x setup_jetson.sh
./setup_jetson.sh
# Then reboot when prompted
```

## 📝 Manual Setup (Step-by-Step)

See **JETSON_SETUP.md** for detailed instructions.

### Quick Summary:

```bash
# 1. Install UV
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Install Ollama
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3.1:8b
ollama pull llava-llama3

# 3. Install Audio Packages
sudo apt-get install -y alsa-base alsa-utils portaudio19-dev \
    libsndfile1-dev pulseaudio ffmpeg

# 4. Install Piper TTS
wget https://github.com/rhasspy/piper/releases/download/v1.2.0/piper_arm64.tar.gz
tar -xzf piper_arm64.tar.gz && sudo mv piper/piper /usr/local/bin/

# 5. Setup Python Environment
cd ~/roboai-espeak
uv sync

# 6. Configure Permissions & Reboot
sudo usermod -a -G audio $USER
sudo reboot
```

## ✅ Testing (After Reboot)

```bash
# Check all dependencies
uv run python check_jetson_dependencies.py

# Test audio hardware
uv run python test_jetson_audio.py

# Test microphone
arecord -d 3 test.wav && aplay test.wav

# Test TTS
echo "Hello" | piper --model ~/piper_voices/en_US-ryan-medium.onnx --output_file test.wav && aplay test.wav
```

## 🤖 Run Agent

```bash
cd ~/roboai-espeak
uv run src/run.py astra_vein_receptionist
```

## 🔧 Common Issues

| Issue | Solution |
|-------|----------|
| `paInvalidSampleRate` | Auto-fixed! Code detects supported rates |
| Mic too quiet | Run `alsamixer`, press F4, increase volume |
| No audio devices | Ensure rebooted after adding to audio group |
| Ollama not running | `sudo systemctl start ollama` |
| Camera not working | `sudo chmod 666 /dev/video0` |

## 📚 Documentation

- **JETSON_SETUP.md** - Complete step-by-step guide with explanations
- **check_jetson_dependencies.py** - Verify all packages installed
- **test_jetson_audio.py** - Test audio hardware capabilities

## 🎯 Expected Behavior

**Voice Input:**
1. You speak: "What are your office hours?"
2. Agent hears, transcribes, responds with TTS

**Vision Curiosity:**
1. You stay quiet but visible to camera
2. Agent describes what it sees
3. Agent welcomes you

## ⚡ Performance Tips for Jetson

- Use `tiny.en` Whisper model (fastest)
- Set `chunk_duration: 2.0` (balanced)
- Set `poll_interval: 5.0` for vision (saves CPU)
- Use `llama3.1:8b` model (good balance)

## 📊 System Requirements

- **RAM:** 8GB minimum (16GB recommended)
- **Storage:** 20GB free (for models and cache)
- **Ollama Models:** ~10GB total
  - llama3.1:8b: 4.7GB
  - llava-llama3: 4.9GB
- **Python Packages:** ~2GB

---

**Need help?** See JETSON_SETUP.md for detailed troubleshooting.
