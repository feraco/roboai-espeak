#!/usr/bin/env python3
"""
Camera Test for Ubuntu G1
Tests camera availability and captures a test frame
"""

import sys
import cv2

def test_camera(camera_index=0):
    """Test camera at specified index"""
    print(f"\n🎥 Testing Camera {camera_index}")
    print("=" * 60)
    
    try:
        # Open camera
        print(f"Opening camera at index {camera_index}...")
        cap = cv2.VideoCapture(camera_index)
        
        if not cap.isOpened():
            print(f"❌ FAIL - Cannot open camera {camera_index}")
            return False
        
        # Get camera properties
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        print(f"✅ Camera opened successfully")
        print(f"   Resolution: {width}x{height}")
        print(f"   FPS: {fps}")
        
        # Try to read a frame
        print("Reading test frame...")
        ret, frame = cap.read()
        
        if not ret or frame is None:
            print("❌ FAIL - Cannot read frame from camera")
            cap.release()
            return False
        
        print(f"✅ Frame captured successfully")
        print(f"   Frame shape: {frame.shape}")
        
        # Save test image
        test_image = f"camera_{camera_index}_test.jpg"
        cv2.imwrite(test_image, frame)
        print(f"✅ Test image saved: {test_image}")
        
        cap.release()
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def main():
    print("\n" + "=" * 60)
    print("🎥 CAMERA HARDWARE TEST")
    print("=" * 60)
    
    # Test multiple camera indices
    cameras_found = []
    
    for i in range(5):  # Test indices 0-4
        if test_camera(i):
            cameras_found.append(i)
    
    print("\n" + "=" * 60)
    print("📋 SUMMARY")
    print("=" * 60)
    
    if cameras_found:
        print(f"✅ Found {len(cameras_found)} working camera(s): {cameras_found}")
        print(f"\n💡 Use camera index {cameras_found[0]} in your config:")
        print(f'   "camera_index": {cameras_found[0]}')
    else:
        print("❌ No working cameras found")
        print("\n🔧 Troubleshooting:")
        print("   1. Check if camera is plugged in:")
        print("      ls -la /dev/video*")
        print("   2. Check permissions:")
        print("      sudo chmod 666 /dev/video0")
        print("   3. Add user to video group:")
        print("      sudo usermod -a -G video $USER")
        print("      (logout and login again)")
        print("   4. Check if another process is using camera:")
        print("      sudo lsof /dev/video0")
    
    print("=" * 60)
    
    return 0 if cameras_found else 1

if __name__ == "__main__":
    sys.exit(main())
