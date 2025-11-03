#!/usr/bin/env python3
"""
Ollama Diagnostic Script for Jetson
Troubleshoot "no output from llm ollama" issues
"""

import subprocess
import json
import requests
import time
import sys
from pathlib import Path

def run_command(cmd, timeout=30):
    """Run a command and return output, handling timeouts"""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=timeout
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", f"Command timed out after {timeout} seconds"

def check_ollama_service():
    """Check Ollama systemd service status"""
    print("🔍 Checking Ollama Service Status...")
    code, out, err = run_command("systemctl status ollama --no-pager")
    if "active (running)" in out:
        print("✅ Ollama service is running")
    else:
        print("❌ Ollama service issue detected")
        print(f"Output: {out}")
        return False
    return True

def check_ollama_connectivity():
    """Test direct connection to Ollama API"""
    print("\n🌐 Testing Ollama API Connectivity...")
    try:
        response = requests.get("http://localhost:11434/api/version", timeout=10)
        if response.status_code == 200:
            version_info = response.json()
            print(f"✅ Ollama API responding: {version_info}")
            return True
        else:
            print(f"❌ Ollama API returned status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to Ollama API: {e}")
        return False

def list_ollama_models():
    """List available models in Ollama"""
    print("\n📋 Checking Available Models...")
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=10)
        if response.status_code == 200:
            models = response.json()
            if models.get('models'):
                print("✅ Available models:")
                for model in models['models']:
                    print(f"  - {model['name']} (Size: {model.get('size', 'unknown')})")
                return models['models']
            else:
                print("⚠️  No models found! Need to pull models first.")
                return []
        else:
            print(f"❌ Failed to list models: {response.status_code}")
            return []
    except requests.exceptions.RequestException as e:
        print(f"❌ Error listing models: {e}")
        return []

def test_model_generation(model_name="llama3.1:8b"):
    """Test model generation with simple prompt"""
    print(f"\n🧠 Testing Model Generation: {model_name}")
    try:
        payload = {
            "model": model_name,
            "prompt": "Say 'Hello from Jetson!'",
            "stream": False,
            "options": {
                "temperature": 0.1,
                "num_predict": 10
            }
        }
        
        print(f"Sending request to Ollama...")
        response = requests.post(
            "http://localhost:11434/api/generate", 
            json=payload, 
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('response'):
                print(f"✅ Model working! Response: {result['response']}")
                return True
            else:
                print(f"⚠️  Empty response from model: {result}")
                return False
        else:
            print(f"❌ Generation failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Model generation timed out (60s)")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Generation request failed: {e}")
        return False

def check_system_resources():
    """Check system resources that might affect Ollama"""
    print("\n💾 Checking System Resources...")
    
    # Check memory
    code, out, err = run_command("free -h")
    if code == 0:
        print("Memory Status:")
        print(out)
    
    # Check disk space
    code, out, err = run_command("df -h /usr/share/ollama")
    if code == 0:
        print("Ollama Storage:")
        print(out)
    
    # Check GPU memory if available
    code, out, err = run_command("nvidia-smi")
    if code == 0:
        print("GPU Status:")
        print(out)

def check_ollama_logs():
    """Check recent Ollama service logs for errors"""
    print("\n📜 Recent Ollama Logs (last 20 lines)...")
    code, out, err = run_command("journalctl -u ollama -n 20 --no-pager")
    if code == 0:
        print(out)
    else:
        print(f"Could not fetch logs: {err}")

def suggest_fixes():
    """Provide suggested fixes based on common issues"""
    print("\n🔧 Suggested Fixes:")
    print("1. Restart Ollama service:")
    print("   sudo systemctl restart ollama")
    print()
    print("2. Pull models if missing:")
    print("   ollama pull llama3.1:8b")
    print("   ollama pull llava-llama3")
    print()
    print("3. Clear model cache if corrupted:")
    print("   sudo rm -rf /usr/share/ollama/.ollama/models/*")
    print("   ollama pull llama3.1:8b")
    print()
    print("4. Check Ollama configuration:")
    print("   sudo systemctl edit ollama")
    print("   Add: Environment=OLLAMA_MAX_LOADED_MODELS=1")
    print()
    print("5. Monitor logs while testing:")
    print("   sudo journalctl -u ollama -f")

def main():
    """Run complete Ollama diagnostics"""
    print("🚀 Ollama Diagnostics for Jetson")
    print("=" * 50)
    
    all_checks_passed = True
    
    # Basic service check
    if not check_ollama_service():
        all_checks_passed = False
    
    # API connectivity
    if not check_ollama_connectivity():
        all_checks_passed = False
        suggest_fixes()
        return
    
    # Model availability
    models = list_ollama_models()
    if not models:
        print("\n⚠️  No models available - need to pull models first!")
        print("Run: ollama pull llama3.1:8b")
        all_checks_passed = False
    
    # Test generation if models available
    if models:
        # Try to find llama3.1:8b or use first available
        target_model = None
        for model in models:
            if "llama3.1" in model['name']:
                target_model = model['name']
                break
        if not target_model and models:
            target_model = models[0]['name']
        
        if target_model:
            if not test_model_generation(target_model):
                all_checks_passed = False
    
    # System resources
    check_system_resources()
    
    # Recent logs
    check_ollama_logs()
    
    # Summary
    print("\n" + "=" * 50)
    if all_checks_passed:
        print("✅ All checks passed! Ollama should be working.")
    else:
        print("❌ Issues detected with Ollama setup.")
        suggest_fixes()

if __name__ == "__main__":
    main()