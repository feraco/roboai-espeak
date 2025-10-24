#!/usr/bin/env python3
"""
Audio System Auto-Detection and Repair for G1 Robot
Handles ALSA device discovery, sample rate detection, and fallback mechanisms
"""

import subprocess
import re
import logging
from typing import Dict, List, Tuple, Optional
import json

logger = logging.getLogger(__name__)


class AudioSystemFixer:
    """Detects and configures audio devices for optimal performance on G1"""
    
    def __init__(self):
        self.supported_sample_rates = [8000, 16000, 22050, 44100, 48000]
        self.alsa_devices = {}
        self.working_configs = []
        
    def run_command(self, cmd: str) -> Tuple[int, str, str]:
        """Execute shell command and return (returncode, stdout, stderr)"""
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            logger.error(f"Command timed out: {cmd}")
            return -1, "", "Timeout"
        except Exception as e:
            logger.error(f"Command failed: {cmd}, error: {e}")
            return -1, "", str(e)
    
    def detect_alsa_input_devices(self) -> Dict[str, List[Dict]]:
        """Parse arecord -l output to get available input devices"""
        returncode, stdout, stderr = self.run_command("arecord -l")
        
        if returncode != 0:
            logger.error(f"arecord failed: {stderr}")
            return {}
        
        devices = {}
        current_card = None
        
        for line in stdout.split('\n'):
            # Match: card 0: Device [USB2.0 Device], device 0: USB Audio [USB Audio]
            card_match = re.match(r'card (\d+): (\w+) \[(.*?)\]', line)
            if card_match:
                card_num = int(card_match.group(1))
                card_name = card_match.group(3)
                current_card = card_num
                if current_card not in devices:
                    devices[current_card] = {
                        'name': card_name,
                        'devices': []
                    }
            
            # Match device line
            device_match = re.search(r'device (\d+): (.*?) \[(.*?)\]', line)
            if device_match and current_card is not None:
                device_num = int(device_match.group(1))
                device_desc = device_match.group(3)
                devices[current_card]['devices'].append({
                    'device': device_num,
                    'description': device_desc,
                    'hw_id': f"hw:{current_card},{device_num}"
                })
        
        self.alsa_devices = devices
        return devices
    
    def detect_alsa_output_devices(self) -> Dict[str, List[Dict]]:
        """Parse aplay -l output to get available output devices"""
        returncode, stdout, stderr = self.run_command("aplay -l")
        
        if returncode != 0:
            logger.error(f"aplay failed: {stderr}")
            return {}
        
        devices = {}
        current_card = None
        
        for line in stdout.split('\n'):
            card_match = re.match(r'card (\d+): (\w+) \[(.*?)\]', line)
            if card_match:
                card_num = int(card_match.group(1))
                card_name = card_match.group(3)
                current_card = card_num
                if current_card not in devices:
                    devices[current_card] = {
                        'name': card_name,
                        'devices': []
                    }
            
            device_match = re.search(r'device (\d+): (.*?) \[(.*?)\]', line)
            if device_match and current_card is not None:
                device_num = int(device_match.group(1))
                device_desc = device_match.group(3)
                devices[current_card]['devices'].append({
                    'device': device_num,
                    'description': device_desc,
                    'hw_id': f"hw:{current_card},{device_num}"
                })
        
        return devices
    
    def test_sample_rate(self, hw_id: str, sample_rate: int, duration: float = 0.5) -> bool:
        """Test if a device supports a specific sample rate"""
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
            tmp_file = tmp.name
        
        try:
            # Try to record with this sample rate
            cmd = f"arecord -D {hw_id} -f S16_LE -r {sample_rate} -c 1 -d {duration} {tmp_file} 2>&1"
            returncode, stdout, stderr = self.run_command(cmd)
            
            os.unlink(tmp_file)
            
            if returncode == 0:
                return True
            
            # Check for specific errors
            combined_output = stdout + stderr
            if "invalid argument" in combined_output.lower():
                return False
            if "sample rate" in combined_output.lower():
                return False
                
            return False
            
        except Exception as e:
            logger.warning(f"Error testing sample rate {sample_rate} on {hw_id}: {e}")
            try:
                os.unlink(tmp_file)
            except:
                pass
            return False
    
    def get_supported_sample_rates(self, hw_id: str) -> List[int]:
        """Get list of supported sample rates for a device"""
        supported = []
        
        logger.info(f"Testing sample rates for {hw_id}...")
        
        for rate in self.supported_sample_rates:
            if self.test_sample_rate(hw_id, rate):
                supported.append(rate)
                logger.info(f"  ✅ {rate} Hz works")
            else:
                logger.info(f"  ❌ {rate} Hz failed")
        
        return supported
    
    def detect_pyaudio_devices(self) -> List[Dict]:
        """Enumerate PyAudio devices and their capabilities"""
        try:
            import pyaudio
            
            p = pyaudio.PyAudio()
            devices = []
            
            for i in range(p.get_device_count()):
                try:
                    info = p.get_device_info_by_index(i)
                    
                    device_info = {
                        'index': i,
                        'name': info['name'],
                        'max_input_channels': info['maxInputChannels'],
                        'max_output_channels': info['maxOutputChannels'],
                        'default_sample_rate': int(info['defaultSampleRate']),
                        'working_rates': []
                    }
                    
                    # Test sample rates for input devices
                    if info['maxInputChannels'] > 0:
                        for rate in self.supported_sample_rates:
                            try:
                                stream = p.open(
                                    format=pyaudio.paInt16,
                                    channels=1,
                                    rate=rate,
                                    input=True,
                                    input_device_index=i,
                                    frames_per_buffer=1024
                                )
                                stream.close()
                                device_info['working_rates'].append(rate)
                            except Exception:
                                continue
                    
                    devices.append(device_info)
                    
                except Exception as e:
                    logger.warning(f"Error querying PyAudio device {i}: {e}")
                    continue
            
            p.terminate()
            return devices
            
        except ImportError:
            logger.error("PyAudio not installed")
            return []
        except Exception as e:
            logger.error(f"Error detecting PyAudio devices: {e}")
            return []
    
    def find_best_input_device(self) -> Optional[Dict]:
        """Find the best working input device configuration"""
        # Priority order: USB mic > Camera mic > Jetson audio
        priority_keywords = [
            'USB2.0',
            'USB',
            'Camera',
            'UVC',
            'ADMAIF'
        ]
        
        alsa_devices = self.detect_alsa_input_devices()
        pyaudio_devices = self.detect_pyaudio_devices()
        
        best_config = None
        best_score = -1
        
        # Match ALSA devices with PyAudio devices
        for card_num, card_info in alsa_devices.items():
            for device in card_info['devices']:
                hw_id = device['hw_id']
                
                # Get supported sample rates
                supported_rates = self.get_supported_sample_rates(hw_id)
                
                if not supported_rates:
                    continue
                
                # Find corresponding PyAudio device
                pyaudio_index = None
                for pa_dev in pyaudio_devices:
                    if pa_dev['max_input_channels'] > 0:
                        # Try to match by name or by testing
                        if card_info['name'].lower() in pa_dev['name'].lower():
                            pyaudio_index = pa_dev['index']
                            break
                
                # Calculate priority score
                score = 0
                device_name = card_info['name'].lower()
                
                for idx, keyword in enumerate(priority_keywords):
                    if keyword.lower() in device_name:
                        score = len(priority_keywords) - idx
                        break
                
                # Prefer 16kHz support (optimal for ASR)
                if 16000 in supported_rates:
                    score += 10
                
                config = {
                    'card': card_num,
                    'device': device['device'],
                    'hw_id': hw_id,
                    'name': card_info['name'],
                    'description': device['description'],
                    'supported_rates': supported_rates,
                    'recommended_rate': 16000 if 16000 in supported_rates else supported_rates[0],
                    'pyaudio_index': pyaudio_index,
                    'score': score
                }
                
                self.working_configs.append(config)
                
                if score > best_score:
                    best_score = score
                    best_config = config
        
        return best_config
    
    def test_camera(self) -> Dict:
        """Test camera availability"""
        result = {
            'available': False,
            'device': None,
            'error': None
        }
        
        try:
            import cv2
            
            for i in range(3):
                cap = cv2.VideoCapture(i)
                if cap.isOpened():
                    ret, frame = cap.read()
                    if ret:
                        result['available'] = True
                        result['device'] = i
                        result['resolution'] = frame.shape
                        cap.release()
                        break
                cap.release()
                
        except ImportError:
            result['error'] = "OpenCV not installed"
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def test_ollama_vision(self) -> Dict:
        """Test Ollama Vision availability"""
        result = {
            'available': False,
            'models': [],
            'error': None
        }
        
        try:
            returncode, stdout, stderr = self.run_command("ollama list")
            
            if returncode == 0:
                # Parse model list
                for line in stdout.split('\n')[1:]:  # Skip header
                    if line.strip():
                        model_name = line.split()[0]
                        result['models'].append(model_name)
                        if 'llava' in model_name.lower() or 'vision' in model_name.lower():
                            result['available'] = True
            else:
                result['error'] = stderr
                
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def find_piper_voices(self) -> Dict:
        """Locate Piper voice files"""
        import os
        
        possible_paths = [
            os.path.expanduser("~/.local/share/piper/voices"),
            "/opt/piper/voices",
            "/usr/local/share/piper/voices",
            "./piper-voices",
            "../piper-voices"
        ]
        
        result = {
            'found': False,
            'path': None,
            'voices': []
        }
        
        for path in possible_paths:
            if os.path.exists(path):
                result['found'] = True
                result['path'] = path
                
                # Find .onnx files
                for root, dirs, files in os.walk(path):
                    for file in files:
                        if file.endswith('.onnx'):
                            result['voices'].append(os.path.join(root, file))
                
                if result['voices']:
                    break
        
        return result
    
    def run_full_diagnostic(self) -> Dict:
        """Run complete hardware diagnostic"""
        logger.info("=" * 60)
        logger.info("🤖 G1 AUDIO SYSTEM DIAGNOSTIC")
        logger.info("=" * 60)
        
        diagnostic = {
            'alsa_input': {},
            'alsa_output': {},
            'pyaudio_devices': [],
            'best_input': None,
            'camera': {},
            'ollama_vision': {},
            'piper_voices': {},
            'recommendations': {}
        }
        
        # Detect ALSA devices
        logger.info("\n📋 Detecting ALSA input devices...")
        diagnostic['alsa_input'] = self.detect_alsa_input_devices()
        
        logger.info("\n📋 Detecting ALSA output devices...")
        diagnostic['alsa_output'] = self.detect_alsa_output_devices()
        
        # Detect PyAudio devices
        logger.info("\n📋 Detecting PyAudio devices...")
        diagnostic['pyaudio_devices'] = self.detect_pyaudio_devices()
        
        # Find best input device
        logger.info("\n🎤 Finding best input device...")
        diagnostic['best_input'] = self.find_best_input_device()
        
        # Test camera
        logger.info("\n📷 Testing camera...")
        diagnostic['camera'] = self.test_camera()
        
        # Test Ollama Vision
        logger.info("\n👁️ Testing Ollama Vision...")
        diagnostic['ollama_vision'] = self.test_ollama_vision()
        
        # Find Piper voices
        logger.info("\n🔊 Locating Piper TTS voices...")
        diagnostic['piper_voices'] = self.find_piper_voices()
        
        # Generate recommendations
        self._generate_recommendations(diagnostic)
        
        return diagnostic
    
    def _generate_recommendations(self, diagnostic: Dict):
        """Generate configuration recommendations based on diagnostic"""
        recommendations = {}
        
        if diagnostic['best_input']:
            best = diagnostic['best_input']
            recommendations['asr_config'] = {
                'input_device': best['pyaudio_index'],
                'sample_rate': best['recommended_rate'],
                'hw_id': best['hw_id'],
                'device_name': best['name']
            }
        else:
            recommendations['asr_config'] = {
                'error': 'No working audio input device found'
            }
        
        if diagnostic['camera']['available']:
            recommendations['camera_config'] = {
                'camera_index': diagnostic['camera']['device'],
                'resolution': diagnostic['camera']['resolution']
            }
        else:
            recommendations['camera_config'] = {
                'error': diagnostic['camera'].get('error', 'Camera not available')
            }
        
        if diagnostic['ollama_vision']['available']:
            recommendations['vision_config'] = {
                'available': True,
                'recommended_model': next(
                    (m for m in diagnostic['ollama_vision']['models'] if 'llava' in m.lower()),
                    diagnostic['ollama_vision']['models'][0] if diagnostic['ollama_vision']['models'] else None
                )
            }
        
        if diagnostic['piper_voices']['found']:
            recommendations['tts_config'] = {
                'voice_dir': diagnostic['piper_voices']['path'],
                'available_voices': len(diagnostic['piper_voices']['voices'])
            }
        
        diagnostic['recommendations'] = recommendations
    
    def print_diagnostic_report(self, diagnostic: Dict):
        """Print human-readable diagnostic report"""
        print("\n" + "=" * 60)
        print("🤖 G1 HARDWARE DIAGNOSTIC REPORT")
        print("=" * 60)
        
        # Audio Input
        print("\n🎤 AUDIO INPUT DEVICES:")
        if diagnostic['best_input']:
            best = diagnostic['best_input']
            print(f"  ✅ Best device: {best['name']}")
            print(f"     Card: {best['card']}, Device: {best['device']}")
            print(f"     ALSA ID: {best['hw_id']}")
            print(f"     PyAudio Index: {best['pyaudio_index']}")
            print(f"     Recommended rate: {best['recommended_rate']} Hz")
            print(f"     Supported rates: {best['supported_rates']}")
        else:
            print("  ❌ No working audio input device found")
        
        # Show all working configs
        if len(self.working_configs) > 1:
            print(f"\n  📋 Alternative devices ({len(self.working_configs) - 1}):")
            for config in self.working_configs[1:]:
                print(f"     • {config['name']}: {config['hw_id']} @ {config['recommended_rate']}Hz")
        
        # Camera
        print("\n📷 CAMERA:")
        if diagnostic['camera']['available']:
            print(f"  ✅ Camera available at /dev/video{diagnostic['camera']['device']}")
            print(f"     Resolution: {diagnostic['camera']['resolution']}")
        else:
            error = diagnostic['camera'].get('error', 'Unknown error')
            print(f"  ❌ Camera not available: {error}")
        
        # Ollama Vision
        print("\n👁️ OLLAMA VISION:")
        if diagnostic['ollama_vision']['available']:
            print(f"  ✅ Ollama Vision available")
            print(f"     Models: {', '.join(diagnostic['ollama_vision']['models'])}")
        else:
            error = diagnostic['ollama_vision'].get('error', 'Ollama not running')
            print(f"  ❌ Ollama Vision not available: {error}")
        
        # Piper TTS
        print("\n🔊 PIPER TTS:")
        if diagnostic['piper_voices']['found']:
            print(f"  ✅ Piper voices found")
            print(f"     Path: {diagnostic['piper_voices']['path']}")
            print(f"     Available voices: {len(diagnostic['piper_voices']['voices'])}")
        else:
            print(f"  ❌ Piper voices not found")
        
        # Recommendations
        print("\n💡 CONFIGURATION RECOMMENDATIONS:")
        rec = diagnostic['recommendations']
        
        if 'asr_config' in rec and 'error' not in rec['asr_config']:
            asr = rec['asr_config']
            print(f"\n  ASR Configuration:")
            print(f"    input_device: {asr['input_device']}")
            print(f"    sample_rate: {asr['sample_rate']}")
            print(f"    # Device: {asr['device_name']} ({asr['hw_id']})")
        
        if 'camera_config' in rec and 'error' not in rec['camera_config']:
            cam = rec['camera_config']
            print(f"\n  Camera Configuration:")
            print(f"    camera_index: {cam['camera_index']}")
        
        print("\n" + "=" * 60)
    
    def generate_config_json(self, diagnostic: Dict, output_file: str = "audio_config.json"):
        """Generate JSON config file with recommendations"""
        import json
        
        with open(output_file, 'w') as f:
            json.dump(diagnostic, f, indent=2)
        
        logger.info(f"Configuration saved to {output_file}")


def main():
    """Run diagnostic as standalone script"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    fixer = AudioSystemFixer()
    diagnostic = fixer.run_full_diagnostic()
    fixer.print_diagnostic_report(diagnostic)
    fixer.generate_config_json(diagnostic)
    
    return diagnostic


if __name__ == "__main__":
    main()
