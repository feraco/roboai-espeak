#!/usr/bin/env python3
"""
Astra Vein Receptionist startup script with audio diagnostics.

This script:
1. Runs audio diagnostics
2. Tests microphone input
3. Verifies device configuration
4. Starts the agent if all checks pass
"""

import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def setup_logging():
    """Configure logging for startup script."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

def run_diagnostics():
    """Run audio diagnostics and return configuration."""
    from utils.audio_config import get_audio_config
    
    print("\n" + "="*70)
    print("🎙️  ASTRA VEIN RECEPTIONIST - STARTUP DIAGNOSTICS")
    print("="*70 + "\n")
    
    # Get audio configuration (with full diagnostics)
    config = get_audio_config(force_detect=True)
    
    return config

def verify_config(config):
    """
    Verify that configuration is valid for starting the agent.
    
    Returns
    -------
    bool
        True if configuration is valid
    """
    print("\n" + "="*70)
    print("📋 CONFIGURATION VERIFICATION")
    print("="*70)
    
    issues = []
    
    if config.input_device is None:
        issues.append("❌ No input device configured")
        print("   Expected: USB PnP Sound Device")
    else:
        print(f"✅ Input device: {config.input_device} - {config.input_name}")
    
    if config.output_device is None:
        issues.append("⚠️  No output device configured (TTS may not work)")
        print("   Expected: USB 2.0 Speaker")
    else:
        print(f"✅ Output device: {config.output_device} - {config.output_name}")
    
    print(f"✅ Sample rate: {config.sample_rate} Hz")
    
    if issues:
        print("\n" + "="*70)
        print("❌ CONFIGURATION ISSUES FOUND")
        print("="*70)
        for issue in issues:
            print(f"  {issue}")
        return False
    
    return True

def start_agent():
    """Start the Astra Vein Receptionist agent."""
    import asyncio
    import json5
    from runtime.single_mode.config import load_config
    from runtime.single_mode.cortex import CortexRuntime
    from runtime.logging import setup_logging as setup_agent_logging
    
    print("\n" + "="*70)
    print("🚀 STARTING AGENT")
    print("="*70 + "\n")
    
    # Setup agent logging
    setup_agent_logging("astra_vein_receptionist", "INFO", False)
    
    # Load configuration
    config = load_config("astra_vein_receptionist")
    
    # Create and run runtime
    runtime = CortexRuntime(config)
    
    print("✅ Agent initialized")
    print("📝 Logging to console (structured I/O format)")
    print("🎤 Listening for audio input...")
    print("📷 Monitoring camera for face detection...")
    print("\nPress Ctrl+C to stop\n")
    
    asyncio.run(runtime.run())

def main():
    """Main startup routine."""
    setup_logging()
    
    try:
        # Run diagnostics
        config = run_diagnostics()
        
        # Verify configuration
        if not verify_config(config):
            print("\n" + "="*70)
            print("❌ CANNOT START AGENT - FIX CONFIGURATION ISSUES")
            print("="*70)
            print("\nTroubleshooting:")
            print("1. Connect USB PnP Sound Device microphone")
            print("2. Connect USB 2.0 Speaker (optional but recommended)")
            print("3. Check system audio permissions:")
            print("   - macOS: System Settings → Privacy → Microphone → Enable Terminal")
            print("   - Linux: Check PulseAudio/ALSA configuration")
            print("4. Run diagnostics again: python3 diagnostics_audio.py")
            return 1
        
        # Start agent
        start_agent()
        return 0
        
    except KeyboardInterrupt:
        print("\n\n" + "="*70)
        print("👋 Agent stopped by user")
        print("="*70)
        return 0
    except Exception as e:
        logging.error(f"\n❌ Fatal error during startup: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
