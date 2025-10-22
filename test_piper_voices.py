from piper import PiperVoice
import json
import sounddevice as sd
import numpy as np
import time
import glob
import os

def test_voice(model_path, text="Hello, I am a virtual assistant at Astra Vein Treatment Center. How may I help you today?"):
    print(f"\nTesting voice: {os.path.basename(model_path)}")
    try:
        config_path = model_path.replace('.onnx', '.onnx.json')
        if not os.path.exists(config_path):
            print(f"Config file not found: {config_path}")
            return
            
        with open(config_path, 'r') as f:
            config = json.load(f)
            
        voice = PiperVoice(model_path, config)
        
        # Generate audio and collect all samples
        audio_chunks = []
        for chunk in voice.synthesize(text):
            audio_chunks.extend(chunk)
        
        # Convert to float32 and normalize
        audio = np.array(audio_chunks, dtype=np.float32) / 32768.0
        
        # Play audio using sounddevice
        sample_rate = 22050  # Default Piper sample rate
        print("Playing audio...")
        sd.play(audio, sample_rate)
        sd.wait()  # Wait until audio is finished playing
        time.sleep(1)  # Add a small gap between voices
        
    except Exception as e:
        print(f"Error testing voice: {e}")

def main():
    # Search for all English voice models
    voice_path = "piper-voices"
    en_voices = glob.glob(f"{voice_path}/en/*/*.onnx")
    
    print(f"Found {len(en_voices)} English voices")
    
    for voice_file in en_voices:
        test_voice(voice_file)
        input("Press Enter to test next voice...")

if __name__ == "__main__":
    main()