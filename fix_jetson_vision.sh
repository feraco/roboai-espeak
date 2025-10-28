#!/bin/bash
# Fix VLMOllamaVision issues on Jetson Orin

set -e

echo "=========================================="
echo "Fixing VLMOllamaVision on Jetson Orin"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print status
print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[⚠]${NC} $1"
}

# 1. Check if we're on Jetson
echo ""
echo "1. Checking if running on Jetson..."
if [ -f /etc/nv_tegra_release ]; then
    print_status "Running on Jetson: $(cat /etc/nv_tegra_release | head -1)"
else
    print_warning "Not running on Jetson (or nv_tegra_release not found)"
fi

# 2. Install OpenCV and NumPy in UV environment
echo ""
echo "2. Installing OpenCV and NumPy..."
if command -v uv &> /dev/null; then
    print_status "UV found, installing dependencies..."
    uv pip install opencv-python-headless numpy
    print_status "OpenCV and NumPy installed"
else
    print_error "UV not found. Install UV first: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# 3. Check camera permissions
echo ""
echo "3. Checking camera permissions..."
if groups | grep -q video; then
    print_status "User is in 'video' group"
else
    print_warning "User not in 'video' group"
    echo "Adding user to video group (requires sudo)..."
    sudo usermod -aG video $USER
    print_status "User added to 'video' group - YOU MUST LOGOUT AND LOGIN AGAIN for this to take effect"
fi

# 4. Check camera devices
echo ""
echo "4. Checking camera devices..."
if ls /dev/video* &> /dev/null; then
    print_status "Camera devices found:"
    ls -l /dev/video* 2>/dev/null || true
else
    print_error "No camera devices found (/dev/video*)"
    echo "Possible fixes:"
    echo "  1. Check if camera is connected"
    echo "  2. Run: sudo modprobe v4l2-ctl"
    echo "  3. For CSI cameras, check cable connection"
fi

# 5. Check Ollama
echo ""
echo "5. Checking Ollama service..."
if systemctl is-active --quiet ollama 2>/dev/null; then
    print_status "Ollama service is running"
elif pgrep -x "ollama" > /dev/null; then
    print_status "Ollama is running (as process)"
else
    print_warning "Ollama is not running"
    echo "Starting Ollama..."
    if command -v systemctl &> /dev/null; then
        sudo systemctl start ollama
        print_status "Ollama service started"
    else
        print_warning "Please start Ollama manually: ollama serve"
    fi
fi

# 6. Check for vision models
echo ""
echo "6. Checking for vision models..."
if curl -s http://localhost:11434/api/tags 2>/dev/null | grep -q "llava"; then
    print_status "Vision models found"
else
    print_warning "No vision models found"
    echo "Installing llava-llama3..."
    ollama pull llava-llama3
    print_status "llava-llama3 installed"
fi

# 7. Test camera with Python
echo ""
echo "7. Testing camera access with Python..."
cat > /tmp/test_camera.py << 'EOF'
import cv2
import sys

try:
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("ERROR: Cannot open camera 0")
        sys.exit(1)
    
    ret, frame = cap.read()
    if ret:
        print(f"SUCCESS: Camera working! Resolution: {frame.shape[1]}x{frame.shape[0]}")
        cap.release()
        sys.exit(0)
    else:
        print("ERROR: Camera opened but cannot read frames")
        cap.release()
        sys.exit(1)
except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)
EOF

if uv run python /tmp/test_camera.py; then
    print_status "Camera test passed"
else
    print_error "Camera test failed"
    echo "Troubleshooting steps:"
    echo "  1. Check if camera is physically connected"
    echo "  2. Try different camera index (0, 1, 2) in config"
    echo "  3. Check camera permissions: ls -l /dev/video*"
    echo "  4. Reboot Jetson if camera was just connected"
fi

rm -f /tmp/test_camera.py

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. If you were added to 'video' group: LOGOUT AND LOGIN AGAIN"
echo "  2. Run diagnostic: uv run python diagnose_jetson_vision.py"
echo "  3. Test agent: uv run src/run.py astra_vein_receptionist"
echo ""
echo "If camera still doesn't work, try:"
echo "  - Different camera_index in config (0, 1, or 2)"
echo "  - Reboot Jetson"
echo "  - Check dmesg | grep video for hardware errors"
