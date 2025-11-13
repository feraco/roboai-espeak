#!/bin/bash
# Pre-start checks for Astra Vein agent on Jetson
# Ensures RealSense camera 4 and USB audio devices are ready

MAX_WAIT=60
REALSENSE_INDEX=4

echo "=========================================="
echo "Astra Agent Pre-Start Checks"
echo "=========================================="

# Wait for RealSense camera
echo "⏳ Waiting for RealSense camera $REALSENSE_INDEX..."
for i in $(seq 1 $MAX_WAIT); do
    if v4l2-ctl --list-devices 2>/dev/null | grep -A 5 "RealSense" | grep "/dev/video$REALSENSE_INDEX" > /dev/null; then
        echo "✅ RealSense camera $REALSENSE_INDEX ready"
        break
    fi
    if [ $i -eq $MAX_WAIT ]; then
        echo "⚠️  Timeout waiting for RealSense camera"
    else
        sleep 1
    fi
done

# Wait for USB microphone
echo "⏳ Waiting for USB PnP Sound Device (microphone)..."
for i in $(seq 1 $MAX_WAIT); do
    if pactl list short sources 2>/dev/null | grep "USB_PnP_Sound_Device" > /dev/null; then
        echo "✅ USB microphone ready"
        break
    fi
    if [ $i -eq $MAX_WAIT ]; then
        echo "⚠️  Timeout waiting for USB microphone"
    else
        sleep 1
    fi
done

# Wait for USB speaker
echo "⏳ Waiting for USB 2.0 Speaker..."
for i in $(seq 1 $MAX_WAIT); do
    if pactl list short sinks 2>/dev/null | grep "USB_2.0_Speaker" > /dev/null; then
        echo "✅ USB speaker ready"
        break
    fi
    if [ $i -eq $MAX_WAIT ]; then
        echo "⚠️  Timeout waiting for USB speaker"
    else
        sleep 1
    fi
done

# Set PulseAudio defaults
echo "🔧 Setting audio defaults..."
MIC=$(pactl list short sources 2>/dev/null | grep "USB_PnP_Sound_Device" | awk '{print $2}' | head -n1)
SPEAKER=$(pactl list short sinks 2>/dev/null | grep "USB_2.0_Speaker" | awk '{print $2}' | head -n1)

if [ -n "$MIC" ]; then
    pactl set-default-source "$MIC"
    echo "✅ Default microphone: $MIC"
fi

if [ -n "$SPEAKER" ]; then
    pactl set-default-sink "$SPEAKER"
    echo "✅ Default speaker: $SPEAKER"
fi

# Remove stale device config to force re-detection
cd "$(dirname "$0")/.." || exit 1
rm -f device_config.yaml

echo "✅ Pre-start checks complete"
echo "=========================================="
