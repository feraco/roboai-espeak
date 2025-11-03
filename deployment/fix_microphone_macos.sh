#!/bin/bash

echo "=========================================="
echo "macOS Microphone Troubleshooting"
echo "=========================================="
echo ""

echo "1. Checking microphone permissions..."
echo ""
echo "   Go to: System Settings > Privacy & Security > Microphone"
echo "   Make sure Terminal (or iTerm2) has microphone access enabled"
echo ""

echo "2. Available audio input devices:"
python3 -c "
import sounddevice as sd
print('')
devices = sd.query_devices()
for i, dev in enumerate(devices):
    if dev['max_input_channels'] > 0:
        print(f'   Device {i}: {dev[\"name\"]} (Inputs: {dev[\"max_input_channels\"]})')
        if 'default' in dev['name'].lower() or dev['hostapi'] == 0:
            print(f'      ⭐ This might be your built-in mic')
print('')
"

echo "3. Testing audio levels..."
echo ""
echo "   Run: python3 test_microphone.py"
echo "   You should see RMS levels > 0.01 when speaking"
echo ""

echo "4. Quick fixes to try:"
echo ""
echo "   A. Grant microphone permission:"
echo "      - Open System Settings"
echo "      - Go to Privacy & Security > Microphone"
echo "      - Enable 'Terminal' or 'iTerm2'"
echo "      - Restart terminal after enabling"
echo ""
echo "   B. Test with built-in microphone:"
echo "      - Disconnect iPhone/external microphones"
echo "      - Use Mac's built-in microphone instead"
echo ""
echo "   C. Check if another app is using it:"
echo "      - Close Zoom, Discord, Chrome, Safari"
echo "      - Run: sudo killall coreaudiod"
echo "      - Wait 5 seconds, then try again"
echo ""
echo "   D. Adjust input volume:"
echo "      - System Settings > Sound > Input"
echo "      - Turn 'Input volume' slider all the way up"
echo "      - Uncheck 'Use ambient noise reduction' if enabled"
echo ""

echo "5. After fixing, test with:"
echo "   python3 test_microphone.py"
echo ""
echo "=========================================="
