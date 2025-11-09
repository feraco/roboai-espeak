#!/bin/bash

# Lex Channel Chief - Pre-Start Hardware & Service Checks
# This script validates all requirements before starting the agent

set -e

LOG_PREFIX="[Lex PreStart]"
TIMEOUT=60  # seconds to wait for hardware
RETRY_INTERVAL=2

echo "$LOG_PREFIX Starting pre-start checks for Lex Channel Chief..."

# Function to wait for USB microphone
wait_for_microphone() {
    echo "$LOG_PREFIX Waiting for USB microphone (timeout: ${TIMEOUT}s)..."
    local elapsed=0
    
    while [ $elapsed -lt $TIMEOUT ]; do
        # Search for USB audio input device
        if arecord -l 2>/dev/null | grep -q "USB" || pactl list sources 2>/dev/null | grep -q "usb"; then
            echo "$LOG_PREFIX ✅ USB microphone detected"
            return 0
        fi
        
        sleep $RETRY_INTERVAL
        elapsed=$((elapsed + RETRY_INTERVAL))
        echo "$LOG_PREFIX Waiting for microphone... (${elapsed}s/${TIMEOUT}s)"
    done
    
    echo "$LOG_PREFIX ⚠️  WARNING: USB microphone not detected after ${TIMEOUT}s"
    echo "$LOG_PREFIX Continuing anyway - agent may use default device"
    return 0
}

# Function to wait for USB speaker/output
wait_for_speaker() {
    echo "$LOG_PREFIX Waiting for USB speaker (timeout: ${TIMEOUT}s)..."
    local elapsed=0
    
    while [ $elapsed -lt $TIMEOUT ]; do
        # Search for USB audio output device
        if aplay -l 2>/dev/null | grep -q "USB" || pactl list sinks 2>/dev/null | grep -q "usb"; then
            echo "$LOG_PREFIX ✅ USB speaker detected"
            
            # Try to set as default in PulseAudio
            if command -v pactl &> /dev/null; then
                local usb_sink=$(pactl list short sinks | grep -i usb | head -n1 | awk '{print $2}')
                if [ -n "$usb_sink" ]; then
                    pactl set-default-sink "$usb_sink" 2>/dev/null || true
                    echo "$LOG_PREFIX ✅ Set USB speaker as default output"
                fi
            fi
            
            return 0
        fi
        
        sleep $RETRY_INTERVAL
        elapsed=$((elapsed + RETRY_INTERVAL))
        echo "$LOG_PREFIX Waiting for speaker... (${elapsed}s/${TIMEOUT}s)"
    done
    
    echo "$LOG_PREFIX ⚠️  WARNING: USB speaker not detected after ${TIMEOUT}s"
    echo "$LOG_PREFIX Continuing anyway - agent may use default device"
    return 0
}

# Function to check Ollama service
check_ollama() {
    echo "$LOG_PREFIX Checking Ollama service..."
    
    # Check if systemd service exists and is active
    if systemctl is-active --quiet ollama 2>/dev/null; then
        echo "$LOG_PREFIX ✅ Ollama service is running"
    else
        echo "$LOG_PREFIX ⚠️  Ollama service not running via systemd"
        
        # Try to check if Ollama is responding via HTTP
        if curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
            echo "$LOG_PREFIX ✅ Ollama is responding on port 11434"
        else
            echo "$LOG_PREFIX ❌ ERROR: Ollama is not responding!"
            echo "$LOG_PREFIX Attempting to start Ollama..."
            
            # Try to restart systemd service
            if systemctl status ollama >/dev/null 2>&1; then
                sudo systemctl restart ollama
                sleep 5
            fi
            
            # Check again
            if curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
                echo "$LOG_PREFIX ✅ Ollama started successfully"
            else
                echo "$LOG_PREFIX ❌ FATAL: Cannot start Ollama!"
                return 1
            fi
        fi
    fi
    
    return 0
}

# Function to validate Ollama model
check_ollama_model() {
    echo "$LOG_PREFIX Validating Ollama model (llama3.1:8b)..."
    
    # Test if model responds
    local test_response=$(curl -s -X POST http://localhost:11434/api/generate -d '{
        "model": "llama3.1:8b",
        "prompt": "Reply with OK only",
        "stream": false
    }' 2>/dev/null)
    
    if echo "$test_response" | grep -q "response"; then
        echo "$LOG_PREFIX ✅ Model llama3.1:8b responds correctly"
        return 0
    else
        echo "$LOG_PREFIX ❌ ERROR: Model llama3.1:8b not responding!"
        echo "$LOG_PREFIX Please run: ollama pull llama3.1:8b"
        return 1
    fi
}

# Function to reset PulseAudio if needed
reset_pulseaudio() {
    if command -v pulseaudio &> /dev/null; then
        echo "$LOG_PREFIX Resetting PulseAudio..."
        pulseaudio -k 2>/dev/null || true
        sleep 2
        pulseaudio --start 2>/dev/null || true
        sleep 2
        echo "$LOG_PREFIX ✅ PulseAudio reset complete"
    fi
}

# Main execution
echo "$LOG_PREFIX ================================================"
echo "$LOG_PREFIX Lex Channel Chief - Pre-Start Checks"
echo "$LOG_PREFIX ================================================"

# Run all checks
wait_for_microphone
wait_for_speaker
check_ollama || exit 1
check_ollama_model || exit 1

echo "$LOG_PREFIX ================================================"
echo "$LOG_PREFIX ✅ All pre-start checks completed!"
echo "$LOG_PREFIX Starting Lex Channel Chief agent..."
echo "$LOG_PREFIX ================================================"

exit 0
