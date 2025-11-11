#!/bin/bash
# Download Piper TTS voice models for astra_vein_receptionist
# Run this on the Jetson after cloning the repo

set -e

VOICES_DIR="piper_voices"
PIPER_REPO="https://huggingface.co/rhasspy/piper-voices/resolve/main"

echo "📥 Downloading Piper TTS voices..."
echo "This will download ~180MB of voice models"
echo ""

mkdir -p "$VOICES_DIR"

# Essential voices for astra_vein_receptionist (English, Spanish, Russian)
VOICES=(
    "en/en_US/kristin/medium/en_US-kristin-medium"
    "es/es_ES/davefx/medium/es_ES-davefx-medium"
    "ru/ru_RU/dmitri/medium/ru_RU-dmitri-medium"
)

download_voice() {
    local voice_path=$1
    local voice_name=$(basename "$voice_path")
    
    echo "📦 Downloading $voice_name..."
    
    # Download .onnx model
    if [ ! -f "$VOICES_DIR/${voice_name}.onnx" ]; then
        curl -L -o "$VOICES_DIR/${voice_name}.onnx" \
            "$PIPER_REPO/$voice_path.onnx"
        echo "  ✅ Downloaded ${voice_name}.onnx"
    else
        echo "  ⏭️  ${voice_name}.onnx already exists"
    fi
    
    # Download .onnx.json config
    if [ ! -f "$VOICES_DIR/${voice_name}.onnx.json" ]; then
        curl -L -o "$VOICES_DIR/${voice_name}.onnx.json" \
            "$PIPER_REPO/$voice_path.onnx.json"
        echo "  ✅ Downloaded ${voice_name}.onnx.json"
    else
        echo "  ⏭️  ${voice_name}.onnx.json already exists"
    fi
    
    echo ""
}

# Download all essential voices
for voice in "${VOICES[@]}"; do
    download_voice "$voice"
done

echo "✅ All essential voices downloaded!"
echo ""
echo "📊 Voice files in $VOICES_DIR:"
ls -lh "$VOICES_DIR"/*.onnx | awk '{print "  " $9 " (" $5 ")"}'
echo ""
echo "🎤 You can now run: uv run src/run.py astra_vein_receptionist"
