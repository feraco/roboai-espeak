#!/usr/bin/env python3
"""
OM1 Configuration Usage Examples
Demonstrates how to use the organized config directory structure.
"""

def show_usage_examples():
    """Display usage examples for the organized config structure."""
    
    print("🎯 OM1 Organized Configuration Usage Examples")
    print("=" * 60)
    
    examples = [
        {
            "category": "🤖 Main Configuration",
            "description": "Primary Lex Channel Chief agent",
            "commands": [
                "uv run src/run.py lex_channel_chief",
                "./lex start",
                "python -m src.control.local_dashboard"
            ]
        },
        {
            "category": "🤖 Robot Configurations", 
            "description": "Physical robot hardware setups",
            "commands": [
                "uv run src/run.py unitree_g1_humanoid",
                "uv run src/run.py unitree_go2_basic",
                "uv run src/run.py spot",
                "uv run src/run.py turtlebot4",
                "uv run src/run.py astra_vein_receptionist"
            ]
        },
        {
            "category": "☁️ Cloud Configurations",
            "description": "Cloud-based AI service setups",
            "commands": [
                "uv run src/run.py gemini",
                "uv run src/run.py open_ai", 
                "uv run src/run.py deepseek",
                "uv run src/run.py cloud_openai_elevenlabs",
                "uv run src/run.py grok"
            ]
        },
        {
            "category": "🏠 Local Configurations",
            "description": "Completely offline local setups",
            "commands": [
                "uv run src/run.py local_agent",
                "uv run src/run.py local_offline_agent",
                "uv run src/run.py gpu_optimized_local",
                "uv run src/run.py macos_offline_agent"
            ]
        },
        {
            "category": "🔀 Hybrid Configurations",
            "description": "Mixed cloud/local service combinations",
            "commands": [
                "uv run src/run.py hybrid_cloud_llm_local_audio",
                "uv run src/run.py hybrid_local_llm_cloud_audio",
                "uv run src/run.py hybrid_mixed_cloud"
            ]
        },
        {
            "category": "🧪 Testing Configurations", 
            "description": "Development and testing setups",
            "commands": [
                "uv run src/run.py test_gps",
                "uv run src/run.py test_lidar",
                "uv run src/run.py dev_mock_services"
            ]
        },
        {
            "category": "🎯 Demo Configurations",
            "description": "Example and demonstration setups", 
            "commands": [
                "uv run src/run.py funny_robot",
                "uv run src/run.py conversation",
                "uv run src/run.py tesla",
                "uv run src/run.py joker_bot"
            ]
        }
    ]
    
    for example in examples:
        print(f"\n{example['category']}")
        print(f"Description: {example['description']}")
        print("Commands:")
        for cmd in example['commands']:
            print(f"  {cmd}")
    
    print(f"\n{'=' * 60}")
    print("📝 Notes:")
    print("• The run.py script automatically searches subdirectories")
    print("• Configuration names remain the same (no path prefixes needed)")
    print("• All existing scripts and tools continue to work")
    print("• See config/README.md for detailed directory structure")
    
    print(f"\n🔍 To explore configurations:")
    print("  ls config/                    # See all categories")
    print("  ls config/robots/             # See robot configs")
    print("  ls config/cloud/              # See cloud configs") 
    print("  find config/ -name '*.json5'  # List all configs")

if __name__ == "__main__":
    show_usage_examples()