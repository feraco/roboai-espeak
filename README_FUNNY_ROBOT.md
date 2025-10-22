# RoboAI Funny Robot

A fun and entertaining AI robot that tells jokes and engages in playful conversations using local speech recognition and text-to-speech on macOS.

## Prerequisites

1. macOS (tested on Sonoma 14.0+)
2. Python 3.10+
3. [Ollama](https://ollama.ai/) for local LLM support
4. UV package manager (recommended) or pip

## Quick Installation

1. Clone the repository:
```bash
git clone https://github.com/feraco/roboai-espeak.git
cd roboai-espeak
```

2. Install Ollama:
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

3. Install the Gemma model (recommended for this setup):
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

## Configuration

The funny robot uses:
- Local ASR (Automatic Speech Recognition) using faster-whisper
- macOS native text-to-speech (no additional installation needed)
- Ollama LLM for local inference
- Pre-configured personality as a joke-telling, friendly robot

## Running the Funny Robot

1. Make sure Ollama is running:
```bash
# Ollama should start automatically after installation
# If needed, start it manually:
ollama serve
```

2. Run the funny robot:
```bash
uv run src/run.py funny_robot
```

or if using pip:
```bash
python src/run.py funny_robot
```

## Troubleshooting

1. If you don't hear any audio:
   - Check your macOS sound settings
   - Make sure your volume is turned up
   - Try running a test command: `say "Testing audio"`

2. If speech recognition isn't working:
   - Check your microphone permissions in System Preferences
   - Make sure your microphone is selected as the input device

3. If Ollama isn't responding:
   - Check if the service is running: `curl http://localhost:11434/api/tags`
   - Restart Ollama if needed: `ollama serve`

## Contributing

1. Fork the repository
2. Create your feature branch: `git checkout -b feature/new-feature`
3. Commit your changes: `git commit -am 'Add new feature'`
4. Push to the branch: `git push origin feature/new-feature`
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.