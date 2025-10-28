#!/usr/bin/env python3
"""
Test script for verifying knowledge injection system.
Tests that the Fuser properly loads external knowledge files.
"""

import sys
sys.path.insert(0, '/Users/wwhs-research/Downloads/roboai-feature-multiple-agent-configurations/src')

from runtime.single_mode.config import load_config
from fuser import Fuser

def test_knowledge_injection():
    """Test that knowledge file is loaded and injected into prompts."""
    
    print("="*70)
    print("TESTING KNOWLEDGE INJECTION SYSTEM")
    print("="*70)
    
    # Load the Lex config
    print("\n1. Loading Lex Channel Chief config...")
    try:
        config = load_config('lex_channel_chief')
        print(f"   ✅ Config loaded successfully!")
        print(f"   - Agent name: {config.name}")
        print(f"   - Knowledge file: {config.knowledge_file}")
        print(f"   - System prompt base length: {len(config.system_prompt_base)} chars")
    except Exception as e:
        print(f"   ❌ Error loading config: {e}")
        return False
    
    # Create Fuser instance
    print("\n2. Creating Fuser instance...")
    try:
        fuser = Fuser(config)
        print("   ✅ Fuser created successfully!")
    except Exception as e:
        print(f"   ❌ Error creating Fuser: {e}")
        return False
    
    # Get system context
    print("\n3. Retrieving system context with knowledge injection...")
    try:
        system_context = fuser.get_system_context()
        print(f"   ✅ System context retrieved!")
        print(f"   - Total length: {len(system_context)} chars")
    except Exception as e:
        print(f"   ❌ Error getting system context: {e}")
        return False
    
    # Verify knowledge base was injected
    print("\n4. Verifying knowledge base injection...")
    if "KNOWLEDGE BASE:" in system_context:
        print("   ✅ Knowledge base section found in system context!")
        
        # Check for specific knowledge content
        checks = [
            ("Lexful", "Product name"),
            ("Channel Chief", "Role name"),
            ("personal injury", "Target market"),
            ("Objection", "Objection handling section"),
            ("Pricing", "Pricing section"),
            ("Sample Dialogue", "Example dialogues"),
        ]
        
        print("\n   Checking for specific knowledge content:")
        for keyword, description in checks:
            if keyword in system_context:
                print(f"   ✅ {description}: Found")
            else:
                print(f"   ⚠️  {description}: Not found (may need to add)")
        
    else:
        print("   ❌ Knowledge base section NOT found in system context!")
        print("\n   System context structure:")
        for section in ["BASIC CONTEXT:", "KNOWLEDGE BASE:", "LAWS:", "EXAMPLES:", "AVAILABLE ACTIONS:"]:
            if section in system_context:
                print(f"   ✅ {section}")
            else:
                print(f"   ❌ {section}")
        return False
    
    # Show sample of knowledge content
    print("\n5. Sample of injected knowledge (first 500 chars):")
    kb_start = system_context.find("KNOWLEDGE BASE:")
    if kb_start != -1:
        kb_end = system_context.find("\nLAWS:", kb_start)
        if kb_end == -1:
            kb_end = kb_start + 1000
        sample = system_context[kb_start:kb_start+500]
        print(f"   {sample}...\n")
    
    print("="*70)
    print("✅ KNOWLEDGE INJECTION TEST PASSED!")
    print("="*70)
    print("\nThe external knowledge file system is working correctly.")
    print("Lex agent is ready to reference Lexful product information.")
    
    return True

if __name__ == "__main__":
    success = test_knowledge_injection()
    sys.exit(0 if success else 1)
