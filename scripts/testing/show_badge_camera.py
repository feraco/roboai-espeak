#!/usr/bin/env python3
"""
Show what the badge reader camera sees and perform OCR
Displays the image and saves it for debugging
"""

import cv2
import numpy as np
import sys

# Try to import pytesseract
try:
    import pytesseract
    HAS_OCR = True
except ImportError:
    print("⚠️  pytesseract not installed - will show camera view only")
    HAS_OCR = False

def preprocess_for_ocr(frame):
    """Preprocess image for better OCR"""
    # Convert to grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # Use center region (where badges typically are)
    h, w = gray.shape
    roi = gray[h//4:3*h//4, w//4:3*w//4]
    
    # Enhance contrast
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(roi)
    
    # Bilateral filter to reduce noise
    filtered = cv2.bilateralFilter(enhanced, 9, 75, 75)
    
    # Adaptive threshold
    processed = cv2.adaptiveThreshold(
        filtered, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY, 11, 2
    )
    
    return processed

def main():
    print("🎥 Badge Reader Camera Test")
    print("=" * 50)
    
    # Try to open camera
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("❌ Failed to open camera 0")
        print("Trying camera 1...")
        cap = cv2.VideoCapture(1)
        
    if not cap.isOpened():
        print("❌ Failed to open any camera")
        sys.exit(1)
    
    print("✅ Camera opened successfully")
    print("")
    print("📝 Instructions:")
    print("- Hold a name badge or paper with name written on it")
    print("- Press SPACE to capture and analyze")
    print("- Press 'q' to quit")
    print("")
    
    frame_count = 0
    
    while True:
        ret, frame = cap.read()
        
        if not ret:
            print("❌ Failed to read frame")
            break
        
        # Draw center box (OCR region)
        h, w = frame.shape[:2]
        cv2.rectangle(frame, (w//4, h//4), (3*w//4, 3*h//4), (0, 255, 0), 2)
        cv2.putText(frame, "Hold badge in green box", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, "Press SPACE to analyze, 'q' to quit", (10, h-20), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Show the frame
        cv2.imshow('Badge Reader Camera View', frame)
        
        key = cv2.waitKey(1) & 0xFF
        
        # Press SPACE to capture and analyze
        if key == ord(' '):
            frame_count += 1
            filename = f"badge_capture_{frame_count}.jpg"
            cv2.imwrite(filename, frame)
            print(f"\n📸 Captured frame: {filename}")
            
            if HAS_OCR:
                print("🔍 Processing with OCR...")
                
                # Preprocess for OCR
                processed = preprocess_for_ocr(frame)
                
                # Save processed image
                processed_filename = f"badge_processed_{frame_count}.jpg"
                cv2.imwrite(processed_filename, processed)
                print(f"📝 Processed image: {processed_filename}")
                
                # Run OCR on both original and processed
                print("\n--- OCR on ORIGINAL frame ---")
                text_original = pytesseract.image_to_string(frame, config='--psm 6')
                print(text_original if text_original.strip() else "(no text detected)")
                
                print("\n--- OCR on PROCESSED frame ---")
                text_processed = pytesseract.image_to_string(processed, config='--psm 6')
                print(text_processed if text_processed.strip() else "(no text detected)")
                
                print("\n✅ Images saved for inspection")
            else:
                print("⚠️  Install pytesseract to see OCR results: uv pip install pytesseract")
            
            print("\nPress SPACE to capture another frame, 'q' to quit\n")
        
        # Press 'q' to quit
        elif key == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()
    print("\n👋 Camera test complete")

if __name__ == "__main__":
    main()
