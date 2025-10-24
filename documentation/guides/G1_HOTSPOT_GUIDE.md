# G1 WiFi Hotspot Guide - Offline Config Editing

This guide explains how to set up the Unitree G1 as a WiFi hotspot, allowing you to connect your phone or laptop directly to the robot and edit configurations without any external WiFi network.

## 🎯 What This Enables

- ✅ Edit configs from your phone/laptop anywhere
- ✅ No external WiFi network needed
- ✅ Works completely offline
- ✅ Direct SSH access to G1
- ✅ Web-based file editing option
- ✅ Perfect for medical offices, labs, or remote locations

## 📱 Quick Start

### Step 1: Initial Setup (One-Time)

Connect to the G1 via ethernet or existing WiFi, then run:

```bash
# SSH into G1
ssh unitree@<G1_IP>

# Navigate to project
cd /home/unitree/roboai-feature-multiple-agent-configurations

# Make script executable
chmod +x setup_g1_hotspot.sh

# Run setup
sudo ./setup_g1_hotspot.sh
```

The script will:
1. Install NetworkManager and dnsmasq
2. Create a WiFi hotspot named "G1-Receptionist"
3. Set password to "astra2025"
4. Configure IP address (10.42.0.1)
5. Create management scripts
6. Optionally enable auto-start on boot

### Step 2: Connect to Hotspot

**From Your Phone/Laptop:**

1. **Open WiFi Settings**
2. **Connect to:** `G1-Receptionist`
3. **Password:** `astra2025`
4. **Wait 5 seconds** for connection

### Step 3: Edit Configs

**Option A: SSH via Mobile App (Recommended)**

1. **Install Termius** (iOS/Android - Free)
2. **Add New Host:**
   - Label: `G1 Receptionist`
   - Hostname: `10.42.0.1`
   - Username: `unitree`
   - Password: (G1 unitree password)
3. **Connect**
4. **Edit config:**
   ```bash
   nano ~/roboai-feature-multiple-agent-configurations/config/astra_vein_receptionist.json5
   ```
5. **Save:** Ctrl+O, Enter, Ctrl+X
6. **Restart service:**
   ```bash
   sudo systemctl restart astra_vein_autostart
   ```

**Option B: Laptop SSH**

```bash
ssh unitree@10.42.0.1
nano ~/roboai-feature-multiple-agent-configurations/config/astra_vein_receptionist.json5
# Make changes, save, restart service
sudo systemctl restart astra_vein_autostart
```

**Option C: Web Browser (After Filebrowser Setup)**

1. Open browser
2. Go to: `http://10.42.0.1:8080`
3. Edit config visually
4. Save changes
5. SSH in to restart service (or add auto-restart)

## 🎛️ Management Commands

These commands are created during setup:

### Start Hotspot
```bash
sudo g1-hotspot-start
```

### Stop Hotspot
```bash
sudo g1-hotspot-stop
```

### Check Status
```bash
g1-hotspot-status
```

### View Connected Devices
```bash
g1-hotspot-status
# or
arp -n | grep "10.42.0"
```

## 🌐 Advanced: Web-Based Config Editor

For the easiest editing experience, install Filebrowser:

### Install Filebrowser

```bash
# SSH into G1
ssh unitree@10.42.0.1

# Install Filebrowser
curl -fsSL https://raw.githubusercontent.com/filebrowser/get/master/get.sh | bash

# Create config directory
mkdir -p /home/unitree/.filebrowser

# Start Filebrowser
filebrowser -r /home/unitree -p 8080 -a 0.0.0.0 -d /home/unitree/.filebrowser/filebrowser.db
```

### Make Filebrowser Auto-Start

```bash
# Create systemd service
sudo nano /etc/systemd/system/filebrowser.service
```

Paste this:

```ini
[Unit]
Description=Filebrowser
After=network.target

[Service]
Type=simple
User=unitree
WorkingDirectory=/home/unitree
ExecStart=/usr/local/bin/filebrowser -r /home/unitree -p 8080 -a 0.0.0.0 -d /home/unitree/.filebrowser/filebrowser.db
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Enable it:

```bash
sudo systemctl daemon-reload
sudo systemctl enable filebrowser
sudo systemctl start filebrowser
```

### Use Filebrowser

1. Connect to G1 hotspot
2. Open browser: `http://10.42.0.1:8080`
3. Login (default: admin/admin)
4. Navigate to: `roboai-feature-multiple-agent-configurations/config/`
5. Click `astra_vein_receptionist.json5`
6. Edit in browser!
7. Save changes

## 📋 Common Workflows

### Workflow 1: Quick Setting Change (Mobile)

```
Time: ~2 minutes

1. Connect phone to "G1-Receptionist" WiFi
2. Open Termius app
3. Connect to saved G1 host
4. Run: nano ~/roboai-feature-multiple-agent-configurations/config/astra_vein_receptionist.json5
5. Change setting (e.g., chunk_duration: 3.0 → 4.0)
6. Save and exit (Ctrl+O, Enter, Ctrl+X)
7. Restart: sudo systemctl restart astra_vein_autostart
8. Done!
```

### Workflow 2: Visual Editing (Laptop/Tablet)

```
Time: ~1 minute

1. Connect to "G1-Receptionist" WiFi
2. Open browser: http://10.42.0.1:8080
3. Click through to config file
4. Edit visually
5. Click Save
6. SSH in: ssh unitree@10.42.0.1
7. Restart: sudo systemctl restart astra_vein_autostart
8. Done!
```

### Workflow 3: Bulk Config Updates

```
Time: ~3 minutes

1. Connect laptop to G1 hotspot
2. Use SCP to copy new configs:
   scp astra_vein_*.json5 unitree@10.42.0.1:~/roboai-feature-multiple-agent-configurations/config/
3. SSH in: ssh unitree@10.42.0.1
4. Restart: sudo systemctl restart astra_vein_autostart
5. Done!
```

## 🔧 Troubleshooting

### Hotspot Won't Start

**Check WiFi interface:**
```bash
nmcli device
# Should show a WiFi interface (usually wlan0)
```

**Check NetworkManager:**
```bash
sudo systemctl status NetworkManager
# Should be active and running
```

**Restart NetworkManager:**
```bash
sudo systemctl restart NetworkManager
sudo g1-hotspot-start
```

### Can't Connect to Hotspot

**Verify hotspot is running:**
```bash
g1-hotspot-status
```

**Check firewall:**
```bash
sudo ufw status
# If active, allow SSH:
sudo ufw allow 22/tcp
sudo ufw allow 8080/tcp
```

**Restart hotspot:**
```bash
sudo g1-hotspot-stop
sudo g1-hotspot-start
```

### Connected but Can't SSH

**Check G1 IP:**
```bash
ip addr show wlan0
# Should show 10.42.0.1
```

**Check SSH is running:**
```bash
sudo systemctl status ssh
# Should be active
```

**Try with verbose SSH:**
```bash
ssh -vvv unitree@10.42.0.1
```

### Web Browser Not Working

**Check Filebrowser is running:**
```bash
sudo systemctl status filebrowser
```

**Test locally on G1:**
```bash
curl http://localhost:8080
# Should return HTML
```

**Restart Filebrowser:**
```bash
sudo systemctl restart filebrowser
```

## 🔐 Security Considerations

### Change Default Password

Edit hotspot password:
```bash
sudo nmcli connection modify "G1-Receptionist" wifi-sec.psk "your-new-password"
sudo g1-hotspot-stop
sudo g1-hotspot-start
```

### Change Filebrowser Password

1. Browse to: `http://10.42.0.1:8080`
2. Login with admin/admin
3. Click Settings (gear icon)
4. Go to User Management
5. Change password

### Disable Hotspot Auto-Start

If you don't want the hotspot to start automatically:
```bash
sudo systemctl disable g1-hotspot.service
```

Start manually only when needed:
```bash
sudo g1-hotspot-start
```

## 🚀 Pro Tips

### Tip 1: Bookmark G1 IP
Save `http://10.42.0.1:8080` as a bookmark on your phone for instant access

### Tip 2: Save SSH Config
Create `~/.ssh/config` on your laptop:
```
Host g1
    HostName 10.42.0.1
    User unitree
    ServerAliveInterval 60
```

Then just: `ssh g1`

### Tip 3: Use VS Code Remote
1. Install VS Code on tablet/laptop
2. Install Remote-SSH extension
3. Connect to: `unitree@10.42.0.1`
4. Edit configs with full IDE features!

### Tip 4: Multiple Config Presets
Keep multiple configs in the folder:
```
config/
├── astra_vein_receptionist.json5          # Active
├── presets/
│   ├── loud_mode.json5
│   ├── quiet_mode.json5
│   └── fast_mode.json5
```

Quick switch via SSH:
```bash
cp config/presets/loud_mode.json5 config/astra_vein_receptionist.json5
sudo systemctl restart astra_vein_autostart
```

## 📱 Recommended Mobile Apps

### iOS
- **Termius** - Best SSH client (Free)
- **Safari** - For Filebrowser web interface
- **Working Copy** - Git client (if using version control)

### Android  
- **Termius** - Cross-platform (Free)
- **Chrome** - For Filebrowser web interface
- **JuiceSSH** - Alternative SSH client

## 🎉 Summary

Once set up, editing G1 configs is as simple as:

1. **Connect phone to "G1-Receptionist" WiFi**
2. **Open Termius or browser**
3. **Edit config in 2 minutes**
4. **Restart service**
5. **Done!**

No cables, no external WiFi, works anywhere! 🚀
