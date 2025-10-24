#!/bin/bash
# Organize documentation files

echo "📁 Organizing documentation files..."

# Setup guides
mv API_KEYS_GUIDE.md documentation/setup/ 2>/dev/null
mv QUICK_INSTALL_MAC.md documentation/setup/ 2>/dev/null
mv LOCAL_SETUP.md documentation/setup/ 2>/dev/null
mv QUICKSTART.md documentation/setup/ 2>/dev/null
mv setup_with_uv.sh documentation/setup/ 2>/dev/null

# Ubuntu/G1 deployment
mv UBUNTU_G1_DEPLOYMENT.md documentation/setup/ 2>/dev/null
mv FASTER_WHISPER_INSTALL.md documentation/setup/ 2>/dev/null
mv setup_piper_ubuntu.sh documentation/setup/ 2>/dev/null
mv setup_g1_autostart.sh documentation/setup/ 2>/dev/null
mv setup_g1_hotspot.sh documentation/setup/ 2>/dev/null
mv setup_robostore_ai.sh documentation/setup/ 2>/dev/null

# Configuration guides
mv CONFIG_GUIDE.md documentation/guides/ 2>/dev/null
mv QUICK_CONFIG_REFERENCE.md documentation/reference/ 2>/dev/null
mv CONFIGURATION_FIX_SUMMARY.md documentation/reference/ 2>/dev/null

# Integration guides
mv G1_ARM_INTEGRATION_GUIDE.md documentation/guides/ 2>/dev/null
mv G1_COMPLETE_SETUP_GUIDE.md documentation/guides/ 2>/dev/null
mv AVSPEECH_INTEGRATION.md documentation/guides/ 2>/dev/null
mv ROBOSTORE_AI_GUIDE.md documentation/guides/ 2>/dev/null
mv G1_HOTSPOT_GUIDE.md documentation/guides/ 2>/dev/null
mv G1_AUTOSTART_GUIDE.md documentation/guides/ 2>/dev/null

# Troubleshooting
mv G1_AUDIO_AUTO_FIX.md documentation/troubleshooting/ 2>/dev/null
mv G1_HARDWARE_TESTING.md documentation/troubleshooting/ 2>/dev/null
mv diagnose_ubuntu_audio.py documentation/troubleshooting/ 2>/dev/null
mv fix_g1_audio.sh documentation/troubleshooting/ 2>/dev/null
mv test_g1_hardware.sh documentation/troubleshooting/ 2>/dev/null
mv test_ubuntu_mic.sh documentation/troubleshooting/ 2>/dev/null
mv check_g1_hardware.py documentation/troubleshooting/ 2>/dev/null

# Reference docs
mv REFACTOR_SUMMARY.md documentation/reference/ 2>/dev/null

echo "✅ Documentation organized!"
echo ""
echo "Structure:"
echo "  documentation/"
echo "    ├── setup/          (Installation & setup guides)"
echo "    ├── guides/         (Integration & configuration)"
echo "    ├── troubleshooting/ (Diagnostic tools)"
echo "    └── reference/      (Technical references)"
