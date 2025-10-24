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
source .venv/bin/activate
pip install -r requirements.txt
```

### For Ubuntu

1. Install system dependencies:
```bash
sudo apt-get update
sudo apt-get install -y portaudio19-dev python3-dev ffmpeg espeak
```

2. Clone the repository:
```bash
git clone https://github.com/feraco/roboai-espeak.git
cd roboai-espeak
```

3. Install Ollama:
```bash
curl -fsSL https://ollama.ai/install.sh | sh
sudo systemctl start ollama  # If using systemd
```

4. Install the required Ollama model:
```bash
ollama pull gemma2:2b
```

5. Set up Python environment using UV (recommended):
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

Alternative setup using pip:
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Running the Funny Robot

1. Ensure Ollama is running:
```bash
# Ollama should start automatically after installation
# If needed, start it manually:
ollama serve
```

2. Run the funny robot configuration:
```bash
uv run src/run.py funny_robot
```

or if using pip:
```bash
python src/run.py funny_robot
```

## Configuration Details

The Funny Robot uses the following components:

- **Speech Recognition**: Local ASR using faster-whisper
- **Text-to-Speech**: Native macOS text-to-speech (no additional installation needed)
- **Language Model**: Ollama with gemma2:2b model
- **Personality**: Pre-configured as a friendly, joke-telling robot

The configuration file is located at `config/funny_robot.json5`.

## Troubleshooting

### Running Diagnostics

The project includes a diagnostic tool to help identify and fix common issues:

```bash
python scripts/diagnose_audio.py
```

This tool will check:
- System audio output
- Microphone input
- Ollama setup and model installation
- Required Python packages
- Configuration file settings

### Audio Issues

1. No Speech Output:
   
   On macOS:
   - Check System Preferences → Sound → Output
   - Verify volume is not muted
   - Test system audio: `say "Testing audio output"`
   
   On Ubuntu:
   - Check Sound Settings in System Settings
   - Verify volume is not muted
   - Test system audio: `espeak "Testing audio output"`
   - Ensure espeak is installed: `sudo apt-get install espeak`

2. Speech Recognition Problems:
   
   On macOS:
   - Check System Preferences → Security & Privacy → Microphone
   - Verify microphone input level in System Preferences → Sound → Input
   
   On Ubuntu:
   - Check Sound Settings → Input in System Settings
   - Verify microphone permissions: `sudo usermod -a -G audio $USER`
   - Test microphone: `arecord -d 5 test.wav && aplay test.wav`
   - Check if microphone is detected: `arecord -l`

### LLM Issues

1. Ollama Connection Errors:
   - Verify Ollama is running: `curl http://localhost:11434/api/tags`
   - Check if model is installed: `ollama list`
   - Try restarting Ollama: `ollama serve`

2. Model Loading Issues:
   - Ensure gemma2:2b is installed: `ollama pull gemma2:2b`
   - Check available memory
   - Try a different model by editing `config/funny_robot.json5`

## Project Structure

```
.
├── config/                  # Configuration files
│   └── funny_robot.json5    # Funny robot configuration
├── src/
│   ├── actions/            # Available actions (speak, move, etc.)
│   ├── inputs/             # Input handlers (ASR, sensors)
│   ├── llm/               # Language model connectors
│   └── run.py             # Main entry point
├── requirements.txt        # Python dependencies
└── README.md              # This file
```



## License

This project is licensed under the terms of the MIT License, which is a permissive free software license that allows users to freely use, modify, and distribute the software. The MIT License is a widely used and well-established license that is known for its simplicity and flexibility. By using the MIT License, this project aims to encourage collaboration, modification, and distribution of the software.
