# G1 Hardware Testing Quick Reference

## 🚀 Quick Testing Commands

### Run Full Hardware Test
```bash
./test_g1_hardware.sh
```

### Manual Testing Commands

#### 1. Check Available Devices
```bash
# List cameras
ls -la /dev/video*

# List audio input devices  
arecord -l

# List audio output devices
aplay -l
```

#### 2. Test Cameras
```bash
# Test camera with v4l2 (install if needed: sudo apt install v4l-utils)
v4l2-ctl --device=/dev/video0 --list-formats-ext

# Quick Python camera test
python3 -c "
import cv2
cap = cv2.VideoCapture(0)
if cap.isOpened():
    ret, frame = cap.read()
    print(f'Camera working: {ret}, Frame shape: {frame.shape if ret else None}')
    cap.release()
else:
    print('Camera failed to open')
"
```

#### 3. Test Microphones
```bash
# Test USB microphone (card 0, device 0)
arecord -D hw:0,0 -f S16_LE -r 16000 -c 1 -d 3 test_usb.wav
aplay test_usb.wav

# Test camera microphone (card 1, device 0)  
arecord -D hw:1,0 -f S16_LE -r 16000 -c 1 -d 3 test_camera.wav
aplay test_camera.wav

# Test Jetson audio (card 3, device 5)
arecord -D hw:3,5 -f S16_LE -r 48000 -c 1 -d 3 test_jetson.wav
aplay test_jetson.wav
```

#### 4. Test Speakers
```bash
# Test with speaker-test
speaker-test -t wav -c 2 -l 1

# Create and play test tone
python3 -c "
import numpy as np, wave
sr, dur, freq = 22050, 1.0, 440.0
t = np.linspace(0, dur, int(sr * dur))
audio = (np.sin(2*np.pi*freq*t) * 0.3 * 32767).astype(np.int16)
with wave.open('beep.wav', 'w') as f:
    f.setnchannels(1); f.setsampwidth(2); f.setframerate(sr)
    f.writeframes(audio.tobytes())
"
aplay beep.wav
```

#### 5. Test PyAudio Compatibility
```bash
python3 -c "
import pyaudio
p = pyaudio.PyAudio()
for i in range(p.get_device_count()):
    info = p.get_device_info_by_index(i)
    if info['maxInputChannels'] > 0:
        print(f'Device {i}: {info[\"name\"]} - Max SR: {info[\"defaultSampleRate\"]}')
        for rate in [16000, 22050, 44100, 48000]:
            try:
                s = p.open(format=pyaudio.paInt16, channels=1, rate=rate, input=True, input_device_index=i, frames_per_buffer=1024)
                s.close()
                print(f'  ✅ {rate}Hz works')
                break
            except: continue
p.terminate()
"
```

#### 6. Test Faster-Whisper
```bash
python3 -c "
from faster_whisper import WhisperModel
model = WhisperModel('tiny.en', device='cpu')
# Record test audio first, then:
segments, info = model.transcribe('test_audio.wav')
for segment in segments:
    print(segment.text)
"
```

#### 7. Test Piper TTS
```bash
# If piper is installed globally
echo 'Hello world' | piper --model piper-voices/en/en_US/ryan/medium/en_US-ryan-medium.onnx --output_file test_tts.wav
aplay test_tts.wav
```

## 📋 Configuration Based on Results

### USB Microphone Working (Recommended)
```json5
"input_device": 0,
"sample_rate": 16000,
"camera_index": 0
```

### Camera Microphone Working
```json5
"input_device": 1,
"sample_rate": 16000, 
"camera_index": 0
```

### Jetson Audio Working  
```json5
"input_device": 5,
"sample_rate": 48000,
"camera_index": 0
```

## 🔧 Troubleshooting

### Audio Issues
- **Sample rate errors**: Try different rates (16000, 22050, 44100, 48000)
- **Device not found**: Check `arecord -l` and use correct device number
- **Permission denied**: Add user to audio group: `sudo usermod -a -G audio $USER`

### Camera Issues
- **No /dev/video***: Check USB connections, try `lsusb` to see devices
- **Permission denied**: Check camera permissions: `ls -la /dev/video*`
- **OpenCV fails**: Install: `pip install opencv-python`

### Dependencies
```bash
# Install required packages
sudo apt update
sudo apt install -y alsa-utils v4l-utils python3-pip
pip install opencv-python pyaudio faster-whisper numpy
```

## 🚀 Final Test
```bash
# Run the actual agent
cd ~/roboai/roboai-espeak  
uv run src/run.py astra_vein_receptionist
```

Expected behavior:
- ✅ Camera feed appears
- ✅ "Hello and welcome..." greeting plays
- ✅ Speech recognition responds to voice
- ✅ Arm movements work (if G1 connected)
- ✅ No audio errors in logs