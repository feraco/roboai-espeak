# 🚀 Complete G1 Setup - All-In-One Installation Guide

This guide will help you set up everything on your G1 robot in the correct order.

## 📦 What Gets Installed

1. **RoboAI Agent** - The main AI agent (Astra Vein receptionist or other configs)
2. **Auto-Start Service** - Makes agent start when G1 boots up
3. **Hotspot** - Creates WiFi network so you can connect without external WiFi
4. **Robostore AI** - Web control panel to manage everything from your phone

---

## 🎯 Quick Start (Just 3 Commands!)

```bash
# 1. Auto-start service
sudo ./setup_g1_autostart.sh

# 2. Hotspot
sudo ./setup_g1_hotspot.sh

# 3. Web control panel
sudo ./setup_robostore_ai.sh
```

Done! Now you can control everything from your phone.

---

## 📋 Detailed Step-by-Step

### Prerequisites

Make sure you have these files on your G1:
- `setup_g1_autostart.sh`
- `astra_vein_autostart.service`
- `setup_g1_hotspot.sh`
- `setup_robostore_ai.sh`
- `robostore-ai.service`
- `robostore_ai/` folder (contains server.py and index.html)

### Step 1: Install Auto-Start Service

This makes your agent start automatically when G1 boots up.

```bash
# Make script executable (first time only)
chmod +x setup_g1_autostart.sh

# Run installation
sudo ./setup_g1_autostart.sh
```

**What it does:**
- Installs uv package manager
- Installs Python dependencies
- Creates systemd service
- Enables auto-start on boot
- Starts the agent

**Test it:**
```bash
# Check if agent is running
systemctl status astra-vein-autostart.service

# You should see "active (running)" in green
```

### Step 2: Install Hotspot

This creates a WiFi network that you can connect to for offline control.

```bash
# Make script executable (first time only)
chmod +x setup_g1_hotspot.sh

# Run installation
sudo ./setup_g1_hotspot.sh
```

**What it does:**
- Detects WiFi adapter
- Creates hotspot named "G1-Receptionist"
- Sets password to "astra2024"
- Configures static IP: 10.42.0.1
- Can optionally auto-start on boot

**Test it:**
```bash
# Check hotspot status
sudo nmcli connection show G1-Receptionist

# Start hotspot if not running
sudo nmcli connection up G1-Receptionist
```

### Step 3: Install Robostore AI Web Interface

This gives you a simple web control panel accessible from any phone/laptop.

```bash
# Make script executable (first time only)
chmod +x setup_robostore_ai.sh

# Run installation
sudo ./setup_robostore_ai.sh
```

**What it does:**
- Installs FastAPI and dependencies
- Copies web interface files
- Creates systemd service
- Enables auto-start on boot
- Starts web server on port 8080

**Test it:**
```bash
# Check if web server is running
systemctl status robostore-ai.service

# Test web interface
curl http://localhost:8080/api/health
```

---

## ✅ Verification Checklist

After installation, verify everything works:

### 1. Agent Service
```bash
systemctl status astra-vein-autostart.service
# Should show: active (running)
```

### 2. Hotspot
```bash
nmcli connection show --active | grep G1-Receptionist
# Should show G1-Receptionist as active
```

### 3. Web Interface
```bash
systemctl status robostore-ai.service
# Should show: active (running)

curl http://localhost:8080/api/health
# Should return: {"status":"healthy","service":"robostore-ai"}
```

### 4. Full Test from Phone

1. Connect phone to WiFi "G1-Receptionist" (password: astra2024)
2. Open browser and go to: `http://10.42.0.1:8080`
3. You should see the Robostore AI control panel
4. Try pressing the RESTART button
5. Status should update to show agent running

---

## 🎮 How to Use After Installation

### From Your Phone (Easiest Way)

1. **Connect to G1's WiFi**
   - Network: `G1-Receptionist`
   - Password: `astra2024`

2. **Open Control Panel**
   - Browser: `http://10.42.0.1:8080`

3. **Control Agent**
   - START/STOP buttons
   - Switch configurations
   - Restart if needed

### From Terminal (Advanced)

```bash
# Start/Stop Agent
sudo systemctl start astra-vein-autostart.service
sudo systemctl stop astra-vein-autostart.service
sudo systemctl restart astra-vein-autostart.service

# Start/Stop Hotspot
sudo nmcli connection up G1-Receptionist
sudo nmcli connection down G1-Receptionist

# Start/Stop Web Interface
sudo systemctl start robostore-ai.service
sudo systemctl stop robostore-ai.service
```

---

## 🔧 Useful Commands

### View Logs

```bash
# Agent logs
sudo journalctl -u astra-vein-autostart.service -f

# Web interface logs
sudo journalctl -u robostore-ai.service -f

# All recent logs
sudo journalctl -xe
```

### Service Status

```bash
# Check all services
systemctl status astra-vein-autostart.service
systemctl status robostore-ai.service

# Check hotspot
nmcli connection show G1-Receptionist
```

### Restart Everything

```bash
# Restart all services
sudo systemctl restart astra-vein-autostart.service
sudo systemctl restart robostore-ai.service

# Restart hotspot
sudo nmcli connection down G1-Receptionist
sudo nmcli connection up G1-Receptionist
```

---

## 🆘 Troubleshooting

### Agent Won't Start

```bash
# Check logs for errors
sudo journalctl -u astra-vein-autostart.service -n 50

# Common issues:
# - Missing dependencies: Run setup script again
# - Config file error: Check config/astra_vein_receptionist.json5
# - Port conflict: Check if another service is using ports
```

### Hotspot Won't Start

```bash
# Check WiFi adapter
nmcli device status

# Check NetworkManager
systemctl status NetworkManager

# Restart NetworkManager
sudo systemctl restart NetworkManager

# Try manual start
sudo nmcli connection up G1-Receptionist
```

### Web Interface Won't Load

```bash
# Check if service is running
systemctl status robostore-ai.service

# Check if port 8080 is in use
sudo lsof -i :8080

# Restart web server
sudo systemctl restart robostore-ai.service

# Check logs
sudo journalctl -u robostore-ai.service -n 50
```

### Can't Connect from Phone

1. **Check hotspot is running:**
   ```bash
   nmcli connection show --active | grep G1
   ```

2. **Check phone WiFi:**
   - Network: G1-Receptionist
   - Password: astra2024 (lowercase)

3. **Try accessing:**
   - `http://10.42.0.1:8080` (not https)
   - Make sure you typed http:// not https://

4. **Disable mobile data on phone** (sometimes interferes)

---

## 🔄 Updating Configurations

### Add New Configuration

1. Copy config file to `config/` directory
2. Web interface will automatically detect it
3. Select it from dropdown in Robostore AI

### Modify Existing Configuration

```bash
# Edit config file
nano config/astra_vein_receptionist.json5

# Restart agent to apply changes
sudo systemctl restart astra-vein-autostart.service
```

---

## 📚 Related Documentation

- **ROBOSTORE_AI_GUIDE.md** - Detailed guide for using web interface
- **G1_HOTSPOT_GUIDE.md** - Detailed guide for hotspot setup
- **G1_AUTOSTART_GUIDE.md** - Detailed guide for auto-start service

---

## 🎯 Quick Reference Commands

```bash
# Installation (run once)
sudo ./setup_g1_autostart.sh      # Install agent auto-start
sudo ./setup_g1_hotspot.sh         # Install hotspot
sudo ./setup_robostore_ai.sh       # Install web interface

# Start/Stop Agent
sudo systemctl start astra-vein-autostart.service
sudo systemctl stop astra-vein-autostart.service
sudo systemctl restart astra-vein-autostart.service

# Start/Stop Hotspot
sudo nmcli connection up G1-Receptionist
sudo nmcli connection down G1-Receptionist

# View Logs
sudo journalctl -u astra-vein-autostart.service -f
sudo journalctl -u robostore-ai.service -f

# Check Status
systemctl status astra-vein-autostart.service
systemctl status robostore-ai.service
nmcli connection show --active
```

---

## 🎉 Success!

If everything is installed correctly:

- ✅ Agent starts automatically on boot
- ✅ Hotspot creates WiFi network
- ✅ Web interface accessible from phone
- ✅ You can control everything with buttons

**Access URL:** `http://10.42.0.1:8080`  
**WiFi:** G1-Receptionist (password: astra2024)

---

**Made for easy G1 setup | Version 1.0**
