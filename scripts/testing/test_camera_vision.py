#!/usr/bin/env python3
"""
Camera and Vision Test Script
Tests camera access and basic computer vision functionality
"""

import cv2
import sys
import numpy as np
import time

def test_camera_access():
    """Test if camera can be accessed and display basic info"""
    print("🎥 Testing Camera Access...")
    
    # Try different camera indices
    for camera_id in range(3):
        print(f"\n📷 Testing camera index {camera_id}...")
        
        try:
            cap = cv2.VideoCapture(camera_id)
            
            if cap.isOpened():
                # Get camera properties
                width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
                height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
                fps = cap.get(cv2.CAP_PROP_FPS)
                
                print(f"✅ Camera {camera_id} FOUND!")
                print(f"   Resolution: {int(width)}x{int(height)}")
                print(f"   FPS: {fps}")
                
                # Try to capture a frame
                ret, frame = cap.read()
                if ret:
                    print(f"   Frame shape: {frame.shape}")
                    print(f"   Frame data type: {frame.dtype}")
                    
                    # Save test image
                    cv2.imwrite(f"camera_{camera_id}_test.jpg", frame)
                    print(f"   ✅ Test image saved: camera_{camera_id}_test.jpg")
                else:
                    print(f"   ❌ Could not capture frame from camera {camera_id}")
                
                cap.release()
            else:
                print(f"   ❌ Camera {camera_id} not accessible")
                
        except Exception as e:
            print(f"   ❌ Error testing camera {camera_id}: {e}")
    
    cv2.destroyAllWindows()

def test_face_detection():
    """Test OpenCV face detection"""
    print("\n👤 Testing Face Detection...")
    
    try:
        # Load face cascade
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("❌ Cannot open camera for face detection test")
            return
        
        print("✅ Face detection ready!")
        print("📸 Capturing frame for face detection...")
        
        ret, frame = cap.read()
        if ret:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.1, 4)
            
            print(f"🔍 Detected {len(faces)} face(s)")
            
            # Draw rectangles around faces
            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
            
            # Save result
            cv2.imwrite("face_detection_test.jpg", frame)
            print("✅ Face detection result saved: face_detection_test.jpg")
        
        cap.release()
        
    except Exception as e:
        print(f"❌ Face detection error: {e}")

def test_vision_processing():
    """Test basic vision processing capabilities"""
    print("\n🔍 Testing Vision Processing...")
    
    try:
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("❌ Cannot open camera for vision processing test")
            return
        
        ret, frame = cap.read()
        if ret:
            # Test different processing operations
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 50, 150)
            
            # Color detection (simple example)
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            
            # Basic statistics
            mean_color = np.mean(frame, axis=(0, 1))
            
            print("✅ Vision processing tests:")
            print(f"   Frame size: {frame.shape}")
            print(f"   Mean color (BGR): {mean_color}")
            print(f"   Edge pixels detected: {np.sum(edges > 0)}")
            
            # Save processed images
            cv2.imwrite("vision_original.jpg", frame)
            cv2.imwrite("vision_edges.jpg", edges)
            print("✅ Vision processing images saved")
            
        cap.release()
        
    except Exception as e:
        print(f"❌ Vision processing error: {e}")

def main():
    """Run all camera and vision tests"""
    print("🚀 Camera and Vision Test Suite")
    print("=" * 40)
    
    # Check if OpenCV is available
    print(f"📦 OpenCV version: {cv2.__version__}")
    
    # Run tests
    test_camera_access()
    test_face_detection()
    test_vision_processing()
    
    print("\n🏁 Test Complete!")
    print("=" * 40)
    print("Check the generated image files to verify camera is working:")
    print("  - camera_*_test.jpg (raw camera captures)")
    print("  - face_detection_test.jpg (face detection results)")
    print("  - vision_*.jpg (processed images)")

if __name__ == "__main__":
    main()