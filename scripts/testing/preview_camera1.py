#!/usr/bin/env python3
"""
Live preview of Camera 1 (RGB camera)
"""

import cv2

print("🎥 Opening Camera 1 (RGB - 3 channels)...")
cap = cv2.VideoCapture(1)

if not cap.isOpened():
    print("❌ Failed to open Camera 1")
    exit(1)

print("✅ Camera 1 opened")
print("📺 Showing live preview...")
print("   Press 'q' to quit")
print("   Press 's' to save a snapshot")
print("")

snapshot_count = 0

while True:
    ret, frame = cap.read()
    
    if not ret:
        print("❌ Failed to read frame")
        break
    
    # Add info overlay
    h, w = frame.shape[:2]
    channels = frame.shape[2] if len(frame.shape) == 3 else 1
    
    cv2.putText(frame, f"Camera 1 - {w}x{h} - {channels} channels (RGB)", (10, 30),
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    cv2.putText(frame, "Press 'q' to quit, 's' to save snapshot", (10, h-20),
               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    # Draw center box for badge area
    cv2.rectangle(frame, (w//4, h//4), (3*w//4, 3*h//4), (0, 255, 0), 2)
    cv2.putText(frame, "Hold badge here", (w//4 + 10, h//4 + 30),
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    
    cv2.imshow('Camera 1 - RGB Preview', frame)
    
    key = cv2.waitKey(1) & 0xFF
    
    if key == ord('q'):
        print("\n👋 Preview closed")
        break
    elif key == ord('s'):
        snapshot_count += 1
        filename = f"camera1_snapshot_{snapshot_count}.jpg"
        cv2.imwrite(filename, frame)
        print(f"📸 Saved: {filename}")

cap.release()
cv2.destroyAllWindows()
