#!/bin/bash
# Quick start script for Docker deployment on Jetson Orin g1
# This script builds and starts the RoboAI container

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "=========================================="
echo "RoboAI Docker Quick Start"
echo "Jetson Orin g1 Platform"
echo "=========================================="
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed!"
    echo ""
    echo "Please install Docker first:"
    echo "  curl -fsSL https://get.docker.com -o get-docker.sh"
    echo "  sudo sh get-docker.sh"
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker compose &> /dev/null && ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed!"
    echo ""
    echo "Please install Docker Compose:"
    echo "  sudo apt-get install -y docker-compose-plugin"
    exit 1
fi

# Check if NVIDIA runtime is available
echo "Checking NVIDIA Container Runtime..."
if docker run --rm --runtime=nvidia nvcr.io/nvidia/l4t-base:r35.2.1 nvidia-smi > /dev/null 2>&1; then
    echo "✅ NVIDIA runtime is available"
else
    echo "⚠️  NVIDIA runtime not detected. GPU acceleration may not work."
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Navigate to project root
cd "$PROJECT_ROOT"

# Check if image exists
if docker images | grep -q "roboai-espeak.*jetson-orin-g1"; then
    echo ""
    echo "Docker image already exists."
    read -p "Do you want to rebuild it? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo ""
        echo "Building Docker image (this may take 15-30 minutes)..."
        docker compose -f docker-compose.jetson.yml build
    fi
else
    echo ""
    echo "Building Docker image (this may take 15-30 minutes)..."
    docker compose -f docker-compose.jetson.yml build
fi

# Stop any existing container
if docker ps -a | grep -q "roboai-jetson-agent"; then
    echo ""
    echo "Stopping existing container..."
    docker compose -f docker-compose.jetson.yml down
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo ""
    echo "Creating .env file from template..."
    if [ -f env.example ]; then
        cp env.example .env
        echo "✅ Created .env file. You can edit it to add API keys if needed."
    fi
fi

# Start the container
echo ""
echo "Starting RoboAI container..."
docker compose -f docker-compose.jetson.yml up -d

# Wait for container to be ready
echo ""
echo "Waiting for container to start..."
sleep 5

# Check if container is running
if docker ps | grep -q "roboai-jetson-agent"; then
    echo ""
    echo "=========================================="
    echo "✅ RoboAI container started successfully!"
    echo "=========================================="
    echo ""
    echo "Container name: roboai-jetson-agent"
    echo "Agent config: ${AGENT_CONFIG:-astra_vein_receptionist}"
    echo ""
    echo "Useful commands:"
    echo "  View logs:     docker logs -f roboai-jetson-agent"
    echo "  Stop:          docker compose -f docker-compose.jetson.yml down"
    echo "  Restart:       docker compose -f docker-compose.jetson.yml restart"
    echo "  Run tests:     ./deployment/test_docker_deployment.sh"
    echo ""
    echo "To view logs now, run:"
    echo "  docker logs -f roboai-jetson-agent"
    echo ""
    
    # Ask if user wants to see logs
    read -p "View logs now? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker logs -f roboai-jetson-agent
    fi
else
    echo ""
    echo "❌ Container failed to start!"
    echo ""
    echo "Check logs with:"
    echo "  docker logs roboai-jetson-agent"
    exit 1
fi
