# Jetson Audio Autostart Fix (USB Mic + USB 2.0 Speaker)

When the Astra agent runs fine with:

```bash
uv run src/run.py astra_vein_receptionist_arm
```

but the `astra_agent` systemd service fails with messages like:

- `Waiting for USB 2.0 Speaker...`  
- `Waiting for USB PnP Sound Device...`  
- and then `Failed to start arm enabled` / service failure,

it usually means the pre-start script never finds the mic/speaker, times out, and the service fails.

This guide shows how to align the pre-start script with the actual device names and make it **non-fatal** so the service can still start.

---

## High-level plan

1. On the Jetson, check the actual PulseAudio device names for microphone and speaker.
2. Adjust the `grep` patterns in `astra_pre_start_checks.sh` to match the real device names.
3. Make the pre-start script log warnings but **not** fail the service if audio isn’t perfect yet.
4. Ensure the systemd service has the right environment (`XDG_RUNTIME_DIR`) and reload systemd.

---

## 1. Check actual device names on the Jetson

On the Jetson:

```bash
ssh unitree@<JETSON_IP>
cd ~/roboai-feature-multiple-agent-configurations

# List sources (microphones)
pactl list short sources

# List sinks (speakers)
pactl list short sinks
```

Look for lines that correspond to:

- USB mic (we initially assumed something like `USB_PnP_Sound_Device`)
- USB 2.0 speaker (we assumed `USB_2.0_Speaker`)

Example real output might look like:

- Source (mic):
  - `alsa_input.usb-C-Media_Electronics_Inc._USB_PnP_Sound_Device-00.mono-fallback`
- Sink (speaker):
  - `alsa_output.usb-Generic_USB2.0_Speaker-00.analog-stereo`

The important part is a **stable substring** you can reliably `grep` for (e.g., `USB_PnP`, `USB2.0_Speaker`, etc.).

---

## 2. Update `astra_pre_start_checks.sh` to match real names and be tolerant

Edit the pre-start script on the Jetson:

```bash
sudo nano /home/unitree/roboai-feature-multiple-agent-configurations/deployment/astra_pre_start_checks.sh
```

Locate the mic/speaker detection section (originally something like):

```bash
MIC=$(pactl list short sources 2>/dev/null | grep "USB_PnP_Sound_Device" | awk '{print $2}' | head -n1)
SPEAKER=$(pactl list short sinks 2>/dev/null | grep "USB_2.0_Speaker" | awk '{print $2}' | head -n1)
```

Replace the `grep` patterns with substrings that match your actual device names from step 1. For example, if `pactl` shows:

- `alsa_input.usb-C-Media_Electronics_Inc._USB_PnP_Sound_Device-00.mono-fallback`
- `alsa_output.usb-Generic_USB2.0_Speaker-00.analog-stereo`

you could use:

```bash
MIC=$(pactl list short sources 2>/dev/null | grep "USB_PnP" | awk '{print $2}' | head -n1)
SPEAKER=$(pactl list short sinks 2>/dev/null | grep "USB2.0_Speaker" | awk '{print $2}' | head -n1)
```

or similar stable substrings that match your exact output.

### Make the waits non-fatal

Ensure the wait loops log warnings but **do not exit** on timeout:

```bash
echo "⏳ Waiting for USB PnP Sound Device (microphone)..."
for i in $(seq 1 $MAX_WAIT); do
    if pactl list short sources 2>/dev/null | grep "USB_PnP" > /dev/null; then
        echo "✅ USB microphone ready"
        break
    fi
    if [ $i -eq $MAX_WAIT ]; then
        echo "⚠️  Timeout waiting for USB microphone (continuing anyway)"
    else
        sleep 1
    fi
done

echo "⏳ Waiting for USB 2.0 Speaker..."
for i in $(seq 1 $MAX_WAIT); do
    if pactl list short sinks 2>/dev/null | grep "USB2.0" > /dev/null; then
        echo "✅ USB speaker ready"
        break
    fi
    if [ $i -eq $MAX_WAIT ]; then
        echo "⚠️  Timeout waiting for USB speaker (continuing anyway)"
    else
        sleep 1
    fi
done
```

### Make default-setting tolerant

Keep the "set default" block tolerant as well:

```bash
echo "🔧 Setting audio defaults..."
MIC=$(pactl list short sources 2>/dev/null | grep "USB_PnP" | awk '{print $2}' | head -n1)
SPEAKER=$(pactl list short sinks 2>/dev/null | grep "USB2.0" | awk '{print $2}' | head -n1)

if [ -n "$MIC" ]; then
    pactl set-default-source "$MIC"
    echo "✅ Default microphone: $MIC"
else
    echo "⚠️  No USB microphone found to set as default"
fi

if [ -n "$SPEAKER" ]; then
    pactl set-default-sink "$SPEAKER"
    echo "✅ Default speaker: $SPEAKER"
else
    echo "⚠️  No USB speaker found to set as default"
fi
```

This way, even if the devices are slow to appear or temporarily missing, the script logs a warning but does **not** cause the service to fail.

Finally, ensure the script is executable:

```bash
sudo chmod +x /home/unitree/roboai-feature-multiple-agent-configurations/deployment/astra_pre_start_checks.sh
```

---

## 3. Ensure the systemd service can talk to PulseAudio

`pactl` needs the correct `XDG_RUNTIME_DIR` so it can talk to the user’s PulseAudio instance.

Edit the service file:

```bash
sudo nano /etc/systemd/system/astra_agent.service
```

Within `[Service]`, make sure you have something like:

```ini
User=unitree
WorkingDirectory=/home/unitree/roboai-feature-multiple-agent-configurations
Environment="PATH=/home/unitree/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
Environment="XDG_RUNTIME_DIR=/run/user/1000"
ExecStartPre=/bin/bash /home/unitree/roboai-feature-multiple-agent-configurations/deployment/astra_pre_start_checks.sh
ExecStart=/home/unitree/.local/bin/uv run src/run.py astra_vein_receptionist_arm
```

Adjust `User`, `WorkingDirectory`, and `XDG_RUNTIME_DIR` if your username or UID is different (check with `id` on the Jetson).

Reload systemd and restart the service:

```bash
sudo systemctl daemon-reload
sudo systemctl restart astra_agent
sudo journalctl -u astra_agent -f
```

You should now see:

- "⏳ Waiting for USB PnP Sound Device..."  
- Either "✅ USB microphone ready" **or** "⚠️ Timeout... (continuing anyway)"
- And the service should continue to start, instead of failing just because audio wasn’t immediately ready.

---

## 4. Summary

1. Use `pactl list short sources/sinks` to find your **real** USB mic and speaker names.
2. Update `astra_pre_start_checks.sh` to `grep` for those real substrings.
3. Make the waits and defaults tolerant: log warnings instead of failing.
4. Ensure `astra_agent.service` has `XDG_RUNTIME_DIR` and correct paths.
5. Reload systemd and restart the service; verify behavior with `journalctl`.

Once these steps are done, the "waiting for USB 2.0 speaker / PnP microphone" messages will be informative logs, not the reason the arm-enabled Astra service fails to start.
