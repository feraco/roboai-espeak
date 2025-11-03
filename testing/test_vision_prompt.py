#!/usr/bin/env python3

import sys
sys.path.append('src')
from fuser import Fuser
from runtime.single_mode.config import load_config

config = load_config('lex_channel_chief')
fuser = Fuser(config)

# Test what the fuser generates for vision-only input
class MockSensor:
    def __init__(self, content):
        self.content = content
    
    def formatted_latest_buffer(self):
        return self.content

# Simulate vision input like what was shown in the log
vision_sensor = MockSensor('INPUT: Vision\n// START\nThe man is sitting on a couch with his arms crossed over his chest. He has a beard and appears to be wearing a white shirt.\n// END')
sensors = [vision_sensor]

# Generate fused prompt
prompt = fuser.fuse(sensors, [])
print('=== UPDATED VISION PROMPT ===')
print(prompt)
print()
print('=== CHECKING KEY ELEMENTS ===')
print(f'Contains "Lex, Channel Chief": {"Lex, Channel Chief" in prompt}')  
print(f'Contains "Lexful": {"Lexful" in prompt}')
print(f'Contains "waiting room": {"waiting room" in prompt}')