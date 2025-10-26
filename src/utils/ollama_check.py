"""
Utility to check if Ollama is running and has required models.
"""
import logging
import sys
from typing import List, Optional

import aiohttp
import asyncio


async def check_ollama_running(base_url: str = "http://localhost:11434") -> bool:
    """
    Check if Ollama service is running.
    
    Parameters
    ----------
    base_url : str
        Ollama API base URL
        
    Returns
    -------
    bool
        True if Ollama is running, False otherwise
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{base_url}/api/tags", timeout=aiohttp.ClientTimeout(total=5)) as response:
                return response.status == 200
    except Exception as e:
        logging.error(f"Failed to connect to Ollama at {base_url}: {e}")
        return False


async def get_available_models(base_url: str = "http://localhost:11434") -> Optional[List[str]]:
    """
    Get list of available Ollama models.
    
    Parameters
    ----------
    base_url : str
        Ollama API base URL
        
    Returns
    -------
    Optional[List[str]]
        List of model names, or None if request failed
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{base_url}/api/tags", timeout=aiohttp.ClientTimeout(total=5)) as response:
                if response.status == 200:
                    data = await response.json()
                    return [model['name'] for model in data.get('models', [])]
                return None
    except Exception as e:
        logging.error(f"Failed to get Ollama models: {e}")
        return None


async def check_model_available(model_name: str, base_url: str = "http://localhost:11434") -> bool:
    """
    Check if a specific model is available in Ollama.
    
    Parameters
    ----------
    model_name : str
        Name of the model to check (e.g., "llama3.1:8b")
    base_url : str
        Ollama API base URL
        
    Returns
    -------
    bool
        True if model is available, False otherwise
    """
    models = await get_available_models(base_url)
    if models is None:
        return False
    
    # Check exact match or with :latest suffix
    return model_name in models or f"{model_name}:latest" in models or model_name.replace(":latest", "") in [m.replace(":latest", "") for m in models]


async def verify_ollama_setup(model_name: str, base_url: str = "http://localhost:11434") -> bool:
    """
    Verify Ollama is running and has the required model.
    
    Parameters
    ----------
    model_name : str
        Name of the model required
    base_url : str
        Ollama API base URL
        
    Returns
    -------
    bool
        True if everything is ready, False otherwise
    """
    logging.info("Checking Ollama setup...")
    
    # Check if Ollama is running
    if not await check_ollama_running(base_url):
        logging.error(f"❌ Ollama is not running at {base_url}")
        logging.error("   Start Ollama with: systemctl start ollama (Linux) or open Ollama.app (Mac)")
        return False
    
    logging.info(f"✅ Ollama is running at {base_url}")
    
    # Check if model is available
    if not await check_model_available(model_name, base_url):
        models = await get_available_models(base_url)
        logging.error(f"❌ Model '{model_name}' is not available")
        logging.error(f"   Available models: {', '.join(models) if models else 'none'}")
        logging.error(f"   Pull the model with: ollama pull {model_name}")
        return False
    
    logging.info(f"✅ Model '{model_name}' is available")
    return True


def verify_ollama_setup_sync(model_name: str, base_url: str = "http://localhost:11434") -> bool:
    """
    Synchronous wrapper for verify_ollama_setup.
    
    Parameters
    ----------
    model_name : str
        Name of the model required
    base_url : str
        Ollama API base URL
        
    Returns
    -------
    bool
        True if everything is ready, False otherwise
    """
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(verify_ollama_setup(model_name, base_url))
