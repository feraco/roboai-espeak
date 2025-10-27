import logging
import asyncio
import os
import subprocess
import tempfile
import time
from typing import Optional

from actions.base import ActionConfig, ActionConnector
from actions.speak.interface import SpeakInput


class PiperTTSConnector(ActionConnector[SpeakInput]):
    """
    Piper TTS connector for offline text-to-speech synthesis with multi-language support.
    
    This connector uses Piper TTS for completely offline speech synthesis
    and automatically selects the appropriate voice model based on the language.
    """

    def __init__(self, config: ActionConfig):
        super().__init__(config)
        self.logger = logging.getLogger(__name__)
        
        # Language-specific voice models
        self.voice_models = {
            "en": {
                "model": getattr(config, 'model_en', 'en_US-ryan-medium'),
                "path": getattr(config, 'model_path_en', None),
            },
            "es": {
                "model": getattr(config, 'model_es', 'es_ES-claudia-medium'),
                "path": getattr(config, 'model_path_es', None),
            },
            "ru": {
                "model": getattr(config, 'model_ru', 'ru_RU-dmitri-medium'),
                "path": getattr(config, 'model_path_ru', None),
            }
        }
        
        # Common configuration
        self.speaker_id = getattr(config, 'speaker_id', 0)
        self.length_scale = getattr(config, 'length_scale', 1.0)
        self.noise_scale = getattr(config, 'noise_scale', 0.667)
        self.noise_w = getattr(config, 'noise_w', 0.8)
        self.sample_rate = getattr(config, 'sample_rate', 22050)
        self.log_sentences = getattr(config, 'log_sentences', False)
        
        # Auto-detect voice model paths
        self._detect_voice_paths()
        
        # Check if Piper is available
        self.piper_available = self._check_piper_availability()
        
        if not self.piper_available:
            self.logger.warning("Piper TTS not available. Speech will be logged only.")

    def _detect_voice_paths(self):
        """Auto-detect voice model paths in common locations."""
        search_paths = [
            "~/piper_voices",
            "./piper_voices", 
            "./piper-voices",
            "/usr/local/share/piper/voices",
            "~/.local/share/piper/voices"
        ]
        
        for lang, voice_info in self.voice_models.items():
            if voice_info["path"]:
                continue  # Already configured
                
            model_name = voice_info["model"]
            
            # Try to find the model file
            for search_path in search_paths:
                expanded_path = os.path.expanduser(search_path)
                if os.path.exists(expanded_path):
                    # Look for .onnx file
                    model_file = os.path.join(expanded_path, f"{model_name}.onnx")
                    if os.path.exists(model_file):
                        voice_info["path"] = model_file
                        self.logger.info(f"Found {lang} voice model: {model_file}")
                        break
            
            if not voice_info["path"]:
                # Fallback to default English model for missing languages
                if lang != "en":
                    self.logger.warning(f"Voice model for {lang} not found, will use English fallback")
                    voice_info["path"] = self.voice_models["en"]["path"]

    def _check_piper_availability(self) -> bool:
        """Check if Piper TTS is available on the system."""
        try:
            # First try the 'piper' command directly
            result = subprocess.run(['piper', '--help'], 
                                  capture_output=True, text=True, timeout=5)
            self.logger.info(f"Piper version check output: {result.stdout}, error: {result.stderr}, returncode: {result.returncode}")
            return True  # If we get here, piper is available
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
            try:
                # Try python -m piper as fallback
                result = subprocess.run(['python', '-m', 'piper', '--help'], 
                                      capture_output=True, text=True, timeout=5)
                return True  # If we get here, piper is available via python -m
            except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
                return False

    def _synthesize_with_piper(self, text: str, language: str = "en") -> Optional[str]:
        """
        Synthesize speech using Piper TTS with language-specific voice.
        
        Parameters
        ----------
        text : str
            Text to synthesize
        language : str
            Language code (en, es, ru)
            
        Returns
        -------
        Optional[str]
            Path to the generated audio file, or None if synthesis failed
        """
        try:
            # Get the appropriate voice model for the language
            voice_info = self.voice_models.get(language, self.voice_models["en"])
            model_path = voice_info["path"]
            
            if not model_path or not os.path.exists(model_path):
                self.logger.warning(f"Voice model for language '{language}' not found, using English fallback")
                model_path = self.voice_models["en"]["path"]
                if not model_path or not os.path.exists(model_path):
                    self.logger.error("No voice models available")
                    return None
            
            # Resolve working directory and output directory
            working_dir = getattr(self.config, 'working_dir', None)
            output_dir = getattr(self.config, 'output_dir', 'audio_output')

            base_dir = os.path.abspath(working_dir) if working_dir else os.getcwd()
            if os.path.isabs(output_dir):
                temp_dir = output_dir
            else:
                temp_dir = os.path.join(base_dir, output_dir)
            os.makedirs(temp_dir, exist_ok=True)
            output_path = os.path.join(
                temp_dir, f"speech_{language}_{os.getpid()}_{time.time()}.wav"
            )

            # Build Piper command
            piper_cmd = getattr(self.config, 'piper_command', 'piper').split()
            cmd = piper_cmd + ['-m', model_path]

            # Add output file (use -f for Anaconda piper)
            cmd.extend(['-f', output_path])
            
            # Add optional parameters
            if hasattr(self, 'speaker_id') and self.speaker_id is not None:
                cmd.extend(['-s', str(self.speaker_id)])
            if hasattr(self, 'length_scale'):
                cmd.extend(['--length-scale', str(self.length_scale)])
            if hasattr(self, 'noise_scale'):
                cmd.extend(['--noise-scale', str(self.noise_scale)])
            if hasattr(self, 'noise_w'):
                cmd.extend(['--noise-w-scale', str(self.noise_w)])

            # Debug logging
            self.logger.info(f"Synthesizing in {language} with model: {model_path}")
            self.logger.info(f"Running Piper command: {' '.join(cmd)}")
            
            # Run Piper
            process = subprocess.run(
                cmd,
                input=text,
                text=True,
                capture_output=True,
                timeout=60,
                cwd=working_dir
            )

            if process.returncode == 0:
                self.logger.info(f"Piper TTS synthesis successful: {output_path}")
                return output_path
            else:
                self.logger.error(f"Piper TTS failed: {process.stderr}")
                # Clean up failed file
                if os.path.exists(output_path):
                    os.unlink(output_path)
                return None

        except subprocess.TimeoutExpired:
            self.logger.error("Piper TTS synthesis timed out")
            return None
        except Exception as e:
            self.logger.error(f"Piper TTS synthesis error: {str(e)}")
            return None

    def _play_audio(self, audio_path: str) -> bool:
        """
        Play audio file using system audio player.
        
        Parameters
        ----------
        audio_path : str
            Path to the audio file
            
        Returns
        -------
        bool
            True if playback was successful, False otherwise
        """
        try:
            # Try different audio players based on platform
            if os.uname().sysname == 'Darwin':  # macOS
                players = ['afplay']
            else:  # Linux and others
                players = ['aplay', 'paplay', 'play', 'ffplay']
            
            for player in players:
                try:
                    result = subprocess.run([player, audio_path], 
                                          capture_output=True, timeout=10)
                    if result.returncode == 0:
                        self.logger.info(f"Audio played successfully with {player}")
                        return True
                except (FileNotFoundError, subprocess.TimeoutExpired):
                    continue
            
            self.logger.warning("No suitable audio player found")
            return False
            
        except Exception as e:
            self.logger.error(f"Audio playback error: {str(e)}")
            return False

    async def connect(self, input_data: SpeakInput) -> None:
        """
        Process speech synthesis request with language support.
        
        Parameters
        ----------
        input_data : SpeakInput
            Input containing the sentence to synthesize and language
        """
        sentence = input_data.sentence
        language = getattr(input_data, 'language', 'en') or 'en'  # Default to English
        
        self.logger.info(f"Piper TTS speaking in {language}: {sentence}")
        if self.log_sentences:
            self.logger.info("=== TTS OUTPUT ===\nLanguage: %s\nText: %s", language, sentence)

        if not self.piper_available:
            self.logger.info(f"[MOCK TTS] Would speak in {language}: {sentence}")
            return

        # Synthesize speech with appropriate language model
        audio_path = self._synthesize_with_piper(sentence, language)

        if audio_path:
            # Play the audio and wait for completion
            success = self._play_audio(audio_path)
            
            # Add a small delay to ensure audio completes
            await asyncio.sleep(0.2)
            
            # Clean up temporary file and any old files
            try:
                # Clean up the current file
                os.unlink(audio_path)

                temp_dir = os.path.dirname(audio_path)
                current_time = time.time()
                for f in os.listdir(temp_dir):
                    if f.startswith("speech_") and f.endswith(".wav"):
                        file_path = os.path.join(temp_dir, f)
                        # Remove files older than 60 seconds
                        if current_time - os.path.getctime(file_path) > 60:
                            try:
                                os.unlink(file_path)
                            except OSError:
                                pass
            except OSError:
                pass

            if not success:
                self.logger.warning(f"Audio synthesis succeeded but playback failed: {sentence}")
        else:
            self.logger.error(f"Failed to synthesize speech: {sentence}")

    def __call__(self, input_data: SpeakInput) -> None:
        """
        Synchronous wrapper for connect method.
        
        Parameters
        ----------
        input_data : SpeakInput
            Input containing the sentence to synthesize
        """
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're already in an async context, create a task
                asyncio.create_task(self.connect(input_data))
            else:
                # If not in async context, run the coroutine
                loop.run_until_complete(self.connect(input_data))
        except RuntimeError:
            # No event loop, create a new one
            asyncio.run(self.connect(input_data))