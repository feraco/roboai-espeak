#!/usr/bin/env python3
"""
Quick diagnostic script to check if all audio dependencies are working on Jetson Orin.
Run this BEFORE running the agent to verify setup.
"""

import sys

def check_import(module_name, package_name=None):
    """Try to import a module and report status."""
    if package_name is None:
        package_name = module_name
    
    try:
        __import__(module_name)
        print(f"✓ {package_name:<20} - OK")
        return True
    except ImportError as e:
        print(f"✗ {package_name:<20} - MISSING: {str(e)[:50]}")
        return False

def check_command(command):
    """Check if a command is available."""
    import subprocess
    try:
        result = subprocess.run(
            ['which', command],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(f"✓ {command:<20} - {result.stdout.strip()}")
            return True
        else:
            print(f"✗ {command:<20} - NOT FOUND")
            return False
    except Exception as e:
        print(f"✗ {command:<20} - ERROR: {e}")
        return False

def main():
    print("=" * 70)
    print("Jetson Orin Audio Dependencies Check")
    print("=" * 70)
    
    all_good = True
    
    print("\n1. System Commands:")
    print("-" * 70)
    commands = ['arecord', 'aplay', 'piper', 'ffmpeg']
    for cmd in commands:
        if not check_command(cmd):
            all_good = False
    
    print("\n2. Python Core Audio Libraries:")
    print("-" * 70)
    core_libs = [
        ('numpy', 'numpy'),
        ('sounddevice', 'sounddevice'),
        ('soundfile', 'soundfile'),
        ('scipy', 'scipy'),
    ]
    for module, name in core_libs:
        if not check_import(module, name):
            all_good = False
    
    print("\n3. Python ASR Libraries:")
    print("-" * 70)
    asr_libs = [
        ('faster_whisper', 'faster-whisper'),
    ]
    for module, name in asr_libs:
        if not check_import(module, name):
            all_good = False
    
    print("\n4. Python Vision Libraries:")
    print("-" * 70)
    vision_libs = [
        ('cv2', 'opencv-python'),
    ]
    for module, name in vision_libs:
        if not check_import(module, name):
            all_good = False
    
    print("\n5. Audio Devices:")
    print("-" * 70)
    try:
        import sounddevice as sd
        devices = sd.query_devices()
        
        input_count = sum(1 for d in devices if d['max_input_channels'] > 0)
        output_count = sum(1 for d in devices if d['max_output_channels'] > 0)
        
        print(f"✓ Input devices found:  {input_count}")
        print(f"✓ Output devices found: {output_count}")
        
        if input_count == 0:
            print("✗ WARNING: No input devices detected!")
            all_good = False
        
        if output_count == 0:
            print("✗ WARNING: No output devices detected!")
            all_good = False
            
    except Exception as e:
        print(f"✗ ERROR querying devices: {e}")
        all_good = False
    
    print("\n6. Camera Devices:")
    print("-" * 70)
    try:
        import cv2
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            print("✓ Camera 0 is accessible")
            cap.release()
        else:
            print("✗ Camera 0 cannot be opened")
            all_good = False
    except Exception as e:
        print(f"✗ ERROR: {e}")
        all_good = False
    
    print("\n" + "=" * 70)
    if all_good:
        print("✓ ALL CHECKS PASSED - Ready to run agent!")
        print("\nNext step:")
        print("  uv run src/run.py astra_vein_receptionist")
    else:
        print("✗ SOME CHECKS FAILED - Fix issues before running agent")
        print("\nTo fix:")
        print("  1. Run: ./setup_jetson_audio.sh")
        print("  2. Reboot: sudo reboot")
        print("  3. Run this check again: python3 check_jetson_dependencies.py")
    print("=" * 70)
    
    return 0 if all_good else 1

if __name__ == "__main__":
    sys.exit(main())
