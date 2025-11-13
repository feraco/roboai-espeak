#!/bin/bash
# Install robust Astra autostart with device detection
# Run this on Jetson: bash scripts/installers/install_astra_autostart_robust.sh

set -e

echo "=========================================="
echo "Installing Astra Agent Robust Auto-Start"
echo "=========================================="
echo ""

# Check we're in the right directory
if [ ! -f "deployment/astra_pre_start_checks.sh" ]; then
    echo "❌ Error: deployment/astra_pre_start_checks.sh not found"
    echo "   Please run this from the roboai-espeak root directory"
    exit 1
fi

# Make pre-start script executable
echo "1. Making pre-start checks executable..."
chmod +x deployment/astra_pre_start_checks.sh
echo "   ✅ Done"

# Test the pre-start checks
echo ""
echo "2. Testing pre-start checks..."
if bash deployment/astra_pre_start_checks.sh; then
    echo "   ✅ Pre-start checks passed!"
else
    echo "   ⚠️  Pre-start checks had issues - check device connections"
    echo "   Continuing with installation anyway..."
fi

# Stop existing service
echo ""
echo "3. Stopping existing astra_agent service..."
sudo systemctl stop astra_agent 2>/dev/null || echo "   (No existing service to stop)"

# Disable existing service
echo ""
echo "4. Disabling old autostart..."
sudo systemctl disable astra_agent 2>/dev/null || echo "   (No existing service to disable)"

# Copy service file
echo ""
echo "5. Installing service file..."
sudo cp deployment/astra_vein_autostart.service /etc/systemd/system/astra_agent.service
echo "   ✅ Service file installed"

# Reload systemd
echo ""
echo "6. Reloading systemd..."
sudo systemctl daemon-reload
echo "   ✅ Systemd reloaded"

# Enable service
echo ""
echo "7. Enabling auto-start on boot..."
sudo systemctl enable astra_agent
echo "   ✅ Auto-start enabled"

# Start service
echo ""
echo "8. Starting service..."
sudo systemctl start astra_agent

# Wait a moment
sleep 3

# Check status
echo ""
echo "9. Checking service status..."
sudo systemctl status astra_agent --no-pager || true

echo ""
echo "=========================================="
echo "✅ Installation Complete!"
echo "=========================================="
echo ""
echo "📋 Useful Commands:"
echo ""
echo "  Check status:"
echo "    sudo systemctl status astra_agent"
echo ""
echo "  View logs:"
echo "    sudo journalctl -u astra_agent -f"
echo ""
echo "  View pre-start checks:"
echo "    sudo journalctl -u astra_agent -n 100 | grep 'Pre-Start'"
echo ""
echo "  Restart agent:"
echo "    sudo systemctl restart astra_agent"
echo ""
echo "  Stop agent:"
echo "    sudo systemctl stop astra_agent"
echo ""
echo "  Disable auto-start:"
echo "    sudo systemctl disable astra_agent"
echo ""
echo "🔧 The agent will now:"
echo "  ✅ Wait for RealSense camera 4 (up to 60s)"
echo "  ✅ Wait for USB PnP Sound Device (up to 60s)"
echo "  ✅ Wait for USB 2.0 Speaker (up to 60s)"
echo "  ✅ Set PulseAudio defaults automatically"
echo "  ✅ Force device re-detection on every start"
echo "  ✅ Use G1 arm gestures (via astra_vein_receptionist_arm config)"
echo ""
echo "🧪 Test autostart after reboot:"
echo "    sudo reboot"
echo ""
