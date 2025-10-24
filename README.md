# RoboAI - Modular AI Agent Runtime

A modular AI runtime that lets you create interactive AI agents for robots and virtual assistants. Supports multiple platforms, local and cloud processing, and features like speech recognition, text-to-speech, vision, and robot control.

## 📚 Documentation

**Complete documentation is now in the [`documentation/`](documentation/) folder:**

- **[📖 Documentation Index](documentation/README.md)** - Full documentation overview
- **[🚀 Quick Start](documentation/setup/QUICKSTART.md)** - Get started in 5 minutes
- **[🤖 Ubuntu G1 Deployment](documentation/setup/UBUNTU_G1_DEPLOYMENT.md)** - Complete G1 robot setup
- **[🔧 Troubleshooting](documentation/troubleshooting/)** - Diagnostic tools and fixes

## 🎯 Quick Links by Platform

| Platform | Documentation | Description |
|----------|---------------|-------------|
| **Ubuntu G1 Robot** | [Ubuntu G1 Deployment](documentation/setup/UBUNTU_G1_DEPLOYMENT.md) | Complete guide with step-by-step troubleshooting |
| **macOS Development** | [macOS Quick Install](documentation/setup/QUICK_INSTALL_MAC.md) | Local development setup |
| **Local Offline** | [Local Setup](documentation/setup/LOCAL_SETUP.md) | Fully offline configuration |

## 🚀 Quick Start

### Option 1: Ubuntu G1 Robot (Recommended for Production)

```bash
# See complete guide with troubleshooting:
# documentation/setup/UBUNTU_G1_DEPLOYMENT.md

cd ~/roboai-espeak
./documentation/setup/setup_piper_ubuntu.sh
python3 documentation/troubleshooting/check_g1_hardware.py
uv run src/run.py astra_vein_receptionist
```

### Option 2: macOS Development

```bash
# Install dependencies
curl -LsSf https://astral.sh/uv/install.sh | sh
brew install portaudio

# Setup
uv sync
ollama pull llama3.1:8b

# Run
uv run src/run.py local_agent
```

### Option 3: Test Camera (Ubuntu)

```bash
# Test your camera before running the agent
python3 test_camera.py
```

This will test all available cameras and save test images.

## 📋 Testing Hardware

On **Ubuntu/G1**, test all components before deploying:

```bash
# Complete hardware check
python3 documentation/troubleshooting/check_g1_hardware.py

# Test microphone
./documentation/troubleshooting/test_ubuntu_mic.sh

# Test camera
python3 test_camera.py

# Audio diagnostics
python3 documentation/troubleshooting/diagnose_ubuntu_audio.py
```

## 🎛️ Configuration

Agent configurations are in [`config/`](config/):

- **`astra_vein_receptionist.json5`** - Medical receptionist (G1 production)
- **`local_agent.json5`** - Local offline agent
- **`conversation.json5`** - Simple conversation agent

See [Configuration Guide](documentation/guides/CONFIG_GUIDE.md) for details.

## 🤖 Available Agents

| Agent | Config | Description |
|-------|--------|-------------|
| **Astra Vein Receptionist** | `astra_vein_receptionist` | Medical office receptionist with vision |
| **Local Agent** | `local_agent` | General purpose offline agent |
| **Conversation** | `conversation` | Simple chat bot |

Run any agent:
```bash
uv run src/run.py <config_name>
```

## 📁 Project Structure

```
roboai-espeak/
├── documentation/          # All documentation (organized)
│   ├── setup/             # Installation guides
│   ├── guides/            # Integration guides
│   ├── troubleshooting/   # Diagnostic tools
│   └── reference/         # Technical references
├── config/                # Agent configurations
├── src/                   # Source code
│   ├── inputs/           # Audio, vision, sensors
│   ├── connectors/       # LLM, TTS providers
│   ├── actions/          # Robot actions
│   └── memory/           # Conversation memory
├── test_camera.py        # Camera testing tool
└── README.md            # This file
```

## 🆘 Troubleshooting

### Quick Fixes

**Microphone not working:**
```bash
./documentation/troubleshooting/test_ubuntu_mic.sh
python3 documentation/troubleshooting/diagnose_ubuntu_audio.py
```

**Camera not working:**
```bash
python3 test_camera.py
sudo usermod -a -G video $USER  # Then logout/login
```

**Ollama not running:**
```bash
sudo systemctl start ollama
ollama list  # Verify models
```

See [Troubleshooting Documentation](documentation/troubleshooting/) for more help.

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines.

## 📜 License

See [LICENSE](LICENSE) for license information.

## 🌟 Features

- ✅ **Local & Cloud** - Run fully offline or use cloud APIs
- ✅ **Multi-Platform** - macOS, Ubuntu, Jetson
- ✅ **Speech Recognition** - Faster-Whisper, OpenAI Whisper
- ✅ **Text-to-Speech** - Piper, ElevenLabs, Azure
- ✅ **Vision** - Ollama Vision (LLaVA), camera integration
- ✅ **Robot Control** - Unitree G1, arm gestures
- ✅ **Auto-Detection** - Audio devices, sample rates, paths
- ✅ **Production Ready** - Systemd services, auto-start, monitoring

---

**Need help?** Check the [Documentation Index](documentation/README.md) or open an issue!
