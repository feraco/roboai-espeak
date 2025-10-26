import asyncio
import io
import logging
import os
import tempfile
import time
import wave
from queue import Empty, Queue
from typing import Optional

import openai
import sounddevice as sd
import soundfile as sf
from inputs.base import SensorConfig
from inputs.base.loop import FuserInput
from providers.io_provider import IOProvider
from providers.sleep_ticker_provider import SleepTickerProvider


class LocalASRInput(FuserInput[str]):
    """
    Local Automatic Speech Recognition (ASR) input handler.

    This class manages local ASR using OpenAI Whisper API or Faster-Whisper for offline processing.
    It records audio from the microphone and converts it to text using the specified engine.
    """

    def __init__(self, config: SensorConfig = SensorConfig()):
        """
        Initialize LocalASRInput instance.
        """
        super().__init__(config)

        # Buffer for storing the final output
        self.messages: list[str] = []

        # Set IO Provider
        self.descriptor_for_LLM = "Voice"
        self.io_provider = IOProvider()

        # Buffer for storing messages
        self.message_buffer: Queue[str] = Queue()

        # Configuration
        self.engine = getattr(self.config, "engine", "openai-whisper")
        requested_sample_rate = getattr(self.config, "sample_rate", 16000)
        self.chunk_duration = getattr(self.config, "chunk_duration", 5)  # seconds
        self.silence_threshold = getattr(self.config, "silence_threshold", 0.01)
        self.min_audio_length = getattr(self.config, "min_audio_length", 1.0)  # seconds
        self.input_device = self._resolve_input_device(
            getattr(self.config, "input_device", None)
        )
        self.amplify_audio = getattr(self.config, "amplify_audio", 1.0)  # Audio amplification factor
        self.always_transcribe = getattr(self.config, "always_transcribe", False)
        self.rms_debug = getattr(self.config, "rms_debug", False)
        
        # Auto-detect supported sample rate if requested rate fails
        self.sample_rate = self._detect_supported_sample_rate(requested_sample_rate)
        
        # OpenAI configuration
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key and self.engine == "openai-whisper":
            logging.warning("OPENAI_API_KEY not found in environment variables. OpenAI Whisper will not work.")
        
        # Initialize OpenAI client if using OpenAI Whisper
        if self.engine == "openai-whisper" and self.openai_api_key:
            self.openai_client = openai.AsyncClient(api_key=self.openai_api_key)
        else:
            self.openai_client = None

        # Initialize Faster-Whisper if using local engine
        self.faster_whisper_model = None
        if self.engine == "faster-whisper":
            try:
                from faster_whisper import WhisperModel
                model_size = getattr(self.config, "model_size", "base")
                self.faster_whisper_model = WhisperModel(model_size, device="cpu", compute_type="int8")
                logging.info(f"Loaded Faster-Whisper model: {model_size}")
            except ImportError:
                logging.error("faster-whisper not installed. Install with: pip install faster-whisper")
                self.engine = "openai-whisper"  # Fallback to OpenAI

        # Audio recording state
        self.is_recording = False
        self.audio_buffer = []
        
        # Initialize sleep ticker provider
        self.global_sleep_ticker_provider = SleepTickerProvider()

        # Audio processing task will be started when the event loop is available
        self._audio_task = None

    def _resolve_input_device(self, device_config):
        """
        Resolve the input device to use for audio recording.
        """
        if device_config is not None:
            return device_config

        # Auto-select the first available input device
        try:
            import sounddevice as _sd
            devices = _sd.query_devices()

            # Find the first input device
            for idx, dev in enumerate(devices):
                if dev["max_input_channels"] > 0:
                    candidate = idx
                    break
            else:
                logging.warning("LocalASRInput: no input device found; will try default device (None)")
                return None

        except ImportError:
            logging.warning("LocalASRInput: sounddevice not available; will try default device (None)")
            return None
        except Exception as exc:
            # Unidentifiable error: let recording try default device
            logging.warning(
                "LocalASRInput: failed to query devices (%s); will try default (None)", exc
            )
            return None
        else:
            # Make sure the device has channels (sanity check)
            try:
                if devices[candidate]["max_input_channels"] <= 0:
                    logging.warning("LocalASRInput: auto-selected device has no input channels!")
                    return None
            except (IndexError, KeyError):
                pass

            logging.info(
                "LocalASRInput: auto-selected input device %s (%s)",
                candidate,
                devices[candidate]["name"],
            )
            return candidate

        logging.warning("LocalASRInput: no audio input device could be resolved; recording may fail")
        return None

    def _detect_supported_sample_rate(self, requested_rate: int) -> int:
        """
        Detect a supported sample rate for the audio device.
        Try the requested rate first, then fallback to common rates.
        
        Parameters
        ----------
        requested_rate : int
            The desired sample rate from config
            
        Returns
        -------
        int
            A supported sample rate
        """
        # Common sample rates to try in order of preference
        # Jetson Orin typically supports: 48000, 44100, 32000, 22050, 11025, 8000
        common_rates = [requested_rate, 48000, 44100, 32000, 22050, 16000, 11025, 8000]
        
        # Remove duplicates while preserving order
        rates_to_try = []
        seen = set()
        for rate in common_rates:
            if rate not in seen:
                rates_to_try.append(rate)
                seen.add(rate)
        
        for rate in rates_to_try:
            try:
                # Try to create a test stream with this rate
                test_stream = sd.InputStream(
                    samplerate=rate,
                    channels=1,
                    dtype='float32',
                    device=self.input_device,
                    blocksize=1024
                )
                test_stream.close()
                
                if rate != requested_rate:
                    logging.warning(
                        f"LocalASRInput: Requested sample rate {requested_rate} Hz not supported. "
                        f"Using {rate} Hz instead."
                    )
                else:
                    logging.info(f"LocalASRInput: Using sample rate {rate} Hz")
                
                return rate
                
            except Exception as e:
                logging.debug(f"LocalASRInput: Sample rate {rate} Hz not supported: {e}")
                continue
        
        # If all rates fail, default to 48000 (most common on modern hardware)
        logging.error(
            f"LocalASRInput: Could not detect supported sample rate. "
            f"Defaulting to 48000 Hz. Original error: {e}"
        )
        return 48000

    def _start_audio_processing(self):
        """Start the audio processing loop."""
        try:
            loop = asyncio.get_running_loop()
            if self._audio_task is None or self._audio_task.done():
                self._audio_task = loop.create_task(self._audio_processing_loop())
        except RuntimeError:
            # No event loop running, will start later
            pass

    async def _audio_processing_loop(self):
        """Main audio processing loop."""
        while True:
            try:
                # Record audio chunk
                audio_data = await self._record_audio_chunk()

                if audio_data is None:
                    logging.warning("LocalASRInput: failed to capture audio chunk")
                    await asyncio.sleep(0.2)
                    continue

                if len(audio_data) == 0:
                    logging.debug("LocalASRInput: captured empty audio chunk")
                    await asyncio.sleep(0.2)
                    continue

                has_speech = self._has_speech(audio_data)

                if has_speech or self.always_transcribe:
                    text = await self._transcribe_audio(audio_data)
                    if text and len(text.strip()) > 0:
                        cleaned = text.strip()
                        self.message_buffer.put(cleaned)
                        logging.info("=== ASR INPUT ===\n%s", cleaned)
                    else:
                        logging.debug("LocalASRInput: chunk produced no transcription")
                
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logging.error(f"Error in audio processing loop: {e}")
                await asyncio.sleep(1)

    async def _record_audio_chunk(self) -> Optional[bytes]:
        """Record a chunk of audio from the microphone."""
        try:
            # Record audio for the specified duration
            audio_data = sd.rec(
                int(self.sample_rate * self.chunk_duration),
                samplerate=self.sample_rate,
                channels=1,
                dtype='float32',
                device=self.input_device  # Use specified input device
            )
            sd.wait()  # Wait until recording is finished
            
            return audio_data.tobytes()
            
        except Exception as e:
            logging.error(f"Error recording audio: {e}")
            return None

    def _has_speech(self, audio_data: bytes) -> bool:
        """Check if audio data contains speech (not just silence)."""
        try:
            # Convert bytes to numpy array
            import numpy as np
            audio_array = np.frombuffer(audio_data, dtype=np.float32)
            
            # Calculate RMS (Root Mean Square) to detect audio level
            rms = np.sqrt(np.mean(audio_array**2))
            
            if self.rms_debug:
                logging.info(
                    "LocalASRInput RMS level: %.6f (threshold %.6f)",
                    rms,
                    self.silence_threshold,
                )

            # Optionally skip silence gating
            if self.always_transcribe:
                return True

            # Check if RMS is above silence threshold
            return rms > self.silence_threshold
            
        except Exception as e:
            logging.error(f"Error checking speech in audio: {e}")
            return False

    async def _transcribe_audio(self, audio_data: bytes) -> Optional[str]:
        """Transcribe audio data to text using the configured engine."""
        try:
            if self.engine == "openai-whisper" and self.openai_client:
                return await self._transcribe_with_openai(audio_data)
            elif self.engine == "faster-whisper" and self.faster_whisper_model:
                return await self._transcribe_with_faster_whisper(audio_data)
            else:
                logging.error(f"No valid ASR engine configured: {self.engine}")
                return None
                
        except Exception as e:
            logging.error(f"Error transcribing audio: {e}")
            return None

    async def _transcribe_with_openai(self, audio_data: bytes) -> Optional[str]:
        """Transcribe audio using OpenAI Whisper API."""
        try:
            # Create a temporary WAV file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                # Convert bytes to numpy array and save as WAV
                import numpy as np
                audio_array = np.frombuffer(audio_data, dtype=np.float32)
                sf.write(temp_file.name, audio_array, self.sample_rate)
                
                # Transcribe with OpenAI
                with open(temp_file.name, "rb") as audio_file:
                    transcript = await self.openai_client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        response_format="text"
                    )
                
                # Clean up temp file
                os.unlink(temp_file.name)
                
                return transcript.strip() if transcript else None
                
        except Exception as e:
            logging.error(f"Error with OpenAI Whisper: {e}")
            return None

    async def _transcribe_with_faster_whisper(self, audio_data: bytes) -> Optional[str]:
        """Transcribe audio using Faster-Whisper (local)."""
        try:
            # Convert bytes to numpy array
            import numpy as np
            audio_array = np.frombuffer(audio_data, dtype=np.float32)
            
            # Resample to 16kHz if needed (Whisper expects 16kHz)
            if self.sample_rate != 16000:
                try:
                    import scipy.signal
                    # Calculate resampling ratio
                    target_length = int(len(audio_array) * 16000 / self.sample_rate)
                    audio_array = scipy.signal.resample(audio_array, target_length)
                    logging.debug(f"Resampled audio from {self.sample_rate} Hz to 16000 Hz")
                except ImportError:
                    logging.warning(
                        f"scipy not available for resampling. Audio is {self.sample_rate} Hz "
                        f"but Whisper expects 16000 Hz. Install scipy for better accuracy: pip install scipy"
                    )
            
            # Amplify audio if needed
            if self.amplify_audio > 1.0:
                audio_array = audio_array * self.amplify_audio
                # Clip to prevent distortion
                audio_array = np.clip(audio_array, -1.0, 1.0)
            
            # Log audio stats for debugging
            rms = np.sqrt(np.mean(audio_array**2))
            logging.debug(f"Audio RMS level: {rms:.4f}, Amplification: {self.amplify_audio}x")
            
            # Transcribe with Faster-Whisper
            segments, info = self.faster_whisper_model.transcribe(
                audio_array,
                beam_size=getattr(self.config, "beam_size", 5),
                language="en",
                vad_filter=getattr(self.config, "vad_filter", True)
            )
            
            # Combine all segments
            text = " ".join([segment.text for segment in segments])
            
            return text.strip() if text else None
            
        except Exception as e:
            logging.error(f"Error with Faster-Whisper: {e}")
            return None

    async def _poll(self) -> Optional[str]:
        """
        Poll for new messages in the buffer. Always continue listening.
        """
        # Ensure audio processing is always running
        if self._audio_task is None or self._audio_task.done():
            logging.warning("LocalASRInput: Audio task was stopped or not started. Restarting audio processing loop.")
            self._start_audio_processing()

        # Loop until a message is available, but never exit
        while True:
            await asyncio.sleep(0.1)
            try:
                message = self.message_buffer.get_nowait()
                return message
            except Empty:
                # If the audio task has stopped, restart it
                if self._audio_task is None or self._audio_task.done():
                    logging.warning("LocalASRInput: Detected stopped audio task during polling. Restarting.")
                    self._start_audio_processing()
                continue

    async def _raw_to_text(self, raw_input: str) -> str:
        """
        Convert raw input to text format.

        Parameters
        ----------
        raw_input : str
            Raw input string to be converted

        Returns
        -------
        str
            Converted text
        """
        return raw_input

    async def raw_to_text(self, raw_input: str):
        """
        Convert raw input to processed text and manage buffer.

        Parameters
        ----------
        raw_input : str
            Raw input to be processed
        """
        pending_message = await self._raw_to_text(raw_input)
        if pending_message is None:
            if len(self.messages) != 0:
                # Skip sleep if there's already a message in the messages buffer
                self.global_sleep_ticker_provider.skip_sleep = True

        if pending_message is not None:
            if len(self.messages) == 0:
                self.messages.append(pending_message)
            else:
                self.messages[-1] = f"{self.messages[-1]} {pending_message}"

    def formatted_latest_buffer(self) -> Optional[str]:
        """
        Format and clear the latest buffer contents.

        Returns
        -------
        Optional[str]
            Formatted string of buffer contents or None if buffer is empty
        """
        if len(self.messages) == 0:
            return None

        result = f"""
INPUT: {self.descriptor_for_LLM}
// START
{self.messages[-1]}
// END
"""
        # Add to IO provider
        self.io_provider.add_input(
            self.descriptor_for_LLM, self.messages[-1], time.time()
        )
        self.io_provider.add_mode_transition_input(self.messages[-1])

        # Reset messages buffer
        self.messages = []
        return result