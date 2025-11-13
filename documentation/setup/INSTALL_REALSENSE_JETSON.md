# Intel RealSense D435i Installation Guide - Jetson Orin Nano

This guide covers installing the Intel RealSense SDK and drivers on Jetson Orin Nano for use with the Astra Vein receptionist agent.

## Prerequisites

- Jetson Orin Nano with JetPack 5.x or 6.x
- Intel RealSense D435i camera
- USB 3.0 connection
- Internet connection for package downloads

## Quick Installation (Recommended)

### 1. Install librealsense2 from Intel Repository

```bash
# Register Intel's public key
sudo mkdir -p /etc/apt/keyrings
curl -sSf https://librealsense.intel.com/Debian/librealsense.pgp | sudo tee /etc/apt/keyrings/librealsense.pgp > /dev/null

# Add Intel repository
echo "deb [signed-by=/etc/apt/keyrings/librealsense.pgp] https://librealsense.intel.com/Debian/apt-repo `lsb_release -cs` main" | \
sudo tee /etc/apt/sources.list.d/librealsense.list

# Update and install
sudo apt-get update
sudo apt-get install -y librealsense2-dkms librealsense2-utils librealsense2-dev
```

### 2. Verify Installation

```bash
# Check kernel modules loaded
lsmod | grep uvcvideo

# List RealSense devices
realsense-viewer
# OR command-line check:
rs-enumerate-devices
```

### 3. Test Camera Connection

```bash
# Plug in RealSense D435i to USB 3.0 port

# Check if detected
v4l2-ctl --list-devices | grep -A 5 RealSense

# Should show something like:
# Intel(R) RealSense(TM) Depth Camera 435i (usb-xhci-hcd.1-2):
#     /dev/video0
#     /dev/video1
#     /dev/video2
#     /dev/video3
#     /dev/video4  ← RGB camera typically here
#     /dev/video5
```

### 4. Find RGB Camera Index

The RealSense D435i exposes multiple video devices. You need the RGB camera index:

```bash
# Test each video device to find RGB camera
for i in {0..10}; do
    echo "Testing /dev/video$i..."
    timeout 2 ffmpeg -f v4l2 -i /dev/video$i -frames:v 1 -f null - 2>&1 | grep -q "Stream.*Video" && echo "✅ Video $i works (likely RGB)"
done

# OR use v4l2-ctl to check pixel formats
for i in {0..10}; do
    echo "=== /dev/video$i ==="
    v4l2-ctl -d /dev/video$i --list-formats-ext 2>/dev/null | grep -E "(YUYV|MJPG|RGB)"
done
```

**Typical RealSense D435i Layout:**
- `/dev/video0-3` - Depth/IR sensors
- **`/dev/video4`** - RGB camera (1920x1080, YUYV) ← Use this for `camera_index: 4`
- `/dev/video5` - Metadata

### 5. Set Permissions (if needed)

```bash
# Add user to video group
sudo usermod -a -G video $USER

# Apply udev rules for RealSense
sudo cp /etc/udev/rules.d/99-realsense-libusb.rules /etc/udev/rules.d/ 2>/dev/null || \
echo 'SUBSYSTEM=="usb", ATTRS{idVendor}=="8086", ATTRS{idProduct}=="0b3a", MODE="0666", GROUP="plugdev"' | \
sudo tee /etc/udev/rules.d/99-realsense-d435i.rules

# Reload udev rules
sudo udevadm control --reload-rules && sudo udevadm trigger
```

### 6. Test with Python (OpenCV)

```bash
cd ~/roboai-feature-multiple-agent-configurations

# Test camera 4 (typical RGB camera index)
python3 test_camera.py

# Or quick inline test:
python3 -c "
import cv2
cap = cv2.VideoCapture(4)
if cap.isOpened():
    ret, frame = cap.read()
    if ret:
        print(f'✅ Camera 4 working! Resolution: {frame.shape[1]}x{frame.shape[0]}')
    else:
        print('❌ Failed to read frame')
    cap.release()
else:
    print('❌ Camera 4 not available')
"
```

## Configuration for Astra Agent

Once you've determined the RGB camera index (typically 4), update your config:

**`config/astra_vein_receptionist_arm.json5`:**
```json5
agent_inputs: [
  {
    type: "FaceEmotionCapture",
    config: {
      camera_index: 4,      // ← Your RealSense RGB camera index
      poll_interval: 60.0,
      timeout: 5
    }
  }
]
```

## Troubleshooting

### Camera Not Detected

```bash
# Check USB connection
lsusb | grep Intel

# Should show:
# Bus 001 Device 003: ID 8086:0b3a Intel Corp. RealSense D435i

# Check dmesg for errors
dmesg | grep -i realsense
```

### Permission Denied Errors

```bash
# Check current permissions
ls -la /dev/video*

# Fix permissions
sudo chmod 666 /dev/video*

# Permanent fix via udev (see step 5 above)
```

### Wrong Camera Index After Reboot

This is handled automatically by the robust autostart system:

1. **Pre-start script** (`deployment/astra_pre_start_checks.sh`) waits for RealSense at the correct `/dev/video` index
2. **FaceEmotionCapture** now reads `camera_index` from config (fixed in this update)
3. **Systemd service** includes pre-start checks

If the camera index changes, update the config and restart:
```bash
sudo systemctl restart astra_agent
```

### Multiple RealSense Cameras

If you have multiple RealSense devices, identify by serial number:

```bash
rs-enumerate-devices | grep -A 10 "Device info"
# Note the serial number

# Use pyrealsense2 to select by serial (advanced usage)
```

## Build from Source (Alternative Method)

If the Intel repository doesn't work for your JetPack version:

```bash
# Install dependencies
sudo apt-get install -y git libssl-dev libusb-1.0-0-dev pkg-config libgtk-3-dev
sudo apt-get install -y libglfw3-dev libgl1-mesa-dev libglu1-mesa-dev

# Clone and build
cd ~/
git clone https://github.com/IntelRealSense/librealsense.git
cd librealsense
mkdir build && cd build

# Configure for Jetson
cmake .. -DFORCE_RSUSB_BACKEND=true -DBUILD_PYTHON_BINDINGS=bool:true -DCMAKE_BUILD_TYPE=release

# Build (this takes ~30 minutes on Jetson)
make -j$(nproc)
sudo make install

# Update library cache
sudo ldconfig
```

## Verification Checklist

- [ ] `librealsense2-utils` installed
- [ ] `rs-enumerate-devices` shows D435i
- [ ] `v4l2-ctl --list-devices` shows RealSense with multiple `/dev/video*`
- [ ] RGB camera index identified (typically `/dev/video4`)
- [ ] `python3 test_camera.py` captures from RGB camera
- [ ] User added to `video` group
- [ ] Udev rules applied
- [ ] Config updated with correct `camera_index`
- [ ] Agent starts without camera errors

## Integration with Astra Agent

The Astra Vein agent uses the RealSense RGB camera for face emotion detection:

1. **FaceEmotionCapture** polls every 60 seconds
2. **DeepFace** analyzes detected faces for emotion
3. **Proactive greeting** triggers when face detected (once per 5 minutes)
4. **Vision context** passed to LLM without announcing

The robust autostart system ensures the camera is ready before the agent starts.

## References

- [Intel RealSense GitHub](https://github.com/IntelRealSense/librealsense)
- [librealsense Documentation](https://dev.intelrealsense.com/docs)
- [Jetson + RealSense Guide](https://github.com/IntelRealSense/librealsense/blob/master/doc/installation_jetson.md)
