#!/bin/bash

# Lex Channel Chief - Robust Auto-Start Installation Script
# This script installs the systemd service with hardware detection

set -e

echo "================================================"
echo "Lex Channel Chief - Auto-Start Installation"
echo "================================================"

# Check if running on Linux with systemd
if ! command -v systemctl &> /dev/null; then
    echo "❌ ERROR: systemctl not found. This script requires systemd (Linux)."
    echo "For macOS, manually run: uv run src/run.py lex_channel_chief"
    exit 1
fi

# Get the current directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "✅ Current directory: $SCRIPT_DIR"

# Test the pre-start checks script
echo ""
echo "Testing pre-start checks script..."
if bash "$SCRIPT_DIR/lex_pre_start_checks.sh"; then
    echo "✅ Pre-start checks passed!"
else
    echo "⚠️  WARNING: Pre-start checks reported issues"
    echo "   Continuing with installation - service will handle this at runtime"
fi

# Copy service file to systemd
echo ""
echo "Installing systemd service..."
sudo cp "$SCRIPT_DIR/lex_agent.service" /etc/systemd/system/lex_agent.service

# Reload systemd daemon
echo "Reloading systemd daemon..."
sudo systemctl daemon-reload

# Enable the service (auto-start on boot)
echo "Enabling auto-start on boot..."
sudo systemctl enable lex_agent.service

# Start the service
echo "Starting Lex agent service..."
sudo systemctl start lex_agent.service

# Check status
echo ""
echo "================================================"
echo "✅ Installation complete!"
echo "================================================"
echo ""
echo "Service status:"
sudo systemctl status lex_agent.service --no-pager || true

echo ""
echo "================================================"
echo "Useful commands:"
echo "================================================"
echo "Check status:   sudo systemctl status lex_agent"
echo "View logs:      sudo journalctl -u lex_agent -f"
echo "Stop agent:     sudo systemctl stop lex_agent"
echo "Start agent:    sudo systemctl start lex_agent"
echo "Restart agent:  sudo systemctl restart lex_agent"
echo "Disable auto-start: sudo systemctl disable lex_agent"
echo ""
echo "To watch live logs:"
echo "sudo journalctl -u lex_agent -f"
echo ""
