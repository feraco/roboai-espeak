#!/usr/bin/env python3
"""
Test if Ollama llava vision model is working and responding to camera input.
Run this on Ubuntu G1 to diagnose vision issues.
"""

import asyncio
import base64
import json
import sys
import time

try:
    import cv2
    import aiohttp
except ImportError as e:
    print(f"❌ Missing dependency: {e}")
    print("Install with: pip install opencv-python aiohttp")
    sys.exit(1)


async def test_vision():
    """Test Ollama vision model with camera."""
    
    print("=" * 70)
    print("OLLAMA LLAVA VISION TEST")
    print("=" * 70)
    
    # Configuration
    base_url = "http://localhost:11434"
    model = "llava-llama3"
    camera_index = 0
    prompt = "In one brief sentence, describe what you see: Is there a person? What are they wearing? Focus on obvious, visible details only."
    
    print(f"\nConfiguration:")
    print(f"  Base URL: {base_url}")
    print(f"  Model: {model}")
    print(f"  Camera Index: {camera_index}")
    print(f"  Prompt: {prompt}")
    
    # Step 1: Check if Ollama is running
    print(f"\n{'='*70}")
    print("STEP 1: Testing Ollama connection...")
    print(f"{'='*70}")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{base_url}/api/tags") as response:
                if response.status == 200:
                    data = await response.json()
                    models = [m['name'] for m in data.get('models', [])]
                    print(f"✅ Ollama is running")
                    print(f"   Available models: {models}")
                    
                    if model not in models and 'llava-llama3:latest' not in models:
                        print(f"\n⚠️  WARNING: {model} not found in available models!")
                        print(f"   Install with: ollama pull {model}")
                        return
                else:
                    print(f"❌ Ollama returned status {response.status}")
                    return
    except Exception as e:
        print(f"❌ Cannot connect to Ollama: {e}")
        print(f"   Make sure Ollama is running: systemctl status ollama")
        return
    
    # Step 2: Check camera
    print(f"\n{'='*70}")
    print("STEP 2: Testing camera...")
    print(f"{'='*70}")
    
    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        print(f"❌ Cannot open camera index {camera_index}")
        print(f"   Try: ls /dev/video*")
        print(f"   Or test other indices: 0, 1, 2, etc.")
        return
    
    print(f"✅ Camera {camera_index} opened successfully")
    
    # Capture a frame
    ret, frame = cap.read()
    if not ret:
        print(f"❌ Failed to capture frame from camera")
        cap.release()
        return
    
    height, width = frame.shape[:2]
    print(f"   Resolution: {width}x{height}")
    
    # Save test image
    cv2.imwrite("/tmp/test_vision_frame.jpg", frame)
    print(f"   Saved test frame to: /tmp/test_vision_frame.jpg")
    
    # Step 3: Encode frame
    print(f"\n{'='*70}")
    print("STEP 3: Encoding frame...")
    print(f"{'='*70}")
    
    ok, buffer = cv2.imencode('.jpg', frame)
    if not ok:
        print(f"❌ Failed to encode frame")
        cap.release()
        return
    
    image_bytes = buffer.tobytes()
    image_b64 = base64.b64encode(image_bytes).decode('utf-8')
    print(f"✅ Frame encoded ({len(image_b64)} bytes base64)")
    
    # Step 4: Send to Ollama
    print(f"\n{'='*70}")
    print("STEP 4: Sending to Ollama vision model...")
    print(f"{'='*70}")
    print(f"This may take 10-30 seconds...")
    
    payload = {
        "model": model,
        "prompt": prompt,
        "images": [image_b64],
        "stream": False
    }
    
    start_time = time.time()
    
    try:
        timeout = aiohttp.ClientTimeout(total=60)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            url = f"{base_url}/api/generate"
            async with session.post(url, json=payload) as response:
                elapsed = time.time() - start_time
                
                if response.status != 200:
                    text = await response.text()
                    print(f"❌ Request failed with status {response.status}")
                    print(f"   Response: {text[:500]}")
                    return
                
                result = await response.json()
                description = result.get('response', '')
                
                print(f"✅ Received response in {elapsed:.1f} seconds")
                print(f"\n{'='*70}")
                print("VISION MODEL OUTPUT:")
                print(f"{'='*70}")
                print(f"\n{description}\n")
                
                # Show what would be sent to LLM
                print(f"{'='*70}")
                print("WHAT THE LLM WOULD SEE:")
                print(f"{'='*70}")
                formatted = f"""
INPUT: Vision
// START
{description.strip()}
// END
"""
                print(formatted)
                
    except asyncio.TimeoutError:
        print(f"❌ Request timed out after 60 seconds")
        print(f"   The model might be loading or your system is slow")
        print(f"   Try running again, first request is usually slower")
    except Exception as e:
        print(f"❌ Error during request: {e}")
        import traceback
        traceback.print_exc()
    
    cap.release()
    
    print(f"\n{'='*70}")
    print("DIAGNOSIS COMPLETE")
    print(f"{'='*70}")
    print("\nIf you see 'VISION MODEL OUTPUT' above, the vision system is working!")
    print("If the LLM still doesn't respond about appearance:")
    print("  1. Check that the vision input is in the AVAILABLE INPUTS section of logs")
    print("  2. Make sure 'analysis_interval' isn't too long (try 5.0 seconds)")
    print("  3. Verify 'poll_interval' is reasonable (2-3 seconds)")
    print()


if __name__ == "__main__":
    try:
        asyncio.run(test_vision())
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
