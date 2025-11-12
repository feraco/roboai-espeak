#!/usr/bin/env python3
"""
RealSense RGB Badge Reader Test for Ubuntu/Jetson
Tests badge detection using Intel RealSense D435/D455 RGB stream
"""

import sys
import time

# Check for pyrealsense2
try:
    import pyrealsense2 as rs
    HAS_REALSENSE = True
except ImportError:
    HAS_REALSENSE = False
    print("❌ pyrealsense2 not installed")
    print("\n📦 Install on Ubuntu/Jetson:")
    print("   sudo apt-get install python3-pyrealsense2")
    print("   or")
    print("   pip install pyrealsense2")
    sys.exit(1)

# Check for OpenCV
try:
    import cv2
    HAS_OPENCV = True
except ImportError:
    HAS_OPENCV = False
    print("❌ opencv-python not installed")
    print("   pip install opencv-python")
    sys.exit(1)

# Check for EasyOCR
try:
    import easyocr
    HAS_EASYOCR = True
except ImportError:
    HAS_EASYOCR = False
    print("❌ easyocr not installed")
    print("   pip install easyocr")
    sys.exit(1)

import numpy as np

print("✅ All dependencies available")
print("\n🎥 Initializing Intel RealSense camera...")

# Create pipeline
pipeline = rs.pipeline()
config = rs.config()

# Get device info
pipeline_wrapper = rs.pipeline_wrapper(pipeline)
pipeline_profile = config.resolve(pipeline_wrapper)
device = pipeline_profile.get_device()

print(f"\n📷 Device: {device.get_info(rs.camera_info.name)}")
print(f"   Serial: {device.get_info(rs.camera_info.serial_number)}")
print(f"   Firmware: {device.get_info(rs.camera_info.firmware_version)}")

# Find RGB stream
found_rgb = False
for s in device.sensors:
    sensor_name = s.get_info(rs.camera_info.name)
    print(f"\n🔍 Sensor: {sensor_name}")
    for profile in s.profiles:
        if profile.stream_type() == rs.stream.color:
            vp = profile.as_video_stream_profile()
            print(f"   ✅ RGB: {vp.width()}x{vp.height()} @ {vp.fps()}fps")
            found_rgb = True

if not found_rgb:
    print("\n❌ No RGB stream found on this device")
    sys.exit(1)

# Check if any RealSense devices are connected
ctx = rs.context()
devices = ctx.query_devices()
if len(devices) == 0:
    print("\n❌ No RealSense devices found!")
    print("\n🔍 Troubleshooting:")
    print("   1. Check USB connection (use USB 3.0 port)")
    print("   2. Check permissions: lsusb | grep Intel")
    print("   3. Add udev rules:")
    print("      wget https://raw.githubusercontent.com/IntelRealSense/librealsense/master/config/99-realsense-libusb.rules")
    print("      sudo cp 99-realsense-libusb.rules /etc/udev/rules.d/")
    print("      sudo udevadm control --reload-rules && sudo udevadm trigger")
    print("   4. Reboot system")
    print("   5. Try: sudo realsense-viewer (if installed)")
    sys.exit(1)

print(f"✅ Found {len(devices)} RealSense device(s)")

# Enable RGB stream (try different resolutions)
rgb_resolution = None
resolutions_to_try = [
    (1920, 1080, 30),
    (1280, 720, 30),
    (640, 480, 30),
    (640, 480, 15),
]

for width, height, fps in resolutions_to_try:
    try:
        # Create fresh config for each attempt
        config = rs.config()
        config.enable_stream(rs.stream.color, width, height, rs.format.bgr8, fps)
        rgb_resolution = f"{width}x{height}@{fps}fps"
        print(f"✅ Will use: {rgb_resolution}")
        break
    except Exception as e:
        print(f"⚠️  {width}x{height}@{fps}fps not available: {e}")
        continue

if not rgb_resolution:
    print("\n❌ Could not find any compatible RGB stream resolution")
    print("\n🔍 Try checking available streams with:")
    print("   realsense-viewer")
    sys.exit(1)

print(f"\n🚀 Starting RGB stream at {rgb_resolution}...")
try:
    pipeline.start(config)
except RuntimeError as e:
    error_msg = str(e)
    print(f"❌ Failed to start pipeline: {error_msg}")
    
    if "couldn't resolve requests" in error_msg.lower():
        print("\n🔍 'Couldn't resolve requests' usually means:")
        print("   1. Camera is already in use by another application")
        print("      - Close realsense-viewer if running")
        print("      - Check: lsof | grep realsense")
        print("      - Check: ps aux | grep realsense")
        print("   2. Requested stream not supported by this camera")
        print("      - Try: rs-enumerate-devices -c")
        print("   3. USB connection issue")
        print("      - Use USB 3.0 port (blue port)")
        print("      - Try different cable")
        print("   4. Firmware issue")
        print("      - Update firmware with realsense-viewer")
    
    sys.exit(1)
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    print(f"   Error type: {type(e).__name__}")
    sys.exit(1)

print("✅ RealSense RGB stream active!")

# Load EasyOCR
print("\n🔄 Loading EasyOCR model (one-time, ~10 seconds)...")
reader = easyocr.Reader(['en'], gpu=True, verbose=False)  # GPU enabled for Jetson
print("✅ EasyOCR ready!")

print("\n" + "="*70)
print("🎯 BADGE READER TEST - RealSense RGB")
print("="*70)
print("\n📝 Instructions:")
print("  1. Write name on paper: JOHN SMITH (or your name)")
print("  2. Hold badge in CENTER of camera view (green box)")
print("  3. Press SPACE to test OCR")
print("  4. Press 'q' to quit")
print("\n💡 Tips:")
print("  - Use LARGE CAPITAL LETTERS (1+ inch tall)")
print("  - Dark marker on white paper")
print("  - Good lighting, no shadows")
print("  - Hold steady for 2-3 seconds")
print("="*70 + "\n")

frame_count = 0

try:
    while True:
        # Wait for frames
        frames = pipeline.wait_for_frames()
        color_frame = frames.get_color_frame()
        
        if not color_frame:
            continue
        
        # Convert to numpy array
        color_image = np.asanyarray(color_frame.get_data())
        
        # Draw UI overlay
        h, w = color_image.shape[:2]
        
        # Draw center box (badge detection area)
        cv2.rectangle(color_image, (w//4, h//4), (3*w//4, 3*h//4), (0, 255, 0), 3)
        cv2.putText(color_image, "Hold badge in GREEN BOX", (w//4 + 10, h//4 - 10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        
        # Status text
        cv2.putText(color_image, f"RealSense RGB - {w}x{h}", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(color_image, "SPACE=Test OCR | q=quit", (10, h-20),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Show frame
        cv2.imshow('RealSense Badge Reader Test', color_image)
        
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord('q'):
            print("\n👋 Exiting...")
            break
        
        elif key == ord(' '):
            frame_count += 1
            print("\n" + "="*70)
            print(f"🔍 TESTING BADGE DETECTION (Frame {frame_count})")
            print("="*70)
            
            # Save original frame
            filename = f"realsense_badge_{frame_count}.jpg"
            cv2.imwrite(filename, color_image)
            print(f"📸 Saved: {filename}")
            
            # Extract center region for OCR
            roi = color_image[h//4:3*h//4, w//4:3*w//4]
            
            # Run EasyOCR
            print("🤖 Running EasyOCR...")
            start_time = time.time()
            results = reader.readtext(roi)
            ocr_time = time.time() - start_time
            
            print(f"⏱️  OCR took {ocr_time:.2f}s")
            
            if not results:
                print("\n❌ No text detected")
                print("\n💡 Try:")
                print("   - LARGER letters (fill the green box)")
                print("   - DARKER pen/marker")
                print("   - Better lighting")
                print("   - Hold closer to camera")
                print("   - Use CAPITAL LETTERS")
            else:
                print(f"\n✅ Detected {len(results)} text region(s):")
                
                all_words = []
                for bbox, text, confidence in results:
                    print(f"   '{text}' (confidence: {confidence:.2f})")
                    if confidence >= 0.7:  # High confidence threshold
                        all_words.append(text)
                
                # Check if we have a valid name (2+ words)
                if len(all_words) >= 2:
                    full_name = " ".join(all_words)
                    print(f"\n🎉 VALID NAME DETECTED: {full_name}")
                    print(f"   ✅ This would trigger a greeting!")
                    print(f"   Agent would say: \"Hi {all_words[0]}, my name is Lex!\"")
                elif len(all_words) == 1:
                    print(f"\n⚠️  Only one word detected: '{all_words[0]}'")
                    print("   Need FIRST and LAST name (2+ words)")
                else:
                    print("\n⚠️  No high-confidence text detected")
            
            print("="*70 + "\n")

finally:
    pipeline.stop()
    cv2.destroyAllWindows()
    print("\n✅ Camera stopped")
    
print("\n📊 SUMMARY:")
print(f"   Total frames tested: {frame_count}")
print(f"   RealSense RGB working: ✅")
print(f"   EasyOCR working: ✅")
print("\n🚀 Ready to use badge_reader_easyocr in agent config!")
print("\nNext steps:")
print("  1. Update your agent config:")
print("     type: 'BadgeReaderEasyOCR'")
print("     camera_index: 0  (or test with list_cameras.py)")
print("  2. Run your agent!")
