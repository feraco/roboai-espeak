#!/usr/bin/env python3
"""
Test if the Fuser correctly loads the knowledge file.
"""

import sys
sys.path.append('src')

from fuser import Fuser
from runtime.single_mode.config import RuntimeConfig
import json

# Load the config
config_path = "config/lex_channel_chief.json5"

print("Testing Fuser Knowledge Loading")
print("=" * 50)

try:
    # Read and parse config 
    with open(config_path, 'r') as f:
        import json5
        config_data = json5.load(f)
    
    # Create RuntimeConfig
    runtime_config = RuntimeConfig(**config_data)
    
    print(f"✓ Config loaded successfully")
    print(f"✓ Knowledge file: {runtime_config.knowledge_file}")
    
    # Create Fuser
    fuser = Fuser(runtime_config)
    
    # Test if knowledge is in system prompt
    test_inputs = []
    system_prompt = fuser.fuse(test_inputs)
    
    print(f"✓ Fuser created successfully")
    print(f"✓ System prompt length: {len(system_prompt)} characters")
    
    # Check for Lexful content
    lexful_terms = ["Lexful", "legal intake", "$1,500", "personal injury", "ROI"]
    found_terms = [term for term in lexful_terms if term in system_prompt]
    
    print(f"✓ Knowledge terms found: {found_terms}")
    
    if len(found_terms) >= 3:
        print("\n✅ SUCCESS: Knowledge file is properly loaded!")
        
        # Show a snippet of the knowledge section
        knowledge_start = system_prompt.find("KNOWLEDGE BASE:")
        if knowledge_start > 0:
            snippet = system_prompt[knowledge_start:knowledge_start + 200]
            print(f"\nKnowledge snippet:")
            print(f"'{snippet}...'")
        
    else:
        print("\n❌ FAILED: Knowledge file not properly loaded")
        print("Check if knowledge_file path is correct in config")
    
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()