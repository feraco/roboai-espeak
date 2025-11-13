#!/bin/bash
# Test Badge Reader on Mac
# Prints instructions and runs the badge greeter

echo "🎯 Badge Reader Test - Mac"
echo "================================"
echo ""
echo "📸 INSTRUCTIONS:"
echo "1. Make sure your camera is working"
echo "2. Write your name on a piece of paper (First + Last name)"
echo "3. Examples: 'John Smith', 'Sarah Jones', 'Michael Brown'"
echo "4. Hold the paper up to your camera"
echo "5. Keep it steady for 3-5 seconds"
echo "6. The agent will detect your name and greet you!"
echo ""
echo "✅ REQUIREMENTS:"
echo "- Ollama running: ollama serve"
echo "- Model downloaded: ollama pull llama3.1:8b"
echo "- Piper TTS installed: brew install piper-tts (or manual install)"
echo "- Camera accessible (grant permissions if prompted)"
echo ""
echo "📝 TIPS FOR BEST RESULTS:"
echo "- Use clear, legible handwriting or printed text"
echo "- Write in CAPITAL LETTERS or Title Case"
echo "- Use a white paper with dark text"
echo "- Ensure good lighting"
echo "- Hold paper close enough to camera"
echo ""
echo "🔍 WHAT THE SYSTEM LOOKS FOR:"
echo "- Two words (First + Last name)"
echo "- Proper name capitalization"
echo "- NOT common words like: VISITOR, GUEST, BADGE, etc."
echo ""
echo "Press Enter to start the test..."
read

echo ""
echo "🚀 Starting badge reader test..."
echo "📸 Point your camera at a name badge or paper with a name written on it"
echo "🛑 Press Ctrl+C to stop"
echo ""

# Run the agent
uv run src/run.py badge_reader_test_mac
