# RoboAI Copilot Instructions

## Project Overview

**OM1** (formerly RoboAI) is a modular AI agent runtime for robots and virtual assistants. It uses a plugin-based architecture where inputs (sensors), LLMs, and actions (actuators) are dynamically loaded from JSON5 configurations.

### Core Architecture

The system follows a **Sense → Think → Act** pipeline orchestrated by the `Fuser`:

1. **Inputs** (`src/inputs/plugins/`) - Sensors that provide data (ASR, vision, GPS, battery, etc.)
2. **Fuser** (`src/fuser/`) - Combines all inputs + system prompts into a unified LLM prompt
3. **LLM** (`src/llm/plugins/`) - Processes fused input and returns structured JSON actions
4. **Actions** (`src/actions/`) - Execute commands (speak, move, gestures, etc.)

### Key Execution Modes

- **Single Mode**: Standard runtime (`src/runtime/single_mode/cortex.py`)
- **Multi Mode**: Dynamic mode switching for different behaviors (`src/runtime/multi_mode/cortex.py`)
  - Configs with `modes` and `default_mode` keys use `ModeCortexRuntime`
  - Examples: `config/unitree_go2_modes.json5`, `config/spot_modes.json5`

## Critical Developer Workflows

### Running Agents

```bash
# Install dependencies (uses UV package manager)
uv sync

# Run an agent configuration
uv run src/run.py <config_name>

# Examples:
uv run src/run.py local_agent           # Local agent with OpenAI
uv run src/run.py astra_vein_receptionist  # G1 robot receptionist
uv run src/run.py unitree_go2_modes     # Multi-mode quadruped robot
```

### Testing

```bash
# Run tests (uses pytest)
uv run pytest

# Test excludes: src/unitree, src/ubtech, gazebo, system_hw_test
# See pyproject.toml [tool.pytest.ini_options]

# Hardware testing scripts:
python3 test_camera.py              # Test camera devices
python3 test_microphone.py          # Test audio input
python3 documentation/troubleshooting/check_g1_hardware.py  # Complete hardware check
```

### Code Quality

```bash
# Pre-commit hooks (auto-formats on commit)
pre-commit install
pre-commit run --all-files

# Manual formatting:
black src/
isort src/
ruff check --fix src/

# Type checking:
pyright src/
```

## Configuration System (JSON5)

All agent configs live in `config/*.json5`. Key structure:

```json5
{
  name: "agent_name",
  hertz: 1,  // Cortex loop frequency
  api_key: "openmind_free",  // Or null
  
  // System prompts (injected into Fuser)
  system_prompt_base: "You are...",
  system_governance: "Laws that govern actions...",
  system_prompt_examples: "Example interactions...",
  
  // Inputs (dynamically loaded from src/inputs/plugins/)
  agent_inputs: [
    {
      type: "LocalASRInput",  // Class name from inputs/plugins/
      config: {
        engine: "faster-whisper",
        model_size: "tiny.en",
        // ... plugin-specific config
      }
    }
  ],
  
  // LLM (dynamically loaded from src/llm/plugins/)
  cortex_llm: {
    type: "OllamaLLM",  // Class name from llm/plugins/
    config: {
      model: "llama3.1:8b",
      base_url: "http://localhost:11434"
    }
  },
  
  // Actions (dynamically loaded from src/actions/)
  agent_actions: [
    {
      name: "speak",           // Directory name in src/actions/
      llm_label: "speak",      // Label LLM uses in JSON output
      connector: "piper_tts",  // File in actions/speak/connector/
      config: { /* ... */ }
    }
  ]
}
```

### Multi-Mode Configs

Add `modes` and `default_mode` for mode-aware agents:

```json5
{
  default_mode: "welcome",
  modes: {
    welcome: { /* mode config */ },
    exploration: { /* mode config */ }
  }
}
```

## Plugin Architecture Patterns

### Adding New Input Plugins

1. Create `src/inputs/plugins/my_sensor.py`
2. Class must inherit from `Sensor` (from `inputs.base`)
3. Implement `async def _raw_to_text(self, raw_input) -> str`
4. Use class name as `type` in config JSON5

Example: `src/inputs/plugins/local_asr.py`, `src/inputs/plugins/vlm_ollama_vision.py`

### Adding New Action Plugins

1. Create directory: `src/actions/my_action/`
2. Define interface: `src/actions/my_action/interface.py` (inherits `Interface`)
3. Create connector: `src/actions/my_action/connector/my_connector.py` (inherits `ActionConnector`)
4. Reference in config: `{name: "my_action", connector: "my_connector"}`

Example: `src/actions/speak/`, `src/actions/move_go2_action/`

### Adding New LLM Plugins

1. Create `src/llm/plugins/my_llm.py`
2. Class must inherit from `LLM` (from `llm`)
3. Implement `async def ask(self, prompt: str, actions: List, response_model) -> Any`
4. Use class name as `type` in cortex_llm config

Example: `src/llm/plugins/ollama_llm.py`, `src/llm/plugins/openai_llm.py`

## Project-Specific Conventions

### Dynamic Class Loading

- All plugins use **class name** as config key (not module name)
- Loader functions scan plugin directories at runtime: `load_input()`, `load_action()`, `load_llm()`
- See: `src/inputs/__init__.py:find_module_with_class()`, `src/actions/__init__.py:load_action()`

### Configuration Validation

- Runtime config validation in `src/runtime/single_mode/config.py:validate_config_keys()`
- Required keys: `hertz`, `name`, `system_prompt_base`, `system_governance`, `system_prompt_examples`, `cortex_llm`, `agent_actions`
- Optional: `robot_ip`, `URID`, `unitree_ethernet`

### Fuser Prompt Structure

The Fuser (`src/fuser/__init__.py`) constructs prompts in this order:
1. `BASIC CONTEXT:` - system_prompt_base
2. Input buffers (formatted_latest_buffer from each sensor)
3. `LAWS:` - system_governance (unless "Universal Laws" in inputs)
4. `EXAMPLES:` - system_prompt_examples
5. Action descriptions (auto-generated from interface docstrings)
6. `What will you do? Actions:`

### Environment Variables

Load from `.env` using `python-dotenv` (see `env.example`):
- `OPENAI_API_KEY`, `ELEVENLABS_API_KEY`, `GOOGLE_API_KEY`
- `OLLAMA_BASE_URL` (defaults to http://localhost:11434)
- `ROBOT_IP`, `URID`, `ETH_ADDRESS`

### Robot Hardware Integration

- **Zenoh**: Used for ROS2 bridge (see `src/inputs/plugins/zenoh.py`, `cyclonedds/cyclonedds.xml`)
- **Unitree SDK**: G1/Go2 robots use `unitree_ethernet` config (e.g., "eno1" on Linux)
- **Hardware tests**: `test_camera.py`, `test_microphone.py`, `documentation/troubleshooting/check_g1_hardware.py`

### Audio/TTS Specifics

- **Piper TTS**: Local offline TTS, voices in `piper_voices/`
- **ElevenLabs**: Cloud TTS (requires API key)
- **Whisper ASR**: Local via `faster-whisper` or cloud via OpenAI API
- Ubuntu G1 audio setup: `documentation/setup/setup_piper_ubuntu.sh`

## Important Files

- `src/run.py` - Main entry point, uses Typer CLI
- `src/runtime/single_mode/cortex.py` - Standard runtime loop
- `src/runtime/multi_mode/cortex.py` - Mode-switching runtime
- `src/fuser/__init__.py` - Prompt fusion logic
- `config/` - All agent configurations
- `documentation/` - Organized docs (setup, guides, troubleshooting)
- `pyproject.toml` - Dependencies, test config, linting rules

## Documentation Structure

- **Setup**: `documentation/setup/QUICKSTART.md`, `UBUNTU_G1_DEPLOYMENT.md`
- **Guides**: `documentation/guides/CONFIG_GUIDE.md`, integration guides
- **Troubleshooting**: Hardware testing scripts, audio diagnostics
- **Reference**: Quick references, refactor summaries

## Common Pitfalls

- **Missing `.env` keys**: Check `env.example` for required API keys
- **Ollama not running**: Start with `ollama serve` or `sudo systemctl start ollama`
- **Plugin not found**: Ensure class name (not filename) matches config `type`
- **Multi-mode vs single-mode**: Check if config has `modes` key to determine runtime type
- **Excluded directories**: `src/unitree`, `src/ubtech`, `gazebo` are excluded from tests/type checking (see `pyproject.toml`, `pyrightconfig.json`)
