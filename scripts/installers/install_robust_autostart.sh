#!/bin/bash
# Install robust auto-start for Astra Agent on Jetson
# Run this on your Jetson: bash install_robust_autostart.sh

set -e

echo "=========================================="
echo "Installing Robust Auto-Start for Astra Agent"
echo "=========================================="

# Check we're in the right directory
if [ ! -f "pre_start_checks.sh" ]; then
    echo "ERROR: pre_start_checks.sh not found in current directory"
    echo "Please run this from the roboai-espeak directory"
    exit 1
fi

# Make pre-start checks executable
echo "1. Making pre-start checks executable..."
chmod +x pre_start_checks.sh

# Test the pre-start checks
echo "2. Testing pre-start checks..."
if bash pre_start_checks.sh; then
    echo "   ✅ Pre-start checks passed!"
else
    echo "   ⚠️  Pre-start checks had issues - continuing anyway"
fi

# Stop existing service
echo "3. Stopping existing service..."
sudo systemctl stop astra_agent 2>/dev/null || true

# Copy service file
echo "4. Installing service file..."
sudo cp astra_agent_robust.service /etc/systemd/system/astra_agent.service

# Reload systemd
echo "5. Reloading systemd..."
sudo systemctl daemon-reload

# Enable service
echo "6. Enabling auto-start on boot..."
sudo systemctl enable astra_agent

# Start service
echo "7. Starting service..."
sudo systemctl start astra_agent

# Wait a moment
sleep 3

# Check status
echo "8. Checking service status..."
sudo systemctl status astra_agent --no-pager || true

echo ""
echo "=========================================="
echo "Installation complete!"
echo "=========================================="
echo ""
echo "Useful commands:"
echo "  Check status:  sudo systemctl status astra_agent"
echo "  View logs:     sudo journalctl -u astra_agent -f"
echo "  Restart:       sudo systemctl restart astra_agent"
echo "  Stop:          sudo systemctl stop astra_agent"
echo "  Disable:       sudo systemctl disable astra_agent"
echo ""
echo "The agent will now:"
echo "  ✅ Wait for USB microphone (up to 60s)"
echo "  ✅ Wait for USB speaker and set as default (up to 60s)"
echo "  ✅ Validate Ollama is running and responsive"
echo "  ✅ Test Ollama model can respond"
echo "  ✅ Auto-restart Ollama if not responding"
echo "  ✅ Clear cache if Ollama is corrupted"
echo "  ✅ Restart agent on failure (up to 3 times in 5 min)"
echo ""
echo "View the pre-start checks with:"
echo "  sudo journalctl -u astra_agent -n 100 | grep PreStart"
echo ""
