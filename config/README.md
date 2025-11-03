# OM1 Configuration Directory Structure

This directory contains all agent configurations organized by category for better maintainability and discovery.

## 📁 Directory Structure

### 🤖 **lex_channel_chief.json5** (Main Config)
The primary configuration for the Lex Channel Chief agent - Lexful's AI-native IT documentation platform representative.

### 🤖 **robots/** - Robot Hardware Configurations
Physical robot configurations for various platforms:
- `unitree_*` - Unitree G1 humanoid and Go2 quadruped robots
- `spot_*` - Boston Dynamics Spot configurations
- `turtlebot4_*` - TurtleBot4 navigation and mapping
- `ubtech_*` - UBTech Yanshee humanoid robot
- `astra_vein_*` - Astra Vein receptionist configurations
- `quadruped_sim.json5` - Quadruped simulation

### ☁️ **cloud/** - Cloud-Based LLM Configurations
Configurations using cloud-based AI services:
- `cloud_*` - Cloud service combinations (OpenAI, Google, Azure)
- `open_ai.json5` - OpenAI GPT models
- `gemini.json5` - Google Gemini
- `deepseek.json5` - DeepSeek AI
- `grok.json5` - xAI Grok
- `twitter.json5` - Social media integration

### 🏠 **local/** - Local/Offline Configurations
Completely offline configurations for privacy and performance:
- `local_*` - Local Ollama-based configurations
- `macos_offline_agent.json5` - macOS optimized offline setup
- `gpu_optimized_local.json5` - GPU-accelerated local processing

### 🔀 **hybrid/** - Hybrid Configurations
Mixed cloud/local service combinations:
- `hybrid_cloud_llm_local_audio.json5` - Cloud LLM + local TTS/ASR
- `hybrid_local_llm_cloud_audio.json5` - Local LLM + cloud audio services
- `hybrid_mixed_cloud.json5` - Multiple cloud service combinations

### 🧪 **testing/** - Development & Testing Configurations
Configurations for development, testing, and debugging:
- `test_*` - Sensor and hardware testing configs
- `dev_mock_services.json5` - Mock services for development

### 🎯 **demo/** - Demo & Example Configurations
Demonstration and example configurations:
- `funny_robot*` - Entertainment robot demos
- `joker_bot.json5` - Comedy/entertainment agent
- `conversation.json5` - General conversation agent
- `tesla.json5` - Tesla-themed configuration
- Other themed demo configurations

### 📋 **schema/** - Configuration Schemas
JSON schemas for validation:
- `single_mode_schema.json` - Single-mode agent validation
- `multi_mode_schema.json` - Multi-mode agent validation

## 🚀 Usage Examples

```bash
# Run the main Lex Channel Chief agent
uv run src/run.py lex_channel_chief

# Run a robot configuration
uv run src/run.py robots/unitree_g1_humanoid

# Run a cloud configuration
uv run src/run.py cloud/gemini

# Run a local configuration
uv run src/run.py local/local_agent

# Run a demo configuration
uv run src/run.py demo/funny_robot
```

## 📝 Configuration Guidelines

- **Main Config**: Keep `lex_channel_chief.json5` in root for primary use case
- **Naming**: Use descriptive names with category prefixes
- **Documentation**: Include comments in JSON5 files explaining purpose
- **Validation**: All configs should validate against appropriate schemas
- **Testing**: Test configurations should be clearly marked and documented

## 🔧 Adding New Configurations

1. Choose appropriate subdirectory based on configuration type
2. Follow naming conventions for the category
3. Include descriptive comments in the JSON5 file
4. Test configuration before committing
5. Update this README if adding new categories

---

*This organization follows OM1 project conventions and maintains backward compatibility with existing scripts and tools.*