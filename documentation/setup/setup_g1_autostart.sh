#!/bin/bash

# Astra Vein Receptionist - G1 Auto-Start Setup Script
# This script sets up the receptionist agent to automatically start on boot

set -e

echo "======================================"
echo "Astra Vein Receptionist Auto-Start Setup"
echo "======================================"
echo ""

# Configuration variables
SERVICE_NAME="astra_vein_autostart"
PROJECT_DIR="/home/unitree/roboai-feature-multiple-agent-configurations"
SERVICE_FILE="${PROJECT_DIR}/${SERVICE_NAME}.service"
SYSTEMD_DIR="/etc/systemd/system"

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then 
    echo "ERROR: This script must be run with sudo"
    echo "Usage: sudo bash setup_g1_autostart.sh"
    exit 1
fi

echo "Step 1: Checking project directory..."
if [ ! -d "$PROJECT_DIR" ]; then
    echo "ERROR: Project directory not found at $PROJECT_DIR"
    echo "Please ensure the project is cloned to: $PROJECT_DIR"
    exit 1
fi
echo "✓ Project directory found"
echo ""

echo "Step 2: Checking service file..."
if [ ! -f "$SERVICE_FILE" ]; then
    echo "ERROR: Service file not found at $SERVICE_FILE"
    exit 1
fi
echo "✓ Service file found"
echo ""

echo "Step 3: Checking uv installation..."
if ! command -v uv &> /dev/null; then
    echo "WARNING: uv not found in PATH"
    echo "Installing uv for user unitree..."
    su - unitree -c "curl -LsSf https://astral.sh/uv/install.sh | sh"
fi
echo "✓ uv is available"
echo ""

echo "Step 4: Installing Python dependencies..."
cd "$PROJECT_DIR"
su - unitree -c "cd $PROJECT_DIR && uv sync"
echo "✓ Dependencies installed"
echo ""

echo "Step 5: Checking Ollama service..."
if ! systemctl is-active --quiet ollama; then
    echo "WARNING: Ollama service is not running"
    echo "The receptionist agent requires Ollama to be running"
    echo "You may need to start it manually: sudo systemctl start ollama"
else
    echo "✓ Ollama is running"
fi
echo ""

echo "Step 6: Installing systemd service..."
# Copy service file to systemd directory
cp "$SERVICE_FILE" "$SYSTEMD_DIR/${SERVICE_NAME}.service"
chmod 644 "$SYSTEMD_DIR/${SERVICE_NAME}.service"
echo "✓ Service file copied to systemd"
echo ""

echo "Step 7: Reloading systemd daemon..."
systemctl daemon-reload
echo "✓ Systemd daemon reloaded"
echo ""

echo "Step 8: Enabling service to start on boot..."
systemctl enable ${SERVICE_NAME}.service
echo "✓ Service enabled"
echo ""

echo "======================================"
echo "Installation Complete!"
echo "======================================"
echo ""
echo "The Astra Vein Receptionist will now start automatically on boot."
echo ""
echo "Useful commands:"
echo "  Start now:        sudo systemctl start ${SERVICE_NAME}"
echo "  Stop:             sudo systemctl stop ${SERVICE_NAME}"
echo "  Status:           sudo systemctl status ${SERVICE_NAME}"
echo "  View logs:        sudo journalctl -u ${SERVICE_NAME} -f"
echo "  Disable autostart: sudo systemctl disable ${SERVICE_NAME}"
echo ""
echo "To start the service now, run:"
echo "  sudo systemctl start ${SERVICE_NAME}"
echo ""
