#!/bin/bash

# Audio Diagnostics and Fixes for macOS

echo "==================================================================="
echo "Audio Device Diagnostics for RoboAI"
echo "==================================================================="

echo ""
echo "1. Checking for processes using audio devices..."
lsof | grep -i "coreaudio\|portaudio" | head -20

echo ""
echo "2. Available audio input devices:"
system_profiler SPAudioDataType | grep -A 5 "Input"

echo ""
echo "3. Current microphone permissions:"
tccutil reset Microphone || echo "   (requires Full Disk Access to check)"

echo ""
echo "==================================================================="
echo "RECOMMENDED FIXES:"
echo "==================================================================="
echo ""
echo "FIX 1: Close apps using microphone"
echo "   - Close Safari, Chrome, Zoom, Discord, etc."
echo "   - Check Activity Monitor for 'coreaudio' processes"
echo ""
echo "FIX 2: Reset audio system"
echo "   - Run: sudo killall coreaudiod"
echo "   - Wait 5 seconds, then try again"
echo ""
echo "FIX 3: Grant microphone permissions"
echo "   - System Settings > Privacy & Security > Microphone"
echo "   - Enable for Terminal or iTerm2"
echo ""
echo "FIX 4: Use built-in microphone instead"
echo "   - Edit config: set 'input_device: null' (auto-select)"
echo "   - Or disconnect iPhone microphone"
echo ""
echo "FIX 5: Reduce audio chunk duration (in config)"
echo "   - Change 'chunk_duration: 2' to 'chunk_duration: 1'"
echo "   - Reduces buffer conflicts"
echo ""
echo "==================================================================="
