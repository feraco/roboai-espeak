import logging
import subprocess
from typing import Optional

from actions.base import ActionConfig, ActionConnector
from actions.speak.interface import SpeakInput


class EspeakTTSConnector(ActionConnector[SpeakInput]):
    """
    Espeak TTS connector for offline text-to-speech synthesis.
    Uses the espeak command line tool for speech synthesis.
    """

    def __init__(self, config: ActionConfig):
        super().__init__(config)
        self.logger = logging.getLogger(__name__)
        
        # Configuration with defaults
        self.voice = getattr(config, 'voice', 'en-us')
        self.rate = getattr(config, 'rate', 175)
        self.pitch = getattr(config, 'pitch', 50)
        self.volume = getattr(config, 'volume', 100)
        
        # Check if espeak is available
        self.espeak_available = self._check_espeak_availability()
        
        if not self.espeak_available:
            self.logger.warning("Espeak not found. Please install with: brew install espeak (macOS) or apt-get install espeak (Ubuntu)")
    
    def _check_espeak_availability(self) -> bool:
        """Check if espeak is available on the system."""
        try:
            result = subprocess.run(['espeak', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def _synthesize_with_espeak(self, text: str) -> bool:
        """
        Synthesize speech using espeak.
        
        Parameters
        ----------
        text : str
            Text to synthesize
            
        Returns
        -------
        bool
            True if synthesis was successful
        """
        try:
            cmd = [
                'espeak',
                f'-v{self.voice}',
                f'-s{self.rate}',
                f'-p{self.pitch}',
                f'-a{self.volume}',
                text
            ]
            
            self.logger.info(f"Running espeak command: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                self.logger.error(f"Espeak failed with return code {result.returncode}")
                self.logger.error(f"Stderr: {result.stderr}")
            else:
                self.logger.info("Espeak synthesis successful")
                
            return result.returncode == 0
            
        except Exception as e:
            self.logger.error(f"Espeak synthesis error: {str(e)}")
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
        self.logger.info(f"Espeak TTS speaking: {sentence}")
        self.logger.debug(f"Espeak settings - Voice: {self.voice}, Rate: {self.rate}, Pitch: {self.pitch}, Volume: {self.volume}")

        if not self.espeak_available:
            self.logger.error("Espeak is not available!")
            self.logger.info(f"[MOCK TTS] Would speak: {sentence}")
            return

        # Synthesize speech
        self.logger.info("Attempting to synthesize speech with espeak...")
        success = self._synthesize_with_espeak(sentence)
        
        if not success:
            self.logger.error(f"Failed to synthesize speech: {sentence}")

    def __call__(self, input_data: SpeakInput) -> None:
        """Synchronous wrapper for connect method."""
        import asyncio
        asyncio.run(self.connect(input_data))