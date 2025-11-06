import asyncio
import logging
import multiprocessing as mp
import os
from pathlib import Path
from typing import Optional

import dotenv
import json5
import typer

from runtime.logging import setup_logging
from runtime.multi_mode.config import load_mode_config
from runtime.multi_mode.cortex import ModeCortexRuntime
from runtime.single_mode.config import load_config
from runtime.single_mode.cortex import CortexRuntime
from utils.audio_validation import validate_audio_before_start, log_audio_troubleshooting_tips
from utils.llm_validation import validate_llm_before_start, log_llm_troubleshooting_tips


def find_config_file(config_name: str) -> Optional[str]:
    """
    Find a configuration file by searching the config directory and subdirectories.
    
    Args:
        config_name: The name of the configuration (without .json5 extension)
        
    Returns:
        Path to the config file if found, None otherwise
    """
    base_config_dir = Path(__file__).parent / "../config"
    
    # First, check if it's in the root config directory
    root_path = base_config_dir / f"{config_name}.json5"
    if root_path.exists():
        return str(root_path)
    
    # Then search subdirectories
    for subdir in base_config_dir.iterdir():
        if subdir.is_dir() and subdir.name != "schema":
            config_path = subdir / f"{config_name}.json5"
            if config_path.exists():
                return str(config_path)
    
    return None


app = typer.Typer()


@app.command()
def start(config_name: str, log_level: str = "INFO", log_to_file: bool = False) -> None:
    """
    Start the OM1 agent with a specific configuration.

    Parameters
    ----------
    config_name : str
        The name of the configuration file (without extension) located in the config directory.
    log_level : str, optional
        The logging level to use (default is "INFO").
    log_to_file : bool, optional
        Whether to log output to a file (default is False).
    """
    setup_logging(config_name, log_level, log_to_file)

    # Find config file in organized directory structure
    config_path = find_config_file(config_name)
    if not config_path:
        raise FileNotFoundError(f"Configuration '{config_name}' not found in config directory or subdirectories")

    try:
        with open(config_path, "r") as f:
            raw_config = json5.load(f)

        # Load configuration
        if "modes" in raw_config and "default_mode" in raw_config:
            mode_config = load_mode_config(config_name)
            config_obj = mode_config
            runtime = ModeCortexRuntime(mode_config)
            logging.info(f"Starting OM1 with mode-aware configuration: {config_name}")
            logging.info(f"Available modes: {list(mode_config.modes.keys())}")
            logging.info(f"Default mode: {mode_config.default_mode}")
        else:
            config = load_config(config_name)
            config_obj = config
            runtime = CortexRuntime(config)
            logging.info(f"Starting OM1 with standard configuration: {config_name}")

        # LLM validation before starting (can be disabled with env var)
        skip_llm_validation = os.getenv("SKIP_LLM_VALIDATION", "false").lower() == "true"
        
        if not skip_llm_validation:
            # Extract model name from config
            model_name = "llama3.1:8b"  # Default
            try:
                llm_config = config_obj.cortex_llm
                if hasattr(llm_config, 'config') and hasattr(llm_config.config, 'model'):
                    model_name = llm_config.config.model
                elif hasattr(llm_config, 'model'):
                    model_name = llm_config.model
            except Exception:
                pass  # Use default
            
            # Run LLM validation
            llm_ok = validate_llm_before_start(model=model_name, timeout=20)
            
            if not llm_ok:
                log_llm_troubleshooting_tips()
                logging.error("❌ LLM validation failed - cannot start agent")
                logging.error("   Set SKIP_LLM_VALIDATION=true to bypass this check")
                raise typer.Exit(2)
        else:
            logging.info("ℹ️  LLM validation skipped (SKIP_LLM_VALIDATION=true)")

        # Audio validation before starting (optional, can be disabled with env var)
        skip_audio_validation = os.getenv("SKIP_AUDIO_VALIDATION", "false").lower() == "true"
        
        if not skip_audio_validation:
            # Extract device index from config if LocalASRInput is configured
            device_index = None
            try:
                for input_cfg in config_obj.agent_inputs:
                    if hasattr(input_cfg, 'type') and 'ASR' in input_cfg.type:
                        device_index = getattr(input_cfg.config, 'input_device', None)
                        break
            except Exception:
                pass  # Ignore errors, use default device
            
            # Run validation (skip actual test if in headless/CI environment)
            skip_recording_test = os.getenv("SKIP_AUDIO_TEST", "false").lower() == "true"
            audio_ok = validate_audio_before_start(
                device_index=device_index,
                skip_test=skip_recording_test
            )
            
            if not audio_ok:
                log_audio_troubleshooting_tips()
                logging.error("❌ Audio validation failed - cannot start agent")
                logging.error("   Set SKIP_AUDIO_VALIDATION=true to bypass this check")
                raise typer.Exit(2)
        else:
            logging.info("ℹ️  Audio validation skipped (SKIP_AUDIO_VALIDATION=true)")

        asyncio.run(runtime.run())

    except FileNotFoundError:
        logging.error(f"Configuration file not found: {config_path}")
        raise typer.Exit(1)
    except Exception as e:
        logging.error(f"Error loading configuration: {e}", exc_info=True)
        raise typer.Exit(1)


if __name__ == "__main__":

    # Fix for Linux multiprocessing
    if mp.get_start_method(allow_none=True) != "spawn":
        mp.set_start_method("spawn")

    dotenv.load_dotenv()
    app()
