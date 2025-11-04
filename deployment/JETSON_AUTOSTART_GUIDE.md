# Auto-Start Lex on Boot - Detailed Systemd Guide for Jetson

## Overview

This guide will help you configure Lex Channel Chief to automatically start when your Jetson boots up using systemd services.

---

## Part 1: Understanding Systemd Services

### What is Systemd?
- Linux system and service manager
- Handles starting/stopping services
- Manages dependencies between services
- Automatic restart on failure
- Logs to system journal

### Why Use Systemd for Lex?
- ✅ Starts automatically on boot
- ✅ Restarts if crashes
- ✅ Waits for Ollama to be ready
- ✅ Proper logging and monitoring
- ✅ Easy control with systemctl commands

---

## Part 2: Pre-Setup Checklist

Before creating the service, verify everything works manually:

```bash
# 1. Check Ollama is running
sudo systemctl status ollama
# Should show: active (running)

# 2. Test Ollama model
ollama list
# Should show: gemma2:2b

# 3. Navigate to project
cd ~/roboai-feature-multiple-agent-configurations

# 4. Test Lex runs manually
uv run src/run.py lex_channel_chief
# Should start without errors
# Press Ctrl+C to stop

# 5. Verify UV path
which uv
# Should show: /home/jetson/.cargo/bin/uv
# (or similar path with your username)

# 6. Get your username
whoami
# Note this for the service file
```

**⚠️ If any step fails, fix it before proceeding!**

---

## Part 3: Create Systemd Service File

### Step 1: Create Service File

```bash
# Create the service file with nano
sudo nano /etc/systemd/system/lex-channel-chief.service
```

### Step 2: Add Service Configuration

**Copy and paste this EXACTLY** (adjust paths if needed):

```ini
[Unit]
Description=Lex Channel Chief AI Agent
Documentation=https://github.com/feraco/roboai-espeak
After=network-online.target ollama.service
Wants=network-online.target
Requires=ollama.service

[Service]
Type=simple
User=jetson
Group=jetson
WorkingDirectory=/home/jetson/roboai-feature-multiple-agent-configurations

# Environment setup
Environment="PATH=/home/jetson/.cargo/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
Environment="HOME=/home/jetson"
Environment="RUST_LOG=info"

# Main command to run
ExecStart=/home/jetson/.cargo/bin/uv run src/run.py lex_channel_chief

# Restart configuration
Restart=always
RestartSec=10
StartLimitInterval=200
StartLimitBurst=5

# Resource limits (adjust for your Jetson)
MemoryMax=4G
CPUQuota=200%

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=lex-channel-chief

# Security (optional but recommended)
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

### Step 3: Save and Exit

- Press `Ctrl+O` to save
- Press `Enter` to confirm
- Press `Ctrl+X` to exit

---

## Part 4: Customize for Your Setup

### Option A: Different Username

If your username is NOT "jetson", replace all instances:

```bash
# Edit the service file
sudo nano /etc/systemd/system/lex-channel-chief.service

# Replace:
User=jetson              → User=YOUR_USERNAME
Group=jetson             → Group=YOUR_USERNAME
WorkingDirectory=/home/jetson/...  → WorkingDirectory=/home/YOUR_USERNAME/...
Environment="HOME=/home/jetson"    → Environment="HOME=/home/YOUR_USERNAME"
ExecStart=/home/jetson/.cargo/...  → ExecStart=/home/YOUR_USERNAME/.cargo/...
```

### Option B: Different Project Location

If project is NOT in `~/roboai-feature-multiple-agent-configurations`:

```bash
# Edit the service file
sudo nano /etc/systemd/system/lex-channel-chief.service

# Update WorkingDirectory:
WorkingDirectory=/path/to/your/project
```

### Option C: Different Agent Config

To run a different agent instead of lex_channel_chief:

```bash
# Edit the service file
sudo nano /etc/systemd/system/lex-channel-chief.service

# Change ExecStart line:
ExecStart=/home/jetson/.cargo/bin/uv run src/run.py YOUR_AGENT_NAME

# Examples:
# ExecStart=/home/jetson/.cargo/bin/uv run src/run.py local_agent
# ExecStart=/home/jetson/.cargo/bin/uv run src/run.py voice_only_greeter
```

### Option D: Different UV Location

If UV is installed elsewhere:

```bash
# Find UV location
which uv
# Example output: /usr/local/bin/uv

# Edit service file
sudo nano /etc/systemd/system/lex-channel-chief.service

# Update Environment PATH and ExecStart:
Environment="PATH=/usr/local/bin:/usr/local/sbin:..."
ExecStart=/usr/local/bin/uv run src/run.py lex_channel_chief
```

---

## Part 5: Activate the Service

### Step 1: Reload Systemd

```bash
# Tell systemd to read the new service file
sudo systemctl daemon-reload
```

### Step 2: Enable Auto-Start

```bash
# Enable the service to start on boot
sudo systemctl enable lex-channel-chief.service

# You should see:
# Created symlink /etc/systemd/system/multi-user.target.wants/lex-channel-chief.service
```

### Step 3: Start the Service Now

```bash
# Start the service immediately (without rebooting)
sudo systemctl start lex-channel-chief.service
```

### Step 4: Check Status

```bash
# Check if service is running
sudo systemctl status lex-channel-chief.service
```

**Expected output:**
```
● lex-channel-chief.service - Lex Channel Chief AI Agent
     Loaded: loaded (/etc/systemd/system/lex-channel-chief.service; enabled)
     Active: active (running) since Mon 2025-11-04 10:30:45 PST; 5s ago
   Main PID: 12345 (uv)
      Tasks: 15
     Memory: 2.5G
        CPU: 3.2s
     CGroup: /system.slice/lex-channel-chief.service
             └─12345 /home/jetson/.cargo/bin/uv run src/run.py lex_channel_chief

Nov 04 10:30:45 jetson systemd[1]: Started Lex Channel Chief AI Agent.
Nov 04 10:30:46 jetson lex-channel-chief[12345]: INFO - Loaded Faster-Whisper model
Nov 04 10:30:47 jetson lex-channel-chief[12345]: INFO - Found cam(0)
Nov 04 10:30:48 jetson lex-channel-chief[12345]: INFO - Starting OM1 with standard configuration
```

---

## Part 6: Verify Auto-Start Works

### Test 1: Reboot Test

```bash
# Reboot the Jetson
sudo reboot

# After reboot, wait 1-2 minutes for full boot

# Check if service started automatically
sudo systemctl status lex-channel-chief.service

# Should show: active (running)
```

### Test 2: Crash Recovery Test

```bash
# Find the Lex process ID
sudo systemctl status lex-channel-chief.service
# Note the Main PID (e.g., 12345)

# Kill the process (simulating a crash)
sudo kill -9 12345

# Wait 10 seconds (RestartSec=10 in config)
sleep 10

# Check status - should be running again
sudo systemctl status lex-channel-chief.service

# Should show: active (running) with NEW PID
```

### Test 3: Dependency Test

```bash
# Stop Ollama (Lex depends on it)
sudo systemctl stop ollama

# Check Lex status
sudo systemctl status lex-channel-chief.service

# Should show: activating (auto-restart) or inactive

# Start Ollama again
sudo systemctl start ollama

# Wait 10 seconds
sleep 10

# Check Lex - should restart automatically
sudo systemctl status lex-channel-chief.service

# Should show: active (running)
```

---

## Part 7: Control Commands

### Basic Commands

```bash
# Start service
sudo systemctl start lex-channel-chief.service

# Stop service
sudo systemctl stop lex-channel-chief.service

# Restart service
sudo systemctl restart lex-channel-chief.service

# Check status
sudo systemctl status lex-channel-chief.service

# Enable auto-start on boot
sudo systemctl enable lex-channel-chief.service

# Disable auto-start on boot
sudo systemctl disable lex-channel-chief.service

# Check if enabled
sudo systemctl is-enabled lex-channel-chief.service
# Output: enabled or disabled

# Check if running
sudo systemctl is-active lex-channel-chief.service
# Output: active or inactive
```

### Advanced Commands

```bash
# View full service configuration
systemctl cat lex-channel-chief.service

# Check service dependencies
systemctl list-dependencies lex-channel-chief.service

# Check what services depend on this
systemctl list-dependencies --reverse lex-channel-chief.service

# Show service properties
systemctl show lex-channel-chief.service

# Reload service file after editing (without restarting)
sudo systemctl daemon-reload

# Reset failed state
sudo systemctl reset-failed lex-channel-chief.service
```

---

## Part 8: View Logs

### Real-Time Logs

```bash
# Follow logs in real-time (like tail -f)
sudo journalctl -u lex-channel-chief.service -f

# Press Ctrl+C to stop following
```

### Historical Logs

```bash
# View all logs
sudo journalctl -u lex-channel-chief.service

# View last 50 lines
sudo journalctl -u lex-channel-chief.service -n 50

# View last 100 lines
sudo journalctl -u lex-channel-chief.service -n 100

# View logs since boot
sudo journalctl -u lex-channel-chief.service -b

# View logs from last hour
sudo journalctl -u lex-channel-chief.service --since "1 hour ago"

# View logs from today
sudo journalctl -u lex-channel-chief.service --since today

# View logs between specific times
sudo journalctl -u lex-channel-chief.service --since "2025-11-04 10:00:00" --until "2025-11-04 11:00:00"

# View logs with priority level
sudo journalctl -u lex-channel-chief.service -p err
# Levels: emerg, alert, crit, err, warning, notice, info, debug
```

### Log Output Options

```bash
# View logs with timestamps
sudo journalctl -u lex-channel-chief.service -o short-iso

# View logs in JSON format
sudo journalctl -u lex-channel-chief.service -o json

# Export logs to file
sudo journalctl -u lex-channel-chief.service > lex_logs.txt

# View logs in reverse order (newest first)
sudo journalctl -u lex-channel-chief.service -r
```

---

## Part 9: Troubleshooting

### Service Won't Start

```bash
# Check status for errors
sudo systemctl status lex-channel-chief.service -l

# View detailed logs
sudo journalctl -u lex-channel-chief.service -n 100 --no-pager

# Common issues:

# 1. Wrong path
# Edit service file:
sudo nano /etc/systemd/system/lex-channel-chief.service
# Verify WorkingDirectory and ExecStart paths

# 2. Wrong user
# Edit service file:
sudo nano /etc/systemd/system/lex-channel-chief.service
# Verify User= matches your username

# 3. UV not found
which uv
# Update PATH in service file

# 4. Permission issues
sudo chown -R jetson:jetson ~/roboai-feature-multiple-agent-configurations

# After ANY edit:
sudo systemctl daemon-reload
sudo systemctl restart lex-channel-chief.service
```

### Service Starts But Crashes

```bash
# Check logs for errors
sudo journalctl -u lex-channel-chief.service -n 200

# Common issues:

# 1. Ollama not running
sudo systemctl status ollama
sudo systemctl start ollama

# 2. Missing dependencies
cd ~/roboai-feature-multiple-agent-configurations
uv sync

# 3. Ollama model missing
ollama list
ollama pull gemma2:2b

# 4. Out of memory
free -h
# If low memory, use smaller model (llama3.2:1b)
```

### Service Restarts Too Often

```bash
# Check restart count
systemctl show lex-channel-chief.service -p NRestarts

# If high number, check logs
sudo journalctl -u lex-channel-chief.service -n 500

# Increase restart delay
sudo nano /etc/systemd/system/lex-channel-chief.service
# Change: RestartSec=30  (instead of 10)

# Reload and restart
sudo systemctl daemon-reload
sudo systemctl restart lex-channel-chief.service
```

### Check Boot Sequence

```bash
# View boot logs to see when Lex starts
sudo journalctl -b | grep lex-channel-chief

# View systemd boot analysis
systemd-analyze blame

# Check if delayed by dependencies
systemd-analyze critical-chain lex-channel-chief.service
```

---

## Part 10: Monitoring and Maintenance

### Create Monitoring Script

Create `~/monitor_lex.sh`:

```bash
#!/bin/bash

echo "=== Lex Channel Chief Status ==="
echo ""

# Service status
if systemctl is-active --quiet lex-channel-chief.service; then
    echo "✅ Service Status: RUNNING"
    
    # Get PID
    PID=$(systemctl show -p MainPID --value lex-channel-chief.service)
    echo "   Process ID: $PID"
    
    # Get uptime
    UPTIME=$(systemctl show -p ActiveEnterTimestamp --value lex-channel-chief.service)
    echo "   Started: $UPTIME"
    
    # Get memory usage
    MEM=$(systemctl show -p MemoryCurrent --value lex-channel-chief.service)
    MEM_MB=$((MEM / 1024 / 1024))
    echo "   Memory: ${MEM_MB} MB"
    
    # Get CPU usage
    CPU=$(systemctl show -p CPUUsageNSec --value lex-channel-chief.service)
    echo "   CPU Time: $((CPU / 1000000000)) seconds"
    
else
    echo "❌ Service Status: NOT RUNNING"
fi

echo ""
echo "=== Ollama Status ==="
if systemctl is-active --quiet ollama; then
    echo "✅ Ollama: RUNNING"
else
    echo "❌ Ollama: NOT RUNNING"
fi

echo ""
echo "=== System Resources ==="
echo "Memory:"
free -h | grep Mem | awk '{print "   Total: "$2" | Used: "$3" | Free: "$4}'

echo ""
echo "=== Recent Errors (last 5) ==="
sudo journalctl -u lex-channel-chief.service -p err -n 5 --no-pager | tail -n 5

echo ""
echo "=== Restart Count ==="
RESTARTS=$(systemctl show -p NRestarts --value lex-channel-chief.service)
echo "   Service has restarted $RESTARTS times"

echo ""
echo "=== Auto-Start Status ==="
if systemctl is-enabled --quiet lex-channel-chief.service; then
    echo "✅ Auto-start on boot: ENABLED"
else
    echo "❌ Auto-start on boot: DISABLED"
fi
```

Make executable:
```bash
chmod +x ~/monitor_lex.sh
```

Run anytime:
```bash
~/monitor_lex.sh
```

### Create Auto-Restart Script

Create `~/restart_lex_if_needed.sh`:

```bash
#!/bin/bash

# Check if Lex is running
if ! systemctl is-active --quiet lex-channel-chief.service; then
    echo "[$(date)] Lex is not running. Starting..."
    sudo systemctl start lex-channel-chief.service
    
    # Wait 10 seconds and check again
    sleep 10
    
    if systemctl is-active --quiet lex-channel-chief.service; then
        echo "[$(date)] Lex started successfully"
    else
        echo "[$(date)] Failed to start Lex"
        # Send alert (optional - configure email/notification)
    fi
else
    echo "[$(date)] Lex is running normally"
fi
```

Make executable:
```bash
chmod +x ~/restart_lex_if_needed.sh
```

### Add to Cron (Optional)

Check Lex every 5 minutes:

```bash
# Edit crontab
crontab -e

# Add this line:
*/5 * * * * /home/jetson/restart_lex_if_needed.sh >> /home/jetson/lex_monitor.log 2>&1

# Save and exit
```

---

## Part 11: Update Service After Code Changes

When you update the project code:

```bash
# Method 1: Simple restart
sudo systemctl restart lex-channel-chief.service

# Method 2: Full reload (if service file changed)
sudo systemctl daemon-reload
sudo systemctl restart lex-channel-chief.service

# Method 3: Update code and restart
cd ~/roboai-feature-multiple-agent-configurations
git pull origin main
uv sync
sudo systemctl restart lex-channel-chief.service

# Verify it's running
sudo systemctl status lex-channel-chief.service
```

---

## Part 12: Disable/Remove Service

### Temporarily Disable

```bash
# Disable auto-start but keep service file
sudo systemctl disable lex-channel-chief.service
sudo systemctl stop lex-channel-chief.service

# Verify disabled
systemctl is-enabled lex-channel-chief.service
# Should show: disabled
```

### Completely Remove

```bash
# Stop and disable
sudo systemctl stop lex-channel-chief.service
sudo systemctl disable lex-channel-chief.service

# Remove service file
sudo rm /etc/systemd/system/lex-channel-chief.service

# Reload systemd
sudo systemctl daemon-reload

# Reset failed state (if any)
sudo systemctl reset-failed
```

---

## Part 13: Multiple Services (Advanced)

If you want to run multiple agents simultaneously:

### Create Second Service

```bash
# Create new service file
sudo nano /etc/systemd/system/lex-voice-only.service
```

Content:
```ini
[Unit]
Description=Lex Voice Only Agent
After=network-online.target ollama.service
Requires=ollama.service

[Service]
Type=simple
User=jetson
WorkingDirectory=/home/jetson/roboai-feature-multiple-agent-configurations
Environment="PATH=/home/jetson/.cargo/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
ExecStart=/home/jetson/.cargo/bin/uv run src/run.py voice_only_greeter
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable lex-voice-only.service
sudo systemctl start lex-voice-only.service
```

---

## Quick Reference

### Service File Location
```
/etc/systemd/system/lex-channel-chief.service
```

### Essential Commands
```bash
# Start
sudo systemctl start lex-channel-chief.service

# Stop
sudo systemctl stop lex-channel-chief.service

# Restart
sudo systemctl restart lex-channel-chief.service

# Status
sudo systemctl status lex-channel-chief.service

# Logs
sudo journalctl -u lex-channel-chief.service -f

# Enable auto-start
sudo systemctl enable lex-channel-chief.service

# After editing service file
sudo systemctl daemon-reload
```

### Verification Checklist

- [ ] Service file created in `/etc/systemd/system/`
- [ ] Paths verified (User, WorkingDirectory, ExecStart)
- [ ] `systemctl daemon-reload` executed
- [ ] Service enabled with `systemctl enable`
- [ ] Service started with `systemctl start`
- [ ] Status shows "active (running)"
- [ ] Logs show normal startup messages
- [ ] Reboot test successful
- [ ] Crash recovery test successful
- [ ] Monitoring script created and tested

---

## Troubleshooting Flowchart

```
Service not starting?
│
├─ Check status: sudo systemctl status lex-channel-chief.service
│  │
│  ├─ Shows "not found"?
│  │  └─ Check file exists: ls -la /etc/systemd/system/lex-channel-chief.service
│  │     └─ Run: sudo systemctl daemon-reload
│  │
│  ├─ Shows "failed"?
│  │  └─ View logs: sudo journalctl -u lex-channel-chief.service -n 50
│  │     │
│  │     ├─ "No such file or directory"?
│  │     │  └─ Fix paths in service file
│  │     │
│  │     ├─ "Permission denied"?
│  │     │  └─ Fix ownership: sudo chown -R jetson:jetson ~/roboai-feature-multiple-agent-configurations
│  │     │
│  │     └─ "command not found"?
│  │        └─ Fix UV path: which uv, update service file
│  │
│  └─ Shows "inactive"?
│     └─ Start it: sudo systemctl start lex-channel-chief.service

```

---

## Success! 🎉

Your Lex Channel Chief should now:
- ✅ Start automatically when Jetson boots
- ✅ Restart automatically if it crashes
- ✅ Wait for Ollama to be ready
- ✅ Log to system journal
- ✅ Be controllable with systemctl commands

For any issues, check the logs:
```bash
sudo journalctl -u lex-channel-chief.service -f
```
