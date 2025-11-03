#!/usr/bin/env python3
"""
Quick validation script for organized config directory structure.
Tests that configurations can be found in their new organized locations.
"""

import sys
from pathlib import Path
from typing import Optional

def find_config_file(config_name: str) -> Optional[str]:
    """Find a configuration file by searching the config directory and subdirectories."""
    base_config_dir = Path("config")
    
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

def main():
    """Test config organization."""
    print("🧪 Testing Organized Config Directory Structure")
    print("=" * 50)
    
    test_configs = [
        # Main configs (should be in root)
        ("lex_channel_chief", "Main Lex Channel Chief config"),
        
        # Robot configs
        ("unitree_g1_humanoid", "Unitree G1 humanoid robot"),
        ("unitree_go2_basic", "Unitree Go2 quadruped"),
        ("spot", "Boston Dynamics Spot"),
        ("turtlebot4", "TurtleBot4 navigation"),
        ("astra_vein_receptionist", "Astra Vein receptionist"),
        
        # Cloud configs
        ("gemini", "Google Gemini AI"),
        ("open_ai", "OpenAI GPT"),
        ("deepseek", "DeepSeek AI"),
        ("cloud_openai_elevenlabs", "OpenAI + ElevenLabs"),
        
        # Local configs
        ("local_agent", "Local Ollama agent"),
        ("local_offline_agent", "Fully offline agent"),
        ("gpu_optimized_local", "GPU-optimized local"),
        
        # Hybrid configs
        ("hybrid_cloud_llm_local_audio", "Cloud LLM + Local Audio"),
        ("hybrid_mixed_cloud", "Mixed cloud services"),
        
        # Test configs
        ("test_gps", "GPS sensor test"),
        ("dev_mock_services", "Mock services for dev"),
        
        # Demo configs
        ("funny_robot", "Funny entertainment robot"),
        ("tesla", "Tesla-themed agent"),
        ("conversation", "General conversation"),
    ]
    
    found_count = 0
    total_count = len(test_configs)
    
    for config_name, description in test_configs:
        result = find_config_file(config_name)
        if result:
            print(f"✅ {config_name}: {result}")
            found_count += 1
        else:
            print(f"❌ {config_name}: Not found")
    
    print("\n" + "=" * 50)
    print(f"📊 Results: {found_count}/{total_count} configs found ({found_count/total_count*100:.1f}%)")
    
    if found_count == total_count:
        print("🎉 All configurations successfully organized!")
        return 0
    else:
        print(f"⚠️  {total_count - found_count} configurations not found")
        return 1

if __name__ == "__main__":
    sys.exit(main())