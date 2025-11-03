#!/usr/bin/env python3

import sys
sys.path.append('src')
from fuser import Fuser
from runtime.single_mode.config import load_config

config = load_config('lex_channel_chief')
fuser = Fuser(config)

print('=== SYSTEM CONTEXT ANALYSIS ===')
system_context = fuser._system_context
print(f'Total length: {len(system_context)} chars')
print()

print('=== KEY INSTRUCTIONS ===')
if "CRITICAL:" in system_context:
    critical_section = system_context.split("CRITICAL:")[1].split("Rules:")[0]
    print("CRITICAL instruction:")
    print(critical_section.strip())
print()

print('=== KNOWLEDGE BASE BEHAVIOR ===')
if "Always check KNOWLEDGE BASE first" in system_context:
    print("✅ Instructed to check knowledge base FIRST")
else:
    print("❌ No knowledge base priority instruction")

if "DO NOT make up any information not in the KNOWLEDGE BASE" in system_context:
    print("✅ Instructed NOT to make up information not in knowledge base")
else:
    print("❌ No restriction on non-knowledge base information")
    
print()
print('=== FLEXIBILITY ANALYSIS ===')
# Check if system allows general conversation or restricts to knowledge base only
restrictive_phrases = [
    "ONLY respond from KNOWLEDGE BASE",
    "NEVER answer questions not in KNOWLEDGE BASE", 
    "MUST use KNOWLEDGE BASE for all responses"
]

flexible_phrases = [
    "check KNOWLEDGE BASE first",
    "use KNOWLEDGE BASE sections", 
    "find the relevant KNOWLEDGE BASE section"
]

is_restrictive = any(phrase in system_context for phrase in restrictive_phrases)
is_flexible = any(phrase in system_context for phrase in flexible_phrases)

print(f"Restrictive (knowledge base only): {is_restrictive}")
print(f"Flexible (knowledge base first, but allows other): {is_flexible}")

if is_flexible and not is_restrictive:
    print("🎯 CONCLUSION: Agent can handle both knowledge base AND general questions")
elif is_restrictive:
    print("🔒 CONCLUSION: Agent restricted to knowledge base only")
else:
    print("❓ CONCLUSION: Unclear - may default to general LLM behavior")