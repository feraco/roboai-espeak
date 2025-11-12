#!/usr/bin/env python3
"""
Simple badge name detector with multiple OCR engines
Tests different approaches to find what works best
"""

import cv2
import numpy as np

# Try different OCR engines
try:
    import pytesseract
    HAS_TESSERACT = True
except ImportError:
    HAS_TESSERACT = False
    print("⚠️  pytesseract not available")

try:
    import easyocr
    HAS_EASYOCR = True
except ImportError:
    HAS_EASYOCR = False
    print("⚠️  easyocr not available (better for handwriting)")

print("🎥 Opening camera 1...")
cap = cv2.VideoCapture(1)

if not cap.isOpened():
    print("❌ Camera 1 failed, trying 0...")
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ No camera available")
        exit(1)

print("✅ Camera opened")
print("\n📝 INSTRUCTIONS:")
print("=" * 60)
print("For best results:")
print("1. Write name in LARGE CAPITAL LETTERS (at least 1 inch tall)")
print("2. Use DARK BLACK marker on WHITE paper")
print("3. Hold paper flat, fill the green box")
print("4. Good lighting (no shadows)")
print("5. Keep steady")
print("\nExamples that work best:")
print("  JOHN SMITH")
print("  SARAH JONES")
print("  ALEX CHEN")
print("\nPress SPACE to test OCR")
print("Press 't' to try Tesseract OCR")
print("Press 'e' to try EasyOCR (if installed)")
print("Press 'q' to quit")
print("=" * 60 + "\n")

# Initialize EasyOCR if available
reader = None
if HAS_EASYOCR:
    print("🔄 Loading EasyOCR (one-time, takes ~10 seconds)...")
    reader = easyocr.Reader(['en'], gpu=False)
    print("✅ EasyOCR ready\n")

def preprocess_aggressive(frame):
    """More aggressive preprocessing for better OCR"""
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # Get center region
    h, w = gray.shape
    roi = gray[h//4:3*h//4, w//4:3*w//4]
    
    # Upscale 2x for better OCR
    roi = cv2.resize(roi, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    
    # Denoise
    denoised = cv2.fastNlMeansDenoising(roi, None, 10, 7, 21)
    
    # Enhance contrast
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(denoised)
    
    # Binary threshold
    _, binary = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    # Morphological operations
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    processed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
    
    return processed

snapshot_count = 0

while True:
    ret, frame = cap.read()
    if not ret:
        print("❌ Failed to read frame")
        break
    
    # Draw UI
    h, w = frame.shape[:2]
    cv2.rectangle(frame, (w//4, h//4), (3*w//4, 3*h//4), (0, 255, 0), 3)
    cv2.putText(frame, "Hold badge HERE (fill green box)", (w//4 + 10, h//4 - 10),
               cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
    cv2.putText(frame, "SPACE=Tesseract | e=EasyOCR | q=quit", (10, h-20),
               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    
    cv2.imshow('Badge Name Detector', frame)
    
    key = cv2.waitKey(1) & 0xFF
    
    if key == ord('q'):
        break
    
    elif key == ord(' ') or key == ord('t'):
        if not HAS_TESSERACT:
            print("❌ Tesseract not available - install: pip install pytesseract")
            continue
            
        print("\n" + "="*60)
        print("🔍 Testing with TESSERACT OCR...")
        snapshot_count += 1
        
        # Save original
        cv2.imwrite(f"badge_original_{snapshot_count}.jpg", frame)
        
        # Preprocess
        processed = preprocess_aggressive(frame)
        cv2.imwrite(f"badge_processed_{snapshot_count}.jpg", processed)
        
        print(f"📸 Saved: badge_original_{snapshot_count}.jpg")
        print(f"📝 Saved: badge_processed_{snapshot_count}.jpg")
        
        # Try different PSM modes
        configs = [
            ('Single block', '--psm 6'),
            ('Single line', '--psm 7'),
            ('Single word', '--psm 8'),
            ('Sparse text', '--psm 11'),
        ]
        
        for name, config in configs:
            text = pytesseract.image_to_string(processed, config=config)
            if text.strip():
                print(f"\n{name} ({config}):")
                print(f"  {text.strip()}")
        
        # Also try on original
        text_orig = pytesseract.image_to_string(frame, config='--psm 6')
        if text_orig.strip():
            print(f"\nOriginal frame (--psm 6):")
            print(f"  {text_orig.strip()}")
        
        print("="*60 + "\n")
    
    elif key == ord('e'):
        if not HAS_EASYOCR:
            print("❌ EasyOCR not available - install: pip install easyocr")
            continue
            
        print("\n" + "="*60)
        print("🔍 Testing with EASYOCR (better for handwriting)...")
        snapshot_count += 1
        
        # Get center region
        h, w = frame.shape[:2]
        roi = frame[h//4:3*h//4, w//4:3*w//4]
        
        # Run EasyOCR
        results = reader.readtext(roi)
        
        if results:
            print(f"\n✅ EasyOCR detected {len(results)} text region(s):")
            for bbox, text, confidence in results:
                print(f"  '{text}' (confidence: {confidence:.2f})")
        else:
            print("\n❌ No text detected")
        
        print("="*60 + "\n")

cap.release()
cv2.destroyAllWindows()

print("\n💡 TIPS FOR BETTER DETECTION:")
print("1. Use PRINTED text if possible (not handwritten)")
print("2. Make letters at least 1 inch (2.5cm) tall")
print("3. Dark black on white background")
print("4. Fill most of the green box")
print("5. If Tesseract fails, try EasyOCR (better for varied text)")
print("\nTo install EasyOCR: pip install easyocr")
