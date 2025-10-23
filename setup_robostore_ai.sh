#!/bin/bash

#############################################################################
# Robostore AI Installation Script for G1
# This script installs and configures the Robostore AI web interface
# 
# SUPER SIMPLE FOR NON-TECHNICAL USERS:
# Just run: sudo ./setup_robostore_ai.sh
#############################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
INSTALL_DIR="/root/roboai"
SERVICE_FILE="robostore-ai.service"
SERVICE_PATH="/etc/systemd/system/${SERVICE_FILE}"
WEB_PORT=8080

# Print colored message
print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Print section header
print_header() {
    echo ""
    print_message "$BLUE" "============================================"
    print_message "$BLUE" "$1"
    print_message "$BLUE" "============================================"
}

# Check if running as root
check_root() {
    if [ "$EUID" -ne 0 ]; then
        print_message "$RED" "❌ Error: This script must be run as root (use sudo)"
        exit 1
    fi
}

# Check if roboai is installed
check_roboai_installation() {
    print_header "Checking Installation"
    
    if [ ! -d "$INSTALL_DIR" ]; then
        print_message "$RED" "❌ Error: RoboAI not found at $INSTALL_DIR"
        print_message "$YELLOW" "Please install RoboAI first, then run this script"
        exit 1
    fi
    
    print_message "$GREEN" "✓ RoboAI installation found"
}

# Install Python dependencies
install_dependencies() {
    print_header "Installing Dependencies"
    
    print_message "$YELLOW" "Installing FastAPI, Uvicorn, and pyjson5..."
    
    cd "$INSTALL_DIR"
    
    # Check if uv is installed
    if ! command -v uv &> /dev/null; then
        print_message "$YELLOW" "Installing uv package manager..."
        curl -LsSf https://astral.sh/uv/install.sh | sh
        export PATH="$HOME/.cargo/bin:$PATH"
    fi
    
    # Install dependencies
    uv pip install fastapi uvicorn pyjson5 --system || {
        print_message "$RED" "❌ Failed to install dependencies"
        exit 1
    }
    
    print_message "$GREEN" "✓ Dependencies installed"
}

# Copy Robostore AI files
install_robostore_files() {
    print_header "Installing Robostore AI Files"
    
    # Get the directory where this script is located
    SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
    
    # Check if robostore_ai directory exists in script directory
    if [ ! -d "${SCRIPT_DIR}/robostore_ai" ]; then
        print_message "$RED" "❌ Error: robostore_ai directory not found"
        print_message "$YELLOW" "Please ensure robostore_ai folder is in the same directory as this script"
        exit 1
    fi
    
    # Copy robostore_ai directory to install location
    print_message "$YELLOW" "Copying Robostore AI files to ${INSTALL_DIR}/robostore_ai..."
    cp -r "${SCRIPT_DIR}/robostore_ai" "$INSTALL_DIR/"
    
    # Make server.py executable
    chmod +x "${INSTALL_DIR}/robostore_ai/server.py"
    
    print_message "$GREEN" "✓ Robostore AI files installed"
}

# Install systemd service
install_service() {
    print_header "Installing Systemd Service"
    
    # Get the directory where this script is located
    SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
    
    if [ ! -f "${SCRIPT_DIR}/${SERVICE_FILE}" ]; then
        print_message "$RED" "❌ Error: ${SERVICE_FILE} not found"
        exit 1
    fi
    
    print_message "$YELLOW" "Installing service file..."
    cp "${SCRIPT_DIR}/${SERVICE_FILE}" "$SERVICE_PATH"
    
    print_message "$YELLOW" "Reloading systemd..."
    systemctl daemon-reload
    
    print_message "$GREEN" "✓ Service installed"
}

# Configure sudoers for web interface
configure_sudoers() {
    print_header "Configuring Permissions"
    
    print_message "$YELLOW" "Setting up sudoers for web interface..."
    
    # Create sudoers rule to allow web interface to control systemd without password
    SUDOERS_FILE="/etc/sudoers.d/robostore-ai"
    
    cat > "$SUDOERS_FILE" << 'EOF'
# Allow Robostore AI to control agent service
root ALL=(ALL) NOPASSWD: /bin/systemctl start astra-vein-autostart.service
root ALL=(ALL) NOPASSWD: /bin/systemctl stop astra-vein-autostart.service
root ALL=(ALL) NOPASSWD: /bin/systemctl restart astra-vein-autostart.service
root ALL=(ALL) NOPASSWD: /bin/systemctl status astra-vein-autostart.service
root ALL=(ALL) NOPASSWD: /bin/systemctl daemon-reload
EOF
    
    chmod 0440 "$SUDOERS_FILE"
    
    print_message "$GREEN" "✓ Permissions configured"
}

# Enable and start service
enable_service() {
    print_header "Starting Robostore AI"
    
    print_message "$YELLOW" "Enabling service to start on boot..."
    systemctl enable "$SERVICE_FILE"
    
    print_message "$YELLOW" "Starting Robostore AI service..."
    systemctl start "$SERVICE_FILE"
    
    # Wait a moment for service to start
    sleep 2
    
    # Check if service is running
    if systemctl is-active --quiet "$SERVICE_FILE"; then
        print_message "$GREEN" "✓ Robostore AI is running!"
    else
        print_message "$RED" "❌ Service failed to start. Checking logs..."
        systemctl status "$SERVICE_FILE" --no-pager
        exit 1
    fi
}

# Test web interface
test_interface() {
    print_header "Testing Web Interface"
    
    print_message "$YELLOW" "Testing connection to http://localhost:${WEB_PORT}..."
    
    sleep 2
    
    if curl -s -f "http://localhost:${WEB_PORT}/api/health" > /dev/null; then
        print_message "$GREEN" "✓ Web interface is accessible!"
    else
        print_message "$YELLOW" "⚠ Warning: Could not reach web interface (this is OK if hotspot is not running yet)"
    fi
}

# Print success message
print_success() {
    print_header "Installation Complete!"
    
    echo ""
    print_message "$GREEN" "🎉 Robostore AI has been installed successfully!"
    echo ""
    print_message "$BLUE" "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    print_message "$BLUE" "HOW TO USE (SUPER SIMPLE):"
    print_message "$BLUE" "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    print_message "$YELLOW" "1. Connect your phone to the G1 hotspot"
    print_message "$YELLOW" "   WiFi Name: G1-Receptionist"
    print_message "$YELLOW" "   Password: astra2024"
    echo ""
    print_message "$YELLOW" "2. Open your phone's browser and go to:"
    print_message "$GREEN" "   http://10.42.0.1:${WEB_PORT}"
    echo ""
    print_message "$YELLOW" "3. You'll see a simple control panel with big buttons:"
    print_message "$GREEN" "   • START button - Turn on the agent"
    print_message "$GREEN" "   • STOP button - Turn off the agent"
    print_message "$GREEN" "   • RESTART button - Restart the agent"
    print_message "$GREEN" "   • Config dropdown - Switch between different personalities"
    echo ""
    print_message "$BLUE" "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    print_message "$BLUE" "USEFUL COMMANDS:"
    print_message "$BLUE" "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    print_message "$YELLOW" "Check if Robostore AI is running:"
    print_message "$NC" "  systemctl status ${SERVICE_FILE}"
    echo ""
    print_message "$YELLOW" "Stop Robostore AI:"
    print_message "$NC" "  sudo systemctl stop ${SERVICE_FILE}"
    echo ""
    print_message "$YELLOW" "Start Robostore AI:"
    print_message "$NC" "  sudo systemctl start ${SERVICE_FILE}"
    echo ""
    print_message "$YELLOW" "View logs:"
    print_message "$NC" "  sudo journalctl -u ${SERVICE_FILE} -f"
    echo ""
    print_message "$BLUE" "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    print_message "$GREEN" "For more details, read: ROBOSTORE_AI_GUIDE.md"
    echo ""
}

# Main installation flow
main() {
    print_header "Robostore AI Installation"
    print_message "$YELLOW" "This will install the web control panel for your G1 agent"
    echo ""
    
    check_root
    check_roboai_installation
    install_dependencies
    install_robostore_files
    install_service
    configure_sudoers
    enable_service
    test_interface
    print_success
}

# Run main function
main
