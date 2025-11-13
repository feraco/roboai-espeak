# CycloneDDS + Unitree SDK2 Python Fix (Jetson)

This guide fixes the common error when installing or using `unitree_sdk2_python` on Jetson:

> `could not locate cyclonedds`  
> or `ModuleNotFoundError: No module named 'cyclonedds'`

The root cause is that the Unitree SDK depends on CycloneDDS being installed and visible in your environment.

---

## 1. Install CycloneDDS on Jetson

SSH into the Jetson:

```bash
ssh unitree@<JETSON_IP>
cd ~
```

Install build dependencies:

```bash
sudo apt-get update
sudo apt-get install -y \
  cmake build-essential git \
  libssl-dev libice-dev libsm-dev libx11-dev
```

Clone and build CycloneDDS:

```bash
# Clone CycloneDDS
cd ~
git clone https://github.com/eclipse-cyclonedds/cyclonedds.git
cd cyclonedds

# Build and install to /opt/cyclonedds/install
mkdir build
cd build
cmake -DCMAKE_BUILD_TYPE=Release \
      -DCMAKE_INSTALL_PREFIX=/opt/cyclonedds/install \
      ..
make -j"$(nproc)"
sudo make install
```

Register the libraries:

```bash
echo "/opt/cyclonedds/install/lib" | sudo tee /etc/ld.so.conf.d/cyclonedds.conf
sudo ldconfig
```

Quick verification:

```bash
ls /opt/cyclonedds/install/lib
# You should see libddsc.so and related CycloneDDS libs
```

---

## 2. Set CycloneDDS Environment Variables (Shell)

From the repo root on the Jetson (for example):

```bash
cd ~/roboai-feature-multiple-agent-configurations

export CYCLONEDDS_HOME=/opt/cyclonedds/install
export CYCLONEDDS_URI="file://$PWD/cyclonedds/cyclonedds.xml"
export CMAKE_PREFIX_PATH=/opt/cyclonedds/install
export LD_LIBRARY_PATH=/opt/cyclonedds/install/lib:$LD_LIBRARY_PATH
```

You can add these lines to `~/.bashrc` or `~/.zshrc` to make them persistent for interactive shells.

---

## 3. Install Unitree SDK2 Python into UV Environment

From the repo root on the Jetson:

```bash
cd ~/roboai-feature-multiple-agent-configurations

# Install Unitree SDK2 Python into UV's virtualenv
uv pip install git+https://github.com/unitreerobotics/unitree_sdk2_python.git
```

Or if you prefer to clone first:

```bash
cd ~
git clone https://github.com/unitreerobotics/unitree_sdk2_python.git

cd ~/roboai-feature-multiple-agent-configurations
uv pip install ~/unitree_sdk2_python/
```

Test that the SDK and CycloneDDS are visible to UV:

```bash
cd ~/roboai-feature-multiple-agent-configurations
uv run python -c "from unitree.unitree_sdk2py.g1.arm.g1_arm_action_client import G1ArmActionClient; print('✅ Unitree SDK + CycloneDDS OK')"
```

If this prints the ✅ message, the SDK and CycloneDDS are correctly installed for `uv run`.

---

## 4. Wire CycloneDDS into Systemd Service (Autostart)

If you use the `astra_agent` systemd service on Jetson, you must add the CycloneDDS env vars there as well.

Edit the service file (on Jetson):

```bash
sudo nano /etc/systemd/system/astra_agent.service
```

Under the `[Service]` section, add:

```ini
Environment="CYCLONEDDS_HOME=/opt/cyclonedds/install"
Environment="CYCLONEDDS_URI=file:///home/unitree/roboai-feature-multiple-agent-configurations/cyclonedds/cyclonedds.xml"
Environment="CMAKE_PREFIX_PATH=/opt/cyclonedds/install"
Environment="LD_LIBRARY_PATH=/opt/cyclonedds/install/lib:/usr/local/lib:/usr/lib"
```

Adjust the path `/home/unitree/roboai-feature-multiple-agent-configurations` if your username or repo location is different.

Reload and restart the service:

```bash
sudo systemctl daemon-reload
sudo systemctl restart astra_agent
sudo journalctl -u astra_agent -f
```

You should no longer see CycloneDDS-related errors.

---

## 5. Common Errors and Fixes

### Error: `could not locate cyclonedds`

- Ensure CycloneDDS is built and installed to `/opt/cyclonedds/install`.
- Ensure `LD_LIBRARY_PATH` includes `/opt/cyclonedds/install/lib`.
- Ensure `CYCLONEDDS_URI` points to a valid XML file, e.g.:
  - `file:///home/unitree/roboai-feature-multiple-agent-configurations/cyclonedds/cyclonedds.xml`

### Error: `ModuleNotFoundError: No module named 'unitree'`

- Ensure you ran `uv pip install git+https://github.com/unitreerobotics/unitree_sdk2_python.git` **inside the repo**.
- Remember: system-wide Python installs do **not** automatically apply to `uv run`.

### Error: Works in shell, fails in systemd

- Check `Environment=` lines in `/etc/systemd/system/astra_agent.service`.
- Run:

```bash
sudo systemctl show astra_agent | grep -E "CYCLONEDDS|LD_LIBRARY_PATH|CMAKE_PREFIX_PATH"
```

- If variables are missing, update the service file and run:

```bash
sudo systemctl daemon-reload
sudo systemctl restart astra_agent
```

---

## 6. Quick Checklist

- [ ] CycloneDDS built and installed at `/opt/cyclonedds/install`
- [ ] `LD_LIBRARY_PATH` includes `/opt/cyclonedds/install/lib`
- [ ] `CYCLONEDDS_URI` points to the repo's `cyclonedds/cyclonedds.xml`
- [ ] `uv pip install git+https://github.com/unitreerobotics/unitree_sdk2_python.git` completed without errors
- [ ] `uv run` import test succeeds
- [ ] systemd service has CycloneDDS env vars and starts without errors

Once all of these are checked, the Unitree SDK-based actions and inputs should run without CycloneDDS errors on Jetson.
