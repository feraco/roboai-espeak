#!/usr/bin/env python3
"""
Test suite for Lex Channel Chief offline control system
Tests OM1 compatibility and control functionality
"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path
import tempfile

def test_om1_structure():
    """Test OM1 project structure validation"""
    print("🧪 Testing OM1 structure validation...")
    
    required_paths = [
        "src/run.py",
        "src/fuser",
        "src/runtime",
        "config",
        "pyproject.toml"
    ]
    
    missing = [p for p in required_paths if not Path(p).exists()]
    if missing:
        print(f"❌ Missing OM1 structure: {missing}")
        return False
    
    print("✅ OM1 structure validation passed")
    return True

def test_dependencies():
    """Test that all required dependencies are available"""
    print("🧪 Testing dependencies...")
    
    try:
        # Test imports
        import fastapi
        import uvicorn
        import typer
        import jinja2
        
        # Test optional import
        try:
            import psutil
            print("✅ PSUtil available for enhanced process management")
        except ImportError:
            print("⚠️  PSUtil not available - basic process management only")
        
        try:
            import json5
            print("✅ JSON5 available for config parsing")
        except ImportError:
            print("⚠️  JSON5 not available - using standard JSON fallback")
        
        print("✅ Core dependencies available")
        return True
        
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        return False

def test_cli_basic():
    """Test CLI basic functionality"""
    print("🧪 Testing CLI basic functionality...")
    
    try:
        # Test CLI help
        result = subprocess.run([
            "uv", "run", "python", "src/control/lex_cli.py", "--help"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0 and "Lex Channel Chief" in result.stdout:
            print("✅ CLI help works")
        else:
            print(f"❌ CLI help failed: {result.stderr}")
            return False
        
        # Test status command
        result = subprocess.run([
            "uv", "run", "python", "src/control/lex_cli.py", "status"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✅ CLI status command works")
        else:
            print(f"❌ CLI status failed: {result.stderr}")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ CLI test failed: {e}")
        return False

def test_config_validation():
    """Test config validation if config exists"""
    print("🧪 Testing config validation...")
    
    config_path = Path("config/lex_channel_chief.json5")
    if not config_path.exists():
        print("⚠️  No lex_channel_chief.json5 - skipping config validation test")
        return True
    
    try:
        # Test config loading
        sys.path.append('src/control')
        from lex_cli import LexCLI
        
        cli = LexCLI()
        if cli.validate_config():
            print("✅ Config validation passed")
            return True
        else:
            print("❌ Config validation failed")
            return False
            
    except Exception as e:
        print(f"❌ Config validation test failed: {e}")
        return False

def test_dashboard_startup():
    """Test dashboard can start (but don't run it)"""
    print("🧪 Testing dashboard startup capability...")
    
    try:
        # Test import and basic setup
        result = subprocess.run([
            "uv", "run", "python", "-c",
            "from src.control.local_dashboard import OfflineAgentController; print('✅ Dashboard import successful')"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✅ Dashboard startup test passed")
            return True
        else:
            print(f"❌ Dashboard startup test failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Dashboard test failed: {e}")
        return False

def test_templates():
    """Test that web templates were created correctly"""
    print("🧪 Testing web templates...")
    
    template_files = [
        "src/control/templates/base.html",
        "src/control/templates/dashboard.html", 
        "src/control/templates/logs.html",
        "src/control/templates/config.html"
    ]
    
    missing = [t for t in template_files if not Path(t).exists()]
    if missing:
        print(f"❌ Missing templates: {missing}")
        return False
    
    # Check template content
    base_template = Path("src/control/templates/base.html")
    content = base_template.read_text()
    
    if "Lex Channel Chief" in content and "{% block content %}" in content:
        print("✅ Templates created correctly")
        return True
    else:
        print("❌ Template content invalid")
        return False

def test_executable_script():
    """Test that CLI executable was created"""
    print("🧪 Testing CLI executable script...")
    
    lex_script = Path("lex")
    if not lex_script.exists():
        print("❌ CLI executable 'lex' not found")
        return False
    
    if not os.access(lex_script, os.X_OK):
        print("❌ CLI executable 'lex' not executable")
        return False
    
    try:
        # Test executable works
        result = subprocess.run(["./lex", "--help"], capture_output=True, text=True, timeout=10)
        if result.returncode == 0 and "Lex Channel Chief" in result.stdout:
            print("✅ CLI executable works")
            return True
        else:
            print(f"❌ CLI executable failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ CLI executable test failed: {e}")
        return False

def test_json_config_handling():
    """Test JSON5 config handling with fallback"""
    print("🧪 Testing JSON config handling...")
    
    try:
        # Create test config
        test_config = {
            "name": "test_agent",
            "hertz": 1,
            "system_prompt_base": "Test prompt",
            "system_governance": "Test governance", 
            "system_prompt_examples": "Test examples",
            "cortex_llm": {"type": "TestLLM"},
            "agent_actions": []
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json5', delete=False) as f:
            json.dump(test_config, f, indent=2)
            temp_path = f.name
        
        try:
            # Test loading
            sys.path.append('src/control')
            from lex_cli import LexCLI
            
            cli = LexCLI()
            cli.config_path = Path(temp_path)
            
            if cli.validate_config():
                print("✅ JSON config handling works")
                return True
            else:
                print("❌ JSON config validation failed")
                return False
                
        finally:
            os.unlink(temp_path)
            
    except Exception as e:
        print(f"❌ JSON config test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Lex Channel Chief Control System Test Suite")
    print("=" * 50)
    
    tests = [
        ("OM1 Structure", test_om1_structure),
        ("Dependencies", test_dependencies),
        ("CLI Basic", test_cli_basic),
        ("Config Validation", test_config_validation),
        ("Dashboard Startup", test_dashboard_startup),
        ("Web Templates", test_templates),
        ("CLI Executable", test_executable_script),
        ("JSON Config", test_json_config_handling),
    ]
    
    results = []
    for name, test_func in tests:
        print(f"\n🔍 {name}:")
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"❌ {name} test crashed: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {status} {name}")
    
    print(f"\n🎯 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Offline control system is ready.")
        
        print("\n🚀 Next steps:")
        print("   1. Create config/lex_channel_chief.json5 if needed")
        print("   2. Run: ./lex status")
        print("   3. Run: ./start_lex_dashboard.sh")
        print("   4. Visit: http://localhost:8080")
        
        return 0
    else:
        print("❌ Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())