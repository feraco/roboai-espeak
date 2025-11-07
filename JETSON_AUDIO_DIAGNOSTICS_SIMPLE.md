# Jetson Audio Diagnostics - Simple Commands

Copy and paste these sections one at a time.

---

## Section 1: Check if Audio System is Working

```bash
# List all audio playback devices (ALSA)
aplay -l

# List all audio recording devices
arecord -l

# Test speaker with simple tone (Ctrl+C to stop)
speaker-test -t sine -f 1000 -c 2
```

---

## Section 2: Test if PulseAudio is Running

```bash
# Check if pulseaudio process exists
ps aux | grep pulseaudio

# If not running, start it:
pulseaudio --start

# Check PulseAudio status
pulseaudio --check && echo "PulseAudio is running" || echo "PulseAudio is NOT running"
```

---

## Section 3: Install PulseAudio Tools (If Missing)

```bash
# Install PulseAudio utilities
sudo apt update
sudo apt install -y pulseaudio pulseaudio-utils

# Start PulseAudio
pulseaudio --start

# Now try these commands:
pactl list sinks short
pactl get-default-sink
```

---

## Section 4: Test Audio Output Directly

```bash
# Generate a test sound file
speaker-test -t wav -c 2 -l 1 -w /tmp/test.wav

# Play it with ALSA
aplay /tmp/test.wav

# If you hear sound, audio hardware works!
```

---

## Section 5: Check What Agent is Using for Audio

```bash
cd ~/roboai/roboai-espeak

# Check what play command Piper is configured to use
grep -r "play_command\|aplay\|paplay" config/

# Test Piper TTS directly
echo "This is a test" | piper \
  --model ./piper_voices/en_US-ryan-medium.onnx \
  --output_file /tmp/test_piper.wav

# Play the generated file
aplay /tmp/test_piper.wav
```

---

## Section 6: Simple Audio Output Fix

```bash
# Method 1: Use ALSA directly (bypass PulseAudio)
cd ~/roboai/roboai-espeak

# Check config for play_command
cat config/astra_vein_receptionist.json5 | grep -A 2 "play_command"

# If it says "null" or missing, add this to config:
# "play_command": "aplay"

# Or create a test with forced aplay:
uv run python -c "
import subprocess
import os
os.system('echo \"Testing audio output\" | piper --model ./piper_voices/en_US-ryan-medium.onnx --output_file /tmp/test.wav && aplay /tmp/test.wav')
"
```

---

## Section 7: Check Service Audio Environment

```bash
# If running as service, check what user it runs as
systemctl show astra_agent | grep User

# Check if that user has access to audio
groups unitree

# User should be in 'audio' group - if not, add them:
sudo usermod -aG audio unitree

# Log out and back in for group change to take effect
```

---

## Section 8: Nuclear Audio Reset

```bash
# Stop everything
pkill -9 -f "src/run.py"
sudo systemctl stop astra_agent

# Kill PulseAudio
pulseaudio --kill
sleep 2

# Restart PulseAudio
pulseaudio --start
sleep 2

# Test speaker
speaker-test -t wav -c 2 -l 1

# If you hear sound, restart agent:
cd ~/roboai/roboai-espeak
uv run src/run.py astra_vein_receptionist
```

---

## Section 9: Force Agent to Use ALSA (Bypass PulseAudio Issues)

```bash
cd ~/roboai/roboai-espeak

# Edit the config to force aplay usage
nano config/astra_vein_receptionist.json5

# Find the "speak" action section and ensure it has:
# "play_command": "aplay"

# Or use sed to add it:
sed -i 's/"play_command": null/"play_command": "aplay"/' config/astra_vein_receptionist.json5

# Test the agent
uv run src/run.py astra_vein_receptionist
```

---

## Section 10: Check What's Actually Happening in Logs

```bash
# Stop service
sudo systemctl stop astra_agent

# Run manually with verbose output
cd ~/roboai/roboai-espeak
uv run src/run.py astra_vein_receptionist 2>&1 | tee /tmp/agent_output.log

# In another terminal, watch for audio commands:
tail -f /tmp/agent_output.log | grep -i "playing\|audio\|speak\|piper\|aplay"

# Speak to the agent and see what commands it runs
```

---

## What to Look For

When you speak to the agent, you should see in logs:

```
✅ GOOD - Audio is working:
INFO - Speaking: "Hello! How can I help you?"
INFO - Playing audio file: audio_output/response_12345.wav
INFO - Audio playback completed successfully

❌ BAD - Audio is NOT working:
INFO - Speaking: "Hello! How can I help you?"
ERROR - Could not play audio file
ERROR - aplay command not found
ERROR - Permission denied
```

---

## Quick Test Commands

```bash
# Test 1: Hardware works?
aplay -l

# Test 2: Can generate sound?
speaker-test -t wav -c 2 -l 1

# Test 3: Can Piper create files?
echo "test" | piper --model ./piper_voices/en_US-ryan-medium.onnx --output_file /tmp/test.wav && ls -lh /tmp/test.wav

# Test 4: Can play Piper output?
aplay /tmp/test.wav

# If all 4 work, the problem is in how the agent/service is configured
```

---

## Most Common Fix

**Problem:** Agent creates audio files but doesn't play them.

**Solution:** Force agent to use `aplay` instead of PulseAudio:

```bash
cd ~/roboai/roboai-espeak

# Update config
python3 << 'EOF'
import json5
with open('config/astra_vein_receptionist.json5', 'r') as f:
    config = json5.load(f)

# Find speak action and set play_command
for action in config['agent_actions']:
    if action['name'] == 'speak':
        action['config']['play_command'] = 'aplay'
        print(f"✅ Updated speak action to use aplay")

with open('config/astra_vein_receptionist.json5', 'w') as f:
    json5.dump(config, f, indent=2)
EOF

# Test
uv run src/run.py astra_vein_receptionist
```
