#!/usr/bin/env python3
"""
Test which sample rates are supported by Ubuntu microphone devices.
This helps diagnose "Invalid sample rate" errors.
"""

import pyaudio
import sys

def test_sample_rates():
    """Test common sample rates for all input devices."""
    
    # Common sample rates to test
    sample_rates = [8000, 11025, 16000, 22050, 32000, 44100, 48000, 96000]
    
    p = pyaudio.PyAudio()
    
    print("=" * 70)
    print("UBUNTU MICROPHONE SAMPLE RATE TEST")
    print("=" * 70)
    
    # Get all input devices
    device_count = p.get_device_count()
    input_devices = []
    
    for i in range(device_count):
        try:
            info = p.get_device_info_by_index(i)
            if info['maxInputChannels'] > 0:
                input_devices.append((i, info))
        except:
            pass
    
    if not input_devices:
        print("\n❌ No input devices found!")
        p.terminate()
        return
    
    print(f"\nFound {len(input_devices)} input device(s)\n")
    
    # Test each device
    for device_idx, device_info in input_devices:
        print(f"\n{'='*70}")
        print(f"Device {device_idx}: {device_info['name']}")
        print(f"{'='*70}")
        print(f"Max Input Channels: {device_info['maxInputChannels']}")
        print(f"Default Sample Rate: {int(device_info['defaultSampleRate'])} Hz")
        
        print("\nTesting sample rates:")
        supported_rates = []
        
        for rate in sample_rates:
            try:
                # Try to check if this rate is supported
                is_supported = p.is_format_supported(
                    rate,
                    input_device=device_idx,
                    input_channels=1,
                    input_format=pyaudio.paInt16
                )
                
                if is_supported:
                    print(f"  ✅ {rate:6d} Hz - SUPPORTED")
                    supported_rates.append(rate)
                else:
                    print(f"  ❌ {rate:6d} Hz - Not supported")
            except Exception as e:
                print(f"  ❌ {rate:6d} Hz - Error: {str(e)}")
        
        if supported_rates:
            print(f"\n✅ Supported rates for device {device_idx}: {supported_rates}")
            print(f"💡 RECOMMENDED: Use sample_rate: {supported_rates[0]} in your config")
        else:
            print(f"\n❌ No supported sample rates found for device {device_idx}")
            print("   Try using a different device_index or check hardware connection")
    
    p.terminate()
    
    print("\n" + "="*70)
    print("CONFIGURATION GUIDE")
    print("="*70)
    print("\nTo fix 'Invalid sample rate' error:")
    print("1. Find a device above with ✅ supported rates")
    print("2. Update your config JSON5 file:")
    print("   - Set 'input_device': <device_number> (or null for default)")
    print("   - Set 'sample_rate': <supported_rate> (e.g., 48000)")
    print("\nExample config:")
    print('  "sample_rate": 48000,')
    print('  "input_device": 0,  // or null for system default')
    print("\n")

if __name__ == "__main__":
    try:
        test_sample_rates()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
