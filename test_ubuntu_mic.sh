#!/bin/bash
# Quick Ubuntu microphone test
# Run this to find your working microphone device

echo "======================================================================"
echo "🎤 UBUNTU MICROPHONE QUICK TEST"
echo "======================================================================"

echo ""
echo "1️⃣  ALSA INPUT DEVICES:"
echo "----------------------------------------------------------------------"
arecord -l

echo ""
echo "2️⃣  TESTING DEFAULT DEVICE:"
echo "----------------------------------------------------------------------"
echo "Recording 3 seconds from 'default' device..."
arecord -D default -f S16_LE -r 16000 -c 1 -d 3 /tmp/test_default.wav 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Default device works!"
    echo "Playing back..."
    aplay /tmp/test_default.wav
else
    echo "❌ Default device failed"
fi

echo ""
echo "3️⃣  TESTING hw:0,0:"
echo "----------------------------------------------------------------------"
echo "Recording 3 seconds from hw:0,0..."
arecord -D hw:0,0 -f S16_LE -r 16000 -c 1 -d 3 /tmp/test_hw00.wav 2>&1
if [ $? -eq 0 ]; then
    echo "✅ hw:0,0 works!"
    echo "Playing back..."
    aplay /tmp/test_hw00.wav
else
    echo "❌ hw:0,0 failed"
fi

echo ""
echo "4️⃣  TESTING hw:1,0:"
echo "----------------------------------------------------------------------"
echo "Recording 3 seconds from hw:1,0..."
arecord -D hw:1,0 -f S16_LE -r 16000 -c 1 -d 3 /tmp/test_hw10.wav 2>&1
if [ $? -eq 0 ]; then
    echo "✅ hw:1,0 works!"
    echo "Playing back..."
    aplay /tmp/test_hw10.wav
else
    echo "❌ hw:1,0 failed"
fi

echo ""
echo "======================================================================"
echo "📋 NEXT STEPS:"
echo "======================================================================"
echo "Find the device that worked (✅) above, then:"
echo ""
echo "1. Run the full diagnostic:"
echo "   python3 diagnose_ubuntu_audio.py"
echo ""
echo "2. Use the working device number in your config:"
echo "   Edit config/astra_vein_receptionist.json5"
echo "   Set: \"input_device\": 0  (or 1, whichever worked)"
echo ""
echo "3. Make sure you're in the audio group:"
echo "   sudo usermod -a -G audio \$USER"
echo "   Then logout and login again"
echo "======================================================================"
