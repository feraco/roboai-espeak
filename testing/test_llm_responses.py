#!/usr/bin/env python3
"""
Simple LLM Response Tester - See what the LLM actually says

Direct test of LLM responses without full agent complexity.
"""

import sys
import asyncio
import aiohttp
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from runtime.single_mode.config import load_config
from fuser import Fuser

# Sample questions
QUESTIONS = [
    # General info
    "What services do you offer?",
    "Where is the office located?",
    "What are your office hours?",
    "How do I schedule an appointment?",
    "Do you accept walk-ins?",
    "Is Spanish language support available?",
    "What is the main phone number?",
    "Do you have multiple locations?",
    
    # Doctors and staff
    "Who is the main doctor here?",
    "Can you tell me about Dr. George Bolotin?",
    "Is Dr. Bolotin board-certified?",
    
    # Treatments
    "Do you treat varicose veins?",
    "What treatments do you offer for spider veins?",
    "Do you offer fibroid treatments?",
    "Is the treatment painful?",
    
    # Insurance
    "Do you accept insurance?",
    "Do you offer payment plans?",
    
    # Other
    "Are you approved as an Ambulatory Surgery Center?",
    "What makes Astra Vein Treatment Center unique?",
]


async def test_ollama_direct(config_name: str = "astra_vein_receptionist"):
    """Test Ollama responses directly via HTTP API."""
    
    print("="*80)
    print(f"TESTING {config_name.upper()} AGENT RESPONSES")
    print("="*80)
    
    # Load config
    print(f"\n📋 Loading config...")
    config = load_config(config_name)
    
    # Get system context
    fuser = Fuser(config)
    system_context = fuser.get_system_context()
    
    print(f"✅ Config loaded")
    print(f"   Agent: {config.name}")
    print(f"   System context: {len(system_context)} chars")
    
    # Get Ollama config
    model = config.cortex_llm._config.model
    base_url = config.cortex_llm._config.base_url
    
    print(f"   LLM: {model} at {base_url}")
    
    # Test connection
    print(f"\n🔌 Testing Ollama connection...")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{base_url}/api/tags") as resp:
                if resp.status == 200:
                    print(f"✅ Ollama is running")
                else:
                    print(f"❌ Ollama returned status {resp.status}")
                    return
    except Exception as e:
        print(f"❌ Cannot connect to Ollama: {e}")
        print(f"\nPlease start Ollama:")
        print(f"  ollama serve")
        return
    
    # Test each question
    print("\n" + "="*80)
    print("QUESTIONS & RESPONSES")
    print("="*80)
    
    async with aiohttp.ClientSession() as session:
        for i, question in enumerate(QUESTIONS, 1):
            print(f"\n{'─'*80}")
            print(f"[{i}/{len(QUESTIONS)}] ❓ {question}")
            print(f"{'─'*80}")
            
            # Create prompt
            user_prompt = f"""CURRENT INPUTS:
Voice Input: "{question}"

Someone is speaking to you. Answer their question professionally and helpfully.

Actions:"""
            
            # Prepare Ollama request
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_context},
                    {"role": "user", "content": user_prompt}
                ],
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "num_predict": 256
                }
            }
            
            try:
                # Call Ollama
                async with session.post(
                    f"{base_url}/api/chat",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as resp:
                    if resp.status != 200:
                        print(f"❌ Error: Status {resp.status}")
                        continue
                    
                    result = await resp.json()
                    raw_response = result.get("message", {}).get("content", "")
                    
                    # Try to parse JSON action
                    import json
                    try:
                        # Look for JSON in the response
                        if "{" in raw_response and "}" in raw_response:
                            start = raw_response.index("{")
                            end = raw_response.rindex("}") + 1
                            json_str = raw_response[start:end]
                            action = json.loads(json_str)
                            
                            if "speak" in action:
                                sentence = action["speak"].get("sentence", "")
                                print(f"🤖 AGENT: {sentence}")
                            else:
                                print(f"🤖 ACTION: {action}")
                        else:
                            print(f"🤖 RAW: {raw_response}")
                    except:
                        # If JSON parsing fails, show raw response
                        print(f"🤖 RAW: {raw_response}")
                    
            except asyncio.TimeoutError:
                print(f"⏱️  Timeout - LLM took too long")
            except Exception as e:
                print(f"❌ Error: {e}")
            
            # Small delay
            await asyncio.sleep(0.3)
    
    print("\n" + "="*80)
    print("✅ TESTING COMPLETE")
    print("="*80)


async def test_single_question(config_name: str, question: str):
    """Test just one question."""
    
    # Load config
    config = load_config(config_name)
    fuser = Fuser(config)
    system_context = fuser.get_system_context()
    
    model = config.cortex_llm._config.model
    base_url = config.cortex_llm._config.base_url
    
    print(f"\n❓ Question: {question}")
    print(f"🤖 Testing with {model}...\n")
    
    user_prompt = f"""CURRENT INPUTS:
Voice Input: "{question}"

Someone is speaking to you. Answer their question professionally and helpfully.

Actions:"""
    
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_context},
            {"role": "user", "content": user_prompt}
        ],
        "stream": False,
        "options": {"temperature": 0.7, "num_predict": 256}
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{base_url}/api/chat",
            json=payload,
            timeout=aiohttp.ClientTimeout(total=30)
        ) as resp:
            result = await resp.json()
            raw_response = result.get("message", {}).get("content", "")
            
            # Parse response
            import json
            try:
                if "{" in raw_response and "}" in raw_response:
                    start = raw_response.index("{")
                    end = raw_response.rindex("}") + 1
                    json_str = raw_response[start:end]
                    action = json.loads(json_str)
                    
                    if "speak" in action:
                        sentence = action["speak"].get("sentence", "")
                        print(f"💬 RESPONSE: {sentence}\n")
                    else:
                        print(f"📋 ACTION: {action}\n")
                else:
                    print(f"📝 RAW: {raw_response}\n")
            except:
                print(f"📝 RAW: {raw_response}\n")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test agent LLM responses")
    parser.add_argument("config", nargs="?", default="astra_vein_receptionist",
                       help="Agent config name")
    parser.add_argument("-q", "--question", help="Test a single question")
    
    args = parser.parse_args()
    
    if args.question:
        asyncio.run(test_single_question(args.config, args.question))
    else:
        asyncio.run(test_ollama_direct(args.config))


if __name__ == "__main__":
    main()
