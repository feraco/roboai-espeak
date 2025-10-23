#!/bin/bash

# G1 Hotspot Setup Script
# Creates a WiFi hotspot on the G1 for offline config editing

set -e

echo "======================================"
echo "G1 WiFi Hotspot Setup"
echo "======================================"
echo ""

# Configuration
HOTSPOT_SSID="G1-Receptionist"
HOTSPOT_PASSWORD="astra2025"
HOTSPOT_IP="10.42.0.1"

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "ERROR: This script must be run with sudo"
    echo "Usage: sudo bash setup_g1_hotspot.sh"
    exit 1
fi

echo "Hotspot Configuration:"
echo "  SSID: $HOTSPOT_SSID"
echo "  Password: $HOTSPOT_PASSWORD"
echo "  G1 IP Address: $HOTSPOT_IP"
echo ""
read -p "Continue with these settings? (y/n): " confirm

if [ "$confirm" != "y" ]; then
    echo "Cancelled."
    exit 0
fi

echo ""
echo "Step 1: Installing NetworkManager (if needed)..."
if ! command -v nmcli &> /dev/null; then
    apt-get update
    apt-get install -y network-manager
fi
echo "✓ NetworkManager installed"
echo ""

echo "Step 2: Checking WiFi interface..."
WIFI_INTERFACE=$(nmcli device | grep wifi | awk '{print $1}' | head -n1)

if [ -z "$WIFI_INTERFACE" ]; then
    echo "ERROR: No WiFi interface found!"
    echo "Available interfaces:"
    nmcli device
    exit 1
fi

echo "✓ Found WiFi interface: $WIFI_INTERFACE"
echo ""

echo "Step 3: Creating hotspot connection..."
# Delete old hotspot if exists
nmcli connection delete "$HOTSPOT_SSID" 2>/dev/null || true

# Create new hotspot
nmcli device wifi hotspot \
    ifname "$WIFI_INTERFACE" \
    con-name "$HOTSPOT_SSID" \
    ssid "$HOTSPOT_SSID" \
    password "$HOTSPOT_PASSWORD"

echo "✓ Hotspot created"
echo ""

echo "Step 4: Configuring hotspot settings..."
# Set static IP
nmcli connection modify "$HOTSPOT_SSID" \
    ipv4.addresses "$HOTSPOT_IP/24" \
    ipv4.method shared

# Enable autoconnect
nmcli connection modify "$HOTSPOT_SSID" \
    connection.autoconnect yes \
    connection.autoconnect-priority 100

echo "✓ Hotspot configured"
echo ""

echo "Step 5: Installing and configuring dnsmasq (DHCP/DNS)..."
if ! command -v dnsmasq &> /dev/null; then
    apt-get install -y dnsmasq
fi

# Configure dnsmasq for hotspot
cat > /etc/dnsmasq.d/g1-hotspot.conf << EOF
# G1 Hotspot DHCP Configuration
interface=wlan0
dhcp-range=10.42.0.10,10.42.0.50,12h
dhcp-option=3,10.42.0.1
dhcp-option=6,10.42.0.1
bind-interfaces
EOF

systemctl restart dnsmasq
echo "✓ DHCP server configured"
echo ""

echo "Step 6: Creating hotspot control scripts..."

# Create start script
cat > /usr/local/bin/g1-hotspot-start << 'EOF'
#!/bin/bash
echo "Starting G1 hotspot..."
nmcli connection up "G1-Receptionist"
sleep 2
systemctl restart dnsmasq
echo "Hotspot started!"
echo ""
echo "Network Details:"
echo "  SSID: G1-Receptionist"
echo "  Password: astra2025"
echo "  G1 IP: 10.42.0.1"
echo ""
echo "Connect your device and SSH to: unitree@10.42.0.1"
EOF

# Create stop script
cat > /usr/local/bin/g1-hotspot-stop << 'EOF'
#!/bin/bash
echo "Stopping G1 hotspot..."
nmcli connection down "G1-Receptionist"
echo "Hotspot stopped."
EOF

# Create status script
cat > /usr/local/bin/g1-hotspot-status << 'EOF'
#!/bin/bash
CONNECTION_STATUS=$(nmcli -t -f NAME,DEVICE,STATE connection show | grep "G1-Receptionist")

if echo "$CONNECTION_STATUS" | grep -q "activated"; then
    echo "✓ Hotspot is ACTIVE"
    echo ""
    echo "Network Details:"
    echo "  SSID: G1-Receptionist"
    echo "  Password: astra2025"
    echo "  G1 IP Address: 10.42.0.1"
    echo ""
    echo "Connected devices:"
    arp -n | grep "10.42.0" | grep -v "10.42.0.1"
    echo ""
    echo "To connect:"
    echo "  1. Connect to WiFi: G1-Receptionist"
    echo "  2. SSH: ssh unitree@10.42.0.1"
    echo "  3. Edit config: nano ~/roboai-feature-multiple-agent-configurations/config/astra_vein_receptionist.json5"
else
    echo "✗ Hotspot is INACTIVE"
    echo ""
    echo "To start: sudo g1-hotspot-start"
fi
EOF

# Make scripts executable
chmod +x /usr/local/bin/g1-hotspot-start
chmod +x /usr/local/bin/g1-hotspot-stop
chmod +x /usr/local/bin/g1-hotspot-status

echo "✓ Control scripts created"
echo ""

echo "Step 7: Setting up auto-start on boot (optional)..."
read -p "Start hotspot automatically on boot? (y/n): " autostart

if [ "$autostart" == "y" ]; then
    # Create systemd service for auto-start
    cat > /etc/systemd/system/g1-hotspot.service << EOF
[Unit]
Description=G1 WiFi Hotspot
After=network.target NetworkManager.service
Wants=NetworkManager.service

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/usr/local/bin/g1-hotspot-start
ExecStop=/usr/local/bin/g1-hotspot-stop

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable g1-hotspot.service
    echo "✓ Auto-start enabled"
else
    echo "⊘ Auto-start skipped"
fi
echo ""

echo "Step 8: Starting hotspot now..."
/usr/local/bin/g1-hotspot-start
echo ""

echo "======================================"
echo "Setup Complete!"
echo "======================================"
echo ""
echo "📱 HOTSPOT ACTIVE"
echo ""
echo "Network Information:"
echo "  SSID: $HOTSPOT_SSID"
echo "  Password: $HOTSPOT_PASSWORD"
echo "  G1 IP Address: $HOTSPOT_IP"
echo ""
echo "🔧 How to Connect and Edit Config:"
echo ""
echo "  1. On your phone/laptop, connect to WiFi:"
echo "     SSID: $HOTSPOT_SSID"
echo "     Password: $HOTSPOT_PASSWORD"
echo ""
echo "  2. SSH to the G1:"
echo "     ssh unitree@$HOTSPOT_IP"
echo ""
echo "  3. Edit the config:"
echo "     nano ~/roboai-feature-multiple-agent-configurations/config/astra_vein_receptionist.json5"
echo ""
echo "  4. Restart the service:"
echo "     sudo systemctl restart astra_vein_autostart"
echo ""
echo "📱 Alternative: Use Mobile SSH App"
echo "  - Download: Termius (iOS/Android)"
echo "  - Add host: unitree@$HOTSPOT_IP"
echo "  - Edit configs from your phone!"
echo ""
echo "🎛️  Management Commands:"
echo "  Start hotspot:  sudo g1-hotspot-start"
echo "  Stop hotspot:   sudo g1-hotspot-stop"
echo "  Check status:   g1-hotspot-status"
echo ""
echo "💡 Pro Tip: Install Filebrowser for web-based editing:"
echo "  curl -fsSL https://raw.githubusercontent.com/filebrowser/get/master/get.sh | bash"
echo "  filebrowser -r /home/unitree -p 8080 -a 0.0.0.0"
echo "  Then browse to: http://$HOTSPOT_IP:8080"
echo ""
