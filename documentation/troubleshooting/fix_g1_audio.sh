#!/bin/bash

#############################################################################
# G1 Audio Device Diagnostic and Fix Script
# Detects supported sample rates and fixes audio configuration
#############################################################################

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

print_header() {
    echo ""
    print_message "$BLUE" "============================================"
    print_message "$BLUE" "$1"
    print_message "$BLUE" "============================================"
}

# List all audio devices
list_audio_devices() {
    print_header "Available Audio Devices"
    
    print_message "$YELLOW" "Recording devices:"
    arecord -l
    
    echo ""
    print_message "$YELLOW" "Playback devices:"
    aplay -l
}

# Test specific device for supported sample rates
test_device_rates() {
    local device=$1
    print_header "Testing Device: $device"
    
    print_message "$YELLOW" "Checking supported sample rates..."
    
    # Common sample rates to test
    RATES=(8000 11025 16000 22050 32000 44100 48000)
    SUPPORTED_RATES=()
    
    for rate in "${RATES[@]}"; do
        # Try to record 0.1 seconds of audio at this rate
        if timeout 0.5 arecord -D "$device" -f S16_LE -r "$rate" -d 0.1 /tmp/test.wav > /dev/null 2>&1; then
            print_message "$GREEN" "  ✓ $rate Hz supported"
            SUPPORTED_RATES+=("$rate")
        else
            print_message "$RED" "  ✗ $rate Hz not supported"
        fi
    done
    
    if [ ${#SUPPORTED_RATES[@]} -eq 0 ]; then
        print_message "$RED" "No common sample rates supported on $device"
        return 1
    fi
    
    echo ""
    print_message "$GREEN" "Supported sample rates: ${SUPPORTED_RATES[*]}"
    
    # Recommend best rate
    if [[ " ${SUPPORTED_RATES[*]} " =~ " 48000 " ]]; then
        RECOMMENDED_RATE=48000
    elif [[ " ${SUPPORTED_RATES[*]} " =~ " 44100 " ]]; then
        RECOMMENDED_RATE=44100
    elif [[ " ${SUPPORTED_RATES[*]} " =~ " 32000 " ]]; then
        RECOMMENDED_RATE=32000
    elif [[ " ${SUPPORTED_RATES[*]} " =~ " 16000 " ]]; then
        RECOMMENDED_RATE=16000
    else
        RECOMMENDED_RATE=${SUPPORTED_RATES[0]}
    fi
    
    print_message "$BLUE" "Recommended sample rate: $RECOMMENDED_RATE Hz"
    echo "$RECOMMENDED_RATE"
}

# Get hardware parameters
get_hw_params() {
    local device=$1
    print_header "Hardware Parameters for $device"
    
    print_message "$YELLOW" "Getting detailed hardware parameters..."
    arecord --dump-hw-params -D "$device" 2>&1 | head -30
}

# Find G1 microphone device
find_g1_mic() {
    print_header "Detecting G1 Microphone"
    
    # G1 typically uses these device patterns
    DEVICES=("hw:1,1" "hw:1,0" "hw:0,0" "plughw:1,1" "plughw:1,0")
    
    for dev in "${DEVICES[@]}"; do
        print_message "$YELLOW" "Testing $dev..."
        if timeout 0.5 arecord -D "$dev" -f S16_LE -r 48000 -d 0.1 /tmp/test.wav > /dev/null 2>&1; then
            print_message "$GREEN" "✓ Found working device: $dev"
            echo "$dev"
            return 0
        fi
    done
    
    print_message "$RED" "Could not find working microphone device"
    return 1
}

# Test recording
test_recording() {
    local device=$1
    local rate=$2
    
    print_header "Test Recording"
    
    print_message "$YELLOW" "Recording 3 seconds of audio..."
    print_message "$YELLOW" "Device: $device"
    print_message "$YELLOW" "Sample rate: $rate Hz"
    print_message "$YELLOW" "Say something!"
    
    arecord -D "$device" -f S16_LE -r "$rate" -d 3 /tmp/test_recording.wav
    
    if [ $? -eq 0 ]; then
        print_message "$GREEN" "✓ Recording successful!"
        print_message "$YELLOW" "Playing back..."
        aplay /tmp/test_recording.wav
        rm -f /tmp/test_recording.wav
    else
        print_message "$RED" "✗ Recording failed"
    fi
}

# Main diagnostic
run_diagnostics() {
    print_header "G1 Audio Diagnostics"
    
    # 1. List devices
    list_audio_devices
    
    # 2. Find G1 mic
    echo ""
    DEVICE=$(find_g1_mic)
    
    if [ -z "$DEVICE" ]; then
        print_message "$RED" "Failed to detect G1 microphone"
        print_message "$YELLOW" "Please check:"
        echo "  1. Is the microphone connected?"
        echo "  2. Run 'arecord -l' to see available devices"
        echo "  3. Try manually specifying device with: $0 test hw:X,Y"
        exit 1
    fi
    
    # 3. Get hardware parameters
    echo ""
    get_hw_params "$DEVICE"
    
    # 4. Test sample rates
    echo ""
    RATE=$(test_device_rates "$DEVICE")
    
    # 5. Show recommended config
    echo ""
    print_header "Recommended Configuration"
    
    print_message "$YELLOW" "Update your config/astra_vein_receptionist.json5:"
    echo ""
    cat << EOF
{
  "type": "LocalASRInput",
  "config": {
    "engine": "faster-whisper",
    "model_size": "tiny.en",
    "device": "cpu",
    "compute_type": "int8",
    "sample_rate": $RATE,  // Changed from 16000
    "input_device": null,   // or specify: "$DEVICE"
    // ... rest of config
  }
}
EOF
    
    echo ""
    print_message "$GREEN" "After updating config, test with:"
    echo "  uv run src/run.py astra_vein_receptionist"
}

# Quick test function
quick_test() {
    local device=${1:-"hw:1,1"}
    local rate=${2:-48000}
    
    print_message "$BLUE" "Quick test: Device $device at $rate Hz"
    test_recording "$device" "$rate"
}

# Main menu
case "${1:-diagnose}" in
    diagnose)
        run_diagnostics
        ;;
    test)
        quick_test "$2" "$3"
        ;;
    list)
        list_audio_devices
        ;;
    *)
        print_message "$YELLOW" "Usage:"
        echo "  $0                  # Run full diagnostics"
        echo "  $0 diagnose        # Run full diagnostics"
        echo "  $0 test hw:1,1 48000  # Test specific device and rate"
        echo "  $0 list            # List audio devices"
        ;;
esac
