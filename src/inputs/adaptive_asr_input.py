#!/usr/bin/env python3
"""
Adaptive ASR Input with automatic device detection and fallback
Replaces LocalASRInput with smart device selection and resampling
"""

import logging
import numpy as np
from typing import Optional, Dict, Any
import time

logger = logging.getLogger(__name__)


class AdaptiveASRInput:
    """
    ASR Input with automatic device detection, sample rate adaptation,
    and fallback mechanisms for robust audio capture on G1
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize adaptive ASR input
        
        Args:
            config: Configuration dict with optional:
                - input_device: PyAudio device index (None for auto-detect)
                - sample_rate: Target sample rate (16000 for ASR)
                - chunk_duration: Audio chunk length in seconds
                - silence_threshold: VAD threshold
                - engine: ASR engine (faster-whisper, etc.)
        """
        self.config = config
        self.target_sample_rate = config.get('sample_rate', 16000)
        self.chunk_duration = config.get('chunk_duration', 4.0)
        self.silence_threshold = config.get('silence_threshold', 0.015)
        
        self.audio_device = None
        self.device_sample_rate = None
        self.pyaudio_instance = None
        self.stream = None
        
        # Initialize audio system
        self._initialize_audio()
        
        # Initialize ASR engine
        self._initialize_asr()
    
    def _initialize_audio(self):
        """Auto-detect and initialize audio device"""
        try:
            import pyaudio
            from src.audio_system_fixer import AudioSystemFixer
            
            logger.info("🎤 Initializing adaptive audio system...")
            
            # Run diagnostic if device not specified
            specified_device = self.config.get('input_device')
            
            if specified_device is None:
                logger.info("No device specified, running auto-detection...")
                fixer = AudioSystemFixer()
                diagnostic = fixer.run_full_diagnostic()
                
                if diagnostic['best_input']:
                    best = diagnostic['best_input']
                    self.audio_device = best['pyaudio_index']
                    self.device_sample_rate = best['recommended_rate']
                    
                    logger.info(f"✅ Auto-selected device: {best['name']}")
                    logger.info(f"   PyAudio index: {self.audio_device}")
                    logger.info(f"   Sample rate: {self.device_sample_rate} Hz")
                else:
                    raise RuntimeError("No working audio input device found")
            else:
                # Use specified device but test it
                self.audio_device = specified_device
                self.device_sample_rate = self.target_sample_rate
                logger.info(f"Using specified device: {self.audio_device}")
            
            # Initialize PyAudio
            self.pyaudio_instance = pyaudio.PyAudio()
            
            # Try to open stream with detected settings
            self._open_stream()
            
        except ImportError as e:
            logger.error(f"Missing dependency: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize audio: {e}")
            raise
    
    def _open_stream(self):
        """Open audio stream with fallback logic"""
        import pyaudio
        
        # Try with device sample rate first
        for attempt_rate in [self.device_sample_rate, 16000, 44100, 48000, 22050]:
            try:
                logger.info(f"Attempting to open stream at {attempt_rate} Hz...")
                
                self.stream = self.pyaudio_instance.open(
                    format=pyaudio.paInt16,
                    channels=1,
                    rate=attempt_rate,
                    input=True,
                    input_device_index=self.audio_device,
                    frames_per_buffer=int(attempt_rate * 0.1),  # 100ms buffer
                    stream_callback=None
                )
                
                self.device_sample_rate = attempt_rate
                logger.info(f"✅ Stream opened successfully at {attempt_rate} Hz")
                return
                
            except Exception as e:
                logger.warning(f"Failed at {attempt_rate} Hz: {e}")
                if self.stream:
                    try:
                        self.stream.close()
                    except:
                        pass
                    self.stream = None
                continue
        
        raise RuntimeError("Could not open audio stream at any supported sample rate")
    
    def _initialize_asr(self):
        """Initialize ASR engine"""
        engine = self.config.get('engine', 'faster-whisper')
        
        if engine == 'faster-whisper':
            try:
                from faster_whisper import WhisperModel
                
                model_size = self.config.get('model_size', 'tiny.en')
                device = self.config.get('device', 'cpu')
                compute_type = self.config.get('compute_type', 'int8')
                
                logger.info(f"Loading Faster-Whisper model: {model_size}")
                self.asr_model = WhisperModel(
                    model_size,
                    device=device,
                    compute_type=compute_type
                )
                logger.info("✅ ASR model loaded")
                
            except ImportError:
                logger.error("faster-whisper not installed")
                raise
            except Exception as e:
                logger.error(f"Failed to load ASR model: {e}")
                raise
        else:
            raise ValueError(f"Unsupported ASR engine: {engine}")
    
    def _resample_audio(self, audio_data: np.ndarray, orig_rate: int, target_rate: int) -> np.ndarray:
        """Resample audio to target rate"""
        if orig_rate == target_rate:
            return audio_data
        
        try:
            import librosa
            return librosa.resample(audio_data, orig_sr=orig_rate, target_sr=target_rate)
        except ImportError:
            # Fallback to simple resampling
            ratio = target_rate / orig_rate
            new_length = int(len(audio_data) * ratio)
            return np.interp(
                np.linspace(0, len(audio_data), new_length),
                np.arange(len(audio_data)),
                audio_data
            )
    
    def capture_audio_chunk(self) -> Optional[np.ndarray]:
        """Capture one chunk of audio"""
        if not self.stream or not self.stream.is_active():
            logger.error("Audio stream not active")
            return None
        
        try:
            # Calculate frames to read
            frames_to_read = int(self.device_sample_rate * self.chunk_duration)
            
            # Read audio data
            audio_data = self.stream.read(frames_to_read, exception_on_overflow=False)
            
            # Convert to numpy array
            audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
            
            # Check for silence
            rms = np.sqrt(np.mean(audio_np ** 2))
            if rms < self.silence_threshold:
                return None
            
            # Resample if needed
            if self.device_sample_rate != self.target_sample_rate:
                audio_np = self._resample_audio(
                    audio_np,
                    self.device_sample_rate,
                    self.target_sample_rate
                )
            
            return audio_np
            
        except Exception as e:
            logger.error(f"Error capturing audio: {e}")
            return None
    
    def transcribe(self, audio_data: np.ndarray) -> Optional[str]:
        """Transcribe audio data"""
        try:
            segments, info = self.asr_model.transcribe(
                audio_data,
                beam_size=self.config.get('beam_size', 1),
                vad_filter=self.config.get('vad_filter', True)
            )
            
            # Combine segments
            text = " ".join([segment.text for segment in segments]).strip()
            
            if text:
                logger.info(f"Transcribed: {text}")
                return text
            
            return None
            
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return None
    
    def run(self):
        """Main capture and transcribe loop"""
        logger.info("🎤 Starting adaptive ASR input...")
        
        try:
            while True:
                # Capture audio
                audio_chunk = self.capture_audio_chunk()
                
                if audio_chunk is not None:
                    # Transcribe
                    text = self.transcribe(audio_chunk)
                    
                    if text:
                        yield text
                
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            logger.info("Stopping ASR input...")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up resources"""
        if self.stream:
            try:
                self.stream.stop_stream()
                self.stream.close()
            except:
                pass
        
        if self.pyaudio_instance:
            try:
                self.pyaudio_instance.terminate()
            except:
                pass
        
        logger.info("ASR input cleaned up")


# For backward compatibility with existing code
class LocalASRInput(AdaptiveASRInput):
    """Backward compatible wrapper"""
    pass
