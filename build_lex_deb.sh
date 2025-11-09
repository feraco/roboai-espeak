#!/bin/bash
set -e

echo "========================================"
echo "  Lex Agent .deb Package Builder"
echo "  Target: ARM64 (Jetson)"
echo "========================================"
echo ""

PACKAGE_NAME="lex-agent"
PACKAGE_VERSION="1.0.0"
ARCH="arm64"
BUILD_DIR="lex_package"
PACKAGE_DIR="${BUILD_DIR}/${PACKAGE_NAME}_${PACKAGE_VERSION}_${ARCH}"

# Clean previous build
echo "🧹 Cleaning previous build..."
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

# Create package directory structure
echo "📁 Creating package structure..."
mkdir -p "${PACKAGE_DIR}/DEBIAN"
mkdir -p "${PACKAGE_DIR}/opt/roboai-lex"
mkdir -p "${PACKAGE_DIR}/etc/systemd/system"
mkdir -p "${PACKAGE_DIR}/usr/local/bin"

echo "✅ Directory structure created"
echo ""

# Create control file
echo "📝 Creating DEBIAN/control file..."
cat > "${PACKAGE_DIR}/DEBIAN/control" << 'EOF'
Package: lex-agent
Version: 1.0.0
Section: utils
Priority: optional
Architecture: arm64
Depends: python3 (>= 3.10), python3-pip, curl, git, tesseract-ocr, pulseaudio, alsa-utils, portaudio19-dev
Maintainer: Frederick Feraco <frederick@lexful.ai>
Description: Lex Channel Chief AI Agent for Lexful
 AI-powered conversational agent with badge detection,
 speech recognition, and text-to-speech capabilities.
 Includes automatic systemd service setup for Jetson/Ubuntu ARM64.
 .
 Features:
  - OCR-based badge reader for personalized greetings
  - Local speech recognition with Faster-Whisper
  - Piper TTS for natural voice output
  - Ollama integration for LLM (llama3.1:8b)
  - Knowledge base integration for Lexful product info
  - Auto-start on boot via systemd
Homepage: https://github.com/feraco/roboai-espeak
EOF

echo "✅ Control file created"
echo ""

# Create postinst script
echo "📝 Creating DEBIAN/postinst script..."
cat > "${PACKAGE_DIR}/DEBIAN/postinst" << 'EOF'
#!/bin/bash
set -e

echo "=== Lex Agent Post-Installation ==="

# Get the user who invoked sudo (or current user if not sudo)
REAL_USER="${SUDO_USER:-$USER}"
REAL_HOME=$(eval echo ~$REAL_USER)

# Install UV package manager for the real user
if ! sudo -u "$REAL_USER" bash -c "command -v uv &> /dev/null"; then
    echo "📦 Installing UV package manager..."
    sudo -u "$REAL_USER" bash -c "curl -LsSf https://astral.sh/uv/install.sh | sh"
fi

# Install Ollama if not present
if ! command -v ollama &> /dev/null; then
    echo "🤖 Installing Ollama..."
    curl -fsSL https://ollama.com/install.sh | sh
fi

# Install Piper TTS if not present
if ! command -v piper &> /dev/null; then
    echo "🎤 Installing Piper TTS..."
    cd /tmp
    wget -q https://github.com/rhasspy/piper/releases/download/2023.11.14-2/piper_arm64.tar.gz
    tar -xzf piper_arm64.tar.gz
    mv piper/piper /usr/local/bin/
    chmod +x /usr/local/bin/piper
    rm -rf piper piper_arm64.tar.gz
fi

# Start Ollama service
echo "🚀 Starting Ollama service..."
systemctl enable ollama 2>/dev/null || true
systemctl start ollama 2>/dev/null || true
sleep 5

# Pull LLM model
echo "🤖 Pulling llama3.1:8b model (this may take several minutes)..."
sudo -u "$REAL_USER" ollama pull llama3.1:8b || echo "⚠️  Model download failed - you may need to run: ollama pull llama3.1:8b"

# Install Python dependencies
echo "📦 Installing Python dependencies..."
cd /opt/roboai-lex
sudo -u "$REAL_USER" bash -c "export PATH=\"$REAL_HOME/.local/bin:\$PATH\" && uv sync"

# Download Piper voices
echo "🗣️  Downloading TTS voices..."
mkdir -p /opt/roboai-lex/piper_voices
cd /opt/roboai-lex/piper_voices

# English voice
if [ ! -f "en_US-ryan-medium.onnx" ]; then
    wget -q https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/ryan/medium/en_US-ryan-medium.onnx
    wget -q https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/ryan/medium/en_US-ryan-medium.onnx.json
fi

# Russian voice
if [ ! -f "ru_RU-dmitri-medium.onnx" ]; then
    wget -q https://huggingface.co/rhasspy/piper-voices/resolve/main/ru/ru_RU/dmitri/medium/ru_RU-dmitri-medium.onnx
    wget -q https://huggingface.co/rhasspy/piper-voices/resolve/main/ru/ru_RU/dmitri/medium/ru_RU-dmitri-medium.onnx.json
fi

# Set ownership
chown -R "$REAL_USER":"$REAL_USER" /opt/roboai-lex

# Update systemd service with actual user
sed -i "s/User=unitree/User=$REAL_USER/g" /etc/systemd/system/lex-agent.service
sed -i "s|WorkingDirectory=/opt/roboai-lex|WorkingDirectory=/opt/roboai-lex|g" /etc/systemd/system/lex-agent.service
sed -i "s|/home/unitree/.local/bin/uv|$REAL_HOME/.local/bin/uv|g" /etc/systemd/system/lex-agent.service

# Reload and enable service
systemctl daemon-reload
systemctl enable lex-agent
systemctl start lex-agent

echo ""
echo "=== Installation Complete! ==="
echo ""
echo "✅ Lex Agent is now running as a systemd service"
echo ""
echo "📋 Commands:"
echo "  sudo systemctl status lex-agent    # Check status"
echo "  sudo systemctl stop lex-agent      # Stop agent"
echo "  sudo systemctl start lex-agent     # Start agent"
echo "  sudo journalctl -u lex-agent -f    # View logs"
echo ""

exit 0
EOF

chmod +x "${PACKAGE_DIR}/DEBIAN/postinst"
echo "✅ Post-install script created"
echo ""

# Create prerm script
echo "📝 Creating DEBIAN/prerm script..."
cat > "${PACKAGE_DIR}/DEBIAN/prerm" << 'EOF'
#!/bin/bash
set -e

echo "=== Stopping Lex Agent ==="
systemctl stop lex-agent 2>/dev/null || true
systemctl disable lex-agent 2>/dev/null || true

exit 0
EOF

chmod +x "${PACKAGE_DIR}/DEBIAN/prerm"
echo "✅ Pre-remove script created"
echo ""

# Create postrm script
echo "📝 Creating DEBIAN/postrm script..."
cat > "${PACKAGE_DIR}/DEBIAN/postrm" << 'EOF'
#!/bin/bash
set -e

if [ "$1" = "purge" ]; then
    echo "=== Purging Lex Agent ==="
    rm -rf /opt/roboai-lex
    rm -f /etc/systemd/system/lex-agent.service
    systemctl daemon-reload
fi

exit 0
EOF

chmod +x "${PACKAGE_DIR}/DEBIAN/postrm"
echo "✅ Post-remove script created"
echo ""

# Copy application files
echo "📦 Copying application files..."
rsync -av --progress \
    --exclude='.git' \
    --exclude='__pycache__' \
    --exclude='.venv' \
    --exclude='*.pyc' \
    --exclude='.pytest_cache' \
    --exclude='lex_package' \
    --exclude='debian_package' \
    --exclude='jetson_package' \
    --exclude='.DS_Store' \
    --exclude='audio_output' \
    --exclude='tmp_audio' \
    --exclude='device_config.yaml' \
    ./ "${PACKAGE_DIR}/opt/roboai-lex/"

echo "✅ Application files copied"
echo ""

# Copy systemd service file
echo "📝 Creating systemd service file..."
cat > "${PACKAGE_DIR}/etc/systemd/system/lex-agent.service" << 'EOF'
[Unit]
Description=Lex Channel Chief AI Agent for Lexful
After=network-online.target ollama.service sound.target
Wants=network-online.target ollama.service

[Service]
Type=simple
User=unitree
Group=unitree
WorkingDirectory=/opt/roboai-lex
Environment="PATH=/home/unitree/.local/bin:/usr/local/bin:/usr/bin:/bin"
Environment="DISPLAY=:0"
Environment="XAUTHORITY=/home/unitree/.Xauthority"
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
ExecStartPre=/bin/bash -c "cd /opt/roboai-lex && rm -f device_config.yaml"

# Start agent
ExecStart=/home/unitree/.local/bin/uv run /opt/roboai-lex/src/run.py lex_channel_chief

# Restart on failure
Restart=on-failure
RestartSec=10

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=lex-agent

[Install]
WantedBy=multi-user.target
EOF

echo "✅ Systemd service file created"
echo ""

# Create convenience command
echo "📝 Creating lex-agent command..."
cat > "${PACKAGE_DIR}/usr/local/bin/lex-agent" << 'EOF'
#!/bin/bash
cd /opt/roboai-lex
exec uv run src/run.py lex_channel_chief "$@"
EOF

chmod +x "${PACKAGE_DIR}/usr/local/bin/lex-agent"
echo "✅ Convenience command created"
echo ""

# Package structure is ready
echo ""
echo "========================================"
echo "  ✅ Package Structure Created!"
echo "========================================"
echo ""
echo "📦 Package directory: ${BUILD_DIR}/${PACKAGE_NAME}_${PACKAGE_VERSION}_${ARCH}/"
echo ""
echo "📋 Next Steps:"
echo ""
echo "OPTION 1: Build on Jetson (Recommended)"
echo "  1. Copy to Jetson:"
echo "     scp -r ${BUILD_DIR} unitree@JETSON_IP:~/roboai-lex/"
echo ""
echo "  2. Build on Jetson:"
echo "     ssh unitree@JETSON_IP"
echo "     cd ~/roboai-lex/${BUILD_DIR}"
echo "     dpkg-deb --build ${PACKAGE_NAME}_${PACKAGE_VERSION}_${ARCH}"
echo ""
echo "  3. Install:"
echo "     sudo dpkg -i ${PACKAGE_NAME}_${PACKAGE_VERSION}_${ARCH}.deb"
echo "     sudo apt install -f -y"
echo ""
echo "OPTION 2: Use build script"
echo "  1. Copy everything to Jetson:"
echo "     scp -r ${BUILD_DIR} build_deb_on_jetson.sh unitree@JETSON_IP:~/roboai-lex/"
echo ""
echo "  2. Run build script on Jetson:"
echo "     ssh unitree@JETSON_IP"
echo "     cd ~/roboai-lex"
echo "     bash build_deb_on_jetson.sh"
echo ""
echo "  3. Install:"
echo "     sudo dpkg -i ${BUILD_DIR}/${PACKAGE_NAME}_${PACKAGE_VERSION}_${ARCH}.deb"
echo "     sudo apt install -f -y"
echo ""
echo "OPTION 3: Use installer script (no .deb needed)"
echo "  bash install_lex_jetson.sh"
echo ""
