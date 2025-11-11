# 🎉 Ubuntu G1 Setup Complete!

## ✅ What We Fixed Today

1. **✅ Microphone Working** - Audio input device configured and tested
2. **✅ Speaker Working** - Audio output device tested
3. **📁 Documentation Organized** - All MD files moved to `documentation/` folder

## 🧪 Next: Test Camera on Ubuntu

On your Ubuntu G1 machine, run:

```bash
cd ~/roboai-espeak
git pull origin main

# Test camera
python3 test_camera.py
```

This will:
- Test all available camera indices (0-4)
- Capture test frames
- Save images as `camera_X_test.jpg`
- Tell you which camera index to use

## 📊 Expected Output

```
🎥 CAMERA HARDWARE TEST
==============================================================

🎥 Testing Camera 0
==============================================================
Opening camera at index 0...
✅ Camera opened successfully
   Resolution: 640x480
   FPS: 30.0
Reading test frame...
✅ Frame captured successfully
   Frame shape: (480, 640, 3)
✅ Test image saved: camera_0_test.jpg

📋 SUMMARY
==============================================================
✅ Found 1 working camera(s): [0]

💡 Use camera index 0 in your config:
   "camera_index": 0
==============================================================
```

## 🎛️ Update Config After Camera Test

Once you know which camera works, verify it's set in your config:

`config/astra_vein_receptionist.json5`:
```json5
{
  type: "VLMOllamaVision",
  config: {
    camera_index: 0,  // Use the working index from test
  }
}
```

## 🚀 Full System Test

After camera test passes:

```bash
# 1. Run complete hardware check
python3 documentation/troubleshooting/check_g1_hardware.py

# Should show ALL GREEN:
# ✅ MICROPHONE
# ✅ SPEAKER  
# ✅ CAMERA
# ✅ OLLAMA LLM
# ✅ OLLAMA VISION
# ✅ PIPER TTS

# 2. Start the agent
uv run src/run.py astra_vein_receptionist
```

## 📋 Checklist Before Production

- [x] Microphone tested and working
- [x] Speaker tested and working
- [ ] Camera tested and working
- [ ] Ollama service running (`sudo systemctl status ollama`)
- [ ] Models downloaded (`ollama list`)
- [ ] Piper TTS installed (`ls ~/.local/share/piper/voices`)
- [ ] Hardware check passes (all ✅)
- [ ] Agent starts without errors
- [ ] Vision compliments working
- [ ] Voice recognition working
- [ ] TTS audio output clear

## 📚 Documentation Structure

All documentation is now organized in `documentation/`:

```
documentation/
├── README.md                    # Documentation index
├── setup/                       # Installation guides
│   ├── UBUNTU_G1_DEPLOYMENT.md # Complete Ubuntu guide ⭐
│   ├── QUICKSTART.md
│   ├── setup_piper_ubuntu.sh
│   └── ...
├── guides/                      # Integration guides
│   ├── CONFIG_GUIDE.md
│   ├── G1_ARM_INTEGRATION_GUIDE.md
│   └── ...
├── troubleshooting/             # Diagnostic tools
│   ├── check_g1_hardware.py    # Main hardware check ⭐
│   ├── diagnose_ubuntu_audio.py
│   ├── test_ubuntu_mic.sh
│   └── ...
└── reference/                   # Technical references
    └── QUICK_CONFIG_REFERENCE.md
```

## 🆘 If Something Goes Wrong

### Camera Issues
```bash
# Check devices
ls -la /dev/video*

# Fix permissions
sudo chmod 666 /dev/video0
sudo usermod -a -G video $USER  # Logout/login after

# Test again
python3 test_camera.py
```

### Microphone Issues
```bash
# Quick test
./documentation/troubleshooting/test_ubuntu_mic.sh

# Detailed diagnostics
python3 documentation/troubleshooting/diagnose_ubuntu_audio.py
```

### Ollama Issues
```bash
# Start service
sudo systemctl start ollama
sudo systemctl enable ollama

# Check status
sudo systemctl status ollama

# Test connection
curl http://localhost:11434/api/tags
```

## 🎯 Production Deployment

Once all hardware checks pass:

1. **Enable auto-start**:
   ```bash
   ./documentation/setup/setup_g1_autostart.sh
   ```

2. **Test reboot**:
   ```bash
   sudo reboot
   # Wait for reboot, then:
   sudo systemctl status roboai-astra-vein
   ```

3. **Monitor logs**:
   ```bash
   journalctl -u roboai-astra-vein -f
   ```

---

**You're almost there!** Just test the camera and you'll be ready to deploy! 🚀
