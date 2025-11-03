from piper import PiperVoice
import json
import sounddevice as sd
import numpy as np

def test_piper():
    # Initialize Piper with our voice model and config
    model_path = "/Users/wwhs-research/Downloads/roboai-feature-multiple-agent-configurations/piper_voices/en_US-amy-low.onnx"
    config_path = "/Users/wwhs-research/Downloads/roboai-feature-multiple-agent-configurations/piper_voices/en_US-amy-low.onnx.json"
    with open(config_path, 'r') as f:
        config = json.load(f)
    voice = PiperVoice(model_path, config)
    
    # Test text
    text = "Hello, this is a test of the Piper TTS system."
    
    # Generate audio and collect all samples
    audio_chunks = []
    for chunk in voice.synthesize(text):
        audio_chunks.extend(chunk)
    
    # Convert to float32 and normalize
    audio = np.array(audio_chunks, dtype=np.float32) / 32768.0
    
    # Play audio using sounddevice
    sample_rate = 22050  # Default Piper sample rate
    sd.play(audio, sample_rate)
    sd.wait()  # Wait until audio finishes playing
    
    print("Audio test complete. Did you hear anything?")

if __name__ == "__main__":
    test_piper()