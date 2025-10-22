#!/usr/bin/env python3
"""
Simple microphone test script to verify audio input is working.
"""
import sounddevice as sd
import numpy as np
import time

print("Testing microphone input...")
print("Speak now for 5 seconds...")
print()

# Record 5 seconds of audio
duration = 5  # seconds
sample_rate = 16000

audio_data = sd.rec(
    int(sample_rate * duration),
    samplerate=sample_rate,
    channels=1,
    dtype='float32',
    device=1  # MacBook Pro Microphone
)

sd.wait()  # Wait until recording is finished

print("Recording complete!")
print()

# Analyze the audio
audio_array = audio_data.flatten()
rms = np.sqrt(np.mean(audio_array**2))
peak = np.max(np.abs(audio_array))
mean_abs = np.mean(np.abs(audio_array))

print(f"Audio Statistics:")
print(f"  RMS Level: {rms:.6f}")
print(f"  Peak Level: {peak:.6f}")
print(f"  Mean Absolute: {mean_abs:.6f}")
print(f"  Silence Threshold (0.003): {'BELOW' if rms < 0.003 else 'ABOVE'}")
print(f"  Silence Threshold (0.01): {'BELOW' if rms < 0.01 else 'ABOVE'}")
print()

if rms < 0.003:
    print("⚠️  WARNING: Audio level is very low!")
    print("   Your microphone might be muted or the volume is too low.")
    print("   Check System Settings > Sound > Input")
elif rms < 0.01:
    print("⚠️  Audio level is low but detectable")
    print("   You may need to speak louder or increase microphone volume")
else:
    print("✅ Audio level looks good!")

print()
print(f"Raw audio sample (first 10 values): {audio_array[:10]}")
