# 📚 Documentation

Complete documentation for the RoboAI system, organized by category.

## 🚀 Quick Links

- **[Main README](../README.md)** - Project overview
- **[Quick Start](setup/QUICKSTART.md)** - Get started in 5 minutes
- **[Ubuntu G1 Deployment](setup/UBUNTU_G1_DEPLOYMENT.md)** - Complete G1 robot setup guide

## 📁 Documentation Structure

### 🛠️ [setup/](setup/)
Installation and initial configuration guides.

- **[QUICKSTART.md](setup/QUICKSTART.md)** - Fast setup guide
- **[UBUNTU_G1_DEPLOYMENT.md](setup/UBUNTU_G1_DEPLOYMENT.md)** - Full Ubuntu G1 deployment with troubleshooting
- **[API_KEYS_GUIDE.md](setup/API_KEYS_GUIDE.md)** - API key configuration
- **[LOCAL_SETUP.md](setup/LOCAL_SETUP.md)** - Local development setup
- **[QUICK_INSTALL_MAC.md](setup/QUICK_INSTALL_MAC.md)** - macOS installation
- **[FASTER_WHISPER_INSTALL.md](setup/FASTER_WHISPER_INSTALL.md)** - Whisper ASR setup
- **Scripts:**
  - `setup_with_uv.sh` - UV package manager setup
  - `setup_piper_ubuntu.sh` - Piper TTS installer for Ubuntu
  - `setup_g1_autostart.sh` - Auto-start service setup
  - `setup_g1_hotspot.sh` - WiFi hotspot creation
  - `setup_robostore_ai.sh` - Web control panel setup

### 📖 [guides/](guides/)
Integration and usage guides for advanced features.

- **[CONFIG_GUIDE.md](guides/CONFIG_GUIDE.md)** - Configuration system explained
- **[G1_ARM_INTEGRATION_GUIDE.md](guides/G1_ARM_INTEGRATION_GUIDE.md)** - Robot arm gesture control
- **[G1_COMPLETE_SETUP_GUIDE.md](guides/G1_COMPLETE_SETUP_GUIDE.md)** - Complete G1 setup
- **[G1_AUTOSTART_GUIDE.md](guides/G1_AUTOSTART_GUIDE.md)** - Systemd service configuration
- **[G1_HOTSPOT_GUIDE.md](guides/G1_HOTSPOT_GUIDE.md)** - WiFi hotspot setup
- **[ROBOSTORE_AI_GUIDE.md](guides/ROBOSTORE_AI_GUIDE.md)** - Web control panel
- **[AVSPEECH_INTEGRATION.md](guides/AVSPEECH_INTEGRATION.md)** - AVSpeech integration

### 🔧 [troubleshooting/](troubleshooting/)
Diagnostic tools and problem-solving guides.

- **[G1_AUDIO_AUTO_FIX.md](troubleshooting/G1_AUDIO_AUTO_FIX.md)** - Audio auto-detection guide
- **[G1_HARDWARE_TESTING.md](troubleshooting/G1_HARDWARE_TESTING.md)** - Hardware testing commands
- **Scripts:**
  - `check_g1_hardware.py` - Complete hardware validation
  - `diagnose_ubuntu_audio.py` - Detailed audio diagnostics
  - `test_g1_hardware.sh` - Interactive hardware testing
  - `test_ubuntu_mic.sh` - Quick microphone test
  - `fix_g1_audio.sh` - Audio troubleshooting script

### 📋 [reference/](reference/)
Technical references and specifications.

- **[QUICK_CONFIG_REFERENCE.md](reference/QUICK_CONFIG_REFERENCE.md)** - Config quick reference
- **[CONFIGURATION_FIX_SUMMARY.md](reference/CONFIGURATION_FIX_SUMMARY.md)** - Configuration fixes
- **[REFACTOR_SUMMARY.md](reference/REFACTOR_SUMMARY.md)** - System architecture changes

### 💡 [examples/](examples/)
Example configurations and use cases.

*Coming soon*

## 🎯 Common Tasks

### Getting Started
1. Read [QUICKSTART.md](setup/QUICKSTART.md)
2. Configure API keys: [API_KEYS_GUIDE.md](setup/API_KEYS_GUIDE.md)
3. Choose your platform:
   - **Ubuntu/G1**: [UBUNTU_G1_DEPLOYMENT.md](setup/UBUNTU_G1_DEPLOYMENT.md)
   - **macOS**: [QUICK_INSTALL_MAC.md](setup/QUICK_INSTALL_MAC.md)
   - **Local Dev**: [LOCAL_SETUP.md](setup/LOCAL_SETUP.md)

### Troubleshooting
1. Run hardware check: `python3 troubleshooting/check_g1_hardware.py`
2. Audio issues: [G1_AUDIO_AUTO_FIX.md](troubleshooting/G1_AUDIO_AUTO_FIX.md)
3. Microphone test: `./troubleshooting/test_ubuntu_mic.sh`
4. Full diagnostics: `python3 troubleshooting/diagnose_ubuntu_audio.py`

### Configuration
1. Read [CONFIG_GUIDE.md](guides/CONFIG_GUIDE.md)
2. Quick reference: [QUICK_CONFIG_REFERENCE.md](reference/QUICK_CONFIG_REFERENCE.md)
3. Example configs in `../config/`

### Advanced Features
- **Robot Arm Control**: [G1_ARM_INTEGRATION_GUIDE.md](guides/G1_ARM_INTEGRATION_GUIDE.md)
- **Web Interface**: [ROBOSTORE_AI_GUIDE.md](guides/ROBOSTORE_AI_GUIDE.md)
- **WiFi Hotspot**: [G1_HOTSPOT_GUIDE.md](guides/G1_HOTSPOT_GUIDE.md)
- **Auto-Start**: [G1_AUTOSTART_GUIDE.md](guides/G1_AUTOSTART_GUIDE.md)

## 🆘 Need Help?

1. **Check troubleshooting docs** in [troubleshooting/](troubleshooting/)
2. **Run diagnostic tools**:
   ```bash
   # Complete hardware check
   python3 troubleshooting/check_g1_hardware.py
   
   # Audio diagnostics
   python3 troubleshooting/diagnose_ubuntu_audio.py
   
   # Quick mic test
   ./troubleshooting/test_ubuntu_mic.sh
   ```
3. **GitHub Issues**: https://github.com/feraco/roboai-espeak/issues

## 🤝 Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) for contribution guidelines.

## 📜 License

See [LICENSE](../LICENSE) for license information.
