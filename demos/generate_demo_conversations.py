#!/usr/bin/env python3
"""
Demo Conversation Generator for Astra Vein Receptionist Agent

This script simulates conversations with preset questions and saves the agent's
audio responses as WAV files for website demos.
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

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import agent components
from actions.speak.connector.piper_tts import PiperTTSConnector
from actions.speak.interface import SpeakInput
from actions.base import ActionConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Demo conversations - English, Spanish, and Russian
DEMO_CONVERSATIONS = [
    {
        "language": "en",
        "conversations": [
            {
                "id": "01_welcome",
                "question": "Hello, I'm new here. What services do you offer?",
                "context": "A new patient asking about services"
            },
            {
                "id": "02_office_hours",
                "question": "What are your office hours?",
                "context": "Patient asking about availability"
            },
            {
                "id": "03_location",
                "question": "Where are you located? I'm in Brooklyn.",
                "context": "Patient asking about locations"
            },
            {
                "id": "04_varicose_veins",
                "question": "Can you help with varicose veins?",
                "context": "Patient asking about treatment"
            },
            {
                "id": "05_appointment",
                "question": "How do I schedule an appointment?",
                "context": "Patient wants to book"
            },
            {
                "id": "06_doctor",
                "question": "Who is the doctor?",
                "context": "Patient asking about physician"
            },
        ]
    },
    {
        "language": "es",
        "conversations": [
            {
                "id": "01_bienvenida",
                "question": "Hola, ¿qué servicios ofrecen?",
                "context": "Spanish-speaking patient asking about services"
            },
            {
                "id": "02_horario",
                "question": "¿Cuál es su horario?",
                "context": "Spanish-speaking patient asking about hours"
            },
            {
                "id": "03_ubicacion",
                "question": "¿Dónde están ubicados?",
                "context": "Spanish-speaking patient asking about location"
            },
        ]
    },
    {
        "language": "ru",
        "conversations": [
            {
                "id": "01_privet",
                "question": "Здравствуйте, какие услуги вы предлагаете?",
                "context": "Russian-speaking patient asking about services"
            },
            {
                "id": "02_raspisanie",
                "question": "Какие у вас часы работы?",
                "context": "Russian-speaking patient asking about hours"
            },
        ]
    }
]

# System prompt for the agent
SYSTEM_PROMPT = """You are a helpful virtual assistant for Astra Vein Treatment Center. You are located in the waiting room to help patients with information about the practice, services, and appointments.

MULTI-LANGUAGE SUPPORT:
- You can understand and respond in English, Spanish, and Russian
- When someone speaks to you in Spanish, respond in Spanish
- When someone speaks to you in Russian, respond in Russian
- When someone speaks to you in English, respond in English
- Always use the appropriate TTS language in your speak action

PRACTICE INFORMATION:
- Name: Astra Vein Treatment Center
- Tagline: Vein Treatment Center Brooklyn and Bronx | Trusted Vein Doctors
- Core Promise: We Treat People, Not Symptoms
- Main Phone: (347) 934-9068

LOCATIONS:
1. Brooklyn Office: 4209A Avenue U, Brooklyn, NY 11234 - Phone: (347) 934-9068
2. Bronx Office: 869 East Tremont Ave, Bronx, NY 10460 - Phone: (929) 447-4563
3. Queens Office: 30-71 Steinway St, Astoria, NY 11103 - Phone: (929) 486-2201

OFFICE HOURS:
Monday to Friday: 9:00 AM to 6:00 PM
Saturday and Sunday: Closed

KEY PERSONNEL:
- Dr. George Bolotin, MD - Interventional Radiologist, double board-certified in Diagnostic and Interventional Radiology. Works at Brooklyn and Bronx locations.

SERVICES AND TREATMENTS:
Vein and Vascular Conditions: Varicose Veins, Spider Veins, Venous Insufficiency, Venous Stasis Ulcer/Wound Care, Hand Veins, Foot Veins, Circulation Problems, Deep Vein Thrombosis (DVT)
Treatment Methods: Endovenous Laser Ablation, Radiofrequency Ablation, Sclerotherapy, Microphlebectomy

Your role: Answer questions about the practice, services, doctors, and locations. Help patients understand conditions and treatments. Provide appointment booking information. Be warm, professional, and empathetic. Keep responses concise and helpful (2-3 sentences max).

IMPORTANT: Include the language code in your speak action:
- For English: {"speak": {"sentence": "Your response here", "language": "en"}}
- For Spanish: {"speak": {"sentence": "Su respuesta aquí", "language": "es"}}
- For Russian: {"speak": {"sentence": "Ваш ответ здесь", "language": "ru"}}
"""


class DemoConversationGenerator:
    def __init__(self, output_dir: str = "demo_conversations"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Ollama settings
        self.ollama_url = "http://localhost:11434"
        self.model = "llama3.1:8b"
        self.system_prompt = SYSTEM_PROMPT
        
        logging.info(f"Demo generator initialized. Output: {self.output_dir}")
        
        # Initialize TTS connector
        tts_config = ActionConfig(
            model_en="en_US-amy-medium",
            model_es="es_ES-davefx-medium",
            model_ru="ru_RU-dmitri-medium",
            model_path_en=None,
            model_path_es=None,
            model_path_ru=None,
            output_dir=str(self.output_dir),
            log_sentences=True,
            clear_on_speak=False,
        )
        self.tts = PiperTTSConnector(tts_config)
        
        logging.info(f"Demo generator initialized. Output: {self.output_dir}")

    async def generate_response(self, question: str, language: str, context: str) -> Dict:
        """Generate LLM response for a question"""
        
        # Build prompt with language context
        lang_names = {"en": "English", "es": "Spanish", "ru": "Russian"}
        prompt = f"""Someone is asking you a question in {lang_names[language]}.

Question: {question}

Context: {context}

Respond naturally in {lang_names[language]} using professional, helpful language. Keep it brief (2-3 sentences).

You must respond with a JSON object in this format:
{{"speak": {{"sentence": "your response here", "language": "{language}"}}}}

Response:"""

        logging.info(f"Generating response for: {question}")
        
        # Call Ollama API directly
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    "stream": False
                }
                
                async with session.post(f"{self.ollama_url}/api/chat", json=payload) as resp:
                    result = await resp.json()
                    
                    if "message" in result and "content" in result["message"]:
                        content = result["message"]["content"]
                        logging.info(f"LLM Response: {content}")
                        
                        # Try to extract JSON
                        json_match = re.search(r'\{[^}]*"speak"[^}]*\{[^}]*\}[^}]*\}', content, re.DOTALL)
                        if json_match:
                            try:
                                parsed = json.loads(json_match.group())
                                speak_data = parsed.get('speak', {})
                                sentence = speak_data.get('sentence', '')
                                return {
                                    'sentence': sentence,
                                    'language': speak_data.get('language', language)
                                }
                            except json.JSONDecodeError as e:
                                logging.error(f"Failed to parse JSON: {e}")
                        
                        # Fallback: extract sentence from any format
                        # Try to find "sentence": "..." pattern
                        sentence_match = re.search(r'"sentence"\s*:\s*"([^"]+)"', content, re.DOTALL)
                        if sentence_match:
                            return {'sentence': sentence_match.group(1), 'language': language}
                        
                        # Last resort: clean and use whole response
                        clean_content = re.sub(r'\{[^}]*\}', '', content).strip()
                        clean_content = clean_content.replace('"', '').replace('\n', ' ')
                        return {'sentence': clean_content if clean_content else content, 'language': language}
            
            logging.error(f"No response from Ollama")
            return {'sentence': '', 'language': language}
            
        except Exception as e:
            logging.error(f"Error generating response: {e}", exc_info=True)
            return {'sentence': '', 'language': language}

    def format_phone_for_speech(self, text: str) -> str:
        """Format phone numbers for natural speech (digit by digit)"""
        # Match phone patterns like (347) 934-9068 or 347-934-9068
        import re
        
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

    async def synthesize_audio(self, sentence: str, language: str, output_file: Path):
        """Synthesize speech and save to file"""
        
        # Format phone numbers for speech
        sentence = self.format_phone_for_speech(sentence)
        
        logging.info(f"Synthesizing [{language}]: {sentence}")
        
        # Create SpeakInput
        speak_input = SpeakInput(sentence=sentence, language=language)
        
        # Synthesize using Piper (this will create temp file in output_dir)
        audio_path = self.tts._synthesize_with_piper(sentence, language)
        
        if audio_path and os.path.exists(audio_path):
            # Move to final location
            shutil.move(audio_path, str(output_file))
            logging.info(f"✅ Saved: {output_file}")
            return True
        else:
            logging.error(f"❌ Failed to synthesize: {sentence}")
            return False

    async def generate_conversation(self, conv: Dict, language: str, index: int):
        """Generate a single conversation Q&A"""
        
        conv_id = conv['id']
        question = conv['question']
        context = conv['context']
        
        logging.info(f"\n{'='*60}")
        logging.info(f"Conversation: {conv_id}")
        logging.info(f"Question: {question}")
        logging.info(f"{'='*60}")
        
        # Generate response
        response_data = await self.generate_response(question, language, context)
        sentence = response_data['sentence']
        resp_lang = response_data['language']
        
        if not sentence:
            logging.warning(f"Empty response for {conv_id}")
            return None
        
        logging.info(f"Response [{resp_lang}]: {sentence}")
        
        # Create output filename
        output_file = self.output_dir / f"{language}_{conv_id}_response.wav"
        
        # Synthesize audio
        success = await self.synthesize_audio(sentence, resp_lang, output_file)
        
        if success:
            return {
                'id': conv_id,
                'language': language,
                'question': question,
                'response': sentence,
                'audio_file': str(output_file),
                'index': index
            }
        
        return None

    async def generate_all_demos(self):
        """Generate all demo conversations"""
        
        logging.info("🎬 Starting demo conversation generation...")
        
        all_results = []
        total = sum(len(lang['conversations']) for lang in DEMO_CONVERSATIONS)
        current = 0
        
        for lang_group in DEMO_CONVERSATIONS:
            language = lang_group['language']
            conversations = lang_group['conversations']
            
            logging.info(f"\n{'#'*60}")
            logging.info(f"Processing {language.upper()} conversations")
            logging.info(f"{'#'*60}")
            
            for conv in conversations:
                current += 1
                logging.info(f"\n[{current}/{total}] Processing...")
                
                result = await self.generate_conversation(conv, language, current)
                if result:
                    all_results.append(result)
                
                # Small delay between requests
                await asyncio.sleep(1)
        
        # Save manifest
        manifest_file = self.output_dir / "manifest.json"
        with open(manifest_file, 'w', encoding='utf-8') as f:
            json.dump({
                'generated_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                'total_conversations': len(all_results),
                'conversations': all_results
            }, f, indent=2, ensure_ascii=False)
        
        logging.info(f"\n{'='*60}")
        logging.info(f"✅ Generation complete!")
        logging.info(f"📁 Output directory: {self.output_dir}")
        logging.info(f"📊 Generated {len(all_results)} conversations")
        logging.info(f"📄 Manifest: {manifest_file}")
        logging.info(f"{'='*60}")
        
        return all_results


async def main():
    """Main entry point"""
    
    print("""
╔════════════════════════════════════════════════════════════╗
║  Astra Vein Receptionist - Demo Conversation Generator    ║
╚════════════════════════════════════════════════════════════╝
    """)
    
    generator = DemoConversationGenerator()
    
    try:
        results = await generator.generate_all_demos()
        
        print("\n" + "="*60)
        print("📋 SUMMARY")
        print("="*60)
        
        for lang in ['en', 'es', 'ru']:
            lang_results = [r for r in results if r['language'] == lang]
            print(f"\n{lang.upper()}: {len(lang_results)} conversations")
            for r in lang_results:
                print(f"  ✓ {r['id']}")
        
        print("\n" + "="*60)
        print(f"🎉 All demo conversations saved to: {generator.output_dir}")
        print("="*60)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Generation interrupted by user")
    except Exception as e:
        logging.error(f"Error: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())
