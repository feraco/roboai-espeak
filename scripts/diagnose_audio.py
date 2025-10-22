#!/usr/bin/env python3
"""
Diagnostic tool for troubleshooting voice and audio issues in the RoboAI project.
Run this script to verify TTS setup and audio output.
"""

import asyncio
import sys
import os
import subprocess
from pathlib import Path

def check_piper_setup():
    """Check Piper TTS installation and test audio output."""
    print("\n🔈 Testing Piper TTS setup...")
    
    # Check if piper-voices directory exists
    if not os.path.exists("piper-voices"):
        print("❌ piper-voices directory not found")
        print("Try: git clone https://huggingface.co/rhasspy/piper-voices")
        return False
    
    # Check for ryan-medium model
    model_path = "piper-voices/en/en_US/ryan/medium/en_US-ryan-medium.onnx"
    if not os.path.exists(model_path):
        print("❌ ryan-medium model not found")
        print("Try: downloading from https://huggingface.co/rhasspy/piper-voices")
        return False
    
    # Test Piper audio output
    print("Testing Piper audio output...")
    try:
        test_output = "test_piper_audio.wav"
        subprocess.run(
            ["piper", "--model", "en_US-ryan-medium", "--output_file", test_output, "--text", "Testing Piper TTS output"],
            check=True
        )
        
        # Play the generated audio
        if sys.platform == "darwin":
            subprocess.run(["afplay", test_output], check=True)
        else:
            subprocess.run(["aplay", test_output], check=True)
            
        # Clean up test file
        os.remove(test_output)
        print("✅ Piper TTS test completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Piper TTS test failed: {e}")
        print("Try: uv pip install piper-tts")
        return False
    except Exception as e:
        print(f"❌ Error during Piper test: {e}")
        return False

def check_ollama():
    """Verify Ollama installation and model."""
    print("\n🤖 Checking Ollama setup...")
    
    try:
        # Check if Ollama is running
        subprocess.run(["curl", "-s", "http://localhost:11434/api/tags"], 
                     check=True, capture_output=True)
        print("✅ Ollama service is running")
    except subprocess.CalledProcessError:
        print("❌ Ollama service is not running")
        print("Try: ollama serve")
        return False

    # Check for required model
    try:
        result = subprocess.run(["ollama", "list"], 
                              check=True, capture_output=True, text=True)
        if "gemma2:2b" in result.stdout:
            print("✅ gemma2:2b model is installed")
        else:
            print("❌ gemma2:2b model not found")
            print("Try: ollama pull gemma2:2b")
    except subprocess.CalledProcessError:
        print("❌ Failed to check Ollama models")
        return False
    
    return True

def check_microphone():
    """Test microphone input."""
    print("\n🎤 Testing microphone...")
    
    if sys.platform == "darwin":  # macOS
        print("On macOS:")
        print("1. Check System Settings → Privacy & Security → Microphone")
        print("2. Check System Settings → Sound → Input")
    else:  # Linux
        try:
            # Record 3 seconds of audio
            print("Recording 3 seconds of audio...")
            subprocess.run(["arecord", "-d", "3", "/tmp/test.wav"], check=True)
            print("Playing back recorded audio...")
            subprocess.run(["aplay", "/tmp/test.wav"], check=True)
            print("✅ Microphone test completed")
            
            # Cleanup
            os.remove("/tmp/test.wav")
        except subprocess.CalledProcessError:
            print("❌ Microphone test failed")
            print("Try: sudo apt-get install alsa-utils")
            print("     sudo usermod -a -G audio $USER")

def check_python_packages():
    """Verify required Python packages."""
    print("\n📦 Checking Python packages...")
    
    required_packages = [
        "faster-whisper",
        "numpy",
        "sounddevice",
        "json5",
        "piper-tts"
    ]
    
    import importlib.metadata
    for package in required_packages:
        try:
            importlib.metadata.version(package)
            print(f"✅ {package} is installed")
        except importlib.metadata.PackageNotFoundError:
            print(f"❌ {package} is missing")
            print(f"Try: uv pip install {package}")

def check_config_file():
    """Verify funny_robot.json5 configuration."""
    print("\n📄 Checking configuration file...")
    
    config_path = Path("config/funny_robot.json5")
    if not config_path.exists():
        print("❌ funny_robot.json5 not found")
        return
    
    try:
        import json5
        with open(config_path) as f:
            config = json5.load(f)
        
        # Check essential configuration
        llm_config = config.get("cortex_llm", {})
        llm_type = llm_config.get("type")
        llm_model = llm_config.get("config", {}).get("model")
        
        checks = {
            "cortex_llm": {
                "status": llm_type == "OllamaLLM",
                "message": f"LLM type is {llm_type}, expected OllamaLLM"
            },
            "llm_model": {
                "status": llm_model in ["gemma2:2b", "llama3:latest"],
                "message": f"Model is {llm_model}, supported: gemma2:2b, llama3:latest"
            },
            "asr": {
                "status": any(input.get("type") == "LocalASRInput" for input in config.get("agent_inputs", [])),
                "message": "LocalASRInput not found in agent_inputs"
            },
            "tts": {
                "status": any(action.get("name") == "speak" for action in config.get("agent_actions", [])),
                "message": "speak action not found in agent_actions"
            }
        }
        
        for check, info in checks.items():
            status = "✅" if info["status"] else "❌"
            print(f"{status} {check}: {info['message'] if not info['status'] else 'OK'}")
            
    except Exception as e:
        print(f"❌ Error reading configuration: {e}")

def main():
    """Run all diagnostic checks."""
    print("🔍 Starting RoboAI Audio Diagnostic Tool")
    print("========================================")
    
    check_piper_setup()
    check_ollama()
    check_microphone()
    check_python_packages()
    check_config_file()
    
    print("\n📋 Diagnostic Summary")
    print("If any tests failed, check the suggested fixes above.")
    print("For more help, visit: https://github.com/feraco/roboai-espeak")

if __name__ == "__main__":
    main()