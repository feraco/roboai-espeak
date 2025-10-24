# 🤖 G1 Audio System Auto-Fix Guide

## 🎯 Problem Solved

This guide implements a **complete auto-detection and repair system** for audio/video on the Unitree G1 robot running Ubuntu 22.04.

### What This Fixes:
- ✅ **Invalid sample rate errors** - Auto-detects supported rates
- ✅ **Device detection failures** - Finds best working microphone automatically  
- ✅ **PyAudio incompatibilities** - Tests all devices and falls back gracefully
- ✅ **Camera access issues** - Verifies camera availability before use
- ✅ **Piper TTS path issues** - Auto-locates voice files
- ✅ **Ollama integration** - Validates LLM and Vision models

## 🚀 Quick Start

### 1. Run Hardware Check
```bash
cd ~/roboai/roboai-espeak
python3 check_g1_hardware.py
```

This will:
- Detect all audio/video hardware
- Test sample rates for each device
- Find the best working configuration
- Validate Ollama and Piper TTS
- Print recommended settings

### 2. Run Auto-Diagnostic
```bash
python3 -m src.audio_system_fixer
```

Generates `audio_config.json` with complete hardware profile.

### 3. Test Individual Components

**Test Microphone:**
```bash
# The fixer will tell you which device works best
arecord -D hw:0,0 -f S16_LE -r 16000 -c 1 -d 3 test.wav
aplay test.wav
```

**Test Camera:**
```bash
python3 -c "
import cv2
cap = cv2.VideoCapture(0)
ret, frame = cap.read()
print(f'Camera OK: {ret}')
cap.release()
"
```

**Test Ollama:**
```bash
ollama list
ollama run llama3.1:8b "Hello"
```

**Test Ollama Vision:**
```bash
# Capture image first
python3 -c "import cv2; cv2.imwrite('test.jpg', cv2.VideoCapture(0).read()[1])"

# Test vision
ollama run llava-llama3 "What do you see?" test.jpg
```

## 📋 Architecture

### Auto-Detection System

```
check_g1_hardware.py
    └─> AudioSystemFixer
            ├─> Detect ALSA devices (arecord -l)
            ├─> Detect PyAudio devices
            ├─> Test sample rates for each device
            ├─> Score and rank devices
            ├─> Test camera (OpenCV)
            ├─> Validate Ollama + models
            └─> Locate Piper voices

AdaptiveASRInput
    ├─> Auto-select best device (or use config)
    ├─> Open stream with fallback rates
    ├─> Resample audio if needed
    └─> Robust error handling
```

### Device Selection Priority

1. **USB2.0 Microphone** (card 0, device 0)
   - Usually best quality
   - Typically supports 16000 Hz natively

2. **UVC Camera Microphone** (card 1, device 0)
   - Built-in camera mic
   - Fallback option

3. **NVIDIA Jetson Audio** (card 3, various devices)
   - Onboard audio
   - May require 48000 Hz sample rate

## 🔧 Configuration

### Automatic (Recommended)

Let the system auto-detect:

```json5
{
  "agent_inputs": [
    {
      "type": "LocalASRInput",
      "config": {
        "engine": "faster-whisper",
        "model_size": "tiny.en",
        "device": "cpu",
        "input_device": null,        // null = auto-detect
        "sample_rate": 16000,         // target rate for ASR
        // System will automatically find best device and resample
      }
    }
  ]
}
```

### Manual Override

Specify device if you know it works:

```json5
{
  "config": {
    "input_device": 0,           // PyAudio device index
    "sample_rate": 16000,        // Must be supported by device
    "hw_id": "hw:0,0"           // ALSA hardware ID
  }
}
```

## 🐛 Troubleshooting

### Error: "Invalid sample rate"

**Solution:** Run auto-detection:
```bash
python3 check_g1_hardware.py
```

It will tell you exactly which rates work.

### Error: "No audio input device found"

**Check devices:**
```bash
arecord -l
```

**Test manually:**
```bash
arecord -D hw:0,0 -f S16_LE -r 16000 -c 1 -d 3 test.wav
```

### Error: "Camera not accessible"

**Check permissions:**
```bash
ls -la /dev/video0
sudo chmod 666 /dev/video0
```

**Add user to video group:**
```bash
sudo usermod -a -G video $USER
# Logout and login again
```

### Error: "Ollama not responding"

**Start Ollama:**
```bash
# As service
sudo systemctl start ollama
sudo systemctl enable ollama

# Or manually
ollama serve &
```

**Check models:**
```bash
ollama list

# Install if missing
ollama pull llama3.1:8b
ollama pull llava-llama3
```

### Error: "Piper voices not found"

**Install Piper:**
```bash
# Download from GitHub
wget https://github.com/rhasspy/piper/releases/download/2023.11.14-2/piper_linux_x86_64.tar.gz
tar -xzf piper_linux_x86_64.tar.gz

# Download voices
mkdir -p ~/.local/share/piper/voices
cd ~/.local/share/piper/voices
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/ryan/medium/en_US-ryan-medium.onnx
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/ryan/medium/en_US-ryan-medium.onnx.json
```

## 🔍 Diagnostic Output Example

```
🤖 G1 HARDWARE DIAGNOSTIC REPORT
==============================================================

🎤 AUDIO INPUT DEVICES:
  ✅ Best device: USB2.0 Device
     Card: 0, Device: 0
     ALSA ID: hw:0,0
     PyAudio Index: 0
     Recommended rate: 16000 Hz
     Supported rates: [16000, 22050, 44100, 48000]

  📋 Alternative devices (2):
     • UVC Camera: hw:1,0 @ 16000Hz
     • NVIDIA Jetson Orin NX APE: hw:3,5 @ 48000Hz

📷 CAMERA:
  ✅ Camera available at /dev/video0
     Resolution: (720, 1280, 3)

👁️ OLLAMA VISION:
  ✅ Ollama Vision available
     Models: llama3.1:8b, llava-llama3

🔊 PIPER TTS:
  ✅ Piper voices found
     Path: /home/unitree/.local/share/piper/voices
     Available voices: 1

💡 CONFIGURATION RECOMMENDATIONS:

  ASR Configuration:
    input_device: 0
    sample_rate: 16000
    # Device: USB2.0 Device (hw:0,0)

  Camera Configuration:
    camera_index: 0
```

## 🛠️ Advanced Features

### Sample Rate Adaptation

The system automatically resamples audio:

```python
# Device captures at 48000 Hz
# System resamples to 16000 Hz for ASR
# Uses librosa if available, falls back to numpy interpolation
```

### Fallback Chain

If primary device fails:

```
1. Try specified device
2. Try default input device
3. Try all detected devices in priority order
4. Test multiple sample rates for each
5. Select best working combination
```

### Health Monitoring

```bash
# Check if audio is working
tail -f logs/roboai.log | grep "ASR"

# Should see:
# "Auto-selected device: USB2.0 Device"
# "Stream opened successfully at 16000 Hz"
# "Transcribed: hello world"
```

## 📊 Performance Tuning

### For Low Latency:
```json5
{
  "chunk_duration": 2.0,        // Shorter chunks
  "beam_size": 1,               // Faster decoding
  "vad_filter": true            // Skip silence
}
```

### For Accuracy:
```json5
{
  "chunk_duration": 4.0,        // Longer context
  "beam_size": 5,               // Better transcription  
  "model_size": "base.en"       // Larger model
}
```

### For Jetson Orin:
```json5
{
  "device": "cuda",             // Use GPU
  "compute_type": "float16",    // GPU acceleration
  "model_size": "small.en"      // Balance speed/accuracy
}
```

## 🚀 Deployment Checklist

- [ ] Run `check_g1_hardware.py` - all systems GREEN
- [ ] Test microphone recording/playback
- [ ] Verify camera with OpenCV
- [ ] Confirm Ollama responds
- [ ] Test Piper TTS output
- [ ] Run agent with `uv run src/run.py astra_vein_receptionist`
- [ ] Verify ASR transcription works
- [ ] Verify TTS audio plays
- [ ] Verify vision compliments work
- [ ] Set up auto-start with `./setup_g1_autostart.sh`

## 📚 Related Files

- `src/audio_system_fixer.py` - Core auto-detection engine
- `src/inputs/adaptive_asr_input.py` - Adaptive ASR with resampling
- `check_g1_hardware.py` - Startup hardware validation
- `test_g1_hardware.sh` - Interactive testing script
- `G1_HARDWARE_TESTING.md` - Manual testing commands

## 🎓 Technical Details

### ALSA vs PyAudio Device Mapping

ALSA uses `hw:CARD,DEVICE` format.
PyAudio uses sequential indices.

The fixer correlates them by:
1. Parsing `arecord -l` for ALSA devices
2. Enumerating PyAudio devices
3. Matching by name and testing each
4. Creating a mapping table

### Sample Rate Resampling

```python
# Using librosa (if available)
audio_resampled = librosa.resample(audio, orig_sr=48000, target_sr=16000)

# Fallback using numpy
ratio = 16000 / 48000
new_length = int(len(audio) * ratio)
audio_resampled = np.interp(
    np.linspace(0, len(audio), new_length),
    np.arange(len(audio)),
    audio
)
```

### Error Recovery

```python
try:
    # Try primary device at target rate
    stream = open_stream(device=0, rate=16000)
except:
    # Fallback to device native rate + resample
    stream = open_stream(device=0, rate=48000)
    audio = resample(audio, 48000, 16000)
```

## 📞 Support

If auto-detection fails:
1. Check `audio_config.json` for diagnostic output
2. Run manual tests from `G1_HARDWARE_TESTING.md`
3. Verify hardware with `arecord -l` and `v4l2-ctl`
4. Check logs for specific error messages

Common issues are usually:
- Wrong sample rate (fixed by auto-detection)
- Missing permissions (add to audio/video groups)
- Ollama not running (start service)
- Missing Piper voices (download from repo)