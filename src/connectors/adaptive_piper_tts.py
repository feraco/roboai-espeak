#!/usr/bin/env python3
"""
Adaptive Piper TTS Connector
Auto-detects paths, audio players, and handles platform differences
"""

import os
import sys
import subprocess
import platform
import logging
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class AdaptivePiperTTS:
    """
    Piper TTS connector with automatic path detection and platform adaptation
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize adaptive Piper TTS
        
        Args:
            config: Configuration dict with optional:
                - model: Voice model name (e.g., "en_US-ryan-medium")
                - model_path: Explicit path to .onnx file (None = auto-detect)
                - config_path: Explicit path to .onnx.json file (None = auto-detect)
                - working_dir: Working directory (None = auto-detect)
                - play_command: Audio player command (None = auto-detect)
                - piper_command: Piper executable name
                - output_dir: Directory for generated audio files
                - sample_rate: Output sample rate
        """
        self.config = config
        self.model_name = config.get('model', 'en_US-ryan-medium')
        self.sample_rate = config.get('sample_rate', 22050)
        self.output_dir = config.get('output_dir', 'audio_output')
        self.piper_command = config.get('piper_command', 'piper')
        
        # Auto-detect platform
        self.platform = platform.system().lower()
        logger.info(f"Platform detected: {self.platform}")
        
        # Initialize paths
        self.model_path = None
        self.config_path = None
        self.working_dir = None
        self.play_command = None
        
        # Run auto-detection
        self._auto_detect()
        
        # Create output directory
        os.makedirs(self.output_dir, exist_ok=True)
    
    def _find_voice_directories(self) -> list:
        """Find possible Piper voice directories"""
        home = str(Path.home())
        
        possible_paths = []
        
        if self.platform == 'linux':
            possible_paths = [
                os.path.join(home, '.local', 'share', 'piper', 'voices'),
                '/opt/piper/voices',
                '/usr/local/share/piper/voices',
                os.path.join(home, 'roboai', 'roboai-espeak', 'piper-voices'),
                './piper-voices',
                '../piper-voices',
            ]
        elif self.platform == 'darwin':  # macOS
            possible_paths = [
                './piper-voices',
                '../piper-voices',
                os.path.join(home, '.local', 'share', 'piper', 'voices'),
                '/usr/local/share/piper/voices',
            ]
        else:
            # Windows or other
            possible_paths = [
                './piper-voices',
                os.path.join(home, 'piper-voices'),
            ]
        
        return possible_paths
    
    def _find_voice_files(self) -> tuple:
        """
        Auto-detect voice model files
        Returns: (model_path, config_path, working_dir)
        """
        # If paths explicitly set in config, use them
        explicit_model = self.config.get('model_path')
        explicit_config = self.config.get('config_path')
        
        if explicit_model and explicit_config:
            if os.path.exists(explicit_model) and os.path.exists(explicit_config):
                working_dir = os.path.dirname(explicit_model)
                logger.info(f"Using explicit paths: {explicit_model}")
                return explicit_model, explicit_config, working_dir
        
        # Parse model name: "en_US-ryan-medium" -> ["en", "en_US", "ryan", "medium"]
        parts = self.model_name.replace('-', '_').split('_')
        if len(parts) >= 4:
            lang = parts[0]  # en
            locale = f"{parts[0]}_{parts[1]}"  # en_US
            voice = parts[2]  # ryan
            quality = parts[3]  # medium
        else:
            logger.error(f"Invalid model name format: {self.model_name}")
            return None, None, None
        
        # Search for voice files
        voice_dirs = self._find_voice_directories()
        
        for base_path in voice_dirs:
            if not os.path.exists(base_path):
                continue
            
            # Try structure: voices/en/en_US/ryan/medium/
            voice_path = os.path.join(base_path, lang, locale, voice, quality)
            
            if os.path.exists(voice_path):
                model_file = os.path.join(voice_path, f"{self.model_name}.onnx")
                config_file = os.path.join(voice_path, f"{self.model_name}.onnx.json")
                
                if os.path.exists(model_file) and os.path.exists(config_file):
                    logger.info(f"✅ Found Piper voice: {model_file}")
                    return model_file, config_file, voice_path
        
        logger.error(f"❌ Could not find Piper voice: {self.model_name}")
        logger.error(f"Searched in: {voice_dirs}")
        return None, None, None
    
    def _detect_audio_player(self) -> str:
        """Detect appropriate audio player for the platform"""
        # If explicitly set, use it
        explicit_command = self.config.get('play_command')
        if explicit_command:
            return explicit_command
        
        # Auto-detect based on platform and availability
        if self.platform == 'darwin':  # macOS
            return 'afplay {filename}'
        
        elif self.platform == 'linux':
            # Try to detect which player is available
            players = [
                ('aplay', 'aplay {filename}'),
                ('paplay', 'paplay {filename}'),
                ('ffplay', 'ffplay -nodisp -autoexit {filename}'),
                ('play', 'play {filename}'),  # SoX
            ]
            
            for cmd, template in players:
                try:
                    result = subprocess.run(
                        ['which', cmd],
                        capture_output=True,
                        timeout=2
                    )
                    if result.returncode == 0:
                        logger.info(f"✅ Found audio player: {cmd}")
                        return template
                except Exception:
                    continue
            
            logger.warning("No audio player found, defaulting to aplay")
            return 'aplay {filename}'
        
        else:
            # Windows or other
            return 'start {filename}'
    
    def _auto_detect(self):
        """Run complete auto-detection"""
        logger.info("🔍 Auto-detecting Piper TTS configuration...")
        
        # Detect voice files
        self.model_path, self.config_path, self.working_dir = self._find_voice_files()
        
        if not self.model_path:
            logger.error("❌ Piper voice files not found!")
            logger.error(f"Please install voice: {self.model_name}")
            logger.error(f"Download from: https://huggingface.co/rhasspy/piper-voices")
            raise FileNotFoundError(f"Piper voice not found: {self.model_name}")
        
        # Detect audio player
        self.play_command = self._detect_audio_player()
        logger.info(f"✅ Audio player: {self.play_command}")
        
        # Verify piper command
        try:
            result = subprocess.run(
                [self.piper_command, '--version'],
                capture_output=True,
                timeout=2
            )
            if result.returncode == 0:
                logger.info(f"✅ Piper executable found: {self.piper_command}")
            else:
                logger.warning(f"⚠️ Piper command may not be available: {self.piper_command}")
        except Exception as e:
            logger.warning(f"⚠️ Could not verify piper command: {e}")
    
    def synthesize(self, text: str, output_file: Optional[str] = None) -> Optional[str]:
        """
        Synthesize speech from text
        
        Args:
            text: Text to synthesize
            output_file: Output filename (optional, will generate if not provided)
            
        Returns:
            Path to generated audio file, or None on error
        """
        import time
        
        # Generate output filename if not provided
        if not output_file:
            timestamp = int(time.time() * 1000000)
            output_file = os.path.join(
                self.output_dir,
                f"speech_{os.getpid()}_{timestamp}.wav"
            )
        
        try:
            # Build piper command
            cmd = [
                self.piper_command,
                '--model', self.model_path,
                '--config', self.config_path,
                '--output_file', output_file
            ]
            
            # Add optional parameters
            if 'speaker_id' in self.config:
                cmd.extend(['--speaker', str(self.config['speaker_id'])])
            
            if 'length_scale' in self.config:
                cmd.extend(['--length_scale', str(self.config['length_scale'])])
            
            if 'noise_scale' in self.config:
                cmd.extend(['--noise_scale', str(self.config['noise_scale'])])
            
            if 'noise_w' in self.config:
                cmd.extend(['--noise_w', str(self.config['noise_w'])])
            
            # Run piper
            logger.debug(f"Running: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                input=text.encode('utf-8'),
                capture_output=True,
                timeout=30
            )
            
            if result.returncode == 0 and os.path.exists(output_file):
                logger.info(f"✅ Generated speech: {output_file}")
                return output_file
            else:
                logger.error(f"Piper failed: {result.stderr.decode()}")
                return None
                
        except Exception as e:
            logger.error(f"Error synthesizing speech: {e}")
            return None
    
    def speak(self, text: str) -> bool:
        """
        Synthesize and play speech
        
        Args:
            text: Text to speak
            
        Returns:
            True if successful, False otherwise
        """
        # Generate audio
        audio_file = self.synthesize(text)
        
        if not audio_file:
            return False
        
        # Play audio
        try:
            play_cmd = self.play_command.format(filename=audio_file)
            
            logger.debug(f"Playing: {play_cmd}")
            
            result = subprocess.run(
                play_cmd,
                shell=True,
                capture_output=True,
                timeout=30
            )
            
            if result.returncode == 0:
                logger.info(f"✅ Played audio: {audio_file}")
                
                # Clean up if configured
                if self.config.get('clear_on_speak', False):
                    try:
                        os.remove(audio_file)
                    except:
                        pass
                
                return True
            else:
                logger.error(f"Audio playback failed: {result.stderr.decode()}")
                return False
                
        except Exception as e:
            logger.error(f"Error playing audio: {e}")
            return False
    
    def get_config_summary(self) -> Dict[str, Any]:
        """Get summary of detected configuration"""
        return {
            'platform': self.platform,
            'model': self.model_name,
            'model_path': self.model_path,
            'config_path': self.config_path,
            'working_dir': self.working_dir,
            'play_command': self.play_command,
            'piper_command': self.piper_command,
            'output_dir': self.output_dir,
            'sample_rate': self.sample_rate
        }


def test_piper_tts():
    """Test Piper TTS with auto-detection"""
    logging.basicConfig(level=logging.INFO)
    
    config = {
        'model': 'en_US-ryan-medium',
        'model_path': None,  # Auto-detect
        'config_path': None,  # Auto-detect
        'play_command': None,  # Auto-detect
        'output_dir': 'test_audio_output',
        'sample_rate': 22050
    }
    
    try:
        tts = AdaptivePiperTTS(config)
        
        print("\n" + "=" * 60)
        print("🎵 PIPER TTS CONFIGURATION")
        print("=" * 60)
        
        summary = tts.get_config_summary()
        for key, value in summary.items():
            print(f"{key}: {value}")
        
        print("\n" + "=" * 60)
        print("Testing speech synthesis...")
        print("=" * 60)
        
        test_text = "Hello! This is a test of the Piper text to speech system."
        
        success = tts.speak(test_text)
        
        if success:
            print("✅ TTS test successful!")
        else:
            print("❌ TTS test failed!")
        
        return success
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == "__main__":
    success = test_piper_tts()
    sys.exit(0 if success else 1)
