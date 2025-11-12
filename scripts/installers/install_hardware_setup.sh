#!/bin/bash
# Install RoboAI Hardware Configuration Service
# Ensures audio/video devices are configured on every boot

set -e

echo "🔧 Installing RoboAI Hardware Configuration Service..."

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then 
    echo "❌ This script must be run with sudo"
    exit 1
fi

# Check if script exists
if [ ! -f "scripts/setup_hardware_defaults.sh" ]; then
    echo "❌ setup_hardware_defaults.sh not found"
    exit 1
fi

# Copy script to system location
echo "📋 Installing hardware setup script..."
cp scripts/setup_hardware_defaults.sh /usr/local/bin/
chmod +x /usr/local/bin/setup_hardware_defaults.sh
echo "✅ Script installed to /usr/local/bin/setup_hardware_defaults.sh"

# Copy service file
echo "📋 Installing systemd service..."
cp systemd_services/roboai-hardware-setup.service /etc/systemd/system/
chmod 644 /etc/systemd/system/roboai-hardware-setup.service
echo "✅ Service file installed"

# Reload systemd
echo "🔄 Reloading systemd..."
systemctl daemon-reload

# Enable service to run on boot
echo "✅ Enabling service for auto-start on boot..."
systemctl enable roboai-hardware-setup.service

# Run service now to test
echo "▶️  Running hardware configuration now..."
systemctl start roboai-hardware-setup.service

# Show status
echo ""
echo "📊 Service Status:"
systemctl status roboai-hardware-setup.service --no-pager || true

# Show device configuration
echo ""
if [ -f /etc/roboai-devices.conf ]; then
    echo "📝 Device Configuration:"
    cat /etc/roboai-devices.conf
fi

# Show ALSA config
echo ""
if [ -f /etc/asound.conf ]; then
    echo "🔊 ALSA Configuration:"
    cat /etc/asound.conf
fi

echo ""
echo "✅ RoboAI Hardware Configuration Service Installed!"
echo ""
echo "📝 What this does on every boot:"
echo "  ✅ Auto-detects USB microphone and speaker"
echo "  ✅ Configures ALSA default devices (/etc/asound.conf)"
echo "  ✅ Sets speaker volume to 100% and unmutes"
echo "  ✅ Configures microphone capture volume"
echo "  ✅ Sets PulseAudio defaults (if running)"
echo "  ✅ Configures camera permissions"
echo "  ✅ Creates device info file (/etc/roboai-devices.conf)"
echo ""
echo "📝 Useful commands:"
echo "  sudo systemctl status roboai-hardware-setup    # Check status"
echo "  sudo systemctl restart roboai-hardware-setup   # Re-run configuration"
echo "  sudo journalctl -u roboai-hardware-setup       # View logs"
echo "  cat /etc/roboai-devices.conf                   # See detected devices"
echo "  cat /etc/asound.conf                           # See ALSA config"
echo ""
echo "🔄 This service runs BEFORE agent services start!"
echo ""
