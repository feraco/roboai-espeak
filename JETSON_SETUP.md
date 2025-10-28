# Complete Setup Guide for Jetson Orin

This guide covers everything from scratch: UV package manager → Ollama → Audio → Running the agent.

---

## 📋 Prerequisites

- Jetson Orin running Ubuntu 20.04 or 22.04
- Internet connection (for initial setup)
- Microphone and speaker connected
- Camera connected (optional, for vision features)

---

## Step 1: Install UV Package Manager

UV is a fast Python package manager that replaces pip/venv.

```bash
# Install UV
curl -LsSf https://astral.sh/uv/install.sh | sh

# Add to PATH (if not auto-added)
echo 'export PATH="$HOME/.cargo/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# Verify installation
uv --version
```

---

## Step 2: Install Ollama (Local LLM)

Ollama runs local language models like Llama 3.1.

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Start Ollama service
sudo systemctl enable ollama
sudo systemctl start ollama

# Verify Ollama is running
curl http://localhost:11434

# Download models (this will take time - models are large!)
# For LLM (text generation)
ollama pull llama3.1:8b          # ~4.7 GB - Main language model

# For Vision (image analysis)
ollama pull llava-llama3          # ~4.9 GB - Vision model

# Verify models are installed
ollama list
```

**Expected output:**
```
NAME              ID              SIZE      MODIFIED
llama3.1:8b       f66fc8dc39ea    4.7 GB    2 minutes ago
llava-llama3      2d9946e5c53d    4.9 GB    5 minutes ago
```

---

## Step 3: Clone Repository

```bash
# Clone the repository
cd ~
git clone https://github.com/feraco/roboai-espeak.git
cd roboai-espeak

# Or if you already have it, just navigate to it
cd ~/roboai-espeak
```

---

## Step 4: Install System Audio Packages

These packages are required for microphone input and speaker output.

```bash
# Update package list
sudo apt-get update

# Install ALSA (core audio system)
sudo apt-get install -y \
    alsa-base \
    alsa-utils \
    libasound2 \
    libasound2-dev \
    libasound2-plugins

# Install PortAudio (required by Python sounddevice)
sudo apt-get install -y \
    portaudio19-dev \
    libportaudio2 \
    libportaudiocpp0

# Install libsndfile (audio file I/O)
sudo apt-get install -y \
    libsndfile1 \
    libsndfile1-dev

# Install PulseAudio (audio server)
sudo apt-get install -y \
    pulseaudio \
    pulseaudio-utils

# Install FFmpeg (audio processing)
sudo apt-get install -y \
    ffmpeg \
    libavcodec-dev \
    libavformat-dev \
    libavutil-dev

# Add your user to audio group (IMPORTANT!)
sudo usermod -a -G audio $USER

# Verify audio devices
arecord -l    # Should list input devices (microphones)
aplay -l      # Should list output devices (speakers)
```

---

## Step 5: Install Piper TTS (Text-to-Speech)

Piper provides local, offline text-to-speech.

```bash
# Download Piper for ARM64 (Jetson Orin)
cd /tmp
wget https://github.com/rhasspy/piper/releases/download/v1.2.0/piper_arm64.tar.gz

# Extract and install
tar -xzf piper_arm64.tar.gz
sudo mv piper/piper /usr/local/bin/
sudo chmod +x /usr/local/bin/piper

# Verify installation
piper --help

# Download voice model
mkdir -p ~/piper_voices
cd ~/piper_voices
wget https://github.com/rhasspy/piper/releases/download/v0.0.2/voice-en-us-ryan-medium.tar.gz
tar -xzf voice-en-us-ryan-medium.tar.gz

# Test Piper
echo "Hello from Astra Vein Treatment Center" | \
    piper --model ~/piper_voices/en_US-ryan-medium.onnx \
    --output_file test.wav

# Play the test audio
aplay test.wav
```

**You should hear the synthesized speech!**

---

## Step 6: Setup Python Environment with UV

```bash
# Navigate to project directory
cd ~/roboai-espeak

# Create virtual environment and install dependencies
uv sync

# This will:
# - Create a .venv directory
# - Install all packages from pyproject.toml
# - Download Python if needed
```

**Note:** `uv sync` reads from `pyproject.toml` and installs everything automatically!

---

## Step 7: Install Additional Audio Python Packages

UV sync installs most packages, but ensure audio-specific ones are present:

```bash
# Install audio packages explicitly
uv pip install \
    sounddevice \
    soundfile \
    numpy \
    scipy \
    faster-whisper \
    opencv-python-headless

# Verify installation
uv run python -c "import sounddevice; print('✓ sounddevice OK')"
uv run python -c "import soundfile; print('✓ soundfile OK')"
uv run python -c "import faster_whisper; print('✓ faster-whisper OK')"
uv run python -c "import cv2; print('✓ opencv OK')"
```

---

## Step 8: REBOOT (Important!)

**You MUST reboot for audio group permissions to take effect!**

```bash
sudo reboot
```

---

## Step 9: Test Audio Setup (After Reboot)

```bash
cd ~/roboai-espeak

# Test 1: Check dependencies
uv run python check_jetson_dependencies.py

# Expected output: All checks should pass ✓

# Test 2: Test sample rates
uv run python test_jetson_audio.py

# Expected output: Should show supported sample rates (likely 48000 Hz)

# Test 3: Record and playback
arecord -d 3 -f cd test.wav && aplay test.wav

# Speak into the microphone for 3 seconds, then hear playback
```

---

## Step 10: Find Your Microphone Device Number ⚠️ IMPORTANT

On Jetson, auto-detection (`input_device: null`) often **fails**. You must manually specify the device number.

### Find Available Audio Devices

```bash
cd ~/roboai-espeak

# Method 1: Use test script (RECOMMENDED)
uv run python test_microphone.py

# Method 2: Use Python directly
uv run python -c "import sounddevice as sd; print(sd.query_devices())"

# Method 3: Use ALSA tools
arecord -l
```

**Example output from test_microphone.py:**
```
Available Audio Devices:
  0: HDA Intel PCH: ALC897 Analog (hw:0,0) - ALSA (2 in, 8 out)
  1: USB Camera: Audio (hw:1,0) - ALSA (1 in, 0 out)  ← Your camera mic!
  2: bcm2835 Headphones (hw:2,0) - ALSA (0 in, 8 out)
```

In this example, **device 1** is the camera microphone.

### Update Your Config with Device Number

```bash
nano config/astra_vein_receptionist.json5
```

Find the `LocalASRInput` section and set `input_device`:

```json5
{
  agent_inputs: [
    {
      type: "LocalASRInput",
      config: {
        engine: "faster-whisper",
        model_size: "tiny.en",
        input_device: 1,  // ⚠️ CHANGE THIS TO YOUR DEVICE NUMBER
        sample_rate: 16000,
        // ... rest of config
      }
    }
  ]
}
```

**Common device numbers on G1:**
- **Device 0**: Usually the built-in audio or HDMI
- **Device 1**: Often the USB camera microphone
- **Device 2+**: Additional USB devices

---

## Step 11: Configure Agent Settings (Optional)

The configuration is already optimized, but you can adjust if needed:

```bash
# Edit the configuration file
nano config/astra_vein_receptionist.json5

# Key settings you might adjust:
# - input_device: 1 (REQUIRED - use device number from above)
# - sample_rate: 48000 (use what test_jetson_audio.py recommends)
# - amplify_audio: 3.0 (increase if microphone is too quiet)
# - chunk_duration: 2.0 (longer = more stable, but slower response)
# - silence_threshold: 0.03 (lower = more sensitive to quiet sounds)
```

**Recommended Jetson config values:**
```json5
{
  agent_inputs: [
    {
      type: "LocalASRInput",
      config: {
        engine: "faster-whisper",
        model_size: "tiny.en",      // Fastest for Jetson
        input_device: 1,            // ⚠️ SET YOUR DEVICE NUMBER
        sample_rate: 16000,         // 16000 is most compatible
        chunk_duration: 2.0,        // 2 seconds
        silence_threshold: 0.03,
        amplify_audio: 3.0,         // Boost quiet mics
        beam_size: 1,               // Fastest decoding
        vad_filter: true,
      }
    },
    {
      type: "VLMOllamaVision",
      config: {
        camera_index: 0,
        poll_interval: 5.0,         // Check camera every 5 seconds
        analysis_interval: 15.0,    // Analyze every 15 seconds
        timeout: 20,
      }
    }
  ],
  
  cortex_llm: {
    type: "OllamaLLM",
    config: {
      model: "llama3.1:8b",
      timeout: 30,                  // Longer timeout for Jetson
      temperature: 0.7,
    }
  }
}
```

---

## Step 12: Run the Agent! 🚀

```bash
cd ~/roboai-espeak

# Run the Astra Vein receptionist agent
uv run src/run.py astra_vein_receptionist
```

**Expected startup logs:**
```
INFO - LocalASRInput: auto-selected input device 0 (USB Microphone)
INFO - LocalASRInput: Using sample rate 48000 Hz
INFO - Loaded Faster-Whisper model: tiny.en
INFO - VLMOllamaVision attached to camera index 0
INFO - LLM initialized with 1 function schemas
INFO - Ollama LLM: System context set
INFO - Starting OM1 with standard configuration: astra_vein_receptionist
```

---

## Step 12: Test the Agent

### Test 1: Voice Input
1. Wait for agent to start (about 5-10 seconds)
2. Speak into microphone: **"What are your office hours?"**
3. Agent should respond with office hours

### Test 2: Vision Curiosity
1. Make sure you're visible to the camera
2. Stay quiet (don't speak)
3. Wait 10-15 seconds
4. Agent should describe what it sees and welcome you

### Test 3: Question and Answer
Try asking:
- "Where are you located?"
- "What services do you offer?"
- "How do I book an appointment?"
- "Who is Dr. Bolotin?"

---

## Troubleshooting

### Issue: "paInvalidSampleRate" Error

**Solution:** This is now auto-fixed! The code detects supported rates automatically.

If it persists:
```bash
# Find supported rates
uv run python test_jetson_audio.py

# Update config with recommended rate (usually 48000)
nano config/astra_vein_receptionist.json5
# Change: "sample_rate": 48000,
```

### Issue: Microphone Too Quiet

```bash
# Increase volume with alsamixer
alsamixer
# Press F4 for Capture mode
# Use arrow keys to increase volume to 80-100%
# Press Esc to save

# Or increase in config
# "amplify_audio": 5.0,  // Higher number = louder
```

### Issue: No Audio Devices Found

```bash
# Check if audio group was applied
groups $USER
# Should include 'audio'

# If not, add and reboot
sudo usermod -a -G audio $USER
sudo reboot
```

### Issue: Ollama Not Running

```bash
# Check Ollama status
sudo systemctl status ollama

# Restart if needed
sudo systemctl restart ollama

# Test connection
curl http://localhost:11434

# Check if models are downloaded
ollama list
```

### Issue: Camera Not Working

```bash
# Check camera devices
ls -l /dev/video*

# Test camera
uv run python -c "import cv2; cap = cv2.VideoCapture(0); print('OK' if cap.isOpened() else 'FAIL'); cap.release()"

# Give permissions
sudo chmod 666 /dev/video0
```

### Issue: Agent Responds Too Slowly

Reduce model complexity in config:
```json5
{
  cortex_llm: {
    config: {
      model: "llama3.1:8b",  // Already the smallest reasonable model
      timeout: 30,
    }
  }
}
```

Or use faster Whisper model:
```json5
{
  agent_inputs: [{
    config: {
      model_size: "tiny.en",  // Already the fastest!
    }
  }]
}
```

---

## Quick Reference Commands

```bash
# Start Ollama
sudo systemctl start ollama

# Check dependencies
uv run python check_jetson_dependencies.py

# Test audio devices
uv run python test_jetson_audio.py

# Test microphone recording
arecord -d 3 test.wav && aplay test.wav

# Test TTS
echo "Test" | piper --model ~/piper_voices/en_US-ryan-medium.onnx --output_file test.wav && aplay test.wav

# Run agent
uv run src/run.py astra_vein_receptionist

# Monitor system resources
tegrastats

# Check Ollama models
ollama list

# Stop agent
Ctrl+C
```

---

## Step 11: Setup G1 Arm Control (Optional - For Unitree G1 Humanoid Robot)

If you want to enable arm gestures on the Unitree G1, follow these steps:

### 11.1: Install Unitree SDK

The G1 arm control requires the official Unitree SDK Python bindings.

```bash
# Navigate to your home directory
cd ~

# Clone the Unitree SDK repository
git clone https://github.com/unitreerobotics/unitree_sdk2_python.git

# Install the SDK
cd unitree_sdk2_python
sudo python3 setup.py install

# Verify installation
python3 -c "from unitree.unitree_sdk2py.g1.arm.g1_arm_action_client import G1ArmActionClient; print('✅ Unitree SDK installed successfully')"
```

**Expected output:**
```
✅ Unitree SDK installed successfully
```

### 11.2: Install CycloneDDS (Required for ROS2 Communication)

The Unitree SDK uses DDS (Data Distribution Service) for robot communication.

```bash
# Install CycloneDDS dependencies
sudo apt-get install -y \
    libcyclonedds-dev \
    cyclonedds-tools

# Verify CycloneDDS
ddsls  # Should list DDS topics if robot is connected
```

### 11.3: Configure Ethernet Interface

The G1 communicates over Ethernet. You need to find your Ethernet interface name:

```bash
# Find your Ethernet interface
ip addr show | grep -E "^[0-9]+: (en|eth)"

# Common outputs:
# - eno1 (most common on G1 Jetson)
# - eth0 (alternative)
# - enp* (PCIe ethernet)
```

Note the interface name (e.g., `eno1`) - you'll need this for the config.

### 11.4: Update Agent Configuration

Add the arm action to your `config/astra_vein_receptionist.json5`:

```json5
{
  name: "astra_vein_receptionist",
  unitree_ethernet: "eno1",  // ⚠️ CHANGE TO YOUR ETHERNET INTERFACE
  
  // ... existing config ...
  
  agent_actions: [
    {
      name: "speak",
      llm_label: "speak",
      connector: "piper_tts",
      config: {
        // ... your TTS config ...
      }
    },
    {
      name: "arm_g1",
      llm_label: "arm movement",
      type: "Action",
      connector: "unitree_sdk",
      config: {}
    }
  ]
}
```

### 11.5: Update System Prompts

Add arm gesture examples to your system prompts:

```json5
{
  system_prompt_examples: "Here are some example interactions:

1. If a patient says 'Hello!', you might:
   Speak: {'sentence': 'Welcome to Astra Vein Treatment Center! How can I help you today?', 'language': 'en'}
   Arm movement: 'high wave'

2. If a patient says 'Thank you!', you might:
   Speak: {'sentence': 'You are very welcome! We are here to help.', 'language': 'en'}
   Arm movement: 'heart'

3. If a patient asks about scheduling:
   Speak: {'sentence': 'I can help you schedule an appointment. Call us at 347-934-9068.', 'language': 'en'}
   Arm movement: 'idle'

Available arm gestures: high wave, heart, high five, shake hand, clap, idle"
}
```

### 11.6: Test G1 Arm Connection

Before running the full agent, test the arm connection:

```bash
# Test importing the SDK
python3 -c "from actions.arm_g1.connector.unitree_sdk import ARMUnitreeSDKConnector; print('✅ Arm connector OK')"

# If successful, run the agent
uv run src/run.py astra_vein_receptionist
```

### Available Arm Gestures

| Gesture | When to Use | Example Context |
|---------|-------------|-----------------|
| **high wave** | Greeting patients, saying goodbye | "Welcome!" |
| **heart** | Showing care, gratitude | "Thank you for visiting!" |
| **high five** | Celebrating good news | "Great choice!" |
| **shake hand** | Professional greeting | Formal introductions |
| **clap** | Celebrating progress | "Wonderful decision!" |
| **idle** | Neutral resting position | Standard responses |

### Troubleshooting G1 Arms

**Issue: "Failed to initialize G1 Arm Action Client"**
- Check ethernet cable is connected
- Verify interface name: `ip addr show`
- Ensure `unitree_ethernet` matches your interface in config
- Test DDS communication: `ddsls`

**Issue: "ModuleNotFoundError: No module named 'unitree'"**
- Reinstall SDK: `cd ~/unitree_sdk2_python && sudo python3 setup.py install`
- Verify: `python3 -c "import unitree; print('OK')"`

**Issue: Arms don't move**
- Check robot is powered on and in ready state
- Verify network connection: `ping <robot-ip>`
- Check logs for "G1 Arm Action Client initialized successfully"

---

## Summary Checklist

- [ ] UV package manager installed
- [ ] Ollama installed and running
- [ ] Models downloaded (llama3.1:8b, llava-llama3)
- [ ] System audio packages installed
- [ ] Piper TTS installed with voice model
- [ ] Python packages installed via `uv sync`
- [ ] User added to audio group
- [ ] System rebooted
- [ ] Audio tests pass (check_jetson_dependencies.py)
- [ ] Sample rate detected (test_jetson_audio.py)
- [ ] **Microphone device number configured in config** (input_device: X)
- [ ] Agent runs successfully
- [ ] **(Optional) Unitree SDK installed for G1 arms**
- [ ] **(Optional) CycloneDDS installed**
- [ ] **(Optional) Ethernet interface configured**
- [ ] **(Optional) Arm gestures working**

---

## Next Steps

Once your agent is running:

1. **Customize prompts**: Edit `config/astra_vein_receptionist.json5` to change personality, add information, etc.

2. **Adjust performance**: Tune `chunk_duration`, `poll_interval`, and `timeout` values for your hardware

3. **Add more actions**: Explore other action plugins in `src/actions/`

4. **Create new configs**: Copy and modify the config to create different agent behaviors

5. **Autostart on boot**: Set up systemd service to run agent automatically

Enjoy your AI-powered receptionist! 🤖🎤
