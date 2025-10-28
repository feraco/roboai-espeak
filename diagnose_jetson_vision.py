#!/usr/bin/env python3
"""
Diagnostic script for VLMOllamaVision issues on Jetson.
Tests camera access, OpenCV, and Ollama connectivity.
"""

import sys
import subprocess

def check_opencv():
    """Check if OpenCV is installed and can access camera."""
    print("=" * 60)
    print("1. Checking OpenCV Installation")
    print("=" * 60)
    
    try:
        import cv2
        print(f"✓ OpenCV version: {cv2.__version__}")
        
        # Try to open camera
        print("\nTesting camera access...")
        for idx in range(3):
            cap = cv2.VideoCapture(idx)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret:
                    print(f"✓ Camera {idx} is accessible (resolution: {frame.shape[1]}x{frame.shape[0]})")
                else:
                    print(f"✗ Camera {idx} opened but cannot read frames")
                cap.release()
            else:
                print(f"✗ Camera {idx} not accessible")
        
        return True
        
    except ImportError as e:
        print(f"✗ OpenCV not installed: {e}")
        print("\nInstall with: uv pip install opencv-python-headless")
        return False
    except Exception as e:
        print(f"✗ Error testing camera: {e}")
        return False

def check_numpy():
    """Check if NumPy is installed."""
    print("\n" + "=" * 60)
    print("2. Checking NumPy Installation")
    print("=" * 60)
    
    try:
        import numpy as np
        print(f"✓ NumPy version: {np.__version__}")
        return True
    except ImportError:
        print("✗ NumPy not installed")
        print("\nInstall with: uv pip install numpy")
        return False

def check_ollama():
    """Check if Ollama is running and has vision models."""
    print("\n" + "=" * 60)
    print("3. Checking Ollama Service")
    print("=" * 60)
    
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        
        if response.status_code == 200:
            print("✓ Ollama is running")
            
            models = response.json().get('models', [])
            vision_models = [m for m in models if 'llava' in m.get('name', '').lower() or 'vision' in m.get('name', '').lower()]
            
            if vision_models:
                print(f"✓ Vision models found: {[m['name'] for m in vision_models]}")
            else:
                print("✗ No vision models found")
                print("\nInstall with: ollama pull llava-llama3")
            
            return True
        else:
            print(f"✗ Ollama returned status {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("✗ Cannot connect to Ollama (not running?)")
        print("\nStart Ollama:")
        print("  sudo systemctl start ollama")
        print("  # or")
        print("  ollama serve")
        return False
    except ImportError:
        print("✗ requests library not installed")
        return False
    except Exception as e:
        print(f"✗ Error checking Ollama: {e}")
        return False

def check_permissions():
    """Check camera permissions on Jetson."""
    print("\n" + "=" * 60)
    print("4. Checking Camera Permissions")
    print("=" * 60)
    
    import os
    import grp
    
    # Check if user is in video group
    try:
        video_gid = grp.getgrnam('video').gr_gid
        user_groups = os.getgroups()
        
        if video_gid in user_groups:
            print("✓ User is in 'video' group")
        else:
            print("✗ User is NOT in 'video' group")
            print(f"\nAdd user to video group:")
            print(f"  sudo usermod -aG video $USER")
            print(f"  # Then logout and login again")
            return False
    except KeyError:
        print("⚠ 'video' group does not exist (unusual)")
    except Exception as e:
        print(f"⚠ Could not check group membership: {e}")
    
    # Check camera device files
    camera_devices = ['/dev/video0', '/dev/video1', '/dev/video2']
    found_cameras = []
    
    for device in camera_devices:
        if os.path.exists(device):
            found_cameras.append(device)
            # Check if readable
            if os.access(device, os.R_OK):
                print(f"✓ {device} exists and is readable")
            else:
                print(f"✗ {device} exists but is NOT readable (permission issue)")
    
    if not found_cameras:
        print("✗ No camera devices found (/dev/video*)")
        return False
    
    return True

def check_jetson_specific():
    """Check Jetson-specific camera issues."""
    print("\n" + "=" * 60)
    print("5. Jetson-Specific Checks")
    print("=" * 60)
    
    # Check if running on Jetson
    try:
        with open('/etc/nv_tegra_release', 'r') as f:
            jetson_version = f.read().strip()
            print(f"✓ Running on Jetson: {jetson_version}")
    except FileNotFoundError:
        print("⚠ Not running on a Jetson (or /etc/nv_tegra_release not found)")
        return True
    
    # Check for common Jetson camera issues
    print("\nChecking camera modules...")
    
    # Check if nvarguscamerasrc is available (for CSI cameras)
    result = subprocess.run(['which', 'nvarguscamerasrc'], 
                          capture_output=True, text=True)
    if result.returncode == 0:
        print("✓ nvarguscamerasrc found (CSI camera support)")
    else:
        print("⚠ nvarguscamerasrc not found (CSI cameras may not work)")
    
    return True

def main():
    """Run all diagnostic checks."""
    print("\n" + "=" * 60)
    print("VLMOllamaVision Diagnostic Tool for Jetson")
    print("=" * 60)
    
    results = {
        'opencv': check_opencv(),
        'numpy': check_numpy(),
        'ollama': check_ollama(),
        'permissions': check_permissions(),
        'jetson': check_jetson_specific()
    }
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    all_good = all(results.values())
    
    for check, status in results.items():
        symbol = "✓" if status else "✗"
        print(f"{symbol} {check.upper()}: {'PASS' if status else 'FAIL'}")
    
    if all_good:
        print("\n✓ All checks passed! Vision input should work.")
    else:
        print("\n✗ Some checks failed. Fix the issues above and try again.")
        sys.exit(1)

if __name__ == "__main__":
    main()
