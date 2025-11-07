#!/bin/bash
# Pre-start checks for Astra Agent
# Validates audio devices, Ollama, and waits for hardware to be ready

set -e

LOG_PREFIX="[PreStart]"
MAX_WAIT=60  # Maximum seconds to wait for devices

log_info() {
    echo "$LOG_PREFIX INFO: $1"
    logger -t astra-agent "$1"
}

log_error() {
    echo "$LOG_PREFIX ERROR: $1" >&2
    logger -t astra-agent "ERROR: $1"
}

log_success() {
    echo "$LOG_PREFIX ✅ $1"
    logger -t astra-agent "SUCCESS: $1"
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

# Function: Wait for USB speaker and set as default
wait_for_speaker() {
    log_info "Waiting for USB speaker..."
    local elapsed=0
    
    # Ensure PulseAudio is running
    if ! pgrep -x pulseaudio > /dev/null; then
        log_info "Starting PulseAudio..."
        pulseaudio -D
        sleep 3
    fi
    
    while [ $elapsed -lt $MAX_WAIT ]; do
        # Check if USB speaker exists
        if aplay -l 2>/dev/null | grep -iq "USB.*Device\|USB2.0"; then
            local device_info=$(aplay -l | grep -i "USB.*Device\|USB2.0" | head -1)
            log_success "USB speaker detected: $device_info"
            
            # Set USB speaker as default in PulseAudio
            sleep 2  # Give PulseAudio time to enumerate devices
            local usb_sink=$(pactl list sinks short 2>/dev/null | grep -i "usb.*analog" | awk '{print $2}' | head -1)
            
            if [ -n "$usb_sink" ]; then
                pactl set-default-sink "$usb_sink" 2>/dev/null || true
                log_success "Set default audio output to: $usb_sink"
            else
                log_info "PulseAudio sink not ready yet, will use ALSA fallback"
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
    
    # Test if Ollama is responsive
    log_info "Testing Ollama responsiveness..."
    local max_attempts=3
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if timeout 15 ollama list > /dev/null 2>&1; then
            log_success "Ollama is responsive"
            return 0
        fi
        
        log_info "Ollama not responding, attempt $attempt/$max_attempts"
        
        if [ $attempt -eq $max_attempts ]; then
            log_error "Ollama not responding after $max_attempts attempts"
            log_info "Attempting Ollama restart and cache clear..."
            
            # Stop Ollama
            sudo systemctl stop ollama
            sleep 2
            
            # Clear cache (optional - only if corrupted)
            # Uncomment if you want automatic cache clearing:
            # log_info "Clearing Ollama cache..."
            # rm -rf ~/.ollama/models/manifests/registry.ollama.ai/library/llama3.1/* 2>/dev/null || true
            
            # Restart Ollama
            sudo systemctl start ollama
            sleep 10
            
            # Test again
            if timeout 15 ollama list > /dev/null 2>&1; then
                log_success "Ollama is now responsive after restart"
                return 0
            else
                log_error "Ollama still not responding after restart"
                return 1
            fi
        fi
        
        sleep 5
        attempt=$((attempt + 1))
    done
}

# Function: Verify Ollama model exists and responds
check_ollama_model() {
    local model="${1:-llama3.1:8b}"
    log_info "Checking if model '$model' exists..."
    
    if ! ollama list | grep -q "$model"; then
        log_error "Model '$model' not found"
        log_info "Available models:"
        ollama list
        return 1
    fi
    
    log_success "Model '$model' is available"
    
    # Test model inference
    log_info "Testing model inference..."
    if echo "Reply OK" | timeout 20 ollama run "$model" > /dev/null 2>&1; then
        log_success "Model '$model' responds correctly"
        return 0
    else
        log_error "Model '$model' does not respond to test prompt"
        return 1
    fi
}

# Function: Reset PulseAudio if needed
reset_pulseaudio() {
    log_info "Resetting PulseAudio..."
    
    # Kill PulseAudio
    pkill -9 pulseaudio 2>/dev/null || true
    sleep 2
    
    # Start fresh
    pulseaudio -D
    sleep 3
    
    if pgrep -x pulseaudio > /dev/null; then
        log_success "PulseAudio restarted successfully"
        return 0
    else
        log_error "Failed to restart PulseAudio"
        return 1
    fi
}

# Main execution
main() {
    log_info "=========================================="
    log_info "Starting pre-start hardware checks..."
    log_info "=========================================="
    
    # Step 1: Check and wait for microphone
    if ! wait_for_microphone; then
        log_error "Microphone check failed - continuing anyway (will use validation skip)"
    fi
    
    # Step 2: Check and wait for speaker
    if ! wait_for_speaker; then
        log_error "Speaker check failed - attempting PulseAudio reset"
        reset_pulseaudio
        sleep 2
        wait_for_speaker || log_error "Speaker still not detected - continuing anyway"
    fi
    
    # Step 3: Check Ollama service
    if ! check_ollama; then
        log_error "Ollama service check failed - agent may not start properly"
        exit 1
    fi
    
    # Step 4: Check Ollama model
    if ! check_ollama_model "llama3.1:8b"; then
        log_error "Ollama model check failed - agent may not respond to queries"
        exit 1
    fi
    
    log_info "=========================================="
    log_success "All pre-start checks completed!"
    log_info "=========================================="
    
    # Final device summary
    log_info "=== Audio Devices Summary ==="
    log_info "Microphones:"
    arecord -l 2>/dev/null | grep -i "card\|usb" || echo "  No devices found"
    
    log_info "Speakers:"
    aplay -l 2>/dev/null | grep -i "card\|usb" || echo "  No devices found"
    
    log_info "PulseAudio default sink:"
    pactl get-default-sink 2>/dev/null || echo "  Not available"
    
    log_info "=== Ollama Status ==="
    log_info "Service: $(systemctl is-active ollama)"
    log_info "Available models:"
    ollama list | head -5
    
    exit 0
}

# Run main function
main "$@"
