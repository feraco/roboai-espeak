#!/bin/bash

# Setup Piper TTS for Ubuntu G1
# Installs Piper and downloads voice models

set -e  # Exit on error

echo "=================================================="
echo "🎵 PIPER TTS SETUP FOR UBUNTU G1"
echo "=================================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PIPER_VERSION="2023.11.14-2"
VOICE_MODEL="en_US-ryan-medium"
INSTALL_DIR="$HOME/.local/share/piper"
VOICES_DIR="$INSTALL_DIR/voices"
BIN_DIR="$HOME/.local/bin"

echo -e "${BLUE}Installation directories:${NC}"
echo "  Piper: $INSTALL_DIR"
echo "  Voices: $VOICES_DIR"
echo "  Binary: $BIN_DIR"
echo ""

# Create directories
mkdir -p "$INSTALL_DIR"
mkdir -p "$VOICES_DIR"
mkdir -p "$BIN_DIR"

# Check if piper is already installed
if command -v piper &> /dev/null; then
    echo -e "${GREEN}✅ Piper already installed${NC}"
    piper --version
else
    echo -e "${BLUE}📥 Downloading Piper...${NC}"
    
    cd "$INSTALL_DIR"
    
    # Detect architecture
    ARCH=$(uname -m)
    if [ "$ARCH" = "x86_64" ]; then
        PIPER_ARCH="amd64"
        DOWNLOAD_URL="https://github.com/rhasspy/piper/releases/download/${PIPER_VERSION}/piper_linux_x86_64.tar.gz"
    elif [ "$ARCH" = "aarch64" ]; then
        PIPER_ARCH="arm64"
        DOWNLOAD_URL="https://github.com/rhasspy/piper/releases/download/${PIPER_VERSION}/piper_linux_aarch64.tar.gz"
    else
        echo -e "${RED}❌ Unsupported architecture: $ARCH${NC}"
        exit 1
    fi
    
    echo "  Architecture: $ARCH ($PIPER_ARCH)"
    echo "  URL: $DOWNLOAD_URL"
    
    # Download
    wget -O piper.tar.gz "$DOWNLOAD_URL"
    
    echo -e "${BLUE}📦 Extracting Piper...${NC}"
    tar -xzf piper.tar.gz
    rm piper.tar.gz
    
    # Make symlink in PATH
    ln -sf "$INSTALL_DIR/piper/piper" "$BIN_DIR/piper"
    
    # Add to PATH if not already there
    if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
        echo "export PATH=\"\$HOME/.local/bin:\$PATH\"" >> ~/.bashrc
        export PATH="$BIN_DIR:$PATH"
        echo -e "${YELLOW}⚠️  Added $BIN_DIR to PATH in ~/.bashrc${NC}"
        echo -e "${YELLOW}   Run: source ~/.bashrc  (or restart terminal)${NC}"
    fi
    
    echo -e "${GREEN}✅ Piper installed${NC}"
fi

# Download voice model
echo ""
echo -e "${BLUE}📥 Downloading voice model: $VOICE_MODEL${NC}"

# Parse voice model name
IFS='_-' read -ra PARTS <<< "$VOICE_MODEL"
LANG="${PARTS[0]}"          # en
LOCALE="${PARTS[0]}_${PARTS[1]}"  # en_US
VOICE="${PARTS[2]}"         # ryan
QUALITY="${PARTS[3]}"       # medium

VOICE_PATH="$VOICES_DIR/$LANG/$LOCALE/$VOICE/$QUALITY"
mkdir -p "$VOICE_PATH"

ONNX_FILE="$VOICE_PATH/${VOICE_MODEL}.onnx"
JSON_FILE="$VOICE_PATH/${VOICE_MODEL}.onnx.json"

if [ -f "$ONNX_FILE" ] && [ -f "$JSON_FILE" ]; then
    echo -e "${GREEN}✅ Voice model already downloaded${NC}"
else
    echo "  Downloading to: $VOICE_PATH"
    
    cd "$VOICE_PATH"
    
    # Download from HuggingFace
    BASE_URL="https://huggingface.co/rhasspy/piper-voices/resolve/main/$LANG/$LOCALE/$VOICE/$QUALITY"
    
    echo "  Downloading ${VOICE_MODEL}.onnx..."
    wget -q --show-progress "${BASE_URL}/${VOICE_MODEL}.onnx"
    
    echo "  Downloading ${VOICE_MODEL}.onnx.json..."
    wget -q --show-progress "${BASE_URL}/${VOICE_MODEL}.onnx.json"
    
    echo -e "${GREEN}✅ Voice model downloaded${NC}"
fi

# Test installation
echo ""
echo -e "${BLUE}🧪 Testing Piper TTS...${NC}"

cd "$VOICE_PATH"

TEST_TEXT="Hello, this is a test of the Piper text to speech system on Ubuntu."
TEST_FILE="/tmp/piper_test.wav"

echo "$TEST_TEXT" | piper --model "$ONNX_FILE" --config "$JSON_FILE" --output_file "$TEST_FILE"

if [ -f "$TEST_FILE" ]; then
    echo -e "${GREEN}✅ Audio file generated: $TEST_FILE${NC}"
    
    # Try to play it
    if command -v aplay &> /dev/null; then
        echo "Playing audio..."
        aplay "$TEST_FILE" 2>/dev/null || echo -e "${YELLOW}⚠️  Could not play audio (check speakers)${NC}"
    elif command -v paplay &> /dev/null; then
        echo "Playing audio..."
        paplay "$TEST_FILE" 2>/dev/null || echo -e "${YELLOW}⚠️  Could not play audio (check speakers)${NC}"
    else:
        echo -e "${YELLOW}⚠️  No audio player found (install: sudo apt install alsa-utils)${NC}"
    fi
    
    rm -f "$TEST_FILE"
else
    echo -e "${RED}❌ Failed to generate audio${NC}"
    exit 1
fi

# Create test script
TEST_SCRIPT="$HOME/test_piper.sh"
cat > "$TEST_SCRIPT" << 'EOF'
#!/bin/bash
# Quick Piper TTS test script

VOICE_PATH="$HOME/.local/share/piper/voices/en/en_US/ryan/medium"
MODEL="$VOICE_PATH/en_US-ryan-medium.onnx"
CONFIG="$VOICE_PATH/en_US-ryan-medium.onnx.json"
OUTPUT="/tmp/piper_test_$(date +%s).wav"

if [ $# -eq 0 ]; then
    TEXT="Hello, this is a test."
else
    TEXT="$*"
fi

echo "Speaking: $TEXT"
echo "$TEXT" | piper --model "$MODEL" --config "$CONFIG" --output_file "$OUTPUT"

if [ -f "$OUTPUT" ]; then
    echo "Generated: $OUTPUT"
    
    if command -v aplay &> /dev/null; then
        aplay "$OUTPUT"
    elif command -v paplay &> /dev/null; then
        paplay "$OUTPUT"
    fi
    
    rm -f "$OUTPUT"
fi
EOF

chmod +x "$TEST_SCRIPT"

# Print summary
echo ""
echo "=================================================="
echo "✅ PIPER TTS SETUP COMPLETE"
echo "=================================================="
echo ""
echo "Installed components:"
echo "  Piper binary: $BIN_DIR/piper"
echo "  Voice model: $VOICE_PATH"
echo "  Test script: $TEST_SCRIPT"
echo ""
echo "Configuration for RoboAI:"
echo "  model: \"$VOICE_MODEL\""
echo "  model_path: \"$ONNX_FILE\""
echo "  config_path: \"$JSON_FILE\""
echo "  play_command: \"aplay {filename}\""
echo ""
echo "Quick tests:"
echo "  # Test Piper directly"
echo "  echo 'Hello world' | piper --model $ONNX_FILE --output_file test.wav && aplay test.wav"
echo ""
echo "  # Use test script"
echo "  $TEST_SCRIPT Hello, this is a test"
echo ""
echo "  # Test with Python"
echo "  python3 -m src.connectors.adaptive_piper_tts"
echo ""

if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    echo -e "${YELLOW}⚠️  IMPORTANT: Run this to update PATH:${NC}"
    echo "  source ~/.bashrc"
    echo ""
fi

echo "=================================================="