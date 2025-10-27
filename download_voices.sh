#!/bin/bash
# Download multi-language Piper TTS voice models
# This script downloads English, Spanish, and Russian voice models

set -e

echo "=========================================="
echo "Downloading Multi-Language Piper Voices"
echo "=========================================="
echo ""

# Create piper_voices directory
VOICE_DIR="piper_voices"
mkdir -p "$VOICE_DIR"
cd "$VOICE_DIR"

echo "Voice models will be saved to: $(pwd)"
echo ""

# Function to download and extract voice model
download_voice() {
    local voice_name="$1"
    local download_url="$2"
    local description="$3"
    
    echo "Downloading $description ($voice_name)..."
    
    if [ -f "${voice_name}.onnx" ]; then
        echo "✓ ${voice_name}.onnx already exists, skipping download"
        return
    fi
    
    # Download the voice model
    wget -q --show-progress "$download_url" -O "${voice_name}.tar.gz"
    
    # Extract the model
    tar -xzf "${voice_name}.tar.gz"
    
    # Clean up the tar file
    rm "${voice_name}.tar.gz"
    
    # Verify the model file exists
    if [ -f "${voice_name}.onnx" ]; then
        echo "✓ Successfully downloaded ${voice_name}.onnx"
    else
        echo "✗ Failed to extract ${voice_name}.onnx"
        return 1
    fi
    
    echo ""
}

# Download English voice (Ryan - male, medium quality)
download_voice "en_US-ryan-medium" \
    "https://github.com/rhasspy/piper/releases/download/v0.0.2/voice-en-us-ryan-medium.tar.gz" \
    "English (US) - Ryan (Male, Medium)"

# Download Spanish voice (Claudia - female, medium quality)
download_voice "es_ES-claudia-medium" \
    "https://github.com/rhasspy/piper/releases/download/v0.0.2/voice-es-es-claudia-medium.tar.gz" \
    "Spanish (Spain) - Claudia (Female, Medium)"

# Alternative Spanish voice if Claudia is not available
if [ ! -f "es_ES-claudia-medium.onnx" ]; then
    echo "Trying alternative Spanish voice..."
    download_voice "es_MX-ald-medium" \
        "https://github.com/rhasspy/piper/releases/download/v0.0.2/voice-es-mx-ald-medium.tar.gz" \
        "Spanish (Mexico) - Ald (Medium)"
fi

# Download Russian voice (Dmitri - male, medium quality)
download_voice "ru_RU-dmitri-medium" \
    "https://github.com/rhasspy/piper/releases/download/v0.0.2/voice-ru-ru-dmitri-medium.tar.gz" \
    "Russian - Dmitri (Male, Medium)"

# Alternative Russian voice if Dmitri is not available
if [ ! -f "ru_RU-dmitri-medium.onnx" ]; then
    echo "Trying alternative Russian voice..."
    download_voice "ru_RU-irina-medium" \
        "https://github.com/rhasspy/piper/releases/download/v0.0.2/voice-ru-ru-irina-medium.tar.gz" \
        "Russian - Irina (Female, Medium)"
fi

echo "=========================================="
echo "Download Summary"
echo "=========================================="
echo ""

# List all downloaded voice models
echo "Available voice models:"
for file in *.onnx; do
    if [ -f "$file" ]; then
        size=$(du -h "$file" | cut -f1)
        echo "  ✓ $file ($size)"
    fi
done

echo ""
echo "Voice model configuration:"
echo "  English:  $(find . -name 'en_US-*.onnx' | head -1 | sed 's|./||')"
echo "  Spanish:  $(find . -name 'es_*-*.onnx' | head -1 | sed 's|./||')"
echo "  Russian:  $(find . -name 'ru_RU-*.onnx' | head -1 | sed 's|./||')"

echo ""
echo "=========================================="
echo "Testing Voice Models"
echo "=========================================="
echo ""

# Test each voice if piper is available
if command -v piper &> /dev/null; then
    echo "Testing voice models with Piper..."
    
    # Test English
    english_model=$(find . -name 'en_US-*.onnx' | head -1)
    if [ -f "$english_model" ]; then
        echo "Testing English voice..."
        echo "Welcome to Astra Vein Treatment Center" | piper --model "$english_model" --output_file test_en.wav
        echo "✓ English test audio saved as test_en.wav"
    fi
    
    # Test Spanish
    spanish_model=$(find . -name 'es_*-*.onnx' | head -1)
    if [ -f "$spanish_model" ]; then
        echo "Testing Spanish voice..."
        echo "Bienvenido al Centro de Tratamiento de Venas Astra" | piper --model "$spanish_model" --output_file test_es.wav
        echo "✓ Spanish test audio saved as test_es.wav"
    fi
    
    # Test Russian
    russian_model=$(find . -name 'ru_RU-*.onnx' | head -1)
    if [ -f "$russian_model" ]; then
        echo "Testing Russian voice..."
        echo "Добро пожаловать в центр лечения вен Астра" | piper --model "$russian_model" --output_file test_ru.wav
        echo "✓ Russian test audio saved as test_ru.wav"
    fi
    
    echo ""
    echo "Test audio files created. You can play them with:"
    echo "  aplay test_en.wav  # English"
    echo "  aplay test_es.wav  # Spanish" 
    echo "  aplay test_ru.wav  # Russian"
    
else
    echo "⚠️  Piper not found. Install Piper to test voice models:"
    echo "   See JETSON_SETUP.md for installation instructions"
fi

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Multi-language voices are now available:"
echo "  📁 Location: $(pwd)"
echo "  🗣️  English: Available"
echo "  🗣️  Spanish: Available" 
echo "  🗣️  Russian: Available"
echo ""
echo "The agent will automatically detect and use these voices"
echo "based on the detected language of the user's speech."
echo ""
echo "Next steps:"
echo "1. Run the agent: uv run src/run.py astra_vein_receptionist"
echo "2. Test with different languages:"
echo "   - English: 'What are your office hours?'"
echo "   - Spanish: '¿Cuáles son sus horarios de oficina?'"
echo "   - Russian: 'Каковы ваши рабочие часы?'"