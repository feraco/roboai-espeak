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
    Piper TTS connector for offline text-to-speech synthesis.
    
    This connector uses Piper TTS for completely offline speech synthesis.
    """

    def __init__(self, config: ActionConfig):
        super().__init__(config)
        self.logger = logging.getLogger(__name__)
        
        # Configuration with safe defaults
        self.model_path = getattr(config, 'model_path', '/usr/local/share/piper/voices/en_US-lessac-medium.onnx')
        self.config_path = getattr(config, 'config_path', '/usr/local/share/piper/voices/en_US-lessac-medium.onnx.json')
        self.speaker_id = getattr(config, 'speaker_id', 0)
        self.length_scale = getattr(config, 'length_scale', 1.0)
        self.noise_scale = getattr(config, 'noise_scale', 0.667)
        self.noise_w = getattr(config, 'noise_w', 0.8)
        self.sample_rate = getattr(config, 'sample_rate', 22050)
        self.log_sentences = getattr(config, 'log_sentences', False)
        
        # Check if Piper is available
        self.piper_available = self._check_piper_availability()
        
        if not self.piper_available:
            self.logger.warning("Piper TTS not available. Speech will be logged only.")

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

    def _synthesize_with_piper(self, text: str) -> Optional[str]:
        """
        Synthesize speech using Piper TTS.
        
        Parameters
        ----------
        text : str
            Text to synthesize
            
        Returns
        -------
        Optional[str]
            Path to the generated audio file, or None if synthesis failed
        """
        try:
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
                temp_dir, f"speech_{os.getpid()}_{time.time()}.wav"
            )

            # Build Piper command
            piper_cmd = getattr(self.config, 'piper_command', 'piper').split()
            model = getattr(self.config, 'model', self.model_path)
            cmd = piper_cmd + ['--model', model]

            config_path = getattr(self.config, 'config_path', self.config_path)
            if config_path:
                cmd.extend(['--config', config_path])

            # Add output file
            cmd.extend(['--output-file', output_path])
            
            # Debug logging
            self.logger.info(f"Running Piper command: {' '.join(cmd)}")
            
            # Add optional parameters
            if hasattr(self, 'speaker_id') and self.speaker_id is not None:
                cmd.extend(['--speaker', str(self.speaker_id)])
            if hasattr(self, 'length_scale'):
                cmd.extend(['--length_scale', str(self.length_scale)])
            if hasattr(self, 'noise_scale'):
                cmd.extend(['--noise_scale', str(self.noise_scale)])
            if hasattr(self, 'noise_w'):
                cmd.extend(['--noise_w', str(self.noise_w)])

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
        Process speech synthesis request.
        
        Parameters
        ----------
        input_data : SpeakInput
            Input containing the sentence to synthesize
        """
        sentence = input_data.action
        self.logger.info(f"Piper TTS speaking: {sentence}")
        if self.log_sentences:
            self.logger.info("=== TTS OUTPUT ===\n%s", sentence)

        if not self.piper_available:
            self.logger.info(f"[MOCK TTS] Would speak: {sentence}")
            return

        # Synthesize speech
        audio_path = self._synthesize_with_piper(sentence)

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