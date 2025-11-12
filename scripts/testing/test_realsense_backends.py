#!/usr/bin/env python3
"""
Try to access all available camera streams from RealSense
Sometimes different backends expose different streams
"""

import cv2
import sys

def try_camera_with_backend(index, backend_name, backend_code):
    """Try opening camera with specific backend"""
    print(f"\n{'='*60}")
    print(f"Camera {index} with {backend_name} backend")
    print('='*60)
    
    try:
        cap = cv2.VideoCapture(index, backend_code)
        
        if not cap.isOpened():
            print(f"❌ Could not open")
            return False
        
        ret, frame = cap.read()
        if not ret or frame is None:
            print(f"❌ Could not read frame")
            cap.release()
            return False
        
        h, w = frame.shape[:2]
        channels = frame.shape[2] if len(frame.shape) == 3 else 1
        
        print(f"✅ Working: {w}x{h}, {channels} channels")
        
        # Show preview
        cv2.putText(frame, f"Cam {index} - {backend_name} - {w}x{h}", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.imshow(f'Camera {index} - {backend_name}', frame)
        
        print("Showing preview (press any key to continue)...")
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        
        cap.release()
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

print("🔍 Testing RealSense Camera Access Methods")
print("Trying different backends to find RGB stream...\n")

backends = [
    ("Default", cv2.CAP_ANY),
    ("AVFoundation (macOS)", cv2.CAP_AVFOUNDATION),
]

# Try cameras 0-5 with different backends
for cam_idx in range(6):
    found = False
    for backend_name, backend_code in backends:
        if try_camera_with_backend(cam_idx, backend_name, backend_code):
            found = True
            break
    
    if not found:
        print(f"\nCamera {cam_idx}: Not available")

print("\n" + "="*60)
print("📋 CONCLUSION")
print("="*60)
print("\nSince pyrealsense2 doesn't support macOS ARM64 + Python 3.12,")
print("you have two options:\n")
print("1. Use Camera 0 or 1 (whichever shows color)")
print("2. Use your Mac's built-in camera instead")
print("\nFor badge reading OCR, any camera with clear RGB will work!")
print("\nUpdate your config:")
print('  "camera_index": 0  // or 1, whichever showed color in the test')
