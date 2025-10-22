# RoboAI with Funny Robot Configuration

A modular AI runtime that lets you create interactive AI agents. This guide focuses on setting up the Funny Robot configuration - a joke-telling AI companion that uses local speech recognition and text-to-speech.

## Prerequisites

### For macOS
- macOS (tested on Sonoma 14.0+)
- Python 3.10 or higher
- [Ollama](https://ollama.ai/) for local LLM support
- UV package manager (recommended) or pip

### For Ubuntu
- Ubuntu 22.04 or higher
- Python 3.10 or higher
- [Ollama](https://ollama.ai/) for local LLM support
- UV package manager (recommended) or pip
- System dependencies (portaudio, ffmpeg)

## Quick Installation

### For macOS

1. Clone the repository:
```bash
git clone https://github.com/feraco/roboai-espeak.git
cd roboai-espeak
```

2. Install Ollama for local LLM support:
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

3. Install the required Ollama model:
```bash
ollama pull gemma2:2b
```

4. Set up Python environment using UV (recommended):
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
