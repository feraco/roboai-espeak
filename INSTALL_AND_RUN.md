# OM1 (RoboAI) — Installation & Run Guide

This project runs a modular AI agent runtime for robots and virtual assistants. It supports multiple configurations including the **Astra Vein Receptionist** - a multilingual AI assistant for medical reception.

## 🧩 Requirements

### Hardware
- **USB PnP Sound Device** (Microphone input)
- **USB 2.0 Speaker** (Audio output) - Optional
- **Intel RealSense D435i RGB Camera** (Optional - for face detection)

### Software
- **Python 3.10+** installed
- **uv** package manager ([Installation guide](https://github.com/astral-sh/uv))
- **Ollama** (for local LLM) - [Download here](https://ollama.ai/)

---

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/feraco/roboai-espeak.git
cd roboai-espeak
```

### 2. Install UV Package Manager

If you don't have UV installed:

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or via pip
pip install uv
```

### 3. Install Dependencies

UV will automatically create a virtual environment and install all dependencies:

```bash
uv sync
```

**Platform-specific notes:**
- **macOS**: Builds for CoreAudio, uses PortAudio for mic/speaker
- **Linux (Jetson Orin)**: Builds for PulseAudio/ALSA (ARM64)

If you need to rebuild the environment:

```bash
rm -rf .venv .uv
uv sync
```

### 4. Install Ollama and Required Models

```bash
# Install Ollama
# macOS: Download from https://ollama.ai/
# Linux: curl -fsSL https://ollama.ai/install.sh | sh

# Pull required models
ollama pull llama3.1:8b          # Main agent model (recommended)
ollama pull llama3.2-vision:11b  # Optional: for vision capabilities

# Start Ollama server (runs in background)
ollama serve
```

### 5. Download TTS Voice Models

The agent uses Piper for text-to-speech. Download voice models:

```bash
# Run the voice download script (downloads ~180MB)
./download_piper_voices.sh
```

**Note:** Voice models (.onnx files) are NOT included in the git repository due to their large size (600MB+). The script downloads only the essential voices needed for the astra_vein_receptionist agent:
- en_US-kristin-medium.onnx (English)
- es_ES-davefx-medium.onnx (Spanish)
- ru_RU-dmitri-medium.onnx (Russian)

---

## 🔍 System Verification

### Run Full System Diagnostics

Run comprehensive system diagnostics (audio, camera, Ollama):

```bash
python diagnostics_audio.py
```

This script will:
1. **Check Ollama**: Verify LLM service, clear cache, restart
2. **Detect Camera**: Find Intel RealSense D435i (if connected)
3. **Test Audio**: Verify microphone and speaker configuration

**Expected output:**
```
🤖 OLLAMA LLM SERVICE
✅ Ollama is running
✅ Required model llama3.1:8b is installed
✅ Ollama restarted successfully

📷 CAMERA CONFIGURATION
✅ Camera detected: Intel(R) RealSense(TM) Depth Camera 435i
   Index: 6
   Resolution: 640x480

🎙️ AUDIO SYSTEM
✅ Input device configured: 1 - USB PnP Sound Device
✅ Output device configured: 2 - USB 2.0 Speaker
📊 Sample rate: 48000 Hz (macOS) or 16000 Hz (Jetson)
```

**On Jetson Orin**, this will also run:
- ALSA device detection (`arecord -l`)
- PulseAudio configuration check
- Mixer level verification
- Live recording tests

**Troubleshooting:**
- See [JETSON_ORIN_AUDIO_GUIDE.md](documentation/troubleshooting/JETSON_ORIN_AUDIO_GUIDE.md) for detailed Linux audio troubleshooting
- See [AUDIO_CONFIG.md](AUDIO_CONFIG.md) for audio system architecture

---

## 🎯 Running the Agent

### Standard Configurations

```bash
# Astra Vein Receptionist (multilingual medical receptionist)
uv run src/run.py astra_vein_receptionist

# Local offline agent (no cloud services)
uv run src/run.py local_offline_agent

# Full list of configurations
ls config/*.json5
```

### Agent Features

**Astra Vein Receptionist** includes:
- 🎙️ **Voice Input**: Faster-Whisper ASR (base model, multi-language)
- 🗣️ **Voice Output**: Piper TTS (English, Spanish, Russian)
- 👁️ **Vision**: Face detection with emotion recognition (optional)
- 🧠 **LLM**: Ollama (llama3.1:8b for reliable JSON output)
- 🌍 **Multi-language**: Automatic language switching

### Testing Language Switching

While the agent is running, speak to it:

```
"Can you speak Spanish?" → Agent responds in Spanish
"Can you speak Russian?" → Agent responds in Russian  
"Can you speak English?" → Agent responds in English
```

### Auto-Start on Boot (Jetson Only)

To configure the agent to start automatically when the Jetson boots:

```bash
# Install systemd service
./install_autostart.sh
```

This will:
- Install a systemd service (`astra_agent.service`)
- Enable auto-start on boot
- Clear Ollama cache and restart on each boot
- Run diagnostics before starting agent

**Service management:**
```bash
# Start agent now
sudo systemctl start astra_agent

# Stop agent
sudo systemctl stop astra_agent

# Check status
sudo systemctl status astra_agent

# View live logs
sudo journalctl -u astra_agent -f

# Disable auto-start
sudo systemctl disable astra_agent
```

---

## 🛠️ Configuration

### Audio Configuration

Audio settings are automatically detected and saved to `device_config.yaml`.

To reconfigure:

```bash
python diagnostics_audio.py
```

### Agent Configuration

Edit `config/astra_vein_receptionist.json5`:

```json5
{
  agent_inputs: [
    {
      type: "LocalASRInput",
      config: {
        input_device: null,        // Auto-detect (recommended)
        sample_rate: 16000,        // 48000 for macOS, 16000 for Jetson
        amplify_audio: 3.0,        // Increase if mic is quiet
        detect_language: true,     // Enable multi-language
        supported_languages: ["en", "es", "ru"]
      }
    }
  ],
  
  cortex_llm: {
    type: "OllamaLLM",
    config: {
      model: "llama3.1:8b",       // More reliable than llama3.2:3b
      timeout: 30,
      max_tokens: 150
    }
  }
}
```

---

## 📁 Project Structure

```
roboai-espeak/
├── config/                    # Agent configurations
│   ├── astra_vein_receptionist.json5
│   ├── local_offline_agent.json5
│   └── ...
├── src/
│   ├── run.py                # Main entry point
│   ├── actions/              # Action plugins (speak, move, etc.)
│   ├── inputs/               # Input plugins (ASR, vision, sensors)
│   ├── llm/                  # LLM plugins (Ollama, OpenAI, etc.)
│   ├── runtime/              # Runtime engines
│   ├── fuser/                # Prompt fusion logic
│   └── utils/                # Utilities (audio_config, validation)
├── piper_voices/             # TTS voice models
├── documentation/            # Comprehensive guides
│   ├── setup/
│   └── troubleshooting/
├── diagnostics_audio.py      # Audio system verification
├── test_microphone.py        # Microphone test
├── test_camera.py            # Camera test
└── device_config.yaml        # Generated audio config (gitignored)
```

---

## 🔧 Troubleshooting

### 🚨 Common Jetson Issues (START HERE)

If you encounter errors on Jetson Orin, follow this comprehensive troubleshooting procedure:

#### Issue 1: "Ollama API error" / "No response from LLM"

**Symptoms:**
```
ERROR - Ollama API error: 
ERROR - OUTPUT(LLM): No response from LLM
```

**Complete Fix:**
```bash
# 1. Kill all Python/agent processes (they may be holding resources)
pkill -9 -f python
pkill -9 -f "src/run.py"
sleep 2

# 2. Restart Ollama service
sudo systemctl restart ollama
sleep 5

# 3. Test Ollama is responding
ollama run llama3.1:8b "Test. Reply with just OK."

# If test fails, run the full fix script:
./fix_ollama.sh
```

**What fix_ollama.sh does:**
- Stops Ollama service
- Kills lingering processes
- Clears ALL cache locations (user + system + tmp)
- Restarts Ollama
- Tests model loading with timeout
- Auto-reinstalls model if corrupted

#### Issue 2: "Invalid number of channels [PaErrorCode -9998]"

**Symptoms:**
```
Expression 'parameters->channelCount <= maxChans' failed
Error opening InputStream: Invalid number of channels [PaErrorCode -9998]
```

**Cause:** USB microphone only supports stereo (2 channels) on Jetson, but code tries mono (1 channel)

**Fix:**
```bash
# Pull the stereo detection fix
git pull origin main

# Clear old audio config (has wrong channel count)
rm device_config.yaml

# Regenerate with channel auto-detection
python diagnostics_audio.py
```

**Expected output after fix:**
```
LocalASRInput: Device only supports stereo (2 channels)
LocalASRInput: Will record in stereo and convert to mono for ASR
✅ Using 2 channel(s)
```

#### Issue 3: "Device unavailable [PaErrorCode -9985]"

**Symptoms:**
```
Expression 'ret' failed in 'src/hostapi/alsa/pa_linux_alsa.c'
Error opening InputStream: Device unavailable [PaErrorCode -9985]
```

**Cause:** Microphone is locked by another process (previous agent run didn't fully stop)

**Fix:**
```bash
# Kill all processes using audio
pkill -9 -f python
pkill -9 -f pulseaudio
sleep 2

# Restart PulseAudio
pulseaudio --start

# Verify device is free
fuser -v /dev/snd/*

# Clear stale config and regenerate
rm device_config.yaml
python diagnostics_audio.py
```

#### Issue 4: Whisper Hallucinations (Garbage Transcriptions)

**Symptoms:**
```
[LANG:en] In fascinación, a sat JUDGE. Hablamos.arina. venas, CR 2...
```

**Cause:** Corrupted audio data from channel mismatch bug

**Fix:**
```bash
# 1. Pull stereo fix
git pull origin main

# 2. Clear audio config
rm device_config.yaml

# 3. Regenerate and test
python diagnostics_audio.py
```

---

### 🔄 Complete Jetson Reset Procedure

If your agent is completely broken, run this full reset:

```bash
# 1. Stop everything
pkill -9 -f python
pkill -9 -f ollama
sudo systemctl stop ollama
sleep 3

# 2. Pull latest fixes
cd ~/Downloads/roboai-espeak/roboai-espeak-main  # or your path
git pull origin main

# 3. Clear all caches and configs
rm device_config.yaml
rm camera_config.yaml
rm -rf ~/.ollama/cache
sudo rm -rf /usr/share/ollama/.ollama/cache
sudo rm -rf /tmp/ollama*

# 4. Restart services
sudo systemctl start ollama
sleep 5
pulseaudio --kill && pulseaudio --start

# 5. Verify Ollama
ollama list
ollama run llama3.1:8b "Test. Reply OK."

# 6. Run full diagnostics
python diagnostics_audio.py

# 7. Start agent fresh
uv run src/run.py astra_vein_receptionist
```

---

### 🎯 Quick Diagnostic Commands

```bash
# Check what's using the microphone
fuser -v /dev/snd/*
lsof | grep snd

# Check Ollama status
systemctl status ollama
sudo journalctl -u ollama -n 50

# Check audio devices
arecord -l
pactl list short sources

# Test microphone manually
arecord -D hw:1,0 -f S16_LE -r 16000 -c 2 -d 3 test.wav
aplay test.wav

# Check system memory (for Ollama)
free -h

# Check USB devices
lsusb | grep -i audio
```

---

### Audio Issues

#### macOS
```bash
# Check permissions
# System Settings → Privacy & Security → Microphone → Enable Terminal

# List devices
python test_microphone.py

# Restart audio service
sudo killall coreaudiod
```

#### Linux (Jetson Orin)
```bash
# Check USB device
lsusb | grep -i audio

# Check ALSA
arecord -l

# Check mixer levels
alsamixer  # F6 → USB card, F4 → capture, M → unmute

# Test recording
arecord -D hw:1,0 -f cd -d 3 test.wav
aplay test.wav

# Check PulseAudio
pactl list short sources
pactl get-default-source

# Restart PulseAudio
pulseaudio --kill && pulseaudio --start

# Add user to audio group
sudo usermod -aG audio $USER  # Then logout/login
```

**See comprehensive guide**: [JETSON_ORIN_AUDIO_GUIDE.md](documentation/troubleshooting/JETSON_ORIN_AUDIO_GUIDE.md)

### Agent Startup Issues

#### "No valid microphone input detected"
```bash
# Run diagnostics first
python diagnostics_audio.py

# If needed, skip validation temporarily
SKIP_AUDIO_VALIDATION=true uv run src/run.py astra_vein_receptionist
```

#### "Ollama connection failed"
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama
ollama serve

# Check model is installed
ollama list
ollama pull llama3.1:8b
```

#### Language switching not working
- **Symptom**: Agent only responds in English
- **Cause**: Using llama3.2:3b (unreliable JSON output)
- **Fix**: Switch to llama3.1:8b in config
- **See**: [LANGUAGE_SWITCHING_FIX.md](LANGUAGE_SWITCHING_FIX.md)

---

## 📊 Logs

All runtime logs are stored in:

```
logs/
├── agent_YYYYMMDD_HHMMSS.log      # Main agent logs
├── audio_diagnostics.log           # Audio diagnostic results
└── camera_startup.log              # Camera initialization
```

To monitor logs in real-time:

```bash
tail -f logs/agent_*.log
```

---

## 🌐 Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SKIP_AUDIO_VALIDATION` | `false` | Skip pre-start audio validation |
| `SKIP_AUDIO_TEST` | `false` | Skip recording test, only check devices |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `OPENAI_API_KEY` | - | OpenAI API key (if using cloud LLM) |
| `ELEVENLABS_API_KEY` | - | ElevenLabs API key (if using cloud TTS) |

Set in `.env` file or export:

```bash
export SKIP_AUDIO_VALIDATION=true
uv run src/run.py astra_vein_receptionist
```

---

## 🚢 Deployment

### Jetson Orin Deployment

1. **On macOS (development machine)**:
   ```bash
   git add .
   git commit -m "Update agent configuration"
   git push origin main
   ```

2. **On Jetson Orin**:
   ```bash
   cd ~/roboai-espeak
   git pull origin main
   uv sync  # Rebuild for ARM64/Linux
   python diagnostics_audio.py  # Verify audio
   uv run src/run.py astra_vein_receptionist
   ```

### Systemd Service (Auto-start on boot)

See [JETSON_ORIN_AUDIO_GUIDE.md](documentation/troubleshooting/JETSON_ORIN_AUDIO_GUIDE.md) for systemd service configuration.

---

## 📚 Documentation

### Setup Guides
- **[QUICKSTART.md](documentation/setup/QUICKSTART.md)** - Quick setup guide
- **[UBUNTU_G1_DEPLOYMENT.md](documentation/setup/UBUNTU_G1_DEPLOYMENT.md)** - G1 robot deployment

### Configuration
- **[CONFIG_GUIDE.md](documentation/guides/CONFIG_GUIDE.md)** - Configuration file reference
- **[AUDIO_CONFIG.md](AUDIO_CONFIG.md)** - Audio system architecture

### Troubleshooting
- **[JETSON_ORIN_AUDIO_GUIDE.md](documentation/troubleshooting/JETSON_ORIN_AUDIO_GUIDE.md)** - Complete Jetson audio troubleshooting (600+ lines)
- **[LANGUAGE_SWITCHING_FIX.md](LANGUAGE_SWITCHING_FIX.md)** - Language switching implementation

### Technical Reference
- **[IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md)** - Current implementation status
- **[JETSON_AUDIO_VALIDATION_SUMMARY.md](JETSON_AUDIO_VALIDATION_SUMMARY.md)** - Audio validation system details
- **[README.md](README.md)** - Project overview

---

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.

---

## 📄 License

See [LICENSE](LICENSE) file.

---

## 🆘 Getting Help

1. **Check documentation** in `documentation/` directory
2. **Run diagnostics**: `python diagnostics_audio.py`
3. **Check logs**: `tail -f logs/agent_*.log`
4. **Open an issue** with:
   - OS and hardware info (`uname -a`, `lsusb`)
   - Diagnostic output
   - Agent logs
   - Configuration file used

---

## ⚡ Quick Command Reference

```bash
# Setup
uv sync                                              # Install dependencies
python diagnostics_audio.py                          # Verify audio
ollama pull llama3.1:8b                             # Install LLM model

# Run
uv run src/run.py astra_vein_receptionist           # Start agent
SKIP_AUDIO_VALIDATION=true uv run src/run.py ...    # Skip validation

# Test
python test_microphone.py                            # Test mic
python test_camera.py                                # Test camera
curl http://localhost:11434/api/tags                 # Check Ollama

# Debug
tail -f logs/agent_*.log                            # Monitor logs
python diagnostics_audio.py > audio_diag.log 2>&1   # Save diagnostics

# Jetson specific
arecord -l                                          # List capture devices
alsamixer                                           # Mixer controls
pactl list short sources                            # PulseAudio sources
pulseaudio --kill && pulseaudio --start             # Restart audio
```

---

**Status**: ✅ Ready for production deployment  
**Last Updated**: 2025-11-06  
**Tested Platforms**: macOS (Apple Silicon), Jetson Orin (ARM64 Linux)
