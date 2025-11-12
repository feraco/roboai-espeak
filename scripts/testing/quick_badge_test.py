#!/usr/bin/env python3
"""Quick test to see what the badge reader OCR detects"""

import cv2
import pytesseract
import numpy as np
import time

def preprocess(frame):
    """Same preprocessing as badge reader"""
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape
    roi = gray[h//4:3*h//4, w//4:3*w//4]
    
    # High quality preprocessing
    if roi.shape[0] < 150 or roi.shape[1] < 150:
        scale = max(150 / roi.shape[0], 150 / roi.shape[1])
        new_w = int(roi.shape[1] * scale)
        new_h = int(roi.shape[0] * scale)
        roi = cv2.resize(roi, (new_w, new_h), interpolation=cv2.INTER_CUBIC)
    
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(roi)
    filtered = cv2.bilateralFilter(enhanced, 9, 75, 75)
    processed = cv2.adaptiveThreshold(
        filtered, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY, 11, 2
    )
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    processed = cv2.morphologyEx(processed, cv2.MORPH_CLOSE, kernel)
    
    return processed

print("🎥 Opening camera 1 (Mac webcam)...")
cap = cv2.VideoCapture(1)

if not cap.isOpened():
    print("❌ Failed to open camera 1, trying camera 0...")
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Failed to open any camera")
        exit(1)

print("✅ Camera ready!")
print("\n📝 Instructions:")
print("1. Write a name on paper: JOHN SMITH")
print("2. Hold it in the CENTER of camera view")
print("3. Press SPACE to test OCR")
print("4. Press 'q' to quit\n")

while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    # Draw center box
    h, w = frame.shape[:2]
    cv2.rectangle(frame, (w//4, h//4), (3*w//4, 3*h//4), (0, 255, 0), 2)
    cv2.putText(frame, "Hold name in green box", (10, 30), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    cv2.putText(frame, "SPACE=test OCR | q=quit", (10, h-20), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    cv2.imshow('Badge Reader Test', frame)
    
    key = cv2.waitKey(1) & 0xFF
    
    if key == ord(' '):
        print("\n" + "="*50)
        print("📸 Testing OCR...")
        
        # Preprocess
        processed = preprocess(frame)
        
        # Run OCR
        text = pytesseract.image_to_string(processed, config='--psm 6')
        
        print(f"\n📝 OCR Result:")
        print(f"{text if text.strip() else '(no text detected)'}")
        
        # Show what name extraction would find
        import re
        patterns = [
            r'\b([A-Z][a-z]+)\s+([A-Z][a-z]+)\b',
            r'\b([A-Z][A-Z]+)\s+([A-Z][A-Z]+)\b',
        ]
        
        names = []
        for pattern in patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                if match.lastindex >= 2:
                    name = f"{match.group(1)} {match.group(2)}"
                    names.append(name)
        
        if names:
            print(f"\n✅ Names detected: {names}")
        else:
            print("\n❌ No names detected")
            print("💡 Try:")
            print("   - LARGER letters")
            print("   - DARKER pen")
            print("   - Better lighting")
            print("   - Proper format: 'JOHN SMITH' or 'John Smith'")
        
        print("="*50 + "\n")
    
    elif key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
print("\n✅ Test complete!")
