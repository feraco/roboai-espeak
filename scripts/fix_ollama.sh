#!/bin/bash
# Ollama Troubleshooting and Reset Script for Jetson Orin
# Run this when Ollama has errors (500, 499, Load failed)

set -e

echo "🔧 Ollama Troubleshooting and Reset"
echo "===================================="
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
   echo "❌ Do not run this script as root"
   echo "   Run as regular user: ./fix_ollama.sh"
   exit 1
fi

# Step 1: Check memory
echo "📊 Step 1: System Memory Check"
echo "--------------------------------"
free -h
echo ""

MEM_AVAILABLE=$(free -m | awk 'NR==2{print $7}')
if [ "$MEM_AVAILABLE" -lt 4000 ]; then
    echo "⚠️  WARNING: Low memory available (${MEM_AVAILABLE}MB)"
    echo "   Ollama needs at least 4GB free for llama3.1:8b"
    echo "   Consider:"
    echo "   - Closing other applications"
    echo "   - Rebooting the Jetson"
    echo "   - Using a smaller model (llama3.2:3b)"
    echo ""
fi

# Step 2: Check current Ollama status
echo "📋 Step 2: Current Ollama Status"
echo "--------------------------------"
systemctl status ollama --no-pager -l | tail -20
echo ""

# Step 3: Stop Ollama completely
echo "🛑 Step 3: Stopping Ollama"
echo "--------------------------------"
echo "Stopping systemd service..."
sudo systemctl stop ollama
sleep 2

echo "Killing any remaining processes..."
sudo pkill -9 ollama || true
sleep 1

echo "✅ Ollama stopped"
echo ""

# Step 4: Clear all cache and temporary data
echo "🧹 Step 4: Clearing Cache and Runtime Data"
echo "--------------------------------"

# User cache
if [ -d "$HOME/.ollama/cache" ]; then
    echo "Clearing user cache: $HOME/.ollama/cache"
    rm -rf "$HOME/.ollama/cache"/*
fi

if [ -d "$HOME/.ollama/tmp" ]; then
    echo "Clearing user tmp: $HOME/.ollama/tmp"
    rm -rf "$HOME/.ollama/tmp"/*
fi

# System cache (if exists)
if [ -d "/usr/share/ollama/.ollama/cache" ]; then
    echo "Clearing system cache: /usr/share/ollama/.ollama/cache"
    sudo rm -rf /usr/share/ollama/.ollama/cache/*
fi

# Temp files
echo "Clearing /tmp/ollama*"
sudo rm -rf /tmp/ollama* || true

echo "✅ Cache cleared"
echo ""

# Step 5: Reset systemd state
echo "🔄 Step 5: Resetting Systemd State"
echo "--------------------------------"
sudo systemctl reset-failed ollama || true
sudo systemctl daemon-reload
echo "✅ Systemd reset"
echo ""

# Step 6: Start Ollama
echo "🚀 Step 6: Starting Ollama"
echo "--------------------------------"
sudo systemctl start ollama
sleep 5

# Check if it started
if systemctl is-active --quiet ollama; then
    echo "✅ Ollama started successfully"
    echo ""
    
    # Step 7: Verify model
    echo "🔍 Step 7: Verifying Model"
    echo "--------------------------------"
    ollama list
    echo ""
    
    if ollama list | grep -q "llama3.1:8b"; then
        echo "✅ Model llama3.1:8b found"
        echo ""
        
        # Step 8: Test model loading
        echo "🧪 Step 8: Testing Model Loading"
        echo "--------------------------------"
        echo "Sending test prompt (this may take 10-20 seconds)..."
        
        if timeout 30 ollama run llama3.1:8b "Say 'Hello' in one word" 2>&1 | grep -i "hello"; then
            echo ""
            echo "✅ Model loads and responds correctly!"
            echo ""
            echo "===================================="
            echo "✅ Ollama is now working properly!"
            echo "===================================="
            echo ""
            echo "You can now run the agent:"
            echo "  uv run src/run.py astra_vein_receptionist"
            exit 0
        else
            echo ""
            echo "⚠️  Model loaded but response test failed"
            echo "   This might be OK - try running the agent"
        fi
    else
        echo "❌ Model llama3.1:8b not found"
        echo ""
        echo "Installing model (this will take several minutes)..."
        ollama pull llama3.1:8b
        
        if [ $? -eq 0 ]; then
            echo "✅ Model installed successfully"
        else
            echo "❌ Model installation failed"
            echo "   Check your internet connection"
            exit 1
        fi
    fi
else
    echo "❌ Ollama failed to start"
    echo ""
    echo "Check logs for details:"
    echo "  sudo journalctl -u ollama -n 50 --no-pager"
    echo ""
    echo "Common issues:"
    echo "1. Insufficient memory (need 4GB+ free)"
    echo "2. GPU driver issues (check: nvidia-smi or tegrastats)"
    echo "3. Corrupted installation (reinstall: curl -fsSL https://ollama.ai/install.sh | sh)"
    exit 1
fi
