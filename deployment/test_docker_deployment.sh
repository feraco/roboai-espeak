#!/bin/bash
# Automated test script for Docker deployment on Jetson Orin g1
# This script validates the Docker container setup and functionality

set -e

CONTAINER_NAME="roboai-jetson-agent"
TEST_RESULTS=()
PASS_COUNT=0
FAIL_COUNT=0

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=========================================="
echo "RoboAI Docker Deployment Tests"
echo "Jetson Orin g1 Platform"
echo "=========================================="
echo ""

# Helper function to log test results
log_test() {
    local test_name="$1"
    local result="$2"
    local message="$3"
    
    if [ "$result" = "PASS" ]; then
        echo -e "${GREEN}✅ PASS${NC}: $test_name"
        TEST_RESULTS+=("PASS: $test_name")
        ((PASS_COUNT++))
    elif [ "$result" = "FAIL" ]; then
        echo -e "${RED}❌ FAIL${NC}: $test_name - $message"
        TEST_RESULTS+=("FAIL: $test_name - $message")
        ((FAIL_COUNT++))
    elif [ "$result" = "WARN" ]; then
        echo -e "${YELLOW}⚠️  WARN${NC}: $test_name - $message"
        TEST_RESULTS+=("WARN: $test_name - $message")
    fi
}

# Test 1: Docker service
echo "Test 1: Docker service status..."
if systemctl is-active --quiet docker; then
    log_test "Docker service" "PASS"
else
    log_test "Docker service" "FAIL" "Docker is not running"
    exit 1
fi

# Test 2: Docker Compose
echo "Test 2: Docker Compose availability..."
if command -v docker compose &> /dev/null || command -v docker-compose &> /dev/null; then
    log_test "Docker Compose" "PASS"
else
    log_test "Docker Compose" "FAIL" "Docker Compose not installed"
    exit 1
fi

# Test 3: NVIDIA runtime
echo "Test 3: NVIDIA Container Runtime..."
if docker run --rm --runtime=nvidia nvcr.io/nvidia/l4t-base:r35.2.1 nvidia-smi > /dev/null 2>&1; then
    log_test "NVIDIA runtime" "PASS"
else
    log_test "NVIDIA runtime" "FAIL" "NVIDIA runtime not available or not configured"
fi

# Test 4: Container existence
echo "Test 4: RoboAI container existence..."
if docker ps -a | grep -q $CONTAINER_NAME; then
    log_test "Container exists" "PASS"
else
    log_test "Container exists" "FAIL" "Container '$CONTAINER_NAME' not found"
    echo ""
    echo "To create the container, run:"
    echo "  cd ~/roboai-espeak"
    echo "  docker compose -f docker-compose.jetson.yml up -d"
    exit 1
fi

# Test 5: Container running status
echo "Test 5: Container running status..."
if docker ps | grep -q $CONTAINER_NAME; then
    log_test "Container running" "PASS"
else
    log_test "Container running" "FAIL" "Container is not running"
    echo ""
    echo "To start the container, run:"
    echo "  docker compose -f docker-compose.jetson.yml up -d"
    exit 1
fi

# Test 6: Container health
echo "Test 6: Container health status..."
HEALTH_STATUS=$(docker inspect --format='{{.State.Health.Status}}' $CONTAINER_NAME 2>/dev/null || echo "no-healthcheck")
if [ "$HEALTH_STATUS" = "healthy" ] || [ "$HEALTH_STATUS" = "no-healthcheck" ]; then
    if [ "$HEALTH_STATUS" = "no-healthcheck" ]; then
        # Check if container is just running
        STATUS=$(docker inspect --format='{{.State.Status}}' $CONTAINER_NAME)
        if [ "$STATUS" = "running" ]; then
            log_test "Container health" "PASS"
        else
            log_test "Container health" "FAIL" "Container status: $STATUS"
        fi
    else
        log_test "Container health" "PASS"
    fi
else
    log_test "Container health" "WARN" "Health status: $HEALTH_STATUS"
fi

# Test 7: Ollama service
echo "Test 7: Ollama service accessibility..."
if docker exec $CONTAINER_NAME curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    log_test "Ollama service" "PASS"
else
    log_test "Ollama service" "FAIL" "Ollama is not responding"
fi

# Test 8: Ollama models
echo "Test 8: Ollama models installed..."
MODEL_COUNT=$(docker exec $CONTAINER_NAME ollama list 2>/dev/null | grep -c "llama" || echo "0")
if [ "$MODEL_COUNT" -gt 0 ]; then
    log_test "Ollama models" "PASS" "$MODEL_COUNT model(s) found"
else
    log_test "Ollama models" "WARN" "No Ollama models found. Models may still be downloading."
fi

# Test 9: Audio input devices
echo "Test 9: Audio input devices..."
if docker exec $CONTAINER_NAME arecord -l > /dev/null 2>&1; then
    AUDIO_IN_COUNT=$(docker exec $CONTAINER_NAME arecord -l 2>/dev/null | grep -c "card" || echo "0")
    if [ "$AUDIO_IN_COUNT" -gt 0 ]; then
        log_test "Audio input devices" "PASS" "$AUDIO_IN_COUNT device(s) found"
    else
        log_test "Audio input devices" "WARN" "No audio input devices detected"
    fi
else
    log_test "Audio input devices" "FAIL" "Cannot access audio devices"
fi

# Test 10: Audio output devices
echo "Test 10: Audio output devices..."
if docker exec $CONTAINER_NAME aplay -l > /dev/null 2>&1; then
    AUDIO_OUT_COUNT=$(docker exec $CONTAINER_NAME aplay -l 2>/dev/null | grep -c "card" || echo "0")
    if [ "$AUDIO_OUT_COUNT" -gt 0 ]; then
        log_test "Audio output devices" "PASS" "$AUDIO_OUT_COUNT device(s) found"
    else
        log_test "Audio output devices" "WARN" "No audio output devices detected"
    fi
else
    log_test "Audio output devices" "FAIL" "Cannot access audio devices"
fi

# Test 11: Video devices
echo "Test 11: Video devices (cameras)..."
if docker exec $CONTAINER_NAME v4l2-ctl --list-devices > /dev/null 2>&1; then
    VIDEO_COUNT=$(docker exec $CONTAINER_NAME ls /dev/video* 2>/dev/null | wc -l)
    if [ "$VIDEO_COUNT" -gt 0 ]; then
        log_test "Video devices" "PASS" "$VIDEO_COUNT device(s) found"
    else
        log_test "Video devices" "WARN" "No video devices detected (optional)"
    fi
else
    log_test "Video devices" "WARN" "Cannot access video devices (optional)"
fi

# Test 12: Piper TTS
echo "Test 12: Piper TTS availability..."
if docker exec $CONTAINER_NAME which piper > /dev/null 2>&1; then
    log_test "Piper TTS" "PASS"
else
    log_test "Piper TTS" "FAIL" "Piper binary not found"
fi

# Test 13: Python environment
echo "Test 13: Python environment..."
if docker exec $CONTAINER_NAME python3 --version > /dev/null 2>&1; then
    PY_VERSION=$(docker exec $CONTAINER_NAME python3 --version)
    log_test "Python environment" "PASS" "$PY_VERSION"
else
    log_test "Python environment" "FAIL" "Python not accessible"
fi

# Test 14: UV package manager
echo "Test 14: UV package manager..."
if docker exec $CONTAINER_NAME which uv > /dev/null 2>&1; then
    UV_VERSION=$(docker exec $CONTAINER_NAME uv --version 2>&1 | head -1)
    log_test "UV package manager" "PASS" "$UV_VERSION"
else
    log_test "UV package manager" "FAIL" "UV not found"
fi

# Test 15: Configuration files
echo "Test 15: Configuration files..."
if docker exec $CONTAINER_NAME test -f /app/roboai-espeak/config/astra_vein_receptionist.json5; then
    log_test "Configuration files" "PASS"
else
    log_test "Configuration files" "WARN" "Default config not found"
fi

# Test 16: Systemd service (if applicable)
echo "Test 16: Systemd auto-start service..."
if systemctl list-unit-files | grep -q "roboai-docker.service"; then
    if systemctl is-enabled --quiet roboai-docker.service 2>/dev/null; then
        log_test "Systemd auto-start" "PASS" "Enabled"
    else
        log_test "Systemd auto-start" "WARN" "Service exists but not enabled"
    fi
else
    log_test "Systemd auto-start" "WARN" "Service not installed (optional)"
fi

# Test 17: Container logs check
echo "Test 17: Container logs (checking for errors)..."
ERROR_COUNT=$(docker logs $CONTAINER_NAME 2>&1 | grep -i "error" | grep -v "ERROR_METRICS" | wc -l)
if [ "$ERROR_COUNT" -eq 0 ]; then
    log_test "Container logs" "PASS" "No errors in logs"
else
    log_test "Container logs" "WARN" "$ERROR_COUNT error message(s) in logs"
fi

# Test 18: GPU access
echo "Test 18: GPU access in container..."
if docker exec $CONTAINER_NAME nvidia-smi > /dev/null 2>&1; then
    log_test "GPU access" "PASS"
else
    log_test "GPU access" "WARN" "nvidia-smi not accessible (may not be critical)"
fi

# Test 19: Network connectivity
echo "Test 19: Network connectivity..."
if docker exec $CONTAINER_NAME ping -c 1 8.8.8.8 > /dev/null 2>&1; then
    log_test "Network connectivity" "PASS"
else
    log_test "Network connectivity" "FAIL" "No network connectivity"
fi

# Test 20: Disk space
echo "Test 20: Disk space availability..."
DISK_USAGE=$(df -h /home | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -lt 90 ]; then
    log_test "Disk space" "PASS" "${DISK_USAGE}% used"
else
    log_test "Disk space" "WARN" "${DISK_USAGE}% used - running low on space"
fi

# Summary
echo ""
echo "=========================================="
echo "Test Summary"
echo "=========================================="
echo ""
echo "Total Tests: $((PASS_COUNT + FAIL_COUNT))"
echo -e "${GREEN}Passed: $PASS_COUNT${NC}"
echo -e "${RED}Failed: $FAIL_COUNT${NC}"
echo ""

# Detailed results
echo "Detailed Results:"
for result in "${TEST_RESULTS[@]}"; do
    echo "  - $result"
done

echo ""
echo "=========================================="

# System information
echo ""
echo "System Information:"
echo "  Container: $CONTAINER_NAME"
echo "  Uptime: $(docker inspect --format='{{.State.StartedAt}}' $CONTAINER_NAME 2>/dev/null || echo 'N/A')"
echo "  Image: $(docker inspect --format='{{.Config.Image}}' $CONTAINER_NAME 2>/dev/null || echo 'N/A')"

# Resource usage
echo ""
echo "Resource Usage:"
docker stats --no-stream $CONTAINER_NAME 2>/dev/null || echo "  Unable to get stats"

# Exit with appropriate code
if [ "$FAIL_COUNT" -gt 0 ]; then
    echo ""
    echo -e "${RED}Some tests failed. Please review the results above.${NC}"
    exit 1
else
    echo ""
    echo -e "${GREEN}All critical tests passed!${NC}"
    exit 0
fi
