# Jetson Ollama Fix - Complete Instructions

## Problem
Getting "no output from llm" error when running Lex Channel Chief on Jetson.

## Root Cause
- Ollama has too many models loaded in memory
- Models are corrupted or cache is stale
- Not enough memory for the model to run properly

## Solution Steps

### Step 1: Stop All Running Processes

```bash
# Stop any running agent
pkill -f "lex_channel_chief"
pkill -f "src/run.py"

# Stop Ollama service
sudo systemctl stop ollama
```

### Step 2: Check Current Ollama Models

```bash
# List all installed models
ollama list
```

You should see something like:
```
NAME                    ID              SIZE      MODIFIED
llama3.2:1b            abc123def       1.3 GB    2 days ago
gemma2:2b              xyz789abc       1.6 GB    1 day ago
llava:latest           def456ghi       4.9 GB    3 days ago
```

### Step 3: Remove ALL Ollama Models

```bash
# Remove each model (replace with your actual model names from ollama list)
ollama rm llama3.2:1b
ollama rm gemma2:2b
ollama rm llava:latest
ollama rm llama3.1:8b
ollama rm phi3:mini

# Verify all removed
ollama list
# Should show: No models found
```

### Step 4: Clear Ollama Cache and Restart

```bash
# Stop Ollama completely
sudo systemctl stop ollama
sleep 3

# Clear cache directories
rm -rf ~/.ollama/models/*
sudo rm -rf /usr/share/ollama/.ollama/models/*

# Restart Ollama service
sudo systemctl start ollama
sleep 5

# Check Ollama is running
sudo systemctl status ollama
# Should show: active (running)
```

### Step 5: Pull Only the Required Model

```bash
# Pull ONLY gemma2:2b (lightweight model for Jetson)
ollama pull gemma2:2b

# Wait for download to complete
# Should see: success
```

### Step 6: Test Ollama Directly

```bash
# Test that Ollama responds properly
curl -X POST http://localhost:11434/api/generate -d '{
  "model": "gemma2:2b",
  "prompt": "Hello",
  "stream": false
}'
```

**Expected output**: JSON response with "response" field containing text

**If you get an error**: Ollama is not working properly, restart from Step 4

### Step 7: Verify System Resources

```bash
# Check available memory
free -h

# Should show at least 2GB free memory:
# Total: ~8GB
# Used: ~4-5GB  
# Free: ~2-3GB

# If memory is low, reboot:
sudo reboot
```

### Step 8: Navigate to Project and Run Lex

```bash
# Navigate to project directory
cd ~/roboai-feature-multiple-agent-configurations

# Or wherever your project is located:
cd /path/to/roboai-feature-multiple-agent-configurations

# Activate environment (if using virtualenv)
source venv/bin/activate

# Or if using uv:
uv sync
```

### Step 9: Run Lex Channel Chief

```bash
# Run with uv
uv run src/run.py lex_channel_chief

# Or with python directly
python3 src/run.py lex_channel_chief
```

### Step 10: Verify It's Working

Look for these log messages:
```
✅ INFO - Loaded Faster-Whisper model: tiny.en
✅ INFO - Found cam(0)
✅ INFO - Ollama LLM: System context set
✅ INFO - Starting OM1 with standard configuration: lex_channel_chief
✅ INFO - LocalASRInput: Using sample rate 16000 Hz
```

**Test voice input**: Speak into the microphone and you should see:
```
INFO - === ASR INPUT ===
[LANG:en] Hello
INFO - === LLM OUTPUT ===
{"actions": [...]}
```

---

## Quick Fix Commands (Copy-Paste)

```bash
# Complete fix in one command block
sudo systemctl stop ollama && \
sleep 3 && \
rm -rf ~/.ollama/models/* && \
sudo systemctl start ollama && \
sleep 5 && \
ollama rm llama3.2:1b 2>/dev/null; \
ollama rm gemma2:2b 2>/dev/null; \
ollama rm llava:latest 2>/dev/null; \
ollama rm llama3.1:8b 2>/dev/null; \
ollama pull gemma2:2b && \
echo "✅ Ollama fixed! Test with: curl -X POST http://localhost:11434/api/generate -d '{\"model\": \"gemma2:2b\", \"prompt\": \"Hello\", \"stream\": false}'"
```

---

## Troubleshooting

### Issue: "connection refused" when testing Ollama
**Solution**:
```bash
sudo systemctl restart ollama
sleep 5
sudo systemctl status ollama
```

### Issue: Ollama service won't start
**Solution**:
```bash
# Check logs
sudo journalctl -u ollama -f

# If port conflict, kill existing process:
sudo lsof -i :11434
sudo kill -9 <PID>
sudo systemctl start ollama
```

### Issue: Still getting "no output from llm"
**Solution**:
```bash
# Check Ollama is actually responding
curl http://localhost:11434/api/tags

# Should return list of models
# If empty or error, repeat from Step 4
```

### Issue: Out of memory on Jetson
**Solution**:
```bash
# Check memory
free -h

# Clear system cache
sudo sync
sudo sh -c 'echo 3 > /proc/sys/vm/drop_caches'

# Use smaller model (if not already)
ollama rm gemma2:2b
ollama pull llama3.2:1b  # Even smaller (1GB vs 1.6GB)

# Update lex_channel_chief.json5 model to "llama3.2:1b"
```

### Issue: Camera not detected
**Solution**:
```bash
# List cameras
ls -l /dev/video*

# Test camera 0
ffmpeg -f v4l2 -list_formats all -i /dev/video0

# If camera not at index 0, update config:
# camera_index: 1  # or 2, 3, etc.
```

### Issue: Audio input not working
**Solution**:
```bash
# List audio devices
arecord -l

# Test microphone
arecord -d 3 test.wav
aplay test.wav

# If wrong device, update config with correct device ID
```

---

## Memory Optimization for Jetson

### Current Memory Footprint:
- **gemma2:2b**: ~1.6GB
- **faster-whisper tiny.en**: ~75MB  
- **DeepFace + TensorFlow**: ~200-300MB
- **System overhead**: ~500MB
- **Total**: ~2.5GB

### If You Need Even Less Memory:

1. **Use llama3.2:1b instead**:
   ```bash
   ollama rm gemma2:2b
   ollama pull llama3.2:1b
   ```
   Update `config/lex_channel_chief.json5`:
   ```json5
   cortex_llm: {
     type: "OllamaLLM",
     config: {
       model: "llama3.2:1b",  // Changed from gemma2:2b
       // ... rest of config
     }
   }
   ```

2. **Disable vision if needed**:
   Comment out FaceEmotionCapture in config to save ~300MB

3. **Use smaller Whisper model**:
   Change `model_size: "tiny.en"` to `model_size: "base.en"` (even smaller)

---

## Automated Monitoring Script

Create `~/check_ollama.sh`:

```bash
#!/bin/bash
# Ollama health check script

echo "🔍 Checking Ollama status..."

# Check service
if systemctl is-active --quiet ollama; then
    echo "✅ Ollama service: running"
else
    echo "❌ Ollama service: stopped"
    exit 1
fi

# Check API
if curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "✅ Ollama API: responding"
else
    echo "❌ Ollama API: not responding"
    exit 1
fi

# Check models
MODEL_COUNT=$(ollama list | tail -n +2 | wc -l)
echo "📦 Models installed: $MODEL_COUNT"
ollama list

# Check memory
FREE_MEM=$(free -h | grep Mem | awk '{print $4}')
echo "💾 Free memory: $FREE_MEM"

# Test inference
echo "🧪 Testing inference..."
RESPONSE=$(curl -s -X POST http://localhost:11434/api/generate -d '{"model": "gemma2:2b", "prompt": "Hi", "stream": false}' | jq -r '.response')

if [ -n "$RESPONSE" ]; then
    echo "✅ Inference test: PASSED"
    echo "   Response: $RESPONSE"
else
    echo "❌ Inference test: FAILED"
    exit 1
fi

echo ""
echo "🎉 All checks passed!"
```

Make executable:
```bash
chmod +x ~/check_ollama.sh
```

Run anytime:
```bash
~/check_ollama.sh
```

---

## Auto-Start on Boot (Optional)

Create systemd service for Lex:

```bash
sudo nano /etc/systemd/system/lex-channel-chief.service
```

Content:
```ini
[Unit]
Description=Lex Channel Chief Service
After=ollama.service
Requires=ollama.service

[Service]
Type=simple
User=jetson
WorkingDirectory=/home/jetson/roboai-feature-multiple-agent-configurations
ExecStart=/usr/local/bin/uv run src/run.py lex_channel_chief
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable lex-channel-chief.service
sudo systemctl start lex-channel-chief.service

# Check status
sudo systemctl status lex-channel-chief.service
```

---

## Summary Checklist

- [ ] Stop Ollama and all agents
- [ ] Remove ALL models with `ollama rm`
- [ ] Clear cache directories
- [ ] Restart Ollama service
- [ ] Pull ONLY gemma2:2b
- [ ] Test Ollama with curl
- [ ] Check memory (should have 2GB+ free)
- [ ] Run Lex Channel Chief
- [ ] Test voice input
- [ ] Test vision (if camera available)

---

## Emergency Reset

If nothing works, complete reset:

```bash
# Stop everything
sudo systemctl stop ollama
sudo systemctl stop lex-channel-chief 2>/dev/null
pkill -9 -f ollama
pkill -9 -f lex_channel_chief

# Remove Ollama completely
sudo apt remove ollama -y
sudo rm -rf /usr/share/ollama
sudo rm -rf ~/.ollama
sudo rm -rf /usr/local/bin/ollama

# Reinstall Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Wait for installation
sleep 10

# Start service
sudo systemctl start ollama
sleep 5

# Pull model
ollama pull gemma2:2b

# Test
curl -X POST http://localhost:11434/api/generate -d '{"model": "gemma2:2b", "prompt": "Test", "stream": false}'
```

---

## Contact for Help

If still having issues, collect these logs:

```bash
# Ollama logs
sudo journalctl -u ollama -n 100 > ollama_logs.txt

# System info
free -h > system_info.txt
df -h >> system_info.txt
ollama list >> system_info.txt

# Test output
curl -X POST http://localhost:11434/api/generate -d '{"model": "gemma2:2b", "prompt": "Test", "stream": false}' > ollama_test.txt 2>&1
```

Share these files for debugging.
