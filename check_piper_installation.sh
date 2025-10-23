#!/bin/bash

#############################################################################
# Piper TTS Installation Checker and Installer for Ubuntu
# Verifies Piper TTS is correctly installed and functional
#############################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

print_header() {
    echo ""
    print_message "$BLUE" "============================================"
    print_message "$BLUE" "$1"
    print_message "$BLUE" "============================================"
}

# Check if piper command exists
check_piper_command() {
    print_header "Checking Piper Command"
    
    if command -v piper &> /dev/null; then
        PIPER_PATH=$(which piper)
        print_message "$GREEN" "✓ Piper command found at: $PIPER_PATH"
        
        # Get version
        print_message "$YELLOW" "Getting Piper version..."
        piper --version 2>/dev/null || echo "Version info not available"
        return 0
    else
        print_message "$RED" "✗ Piper command not found"
        return 1
    fi
}

# Check Python piper-tts package
check_python_piper() {
    print_header "Checking Python Piper-TTS Package"
    
    if python3 -c "import piper" 2>/dev/null; then
        print_message "$GREEN" "✓ Python piper module found"
        python3 -c "import piper; print(f'Version: {piper.__version__}')" 2>/dev/null || echo "Version info not available"
        return 0
    else
        print_message "$RED" "✗ Python piper module not found"
        return 1
    fi
}

# Check for voice models
check_voice_models() {
    print_header "Checking Voice Models"
    
    # Common locations for Piper voice models
    VOICE_DIRS=(
        "$HOME/.local/share/piper-tts"
        "$HOME/.local/share/piper"
        "/usr/local/share/piper-tts"
        "/usr/share/piper-tts"
        "./voices"
    )
    
    FOUND_VOICES=false
    
    for dir in "${VOICE_DIRS[@]}"; do
        if [ -d "$dir" ]; then
            VOICE_COUNT=$(find "$dir" -name "*.onnx" 2>/dev/null | wc -l)
            if [ "$VOICE_COUNT" -gt 0 ]; then
                print_message "$GREEN" "✓ Found $VOICE_COUNT voice model(s) in: $dir"
                find "$dir" -name "*.onnx" -exec basename {} \; | head -5
                FOUND_VOICES=true
            fi
        fi
    done
    
    if [ "$FOUND_VOICES" = false ]; then
        print_message "$RED" "✗ No voice models found"
        print_message "$YELLOW" "Voice models need to be downloaded separately"
        return 1
    fi
    
    return 0
}

# Test Piper functionality
test_piper_tts() {
    print_header "Testing Piper TTS"
    
    # Try to generate a test audio file
    TEST_TEXT="Hello, this is a test of Piper text to speech."
    TEST_OUTPUT="/tmp/piper_test.wav"
    
    print_message "$YELLOW" "Attempting to generate test audio..."
    print_message "$YELLOW" "Text: '$TEST_TEXT'"
    
    # Try using piper command
    if command -v piper &> /dev/null; then
        # Look for a voice model
        VOICE_MODEL=$(find $HOME/.local/share/piper* /usr/share/piper* -name "*.onnx" 2>/dev/null | head -1)
        
        if [ -n "$VOICE_MODEL" ]; then
            print_message "$YELLOW" "Using voice model: $VOICE_MODEL"
            
            if echo "$TEST_TEXT" | piper --model "$VOICE_MODEL" --output_file "$TEST_OUTPUT" 2>/dev/null; then
                if [ -f "$TEST_OUTPUT" ]; then
                    FILE_SIZE=$(stat -f%z "$TEST_OUTPUT" 2>/dev/null || stat -c%s "$TEST_OUTPUT" 2>/dev/null)
                    print_message "$GREEN" "✓ Successfully generated test audio: $TEST_OUTPUT ($FILE_SIZE bytes)"
                    
                    # Try to play it (optional)
                    if command -v aplay &> /dev/null; then
                        print_message "$YELLOW" "Would you like to play the test audio? (y/n)"
                        read -r response
                        if [[ "$response" =~ ^[Yy]$ ]]; then
                            aplay "$TEST_OUTPUT"
                        fi
                    elif command -v paplay &> /dev/null; then
                        print_message "$YELLOW" "Would you like to play the test audio? (y/n)"
                        read -r response
                        if [[ "$response" =~ ^[Yy]$ ]]; then
                            paplay "$TEST_OUTPUT"
                        fi
                    fi
                    
                    rm -f "$TEST_OUTPUT"
                    return 0
                fi
            fi
        else
            print_message "$RED" "✗ No voice model found for testing"
            return 1
        fi
    fi
    
    print_message "$RED" "✗ Failed to generate test audio"
    return 1
}

# Check dependencies
check_dependencies() {
    print_header "Checking Dependencies"
    
    DEPS=("python3" "pip3" "ffmpeg")
    ALL_FOUND=true
    
    for dep in "${DEPS[@]}"; do
        if command -v "$dep" &> /dev/null; then
            print_message "$GREEN" "✓ $dep found"
        else
            print_message "$RED" "✗ $dep not found"
            ALL_FOUND=false
        fi
    done
    
    if [ "$ALL_FOUND" = true ]; then
        return 0
    else
        return 1
    fi
}

# Install Piper TTS
install_piper() {
    print_header "Installing Piper TTS"
    
    print_message "$YELLOW" "Installing piper-tts via pip..."
    
    # Install piper-tts
    pip3 install piper-tts --user || {
        print_message "$RED" "Failed to install piper-tts"
        return 1
    }
    
    print_message "$GREEN" "✓ piper-tts installed"
    
    # Download a default voice model
    print_message "$YELLOW" "Downloading default voice model (en_US-ryan-medium)..."
    
    VOICE_DIR="$HOME/.local/share/piper-tts/voices"
    mkdir -p "$VOICE_DIR"
    
    cd "$VOICE_DIR"
    
    # Download Ryan voice (medium quality)
    VOICE_URL="https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/ryan/medium/en_US-ryan-medium.onnx"
    CONFIG_URL="https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/ryan/medium/en_US-ryan-medium.onnx.json"
    
    wget -q --show-progress "$VOICE_URL" || {
        print_message "$RED" "Failed to download voice model"
        return 1
    }
    
    wget -q --show-progress "$CONFIG_URL" || {
        print_message "$RED" "Failed to download voice config"
        return 1
    }
    
    print_message "$GREEN" "✓ Voice model downloaded to: $VOICE_DIR"
    
    return 0
}

# Main menu
main_menu() {
    print_header "Piper TTS Installation Checker"
    
    echo ""
    print_message "$YELLOW" "What would you like to do?"
    echo "1) Check current installation"
    echo "2) Install/Reinstall Piper TTS"
    echo "3) Download additional voice models"
    echo "4) Run full diagnostic"
    echo "5) Exit"
    echo ""
    read -p "Enter choice [1-5]: " choice
    
    case $choice in
        1)
            check_piper_command
            check_python_piper
            check_voice_models
            ;;
        2)
            check_dependencies
            install_piper
            ;;
        3)
            download_voices_menu
            ;;
        4)
            run_full_diagnostic
            ;;
        5)
            exit 0
            ;;
        *)
            print_message "$RED" "Invalid choice"
            ;;
    esac
}

# Download voices menu
download_voices_menu() {
    print_header "Download Voice Models"
    
    VOICE_DIR="$HOME/.local/share/piper-tts/voices"
    mkdir -p "$VOICE_DIR"
    
    echo ""
    print_message "$YELLOW" "Available voices:"
    echo "1) en_US-ryan-medium (Male, American English)"
    echo "2) en_US-lessac-medium (Female, American English)"
    echo "3) en_GB-alan-medium (Male, British English)"
    echo "4) en_GB-southern_english_female-medium (Female, British)"
    echo "5) Back to main menu"
    echo ""
    read -p "Enter choice [1-5]: " voice_choice
    
    case $voice_choice in
        1)
            download_voice "en_US-ryan-medium" "en/en_US/ryan/medium"
            ;;
        2)
            download_voice "en_US-lessac-medium" "en/en_US/lessac/medium"
            ;;
        3)
            download_voice "en_GB-alan-medium" "en/en_GB/alan/medium"
            ;;
        4)
            download_voice "en_GB-southern_english_female-medium" "en/en_GB/southern_english_female/medium"
            ;;
        5)
            return
            ;;
    esac
}

# Download specific voice
download_voice() {
    local voice_name=$1
    local voice_path=$2
    
    VOICE_DIR="$HOME/.local/share/piper-tts/voices"
    cd "$VOICE_DIR"
    
    print_message "$YELLOW" "Downloading $voice_name..."
    
    VOICE_URL="https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/${voice_path}/${voice_name}.onnx"
    CONFIG_URL="https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/${voice_path}/${voice_name}.onnx.json"
    
    wget -q --show-progress "$VOICE_URL" && \
    wget -q --show-progress "$CONFIG_URL" && \
    print_message "$GREEN" "✓ Downloaded $voice_name" || \
    print_message "$RED" "✗ Failed to download $voice_name"
}

# Run full diagnostic
run_full_diagnostic() {
    print_header "Running Full Diagnostic"
    
    check_dependencies
    echo ""
    check_piper_command
    echo ""
    check_python_piper
    echo ""
    check_voice_models
    echo ""
    test_piper_tts
    
    print_header "Diagnostic Complete"
}

# Run main menu
main_menu
