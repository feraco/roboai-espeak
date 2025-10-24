# Astra Vein Receptionist - G1 Auto-Start Guide

This guide explains how to set up the Astra Vein Receptionist agent to automatically start when your Unitree G1 robot boots up.

## Prerequisites

1. **Unitree G1 robot** running Ubuntu/Linux
2. **SSH access** to the G1
3. **This project** cloned to `/home/unitree/roboai-feature-multiple-agent-configurations`
4. **Ollama** installed and running on the G1
5. **sudo/root access** on the G1

## Quick Setup

### 1. Transfer Files to G1

From your development machine, copy the project to the G1:

```bash
# Replace <G1_IP> with your robot's IP address
scp -r /path/to/roboai-feature-multiple-agent-configurations unitree@<G1_IP>:/home/unitree/
```

### 2. SSH into the G1

```bash
ssh unitree@<G1_IP>
```

### 3. Run the Auto-Start Setup Script

```bash
cd /home/unitree/roboai-feature-multiple-agent-configurations
chmod +x setup_g1_autostart.sh
sudo ./setup_g1_autostart.sh
```

The script will:
- ✅ Check all dependencies
- ✅ Install Python packages with `uv`
- ✅ Install the systemd service
- ✅ Enable auto-start on boot

### 4. Start the Service Now (Optional)

To test immediately without rebooting:

```bash
sudo systemctl start astra_vein_autostart
```

Check the status:

```bash
sudo systemctl status astra_vein_autostart
```

### 5. Reboot to Test Auto-Start

```bash
sudo reboot
```

After reboot, the receptionist should start automatically!

## Management Commands

### View Real-Time Logs

```bash
sudo journalctl -u astra_vein_autostart -f
```

### Check Service Status

```bash
sudo systemctl status astra_vein_autostart
```

### Stop the Service

```bash
sudo systemctl stop astra_vein_autostart
```

### Restart the Service

```bash
sudo systemctl restart astra_vein_autostart
```

### Disable Auto-Start

```bash
sudo systemctl disable astra_vein_autostart
```

### Re-Enable Auto-Start

```bash
sudo systemctl enable astra_vein_autostart
```

## Troubleshooting

### Service Won't Start

1. **Check Ollama is running:**
   ```bash
   sudo systemctl status ollama
   sudo systemctl start ollama  # If not running
   ```

2. **Check audio devices:**
   ```bash
   aplay -l  # List playback devices
   arecord -l  # List recording devices
   ```

3. **View detailed logs:**
   ```bash
   sudo journalctl -u astra_vein_autostart -n 100
   ```

### Camera Not Working

Ensure the camera is accessible:
```bash
ls -l /dev/video*
```

Add the `unitree` user to the video group if needed:
```bash
sudo usermod -a -G video unitree
```

### Permission Issues

Ensure the `unitree` user owns the project files:
```bash
sudo chown -R unitree:unitree /home/unitree/roboai-feature-multiple-agent-configurations
```

### Service Crashes or Restarts

The service is configured to automatically restart on failure with a 10-second delay. Check logs to diagnose:

```bash
sudo journalctl -u astra_vein_autostart -n 50
```

## Configuration Changes

After modifying the configuration file (`config/astra_vein_receptionist.json5`):

1. **Option A: Restart the service** (keeps auto-start enabled)
   ```bash
   sudo systemctl restart astra_vein_autostart
   ```

2. **Option B: Stop, modify, then start**
   ```bash
   sudo systemctl stop astra_vein_autostart
   # Make your changes
   sudo systemctl start astra_vein_autostart
   ```

## Customization

### Change the Startup Delay

Edit `/etc/systemd/system/astra_vein_autostart.service`:

```ini
ExecStartPre=/bin/sleep 10  # Change to desired seconds
```

Then reload:
```bash
sudo systemctl daemon-reload
sudo systemctl restart astra_vein_autostart
```

### Change Resource Limits

Edit the service file to adjust:
- `CPUQuota=80%` - CPU usage limit
- `MemoryLimit=2G` - RAM limit
- `Nice=-10` - Process priority

### Run as Different User

Change the `User=` line in the service file to your preferred user.

## Uninstall

To completely remove the auto-start:

```bash
sudo systemctl stop astra_vein_autostart
sudo systemctl disable astra_vein_autostart
sudo rm /etc/systemd/system/astra_vein_autostart.service
sudo systemctl daemon-reload
```

## Multiple Agents

To run multiple agents on boot, create separate service files:

1. Copy `astra_vein_autostart.service` to a new name
2. Change the `ExecStart` line to use a different config
3. Follow the same setup process

Example:
```bash
cp astra_vein_autostart.service another_agent.service
# Edit another_agent.service and change config name
sudo cp another_agent.service /etc/systemd/system/
sudo systemctl enable another_agent
sudo systemctl start another_agent
```

## Support

For issues or questions, check:
- Service logs: `sudo journalctl -u astra_vein_autostart -f`
- System logs: `sudo journalctl -xe`
- Project README: `/home/unitree/roboai-feature-multiple-agent-configurations/README.md`
