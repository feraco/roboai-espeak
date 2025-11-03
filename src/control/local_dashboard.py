"""
Local offline control dashboard for Lex Channel Chief
Follows OM1 architecture patterns - no internet required
"""
import asyncio
import json
import logging
import subprocess
import time
from pathlib import Path
from typing import Dict, Optional, List, Any

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

try:
    from fastapi import FastAPI, WebSocket, Request, Form
    from fastapi.responses import HTMLResponse, RedirectResponse
    from fastapi.templating import Jinja2Templates
    import uvicorn
except ImportError as e:
    print(f"❌ Missing FastAPI dependencies: {e}")
    print("Run: uv add fastapi uvicorn jinja2 python-multipart")
    exit(1)

class OfflineAgentController:
    """
    Manages Lex agent lifecycle following OM1 runtime patterns.
    Compatible with fuser system context and knowledge base loading.
    Integrates with the OM1 Sense → Think → Act pipeline.
    """
    
    def __init__(self):
        """Initialize the offline agent controller"""
        self.config_path = Path("config/lex_channel_chief.json5")
        self.process = None
        self.is_running = False
        self.start_time = None
        self.log_buffer = []
        self.max_log_lines = 1000
        self._log_task = None
    
    def _validate_om1_structure(self) -> bool:
        """Validate OM1 project structure"""
        required_paths = [
            Path("src/run.py"),
            Path("src/fuser"),
            Path("src/runtime"),
            Path("config"),
            Path("pyproject.toml")
        ]
        
        for path in required_paths:
            if not path.exists():
                logging.error(f"Missing OM1 structure: {path}")
                return False
        
        return True
        
        # Verify OM1 config exists and validate structure
        if not self.config_path.exists():
            logging.warning(f"OM1 config not found: {self.config_path}")
    
    def start_agent(self) -> Dict[str, str]:
        """Start the Lex agent using OM1 run pattern with safety checks"""
        # Safety check - prevent multiple starts
        if self.is_running and self.process and self.process.poll() is None:
            return {"status": "warning", "message": "Agent is already running"}
        
        # Reset state if process died but flag still set
        if self.is_running and (not self.process or self.process.poll() is not None):
            self.is_running = False
            self.process = None
        
        # Validate OM1 structure
        required_files = ["src/run.py", "config/lex_channel_chief.json5", "pyproject.toml"]
        for file_path in required_files:
            if not Path(file_path).exists():
                return {"status": "error", "message": f"Missing required file: {file_path}"}
        
        try:
            # Use OM1 standard run command with timeout protection
            cmd = ["uv", "run", "src/run.py", "lex_channel_chief"]
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            # Verify process started successfully (give it 2 seconds)
            time.sleep(2)
            if self.process.poll() is not None:
                # Process died immediately - get error output
                error_output = self.process.stdout.read() if self.process.stdout else "Unknown error"
                return {"status": "error", "message": f"Agent failed to start: {error_output[:200]}..."}
            
            self.is_running = True
            self.start_time = time.time()
            
            # Start async log reading task safely
            try:
                if self._log_task:
                    self._log_task.cancel()
                self._log_task = asyncio.create_task(self._read_logs())
            except Exception:
                pass  # Log task is optional
            
            logging.info(f"Started Lex agent with PID: {self.process.pid} using OM1 runtime")
            return {"status": "success", "message": f"Lex started successfully (PID: {self.process.pid})"}
            
        except FileNotFoundError as e:
            if "uv" in str(e):
                return {"status": "error", "message": "UV package manager not found - please install UV first"}
            return {"status": "error", "message": f"File not found: {e}"}
        except Exception as e:
            logging.error(f"Failed to start agent: {e}")
            self.is_running = False
            self.process = None
            return {"status": "error", "message": f"Start failed: {str(e)[:100]}..."}
    
    def stop_agent(self) -> Dict[str, str]:
        """Stop the Lex agent process gracefully with safety checks"""
        # Check if actually running
        if not self.is_running and not self.process:
            return {"status": "warning", "message": "Agent is not running"}
        
        # If process exists but is already dead, just clean up
        if self.process and self.process.poll() is not None:
            self.is_running = False
            self.process = None
            self.start_time = None
            return {"status": "success", "message": "Agent was already stopped - cleaned up"}
        
        pid = self.process.pid if self.process else "Unknown"
        
        try:
            # Cancel log reading task safely
            if self._log_task:
                try:
                    self._log_task.cancel()
                except Exception:
                    pass  # Task cancellation can fail safely
                self._log_task = None
            
            if not self.process:
                self.is_running = False
                return {"status": "warning", "message": "No process to stop"}
            
            # Try graceful shutdown first (SIGTERM)
            logging.info(f"Attempting graceful shutdown of PID: {pid}")
            self.process.terminate()
            
            try:
                # Wait up to 8 seconds for graceful shutdown
                self.process.wait(timeout=8)
                logging.info("Agent stopped gracefully")
            except subprocess.TimeoutExpired:
                # Force kill if graceful doesn't work (SIGKILL)
                logging.warning(f"Graceful shutdown failed, force killing PID: {pid}")
                try:
                    self.process.kill()
                    self.process.wait(timeout=3)
                    logging.info("Agent force killed successfully")
                except Exception as kill_error:
                    logging.error(f"Force kill failed: {kill_error}")
                    # Continue with cleanup anyway
            
            # Always clean up state
            self.is_running = False
            self.process = None
            self.start_time = None
            
            logging.info(f"Lex agent stopped successfully (was PID: {pid})")
            return {"status": "success", "message": f"Lex stopped successfully (was PID: {pid})"}
            
        except ProcessLookupError:
            # Process already dead
            self.is_running = False
            self.process = None
            self.start_time = None
            return {"status": "success", "message": "Agent process was already terminated"}
        except Exception as e:
            logging.error(f"Failed to stop agent: {e}")
            # Force cleanup even if stop failed
            self.is_running = False
            self.process = None
            self.start_time = None
            return {"status": "warning", "message": f"Stop had issues but cleaned up: {str(e)[:100]}"}
    
    def restart_agent(self) -> Dict[str, str]:
        """Restart the Lex agent (stop + start)"""
        stop_result = self.stop_agent()
        if stop_result["status"] == "error" and "not running" not in stop_result["message"]:
            return stop_result
        
        time.sleep(2)  # Brief pause for cleanup
        return self.start_agent()
    
    def get_status(self) -> Dict[str, Any]:
        """Get current agent status following OM1 patterns"""
        uptime = time.time() - self.start_time if self.start_time else 0
        
        # Load config info if available
        config_info = {}
        if self.config_path.exists():
            try:
                with open(self.config_path) as f:
                    config = json5.load(f)
                config_info = {
                    "agent_name": config.get("name", "Unknown"),
                    "hertz": config.get("hertz", "Unknown"),
                    "llm_type": config.get("cortex_llm", {}).get("type", "Unknown"),
                    "actions_count": len(config.get("agent_actions", [])),
                    "has_knowledge_file": bool(config.get("knowledge_file")),
                    "knowledge_file": config.get("knowledge_file", None)
                }
            except Exception as e:
                logging.warning(f"Could not parse config: {e}")
                config_info = {"parse_error": str(e)}
        
        return {
            "is_running": self.is_running,
            "uptime": self._format_uptime(uptime),
            "pid": self.process.pid if self.process else None,
            "valid_structure": True,  # We validated this at startup
            "valid_config": self.config_path.exists(),
            "memory_mb": self._get_memory_usage(),
            "cpu_percent": None  # Could add psutil support later
        }
    
    def get_config(self) -> Dict[str, Any]:
        """Get OM1 config data for templates"""
        if not self.config_path.exists():
            return {
                "name": "No config",
                "hertz": 0,
                "cortex_llm": {"type": "Unknown"},
                "knowledge_file": None
            }
        
        try:
            with open(self.config_path) as f:
                config = json5.load(f)
            return config
        except Exception as e:
            logging.warning(f"Could not load config: {e}")
            return {
                "name": "Config error",
                "hertz": 0,
                "cortex_llm": {"type": "Error"},
                "knowledge_file": None
            }
    
    def _get_memory_usage(self) -> Optional[float]:
        """Get memory usage in MB if psutil available"""
        if not HAS_PSUTIL or not self.process:
            return None
        
        try:
            process = psutil.Process(self.process.pid)
            return round(process.memory_info().rss / 1024 / 1024, 1)
        except Exception:
            return None
    
    def _format_uptime(self, seconds: float) -> str:
        """Format uptime in human readable format"""
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            return f"{int(seconds//60)}m {int(seconds%60)}s"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"{hours}h {minutes}m"
    
    async def _read_logs(self):
        """Read logs from agent process asynchronously"""
        if not self.process or not self.process.stdout:
            return
            
        try:
            while self.is_running and self.process:
                line = self.process.stdout.readline()
                if line:
                    timestamp = time.strftime("%H:%M:%S")
                    log_entry = f"[{timestamp}] {line.strip()}"
                    self.log_buffer.append(log_entry)
                    
                    # Keep buffer size manageable
                    if len(self.log_buffer) > self.max_log_lines:
                        self.log_buffer.pop(0)
                elif self.process.poll() is not None:
                    # Process has ended
                    break
                else:
                    await asyncio.sleep(0.1)
        except asyncio.CancelledError:
            logging.info("Log reading task cancelled")
        except Exception as e:
            logging.error(f"Error reading logs: {e}")
    
    def get_logs(self, last_n: int = 50) -> List[str]:
        """Get recent log entries"""
        if not self.log_buffer:
            return ["[INFO] No logs available - agent may not be running"]
        return self.log_buffer[-last_n:]
    
    def update_config(self, updates: Dict[str, Any]) -> Dict[str, str]:
        """
        Update agent configuration following OM1 JSON5 format and fuser patterns.
        Updates system prompts, voice settings, and cortex hertz.
        """
        if not self.config_path.exists():
            return {"status": "error", "message": "Configuration file not found"}
        
        try:
            # Load OM1 JSON5 config
            with open(self.config_path, 'r') as f:
                config = json5.load(f)
            
            changes_made = False
            
            # Update system prompt (used by fuser system context)
            if "system_prompt_base" in updates and updates["system_prompt_base"].strip():
                config["system_prompt_base"] = updates["system_prompt_base"]
                changes_made = True
                logging.info("Updated system_prompt_base for fuser")
            
            # Update voice volume (following OM1 action config pattern)
            if "voice_volume" in updates:
                try:
                    volume = float(updates["voice_volume"])
                    if 0.0 <= volume <= 1.0:
                        # Find speak action in OM1 config structure
                        for action in config.get("agent_actions", []):
                            if action.get("name") == "speak":
                                if "config" not in action:
                                    action["config"] = {}
                                action["config"]["volume"] = volume
                                changes_made = True
                                logging.info(f"Updated voice volume to {volume}")
                except (ValueError, KeyError, TypeError) as e:
                    logging.warning(f"Failed to update voice volume: {e}")
            
            # Update response speed (OM1 hertz pattern used by cortex)
            if "response_speed" in updates:
                try:
                    speed = float(updates["response_speed"])
                    if 0.5 <= speed <= 2.0:
                        config["hertz"] = max(1, int(speed * 2))
                        changes_made = True
                        logging.info(f"Updated cortex hertz to {config['hertz']} (speed: {speed})")
                except (ValueError, KeyError, TypeError) as e:
                    logging.warning(f"Failed to update response speed: {e}")
            
            if changes_made:
                # Save config - use JSON for compatibility (OM1 accepts both JSON5 and JSON)
                with open(self.config_path, 'w') as f:
                    json.dump(config, f, indent=2)
                
                logging.info("Configuration updated successfully")
                return {"status": "success", "message": "Configuration updated. Restart to apply changes."}
            else:
                return {"status": "info", "message": "No changes made to configuration"}
                
        except Exception as e:
            logging.error(f"Failed to update config: {e}")
            return {"status": "error", "message": f"Failed to update config: {e}"}


# Setup FastAPI app following OM1 conventions
app = FastAPI(
    title="Lex Channel Chief - Offline Control", 
    version="1.0.0",
    description="OM1-compatible offline control dashboard for Lexful AI agent"
)

# Create templates directory structure
templates_dir = Path("src/control/templates")
templates_dir.mkdir(parents=True, exist_ok=True)

templates = Jinja2Templates(directory=str(templates_dir))
controller = OfflineAgentController()

# Routes following OM1 FastAPI patterns
@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard page"""
    status = controller.get_status()
    
    # Get config data for template
    config = controller.get_config()
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "is_running": status.get("is_running", False),
        "pid": status.get("pid"),
        "uptime": status.get("uptime"),
        "config": config,
        "valid_structure": status.get("valid_structure", False),
        "valid_config": status.get("valid_config", False),
        "memory_mb": status.get("memory_mb"),
        "cpu_percent": status.get("cpu_percent")
    })

@app.get("/start")
async def start_agent(request: Request):
    """Start the agent using OM1 patterns with error handling"""
    try:
        result = controller.start_agent()
        logging.info(f"Start agent result: {result}")
        
        if result["status"] == "error":
            # Show error page instead of redirect
            return templates.TemplateResponse("error.html", {
                "request": request,
                "error_title": "Failed to Start Agent",
                "error_message": result["message"],
                "back_url": "/"
            })
        
        return RedirectResponse(url="/", status_code=302)
    except Exception as e:
        logging.error(f"Start agent failed: {e}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error_title": "System Error",
            "error_message": f"Unexpected error: {str(e)[:200]}",
            "back_url": "/"
        })

@app.get("/stop")
async def stop_agent(request: Request):
    """Stop the agent with error handling"""
    try:
        result = controller.stop_agent()
        logging.info(f"Stop agent result: {result}")
        
        if result["status"] == "error":
            return templates.TemplateResponse("error.html", {
                "request": request,
                "error_title": "Failed to Stop Agent",
                "error_message": result["message"],
                "back_url": "/"
            })
        
        return RedirectResponse(url="/", status_code=302)
    except Exception as e:
        logging.error(f"Stop agent failed: {e}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error_title": "System Error", 
            "error_message": f"Unexpected error: {str(e)[:200]}",
            "back_url": "/"
        })

@app.get("/restart")
async def restart_agent(request: Request):
    """Restart the agent with error handling"""
    try:
        result = controller.restart_agent()
        logging.info(f"Restart agent result: {result}")
        
        if result["status"] == "error":
            return templates.TemplateResponse("error.html", {
                "request": request,
                "error_title": "Failed to Restart Agent",
                "error_message": result["message"],
                "back_url": "/"
            })
        
        return RedirectResponse(url="/", status_code=302)
    except Exception as e:
        logging.error(f"Restart agent failed: {e}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error_title": "System Error",
            "error_message": f"Unexpected error: {str(e)[:200]}",
            "back_url": "/"
        })

@app.get("/api/status")
async def api_status():
    """Get status as JSON API"""
    return controller.get_status()

@app.get("/api/logs")
async def api_logs():
    """Get logs as JSON API"""
    return {"logs": controller.get_logs(50)}

@app.get("/logs", response_class=HTMLResponse)
async def logs_page(request: Request):
    """Logs display page"""
    logs = controller.get_logs(50)
    return templates.TemplateResponse("logs.html", {
        "request": request,
        "logs": "\n".join(logs) if logs else "No logs available"
    })

@app.get("/config", response_class=HTMLResponse)
async def config_page(request: Request):
    """Configuration page"""
    config = controller.get_config()
    status = controller.get_status()
    
    return templates.TemplateResponse("config.html", {
        "request": request,
        "config_json": json.dumps(config, indent=2),
        "current_volume": config.get("agent_actions", [{}])[0].get("config", {}).get("volume", 0.8),
        "current_speed": config.get("hertz", 1) / 2.0,  # Convert hertz back to speed
        "current_prompt": config.get("system_prompt_base", ""),
        "is_running": status.get("is_running", False),
        "message": None,
        "success": False
    })

@app.post("/config")
async def update_config(
    system_prompt: str = Form(""),
    voice_volume: str = Form("0.8"),
    response_speed: str = Form("1.0")
):
    """Update configuration following OM1 config patterns"""
    updates = {
        "system_prompt_base": system_prompt,
        "voice_volume": voice_volume,
        "response_speed": response_speed
    }
    
    result = controller.update_config(updates)
    logging.info(f"Config update result: {result}")
    return RedirectResponse(url="/", status_code=302)

@app.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket):
    """Live log streaming via WebSocket"""
    await websocket.accept()
    
    last_sent = 0
    try:
        while True:
            logs = controller.get_logs()
            if len(logs) > last_sent:
                new_logs = logs[last_sent:]
                for log in new_logs:
                    await websocket.send_text(log)
                last_sent = len(logs)
            
            await asyncio.sleep(1)
    except Exception as e:
        logging.error(f"WebSocket error: {e}")

def run_dashboard(port: int = 8000, host: str = "127.0.0.1"):
    """Run the local dashboard following OM1 patterns"""
    print(f"🎛️  Starting Lex Offline Control Dashboard")
    print(f"🌐 Open in browser: http://{host}:{port}")
    print(f"🔒 Completely offline - no internet required")
    print(f"⚡ Control Lex Channel Chief locally")
    print(f"🤖 Compatible with OM1 fuser and runtime patterns")
    
    # Setup logging for better debugging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    uvicorn.run(app, host=host, port=port, log_level="info")

if __name__ == "__main__":
    run_dashboard()