#!/usr/bin/env python3
"""
Quick test to find the correct device index and sample rate for Ubuntu G1.
Run this on the Ubuntu machine to diagnose audio issues.
"""

import pyaudio
import sys

def quick_test():
    """Quick test to find working audio configuration."""
    
    p = pyaudio.PyAudio()
    
    print("=" * 70)
    print("QUICK AUDIO DEVICE + SAMPLE RATE TEST")
    print("=" * 70)
    
    device_count = p.get_device_count()
    print(f"\nTotal devices: {device_count}\n")
    
    working_configs = []
    
    for i in range(device_count):
        try:
            info = p.get_device_info_by_index(i)
            if info['maxInputChannels'] > 0:
                print(f"\n--- Device {i}: {info['name']} ---")
                print(f"Max Input Channels: {info['maxInputChannels']}")
                print(f"Default Sample Rate: {int(info['defaultSampleRate'])} Hz")
                
                # Test common sample rates
                for rate in [16000, 48000, 44100, 22050]:
                    try:
                        # Try to actually open a stream
                        test_stream = p.open(
                            format=pyaudio.paInt16,
                            channels=1,
                            rate=rate,
                            input=True,
                            input_device_index=i,
                            frames_per_buffer=1024,
                            start=False
                        )
                        test_stream.close()
                        print(f"  ✅ {rate} Hz WORKS")
                        working_configs.append((i, rate, info['name']))
                    except Exception as e:
                        print(f"  ❌ {rate} Hz FAILS: {str(e)[:50]}")
        except Exception as e:
            print(f"Device {i}: Error - {e}")
    
    print("\n" + "=" * 70)
    print("WORKING CONFIGURATIONS")
    print("=" * 70)
    
    if working_configs:
        print("\nThese device + sample rate combinations work:")
        for idx, rate, name in working_configs:
            print(f"\n  Device {idx}: {name}")
            print(f"    → Sample Rate: {rate} Hz")
            print(f"    → Config: \"input_device\": {idx}, \"sample_rate\": {rate}")
    else:
        print("\n❌ No working configurations found!")
        print("   Check if microphone is properly connected")
    
    p.terminate()
    
    print("\n" + "=" * 70)
    print("NEXT STEPS")
    print("=" * 70)
    if working_configs:
        idx, rate, name = working_configs[0]
        print(f"\n✅ RECOMMENDED CONFIG for astra_vein_receptionist.json5:")
        print(f'\n  "input_device": {idx},  // {name}')
        print(f'  "sample_rate": {rate},')
        print(f'\nEdit with: nano config/astra_vein_receptionist.json5')
    else:
        print("\n1. Check microphone connection")
        print("2. Run: arecord -l")
        print("3. Try different USB ports")
    print()

if __name__ == "__main__":
    try:
        quick_test()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
