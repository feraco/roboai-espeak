#!/usr/bin/env python3
"""
List all available cameras and test them
"""

import cv2
import sys

def test_camera(index):
    """Test if camera at index works"""
    cap = cv2.VideoCapture(index)
    if cap.isOpened():
        ret, frame = cap.read()
        cap.release()
        if ret and frame is not None:
            return True, frame.shape
    return False, None

print("🎥 Scanning for cameras...\n")
print("=" * 60)

found_cameras = []

# Test camera indices 0-10
for i in range(10):
    works, shape = test_camera(i)
    if works:
        found_cameras.append((i, shape))
        print(f"✅ Camera {i}: WORKING - Resolution: {shape[1]}x{shape[0]}")
    else:
        # Don't spam for every non-existent camera
        pass

print("=" * 60)

if not found_cameras:
    print("\n❌ No cameras found!")
    print("\n💡 Troubleshooting:")
    print("   - Check if camera is plugged in")
    print("   - Check System Preferences → Privacy → Camera")
    print("   - Try restarting the camera or computer")
    sys.exit(1)

print(f"\n✅ Found {len(found_cameras)} camera(s)")

if len(found_cameras) == 1:
    cam_index = found_cameras[0][0]
    print(f"\n📌 Use camera_index: {cam_index} in your config")
else:
    print("\n📌 Multiple cameras found. Test each one:")
    for cam_index, shape in found_cameras:
        print(f"   - Camera {cam_index}: {shape[1]}x{shape[0]}")
    
print("\n🧪 Testing each camera (press any key to switch, 'q' to quit)...\n")

for cam_index, shape in found_cameras:
    print(f"Opening camera {cam_index}...")
    cap = cv2.VideoCapture(cam_index)
    
    if not cap.isOpened():
        print(f"   ❌ Failed to open camera {cam_index}")
        continue
    
    print(f"   ✅ Camera {cam_index} opened - press any key for next, 'q' to quit")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Add text overlay
        h, w = frame.shape[:2]
        text = f"Camera {cam_index} - {w}x{h}"
        cv2.putText(frame, text, (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(frame, "Press any key for next camera, 'q' to quit", (10, h-20),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        cv2.imshow(f'Camera Test - Index {cam_index}', frame)
        
        key = cv2.waitKey(1) & 0xFF
        if key != 255:  # Any key pressed
            if key == ord('q'):
                cap.release()
                cv2.destroyAllWindows()
                print("\n👋 Camera test complete!")
                sys.exit(0)
            break
    
    cap.release()
    cv2.destroyAllWindows()

print("\n✅ All cameras tested!")
print(f"\n📋 Summary:")
for cam_index, shape in found_cameras:
    print(f"   Camera {cam_index}: {shape[1]}x{shape[0]}")

print(f"\n💡 Update your config to use the camera you want:")
print(f'   "camera_index": {found_cameras[0][0]}  // or whichever camera works best')
