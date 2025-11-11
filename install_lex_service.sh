#!/bin/bash
set -e

echo "🚀 Installing Lex Agent Autostart Service..."

# Check if running on Jetson/Ubuntu
if [[ ! -f /etc/os-release ]]; then
    echo "❌ Error: This script is for Ubuntu/Jetson only"
    exit 1
fi

# Check if in correct directory
if [[ ! -f "lex_agent.service" ]]; then
    echo "❌ Error: lex_agent.service not found. Run from roboai-espeak directory."
    exit 1
fi

# Stop service if already running
echo "🛑 Stopping existing service (if running)..."
sudo systemctl stop lex_agent 2>/dev/null || true

# Copy service file
echo "📋 Installing service file..."
sudo cp lex_agent.service /etc/systemd/system/lex_agent.service

# Make sure pre-start checks script is executable
echo "🔧 Making scripts executable..."
chmod +x lex_pre_start_checks.sh

# Reload systemd
echo "🔄 Reloading systemd..."
sudo systemctl daemon-reload

# Enable auto-start on boot
echo "✅ Enabling auto-start on boot..."
sudo systemctl enable lex_agent

# Start the service
echo "▶️  Starting Lex agent..."
sudo systemctl start lex_agent

# Wait a moment for service to start
sleep 3

# Show status
echo ""
echo "📊 Service Status:"
sudo systemctl status lex_agent --no-pager

echo ""
echo "✅ Lex Agent installed and started!"
echo ""
echo "📝 Useful commands:"
echo "  sudo systemctl status lex_agent     # Check status"
echo "  sudo systemctl stop lex_agent       # Stop service"
echo "  sudo systemctl start lex_agent      # Start service"
echo "  sudo systemctl restart lex_agent    # Restart service"
echo "  sudo systemctl disable lex_agent    # Disable auto-start"
echo "  sudo journalctl -u lex_agent -f     # View live logs"
echo ""
