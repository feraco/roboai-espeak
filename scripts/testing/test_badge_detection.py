#!/usr/bin/env python3
"""
Badge Detection Test Script
Test the camera and OCR functionality before integrating with the bot
"""

import cv2
import pytesseract
import time
import numpy as np

def test_camera():
    """Test camera functionality"""
    print("🎥 Testing camera...")
    
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Cannot open camera")
        return False
    
    # Capture a few frames
    for i in range(5):
        ret, frame = cap.read()
        if ret:
            print(f"✅ Frame {i+1} captured: {frame.shape}")
        else:
            print(f"❌ Failed to capture frame {i+1}")
    
    cap.release()
    return True

def test_ocr():
    """Test OCR functionality"""
    print("\n🔍 Testing OCR...")
    
    try:
        # Create a simple test image with text
        from PIL import Image, ImageDraw, ImageFont
        
        # Create a white image with text
        img = Image.new('RGB', (200, 50), color='white')
        draw = ImageDraw.Draw(img)
        draw.text((10, 10), "John Smith", fill='black')
        
        # Convert PIL to numpy array for OpenCV
        img_array = np.array(img)
        
        # Test OCR
        test_text = pytesseract.image_to_string(img_array)
        print(f"✅ OCR working: '{test_text.strip()}'")
        return True
    except Exception as e:
        print(f"❌ OCR error: {e}")
        return False

def test_badge_detection_realtime():
    """Test real-time badge detection"""
    print("\n👋 Testing real-time badge detection (press 'q' to quit)...")
    
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Cannot open camera for real-time test")
        return
    
    # Set camera properties
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    last_detection = time.time()
    detection_interval = 3.0  # Check every 3 seconds
    
    print("\n📸 Camera feed open. Hold up a badge or paper with a name written on it.")
    print("Press 'q' in the camera window to quit.\n")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Show the frame
        cv2.imshow('Badge Detection Test', frame)
        
        # Perform OCR detection every few seconds
        current_time = time.time()
        if current_time - last_detection > detection_interval:
            try:
                # Convert to grayscale for better OCR
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                
                # Apply threshold for better text detection
                _, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
                
                # Extract text
                text = pytesseract.image_to_string(thresh, config='--psm 6')
                
                if text.strip():
                    print(f"📝 Detected text: {text.strip()}")
                    
                    # Simple name detection (basic version)
                    import re
                    name_matches = re.findall(r'\b([A-Z][a-z]+)\s+([A-Z][a-z]+)\b', text)
                    if name_matches:
                        for first, last in name_matches:
                            full_name = f"{first} {last}"
                            print(f"👤 Potential name detected: {full_name}")
                
                last_detection = current_time
                
            except Exception as e:
                print(f"🚨 Detection error: {e}")
        
        # Check for quit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()

def main():
    """Run all tests"""
    print("🚀 Starting Badge Detection Tests...\n")
    
    # Test individual components
    camera_ok = test_camera()
    ocr_ok = test_ocr()
    
    if camera_ok and ocr_ok:
        print("\n✅ All components working!")
        print("\nStarting real-time test...")
        test_badge_detection_realtime()
    else:
        print("\n❌ Some components failed. Please check your setup:")
        if not camera_ok:
            print("  - Camera not working")
        if not ocr_ok:
            print("  - OCR not working (check tesseract installation)")
            print("\n💡 Install tesseract:")
            print("  macOS: brew install tesseract")
            print("  Ubuntu: sudo apt install tesseract-ocr")

if __name__ == "__main__":
    main()
