# Docker Deployment for Jetson Orin g1

Quick reference for deploying RoboAI-espeak using Docker on NVIDIA Jetson Orin g1 hardware.

## Quick Start

```bash
# Clone repository
git clone https://github.com/feraco/roboai-espeak.git
cd roboai-espeak

# Run quick start script
./deployment/docker_quickstart_jetson.sh

# View logs
docker logs -f roboai-jetson-agent
```

## Files Overview

| File | Purpose |
|------|---------|
| `Dockerfile.jetson` | Jetson Orin g1 optimized Dockerfile with GPU support |
| `docker-compose.jetson.yml` | Docker Compose configuration for Jetson |
| `DOCKER_JETSON_DEPLOYMENT.md` | Complete deployment guide with troubleshooting |
| `docker_quickstart_jetson.sh` | Automated setup script |
| `test_docker_deployment.sh` | Validation and smoke tests |
| `systemd_services/roboai-docker.service` | Auto-start systemd service |

## Prerequisites

- **Hardware**: NVIDIA Jetson Orin g1 (or compatible)
- **OS**: JetPack 5.x (Ubuntu 20.04 based)
- **Docker**: 20.10+
- **NVIDIA Container Runtime**: For GPU acceleration
- **Storage**: 32GB minimum (64GB+ recommended)

## Installation

### 1. Install Docker

```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
```

### 2. Install NVIDIA Container Runtime

```bash
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
    sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update
sudo apt-get install -y nvidia-container-runtime

# Configure Docker
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

sudo systemctl restart docker
```

### 3. Build and Run

```bash
cd ~/roboai-espeak

# Build image
docker compose -f docker-compose.jetson.yml build

# Start container
docker compose -f docker-compose.jetson.yml up -d

# View logs
docker logs -f roboai-jetson-agent
```

## Configuration

### Change Agent Configuration

```bash
# Set environment variable
AGENT_CONFIG=local_agent docker compose -f docker-compose.jetson.yml up -d

# Or edit .env file
echo "AGENT_CONFIG=local_agent" >> .env
docker compose -f docker-compose.jetson.yml up -d
```

### Modify Agent Settings

Agent configurations are in `config/*.json5`. Edit on host and restart:

```bash
nano config/astra_vein_receptionist.json5
docker compose -f docker-compose.jetson.yml restart
```

## Auto-Start on Boot

```bash
# Copy systemd service
sudo cp systemd_services/roboai-docker.service /etc/systemd/system/

# Edit paths (replace %u with your username)
sudo nano /etc/systemd/system/roboai-docker.service

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable roboai-docker.service
sudo systemctl start roboai-docker.service
```

## Testing

```bash
# Run comprehensive tests
./deployment/test_docker_deployment.sh

# Check container status
docker ps | grep roboai

# View logs
docker logs --tail 50 roboai-jetson-agent

# Enter container for debugging
docker exec -it roboai-jetson-agent bash
```

## Common Commands

```bash
# Start
docker compose -f docker-compose.jetson.yml up -d

# Stop
docker compose -f docker-compose.jetson.yml down

# Restart
docker compose -f docker-compose.jetson.yml restart

# View logs
docker logs -f roboai-jetson-agent

# Check resource usage
docker stats roboai-jetson-agent

# Update and rebuild
git pull origin main
docker compose -f docker-compose.jetson.yml build
docker compose -f docker-compose.jetson.yml up -d
```

## Troubleshooting

### Container won't start

```bash
# Check logs
docker logs roboai-jetson-agent

# Verify NVIDIA runtime
docker run --rm --runtime=nvidia nvcr.io/nvidia/l4t-base:r35.2.1 nvidia-smi
```

### Audio issues

```bash
# Check audio devices on host
arecord -l
aplay -l

# Check inside container
docker exec roboai-jetson-agent arecord -l
```

### GPU not accessible

```bash
# Verify NVIDIA runtime configuration
cat /etc/docker/daemon.json

# Test GPU in container
docker exec roboai-jetson-agent nvidia-smi
```

## Performance Optimization

```bash
# Set Jetson to maximum performance mode
sudo nvpmodel -m 0
sudo jetson_clocks

# Monitor resources
sudo tegrastats
docker stats roboai-jetson-agent
```

## Documentation

- **Complete Guide**: [DOCKER_JETSON_DEPLOYMENT.md](DOCKER_JETSON_DEPLOYMENT.md)
- **Main README**: [../README.md](../README.md)
- **Configuration Guide**: [../documentation/guides/CONFIG_GUIDE.md](../documentation/guides/CONFIG_GUIDE.md)

## Features

✅ **GPU Acceleration**: CUDA support for faster-whisper and Ollama  
✅ **Audio Support**: Full ALSA and PulseAudio integration  
✅ **Camera Access**: USB and CSI camera support  
✅ **Auto-Start**: Systemd service for boot-time startup  
✅ **Health Checks**: Built-in container health monitoring  
✅ **Multi-Language**: Support for English, Spanish, Russian TTS  
✅ **Resource Limits**: Configurable memory and CPU limits  
✅ **Persistent Storage**: Ollama models and configs preserved  

## Support

For detailed troubleshooting, see [DOCKER_JETSON_DEPLOYMENT.md](DOCKER_JETSON_DEPLOYMENT.md) or open an issue on GitHub.

---

**Last Updated**: November 2025
