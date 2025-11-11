#!/bin/bash
set -e

echo "========================================"
echo "  Lex Channel Chief Agent Installer"
echo "  For Jetson/Ubuntu ARM64"
echo "========================================"
echo ""

# Check if running on ARM64
if [ "$(uname -m)" != "aarch64" ]; then
    echo "❌ Error: This installer is for ARM64/Jetson devices only"
    echo "   Detected: $(uname -m)"
    exit 1
fi

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
    echo "❌ Error: Do not run this script as root (no sudo)"
    echo "   Run as: bash install_lex_jetson.sh"
    exit 1
fi

echo "✅ Platform check passed (ARM64)"
echo ""

# Install system dependencies
echo "📦 Installing system dependencies..."
sudo apt update
sudo apt install -y \
    python3 \
    python3-pip \
    curl \
    git \
    tesseract-ocr \
    tesseract-ocr-eng \
    pulseaudio \
    alsa-utils \
    portaudio19-dev \
    libopencv-dev \
    python3-opencv \
    || { echo "❌ Failed to install dependencies"; exit 1; }

echo "✅ System dependencies installed"
echo ""

# Install UV package manager
if ! command -v uv &> /dev/null; then
    echo "📦 Installing UV package manager..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
    echo "✅ UV installed"
else
    echo "✅ UV already installed"
fi
echo ""

# Install Ollama
if ! command -v ollama &> /dev/null; then
    echo "🤖 Installing Ollama..."
    curl -fsSL https://ollama.com/install.sh | sudo sh
    echo "✅ Ollama installed"
else
    echo "✅ Ollama already installed"
fi
echo ""

# Install Piper TTS
if ! command -v piper &> /dev/null; then
    echo "🎤 Installing Piper TTS..."
    cd /tmp
    wget -q https://github.com/rhasspy/piper/releases/download/2023.11.14-2/piper_arm64.tar.gz
    tar -xzf piper_arm64.tar.gz
    sudo mv piper/piper /usr/local/bin/
    sudo chmod +x /usr/local/bin/piper
    rm -rf piper piper_arm64.tar.gz
    echo "✅ Piper TTS installed"
else
    echo "✅ Piper TTS already installed"
fi
echo ""

# Clone/update repository
echo "📥 Setting up Lex agent code..."
INSTALL_DIR="$HOME/roboai-lex"

if [ -d "$INSTALL_DIR" ]; then
    echo "   Updating existing installation..."
    cd "$INSTALL_DIR"
    git pull origin main
else
    echo "   Cloning repository..."
    git clone https://github.com/feraco/roboai-espeak.git "$INSTALL_DIR"
    cd "$INSTALL_DIR"
fi

echo "✅ Code updated"
echo ""

# Install Python dependencies
echo "📦 Installing Python dependencies..."
cd "$INSTALL_DIR"
uv sync
echo "✅ Python dependencies installed"
echo ""

# Start Ollama service
echo "🚀 Starting Ollama service..."
sudo systemctl enable ollama
sudo systemctl start ollama
sleep 5
echo "✅ Ollama service started"
echo ""

# Pull LLM model
echo "🤖 Downloading LLM model (llama3.1:8b)..."
echo "   This may take several minutes..."
ollama pull llama3.1:8b
echo "✅ LLM model downloaded"
echo ""

# Download Piper voices
echo "🗣️  Downloading TTS voices..."
mkdir -p "$INSTALL_DIR/piper_voices"
cd "$INSTALL_DIR/piper_voices"

# English voice (Ryan - male)
if [ ! -f "en_US-ryan-medium.onnx" ]; then
    echo "   Downloading English voice..."
    wget -q https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/ryan/medium/en_US-ryan-medium.onnx
    wget -q https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/ryan/medium/en_US-ryan-medium.onnx.json
fi

# Russian voice (Dmitri - male)
if [ ! -f "ru_RU-dmitri-medium.onnx" ]; then
    echo "   Downloading Russian voice..."
    wget -q https://huggingface.co/rhasspy/piper-voices/resolve/main/ru/ru_RU/dmitri/medium/ru_RU-dmitri-medium.onnx
    wget -q https://huggingface.co/rhasspy/piper-voices/resolve/main/ru/ru_RU/dmitri/medium/ru_RU-dmitri-medium.onnx.json
fi

echo "✅ TTS voices downloaded"
echo ""

# Create systemd service
echo "⚙️  Installing systemd service..."
sudo tee /etc/systemd/system/lex-agent.service > /dev/null << SERVICE
[Unit]
Description=Lex Channel Chief AI Agent for Lexful
After=network-online.target ollama.service sound.target
Wants=network-online.target ollama.service

[Service]
Type=simple
User=$USER
Group=$USER
WorkingDirectory=$HOME/roboai-lex
Environment="PATH=$HOME/.local/bin:/usr/local/bin:/usr/bin:/bin"
Environment="DISPLAY=:0"
Environment="XAUTHORITY=$HOME/.Xauthority"
Environment="DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus"
Environment="PULSE_SERVER=unix:/run/user/1000/pulse/native"
Environment="XDG_RUNTIME_DIR=/run/user/1000"
Environment="SKIP_AUDIO_VALIDATION=true"

# Wait for system to be fully ready
ExecStartPre=/bin/sleep 20

# Ensure Ollama is running
ExecStartPre=/bin/bash -c "systemctl is-active ollama || sudo systemctl start ollama"
ExecStartPre=/bin/sleep 5

# Test Ollama model
ExecStartPre=/bin/bash -c "timeout 20 ollama run llama3.1:8b 'Reply OK' || exit 1"

# Clear stale configs
ExecStartPre=/bin/bash -c "cd $HOME/roboai-lex && rm -f device_config.yaml"

# Start agent
ExecStart=$HOME/.local/bin/uv run $HOME/roboai-lex/src/run.py lex_channel_chief

# Restart on failure
Restart=on-failure
RestartSec=10

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=lex-agent

[Install]
WantedBy=multi-user.target
SERVICE

# Replace $USER and $HOME with actual values
sudo sed -i "s|\$USER|$USER|g" /etc/systemd/system/lex-agent.service
sudo sed -i "s|\$HOME|$HOME|g" /etc/systemd/system/lex-agent.service

sudo systemctl daemon-reload
sudo systemctl enable lex-agent
echo "✅ Systemd service installed"
echo ""

# Start the service
echo "🚀 Starting Lex agent..."
sudo systemctl start lex-agent
sleep 3

# Check status
echo ""
echo "========================================"
echo "  Installation Complete!"
echo "========================================"
echo ""
echo "✅ Lex Channel Chief agent is now running as a systemd service"
echo ""
echo "📋 Useful Commands:"
echo ""
echo "  Check status:       sudo systemctl status lex-agent"
echo "  View live logs:     sudo journalctl -u lex-agent -f"
echo "  Stop agent:         sudo systemctl stop lex-agent"
echo "  Start agent:        sudo systemctl start lex-agent"
echo "  Restart agent:      sudo systemctl restart lex-agent"
echo "  Disable auto-start: sudo systemctl disable lex-agent"
echo ""
echo "  Manual run:         cd ~/roboai-lex && uv run src/run.py lex_channel_chief"
echo ""
echo "  Update agent:       cd ~/roboai-lex && git pull && uv sync && sudo systemctl restart lex-agent"
echo ""
echo "📊 Current Status:"
sudo systemctl status lex-agent --no-pager -l
