from piper import PiperVoice
import numpy as np
import sounddevice as sd

def test_piper():
    # Test text
    text = "Hello, I am testing Piper TTS, a fast and local neural text-to-speech engine."
    
    try:
        # Initialize Piper with a voice model
        voice_dir = "piper-voices/en/en_US/amy/low/"
        model_path = voice_dir + "en_US-amy-low.onnx"
        config_path = model_path + ".json"
        
        print(f"Loading voice model from: {model_path}")
        voice = PiperVoice.load(model_path)
        
        print("Synthesizing speech...")
        # Generate audio samples
        audio_chunks = []
        for chunk in voice.synthesize(text):
            audio_chunks.append(chunk)
            
        # Combine chunks into a single array
        audio = np.concatenate(audio_chunks)
        audio = audio.astype(np.float32) / 32768.0
        
        # Play audio using sounddevice
        sample_rate = 22050  # Default Piper sample rate
        print("Playing audio...")
        sd.play(audio, sample_rate)
        sd.wait()  # Wait until audio is finished playing
        
    except Exception as e:
        print(f"Error testing Piper TTS: {e}")

if __name__ == "__main__":
    test_piper()