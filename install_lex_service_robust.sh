#!/bin/bash
set -e

echo "🚀 Installing Lex Agent ROBUST Service with Hardware Checks..."

# Check if running on Jetson/Ubuntu
if [[ ! -f /etc/os-release ]]; then
    echo "❌ Error: This script is for Ubuntu/Jetson only"
    exit 1
fi

# Check if in correct directory
if [[ ! -f "lex_agent_robust.service" ]]; then
    echo "❌ Error: lex_agent_robust.service not found. Run from roboai-espeak directory."
    exit 1
fi

# Stop any existing lex_agent service
echo "🛑 Stopping existing lex_agent service (if running)..."
sudo systemctl stop lex_agent 2>/dev/null || true

# Make scripts executable
echo "🔧 Making scripts executable..."
chmod +x lex_pre_start_checks_robust.sh

# Copy service file
echo "📋 Installing ROBUST service file..."
sudo cp lex_agent_robust.service /etc/systemd/system/lex_agent.service

# Reload systemd
echo "🔄 Reloading systemd..."
sudo systemctl daemon-reload

# Enable auto-start on boot
echo "✅ Enabling auto-start on boot..."
sudo systemctl enable lex_agent

# Start the service
echo "▶️  Starting Lex agent with robust checks..."
sudo systemctl start lex_agent

# Wait for service to start
sleep 5

# Show status
echo ""
echo "📊 Service Status:"
sudo systemctl status lex_agent --no-pager || true

echo ""
echo "🔍 Checking logs for hardware detection:"
sudo journalctl -u lex_agent -n 30 --no-pager | grep -E "PreStart|SUCCESS|ERROR" || true

echo ""
echo "✅ Lex Agent ROBUST service installed!"
echo ""
echo "📝 This service includes:"
echo "  ✅ Hardware detection (mic, speaker, camera)"
echo "  ✅ Ollama validation (checks model availability)"
echo "  ✅ Piper TTS verification"
echo "  ✅ Python dependencies check"
echo "  ✅ Auto-restart on failure"
echo "  ✅ Complete logging"
echo ""
echo "📝 Useful commands:"
echo "  sudo systemctl status lex_agent     # Check status"
echo "  sudo systemctl stop lex_agent       # Stop service"
echo "  sudo systemctl start lex_agent      # Start service"
echo "  sudo systemctl restart lex_agent    # Restart service"
echo "  sudo journalctl -u lex_agent -f     # View live logs"
echo "  sudo journalctl -u lex_agent -n 50  # View last 50 lines"
echo ""
