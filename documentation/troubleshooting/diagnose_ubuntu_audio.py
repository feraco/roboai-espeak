#!/usr/bin/env python3
"""
Ubuntu Audio Diagnostic - Simple test to see what's detected
"""

import subprocess
import sys

print("=" * 70)
print("🔍 UBUNTU AUDIO DIAGNOSTIC")
print("=" * 70)

# Test 1: Check ALSA input devices
print("\n1️⃣  ALSA INPUT DEVICES (arecord -l):")
print("-" * 70)
try:
    result = subprocess.run(['arecord', '-l'], capture_output=True, text=True, timeout=5)
    if result.returncode == 0:
        print(result.stdout)
        if "card" in result.stdout.lower():
            print("✅ ALSA input devices found")
        else:
            print("⚠️  No input devices listed")
    else:
        print(f"❌ arecord failed: {result.stderr}")
except FileNotFoundError:
    print("❌ arecord command not found - install alsa-utils:")
    print("   sudo apt install alsa-utils")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 2: Check ALSA output devices
print("\n2️⃣  ALSA OUTPUT DEVICES (aplay -l):")
print("-" * 70)
try:
    result = subprocess.run(['aplay', '-l'], capture_output=True, text=True, timeout=5)
    if result.returncode == 0:
        print(result.stdout)
        if "card" in result.stdout.lower():
            print("✅ ALSA output devices found")
        else:
            print("⚠️  No output devices listed")
    else:
        print(f"❌ aplay failed: {result.stderr}")
except FileNotFoundError:
    print("❌ aplay command not found - install alsa-utils:")
    print("   sudo apt install alsa-utils")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 3: Check PyAudio devices
print("\n3️⃣  PYAUDIO DEVICES:")
print("-" * 70)
try:
    import pyaudio
    p = pyaudio.PyAudio()
    
    input_devices = []
    output_devices = []
    
    for i in range(p.get_device_count()):
        try:
            info = p.get_device_info_by_index(i)
            if info['maxInputChannels'] > 0:
                input_devices.append(f"  [{i}] {info['name']} (channels: {info['maxInputChannels']})")
            if info['maxOutputChannels'] > 0:
                output_devices.append(f"  [{i}] {info['name']} (channels: {info['maxOutputChannels']})")
        except Exception as e:
            continue
    
    print(f"INPUT DEVICES ({len(input_devices)} found):")
    if input_devices:
        for dev in input_devices:
            print(dev)
        print("✅ PyAudio input devices found")
    else:
        print("❌ No PyAudio input devices found")
    
    print(f"\nOUTPUT DEVICES ({len(output_devices)} found):")
    if output_devices:
        for dev in output_devices:
            print(dev)
        print("✅ PyAudio output devices found")
    else:
        print("❌ No PyAudio output devices found")
    
    p.terminate()
    
except ImportError:
    print("❌ PyAudio not installed:")
    print("   sudo apt install python3-pyaudio")
    print("   or: pip install pyaudio")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 4: Test recording with arecord
print("\n4️⃣  TEST RECORDING (if devices found):")
print("-" * 70)
print("Attempting to record 2 seconds from default device...")
try:
    # Try default device first
    result = subprocess.run(
        ['arecord', '-D', 'default', '-f', 'S16_LE', '-r', '16000', '-c', '1', '-d', '2', '/tmp/test_audio.wav'],
        capture_output=True,
        text=True,
        timeout=5
    )
    if result.returncode == 0:
        print("✅ Recording from default device works!")
    else:
        print(f"❌ Recording failed: {result.stderr}")
        
        # Try hw:0,0
        print("\nTrying hw:0,0...")
        result = subprocess.run(
            ['arecord', '-D', 'hw:0,0', '-f', 'S16_LE', '-r', '16000', '-c', '1', '-d', '2', '/tmp/test_audio.wav'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print("✅ Recording from hw:0,0 works!")
        else:
            print(f"❌ Recording from hw:0,0 failed: {result.stderr}")
            
except Exception as e:
    print(f"❌ Error: {e}")

# Test 5: Check user permissions
print("\n5️⃣  USER PERMISSIONS:")
print("-" * 70)
try:
    import os
    import grp
    
    username = os.getenv('USER')
    groups = [grp.getgrgid(g).gr_name for g in os.getgroups()]
    
    print(f"User: {username}")
    print(f"Groups: {', '.join(groups)}")
    
    if 'audio' in groups:
        print("✅ User is in 'audio' group")
    else:
        print("⚠️  User NOT in 'audio' group")
        print("   Fix: sudo usermod -a -G audio $USER")
        print("   Then logout and login again")
    
    # Check device permissions
    import glob
    audio_devices = glob.glob('/dev/snd/*')
    if audio_devices:
        print(f"\nFound {len(audio_devices)} audio devices in /dev/snd/")
        
        # Check first pcm device
        pcm_devices = [d for d in audio_devices if 'pcmC' in d]
        if pcm_devices:
            test_device = pcm_devices[0]
            import stat
            st = os.stat(test_device)
            mode = stat.filemode(st.st_mode)
            print(f"Permissions on {test_device}: {mode}")
            
            if os.access(test_device, os.R_OK | os.W_OK):
                print(f"✅ Can read/write {test_device}")
            else:
                print(f"❌ Cannot access {test_device}")
                print("   May need to add user to audio group")
    
except Exception as e:
    print(f"⚠️  Error checking permissions: {e}")

# Summary
print("\n" + "=" * 70)
print("📋 SUMMARY & RECOMMENDATIONS:")
print("=" * 70)
print("""
If you see:
- ✅ ALSA devices found BUT ❌ PyAudio devices NOT found:
  → Install: sudo apt install python3-pyaudio portaudio19-dev
  
- ❌ Permission denied errors:
  → Add to audio group: sudo usermod -a -G audio $USER
  → Logout and login again
  
- ❌ No devices found at all:
  → Check if microphone is plugged in
  → Try: sudo alsa force-reload
  → Check: lsusb (for USB mics)
  
- ✅ ALSA works BUT ❌ Recording fails:
  → Device may be in use by another program
  → Try: fuser -v /dev/snd/*
  → Kill conflicting process
""")

print("\nTo run hardware check after fixing issues:")
print("  python3 check_g1_hardware.py")
print("=" * 70)
