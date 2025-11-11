#!/usr/bin/env python3
"""Update Lex config to use active badge greeting behavior"""

import json5

config_path = "config/lex_channel_chief.json5"

# Read config
with open(config_path, 'r') as f:
    config = json5.load(f)

# Old badge behavior text
old_badge_text = """⚠️ BADGE INFO IS FOR PERSONALIZATION ONLY - USE NAMES NATURALLY IN CONVERSATION
- Badge scanner detects name tags and provides names silently
- When badge input shows "I see [Name] is here. Their badge shows the name [Name]":
  * Use the person's name NATURALLY in your greeting or response
  * DO NOT say "I see your badge" or "I read your name tag"
  * DO NOT announce that you detected their name
- Example CORRECT usage:
  * Badge: "I see John Smith is here. Their badge shows the name John Smith."
  * User: "Tell me about Lexful"
  * You: "Great to meet you, John! Lexful is the AI-native IT documentation platform..." ✅ (personalized naturally)
- Example WRONG usage:
  * Badge: "I see Sarah Johnson is here."
  * You: "I can see from your badge that your name is Sarah Johnson!" ❌ (DO NOT announce detection)
- Only use first name in conversation (e.g., "John" not "John Smith")
- Badge detection happens every 8 seconds - you'll get updates periodically
- If no badge detected, proceed with conversation normally (no name used)"""

# New active greeting text
new_badge_text = """⚠️ WHEN BADGE IS DETECTED, GREET THE PERSON IMMEDIATELY
- Badge scanner detects name tags and triggers automatic greeting
- When badge input shows "BADGE DETECTED: Greet [Name]. Say: 'Hi [Name], my name is Lex' and introduce yourself.":
  * IMMEDIATELY speak the greeting shown in the badge message
  * Keep it warm: "Hi [Name], my name is Lex!"
  * Then briefly introduce yourself
  * Example: "Hi Frederick, my name is Lex! I'm the Channel Chief for Lexful. How can I help you today?"
- Badge detection happens every 8 seconds automatically
- Same person won't be greeted again for 90 seconds (cooldown)
- If no badge detected, wait for audio input normally
- DO NOT announce "I see your badge" - just greet them naturally"""

# Replace in system_prompt_base
config['system_prompt_base'] = config['system_prompt_base'].replace(old_badge_text, new_badge_text)

# Update examples to match new behavior
old_example_5 = """5. When badge detected + question asked (USE NAME NATURALLY):
   Badge: "I see Michael Chen is here. Their badge shows the name Michael Chen."
   User: "Tell me about Lexful"
   speak: {"sentence": "Great to meet you, Michael! Lexful is the AI-native IT documentation platform for MSPs.", "language": "en"}"""

new_example_5 = """5. When badge detected (GREET IMMEDIATELY):
   Badge: "BADGE DETECTED: Greet Michael. Say: 'Hi Michael, my name is Lex' and introduce yourself."
   speak: {"sentence": "Hi Michael, my name is Lex! I'm the Channel Chief for Lexful. How can I help you today?", "language": "en"}"""

config['system_prompt_examples'] = config['system_prompt_examples'].replace(old_example_5, new_example_5)

old_example_10 = """10. Badge + first time greeting:
    Badge: "I see Sarah Johnson is here. Their badge shows the name Sarah Johnson."
    User: "Hi there"
    speak: {"sentence": "Hello Sarah! I'm Lex, Channel Chief for Lexful. How can I help you today?", "language": "en"}"""

new_example_10 = """10. Badge detected (automatic greeting):
    Badge: "BADGE DETECTED: Greet Sarah. Say: 'Hi Sarah, my name is Lex' and introduce yourself."
    speak: {"sentence": "Hi Sarah, my name is Lex! I'm Channel Chief for Lexful. How can I help you today?", "language": "en"}"""

config['system_prompt_examples'] = config['system_prompt_examples'].replace(old_example_10, new_example_10)

# Write updated config
with open(config_path, 'w') as f:
    json5.dump(config, f, indent=2, quote_keys=False, trailing_commas=False)

print("✅ Updated Lex config with active badge greeting behavior")
print("📝 Changes:")
print("  - Badge behavior: Passive context → Active greeting trigger")
print("  - Examples updated to match new message format")
print("  - Ready for testing with: uv run src/run.py lex_channel_chief")
