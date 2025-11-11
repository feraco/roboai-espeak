# Lex Channel Chief Agent - Debian Package

Complete `.deb` package for installing Lex agent on Jetson/Ubuntu ARM64.

## Quick Install (Recommended)

Use the all-in-one installer script (no .deb building needed):

```bash
# On Jetson
bash install_lex_jetson.sh
```

## Build .deb Package

### Step 1: Prepare Package (On Mac)

```bash
# On your Mac
cd /path/to/roboai-espeak
./build_lex_deb.sh
```

This creates `lex_package/lex-agent_1.0.0_arm64/` with all files.

### Step 2: Copy to Jetson

```bash
# Copy package folder and build script
scp -r lex_package build_deb_on_jetson.sh unitree@JETSON_IP:~/
```

### Step 3: Build on Jetson

```bash
# SSH to Jetson
ssh unitree@JETSON_IP

# Build the .deb
bash build_deb_on_jetson.sh
```

### Step 4: Install

```bash
# Install the package
sudo dpkg -i lex_package/lex-agent_1.0.0_arm64.deb

# Fix any missing dependencies
sudo apt install -f -y

# Check status
sudo systemctl status lex-agent
```

## What Gets Installed

- **Application**: `/opt/roboai-lex/` (all source code)
- **Service**: `/etc/systemd/system/lex-agent.service` (auto-start on boot)
- **Command**: `/usr/local/bin/lex-agent` (run manually)
- **Dependencies**: Ollama, Piper TTS, UV, Python packages

## Post-Installation

The package automatically:
1. Installs UV package manager
2. Installs and starts Ollama
3. Downloads llama3.1:8b model (~4.7 GB)
4. Installs Piper TTS
5. Downloads English and Russian TTS voices
6. Installs Python dependencies
7. Enables and starts lex-agent service

## Service Management

```bash
# Check status
sudo systemctl status lex-agent

# View logs
sudo journalctl -u lex-agent -f

# Stop/start/restart
sudo systemctl stop lex-agent
sudo systemctl start lex-agent
sudo systemctl restart lex-agent

# Disable auto-start
sudo systemctl disable lex-agent
```

## Manual Run (Without Service)

```bash
# Stop service first
sudo systemctl stop lex-agent

# Run manually
cd /opt/roboai-lex
uv run src/run.py lex_channel_chief
```

## Updating

```bash
# Stop service
sudo systemctl stop lex-agent

# Update code
cd /opt/roboai-lex
git pull origin main
uv sync

# Restart service
sudo systemctl restart lex-agent
```

## Uninstall

```bash
# Remove package
sudo apt remove lex-agent

# Purge all files (including /opt/roboai-lex)
sudo apt purge lex-agent

# Optional: Remove Ollama
sudo systemctl stop ollama
sudo systemctl disable ollama
sudo rm /usr/local/bin/ollama
sudo rm -rf ~/.ollama
```

## Troubleshooting

### Package Installation Fails

```bash
# Check for missing dependencies
sudo apt install -f

# View detailed error
sudo dpkg -i lex-agent_1.0.0_arm64.deb
```

### Service Won't Start

```bash
# Check logs
sudo journalctl -u lex-agent -n 100

# Common issues:
# 1. Ollama not running: sudo systemctl start ollama
# 2. Model not downloaded: ollama pull llama3.1:8b
# 3. UV not in PATH: export PATH="$HOME/.local/bin:$PATH"
```

### Audio Issues

```bash
# Test microphone
cd /opt/roboai-lex
python3 test_microphone.py

# Test camera
python3 test_camera.py

# Restart audio
pulseaudio --kill && sleep 2 && pulseaudio --start
```

## Package Contents

```
lex-agent_1.0.0_arm64/
├── DEBIAN/
│   ├── control          # Package metadata
│   ├── postinst         # Post-install script (downloads models, starts service)
│   ├── prerm            # Pre-remove script (stops service)
│   └── postrm           # Post-remove script (cleanup)
├── opt/roboai-lex/      # Application files
│   ├── src/             # Source code
│   ├── config/          # Agent configurations
│   ├── docs/            # Knowledge base
│   └── ...
├── etc/systemd/system/
│   └── lex-agent.service  # Systemd service
└── usr/local/bin/
    └── lex-agent        # Convenience command
```

## Files

- `build_lex_deb.sh` - Prepare package structure (run on Mac)
- `build_deb_on_jetson.sh` - Build .deb file (run on Jetson)
- `install_lex_jetson.sh` - All-in-one installer (easiest method)
- `LEX_PACKAGE_README.md` - This file

## Support

- GitHub: https://github.com/feraco/roboai-espeak
- Issues: https://github.com/feraco/roboai-espeak/issues
