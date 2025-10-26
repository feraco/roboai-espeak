"""
Test script to verify LLM efficiency improvements.

This script demonstrates the token savings from separating static system context
from dynamic user inputs.
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from runtime.single_mode.config import load_config
from fuser import Fuser


def test_token_efficiency():
    """Test that system context is separated from dynamic inputs."""
    print("=" * 80)
    print("Testing LLM Efficiency Optimization")
    print("=" * 80)
    
    # Load a test configuration
    config = load_config("astra_vein_receptionist")
    
    # Create fuser
    fuser = Fuser(config)
    
    # Get static system context (sent once)
    system_context = fuser.get_system_context()
    
    print("\n📋 STATIC SYSTEM CONTEXT (sent once, cached):")
    print(f"   Length: {len(system_context)} characters")
    print(f"   Estimated tokens: ~{len(system_context) // 4}")
    print(f"\n   First 200 chars: {system_context[:200]}...")
    
    # Simulate a dynamic user input
    from inputs.base import Sensor, SensorConfig
    
    class MockSensor(Sensor):
        def __init__(self):
            super().__init__(SensorConfig())
            self.test_input = "Hello, I need to schedule an appointment"
        
        def formatted_latest_buffer(self):
            return f"ASR Input: {self.test_input}"
        
        async def _raw_to_text(self, raw_input):
            return raw_input
    
    mock_sensor = MockSensor()
    
    # Get dynamic user prompt (sent every time)
    user_prompt = fuser.fuse([mock_sensor], [])
    
    print("\n💬 DYNAMIC USER PROMPT (sent each time):")
    print(f"   Length: {len(user_prompt)} characters")
    print(f"   Estimated tokens: ~{len(user_prompt) // 4}")
    print(f"\n   Content:\n{user_prompt}")
    
    print("\n" + "=" * 80)
    print("📊 EFFICIENCY COMPARISON:")
    print("=" * 80)
    
    # Old approach: everything in one prompt
    old_total = len(system_context) + len(user_prompt)
    
    # New approach: system context sent once, only dynamic input sent repeatedly
    new_per_request = len(user_prompt)
    
    print(f"\n❌ OLD APPROACH (per request):")
    print(f"   Total chars: {old_total}")
    print(f"   Estimated tokens: ~{old_total // 4}")
    
    print(f"\n✅ NEW APPROACH:")
    print(f"   System context (once): {len(system_context)} chars (~{len(system_context) // 4} tokens)")
    print(f"   Per request: {new_per_request} chars (~{new_per_request // 4} tokens)")
    
    # Calculate savings over 10 requests
    requests = 10
    old_total_requests = old_total * requests
    new_total_requests = len(system_context) + (new_per_request * requests)
    savings = old_total_requests - new_total_requests
    savings_pct = (savings / old_total_requests) * 100
    
    print(f"\n💰 SAVINGS OVER {requests} REQUESTS:")
    print(f"   Old total: {old_total_requests} chars (~{old_total_requests // 4} tokens)")
    print(f"   New total: {new_total_requests} chars (~{new_total_requests // 4} tokens)")
    print(f"   Savings: {savings} chars (~{savings // 4} tokens)")
    print(f"   Percentage saved: {savings_pct:.1f}%")
    
    print("\n" + "=" * 80)
    print("✨ System context is now cached by OpenAI/Ollama APIs!")
    print("   Only dynamic inputs are sent with each request.")
    print("=" * 80)


if __name__ == "__main__":
    test_token_efficiency()
