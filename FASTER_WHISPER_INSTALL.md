# Faster-Whisper Installation Guide

## Quick Install (Recommended)

### Method 1: Using pip (Simplest)

```bash
# Install faster-whisper
pip install faster-whisper

# Or with uv (if you're using it)
uv pip install faster-whisper
```

### Method 2: With CUDA GPU Support (For Better Performance)

```bash
# For NVIDIA GPUs with CUDA
pip install faster-whisper[cuda]

# Or
pip install faster-whisper nvidia-cublas-cu12 nvidia-cudnn-cu12
```

---

## Complete Installation Steps

### Ubuntu/Linux (Including G1)

```bash
# 1. Update system
sudo apt update

# 2. Install dependencies
sudo apt install -y python3-pip ffmpeg

# 3. Install faster-whisper
pip3 install faster-whisper

# 4. Test installation
python3 -c "from faster_whisper import WhisperModel; print('✓ Faster-whisper installed successfully!')"
```

### macOS

```bash
# 1. Install Homebrew (if not already installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 2. Install ffmpeg
brew install ffmpeg

# 3. Install faster-whisper
pip3 install faster-whisper

# 4. Test installation
python3 -c "from faster_whisper import WhisperModel; print('✓ Faster-whisper installed successfully!')"
```

---

## Download Models

Faster-whisper will automatically download models on first use, but you can pre-download:

```bash
# Python script to download models
python3 << 'EOF'
from faster_whisper import WhisperModel

# Download tiny.en model (fastest, English-only)
print("Downloading tiny.en model...")
model = WhisperModel("tiny.en", device="cpu", compute_type="int8")
print("✓ tiny.en model downloaded")

# Download base.en model (better accuracy)
print("Downloading base.en model...")
model = WhisperModel("base.en", device="cpu", compute_type="int8")
print("✓ base.en model downloaded")

print("\n✅ All models downloaded successfully!")
EOF
```

---

## Available Models

| Model | Size | Speed | Accuracy | RAM Usage |
|-------|------|-------|----------|-----------|
| `tiny.en` | 75 MB | Fastest | Basic | ~1 GB |
| `base.en` | 142 MB | Fast | Good | ~1 GB |
| `small.en` | 466 MB | Medium | Better | ~2 GB |
| `medium.en` | 1.5 GB | Slow | Great | ~5 GB |
| `large-v3` | 3.1 GB | Slowest | Best | ~10 GB |

**Recommended for G1:** `tiny.en` or `base.en` (good balance of speed and accuracy)

---

## Test Installation

### Quick Test

```bash
# Test if faster-whisper is installed
python3 -c "from faster_whisper import WhisperModel; print('✓ Installation successful!')"
```

### Full Test with Audio

```bash
# Create test script
cat > test_faster_whisper.py << 'EOF'
from faster_whisper import WhisperModel
import time

print("Loading Faster-Whisper model...")
model = WhisperModel("tiny.en", device="cpu", compute_type="int8")
print("✓ Model loaded successfully!")

# Test with a dummy audio file (you can replace with your own)
print("\nYou can now use faster-whisper for speech recognition!")
print("Example usage:")
print('  segments, info = model.transcribe("audio.wav")')
print('  for segment in segments:')
print('      print(f"[{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text}")')
EOF

python3 test_faster_whisper.py
```

---

## Integration with RoboAI

Your config already has faster-whisper configured:

```json5
{
  "type": "LocalASRInput",
  "config": {
    "engine": "faster-whisper",
    "model_size": "tiny.en",
    "device": "cpu",
    "compute_type": "int8",
    // ... other settings
  }
}
```

**No additional configuration needed!** Just make sure faster-whisper is installed.

---

## GPU Acceleration (Optional)

### For NVIDIA GPUs

```bash
# Install CUDA support
pip install faster-whisper[cuda]

# Or install specific CUDA dependencies
pip install nvidia-cublas-cu12 nvidia-cudnn-cu12
```

### Update config for GPU:

```json5
{
  "type": "LocalASRInput",
  "config": {
    "engine": "faster-whisper",
    "model_size": "base.en",
    "device": "cuda",           // Change from "cpu" to "cuda"
    "compute_type": "float16",  // Change from "int8" to "float16"
    // ...
  }
}
```

---

## Troubleshooting

### Error: "No module named 'faster_whisper'"

```bash
# Make sure you're using the right Python
which python3
python3 -m pip install faster-whisper

# Or if using conda/miniconda
conda install -c conda-forge faster-whisper
```

### Error: "Could not load library libcublas"

```bash
# Install CUDA dependencies
pip install nvidia-cublas-cu12 nvidia-cudnn-cu12

# Or use CPU instead
# Change device: "cuda" to device: "cpu" in config
```

### Error: "Model not found"

```bash
# Models download automatically on first use
# But you can pre-download:
python3 -c "from faster_whisper import WhisperModel; WhisperModel('tiny.en')"
```

### Slow Performance

```bash
# Use smaller model
# Change model_size from "base.en" to "tiny.en"

# Or use GPU if available
# Change device from "cpu" to "cuda"

# Reduce compute precision
# Change compute_type from "float32" to "int8"
```

---

## Verify Installation Checklist

Run these commands to verify everything is working:

```bash
# 1. Check Python version (should be 3.8+)
python3 --version

# 2. Check if faster-whisper is installed
python3 -c "import faster_whisper; print(f'✓ faster-whisper version: {faster_whisper.__version__}')"

# 3. Check if models can be loaded
python3 -c "from faster_whisper import WhisperModel; m = WhisperModel('tiny.en'); print('✓ Model loaded')"

# 4. Check ffmpeg (required for audio processing)
ffmpeg -version
```

All should complete without errors!

---

## Model Storage Location

Models are stored in:
- **Linux/G1:** `~/.cache/huggingface/hub/`
- **macOS:** `~/.cache/huggingface/hub/`
- **Windows:** `C:\Users\YourName\.cache\huggingface\hub\`

You can check disk space:
```bash
du -sh ~/.cache/huggingface/hub/
```

---

## Performance Tuning

### For G1 (Limited Resources)

```json5
{
  "engine": "faster-whisper",
  "model_size": "tiny.en",      // Smallest, fastest
  "device": "cpu",               // CPU mode
  "compute_type": "int8",        // Low precision for speed
  "beam_size": 1,                // Fastest decoding
  "vad_filter": true,            // Filter out silence
}
```

### For Desktop (More Resources)

```json5
{
  "engine": "faster-whisper",
  "model_size": "base.en",       // Better accuracy
  "device": "cuda",               // GPU acceleration
  "compute_type": "float16",      // Higher precision
  "beam_size": 5,                 // Better accuracy
  "vad_filter": true,
}
```

---

## Quick Commands Reference

```bash
# Install
pip install faster-whisper

# Install with GPU support
pip install faster-whisper[cuda]

# Test installation
python3 -c "from faster_whisper import WhisperModel; print('✓ OK')"

# Pre-download models
python3 -c "from faster_whisper import WhisperModel; WhisperModel('tiny.en')"

# Check version
python3 -c "import faster_whisper; print(faster_whisper.__version__)"

# Run your agent
uv run src/run.py astra_vein_receptionist
```

---

## All-in-One Installation Script

Save this as `install_faster_whisper.sh`:

```bash
#!/bin/bash
echo "Installing faster-whisper..."

# Install dependencies
pip3 install --upgrade pip
pip3 install faster-whisper

# Pre-download models
echo "Downloading models..."
python3 << 'EOF'
from faster_whisper import WhisperModel
print("Downloading tiny.en...")
WhisperModel("tiny.en", device="cpu", compute_type="int8")
print("✓ Done!")
EOF

# Test
python3 -c "from faster_whisper import WhisperModel; print('✅ Installation successful!')"
```

Run it:
```bash
chmod +x install_faster_whisper.sh
./install_faster_whisper.sh
```

---

**That's it!** Faster-whisper should now be ready to use with your Astra Vein receptionist agent. 🎤✨
