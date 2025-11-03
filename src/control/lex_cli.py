"""
Command line interface for offline Lex control
Follows OM1 typer CLI patterns and runtime validation
"""
import json
import subprocess
import sys
import time
from pathlib import Path
import typer
from typing import Optional

# OM1-style imports following project conventions
try:
    import json5
except ImportError:
    import json as json5

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

app = typer.Typer(
    help="🤖 Lex Channel Chief - OM1 Offline Control CLI",
    add_completion=False
)

class LexCLI:
    """OM1-compatible CLI controller for Lex agent following project patterns"""
    
    def __init__(self):
        self.config_path = Path("config/lex_channel_chief.json5")
        self.pid_file = Path(".lex_agent.pid")
    
    def validate_om1_structure(self) -> bool:
        """Validate OM1 project structure following project conventions"""
        required_paths = [
            Path("src/run.py"),
            Path("src/fuser"),
            Path("src/runtime"),
            Path("config"),
            Path("pyproject.toml")
        ]
        
        for path in required_paths:
            if not path.exists():
                typer.echo(f"❌ Missing OM1 structure: {path}", err=True)
                return False
        
        return True
    
    def validate_config(self) -> bool:
        """Validate OM1 config file structure following runtime validation"""
        if not self.config_path.exists():
            typer.echo(f"❌ Config not found: {self.config_path}", err=True)
            return False
        
        try:
            with open(self.config_path) as f:
                config = json5.load(f)
            
            # Check OM1 required keys (from runtime/single_mode/config.py)
            required_keys = [
                "hertz", "name", "system_prompt_base", 
                "system_governance", "cortex_llm", "agent_actions"
            ]
            
            missing_keys = [key for key in required_keys if key not in config]
            if missing_keys:
                typer.echo(f"❌ Missing config keys: {missing_keys}", err=True)
                return False
            
            # Validate cortex_llm structure
            if not isinstance(config.get("cortex_llm"), dict) or "type" not in config["cortex_llm"]:
                typer.echo("❌ Invalid cortex_llm configuration", err=True)
                return False
            
            # Validate agent_actions structure
            if not isinstance(config.get("agent_actions"), list):
                typer.echo("❌ Invalid agent_actions configuration", err=True)
                return False
            
            return True
        except Exception as e:
            typer.echo(f"❌ Config validation failed: {e}", err=True)
            return False
    
    def is_running(self) -> bool:
        """Check if Lex agent is running"""
        if not self.pid_file.exists():
            return False
        
        try:
            with open(self.pid_file) as f:
                pid = int(f.read().strip())
            
            if HAS_PSUTIL:
                return psutil.pid_exists(pid)
            else:
                # Fallback without psutil
                try:
                    subprocess.check_output(["ps", "-p", str(pid)], stderr=subprocess.DEVNULL)
                    return True
                except subprocess.CalledProcessError:
                    return False
        except (ValueError, FileNotFoundError):
            return False
    
    def get_pid(self) -> Optional[int]:
        """Get current agent PID"""
        if self.pid_file.exists():
            try:
                with open(self.pid_file) as f:
                    return int(f.read().strip())
            except (ValueError, FileNotFoundError):
                pass
        return None

@app.command()
def start():
    """🚀 Start the Lex Channel Chief agent using OM1 run pattern"""
    cli = LexCLI()
    
    # Validate OM1 structure first
    if not cli.validate_om1_structure():
        typer.echo("❌ Not a valid OM1 project structure", err=True)
        typer.echo("Must be run from OM1 project root with src/run.py", err=True)
        raise typer.Exit(1)
    
    if not cli.validate_config():
        typer.echo("❌ Invalid OM1 configuration", err=True)
        raise typer.Exit(1)
    
    if cli.is_running():
        typer.echo("❌ Lex is already running", err=True)
        raise typer.Exit(1)
    
    typer.echo("🚀 Starting Lex Channel Chief...")
    typer.echo("📋 Using OM1 runtime with fuser integration")
    
    try:
        # Use OM1 standard run pattern (src/run.py)
        process = subprocess.Popen([
            "uv", "run", "src/run.py", "lex_channel_chief"
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Save PID for tracking
        with open(cli.pid_file, 'w') as f:
            f.write(str(process.pid))
        
        typer.echo(f"✅ Lex started successfully (PID: {process.pid})")
        typer.echo("💡 Use './lex status' to check running state")
        typer.echo("🛑 Use './lex stop' to shutdown")
        
    except Exception as e:
        typer.echo(f"❌ Failed to start Lex: {e}", err=True)
        raise typer.Exit(1)

@app.command()
def stop():
    """🛑 Stop the Lex Channel Chief agent"""
    cli = LexCLI()
    
    if not cli.is_running():
        typer.echo("❌ Lex is not running")
        return
    
    pid = cli.get_pid()
    if pid:
        typer.echo(f"🛑 Stopping Lex (PID: {pid})...")
        
        try:
            if HAS_PSUTIL:
                process = psutil.Process(pid)
                process.terminate()
                process.wait(timeout=5)
            else:
                subprocess.run(["kill", str(pid)], check=True)
                time.sleep(2)
            
            cli.pid_file.unlink(missing_ok=True)
            typer.echo("✅ Lex stopped successfully")
            
        except Exception:
            # Try force kill
            try:
                subprocess.run(["kill", "-9", str(pid)], check=False)
                cli.pid_file.unlink(missing_ok=True)
                typer.echo("✅ Lex force-stopped")
            except Exception as e:
                typer.echo(f"❌ Failed to stop Lex: {e}", err=True)

@app.command()
def restart():
    """🔄 Restart the Lex Channel Chief agent"""
    typer.echo("🔄 Restarting Lex Channel Chief...")
    
    stop()
    time.sleep(2)
    start()

@app.command()
def status():
    """📊 Show Lex agent status and OM1 config info"""
    cli = LexCLI()
    
    typer.echo("📊 Lex Channel Chief Status")
    typer.echo("=" * 30)
    
    # OM1 Structure Check
    if cli.validate_om1_structure():
        typer.echo("Structure: ✅ Valid OM1 project")
    else:
        typer.echo("Structure: ❌ Invalid OM1 project")
    
    # Config Check
    if cli.validate_config():
        typer.echo("Config: ✅ Valid OM1 configuration")
    else:
        typer.echo("Config: ❌ Invalid configuration")
    
    # Runtime Status
    if cli.is_running():
        pid = cli.get_pid()
        typer.echo(f"Runtime: 🟢 Running (PID: {pid})")
        
        if HAS_PSUTIL and pid:
            try:
                process = psutil.Process(pid)
                uptime = time.time() - process.create_time()
                memory = process.memory_info().rss / 1024 / 1024  # MB
                cpu = process.cpu_percent()
                
                typer.echo(f"Uptime: {uptime:.0f}s")
                typer.echo(f"Memory: {memory:.1f}MB")
                typer.echo(f"CPU: {cpu:.1f}%")
            except Exception as e:
                typer.echo(f"Details unavailable: {e}")
    else:
        typer.echo("Runtime: 🔴 Stopped")
    
    # Show OM1 config details
    if cli.config_path.exists():
        try:
            with open(cli.config_path) as f:
                config = json5.load(f)
                
            typer.echo("=" * 30)
            typer.echo("OM1 Configuration Details:")
            typer.echo(f"Agent Name: {config.get('name', 'Unknown')}")
            typer.echo(f"Cortex Hertz: {config.get('hertz', 'Unknown')}")
            typer.echo(f"LLM Type: {config.get('cortex_llm', {}).get('type', 'Unknown')}")
            typer.echo(f"Actions: {len(config.get('agent_actions', []))}")
            
            # Check for fuser knowledge file
            if config.get('knowledge_file'):
                knowledge_path = Path(config['knowledge_file'])
                if knowledge_path.exists():
                    typer.echo(f"Knowledge: ✅ {config['knowledge_file']}")
                else:
                    typer.echo(f"Knowledge: ❌ {config['knowledge_file']} (not found)")
            else:
                typer.echo("Knowledge: No external knowledge file")
                
            # Check for multi-mode configuration
            if "modes" in config and "default_mode" in config:
                typer.echo(f"Runtime: Multi-mode ({len(config['modes'])} modes)")
                typer.echo(f"Default Mode: {config['default_mode']}")
            else:
                typer.echo("Runtime: Single-mode")
                
        except Exception as e:
            typer.echo(f"Config details unavailable: {e}")

@app.command()
def config(
    volume: Optional[float] = typer.Option(None, "--volume", "-v", help="Voice volume (0.0-1.0)"),
    speed: Optional[float] = typer.Option(None, "--speed", "-s", help="Response speed (0.5-2.0) - affects cortex hertz"),
    prompt: Optional[str] = typer.Option(None, "--prompt", "-p", help="System prompt text for fuser"),
):
    """⚙️ Update Lex configuration following OM1 patterns"""
    cli = LexCLI()
    
    if not cli.validate_config():
        typer.echo("❌ Invalid configuration file", err=True)
        raise typer.Exit(1)
    
    try:
        # Load OM1 JSON5 config
        with open(cli.config_path, 'r') as f:
            config = json5.load(f)
        
        changes_made = False
        
        # Update volume (OM1 action config pattern)
        if volume is not None:
            if 0.0 <= volume <= 1.0:
                for action in config.get("agent_actions", []):
                    if action.get("name") == "speak":
                        if "config" not in action:
                            action["config"] = {}
                        action["config"]["volume"] = volume
                        changes_made = True
                        typer.echo(f"✅ Volume updated to {volume}")
            else:
                typer.echo("❌ Volume must be between 0.0 and 1.0", err=True)
        
        # Update speed (OM1 hertz pattern used by cortex)
        if speed is not None:
            if 0.5 <= speed <= 2.0:
                config["hertz"] = max(1, int(speed * 2))
                changes_made = True
                typer.echo(f"✅ Speed updated to {speed} (cortex hertz: {config['hertz']})")
            else:
                typer.echo("❌ Speed must be between 0.5 and 2.0", err=True)
        
        # Update prompt (used by fuser system context)
        if prompt:
            config["system_prompt_base"] = prompt
            changes_made = True
            typer.echo("✅ System prompt updated (affects fuser context)")
        
        if changes_made:
            # Save config - use JSON for compatibility (OM1 accepts both)
            with open(cli.config_path, 'w') as f:
                json.dump(config, f, indent=2)
            
            typer.echo("💾 Configuration saved")
            
            if cli.is_running():
                typer.echo("⚠️  Restart Lex to apply changes (fuser caches system context)")
        else:
            typer.echo("ℹ️  No changes made")
            
    except Exception as e:
        typer.echo(f"❌ Failed to update config: {e}", err=True)
        raise typer.Exit(1)

@app.command()
def logs(lines: int = typer.Option(20, "--lines", "-n", help="Number of log lines to show")):
    """📝 Show recent Lex logs"""
    try:
        # Try multiple log locations (project convention)
        log_paths = [
            "/tmp/lex_agent.log",
            "lex_agent.log", 
            "/var/log/lex_agent.log"
        ]
        
        log_content = None
        for log_path in log_paths:
            if Path(log_path).exists():
                try:
                    result = subprocess.run([
                        "tail", "-n", str(lines), log_path
                    ], capture_output=True, text=True)
                    
                    if result.returncode == 0 and result.stdout:
                        log_content = result.stdout
                        break
                except Exception:
                    continue
        
        if log_content:
            typer.echo("📝 Recent Lex Logs:")
            typer.echo("=" * 20)
            typer.echo(log_content)
        else:
            typer.echo("ℹ️  No logs available")
            typer.echo("   Agent may not be running or logs not configured")
            
    except Exception as e:
        typer.echo(f"❌ Failed to get logs: {e}", err=True)

if __name__ == "__main__":
    app()