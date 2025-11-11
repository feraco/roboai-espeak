#!/bin/bash
# Pre-start checks for Lex Agent
# Validates audio devices, camera, Ollama, and waits for hardware to be ready

set -e

LOG_PREFIX="[LexPreStart]"
MAX_WAIT=60  # Maximum seconds to wait for devices

log_info() {
    echo "$LOG_PREFIX INFO: $1"
    logger -t lex-agent "$1"
}

log_error() {
    echo "$LOG_PREFIX ERROR: $1" >&2
    logger -t lex-agent "ERROR: $1"
}

log_success() {
    echo "$LOG_PREFIX ✅ $1"
    logger -t lex-agent "SUCCESS: $1"
}

# Function: Wait for USB microphone
wait_for_microphone() {
    log_info "Waiting for USB microphone..."
    local elapsed=0
    
    while [ $elapsed -lt $MAX_WAIT ]; do
        # Check if USB PnP Sound Device exists
        if arecord -l 2>/dev/null | grep -iq "USB.*Sound\|USB PnP"; then
            local device_info=$(arecord -l | grep -i "USB.*Sound\|USB PnP" | head -1)
            log_success "USB microphone detected: $device_info"
            return 0
        fi
        
        sleep 2
        elapsed=$((elapsed + 2))
        log_info "Still waiting for microphone... ($elapsed/${MAX_WAIT}s)"
    done
    
    log_error "USB microphone not detected after ${MAX_WAIT}s"
    return 1
}

# Function: Wait for USB speaker (ALSA direct - no PulseAudio required)
wait_for_speaker() {
    log_info "Waiting for USB speaker..."
    local elapsed=0
    
    while [ $elapsed -lt $MAX_WAIT ]; do
        # Check if USB speaker exists (ALSA)
        if aplay -l 2>/dev/null | grep -iq "USB.*Device\|USB2.0"; then
            local device_info=$(aplay -l | grep -i "USB.*Device\|USB2.0" | head -1)
            log_success "USB speaker detected: $device_info"
            
            # Extract card number
            local card_num=$(echo "$device_info" | grep -oP "card \K\d+")
            
            # Unmute and set volume using ALSA
            if [ -n "$card_num" ]; then
                amixer -c $card_num set Speaker unmute 2>/dev/null || true
                amixer -c $card_num set Speaker 100% 2>/dev/null || true
                log_success "Speaker unmuted and volume set to 100% (card $card_num)"
            fi
            
            return 0
        fi
        
        sleep 2
        elapsed=$((elapsed + 2))
        log_info "Still waiting for speaker... ($elapsed/${MAX_WAIT}s)"
    done
    
    log_error "USB speaker not detected after ${MAX_WAIT}s"
    return 1
}

# Function: Wait for camera (badge reader)
wait_for_camera() {
    log_info "Waiting for camera (badge reader)..."
    local elapsed=0
    
    while [ $elapsed -lt $MAX_WAIT ]; do
        # Check if /dev/video0 exists
        if [ -e /dev/video0 ]; then
            log_success "Camera detected: /dev/video0"
            
            # Check if camera is accessible
            if v4l2-ctl --device=/dev/video0 --all &>/dev/null; then
                log_success "Camera is accessible and working"
            else
                log_info "Camera detected but not fully ready yet"
            fi
            
            return 0
        fi
        
        sleep 2
        elapsed=$((elapsed + 2))
        log_info "Still waiting for camera... ($elapsed/${MAX_WAIT}s)"
    done
    
    log_error "Camera not detected after ${MAX_WAIT}s (badge reader may not work)"
    # Don't fail - badge reader is optional
    return 0
}

# Function: Verify Ollama is responsive
check_ollama() {
    log_info "Checking Ollama service..."
    
    # Check if service is running
    if ! systemctl is-active --quiet ollama; then
        log_info "Ollama service not running, starting..."
        sudo systemctl start ollama
        sleep 5
    fi
    
    log_success "Ollama service is running"
    
    # Wait for Ollama to be responsive
    local elapsed=0
    local max_ollama_wait=30
    
    while [ $elapsed -lt $max_ollama_wait ]; do
        if curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
            log_success "Ollama is responsive"
            
            # Check if llama3.1:8b model exists
            if curl -s http://localhost:11434/api/tags | grep -q "llama3.1:8b"; then
                log_success "Model llama3.1:8b is available"
            else
                log_error "Model llama3.1:8b not found! Run: ollama pull llama3.1:8b"
                return 1
            fi
            
            return 0
        fi
        
        sleep 2
        elapsed=$((elapsed + 2))
        log_info "Waiting for Ollama to respond... ($elapsed/${max_ollama_wait}s)"
    done
    
    log_error "Ollama not responding after ${max_ollama_wait}s"
    return 1
}

# Function: Check Piper TTS installation
check_piper() {
    log_info "Checking Piper TTS..."
    
    if ! command -v piper &> /dev/null; then
        log_error "Piper TTS not found in PATH"
        return 1
    fi
    
    log_success "Piper TTS is installed"
    
    # Check for Ryan voice model
    local voice_found=false
    for voice_dir in ~/piper_voices ./piper-voices ./piper_voices /usr/local/share/piper/voices ~/.local/share/piper/voices; do
        if [ -f "$voice_dir/en_US-ryan-medium.onnx" ]; then
            log_success "Found Ryan voice model in $voice_dir"
            voice_found=true
            break
        fi
    done
    
    if [ "$voice_found" = false ]; then
        log_error "Ryan voice model (en_US-ryan-medium.onnx) not found"
        return 1
    fi
    
    return 0
}

# Function: Check Python dependencies
check_python_deps() {
    log_info "Checking Python environment..."
    
    if ! command -v uv &> /dev/null; then
        log_error "UV package manager not found"
        return 1
    fi
    
    log_success "UV package manager is available"
    
    # Check if pytesseract is available (for badge reader)
    if python3 -c "import pytesseract" 2>/dev/null; then
        log_success "pytesseract is installed (badge reader ready)"
    else
        log_info "pytesseract not found (badge reader may not work)"
    fi
    
    return 0
}

# Main execution
main() {
    log_info "========================================"
    log_info "Starting Lex Agent Pre-Start Checks"
    log_info "========================================"
    
    # Run all checks
    wait_for_microphone || log_error "Microphone check failed (continuing anyway)"
    wait_for_speaker || log_error "Speaker check failed (continuing anyway)"
    wait_for_camera || log_info "Camera optional - continuing"
    check_ollama || { log_error "Ollama check FAILED - agent cannot start"; exit 1; }
    check_piper || { log_error "Piper TTS check FAILED - agent cannot start"; exit 1; }
    check_python_deps || { log_error "Python dependencies check FAILED"; exit 1; }
    
    log_info "========================================"
    log_success "All critical checks passed!"
    log_info "Starting Lex Agent..."
    log_info "========================================"
    
    exit 0
}

# Run main
main
