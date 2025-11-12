#!/usr/bin/env python3
"""
Simple RealSense Badge Reader Test (Auto-detect streams)
Uses default configuration - no manual stream setup
"""

import sys
import time

try:
    import pyrealsense2 as rs
except ImportError:
    print("❌ pyrealsense2 not installed")
    print("   sudo apt-get install python3-pyrealsense2")
    sys.exit(1)

try:
    import cv2
except ImportError:
    print("❌ opencv-python not installed")
    sys.exit(1)

try:
    import easyocr
except ImportError:
    print("❌ easyocr not installed")
    sys.exit(1)

import numpy as np

print("✅ All dependencies available\n")

# Check for RealSense devices
ctx = rs.context()
devices = ctx.query_devices()

if len(devices) == 0:
    print("❌ No RealSense devices found!")
    print("\n🔍 Troubleshooting:")
    print("   1. Check USB connection (use USB 3.0 blue port)")
    print("   2. Check: lsusb | grep Intel")
    print("   3. Install udev rules:")
    print("      sudo apt-get install librealsense2-utils")
    print("   4. Test with: realsense-viewer")
    sys.exit(1)

print(f"✅ Found {len(devices)} RealSense device(s)\n")

for dev in devices:
    print(f"📷 Device: {dev.get_info(rs.camera_info.name)}")
    print(f"   Serial: {dev.get_info(rs.camera_info.serial_number)}")
    print(f"   Firmware: {dev.get_info(rs.camera_info.firmware_version)}")

print("\n🚀 Starting pipeline with default configuration...")

# Use SIMPLEST possible configuration - let RealSense auto-detect
pipeline = rs.pipeline()

try:
    # Start with default config (auto-detects best available streams)
    profile = pipeline.start()
    
    # Get stream info
    streams = profile.get_streams()
    print(f"\n✅ Pipeline started with {len(streams)} stream(s):")
    for stream in streams:
        if stream.stream_type() == rs.stream.color:
            vp = stream.as_video_stream_profile()
            print(f"   RGB: {vp.width()}x{vp.height()} @ {vp.fps()}fps")
            
except RuntimeError as e:
    print(f"\n❌ Failed to start: {e}")
    print("\n🔍 Troubleshooting:")
    print("   1. Close any other apps using the camera:")
    print("      pkill realsense-viewer")
    print("      lsof | grep realsense")
    print("   2. Check USB connection (must be USB 3.0)")
    print("   3. Update firmware: realsense-viewer")
    print("   4. Reboot system")
    sys.exit(1)

# Load EasyOCR
print("\n🔄 Loading EasyOCR model...")
try:
    reader = easyocr.Reader(['en'], gpu=True, verbose=False)
    print("✅ EasyOCR ready (GPU enabled)!")
except Exception as e:
    print(f"⚠️  GPU failed, trying CPU: {e}")
    reader = easyocr.Reader(['en'], gpu=False, verbose=False)
    print("✅ EasyOCR ready (CPU mode)!")

print("\n" + "="*70)
print("🎯 BADGE READER TEST - RealSense Simple Mode")
print("="*70)
print("\n📝 Instructions:")
print("  1. Write name: JOHN SMITH (both first and last)")
print("  2. Hold badge in CENTER of screen (green box)")
print("  3. Press SPACE to test OCR")
print("  4. Press 'q' to quit")
print("\n💡 Tips:")
print("  - LARGE CAPITAL LETTERS (1+ inch tall)")
print("  - Dark marker on white paper")
print("  - Good lighting, no shadows")
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
        
        # Get dimensions
        h, w = color_image.shape[:2]
        
        # Draw center box (badge area)
        box_margin = 4
        cv2.rectangle(color_image, 
                     (w//box_margin, h//box_margin), 
                     ((box_margin-1)*w//box_margin, (box_margin-1)*h//box_margin), 
                     (0, 255, 0), 3)
        
        # Status overlay
        cv2.putText(color_image, f"RealSense RGB - {w}x{h}", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(color_image, "SPACE=Test OCR | q=Quit", (10, h-20),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Show frame
        cv2.imshow('RealSense Badge Test', color_image)
        
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord('q'):
            print("\n👋 Exiting...")
            break
        
        elif key == ord(' '):
            frame_count += 1
            print("\n" + "="*70)
            print(f"🔍 TEST {frame_count}")
            print("="*70)
            
            # Save frame
            filename = f"badge_test_{frame_count}.jpg"
            cv2.imwrite(filename, color_image)
            print(f"📸 Saved: {filename}")
            
            # Extract center region
            roi = color_image[h//4:3*h//4, w//4:3*w//4]
            
            # Run EasyOCR
            print("🤖 Running EasyOCR...")
            start = time.time()
            results = reader.readtext(roi)
            elapsed = time.time() - start
            
            print(f"⏱️  Took {elapsed:.2f}s")
            
            if not results:
                print("\n❌ No text detected")
                print("💡 Try: LARGER letters, DARKER pen, better lighting")
            else:
                print(f"\n✅ Detected {len(results)} text region(s):")
                
                high_conf_words = []
                for bbox, text, conf in results:
                    print(f"   '{text}' ({conf:.2f})")
                    if conf >= 0.7:
                        high_conf_words.append(text)
                
                if len(high_conf_words) >= 2:
                    name = " ".join(high_conf_words)
                    print(f"\n🎉 VALID NAME: {name}")
                    print(f"   ✅ Would trigger greeting!")
                elif len(high_conf_words) == 1:
                    print(f"\n⚠️  Only 1 word: '{high_conf_words[0]}'")
                    print("   Need FIRST + LAST name")
                else:
                    print("\n⚠️  No high-confidence text (need 70%+)")
            
            print("="*70)

finally:
    pipeline.stop()
    cv2.destroyAllWindows()
    print("\n✅ Camera stopped")

print(f"\n📊 Total tests: {frame_count}")
print("✅ RealSense working!")
print("\n🚀 Ready for agent configuration!")
