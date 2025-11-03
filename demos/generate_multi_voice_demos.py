#!/usr/bin/env python3
"""
Multi-Voice Demo Generator for Astra Vein Receptionist Agent

Generates demo WAV files with multiple female voice options.
"""

import asyncio
import os
import sys
import json
import re
import time
import shutil
from pathlib import Path
from typing import List, Dict
import logging
import aiohttp
import subprocess

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Voice configurations - female voices with different characteristics
VOICE_CONFIGS = {
    "amy": {
        "model": "en_US-amy-medium",
        "description": "Amy - Clear, professional female voice (default)",
        "speaker_id": 0
    },
    "lessac": {
        "model": "en_US-lessac-medium",
        "description": "Lessac - Warm, expressive female voice",
        "speaker_id": 0
    },
    "libritts_female_1": {
        "model": "en_US-libritts-high",
        "description": "LibriTTS Female #1 - Natural conversational voice",
        "speaker_id": 200  # Female speaker
    },
    "libritts_female_2": {
        "model": "en_US-libritts-high",
        "description": "LibriTTS Female #2 - Professional mature voice",
        "speaker_id": 446  # Female speaker
    },
    "libritts_female_3": {
        "model": "en_US-libritts-high",
        "description": "LibriTTS Female #3 - Bright, friendly voice",
        "speaker_id": 121  # Female speaker
    }
}

# Sample conversations for demo
DEMO_CONVERSATIONS = [
    {
        "id": "01_welcome",
        "question": "Hello, I'm new here. What services do you offer?",
        "response": "Welcome to Astra Vein Treatment Center! We specialize in diagnosing and treating various vein and vascular conditions, including varicose veins, spider veins, and circulation problems."
    },
    {
        "id": "02_office_hours",
        "question": "What are your office hours?",
        "response": "Our office hours are Monday to Friday from 9:00 AM to 6:00 PM. We're closed on Saturdays and Sundays."
    },
    {
        "id": "03_location",
        "question": "Where are you located? I'm in Brooklyn.",
        "response": "We have three locations in the NYC area, but our Brooklyn office is conveniently located at 4209A Avenue U. You're already close by!"
    },
    {
        "id": "04_phone",
        "question": "What's your phone number?",
        "response": "You can reach our main office at 3 4 7 9 3 4 9 0 6 8. Our staff will be happy to assist you."
    },
    {
        "id": "05_doctor",
        "question": "Who is the doctor?",
        "response": "Our main doctor is Dr. George Bolotin, MD, an interventional radiologist who specializes in vein and vascular conditions."
    }
]


class MultiVoiceDemoGenerator:
    def __init__(self, output_dir: str = "demo_multi_voice"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Find piper executable
        self.piper_path = self._find_piper()
        
        # Find voice models
        self.voice_dir = Path("piper_voices")
        
        logging.info(f"Multi-voice demo generator initialized")
        logging.info(f"Piper: {self.piper_path}")
        logging.info(f"Output: {self.output_dir}")
    
    def _find_piper(self) -> str:
        """Find piper executable"""
        paths = [
            "/opt/anaconda3/bin/piper",
            "/usr/local/bin/piper",
            shutil.which("piper")
        ]
        
        for path in paths:
            if path and os.path.exists(path):
                return path
        
        raise RuntimeError("Piper executable not found")
    
    def format_phone_for_speech(self, text: str) -> str:
        """Format phone numbers for natural speech (digit by digit)"""
        # Match phone patterns like (347) 934-9068 or 347-934-9068
        def replace_phone(match):
            phone = match.group(0)
            # Remove formatting
            digits = re.sub(r'[^\d]', '', phone)
            # Convert to space-separated digits
            return ' '.join(digits)
        
        # Pattern for various phone formats
        phone_pattern = r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
        text = re.sub(phone_pattern, replace_phone, text)
        
        return text
    
    def synthesize_with_piper(self, text: str, voice_name: str, output_file: Path) -> bool:
        """Synthesize speech with specified voice"""
        
        voice_config = VOICE_CONFIGS[voice_name]
        model_name = voice_config["model"]
        speaker_id = voice_config["speaker_id"]
        
        # Find model file
        model_path = None
        for search_dir in [self.voice_dir, Path("./piper_voices"), Path(".")]:
            candidate = search_dir / f"{model_name}.onnx"
            if candidate.exists():
                model_path = candidate
                break
        
        if not model_path:
            logging.error(f"Model not found: {model_name}")
            return False
        
        # Format phone numbers
        text = self.format_phone_for_speech(text)
        
        logging.info(f"Synthesizing with {voice_name}: {text[:50]}...")
        
        # Run piper
        cmd = [
            self.piper_path,
            "-m", str(model_path),
            "-f", str(output_file),
            "-s", str(speaker_id)
        ]
        
        try:
            result = subprocess.run(
                cmd,
                input=text,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0 and output_file.exists():
                logging.info(f"✅ Saved: {output_file}")
                return True
            else:
                logging.error(f"Piper failed: {result.stderr}")
                return False
                
        except Exception as e:
            logging.error(f"Error running Piper: {e}")
            return False
    
    def generate_all_demos(self):
        """Generate demo files for all voices"""
        
        print("\n" + "="*70)
        print("🎤 MULTI-VOICE DEMO GENERATOR")
        print("="*70 + "\n")
        
        manifest = {
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "voices": {},
            "conversations": DEMO_CONVERSATIONS
        }
        
        total_generated = 0
        
        for voice_name, voice_config in VOICE_CONFIGS.items():
            print(f"\n{'#'*70}")
            print(f"Voice: {voice_config['description']}")
            print(f"{'#'*70}\n")
            
            voice_manifest = {
                "description": voice_config["description"],
                "model": voice_config["model"],
                "speaker_id": voice_config["speaker_id"],
                "files": []
            }
            
            for idx, conv in enumerate(DEMO_CONVERSATIONS, 1):
                conv_id = conv["id"]
                response = conv["response"]
                
                print(f"[{idx}/{len(DEMO_CONVERSATIONS)}] {conv_id}...")
                
                # Generate filename
                output_file = self.output_dir / f"{voice_name}_{conv_id}.wav"
                
                # Synthesize
                success = self.synthesize_with_piper(response, voice_name, output_file)
                
                if success:
                    voice_manifest["files"].append({
                        "conversation_id": conv_id,
                        "file": str(output_file),
                        "question": conv["question"],
                        "response": response
                    })
                    total_generated += 1
                
                # Small delay
                time.sleep(0.5)
            
            manifest["voices"][voice_name] = voice_manifest
        
        # Save manifest
        manifest_file = self.output_dir / "manifest.json"
        with open(manifest_file, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        print("\n" + "="*70)
        print("✅ GENERATION COMPLETE!")
        print("="*70)
        print(f"📁 Output directory: {self.output_dir}")
        print(f"🎵 Generated {total_generated} audio files across {len(VOICE_CONFIGS)} voices")
        print(f"📄 Manifest: {manifest_file}")
        print("="*70 + "\n")
        
        # Print voice comparison guide
        print("\n🎤 VOICE COMPARISON GUIDE:")
        print("-" * 70)
        for voice_name, config in VOICE_CONFIGS.items():
            print(f"  {voice_name}: {config['description']}")
        print("-" * 70)


def main():
    generator = MultiVoiceDemoGenerator()
    generator.generate_all_demos()


if __name__ == "__main__":
    main()
