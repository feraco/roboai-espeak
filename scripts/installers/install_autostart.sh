#!/bin/bash
# Install Astra Agent as a systemd service for auto-start on boot

set -e

SERVICE_NAME="astra_agent.service"
SERVICE_FILE="$(pwd)/$SERVICE_NAME"
SYSTEMD_DIR="/etc/systemd/system"
INSTALL_DIR="$(pwd)"
USER="$(whoami)"

echo "🚀 Installing Astra Agent Auto-Start Service"
echo "=============================================="
echo ""
echo "Install directory: $INSTALL_DIR"
echo "User: $USER"
echo "Service: $SERVICE_NAME"
echo ""

# Check if service file exists
if [ ! -f "$SERVICE_FILE" ]; then
    echo "❌ Error: $SERVICE_FILE not found"
    echo "   Make sure you're running this from the roboai-espeak directory"
    exit 1
fi

# Update service file with actual user and install directory
echo "📝 Configuring service file..."
TEMP_SERVICE="/tmp/$SERVICE_NAME"

sed -e "s|User=ubuntu|User=$USER|g" \
    -e "s|Group=ubuntu|Group=$USER|g" \
    -e "s|WorkingDirectory=/home/ubuntu/roboai-espeak|WorkingDirectory=$INSTALL_DIR|g" \
    -e "s|/home/ubuntu/.local/bin/uv|$(which uv)|g" \
    -e "s|/home/ubuntu/.ollama|$HOME/.ollama|g" \
    -e "s|/home/ubuntu/roboai-espeak|$INSTALL_DIR|g" \
    -e "s|/run/user/1000/pulse|/run/user/$(id -u)/pulse|g" \
    "$SERVICE_FILE" > "$TEMP_SERVICE"

echo "   ✅ Service configured for user: $USER"

# Install service
echo ""
echo "📦 Installing service to $SYSTEMD_DIR..."
sudo cp "$TEMP_SERVICE" "$SYSTEMD_DIR/$SERVICE_NAME"
sudo chmod 644 "$SYSTEMD_DIR/$SERVICE_NAME"
echo "   ✅ Service file installed"

# Reload systemd
echo ""
echo "🔄 Reloading systemd..."
sudo systemctl daemon-reload
echo "   ✅ Systemd reloaded"

# Enable service
echo ""
echo "🔧 Enabling service to start on boot..."
sudo systemctl enable "$SERVICE_NAME"
echo "   ✅ Service enabled"

# Show service status
echo ""
echo "=============================================="
echo "✅ Installation Complete!"
echo "=============================================="
echo ""
echo "📋 Service Management Commands:"
echo ""
echo "Start agent now:"
echo "  sudo systemctl start $SERVICE_NAME"
echo ""
echo "Stop agent:"
echo "  sudo systemctl stop $SERVICE_NAME"
echo ""
echo "Check status:"
echo "  sudo systemctl status $SERVICE_NAME"
echo ""
echo "View logs:"
echo "  sudo journalctl -u $SERVICE_NAME -f"
echo ""
echo "Disable auto-start:"
echo "  sudo systemctl disable $SERVICE_NAME"
echo ""
echo "⚠️  Note: The agent will start automatically on next boot!"
echo ""
echo "Would you like to start the agent now? (y/n)"
read -r response

if [[ "$response" =~ ^[Yy]$ ]]; then
    echo ""
    echo "🚀 Starting agent..."
    sudo systemctl start "$SERVICE_NAME"
    sleep 2
    sudo systemctl status "$SERVICE_NAME" --no-pager
    echo ""
    echo "✅ Agent started! View logs with:"
    echo "   sudo journalctl -u $SERVICE_NAME -f"
else
    echo ""
    echo "👍 Agent will start automatically on next boot"
    echo "   Or start manually with: sudo systemctl start $SERVICE_NAME"
fi

# Cleanup
rm -f "$TEMP_SERVICE"
