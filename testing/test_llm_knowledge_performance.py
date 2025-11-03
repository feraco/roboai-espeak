#!/usr/bin/env python3
"""
Quick test to verify LLM and knowledge system performance.
Tests response time and knowledge integration for Lex Channel Chief.
"""

import asyncio
import time
import json
import aiohttp
from pathlib import Path

async def test_ollama_direct():
    """Test direct Ollama API for speed baseline."""
    print("=" * 60)
    print("1. Testing Direct Ollama API Speed")
    print("=" * 60)
    
    prompt = "What is Lexful? Answer in one sentence."
    
    payload = {
        "model": "gemma2:2b",  # Use faster model
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.7,
            "num_predict": 30  # Very short for baseline test
        }
    }
    
    start_time = time.time()
    
    try:
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post("http://localhost:11434/api/generate", json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    response_text = result.get("response", "").strip()
                    
                    end_time = time.time()
                    response_time = end_time - start_time
                    
                    print(f"✓ Response time: {response_time:.2f} seconds")
                    print(f"✓ Response: {response_text}")
                    
                    if response_time < 3.0:
                        print("✓ FAST: Response under 3 seconds")
                    else:
                        print("⚠ SLOW: Response over 3 seconds")
                        
                    return True
                else:
                    print(f"✗ Ollama error: {response.status}")
                    return False
                    
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        return False

async def test_knowledge_loading():
    """Test that knowledge file can be loaded."""
    print("\n" + "=" * 60)
    print("2. Testing Knowledge File Loading")
    print("=" * 60)
    
    knowledge_path = Path("docs/lexful_knowledge.md")
    
    if not knowledge_path.exists():
        print("✗ Knowledge file not found")
        return False
    
    try:
        content = knowledge_path.read_text(encoding="utf-8")
        
        print(f"✓ Knowledge file loaded: {len(content)} characters")
        
        # Check for key Lexful concepts
        key_terms = ["Lexful", "legal practice", "software", "management"]
        found_terms = [term for term in key_terms if term.lower() in content.lower()]
        
        print(f"✓ Key terms found: {found_terms}")
        
        if len(found_terms) >= 3:
            print("✓ Knowledge file contains expected content")
            return True
        else:
            print("⚠ Knowledge file may be incomplete")
            return False
            
    except Exception as e:
        print(f"✗ Error loading knowledge file: {e}")
        return False

async def test_lex_agent_with_knowledge():
    """Test Lex agent response with knowledge integration."""
    print("\n" + "=" * 60)
    print("3. Testing Lex Agent with Knowledge Integration")
    print("=" * 60)
    
    # Simulate the fuser prompt that would be sent to LLM
    knowledge_path = Path("docs/lexful_knowledge.md")
    knowledge_content = knowledge_path.read_text(encoding="utf-8")
    
    # Create a prompt similar to what the Fuser would generate
    test_prompt = f"""BASIC CONTEXT:
You are Lex, the Channel Chief for Lexful. You're a charismatic sales leader who helps law firms discover how Lexful transforms their practice management. You combine deep software knowledge with genuine relationship-building skills.

KNOWLEDGE BASE:
{knowledge_content}

EXAMPLES:
If someone asks about Lexful pricing, you might:
Speak: {{"sentence": "Lexful offers flexible pricing starting at $39/month per user, with enterprise packages for larger firms. Let me show you how it pays for itself!"}}

If someone asks what Lexful does, you might:
Speak: {{"sentence": "Lexful is comprehensive legal practice management software that handles everything from client intake to billing, helping law firms increase revenue by 25% on average."}}

What will you do? Actions:
speak(sentence: str) - Respond to the user

Current situation: Someone asks "What makes Lexful different from other legal software?"

Response (valid JSON only):"""

    payload = {
        "model": "gemma2:2b",  # Use the faster model from optimized config
        "prompt": test_prompt,
        "stream": False,
        "options": {
            "temperature": 0.7,
            "num_predict": 50,  # Faster with shorter responses
            "top_p": 0.9,
            "top_k": 40
        }
    }
    
    start_time = time.time()
    
    try:
        timeout = aiohttp.ClientTimeout(total=15)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post("http://localhost:11434/api/generate", json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    response_text = result.get("response", "").strip()
                    
                    end_time = time.time()
                    response_time = end_time - start_time
                    
                    print(f"✓ Response time: {response_time:.2f} seconds")
                    print(f"✓ Raw response: {response_text}")
                    
                    # Check if response contains Lexful-specific knowledge
                    knowledge_indicators = [
                        "lexful", "legal practice", "law firm", "case management",
                        "client intake", "billing", "practice management"
                    ]
                    
                    found_knowledge = [term for term in knowledge_indicators 
                                     if term.lower() in response_text.lower()]
                    
                    if found_knowledge:
                        print(f"✓ KNOWLEDGE USED: Found terms: {found_knowledge}")
                    else:
                        print("⚠ No clear knowledge integration detected")
                    
                    # Try to parse JSON
                    try:
                        # Look for JSON in the response
                        json_start = response_text.find('{')
                        json_end = response_text.rfind('}') + 1
                        
                        if json_start >= 0 and json_end > json_start:
                            json_part = response_text[json_start:json_end]
                            parsed = json.loads(json_part)
                            
                            if "speak" in parsed or "sentence" in parsed:
                                print("✓ VALID JSON: Response format correct")
                            else:
                                print("⚠ JSON parsed but no speak action found")
                        else:
                            print("⚠ No JSON structure found in response")
                            
                    except json.JSONDecodeError:
                        print("⚠ Response not valid JSON")
                    
                    if response_time < 5.0:
                        print("✓ PERFORMANCE: Good response time")
                        return True
                    else:
                        print("⚠ PERFORMANCE: Slow response time")
                        return False
                        
                else:
                    print(f"✗ API error: {response.status}")
                    return False
                    
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False

async def main():
    """Run all tests."""
    print("Testing LLM Performance and Knowledge Integration")
    print("=" * 60)
    
    results = {
        "ollama_speed": await test_ollama_direct(),
        "knowledge_loading": await test_knowledge_loading(),
        "agent_integration": await test_lex_agent_with_knowledge()
    }
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    all_passed = all(results.values())
    
    for test, passed in results.items():
        symbol = "✓" if passed else "✗"
        print(f"{symbol} {test.replace('_', ' ').upper()}: {'PASS' if passed else 'FAIL'}")
    
    if all_passed:
        print(f"\n✓ ALL TESTS PASSED - System ready!")
        print("\nTo run Lex agent: uv run src/run.py lex_channel_chief")
    else:
        print(f"\n✗ Some tests failed. Check issues above.")
    
    print("\nPerformance Tips:")
    print("  - Use smaller models (gemma2:2b) for faster responses")
    print("  - Reduce max_tokens in config for quicker responses") 
    print("  - Check system CPU/RAM usage during agent runs")

if __name__ == "__main__":
    asyncio.run(main())