#!/bin/bash
# Quick Ollama Fix Script for Jetson
# Addresses common "no output from llm" issues

echo "🔧 Ollama Quick Fix for Jetson"
echo "==============================="

# Check if running as root for systemctl commands
if [[ $EUID -eq 0 ]]; then
   echo "⚠️  Please run this script as regular user (not sudo)"
   exit 1
fi

echo "1. Stopping Ollama service..."
sudo systemctl stop ollama
sleep 3

echo "2. Clearing potentially corrupted model cache..."
sudo rm -rf /usr/share/ollama/.ollama/models/manifests/*
sudo rm -rf /usr/share/ollama/.ollama/models/blobs/sha256-*

echo "3. Starting Ollama service..."
sudo systemctl start ollama
sleep 5

echo "4. Checking service status..."
if sudo systemctl is-active --quiet ollama; then
    echo "✅ Ollama service is running"
else
    echo "❌ Ollama service failed to start"
    sudo journalctl -u ollama -n 10 --no-pager
    exit 1
fi

echo "5. Re-pulling models (this may take several minutes)..."
echo "   Pulling llama3.1:8b..."
ollama pull llama3.1:8b

if [ $? -eq 0 ]; then
    echo "✅ llama3.1:8b pulled successfully"
else
    echo "❌ Failed to pull llama3.1:8b"
    exit 1
fi

echo "   Pulling llava-llama3..."
ollama pull llava-llama3

if [ $? -eq 0 ]; then
    echo "✅ llava-llama3 pulled successfully"
else
    echo "❌ Failed to pull llava-llama3"
    exit 1
fi

echo "6. Testing Ollama with simple query..."
response=$(curl -s -X POST http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.1:8b",
    "prompt": "Say hello",
    "stream": false,
    "options": {"num_predict": 5}
  }' | jq -r '.response' 2>/dev/null)

if [ -n "$response" ] && [ "$response" != "null" ]; then
    echo "✅ Ollama is working! Response: $response"
    echo ""
    echo "🎉 Fix completed successfully!"
    echo "You can now run: uv run src/run.py astra_vein_receptionist"
else
    echo "❌ Ollama still not responding properly"
    echo "Try running the diagnostic script: python testing/diagnose_ollama_jetson.py"
fi