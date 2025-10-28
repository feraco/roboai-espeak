#!/bin/bash
# Test camera and microphone device conflicts on Jetson

echo "=========================================="
echo "Testing Camera/Microphone Device Conflicts"
echo "=========================================="

# Check all video devices
echo ""
echo "Video devices:"
ls -l /dev/video* 2>/dev/null || echo "No video devices found"

# Check all audio devices
echo ""
echo "Audio devices:"
arecord -l 2>/dev/null || echo "arecord not available"

# Check if camera and mic are same device
echo ""
echo "USB devices (audio/video):"
lsusb | grep -iE "camera|audio|video|webcam|microphone" || echo "No USB audio/video devices found"

# Test camera access while mic might be in use
echo ""
echo "Testing if camera can be opened..."
python3 << 'EOF'
import cv2
import sys

for idx in range(3):
    print(f"\nTrying camera index {idx}...")
    try:
        cap = cv2.VideoCapture(idx)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret:
                print(f"  ✓ Camera {idx} works! Resolution: {frame.shape[1]}x{frame.shape[0]}")
            else:
                print(f"  ✗ Camera {idx} opened but can't read frames")
            cap.release()
        else:
            print(f"  ✗ Camera {idx} cannot be opened")
    except Exception as e:
        print(f"  ✗ Error with camera {idx}: {e}")
EOF

echo ""
echo "=========================================="
echo "Recommendation:"
echo "=========================================="
echo "If you see 'Camera X cannot be opened' errors, it may be because:"
echo "  1. Another process (like ASR) is using the device"
echo "  2. Camera and microphone are the same USB device"
echo ""
echo "Solutions:"
echo "  A. Use separate camera and microphone devices"
echo "  B. Use config without vision: astra_vein_receptionist_no_vision"
echo "  C. Try different camera_index values (0, 1, 2)"
echo ""
