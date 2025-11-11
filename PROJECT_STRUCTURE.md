# 📁 Project Structure

```
roboai-espeak/
├── README.md                    # Main project documentation
├── CONTRIBUTING.md              # Contribution guidelines
├── LICENSE                      # Project license
├── pyproject.toml              # Python dependencies (UV)
├── pyrightconfig.json          # Type checking config
│
├── config/                      # Agent configurations (JSON5)
│   ├── astra_vein_receptionist.json5    # Medical receptionist
│   ├── lex_channel_chief.json5          # Sales agent with badge reader
│   └── ...                              # Other agent configs
│
├── src/                         # Main source code
│   ├── run.py                  # Agent entry point
│   ├── inputs/                 # Input plugins (ASR, vision, sensors)
│   ├── actions/                # Action plugins (TTS, movement)
│   ├── llm/                    # LLM plugins (Ollama, OpenAI, etc)
│   ├── fuser/                  # Prompt fusion logic
│   └── runtime/                # Agent runtime engines
│
├── docs/                        # Documentation
│   ├── deployment/             # Deployment guides
│   │   ├── ROBUST_AUTOSTART_GUIDE.md
│   │   ├── LEX_PACKAGE_README.md
│   │   └── ...
│   ├── setup/                  # Setup instructions
│   │   ├── JETSON_SETUP.md
│   │   ├── QUICKSTART_JETSON.md
│   │   └── ...
│   ├── troubleshooting/        # Troubleshooting guides
│   │   ├── JETSON_AUDIO_OUTPUT_FIX.md
│   │   ├── OLLAMA_FIX_COMMANDS.txt
│   │   └── ...
│   └── *.md                    # Other documentation
│
├── scripts/                     # Utility scripts
│   ├── installers/             # Installation scripts
│   │   ├── install_lex_service_robust.sh
│   │   ├── install_lex_jetson.sh
│   │   └── ...
│   ├── testing/                # Test scripts and test data
│   │   ├── test_badge_detection.py
│   │   ├── diagnostics_audio.py
│   │   └── ...
│   ├── pre_start_checks.sh     # Astra pre-start validation
│   ├── lex_pre_start_checks_robust.sh  # Lex pre-start validation
│   └── fix_ollama.sh           # Ollama troubleshooting
│
├── systemd_services/            # Systemd service files
│   ├── astra_agent_robust.service
│   ├── lex_agent_robust.service
│   └── ...
│
├── piper_voices/                # TTS voice models (local)
├── audio_output/                # Generated TTS audio files
├── tests/                       # Unit tests
└── .github/                     # GitHub workflows and config
```

## 🚀 Quick Start

### Run an Agent
```bash
uv run src/run.py <config_name>

# Examples:
uv run src/run.py astra_vein_receptionist
uv run src/run.py lex_channel_chief
```

### Install as Service (Auto-start on boot)
```bash
# Lex Agent (with badge reader)
bash scripts/installers/install_lex_service_robust.sh

# Astra Agent (medical receptionist)
bash scripts/installers/install_robust_autostart.sh
```

## 📚 Documentation

- **Setup**: `docs/setup/` - Installation and configuration guides
- **Deployment**: `docs/deployment/` - Production deployment guides  
- **Troubleshooting**: `docs/troubleshooting/` - Common issues and fixes
- **API Docs**: See main `README.md` for architecture overview

## 🛠️ Development

- **Source Code**: `src/` - All agent runtime code
- **Config Files**: `config/` - Agent behavior definitions
- **Tests**: `tests/` + `scripts/testing/` - Unit and integration tests
- **Scripts**: `scripts/` - Helper utilities and installers

## 🔧 Service Management

All systemd service files are in `systemd_services/`. To install:

```bash
sudo cp systemd_services/lex_agent_robust.service /etc/systemd/system/lex_agent.service
sudo systemctl daemon-reload
sudo systemctl enable lex_agent
sudo systemctl start lex_agent
```

Or use the installer scripts in `scripts/installers/` for one-command setup.

## 📝 Configuration

All agent configs live in `config/*.json5`. Key configs:

- `astra_vein_receptionist.json5` - Medical reception desk agent
- `lex_channel_chief.json5` - Sales/marketing agent with badge reader
- `local_agent.json5` - Basic local testing agent

See `.github/copilot-instructions.md` for detailed config documentation.
