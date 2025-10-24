#!/usr/bin/env python3
"""
G1 Hardware Startup Check
Validates all hardware components before starting the agent
"""

import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.audio_system_fixer import AudioSystemFixer

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def check_hardware() -> bool:
    """
    Run complete hardware check
    Returns True if all critical components are OK
    """
    
    print("\n" + "=" * 70)
    print("🤖 G1 HARDWARE STARTUP CHECK")
    print("=" * 70)
    
    all_ok = True
    
    # Run diagnostic
    fixer = AudioSystemFixer()
    diagnostic = fixer.run_full_diagnostic()
    
    # Check microphone
    print("\n🎤 MICROPHONE:")
    if diagnostic['best_input']:
        best = diagnostic['best_input']
        print(f"  ✅ OK - {best['name']}")
        print(f"     Device: {best['hw_id']}")
        print(f"     Sample rate: {best['recommended_rate']} Hz")
    else:
        print("  ❌ FAIL - No working microphone found")
        all_ok = False
    
    # Check speaker
    print("\n🔊 SPEAKER:")
    if diagnostic['alsa_output']:
        print(f"  ✅ OK - {len(diagnostic['alsa_output'])} output device(s) found")
        for card_num, card_info in diagnostic['alsa_output'].items():
            print(f"     Card {card_num}: {card_info['name']}")
    else:
        print("  ❌ FAIL - No audio output device found")
        all_ok = False
    
    # Check camera
    print("\n📷 CAMERA:")
    if diagnostic['camera']['available']:
        print(f"  ✅ OK - Camera at /dev/video{diagnostic['camera']['device']}")
        print(f"     Resolution: {diagnostic['camera']['resolution']}")
    else:
        error = diagnostic['camera'].get('error', 'Not available')
        print(f"  ⚠️  WARNING - Camera not available: {error}")
        print("     (Vision features will be disabled)")
    
    # Check Ollama LLM
    print("\n🧠 OLLAMA LLM:")
    if diagnostic['ollama_vision']['models']:
        print(f"  ✅ OK - Ollama running")
        print(f"     Models: {', '.join(diagnostic['ollama_vision']['models'][:3])}")
    else:
        print("  ❌ FAIL - Ollama not running or no models available")
        print("     Start Ollama: systemctl start ollama")
        all_ok = False
    
    # Check Ollama Vision
    print("\n👁️  OLLAMA VISION:")
    if diagnostic['ollama_vision']['available']:
        vision_models = [m for m in diagnostic['ollama_vision']['models'] 
                        if 'llava' in m.lower() or 'vision' in m.lower()]
        print(f"  ✅ OK - Vision model available: {vision_models[0]}")
    else:
        print("  ⚠️  WARNING - No vision model found")
        print("     Install: ollama pull llava-llama3")
        print("     (Vision features will be disabled)")
    
    # Check Piper TTS
    print("\n🎵 PIPER TTS:")
    if diagnostic['piper_voices']['found']:
        print(f"  ✅ OK - Piper voices found")
        print(f"     Path: {diagnostic['piper_voices']['path']}")
        print(f"     Voices: {len(diagnostic['piper_voices']['voices'])}")
    else:
        print("  ❌ FAIL - Piper voices not found")
        print("     Install voices or check path")
        all_ok = False
    
    # Print configuration recommendation
    print("\n" + "=" * 70)
    print("📝 RECOMMENDED CONFIGURATION:")
    print("=" * 70)
    
    rec = diagnostic['recommendations']
    
    if 'asr_config' in rec and 'error' not in rec['asr_config']:
        asr = rec['asr_config']
        print("\nASR Input Settings:")
        print(f"  input_device: {asr['input_device']}")
        print(f"  sample_rate: {asr['sample_rate']}")
        print(f"  # Using: {asr['device_name']} ({asr['hw_id']})")
    
    if 'camera_config' in rec and 'error' not in rec['camera_config']:
        cam = rec['camera_config']
        print("\nCamera Settings:")
        print(f"  camera_index: {cam['camera_index']}")
    
    if 'vision_config' in rec:
        print("\nVision Settings:")
        if rec['vision_config'].get('available'):
            print(f"  model: {rec['vision_config']['recommended_model']}")
        else:
            print("  # Vision disabled - no model available")
    
    if 'tts_config' in rec:
        tts = rec['tts_config']
        print("\nTTS Settings:")
        print(f"  voice_dir: {tts['voice_dir']}")
    
    # Final status
    print("\n" + "=" * 70)
    if all_ok:
        print("✅ ALL SYSTEMS GO - Ready to start agent")
        print("=" * 70)
        return True
    else:
        print("❌ HARDWARE CHECK FAILED - Fix issues before starting")
        print("=" * 70)
        return False


if __name__ == "__main__":
    success = check_hardware()
    sys.exit(0 if success else 1)
