#!/usr/bin/env python3

import sys
sys.path.append('src')
from fuser import Fuser
from runtime.single_mode.config import load_config

config = load_config('lex_channel_chief')
fuser = Fuser(config)

# Check what happens during initialization
print('=== FUSER INITIALIZATION ===')
print(f'Knowledge file path: {config.knowledge_file}')
print(f'System context length: {len(fuser._system_context)}')
print()

# Check system context content
print('=== SYSTEM CONTEXT CONTENT ===')
print(fuser._system_context)
print()

# Test prompt with empty sensors to see full structure
prompt = fuser.fuse([], [])
print('=== FULL PROMPT WITH NO INPUTS ===')
print(prompt)