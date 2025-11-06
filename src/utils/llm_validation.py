"""
LLM validation utility for pre-start checks.

Ensures Ollama is running and responsive before starting the agent.
"""

import logging
import os
import subprocess
import time
from typing import Optional, Tuple


def check_ollama_service() -> bool:
    """
    Check if Ollama service is running.
    
    Returns
    -------
    bool
        True if Ollama is running, False otherwise
    """
    try:
        # Try systemctl first (Linux)
        result = subprocess.run(
            ["systemctl", "is-active", "ollama"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0 and "active" in result.stdout:
            return True
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    
    # Try curl to check if API is responding
    try:
        result = subprocess.run(
            ["curl", "-s", "-f", "http://localhost:11434/api/tags"],
            capture_output=True,
            timeout=5
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def start_ollama_service() -> bool:
    """
    Try to start Ollama service if it's not running.
    
    Returns
    -------
    bool
        True if service was started successfully
    """
    try:
        # Try systemctl start (needs sudo)
        result = subprocess.run(
            ["sudo", "systemctl", "start", "ollama"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            logging.info("✅ Started Ollama service")
            time.sleep(3)  # Wait for service to fully start
            return True
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        logging.warning(f"Could not start Ollama service: {e}")
    
    return False


def test_ollama_model(model: str, timeout: int = 15) -> Tuple[bool, Optional[str]]:
    """
    Test if Ollama can load and respond with the specified model.
    
    Parameters
    ----------
    model : str
        Model name (e.g., "llama3.1:8b")
    timeout : int
        Timeout in seconds
        
    Returns
    -------
    Tuple[bool, Optional[str]]
        (success, error_message)
    """
    try:
        # Use ollama run with a simple test prompt
        result = subprocess.run(
            ["ollama", "run", model, "Reply with just OK"],
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        if result.returncode == 0:
            response = result.stdout.strip().lower()
            if "ok" in response or len(response) > 0:
                return True, None
            else:
                return False, f"Model responded but output unexpected: {response}"
        else:
            error = result.stderr.strip()
            if "not found" in error.lower():
                return False, f"Model '{model}' not found. Run: ollama pull {model}"
            else:
                return False, f"Model test failed: {error}"
                
    except subprocess.TimeoutExpired:
        return False, f"Model test timed out after {timeout}s. Model may be too large or system too slow."
    except FileNotFoundError:
        return False, "Ollama CLI not found. Is Ollama installed?"
    except Exception as e:
        return False, f"Unexpected error testing model: {e}"


def check_model_exists(model: str) -> bool:
    """
    Check if a model is already pulled/downloaded.
    
    Parameters
    ----------
    model : str
        Model name (e.g., "llama3.1:8b")
        
    Returns
    -------
    bool
        True if model exists locally
    """
    try:
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            # Check if model name appears in the list
            return model in result.stdout
        return False
    except:
        return False


def validate_llm_before_start(model: str = "llama3.1:8b", timeout: int = 20) -> bool:
    """
    Comprehensive LLM validation before starting agent.
    
    Checks:
    1. Ollama service is running
    2. Model is downloaded
    3. Model can respond to test prompt
    
    Parameters
    ----------
    model : str
        Model name to test
    timeout : int
        Timeout for model test in seconds
        
    Returns
    -------
    bool
        True if all checks pass
    """
    logging.info("="*70)
    logging.info(" 🤖 LLM VALIDATION (Pre-Start)")
    logging.info("="*70)
    
    # 1. Check if Ollama is running
    logging.info("📡 Checking Ollama service...")
    if not check_ollama_service():
        logging.warning("⚠️  Ollama service not running")
        logging.info("   Attempting to start Ollama...")
        
        if not start_ollama_service():
            logging.error("❌ Failed to start Ollama service")
            logging.error("   Manual fix: sudo systemctl start ollama")
            return False
    
    logging.info("✅ Ollama service is running")
    
    # 2. Check if model exists
    logging.info(f"📦 Checking if model '{model}' is downloaded...")
    if not check_model_exists(model):
        logging.error(f"❌ Model '{model}' not found locally")
        logging.error(f"   Download with: ollama pull {model}")
        logging.error(f"   This may take several minutes depending on model size")
        return False
    
    logging.info(f"✅ Model '{model}' is available")
    
    # 3. Test model can respond
    logging.info(f"🧪 Testing model inference (timeout: {timeout}s)...")
    logging.info("   Sending test prompt: 'Reply with just OK'")
    
    success, error = test_ollama_model(model, timeout)
    
    if not success:
        logging.error(f"❌ Model test failed: {error}")
        logging.error("   This usually means:")
        logging.error("   1. Model cache is corrupted → Run: ./fix_ollama.sh")
        logging.error("   2. Not enough RAM/memory → Check: free -h")
        logging.error("   3. Model too large for system → Try smaller model")
        return False
    
    logging.info("✅ Model responds correctly")
    logging.info("="*70)
    logging.info("✅ LLM validation PASSED - agent can start")
    logging.info("="*70)
    
    return True


def log_llm_troubleshooting_tips():
    """Log helpful troubleshooting tips for LLM issues."""
    logging.info("")
    logging.info("="*70)
    logging.info(" 🔧 LLM TROUBLESHOOTING TIPS")
    logging.info("="*70)
    logging.info("")
    logging.info("Quick fixes:")
    logging.info("  1. Restart Ollama:     sudo systemctl restart ollama")
    logging.info("  2. Check status:       systemctl status ollama")
    logging.info("  3. View logs:          sudo journalctl -u ollama -n 50")
    logging.info("  4. Test manually:      ollama run llama3.1:8b 'test'")
    logging.info("  5. Clear cache:        ./fix_ollama.sh")
    logging.info("")
    logging.info("If model not found:")
    logging.info("  ollama pull llama3.1:8b")
    logging.info("")
    logging.info("If model test times out:")
    logging.info("  - Check memory: free -h (need ~8GB+ for llama3.1:8b)")
    logging.info("  - Try smaller model: llama3.2:3b")
    logging.info("  - Increase timeout: Set longer timeout in config")
    logging.info("")
    logging.info("If errors 500/499 persist:")
    logging.info("  - Run: ./fix_ollama.sh")
    logging.info("  - Or manually: sudo systemctl stop ollama")
    logging.info("                 rm -rf ~/.ollama/cache")
    logging.info("                 sudo systemctl start ollama")
    logging.info("")
    logging.info("See: JETSON_QUICK_FIX.md for complete troubleshooting")
    logging.info("="*70)
