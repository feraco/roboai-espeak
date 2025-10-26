#!/bin/bash
# Quick setup script for Jetson Orin
# This automates most of the setup process from JETSON_SETUP.md

set -e

echo "=========================================="
echo "Jetson Orin Complete Setup"
echo "=========================================="
echo ""
echo "This will install:"
echo "  - UV package manager"
echo "  - Ollama (local LLM)"
echo "  - System audio packages"
echo "  - Piper TTS"
echo "  - Python dependencies"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
fi

echo ""
echo "Step 1: Installing UV package manager..."
if ! command -v uv &> /dev/null; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
    echo 'export PATH="$HOME/.cargo/bin:$PATH"' >> ~/.bashrc
    echo "✓ UV installed"
else
    echo "✓ UV already installed: $(uv --version)"
fi

echo ""
echo "Step 2: Installing Ollama..."
if ! command -v ollama &> /dev/null; then
    curl -fsSL https://ollama.com/install.sh | sh
    sudo systemctl enable ollama
    sudo systemctl start ollama
    echo "✓ Ollama installed"
else
    echo "✓ Ollama already installed"
    sudo systemctl start ollama 2>/dev/null || true
fi

echo ""
echo "Step 3: Downloading LLM models (this may take 10-20 minutes)..."
echo "Pulling llama3.1:8b (~4.7 GB)..."
ollama pull llama3.1:8b
echo "Pulling llava-llama3 (~4.9 GB)..."
ollama pull llava-llama3
echo "✓ Models downloaded"

echo ""
echo "Step 4: Installing system audio packages..."
sudo apt-get update -qq
sudo apt-get install -y -qq \
    alsa-base alsa-utils libasound2 libasound2-dev alsa-plugins \
    portaudio19-dev libportaudio2 libportaudiocpp0 \
    libsndfile1 libsndfile1-dev \
    pulseaudio pulseaudio-utils \
    ffmpeg libavcodec-dev libavformat-dev libavutil-dev
echo "✓ Audio packages installed"

echo ""
echo "Step 5: Installing Piper TTS..."
if ! command -v piper &> /dev/null; then
    cd /tmp
    wget -q https://github.com/rhasspy/piper/releases/download/v1.2.0/piper_arm64.tar.gz
    tar -xzf piper_arm64.tar.gz
    sudo mv piper/piper /usr/local/bin/
    sudo chmod +x /usr/local/bin/piper
    echo "✓ Piper installed"
else
    echo "✓ Piper already installed"
fi

echo ""
echo "Step 6: Downloading Piper voice model..."
mkdir -p ~/piper_voices
cd ~/piper_voices
if [ ! -f "en_US-ryan-medium.onnx" ]; then
    wget -q https://github.com/rhasspy/piper/releases/download/v0.0.2/voice-en-us-ryan-medium.tar.gz
    tar -xzf voice-en-us-ryan-medium.tar.gz
    echo "✓ Voice model downloaded"
else
    echo "✓ Voice model already exists"
fi

echo ""
echo "Step 7: Installing Python dependencies..."
cd ~/roboai-espeak || cd "$(dirname "$0")"
uv sync
echo "✓ Python packages installed"

echo ""
echo "Step 8: Configuring audio permissions..."
sudo usermod -a -G audio $USER
echo "✓ User added to audio group"

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "⚠️  IMPORTANT: You MUST REBOOT for audio permissions to take effect!"
echo ""
echo "After reboot, test with:"
echo "  cd ~/roboai-espeak"
echo "  uv run python check_jetson_dependencies.py"
echo "  uv run python test_jetson_audio.py"
echo "  uv run src/run.py astra_vein_receptionist"
echo ""
read -p "Reboot now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    sudo reboot
fi
