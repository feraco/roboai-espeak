#!/usr/bin/env python3
"""
Test Lex agent with specific Lexful questions to verify knowledge integration.
"""

import asyncio
import time
import json
import aiohttp
from pathlib import Path

async def test_lexful_knowledge():
    """Test specific Lexful questions with the optimized knowledge base."""
    
    # Load the optimized knowledge
    knowledge_path = Path("docs/lexful_knowledge_optimized.md")
    knowledge_content = knowledge_path.read_text(encoding="utf-8")
    
    test_questions = [
        {
            "question": "What does Lexful cost?",
            "expected_keywords": ["1500", "2500", "setup fee", "month"]
        },
        {
            "question": "How does Lexful handle objections about existing staff?",
            "expected_keywords": ["augments", "doesn't replace", "30-50%", "after hours"]
        },
        {
            "question": "What ROI can firms expect?",
            "expected_keywords": ["2-3 months", "4000-6000", "50000-150000", "specialist costs"]
        },
        {
            "question": "Who is the ideal customer for Lexful?",
            "expected_keywords": ["5-25 attorneys", "personal injury", "50-200 leads"]
        }
    ]
    
    print("Testing Lexful Knowledge Integration")
    print("=" * 60)
    
    results = []
    
    for i, test in enumerate(test_questions, 1):
        print(f"\n{i}. Testing: {test['question']}")
        print("-" * 40)
        
        # Create prompt with knowledge base
        prompt = f"""BASIC CONTEXT:
You are Lex, Channel Chief for Lexful - AI-powered legal intake software for personal injury law firms.

KNOWLEDGE BASE:
{knowledge_content}

IMPORTANT: Use ONLY information from the KNOWLEDGE BASE above. No emojis.

Question: {test['question']}

Respond with accurate information from the knowledge base in this format:
{{"sentence": "your response here"}}"""

        payload = {
            "model": "gemma2:2b",
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.3,  # Lower temperature for more factual responses
                "num_predict": 80,
                "top_p": 0.9
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
                        
                        print(f"Response time: {response_time:.2f}s")
                        print(f"Response: {response_text}")
                        
                        # Check for expected keywords
                        found_keywords = []
                        for keyword in test["expected_keywords"]:
                            if keyword.lower() in response_text.lower():
                                found_keywords.append(keyword)
                        
                        accuracy = len(found_keywords) / len(test["expected_keywords"])
                        
                        print(f"Expected keywords: {test['expected_keywords']}")
                        print(f"Found keywords: {found_keywords}")
                        print(f"Accuracy: {accuracy:.0%}")
                        
                        # Check for emojis
                        has_emojis = any(ord(char) > 127 for char in response_text)
                        emoji_status = "FAIL - Contains emojis" if has_emojis else "PASS - No emojis"
                        print(f"Emoji check: {emoji_status}")
                        
                        results.append({
                            "question": test["question"],
                            "accuracy": accuracy,
                            "response_time": response_time,
                            "no_emojis": not has_emojis,
                            "found_keywords": found_keywords
                        })
                        
                    else:
                        print(f"ERROR: {response.status}")
                        results.append({"question": test["question"], "error": True})
                        
        except Exception as e:
            print(f"ERROR: {e}")
            results.append({"question": test["question"], "error": True})
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    successful_tests = [r for r in results if not r.get("error", False)]
    
    if successful_tests:
        avg_accuracy = sum(r["accuracy"] for r in successful_tests) / len(successful_tests)
        avg_response_time = sum(r["response_time"] for r in successful_tests) / len(successful_tests)
        all_emoji_free = all(r["no_emojis"] for r in successful_tests)
        
        print(f"Average accuracy: {avg_accuracy:.0%}")
        print(f"Average response time: {avg_response_time:.2f}s")
        print(f"Emoji-free responses: {'YES' if all_emoji_free else 'NO'}")
        
        if avg_accuracy >= 0.7 and avg_response_time < 5.0 and all_emoji_free:
            print("\n✓ ALL TESTS PASSED - Knowledge integration working!")
        else:
            print("\n⚠ Some issues detected - check responses above")
    else:
        print("✗ All tests failed - check Ollama connection")

if __name__ == "__main__":
    asyncio.run(test_lexful_knowledge())