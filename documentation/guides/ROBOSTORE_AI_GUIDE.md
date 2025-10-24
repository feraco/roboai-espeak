# 🤖 Robostore AI - Super Simple Guide

## What is Robostore AI?

Robostore AI is a **super simple web control panel** for your G1 robot agent. You don't need to know anything about computers or programming - just connect your phone to the G1's WiFi and use big buttons to control everything!

## 🎯 What Can You Do?

With Robostore AI, you can:

1. **Turn the agent ON or OFF** with one button
2. **Switch between different personalities** (receptionist, greeter, security, etc.)
3. **Restart the agent** if something goes wrong
4. **See the status** - is it running or stopped?

**No typing required!** Everything is done with buttons and dropdowns.

---

## 📱 Step-by-Step: How to Use It

### Step 1: Connect to G1's WiFi

1. On your phone, go to **WiFi settings**
2. Look for a network named: **`G1-Receptionist`**
3. Tap it and enter password: **`astra2024`**
4. Wait until connected (you'll see the WiFi icon on your phone)

### Step 2: Open the Control Panel

1. Open any web browser on your phone (Safari, Chrome, etc.)
2. Type this address in the URL bar:
   ```
   http://10.42.0.1:8080
   ```
3. Press GO

### Step 3: Use the Control Panel

You'll see a purple and white screen with big buttons:

#### 🟢 **Agent Status** (Top Box)
- Shows if agent is **Running** (green) or **Stopped** (red)
- Shows which personality is currently active

#### ▶️ **Power Controls**
- **START** button (green) - Turn on the agent
- **STOP** button (red) - Turn off the agent
- **RESTART** button (yellow) - Restart if it's acting weird

#### 🔄 **Change Configuration**
1. Tap the dropdown menu
2. Pick a personality (like "Astra Vein Receptionist" or "Greeter")
3. Tap the **"Apply & Restart"** button
4. Wait 5-10 seconds - done!

---

## 📸 What You'll See

```
┌─────────────────────────────────────┐
│     🤖 Robostore AI                 │
│     Control Panel for G1 Agent      │
├─────────────────────────────────────┤
│  Agent Status: 🟢 Running           │
│  Current Config: Astra Vein         │
├─────────────────────────────────────┤
│  Power Controls                     │
│  [▶ Start]  [⏹ Stop]               │
│  [🔄 Restart Agent]                 │
├─────────────────────────────────────┤
│  Change Configuration               │
│  [Dropdown: Select config...]       │
│  [✓ Apply & Restart]                │
└─────────────────────────────────────┘
```

---

## 🆘 Troubleshooting (If Something Goes Wrong)

### Problem: Can't connect to WiFi
**Solution:**
- Make sure G1 hotspot is running (see hotspot guide)
- Try forgetting the network and reconnecting
- Check password is exactly: `astra2024` (lowercase)

### Problem: Can't open the web page
**Solution:**
- Make sure you're connected to `G1-Receptionist` WiFi
- Try typing the address again: `http://10.42.0.1:8080`
- Make sure you typed `http://` not `https://`

### Problem: Buttons don't work
**Solution:**
- Wait 5 seconds and try again
- Check if you have internet connection showing (even though we're offline, phone might show "no internet")
- Try refreshing the page (pull down on iPhone, or tap reload button)

### Problem: Agent won't start
**Solution:**
- Tap the **RESTART** button and wait 10 seconds
- If still not working, the G1 might need to be restarted (ask someone technical)

---

## 🎨 Available Configurations (Personalities)

When you tap the dropdown, you'll see options like:

- **Astra Vein Receptionist** - Friendly medical office assistant with vision
- **Greeter** - Welcomes visitors
- **Security** - Watches and reports activities
- **Conversation** - General chat buddy
- **Local Agent** - Basic offline agent

Each one makes the robot act differently!

---

## ⚠️ Important Notes

### ✅ Do This:
- Connect to G1 WiFi before opening the web page
- Wait a few seconds after pressing buttons
- If you change config, wait for "Success" message

### ❌ Don't Do This:
- Don't press buttons multiple times quickly
- Don't close the page right after pressing a button
- Don't try to access from regular WiFi (must be on G1 hotspot)

---

## 🔧 Installation (For Setup Person)

If you're setting this up for the first time on G1:

### 1. Transfer Files to G1
```bash
# Copy everything to G1
scp -r robostore_ai setup_robostore_ai.sh robostore-ai.service username@g1-ip:~
```

### 2. Run Installation Script
```bash
# SSH into G1
ssh username@g1-ip

# Run the installer (just once!)
sudo ./setup_robostore_ai.sh
```

### 3. Done!
The installer will:
- Install all needed software automatically
- Set up the web server to start on boot
- Test that everything works

---

## 📞 Quick Reference Card

**Print this out and tape it near the G1:**

```
┌──────────────────────────────────────────┐
│       🤖 ROBOSTORE AI QUICK GUIDE        │
├──────────────────────────────────────────┤
│ 1. Connect Phone to WiFi:                │
│    Network: G1-Receptionist               │
│    Password: astra2024                    │
│                                           │
│ 2. Open Browser, Go To:                  │
│    http://10.42.0.1:8080                 │
│                                           │
│ 3. Use Big Buttons:                      │
│    • START - Turn on robot                │
│    • STOP - Turn off robot                │
│    • RESTART - Fix if broken              │
│    • Dropdown - Change personality        │
│                                           │
│ Problems? Try RESTART button first!       │
└──────────────────────────────────────────┘
```

---

## 🔐 Security Notes

- **Password Protected WiFi:** Only people with the password can connect
- **Local Network Only:** The control panel only works when connected to G1's hotspot
- **No Internet Needed:** Everything works offline
- **Safe Changes:** The system validates changes before applying them

---

## 💡 Pro Tips

1. **Bookmark the page** on your phone for quick access
2. **Add to Home Screen** (iPhone: Share → Add to Home Screen)
3. **Check status first** before making changes
4. **One change at a time** - don't rush
5. **Wait for green "Success" message** before closing page

---

## 🚀 Advanced (For Technical Users)

### Check if Robostore AI is Running
```bash
systemctl status robostore-ai.service
```

### View Live Logs
```bash
sudo journalctl -u robostore-ai.service -f
```

### Restart Web Server
```bash
sudo systemctl restart robostore-ai.service
```

### Manual Start/Stop
```bash
# Start
sudo systemctl start robostore-ai.service

# Stop
sudo systemctl stop robostore-ai.service
```

---

## ❓ FAQ

**Q: Do I need internet?**  
A: No! Everything works offline on the hotspot.

**Q: Can multiple phones connect?**  
A: Yes! Multiple people can use the control panel at the same time.

**Q: What happens if I pick the wrong config?**  
A: No problem! Just pick a different one and press "Apply & Restart"

**Q: Can I break the robot with this?**  
A: No. You can only switch between pre-configured safe settings.

**Q: How long does it take to switch configs?**  
A: About 5-10 seconds. Wait for the green "Success!" message.

**Q: Why does it say "no internet" on my phone?**  
A: That's normal! You're on a local network (hotspot) without internet. The control panel will still work fine.

---

## 📞 Need Help?

If something isn't working:

1. **Try the RESTART button** first
2. **Reconnect to WiFi**
3. **Refresh the web page**
4. **Check the troubleshooting section above**
5. **Ask the technical person who set this up**

---

**Made with ❤️ for simple, easy robot control**  
**Version 1.0 | Offline Edition**
