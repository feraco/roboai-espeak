# Last Steps: Jetson/G1 Audio, CycloneDDS, OM1, and Astra Autostart Restart

## 1. Refresh Your Environment

After installing packages, either restart your Terminal or run:
```bash
source "$HOME/.local/bin/env"
```
This ensures your PATH and environment variables are up to date.

---

## 2. Install Voice and Video Packages

```bash
sudo apt-get update
sudo apt-get install -y portaudio19-dev python-all-dev
sudo apt-get install -y ffmpeg v4l-utils
```
- `ffmpeg` (with `ffprobe`) is required for audio.
- `v4l-utils` is required for video/camera support.

---

## 3. Install CycloneDDS (for DDS/G1 motion client)

```bash
cd ~
git clone https://github.com/eclipse-cyclonedds/cyclonedds -b releases/0.10.x
cd cyclonedds
mkdir build
cd build
cmake -DBUILD_EXAMPLES=ON -DCMAKE_INSTALL_PREFIX=$HOME/Documents/GitHub/cyclonedds/install ..
cmake --build .
cmake --build . --target install
```



## 4. CycloneDDS Fix for G1 Orin (Unitree `unitree_hg` Bug)

- The default CycloneDDS on G1 Orin does **not** support the newer `unitree_hg` IDL format.
- Solution: Remove the default CycloneDDS and reinstall following Unitree ROS2 instructions.
- The bug was fixed in Dec. 2024 (`unitreerobotics/unitree_ros2@b34fdf7`).
- If you missed this during ROS2 setup, revisit Module 1 (ROS2).

Set the correct environment variable:
```bash
export CYCLONEDDS_HOME="$HOME/unitree_ros2/cyclonedds_ws/install/cyclonedds"
```
Add to your shell config for persistence:
```bash
echo 'export CYCLONEDDS_HOME="$HOME/unitree_ros2/cyclonedds_ws/install/cyclonedds"' >> ~/.bashrc
source ~/.bashrc

maybe this is needed - 

export CYCLONEDDS_HOME="$HOME/unitree_ros2/cyclonedds_ws/install/cyclonedds"
export CMAKE_PREFIX_PATH="$HOME/unitree_ros2/cyclonedds_ws/install:$CMAKE_PREFIX_PATH"
export LD_LIBRARY_PATH="$CYCLONEDDS_HOME/lib:$LD_LIBRARY_PATH"
export PATH="$CYCLONEDDS_HOME/bin:$PATH"
```

---

## 6. Astra Autostart Restart Helper

**Create the restart script:**
```bash
sudo nano /home/unitree/roboai-espeak/deployment/restart_astra_agent.sh
```
Paste:
```bash
#!/bin/bash
sleep 20
/usr/bin/systemctl restart astra_vein_autostart.service
```
Make it executable:
```bash
sudo chmod +x /home/unitree/roboai-espeak/deployment/restart_astra_agent.sh
```

**Wire into rc.local for auto-restart after boot:**
```bash
sudo nano /etc/rc.local
```
Paste:
```bash
#!/bin/bash
/home/unitree/roboai-espeak/deployment/restart_astra_agent.sh &
exit 0
```
Make executable:
```bash
sudo chmod +x /etc/rc.local
sudo systemctl enable --now rc-local.service 2>/dev/null || true
```

---

## Summary

- Refresh environment after installing packages.
- Install required audio/video packages.
- Build and install CycloneDDS.
- Set up OM1 with DDS support.
- Fix CycloneDDS for G1 Orin if needed.
- Use the Astra restart helper to ensure reliable autostart after boot.
