# Docker Deployment Guide for Jetson Orin g1

This guide provides complete instructions for deploying RoboAI-espeak on NVIDIA Jetson Orin g1 using Docker containers with automatic startup.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Initial Setup](#initial-setup)
3. [Building the Docker Image](#building-the-docker-image)
4. [Running the Container](#running-the-container)
5. [Configuring Auto-Start](#configuring-auto-start)
6. [Validation and Testing](#validation-and-testing)
7. [Troubleshooting](#troubleshooting)
8. [Configuration](#configuration)
9. [Maintenance](#maintenance)

---

## Prerequisites

### Hardware Requirements
- **NVIDIA Jetson Orin g1** (or compatible Jetson device)
- **Minimum 32GB storage** (64GB+ recommended for models and data)
- **8GB RAM minimum** (16GB recommended)
- **USB Microphone** (for speech input)
- **USB Speaker or Audio Output** (for text-to-speech)
- **USB Camera** (optional, for vision features)

### Software Requirements
- **JetPack 5.x** (Ubuntu 20.04 based)
- **Docker** (20.10+)
- **NVIDIA Container Runtime** (for GPU acceleration)
- **Docker Compose** (2.x+)

---

## Initial Setup

### Step 1: Install Docker

If Docker is not already installed:

```bash
# Update system packages
sudo apt-get update
sudo apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add your user to docker group
sudo usermod -aG docker $USER

# Enable Docker service
sudo systemctl enable docker
sudo systemctl start docker

# Verify installation
docker --version
```

**Log out and back in** for group changes to take effect.

### Step 2: Install NVIDIA Container Runtime

The NVIDIA Container Runtime enables GPU access inside Docker containers:

```bash
# Install NVIDIA Container Runtime
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
    sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update
sudo apt-get install -y nvidia-container-runtime

# Configure Docker to use NVIDIA runtime as default
sudo tee /etc/docker/daemon.json > /dev/null <<EOF
{
    "runtimes": {
        "nvidia": {
            "path": "nvidia-container-runtime",
            "runtimeArgs": []
        }
    },
    "default-runtime": "nvidia"
}
EOF

# Restart Docker
sudo systemctl restart docker

# Verify NVIDIA runtime
docker run --rm --runtime=nvidia nvcr.io/nvidia/l4t-base:r35.2.1 nvidia-smi
```

### Step 3: Install Docker Compose

```bash
# Install Docker Compose
sudo apt-get install -y docker-compose-plugin

# Verify installation
docker compose version
```

### Step 4: Clone Repository

```bash
# Clone the repository
cd ~
git clone https://github.com/feraco/roboai-espeak.git
cd roboai-espeak

# Create .env file for environment variables (optional)
cp env.example .env
# Edit .env if you need to add API keys
```

---

## Building the Docker Image

### Option 1: Build Locally (Recommended)

```bash
cd ~/roboai-espeak

# Build the Jetson-optimized Docker image
# This will take 15-30 minutes on first build
docker build -f Dockerfile.jetson -t roboai-espeak:jetson-orin-g1 .

# Verify the image was created
docker images | grep roboai-espeak
```

### Option 2: Build with Docker Compose

```bash
cd ~/roboai-espeak

# Build using docker-compose
docker compose -f docker-compose.jetson.yml build

# This will automatically tag the image
```

---

## Running the Container

### Option 1: Using Docker Compose (Recommended)

```bash
cd ~/roboai-espeak

# Start the container in detached mode
docker compose -f docker-compose.jetson.yml up -d

# View logs
docker compose -f docker-compose.jetson.yml logs -f

# Stop the container
docker compose -f docker-compose.jetson.yml down
```

### Option 2: Using Docker Run Directly

```bash
# Run with default agent (astra_vein_receptionist)
docker run -d \
  --name roboai-jetson-agent \
  --restart unless-stopped \
  --runtime=nvidia \
  --network host \
  -e AGENT_CONFIG=astra_vein_receptionist \
  -e NVIDIA_VISIBLE_DEVICES=all \
  -v $(pwd)/config:/app/roboai-espeak/config:rw \
  -v $(pwd)/piper_voices:/app/piper_voices:ro \
  -v $HOME/.ollama:/root/.ollama:rw \
  --device /dev/snd:/dev/snd \
  --device /dev/video0:/dev/video0 \
  roboai-espeak:jetson-orin-g1

# View logs
docker logs -f roboai-jetson-agent

# Stop container
docker stop roboai-jetson-agent
docker rm roboai-jetson-agent
```

### Running Different Agent Configurations

To run a different agent configuration:

```bash
# Using docker-compose
AGENT_CONFIG=local_agent docker compose -f docker-compose.jetson.yml up -d

# Or using docker run
docker run -d \
  --name roboai-jetson-agent \
  -e AGENT_CONFIG=local_agent \
  # ... (other options same as above)
  roboai-espeak:jetson-orin-g1
```

Available agents: `astra_vein_receptionist`, `local_agent`, `conversation`, etc.

---

## Configuring Auto-Start

To automatically start the RoboAI agent when the Jetson boots:

### Step 1: Install Systemd Service

```bash
cd ~/roboai-espeak

# Copy the systemd service file
sudo cp systemd_services/roboai-docker.service /etc/systemd/system/

# Edit the service file to match your username and paths
sudo nano /etc/systemd/system/roboai-docker.service
```

**Update these lines in the service file:**
- Change `/home/%u/roboai-espeak` to your actual path (e.g., `/home/jetson/roboai-espeak`)
- Verify `AGENT_CONFIG` environment variable is set to your desired agent

### Step 2: Enable and Start Service

```bash
# Reload systemd to recognize the new service
sudo systemctl daemon-reload

# Enable auto-start on boot
sudo systemctl enable roboai-docker.service

# Start the service immediately
sudo systemctl start roboai-docker.service

# Check service status
sudo systemctl status roboai-docker.service
```

### Step 3: Verify Auto-Start

```bash
# Check container is running
docker ps

# View logs
docker logs -f roboai-jetson-agent

# Or view systemd logs
sudo journalctl -u roboai-docker.service -f
```

### Service Control Commands

```bash
# Start service
sudo systemctl start roboai-docker.service

# Stop service
sudo systemctl stop roboai-docker.service

# Restart service
sudo systemctl restart roboai-docker.service

# Check status
sudo systemctl status roboai-docker.service

# View logs
sudo journalctl -u roboai-docker.service -f

# Disable auto-start
sudo systemctl disable roboai-docker.service
```

---

## Validation and Testing

### Basic Smoke Tests

#### 1. Container Health Check

```bash
# Check if container is running
docker ps | grep roboai-jetson-agent

# Check container health status
docker inspect roboai-jetson-agent | grep -A 5 Health

# View container logs
docker logs --tail 50 roboai-jetson-agent
```

Expected output in logs:
```
Starting Ollama service...
Waiting for Ollama to start...
Ollama is ready
Checking Ollama models...
Starting RoboAI agent: astra_vein_receptionist
INFO - LocalASRInput: auto-selected input device
INFO - Loaded Faster-Whisper model
INFO - Starting OM1 with standard configuration
```

#### 2. Audio Device Test

```bash
# Enter the container
docker exec -it roboai-jetson-agent bash

# Inside container: List audio devices
arecord -l
aplay -l

# Test microphone recording
arecord -D hw:0,0 -d 3 -f cd test.wav
aplay test.wav

# Exit container
exit
```

#### 3. Camera Test

```bash
# Enter the container
docker exec -it roboai-jetson-agent bash

# Inside container: List cameras
v4l2-ctl --list-devices

# Test camera capture
ffmpeg -f v4l2 -i /dev/video0 -frames 1 test.jpg

# Exit container
exit
```

#### 4. Ollama Test

```bash
# Test Ollama from inside container
docker exec roboai-jetson-agent curl -s http://localhost:11434/api/tags

# Test model interaction
docker exec roboai-jetson-agent ollama run llama3.1:8b "Hello, reply with OK"
```

#### 5. End-to-End Test

1. **Speak into microphone**: "Hello"
2. **Check logs**: `docker logs -f roboai-jetson-agent`
3. **Expected output**:
   - Voice transcription logged
   - LLM response generated
   - TTS audio played

### Automated Test Script

Create a test script `test_docker_deployment.sh`:

```bash
#!/bin/bash
# Automated test script for Docker deployment

echo "=========================================="
echo "RoboAI Docker Deployment Tests"
echo "=========================================="
echo ""

# Test 1: Docker is running
echo "Test 1: Docker service..."
if systemctl is-active --quiet docker; then
    echo "✅ Docker is running"
else
    echo "❌ Docker is NOT running"
    exit 1
fi

# Test 2: NVIDIA runtime available
echo "Test 2: NVIDIA runtime..."
if docker run --rm --runtime=nvidia nvcr.io/nvidia/l4t-base:r35.2.1 nvidia-smi > /dev/null 2>&1; then
    echo "✅ NVIDIA runtime is working"
else
    echo "❌ NVIDIA runtime is NOT working"
    exit 1
fi

# Test 3: Container is running
echo "Test 3: RoboAI container..."
if docker ps | grep -q roboai-jetson-agent; then
    echo "✅ Container is running"
else
    echo "❌ Container is NOT running"
    exit 1
fi

# Test 4: Container is healthy
echo "Test 4: Container health..."
HEALTH=$(docker inspect roboai-jetson-agent | grep -o '"Status": "[^"]*"' | head -1 | cut -d'"' -f4)
if [ "$HEALTH" = "running" ]; then
    echo "✅ Container is healthy"
else
    echo "❌ Container health: $HEALTH"
fi

# Test 5: Ollama is accessible
echo "Test 5: Ollama service..."
if docker exec roboai-jetson-agent curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "✅ Ollama is accessible"
else
    echo "❌ Ollama is NOT accessible"
fi

# Test 6: Audio devices
echo "Test 6: Audio devices..."
if docker exec roboai-jetson-agent arecord -l > /dev/null 2>&1; then
    echo "✅ Audio devices are accessible"
else
    echo "❌ Audio devices are NOT accessible"
fi

# Test 7: Video devices
echo "Test 7: Video devices..."
if docker exec roboai-jetson-agent v4l2-ctl --list-devices > /dev/null 2>&1; then
    echo "✅ Video devices are accessible"
else
    echo "⚠️  Video devices may not be accessible (optional)"
fi

echo ""
echo "=========================================="
echo "Tests completed!"
echo "=========================================="
```

Make it executable and run:

```bash
chmod +x test_docker_deployment.sh
./test_docker_deployment.sh
```

---

## Troubleshooting

### Container Won't Start

**Problem**: Container exits immediately after starting

**Solutions**:

```bash
# Check logs for error messages
docker logs roboai-jetson-agent

# Common issues:

# 1. Ollama fails to start
# Check if port 11434 is already in use
sudo netstat -tulpn | grep 11434
# If in use, stop the conflicting process

# 2. Audio devices not accessible
# Check device permissions
ls -la /dev/snd/
# Ensure your user is in audio group
groups $USER | grep audio

# 3. GPU not accessible
# Verify NVIDIA runtime
docker run --rm --runtime=nvidia nvcr.io/nvidia/l4t-base:r35.2.1 nvidia-smi
```

### Audio Not Working

**Problem**: No audio input/output in container

**Solutions**:

```bash
# 1. Check host audio devices
arecord -l
aplay -l

# 2. Verify PulseAudio is running
pulseaudio --check
# If not running
pulseaudio --start

# 3. Check container has access to audio devices
docker exec roboai-jetson-agent arecord -l

# 4. Test audio recording in container
docker exec -it roboai-jetson-agent bash
arecord -D hw:0,0 -d 3 test.wav
aplay test.wav
exit
```

### Camera Not Working

**Problem**: Camera not detected in container

**Solutions**:

```bash
# 1. Check host camera devices
ls -la /dev/video*
v4l2-ctl --list-devices

# 2. Verify video group membership
groups $USER | grep video
# If not in group
sudo usermod -aG video $USER
# Log out and back in

# 3. Test camera in container
docker exec -it roboai-jetson-agent bash
ffmpeg -f v4l2 -list_formats all -i /dev/video0
exit

# 4. Grant container access to more video devices
# Edit docker-compose.jetson.yml and add more devices:
#   - /dev/video2:/dev/video2
#   - /dev/video3:/dev/video3
```

### Ollama Issues

**Problem**: Ollama not responding or models not loading

**Solutions**:

```bash
# 1. Check Ollama logs
docker exec roboai-jetson-agent cat /var/log/ollama.log

# 2. Manually pull models
docker exec roboai-jetson-agent ollama pull llama3.1:8b

# 3. Check Ollama is responding
docker exec roboai-jetson-agent curl http://localhost:11434/api/tags

# 4. Restart container to restart Ollama
docker restart roboai-jetson-agent
```

### Performance Issues

**Problem**: Container runs slowly or uses excessive resources

**Solutions**:

```bash
# 1. Check resource usage
docker stats roboai-jetson-agent

# 2. Monitor Jetson resources
sudo tegrastats

# 3. Adjust memory limits in docker-compose.jetson.yml
# Edit limits.memory and reservations.memory

# 4. Use a smaller LLM model
# Change AGENT_CONFIG or edit config/*.json5 to use llama3.2:3b instead

# 5. Increase Jetson performance mode
sudo nvpmodel -m 0
sudo jetson_clocks
```

### Auto-Start Not Working

**Problem**: Container doesn't start on boot

**Solutions**:

```bash
# 1. Check systemd service status
sudo systemctl status roboai-docker.service

# 2. Check service is enabled
sudo systemctl is-enabled roboai-docker.service

# 3. View service logs
sudo journalctl -u roboai-docker.service -b

# 4. Verify service file syntax
systemctl cat roboai-docker.service

# 5. Test service manually
sudo systemctl start roboai-docker.service
sudo systemctl status roboai-docker.service
```

---

## Configuration

### Environment Variables

The following environment variables can be configured in `docker-compose.jetson.yml` or `.env` file:

| Variable | Default | Description |
|----------|---------|-------------|
| `AGENT_CONFIG` | `astra_vein_receptionist` | Agent configuration to run |
| `PULSE_SERVER` | `unix:/run/user/1000/pulse/native` | PulseAudio server path |
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama API endpoint |
| `NVIDIA_VISIBLE_DEVICES` | `all` | GPU devices to expose |
| `OPENAI_API_KEY` | - | Optional OpenAI API key |
| `ELEVENLABS_API_KEY` | - | Optional ElevenLabs API key |

### Agent Configuration Files

Agent configurations are stored in `config/*.json5`. To modify an agent:

1. Edit the config file on the host:
   ```bash
   nano ~/roboai-espeak/config/astra_vein_receptionist.json5
   ```

2. Restart the container to apply changes:
   ```bash
   docker restart roboai-jetson-agent
   # Or with docker-compose:
   docker compose -f docker-compose.jetson.yml restart
   ```

### Volume Mounts

Important volume mounts in the container:

| Host Path | Container Path | Purpose |
|-----------|----------------|---------|
| `./config` | `/app/roboai-espeak/config` | Agent configurations |
| `./piper_voices` | `/app/piper_voices` | TTS voice models |
| `$HOME/.ollama` | `/root/.ollama` | Ollama models (persistent) |
| `./audio_output` | `/app/roboai-espeak/audio_output` | Generated audio files |

---

## Maintenance

### Updating the Application

To update RoboAI to the latest version:

```bash
cd ~/roboai-espeak

# Stop the container
docker compose -f docker-compose.jetson.yml down

# Pull latest code
git pull origin main

# Rebuild the image
docker compose -f docker-compose.jetson.yml build

# Start the updated container
docker compose -f docker-compose.jetson.yml up -d

# Verify it's running
docker logs -f roboai-jetson-agent
```

### Updating Ollama Models

```bash
# Enter the container
docker exec -it roboai-jetson-agent bash

# Update/pull new models
ollama pull llama3.1:8b
ollama pull llava-llama3

# List installed models
ollama list

# Remove old models to save space
ollama rm old-model-name

# Exit container
exit
```

### Cleaning Up Docker Resources

```bash
# Remove stopped containers
docker container prune

# Remove unused images
docker image prune -a

# Remove unused volumes
docker volume prune

# Complete cleanup (CAUTION: removes all unused resources)
docker system prune -a --volumes
```

### Backup and Restore

#### Backup

```bash
# Backup Ollama models
tar -czf ollama-models-backup.tar.gz ~/.ollama/

# Backup configuration
tar -czf config-backup.tar.gz ~/roboai-espeak/config/

# Backup Piper voices
tar -czf piper-voices-backup.tar.gz ~/roboai-espeak/piper_voices/
```

#### Restore

```bash
# Restore Ollama models
tar -xzf ollama-models-backup.tar.gz -C ~/

# Restore configuration
tar -xzf config-backup.tar.gz -C ~/

# Restore Piper voices
tar -xzf piper-voices-backup.tar.gz -C ~/
```

### Monitoring

Create a monitoring script `monitor_docker.sh`:

```bash
#!/bin/bash
# Monitor Docker deployment

echo "=== RoboAI Docker Status ==="
echo ""

# Container status
if docker ps | grep -q roboai-jetson-agent; then
    echo "✅ Container: RUNNING"
    
    # Uptime
    UPTIME=$(docker inspect -f '{{.State.StartedAt}}' roboai-jetson-agent)
    echo "   Started: $UPTIME"
    
    # Resource usage
    docker stats --no-stream roboai-jetson-agent
else
    echo "❌ Container: NOT RUNNING"
fi

echo ""
echo "=== Recent Logs (last 20 lines) ==="
docker logs --tail 20 roboai-jetson-agent

echo ""
echo "=== Systemd Service Status ==="
systemctl status roboai-docker.service --no-pager
```

---

## Additional Resources

- **Main Documentation**: [README.md](../README.md)
- **Configuration Guide**: [documentation/guides/CONFIG_GUIDE.md](../documentation/guides/CONFIG_GUIDE.md)
- **Troubleshooting**: [documentation/troubleshooting/](../documentation/troubleshooting/)
- **GitHub Repository**: https://github.com/feraco/roboai-espeak

---

## Support

If you encounter issues not covered in this guide:

1. Check container logs: `docker logs roboai-jetson-agent`
2. Check systemd logs: `sudo journalctl -u roboai-docker.service -f`
3. Run the test script: `./test_docker_deployment.sh`
4. Open an issue on GitHub with logs and system information

---

**Last Updated**: November 2025
