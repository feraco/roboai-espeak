#!/usr/bin/env python3
"""
Access Intel RealSense RGB camera directly using pyrealsense2
This bypasses OpenCV and accesses all RealSense streams
"""

try:
    import pyrealsense2 as rs
    import numpy as np
    import cv2
    HAS_REALSENSE = True
except ImportError:
    HAS_REALSENSE = False
    print("❌ pyrealsense2 not installed")
    print("\n📦 Install with:")
    print("   pip install pyrealsense2")
    print("   or")
    print("   uv pip install pyrealsense2")
    exit(1)

print("🎥 Initializing Intel RealSense camera...")
print("Looking for RGB stream...\n")

# Create a pipeline
pipeline = rs.pipeline()
config = rs.config()

# Get device info
pipeline_wrapper = rs.pipeline_wrapper(pipeline)
pipeline_profile = config.resolve(pipeline_wrapper)
device = pipeline_profile.get_device()

print(f"Device: {device.get_info(rs.camera_info.name)}")
print(f"Serial: {device.get_info(rs.camera_info.serial_number)}")

# Find RGB stream
found_rgb = False
for s in device.sensors:
    print(f"\nSensor: {s.get_info(rs.camera_info.name)}")
    for profile in s.profiles:
        if profile.stream_type() == rs.stream.color:
            found_rgb = True
            vp = profile.as_video_stream_profile()
            print(f"  ✅ RGB Stream: {vp.width()}x{vp.height()} @ {vp.fps()}fps")

if not found_rgb:
    print("\n❌ No RGB stream found on this device")
    exit(1)

# Enable RGB stream (highest resolution available)
config.enable_stream(rs.stream.color, 1920, 1080, rs.format.bgr8, 30)

print("\n🚀 Starting RGB stream...")
try:
    pipeline.start(config)
except Exception as e:
    print(f"❌ Failed to start: {e}")
    print("\nTrying lower resolution...")
    config = rs.config()
    config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
    pipeline.start(config)

print("✅ RealSense RGB stream active!")
print("\n📺 Controls:")
print("   Press 'q' to quit")
print("   Press 's' to save snapshot")
print("   Press SPACE to test OCR\n")

snapshot_count = 0

# Import pytesseract for OCR test
try:
    import pytesseract
    HAS_OCR = True
except ImportError:
    HAS_OCR = False
    print("⚠️  pytesseract not available - OCR test disabled")

try:
    while True:
        # Wait for frames
        frames = pipeline.wait_for_frames()
        color_frame = frames.get_color_frame()
        
        if not color_frame:
            continue
        
        # Convert to numpy array
        color_image = np.asanyarray(color_frame.get_data())
        
        # Add overlay
        h, w = color_image.shape[:2]
        cv2.putText(color_image, f"RealSense RGB - {w}x{h}", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(color_image, "q=quit | s=snapshot | SPACE=OCR test", (10, h-20),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Draw badge area box
        cv2.rectangle(color_image, (w//4, h//4), (3*w//4, 3*h//4), (0, 255, 0), 2)
        cv2.putText(color_image, "Hold badge in green box", (w//4 + 10, h//4 + 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        cv2.imshow('RealSense RGB Camera', color_image)
        
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord('q'):
            print("\n👋 Closing camera...")
            break
        elif key == ord('s'):
            snapshot_count += 1
            filename = f"realsense_rgb_{snapshot_count}.jpg"
            cv2.imwrite(filename, color_image)
            print(f"📸 Saved: {filename}")
        elif key == ord(' ') and HAS_OCR:
            print("\n" + "="*50)
            print("🔍 Testing OCR on current frame...")
            
            # Extract center region
            gray = cv2.cvtColor(color_image, cv2.COLOR_BGR2GRAY)
            roi = gray[h//4:3*h//4, w//4:3*w//4]
            
            # Run OCR
            text = pytesseract.image_to_string(roi, config='--psm 6')
            print(f"\n📝 OCR Result:")
            print(text if text.strip() else "(no text detected)")
            print("="*50 + "\n")

finally:
    pipeline.stop()
    cv2.destroyAllWindows()
    print("✅ Camera stopped")
