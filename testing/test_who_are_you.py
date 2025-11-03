#!/usr/bin/env python3

import sys
sys.path.append('src')
from fuser import Fuser
from runtime.single_mode.config import load_config

config = load_config('lex_channel_chief')
fuser = Fuser(config)

# Test what the fuser generates for "Who are you?"
class MockSensor:
    def __init__(self, content):
        self.content = content
    
    def formatted_latest_buffer(self):
        return self.content

# Simulate "Who are you?" question
voice_sensor = MockSensor('INPUT: Voice\n// START\n[LANG:en] Who are you?\n// END')
sensors = [voice_sensor]

# Generate fused prompt
prompt = fuser.fuse(sensors, [])
print('=== FUSED PROMPT FOR "WHO ARE YOU?" ===')
print(prompt)
print()
print('=== CHECKING KEY ELEMENTS ===')
print(f'Contains "WHO ARE YOU": {"WHO ARE YOU" in prompt}')  
print(f'Contains "Lex, Channel Chief": {"Lex, Channel Chief" in prompt}')
print(f'Contains "Pinar Ormeci": {"Pinar Ormeci" in prompt}')