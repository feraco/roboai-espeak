# Fixing "No Module Named Unitree" Error on Jetson

## Problem
When trying to add arm movements to your Astra config on the Jetson Orin, you get:
```
error loading config: no module named unitree
```

## Root Cause
The Unitree SDK is not installed in **UV's virtual environment** on your Jetson. Even if you installed it system-wide with `sudo python3 setup.py install`, UV can't see it because UV uses an isolated `.venv` directory.

## Quick Fix (Run on Jetson)

### Step 1: Transfer the fix script to your Jetson

On your **Mac**, copy the script to Jetson:
```bash
# Replace with your Jetson's IP and username
scp fix_unitree_sdk_jetson.sh unitree@YOUR_JETSON_IP:~/
```

### Step 2: Run the fix script on Jetson

SSH into your **Jetson**:
```bash
ssh unitree@YOUR_JETSON_IP
cd ~/roboai-espeak
bash ~/fix_unitree_sdk_jetson.sh
```

The script will:
1. Clone the Unitree SDK if needed
2. Install it into UV's virtual environment
3. Verify the installation works

## Manual Fix (If script fails)

SSH into your **Jetson** and run:

```bash
# 1. Navigate to your project
cd ~/roboai-espeak

# 2. Clone SDK if you haven't already
cd ~
git clone https://github.com/unitreerobotics/unitree_sdk2_python.git

# 3. Install into UV's environment
cd ~/roboai-espeak
uv pip install ~/unitree_sdk2_python/

# 4. Verify it works
uv run python -c "from unitree.unitree_sdk2py.g1.arm.g1_arm_action_client import G1ArmActionClient; print('✅ Works!')"
```

## Diagnostic Tool

If you're still having issues, run the diagnostic script on your **Jetson**:

```bash
# Transfer diagnostic script to Jetson first
scp diagnose_unitree_sdk.py unitree@YOUR_JETSON_IP:~/roboai-espeak/

# On Jetson, run diagnostic
cd ~/roboai-espeak
uv run python diagnose_unitree_sdk.py
```

This will tell you exactly what's wrong and how to fix it.

## Why This Happens

| Environment | Installation Method | Accessible to `python3` | Accessible to `uv run` |
|-------------|---------------------|------------------------|------------------------|
| System-wide | `sudo python3 setup.py install` | ✅ Yes | ❌ No |
| UV's .venv | `uv pip install ...` | ❌ No | ✅ Yes |

**Solution:** You need to install with `uv pip install` for it to work with `uv run src/run.py`

## Verifying It Works

On your **Jetson**, test the import:

```bash
cd ~/roboai-espeak
uv run python -c "from unitree.unitree_sdk2py.g1.arm.g1_arm_action_client import G1ArmActionClient; print('SDK works!')"
```

Expected output:
```
SDK works!
```

Then try running your agent:
```bash
uv run src/run.py astra_vein_receptionist
```

## Common Issues

### Issue: "git clone failed"
**Fix:** Check internet connection on Jetson
```bash
ping github.com
```

### Issue: "uv command not found"
**Fix:** Install UV on Jetson
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc
```

### Issue: SDK installs but still can't import
**Fix:** You might have multiple Python versions. Ensure you're using UV consistently:
```bash
# DON'T use:
python src/run.py astra_vein_receptionist

# DO use:
uv run src/run.py astra_vein_receptionist
```

## Next Steps

Once the SDK is installed:

1. **Add arm action to your config** (`config/astra_vein_receptionist.json5`):
```json5
{
  unitree_ethernet: "eno1",  // Your Jetson's ethernet interface
  
  agent_actions: [
    {
      name: "speak",
      llm_label: "speak",
      connector: "piper_tts",
      config: { /* ... */ }
    },
    {
      name: "arm_g1",
      llm_label: "arm movement",
      connector: "unitree_sdk",
      config: {}
    }
  ]
}
```

2. **Update system prompts** with arm gesture examples (see JETSON_SETUP.md Step 11.5)

3. **Test arm movements**:
```bash
uv run src/run.py astra_vein_receptionist
# Say: "Wave hello!"
```

## Need More Help?

- See: `docs/UNITREE_SDK_UV_INSTALL.md` - Complete guide
- See: `JETSON_SETUP.md` Step 11 - Full G1 arm setup instructions
- Run: `diagnose_unitree_sdk.py` - Detailed diagnostic

---

**TL;DR:** On your Jetson, run:
```bash
cd ~/roboai-espeak
uv pip install git+https://github.com/unitreerobotics/unitree_sdk2_python.git
```
