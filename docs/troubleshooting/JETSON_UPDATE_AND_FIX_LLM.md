# Jetson Update - Fix "No output from LLM" Error

This error happens when Ollama is not responding properly. The latest code includes LLM validation that prevents this.

---

## Step 1: Stop Everything and Pull Latest Code

```bash
cd ~/roboai/roboai-espeak

# Stop any running agents
pkill -9 -f "src/run.py"

# Stop service if installed
sudo systemctl stop astra_agent 2>/dev/null || true

# Check current git status
git status

# Stash any local changes
git stash

# Pull latest updates (includes LLM validation)
git pull origin main

# Update dependencies
uv sync

# Clear old audio config
rm -f device_config.yaml
```

---

## Step 2: Fix Ollama (Most Common Cause)

```bash
# Restart Ollama service
sudo systemctl restart ollama

# Wait for it to start
sleep 5

# Test if Ollama is responding
ollama run llama3.1:8b "Reply with just OK"

# If that hangs or errors, run the nuclear reset:
sudo systemctl stop ollama
rm -rf ~/.ollama/models/manifests/registry.ollama.ai/library/llama3.1/*
sudo systemctl start ollama
sleep 5
ollama pull llama3.1:8b
```

---

## Step 3: Test Agent Manually

```bash
cd ~/roboai/roboai-espeak

# Run agent - should now show LLM validation
uv run src/run.py lex_channel_chief

# You should see:
# 🤖 LLM VALIDATION (Pre-Start)
# ✅ Ollama service is running
# ✅ Model 'llama3.1:8b' available
# ✅ Model responds correctly
# ✅ LLM validation PASSED

# If validation FAILS, it will show you exactly what's wrong
```

---

## Step 4: Common LLM Errors and Fixes

### Error: "Ollama API error" or "No output from LLM"

```bash
# Check if Ollama is running
systemctl status ollama

# If not running:
sudo systemctl start ollama

# If running but not responding:
sudo systemctl restart ollama
sleep 5
ollama run llama3.1:8b "test"
```

### Error: "Model not found"

```bash
# Pull the model
ollama pull llama3.1:8b

# Verify it's there
ollama list
```

### Error: "Model test timed out"

```bash
# Not enough RAM - try smaller model
ollama pull llama3.2:3b

# Then edit your config to use llama3.2:3b instead
```

---

## Step 5: If Manual Run Works, Update Auto-Start Service

```bash
cd ~/roboai/roboai-espeak

# Stop old service
sudo systemctl stop astra_agent

# Create updated service file for unitree user
cat > astra_agent.service << 'EOF'
[Unit]
Description=Astra Vein Receptionist AI Agent
After=network-online.target ollama.service sound.target
Wants=network-online.target ollama.service

[Service]
Type=simple
User=unitree
Group=unitree
WorkingDirectory=/home/unitree/roboai/roboai-espeak
Environment="PATH=/home/unitree/.local/bin:/usr/local/bin:/usr/bin:/bin"
Environment="DISPLAY=:0"
Environment="XAUTHORITY=/home/unitree/.Xauthority"
Environment="DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus"
Environment="PULSE_SERVER=unix:/run/user/1000/pulse/native"
Environment="XDG_RUNTIME_DIR=/run/user/1000"
Environment="SKIP_AUDIO_VALIDATION=true"

# Wait for system to be fully ready
ExecStartPre=/bin/sleep 15

# Ensure Ollama is running
ExecStartPre=/bin/bash -c "systemctl is-active ollama || sudo systemctl start ollama"
ExecStartPre=/bin/sleep 5

# Test Ollama model before starting (NEW - prevents "No output from LLM")
ExecStartPre=/bin/bash -c "timeout 20 ollama run llama3.1:8b 'Reply OK' || exit 1"

# Clear stale audio configs
ExecStartPre=/bin/bash -c "cd /home/unitree/roboai/roboai-espeak && rm -f device_config.yaml"

# Start agent with LLM validation
ExecStart=/home/unitree/.local/bin/uv run /home/unitree/roboai/roboai-espeak/src/run.py astra_vein_receptionist

# Restart on failure
Restart=on-failure
RestartSec=10

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=astra-agent

[Install]
WantedBy=multi-user.target
EOF

# Install updated service
sudo cp astra_agent.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable and start
sudo systemctl enable astra_agent
sudo systemctl start astra_agent

# Check status
sudo systemctl status astra_agent

# Watch logs
sudo journalctl -u astra_agent -f
```

---

## Step 6: Verify Everything Works

```bash
# Check service status
sudo systemctl status astra_agent

# Should show:
# Active: active (running)

# Check logs for LLM validation
sudo journalctl -u astra_agent -n 100 | grep -A 5 "LLM VALIDATION"

# You should see:
# ✅ LLM validation PASSED
```

---

## Step 7: Test Auto-Start on Reboot

```bash
# Verify auto-start is enabled
sudo systemctl is-enabled astra_agent

# Should show: enabled

# Test reboot (optional)
sudo reboot

# After reboot, SSH back in and check:
sudo systemctl status astra_agent
sudo journalctl -u astra_agent -n 50
```

---

## Quick Diagnostic Commands

```bash
# Check Ollama status
systemctl status ollama

# Test Ollama model
ollama run llama3.1:8b "test"

# List available models
ollama list

# Check agent service
sudo systemctl status astra_agent

# View agent logs
sudo journalctl -u astra_agent -n 50

# Restart everything
sudo systemctl restart ollama
sleep 5
sudo systemctl restart astra_agent
```

---

## What the New LLM Validation Does

The updated code now validates Ollama BEFORE starting the agent:

1. ✅ Checks if Ollama service is running
2. ✅ Verifies model is downloaded
3. ✅ Tests model responds to prompts
4. ✅ Auto-starts Ollama if needed
5. ✅ Shows detailed error messages if fails

This prevents the "Ollama API error" and "No output from LLM" issues you were seeing!

---

## Expected Output After Update

```
🤖 LLM VALIDATION (Pre-Start)
======================================================================
📡 Checking Ollama service...
✅ Ollama service is running
📦 Checking if model 'llama3.1:8b' is downloaded...
✅ Model 'llama3.1:8b' is available
🧪 Testing model inference (timeout: 20s)...
   Sending test prompt: 'Reply with just OK'
✅ Model responds correctly
======================================================================
✅ LLM validation PASSED - agent can start
======================================================================
```

If you see this, your LLM is working correctly! 🚀
