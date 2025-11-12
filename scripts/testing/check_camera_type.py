#!/usr/bin/env python3
"""
Check if depth camera has RGB stream
Many depth cameras (RealSense, etc.) have multiple streams
"""

import cv2

def check_camera_properties(index):
    """Check what formats/streams a camera supports"""
    print(f"\n{'='*60}")
    print(f"Checking Camera {index}")
    print('='*60)
    
    cap = cv2.VideoCapture(index)
    
    if not cap.isOpened():
        print(f"❌ Camera {index} could not be opened")
        return False
    
    # Get basic properties
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    fourcc = int(cap.get(cv2.CAP_PROP_FOURCC))
    format_code = int(cap.get(cv2.CAP_PROP_FORMAT))
    
    # Decode fourcc
    fourcc_str = "".join([chr((fourcc >> 8 * i) & 0xFF) for i in range(4)])
    
    print(f"Resolution: {width}x{height}")
    print(f"FPS: {fps}")
    print(f"FourCC: {fourcc_str}")
    print(f"Format code: {format_code}")
    
    # Try to read a frame
    ret, frame = cap.read()
    
    if ret and frame is not None:
        print(f"Frame shape: {frame.shape}")
        print(f"Frame dtype: {frame.dtype}")
        
        if len(frame.shape) == 3:
            channels = frame.shape[2]
            print(f"Channels: {channels}")
            if channels == 3:
                print("✅ This is RGB/BGR (color)")
            elif channels == 1:
                print("⚠️  This is grayscale")
        elif len(frame.shape) == 2:
            print("⚠️  This is grayscale/depth (2D)")
        
        # Check if it's actually IR/depth by looking at pixel values
        if len(frame.shape) == 2 or (len(frame.shape) == 3 and frame.shape[2] == 1):
            unique_values = len(set(frame.flatten()[:1000]))
            print(f"Sample unique pixel values: {unique_values}")
            if unique_values < 50:
                print("⚠️  Likely IR pattern/depth (limited unique values)")
            else:
                print("✅ Likely real image (many unique values)")
        
        # Show a preview
        print("\n🎥 Showing preview (press any key to continue)...")
        cv2.imshow(f'Camera {index} Preview', frame)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        
    else:
        print("❌ Could not read frame")
    
    cap.release()
    return True

# Check cameras 0 and 1
print("🔍 Depth Camera Analysis")
print("Checking for RGB streams...\n")

for i in range(2):
    check_camera_properties(i)

print("\n" + "="*60)
print("📋 SUMMARY")
print("="*60)
print("\nIf you see:")
print("  ✅ Channels: 3 + many unique values = RGB color camera (use this!)")
print("  ⚠️  Grayscale + limited values = IR/depth camera (don't use)")
print("\nDepth cameras like Intel RealSense have:")
print("  - RGB stream (color camera)")
print("  - Depth stream (distance data)")
print("  - IR stream (infrared pattern for depth)")
print("\nYou want the RGB stream for OCR badge reading!")
