# Unitree SDK Installation for UV - Quick Reference

## TL;DR

**Yes, the SDK works from any directory!** But when using UV, you need to install it **into UV's virtual environment**, not just system-wide.

## Two Installation Methods

### Method 1: Direct Git Install (Easiest for UV)

```bash
cd ~/roboai-espeak
uv pip install git+https://github.com/unitreerobotics/unitree_sdk2_python.git
```

### Method 2: Local Clone + Install

```bash
# Clone anywhere (home directory is fine)
cd ~
git clone https://github.com/unitreerobotics/unitree_sdk2_python.git

# Install into UV environment
cd ~/roboai-espeak
uv pip install ~/unitree_sdk2_python/
```

## Why This Matters

### UV's Isolated Environment
- UV creates `.venv/` directory with its own Python environment
- System-wide packages (installed with `sudo python setup.py install`) are **NOT** accessible to `uv run`
- You must explicitly install packages into UV's environment using `uv pip install`

### Comparison

| Installation Method | Accessible to `python3` | Accessible to `uv run` |
|---------------------|------------------------|------------------------|
| `sudo python3 setup.py install` | ✅ Yes | ❌ No |
| `uv pip install ...` | ❌ No | ✅ Yes |
| Both methods | ✅ Yes | ✅ Yes |

## Testing Your Installation

### Test with UV (What the agent uses)
```bash
cd ~/roboai-espeak
uv run python -c "from unitree.unitree_sdk2py.g1.arm.g1_arm_action_client import G1ArmActionClient; print('✅ SDK works with UV')"
```

### Test with system Python (optional)
```bash
python3 -c "from unitree.unitree_sdk2py.g1.arm.g1_arm_action_client import G1ArmActionClient; print('✅ SDK works system-wide')"
```

## Common Issues

### Issue: "ModuleNotFoundError: No module named 'unitree'" when running agent

**Cause:** SDK not installed in UV's environment

**Fix:**
```bash
cd ~/roboai-espeak
uv pip install git+https://github.com/unitreerobotics/unitree_sdk2_python.git
```

### Issue: UV pip install fails

**Alternative:** Manual installation into UV's venv
```bash
cd ~/roboai-espeak
source .venv/bin/activate
cd ~/unitree_sdk2_python
python setup.py install
deactivate

# Test
uv run python -c "import unitree; print('OK')"
```

## Does Clone Location Matter?

**No!** You can clone the SDK anywhere:
- `~/unitree_sdk2_python/` ✅
- `/tmp/unitree_sdk2_python/` ✅
- `/opt/unitree_sdk2_python/` ✅
- `~/Downloads/unitree_sdk2_python/` ✅

Once installed via `uv pip install`, the location doesn't matter. You can even delete the clone after installation (though it's useful to keep for updates).

## Updating the SDK

```bash
# If installed from git
cd ~/roboai-espeak
uv pip install --upgrade git+https://github.com/unitreerobotics/unitree_sdk2_python.git

# If installed from local clone
cd ~/unitree_sdk2_python
git pull
cd ~/roboai-espeak
uv pip install --upgrade ~/unitree_sdk2_python/
```

## When Do You Need Both Installations?

You might want both system-wide AND UV installations if:
- You run scripts outside UV with `python3 script.py`
- You develop/test with Jupyter notebooks using system Python
- You have other projects not using UV

In this case:
```bash
# System-wide installation
cd ~/unitree_sdk2_python
sudo python3 setup.py install

# UV environment installation
cd ~/roboai-espeak
uv pip install ~/unitree_sdk2_python/
```

## Summary

✅ **Clone location:** Doesn't matter (anywhere is fine)  
✅ **For UV agents:** Must install with `uv pip install`  
✅ **System-wide install:** Only helps system Python, not UV  
✅ **Both installations:** Safe and sometimes useful  

---

**Bottom Line:** When using `uv run`, think of UV's environment as completely separate from system Python. Any package you need must be explicitly installed via `uv pip install`.
