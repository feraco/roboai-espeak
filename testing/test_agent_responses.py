#!/usr/bin/env python3
"""
Test Agent Responses - Preview what the agent would say to sample questions

This script tests the agent's responses without running the full agent loop
(no audio input/output, no TTS). It directly queries the LLM to see responses.
"""

import sys
import asyncio
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from runtime.single_mode.config import load_config
from fuser import Fuser

# Sample questions from demo_questions_doctors_office.py
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
    "Is parking available at the office?",
    "Do you offer telemedicine appointments?",

    # Doctors and staff
    "Who is the main doctor here?",
    "Can you tell me about Dr. George Bolotin?",
    "Are there other doctors or staff I can speak to?",
    "Is Dr. Bolotin board-certified?",
    "What are the qualifications of your staff?",

    # Treatments and conditions
    "Do you treat varicose veins?",
    "What treatments do you offer for spider veins?",
    "Do you provide wound care for venous ulcers?",
    "Can you help with circulation problems?",
    "Do you treat deep vein thrombosis (DVT)?",
    "What methods do you use for vein treatment?",
    "Do you offer fibroid treatments?",
    "Are your procedures outpatient?",
    "Is the treatment painful?",
    "How long does recovery take?",

    # Insurance and payment
    "Do you accept insurance?",
    "What payment methods are accepted?",
    "Do you offer payment plans?",

    # Patient experience
    "Is the office wheelchair accessible?",
    "How long is the typical wait time?",
    "What should I bring to my appointment?",
    "Can I bring a family member with me?",
    "Do you have a waiting room?",
    "Is there Wi-Fi available for patients?",

    # Other
    "Are you approved as an Ambulatory Surgery Center?",
    "What makes Astra Vein Treatment Center unique?",
    "How do you ensure patient privacy?",
    "Can I get directions to the office?",
    "Do you offer consultations for new patients?"
]


async def test_agent_responses(config_name: str = "astra_vein_receptionist", questions: list = None):
    """
    Test agent responses to a list of questions.
    
    Parameters
    ----------
    config_name : str
        Name of the agent config to test
    questions : list
        List of questions to ask (defaults to QUESTIONS)
    """
    if questions is None:
        questions = QUESTIONS
    
    print("="*80)
    print(f"TESTING AGENT RESPONSES - {config_name}")
    print("="*80)
    
    # Load config
    print(f"\n📋 Loading config '{config_name}'...")
    try:
        config = load_config(config_name)
        print(f"✅ Config loaded: {config.name}")
        if hasattr(config, 'knowledge_file') and config.knowledge_file:
            print(f"📚 Knowledge file: {config.knowledge_file}")
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        return
    
    # Create Fuser to get system context
    print("\n🔧 Creating Fuser...")
    try:
        fuser = Fuser(config)
        system_context = fuser.get_system_context()
        print(f"✅ System context ready ({len(system_context)} chars)")
    except Exception as e:
        print(f"❌ Error creating Fuser: {e}")
        return
    
    # Get LLM
    llm = config.cortex_llm
    model_name = getattr(llm._config, 'model', 'unknown') if hasattr(llm, '_config') else 'unknown'
    print(f"🤖 LLM: {llm.__class__.__name__} ({model_name})")
    
    # Test each question
    print("\n" + "="*80)
    print("TESTING QUESTIONS")
    print("="*80)
    
    results = []
    
    for i, question in enumerate(questions, 1):
        print(f"\n{'='*80}")
        print(f"Question {i}/{len(questions)}")
        print(f"{'='*80}")
        print(f"❓ USER: {question}")
        print()
        
        # Create user prompt
        user_prompt = f"""CURRENT INPUTS:
Voice Input: "{question}"

Someone is speaking to you. Focus on answering their question professionally and helpfully.

Respond in English using natural, professional language.

IMPORTANT: Include the language code in your speak action:
- For English: {{"speak": {{"sentence": "Your response here", "language": "en"}}}}

Actions:"""
        
        # Get available actions for response model
        actions = [action.llm_label for action in config.agent_actions]
        
        try:
            # Query LLM
            response = await llm.ask(
                prompt=user_prompt,
                actions=actions,
                response_model=None,
                system_context=system_context
            )
            
            # Extract response text
            if isinstance(response, dict):
                if 'speak' in response:
                    answer = response['speak'].get('sentence', str(response))
                else:
                    answer = str(response)
            elif hasattr(response, 'speak'):
                answer = response.speak.sentence if hasattr(response.speak, 'sentence') else str(response.speak)
            else:
                answer = str(response)
            
            print(f"🤖 AGENT: {answer}")
            
            results.append({
                "question": question,
                "answer": answer,
                "status": "success"
            })
            
        except Exception as e:
            error_msg = f"Error: {e}"
            print(f"❌ {error_msg}")
            results.append({
                "question": question,
                "answer": error_msg,
                "status": "error"
            })
        
        # Small delay to avoid overwhelming the LLM
        await asyncio.sleep(0.5)
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    success_count = sum(1 for r in results if r['status'] == 'success')
    error_count = len(results) - success_count
    
    print(f"\n✅ Successful: {success_count}/{len(results)}")
    print(f"❌ Errors: {error_count}/{len(results)}")
    
    # Save results
    output_file = f"test_responses_{config_name}.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n💾 Results saved to: {output_file}")
    
    return results


async def test_single_question(config_name: str, question: str):
    """Test a single question quickly."""
    print(f"\n🤖 Testing: {question}")
    results = await test_agent_responses(config_name, [question])
    return results[0] if results else None


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test agent responses to sample questions")
    parser.add_argument("config", nargs="?", default="astra_vein_receptionist",
                       help="Agent config name (default: astra_vein_receptionist)")
    parser.add_argument("-q", "--question", help="Test a single question")
    parser.add_argument("--lex", action="store_true", help="Test Lex agent instead")
    
    args = parser.parse_args()
    
    config_name = "lex_channel_chief" if args.lex else args.config
    
    if args.question:
        # Test single question
        asyncio.run(test_single_question(config_name, args.question))
    else:
        # Test all questions
        asyncio.run(test_agent_responses(config_name))


if __name__ == "__main__":
    main()
