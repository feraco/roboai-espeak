#!/usr/bin/env python3
"""
Test script to identify supported audio sample rates on Jetson Orin or other hardware.
Run this on your Jetson to find out which sample rates work.
"""

import sounddevice as sd
import numpy as np

def test_sample_rates():
    """Test common sample rates to see which ones are supported."""
    
    print("=" * 60)
    print("Audio Device Information")
    print("=" * 60)
    
    # List all devices
    devices = sd.query_devices()
    print("\nAvailable Audio Devices:")
    for idx, dev in enumerate(devices):
        if dev["max_input_channels"] > 0:
            print(f"  [{idx}] {dev['name']}")
            print(f"      Input Channels: {dev['max_input_channels']}")
            print(f"      Default Sample Rate: {dev['default_samplerate']} Hz")
    
    # Get default input device
    default_input = sd.query_devices(kind='input')
    print(f"\nDefault Input Device: {default_input['name']}")
    print(f"Default Sample Rate: {default_input['default_samplerate']} Hz")
    
    print("\n" + "=" * 60)
    print("Testing Sample Rates")
    print("=" * 60)
    
    # Common sample rates to test
    test_rates = [8000, 11025, 16000, 22050, 32000, 44100, 48000, 96000]
    
    supported_rates = []
    
    for rate in test_rates:
        try:
            # Try to create a test stream
            stream = sd.InputStream(
                samplerate=rate,
                channels=1,
                dtype='float32',
                blocksize=1024
            )
            stream.close()
            
            print(f"✓ {rate} Hz - SUPPORTED")
            supported_rates.append(rate)
            
        except Exception as e:
            print(f"✗ {rate} Hz - NOT SUPPORTED ({str(e)[:50]}...)")
    
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"\nSupported Sample Rates: {supported_rates}")
    
    if 16000 in supported_rates:
        print("\n✓ 16000 Hz is supported - no changes needed!")
    else:
        recommended = supported_rates[0] if supported_rates else 48000
        print(f"\n⚠ 16000 Hz NOT supported!")
        print(f"Recommended: Use {recommended} Hz in your config")
        print(f"\nUpdate your config file:")
        print(f'  "sample_rate": {recommended},')
    
    print("\n" + "=" * 60)
    
    # Test recording with the first supported rate
    if supported_rates:
        print(f"\nTesting 1-second recording at {supported_rates[0]} Hz...")
        try:
            duration = 1.0  # seconds
            recording = sd.rec(
                int(supported_rates[0] * duration),
                samplerate=supported_rates[0],
                channels=1,
                dtype='float32'
            )
            sd.wait()
            
            # Calculate RMS to check if audio was captured
            rms = np.sqrt(np.mean(recording**2))
            print(f"Recording successful!")
            print(f"RMS Level: {rms:.6f}")
            
            if rms > 0.001:
                print("✓ Audio appears to be working!")
            else:
                print("⚠ Audio level very low - check microphone connection")
                
        except Exception as e:
            print(f"✗ Recording test failed: {e}")

if __name__ == "__main__":
    try:
        test_sample_rates()
    except Exception as e:
        print(f"Error: {e}")
        print("\nMake sure sounddevice is installed:")
        print("  pip install sounddevice numpy")
