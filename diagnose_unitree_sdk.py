#!/usr/bin/env python3
"""
Diagnostic script for Unitree SDK installation issues on Jetson
Run this on your Jetson to diagnose why the SDK isn't loading
"""

import sys
import os
from pathlib import Path

print("="*60)
print("Unitree SDK Diagnostic Tool - Jetson")
print("="*60)
print()

# Check 1: Python version
print("1. Python Environment:")
print(f"   Python version: {sys.version}")
print(f"   Python executable: {sys.executable}")
print(f"   Virtual environment: {hasattr(sys, 'real_prefix') or sys.base_prefix != sys.prefix}")
print()

# Check 2: sys.path
print("2. Python Path (first 5 entries):")
for i, path in enumerate(sys.path[:5], 1):
    print(f"   {i}. {path}")
print()

# Check 3: Try importing unitree
print("3. Attempting to import unitree...")
try:
    import unitree
    print("   ✅ unitree module found!")
    print(f"   Location: {unitree.__file__ if hasattr(unitree, '__file__') else 'built-in'}")
except ImportError as e:
    print(f"   ❌ Import failed: {e}")
    print()
    print("   Possible causes:")
    print("   - SDK not installed in this Python environment")
    print("   - SDK installed in system Python but not UV's .venv")
    print("   - Installation was incomplete")
print()

# Check 4: Try importing the specific class
print("4. Attempting to import G1ArmActionClient...")
try:
    from unitree.unitree_sdk2py.g1.arm.g1_arm_action_client import G1ArmActionClient
    print("   ✅ G1ArmActionClient imported successfully!")
except ImportError as e:
    print(f"   ❌ Import failed: {e}")
print()

# Check 5: Look for SDK in common locations
print("5. Checking for SDK in common locations:")
sdk_locations = [
    Path.home() / "unitree_sdk2_python",
    Path("/opt/unitree_sdk2_python"),
    Path("/tmp/unitree_sdk2_python"),
]

for location in sdk_locations:
    if location.exists():
        print(f"   ✅ Found: {location}")
    else:
        print(f"   ❌ Not found: {location}")
print()

# Check 6: Check if installed packages
print("6. Checking installed packages...")
try:
    import pkg_resources
    installed_packages = [pkg.key for pkg in pkg_resources.working_set]
    unitree_packages = [pkg for pkg in installed_packages if 'unitree' in pkg]
    
    if unitree_packages:
        print(f"   ✅ Found Unitree packages: {unitree_packages}")
    else:
        print("   ❌ No Unitree packages found in installed packages")
except Exception as e:
    print(f"   ⚠ Could not check installed packages: {e}")
print()

# Check 7: Check site-packages
print("7. Checking site-packages directories:")
for path in sys.path:
    if 'site-packages' in path or 'dist-packages' in path:
        site_pkg = Path(path)
        if site_pkg.exists():
            unitree_files = list(site_pkg.glob("*unitree*"))
            if unitree_files:
                print(f"   ✅ {path}")
                for f in unitree_files[:3]:  # Show first 3
                    print(f"      - {f.name}")
            else:
                print(f"   ❌ {path} (no unitree files)")
print()

# Summary and recommendations
print("="*60)
print("SUMMARY & RECOMMENDATIONS")
print("="*60)

try:
    import unitree
    print("✅ SDK is installed and working!")
except ImportError:
    print("❌ SDK is NOT working. Recommended fixes:")
    print()
    print("Option 1 - Install with UV pip (RECOMMENDED):")
    print("  cd ~/roboai-espeak")
    print("  uv pip install git+https://github.com/unitreerobotics/unitree_sdk2_python.git")
    print()
    print("Option 2 - Install from local clone:")
    print("  cd ~")
    print("  git clone https://github.com/unitreerobotics/unitree_sdk2_python.git")
    print("  cd ~/roboai-espeak")
    print("  uv pip install ~/unitree_sdk2_python/")
    print()
    print("Option 3 - Manual install into .venv:")
    print("  cd ~/roboai-espeak")
    print("  source .venv/bin/activate")
    print("  cd ~/unitree_sdk2_python")
    print("  python setup.py install")
    print("  deactivate")
    print()
    print("After installing, run this script again to verify:")
    print("  uv run python diagnose_unitree_sdk.py")
