#!/bin/bash
# System-wide hardware configuration for RoboAI agents
# Runs on boot to ensure all audio/video devices are properly configured
# Place in /usr/local/bin/ and call from systemd or rc.local

set -e

LOG_FILE="/var/log/roboai-hardware-setup.log"
LOG_PREFIX="[HW-Setup]"

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') $LOG_PREFIX $1" | tee -a "$LOG_FILE"
}

log "=========================================="
log "Starting RoboAI Hardware Configuration"
log "=========================================="

# ============================================
# 1. USB Audio Devices Detection
# ============================================

log "Detecting USB audio devices..."

# Find USB microphone
USB_MIC=$(arecord -l 2>/dev/null | grep -i "USB.*Sound\|USB PnP" | head -1)
if [ -n "$USB_MIC" ]; then
    MIC_CARD=$(echo "$USB_MIC" | grep -oP "card \K\d+")
    MIC_DEVICE=$(echo "$USB_MIC" | grep -oP "device \K\d+")
    log "✅ USB Microphone detected: card $MIC_CARD, device $MIC_DEVICE"
else
    log "⚠️  No USB microphone detected"
    MIC_CARD=""
fi

# Find USB speaker
USB_SPEAKER=$(aplay -l 2>/dev/null | grep -i "USB.*Device\|USB2.0" | head -1)
if [ -n "$USB_SPEAKER" ]; then
    SPEAKER_CARD=$(echo "$USB_SPEAKER" | grep -oP "card \K\d+")
    SPEAKER_DEVICE=$(echo "$USB_SPEAKER" | grep -oP "device \K\d+")
    log "✅ USB Speaker detected: card $SPEAKER_CARD, device $SPEAKER_DEVICE"
else
    log "⚠️  No USB speaker detected"
    SPEAKER_CARD=""
fi

# ============================================
# 2. Configure ALSA Defaults
# ============================================

log "Configuring ALSA default devices..."

# Create system-wide ALSA config
ALSA_CONF="/etc/asound.conf"

if [ -n "$SPEAKER_CARD" ] && [ -n "$MIC_CARD" ]; then
    cat > "$ALSA_CONF" <<EOF
# RoboAI Auto-Generated ALSA Configuration
# Generated: $(date)

# Default playback device (USB Speaker)
pcm.!default {
    type asym
    playback.pcm {
        type plug
        slave.pcm "hw:${SPEAKER_CARD},${SPEAKER_DEVICE}"
    }
    capture.pcm {
        type plug
        slave.pcm "hw:${MIC_CARD},0"
    }
}

ctl.!default {
    type hw
    card ${SPEAKER_CARD}
}

# Direct access to USB speaker
pcm.usbspeaker {
    type hw
    card ${SPEAKER_CARD}
    device ${SPEAKER_DEVICE}
}

# Direct access to USB microphone
pcm.usbmic {
    type hw
    card ${MIC_CARD}
    device 0
}
EOF
    log "✅ ALSA config written to $ALSA_CONF"
else
    log "⚠️  Skipping ALSA config (devices not detected)"
fi

# ============================================
# 3. Set Speaker Volume and Unmute
# ============================================

if [ -n "$SPEAKER_CARD" ]; then
    log "Configuring speaker volume..."
    
    # Unmute and set volume to 100%
    amixer -c "$SPEAKER_CARD" set Speaker unmute 2>/dev/null || true
    amixer -c "$SPEAKER_CARD" set Speaker 100% 2>/dev/null || true
    amixer -c "$SPEAKER_CARD" set PCM unmute 2>/dev/null || true
    amixer -c "$SPEAKER_CARD" set PCM 100% 2>/dev/null || true
    
    log "✅ Speaker unmuted and volume set to 100%"
fi

# ============================================
# 4. Configure Microphone
# ============================================

if [ -n "$MIC_CARD" ]; then
    log "Configuring microphone..."
    
    # Unmute microphone
    amixer -c "$MIC_CARD" set Mic unmute 2>/dev/null || true
    amixer -c "$MIC_CARD" set Mic 100% 2>/dev/null || true
    amixer -c "$MIC_CARD" set Capture unmute 2>/dev/null || true
    amixer -c "$MIC_CARD" set Capture 80% 2>/dev/null || true
    
    log "✅ Microphone configured"
fi

# ============================================
# 5. Configure PulseAudio (if running)
# ============================================

if pgrep -x pulseaudio > /dev/null; then
    log "Configuring PulseAudio defaults..."
    
    # Wait for PulseAudio to enumerate devices
    sleep 2
    
    # Set USB speaker as default sink
    USB_SINK=$(pactl list sinks short 2>/dev/null | grep -i "usb.*analog" | awk '{print $2}' | head -1)
    if [ -n "$USB_SINK" ]; then
        pactl set-default-sink "$USB_SINK" 2>/dev/null || true
        pactl set-sink-volume "$USB_SINK" 100% 2>/dev/null || true
        log "✅ PulseAudio default sink: $USB_SINK"
    fi
    
    # Set USB microphone as default source
    USB_SOURCE=$(pactl list sources short 2>/dev/null | grep -i "usb.*analog" | awk '{print $2}' | head -1)
    if [ -n "$USB_SOURCE" ]; then
        pactl set-default-source "$USB_SOURCE" 2>/dev/null || true
        pactl set-source-volume "$USB_SOURCE" 80% 2>/dev/null || true
        log "✅ PulseAudio default source: $USB_SOURCE"
    fi
else
    log "ℹ️  PulseAudio not running (using ALSA direct)"
fi

# ============================================
# 6. Configure Camera Permissions
# ============================================

log "Configuring camera permissions..."

# Check for cameras
CAMERAS=$(ls /dev/video* 2>/dev/null | wc -l)
if [ "$CAMERAS" -gt 0 ]; then
    # Set permissions for video devices
    for camera in /dev/video*; do
        if [ -e "$camera" ]; then
            chmod 666 "$camera" 2>/dev/null || true
            log "✅ Camera permissions set: $camera"
        fi
    done
    
    # Add user to video group if not already
    if ! groups unitree | grep -q video; then
        usermod -aG video unitree 2>/dev/null || true
        log "✅ User 'unitree' added to video group"
    fi
else
    log "ℹ️  No cameras detected"
fi

# ============================================
# 7. Create Device Info File
# ============================================

DEVICE_INFO="/etc/roboai-devices.conf"
cat > "$DEVICE_INFO" <<EOF
# RoboAI Device Configuration
# Auto-generated: $(date)

# Audio Devices
SPEAKER_CARD=${SPEAKER_CARD:-none}
SPEAKER_DEVICE=${SPEAKER_DEVICE:-none}
MIC_CARD=${MIC_CARD:-none}
MIC_DEVICE=0

# Camera
CAMERA_COUNT=$CAMERAS
PRIMARY_CAMERA=/dev/video0

# ALSA Playback Device
ALSA_PLAYBACK_DEVICE=plughw:${SPEAKER_CARD:-0},${SPEAKER_DEVICE:-0}

# ALSA Capture Device  
ALSA_CAPTURE_DEVICE=plughw:${MIC_CARD:-0},0
EOF

chmod 644 "$DEVICE_INFO"
log "✅ Device info written to $DEVICE_INFO"

# ============================================
# 8. Verify Configuration
# ============================================

log "Verifying configuration..."

# Test speaker (silent test - just check if command works)
if [ -n "$SPEAKER_CARD" ]; then
    if speaker-test -D plughw:${SPEAKER_CARD},${SPEAKER_DEVICE} -c 2 -t wav -l 1 >/dev/null 2>&1; then
        log "✅ Speaker test passed"
    else
        log "⚠️  Speaker test failed"
    fi
fi

# Check microphone recording capability
if [ -n "$MIC_CARD" ]; then
    if arecord -D plughw:${MIC_CARD},0 -f S16_LE -r 16000 -d 1 /tmp/mic_test.wav >/dev/null 2>&1; then
        log "✅ Microphone test passed"
        rm -f /tmp/mic_test.wav
    else
        log "⚠️  Microphone test failed"
    fi
fi

# ============================================
# 9. Summary
# ============================================

log "=========================================="
log "Hardware Configuration Complete!"
log "=========================================="
log "Speaker:     plughw:${SPEAKER_CARD:-?},${SPEAKER_DEVICE:-?}"
log "Microphone:  plughw:${MIC_CARD:-?},0"
log "Cameras:     $CAMERAS detected"
log "Config file: $DEVICE_INFO"
log "ALSA config: $ALSA_CONF"
log "=========================================="

exit 0
