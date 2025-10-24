#!/bin/bash

# G1 Hardware Testing Guide
# This script helps test camera, microphone, and speaker functionality on Unitree G1

echo "=================================================="
echo "🤖 G1 HARDWARE TESTING GUIDE"
echo "=================================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}This guide will test your G1's camera, microphone, and speakers${NC}"
echo -e "${BLUE}Follow each step and confirm functionality before proceeding${NC}"
echo ""

# Function to wait for user confirmation
wait_for_user() {
    echo -e "${YELLOW}Press Enter to continue or Ctrl+C to exit...${NC}"
    read
}

echo "=================================================="
echo "📋 STEP 1: CHECK AVAILABLE HARDWARE"
echo "=================================================="

echo -e "${BLUE}1.1 Checking available cameras...${NC}"
ls -la /dev/video* 2>/dev/null || echo "No video devices found"
echo ""

echo -e "${BLUE}1.2 Checking available audio devices...${NC}"
arecord -l
echo ""

echo -e "${BLUE}1.3 Checking speakers/audio output...${NC}"
aplay -l
echo ""

wait_for_user

echo "=================================================="
echo "🎥 STEP 2: TEST CAMERA"
echo "=================================================="

echo -e "${BLUE}2.1 Testing camera with v4l2-ctl (if available)...${NC}"
if command -v v4l2-ctl &> /dev/null; then
    echo "Camera capabilities for /dev/video0:"
    v4l2-ctl --device=/dev/video0 --list-formats-ext 2>/dev/null || echo "Camera not accessible or v4l2-ctl not available"
else
    echo "v4l2-ctl not installed. Install with: sudo apt install v4l-utils"
fi
echo ""

echo -e "${BLUE}2.2 Testing camera with Python OpenCV...${NC}"
cat > test_camera.py << 'EOF'
#!/usr/bin/env python3
import cv2
import sys

def test_camera(camera_index=0):
    print(f"Testing camera index {camera_index}...")
    
    try:
        cap = cv2.VideoCapture(camera_index)
        
        if not cap.isOpened():
            print(f"❌ Could not open camera {camera_index}")
            return False
            
        # Get camera properties
        width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        print(f"✅ Camera {camera_index} opened successfully")
        print(f"   Resolution: {width}x{height}")
        print(f"   FPS: {fps}")
        
        # Try to capture a frame
        ret, frame = cap.read()
        if ret:
            print(f"✅ Successfully captured frame from camera {camera_index}")
            print(f"   Frame shape: {frame.shape}")
        else:
            print(f"❌ Failed to capture frame from camera {camera_index}")
            return False
            
        cap.release()
        return True
        
    except Exception as e:
        print(f"❌ Error testing camera {camera_index}: {e}")
        return False

if __name__ == "__main__":
    # Test cameras 0-2
    working_cameras = []
    for i in range(3):
        if test_camera(i):
            working_cameras.append(i)
        print()
    
    print(f"Working cameras: {working_cameras}")
EOF

python3 test_camera.py
echo ""

wait_for_user

echo "=================================================="
echo "🎤 STEP 3: TEST MICROPHONES"
echo "=================================================="

echo -e "${BLUE}3.1 Testing USB microphone (card 0, device 0)...${NC}"
echo "Recording 5 seconds of audio from USB microphone..."
arecord -D hw:0,0 -f S16_LE -r 16000 -c 1 -d 5 test_usb_mic.wav 2>&1
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ USB microphone recording successful${NC}"
    echo "Playing back recording..."
    aplay test_usb_mic.wav 2>/dev/null
else
    echo -e "${RED}❌ USB microphone test failed${NC}"
fi
echo ""

echo -e "${BLUE}3.2 Testing camera microphone (card 1, device 0)...${NC}"
echo "Recording 5 seconds of audio from camera microphone..."
arecord -D hw:1,0 -f S16_LE -r 16000 -c 1 -d 5 test_camera_mic.wav 2>&1
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Camera microphone recording successful${NC}"
    echo "Playing back recording..."
    aplay test_camera_mic.wav 2>/dev/null
else
    echo -e "${RED}❌ Camera microphone test failed${NC}"
fi
echo ""

echo -e "${BLUE}3.3 Testing NVIDIA Jetson audio (card 3, device 5)...${NC}"
echo "Recording 5 seconds of audio from Jetson device..."
arecord -D hw:3,5 -f S16_LE -r 48000 -c 1 -d 5 test_jetson_mic.wav 2>&1
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Jetson microphone recording successful${NC}"
    echo "Playing back recording..."
    aplay test_jetson_mic.wav 2>/dev/null
else
    echo -e "${RED}❌ Jetson microphone test failed${NC}"
fi
echo ""

wait_for_user

echo "=================================================="
echo "🔊 STEP 4: TEST SPEAKERS/AUDIO OUTPUT"
echo "=================================================="

echo -e "${BLUE}4.1 Testing default audio output...${NC}"
echo "Playing test tone..."
speaker-test -t wav -c 2 -l 1 2>/dev/null || echo "speaker-test not available, trying aplay..."

echo -e "${BLUE}4.2 Creating and playing test audio file...${NC}"
# Create a simple beep
python3 -c "
import numpy as np
import wave
import struct

# Generate a 1-second 440Hz tone
sample_rate = 22050
duration = 1.0
frequency = 440.0

t = np.linspace(0, duration, int(sample_rate * duration))
audio = np.sin(2 * np.pi * frequency * t) * 0.3

# Convert to 16-bit integers
audio_16bit = (audio * 32767).astype(np.int16)

# Save as WAV
with wave.open('test_beep.wav', 'w') as wav_file:
    wav_file.setnchannels(1)
    wav_file.setsampwidth(2)
    wav_file.setframerate(sample_rate)
    wav_file.writeframes(audio_16bit.tobytes())

print('Created test beep')
"

echo "Playing test beep..."
aplay test_beep.wav
echo ""

wait_for_user

echo "=================================================="
echo "🧪 STEP 5: TEST PYAUDIO COMPATIBILITY"
echo "=================================================="

echo -e "${BLUE}5.1 Testing PyAudio device enumeration...${NC}"
cat > test_pyaudio.py << 'EOF'
#!/usr/bin/env python3
import pyaudio
import numpy as np

def test_pyaudio_devices():
    p = pyaudio.PyAudio()
    
    print("Available PyAudio devices:")
    print("-" * 50)
    
    device_count = p.get_device_count()
    working_devices = []
    
    for i in range(device_count):
        try:
            info = p.get_device_info_by_index(i)
            print(f"Device {i}: {info['name']}")
            print(f"  Max input channels: {info['maxInputChannels']}")
            print(f"  Max output channels: {info['maxOutputChannels']}")
            print(f"  Default sample rate: {info['defaultSampleRate']}")
            
            # Test if we can record from this device
            if info['maxInputChannels'] > 0:
                for sample_rate in [16000, 22050, 44100, 48000]:
                    try:
                        stream = p.open(
                            format=pyaudio.paInt16,
                            channels=1,
                            rate=sample_rate,
                            input=True,
                            input_device_index=i,
                            frames_per_buffer=1024
                        )
                        stream.close()
                        print(f"  ✅ Works at {sample_rate}Hz")
                        working_devices.append((i, sample_rate))
                        break
                    except Exception as e:
                        continue
                else:
                    print(f"  ❌ No compatible sample rates found")
            print()
        except Exception as e:
            print(f"Device {i}: Error - {e}")
            print()
    
    p.terminate()
    return working_devices

if __name__ == "__main__":
    working = test_pyaudio_devices()
    print("Working PyAudio devices:")
    for device_id, sample_rate in working:
        print(f"  Device {device_id} at {sample_rate}Hz")
EOF

python3 test_pyaudio.py
echo ""

wait_for_user

echo "=================================================="
echo "🔄 STEP 6: TEST FASTER-WHISPER"
echo "=================================================="

echo -e "${BLUE}6.1 Testing Faster-Whisper with recorded audio...${NC}"

# Test with the recorded audio files
for audio_file in test_usb_mic.wav test_camera_mic.wav test_jetson_mic.wav; do
    if [ -f "$audio_file" ]; then
        echo "Testing Faster-Whisper with $audio_file..."
        python3 -c "
import whisper
try:
    from faster_whisper import WhisperModel
    model = WhisperModel('tiny.en', device='cpu')
    segments, info = model.transcribe('$audio_file')
    print('Transcription:')
    for segment in segments:
        print(f'  {segment.text}')
except Exception as e:
    print(f'Error: {e}')
"
        echo ""
    fi
done

wait_for_user

echo "=================================================="
echo "🎵 STEP 7: TEST PIPER TTS"
echo "=================================================="

echo -e "${BLUE}7.1 Testing Piper TTS...${NC}"

# Test Piper TTS if available
if [ -f "piper-voices/en/en_US/ryan/medium/en_US-ryan-medium.onnx" ]; then
    echo "Testing Piper TTS..."
    echo "Hello, this is a test of the Piper text-to-speech system." | python3 -c "
import sys
import subprocess
import os

text = sys.stdin.read().strip()
model_path = 'piper-voices/en/en_US/ryan/medium/en_US-ryan-medium.onnx'
config_path = 'piper-voices/en/en_US/ryan/medium/en_US-ryan-medium.onnx.json'
output_file = 'test_piper_output.wav'

if os.path.exists(model_path):
    cmd = f'echo \"{text}\" | piper --model {model_path} --config {config_path} --output_file {output_file}'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        print('✅ Piper TTS successful')
        print('Playing TTS output...')
        subprocess.run(['aplay', output_file])
    else:
        print('❌ Piper TTS failed:', result.stderr)
else:
    print('❌ Piper model not found at expected location')
"
else
    echo "❌ Piper TTS model not found. Please run the setup script first."
fi

echo ""

wait_for_user

echo "=================================================="
echo "📊 STEP 8: CONFIGURATION RECOMMENDATIONS"
echo "=================================================="

echo -e "${BLUE}8.1 Analyzing test results...${NC}"

echo -e "${YELLOW}Based on the tests above, here are the recommended settings:${NC}"
echo ""

# Check which audio files were created successfully
echo "Audio device recommendations:"
if [ -f "test_usb_mic.wav" ]; then
    echo -e "${GREEN}✅ USB microphone (recommended): input_device: 0, sample_rate: 16000${NC}"
fi

if [ -f "test_camera_mic.wav" ]; then
    echo -e "${GREEN}✅ Camera microphone (alternative): input_device: 1, sample_rate: 16000${NC}"
fi

if [ -f "test_jetson_mic.wav" ]; then
    echo -e "${GREEN}✅ Jetson audio (alternative): input_device: 5, sample_rate: 48000${NC}"
fi

echo ""
echo "Camera recommendations:"
echo -e "${GREEN}✅ Use camera_index: 0 (primary camera)${NC}"

echo ""

wait_for_user

echo "=================================================="
echo "🚀 STEP 9: FINAL SYSTEM TEST"
echo "=================================================="

echo -e "${BLUE}9.1 Testing the actual RoboAI configuration...${NC}"
echo "This will run the agent with current config for 30 seconds..."
echo -e "${YELLOW}You should see camera feed, hear TTS, and be able to speak${NC}"

echo -e "${BLUE}Starting RoboAI agent test...${NC}"
echo "Press Ctrl+C to stop the test"

cd /Users/wwhs-research/Downloads/roboai-feature-multiple-agent-configurations
timeout 30 uv run src/run.py astra_vein_receptionist || echo "Test completed or interrupted"

echo ""
echo "=================================================="
echo "✅ TESTING COMPLETE"
echo "=================================================="

echo -e "${GREEN}Hardware testing finished!${NC}"
echo ""
echo "If all tests passed, your G1 is ready for deployment."
echo "If any tests failed, check the error messages and adjust your configuration."
echo ""
echo "Configuration file: config/astra_vein_receptionist.json5"
echo "Diagnostic script: ./fix_g1_audio.sh"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "1. Update config based on test results"
echo "2. Run: uv run src/run.py astra_vein_receptionist"
echo "3. Deploy with: ./setup_g1_autostart.sh"

# Cleanup test files
echo ""
echo "Cleaning up test files..."
rm -f test_*.wav test_camera.py test_pyaudio.py test_beep.wav

echo -e "${GREEN}Done! 🤖${NC}"