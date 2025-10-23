#!/usr/bin/env python3
"""
Robostore AI - Simple Web Interface for G1 Agent Configuration
Runs offline on G1 hotspot at http://10.42.0.1:8080
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import subprocess
import json
import os
from pathlib import Path
from typing import List, Dict, Any
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Robostore AI", version="1.0.0")

# Configuration
CONFIG_DIR = Path(__file__).parent.parent / "config"
SERVICE_NAME = "astra-vein-autostart.service"
CURRENT_CONFIG_FILE = Path(__file__).parent / "current_config.txt"

# Models
class ConfigSwitch(BaseModel):
    config_name: str

class StatusResponse(BaseModel):
    agent_running: bool
    current_config: str
    service_status: str

# Helper functions
def get_service_status() -> Dict[str, Any]:
    """Check systemd service status"""
    try:
        result = subprocess.run(
            ["systemctl", "is-active", SERVICE_NAME],
            capture_output=True,
            text=True,
            timeout=5
        )
        is_running = result.stdout.strip() == "active"
        
        # Get detailed status
        status_result = subprocess.run(
            ["systemctl", "status", SERVICE_NAME, "--no-pager"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        return {
            "running": is_running,
            "status": result.stdout.strip(),
            "details": status_result.stdout
        }
    except Exception as e:
        logger.error(f"Error checking service status: {e}")
        return {
            "running": False,
            "status": "unknown",
            "details": str(e)
        }

def get_current_config() -> str:
    """Get currently active config name"""
    try:
        if CURRENT_CONFIG_FILE.exists():
            return CURRENT_CONFIG_FILE.read_text().strip()
        return "astra_vein_receptionist.json5"
    except Exception as e:
        logger.error(f"Error reading current config: {e}")
        return "unknown"

def set_current_config(config_name: str):
    """Save currently active config name"""
    try:
        CURRENT_CONFIG_FILE.write_text(config_name)
    except Exception as e:
        logger.error(f"Error saving current config: {e}")

def list_available_configs() -> List[Dict[str, str]]:
    """List all available .json5 config files"""
    configs = []
    try:
        for config_file in CONFIG_DIR.glob("*.json5"):
            # Read config to get friendly name
            name = config_file.stem.replace("_", " ").title()
            configs.append({
                "filename": config_file.name,
                "display_name": name,
                "path": str(config_file)
            })
        return sorted(configs, key=lambda x: x["display_name"])
    except Exception as e:
        logger.error(f"Error listing configs: {e}")
        return []

def start_agent():
    """Start the agent service"""
    try:
        result = subprocess.run(
            ["sudo", "systemctl", "start", SERVICE_NAME],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode != 0:
            raise Exception(f"Failed to start service: {result.stderr}")
        logger.info("Agent service started")
        return True
    except Exception as e:
        logger.error(f"Error starting agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def stop_agent():
    """Stop the agent service"""
    try:
        result = subprocess.run(
            ["sudo", "systemctl", "stop", SERVICE_NAME],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode != 0:
            raise Exception(f"Failed to stop service: {result.stderr}")
        logger.info("Agent service stopped")
        return True
    except Exception as e:
        logger.error(f"Error stopping agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def restart_agent():
    """Restart the agent service"""
    try:
        result = subprocess.run(
            ["sudo", "systemctl", "restart", SERVICE_NAME],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode != 0:
            raise Exception(f"Failed to restart service: {result.stderr}")
        logger.info("Agent service restarted")
        return True
    except Exception as e:
        logger.error(f"Error restarting agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def switch_config(config_filename: str):
    """Switch to a different config file"""
    try:
        config_path = CONFIG_DIR / config_filename
        if not config_path.exists():
            raise Exception(f"Config file not found: {config_filename}")
        
        # Update the service file to use new config
        service_file = Path("/etc/systemd/system") / SERVICE_NAME
        if service_file.exists():
            content = service_file.read_text()
            # Update ExecStart line with new config
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.strip().startswith('ExecStart='):
                    # Replace config filename in the command
                    parts = line.split()
                    for j, part in enumerate(parts):
                        if part.startswith('config/') and part.endswith('.json5'):
                            parts[j] = f"config/{config_filename}"
                            break
                    lines[i] = ' '.join(parts)
                    break
            
            # Write back
            service_file.write_text('\n'.join(lines))
            
            # Reload systemd
            subprocess.run(["sudo", "systemctl", "daemon-reload"], check=True)
            
            # Save current config
            set_current_config(config_filename)
            
            logger.info(f"Switched to config: {config_filename}")
            return True
        else:
            raise Exception("Service file not found")
    except Exception as e:
        logger.error(f"Error switching config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# API Endpoints
@app.get("/")
async def root():
    """Serve the web interface"""
    html_file = Path(__file__).parent / "index.html"
    if html_file.exists():
        return HTMLResponse(content=html_file.read_text())
    else:
        return HTMLResponse(content="""
        <html><body>
        <h1>Robostore AI</h1>
        <p>Error: Interface file not found. Please check installation.</p>
        </body></html>
        """)

@app.get("/api/status")
async def get_status():
    """Get current agent status"""
    service_status = get_service_status()
    current_config = get_current_config()
    
    return JSONResponse({
        "agent_running": service_status["running"],
        "current_config": current_config,
        "service_status": service_status["status"],
        "details": service_status.get("details", "")
    })

@app.get("/api/configs")
async def get_configs():
    """List all available configurations"""
    configs = list_available_configs()
    return JSONResponse({"configs": configs})

@app.post("/api/agent/start")
async def start_agent_endpoint():
    """Start the agent"""
    start_agent()
    return JSONResponse({"success": True, "message": "Agent started"})

@app.post("/api/agent/stop")
async def stop_agent_endpoint():
    """Stop the agent"""
    stop_agent()
    return JSONResponse({"success": True, "message": "Agent stopped"})

@app.post("/api/agent/restart")
async def restart_agent_endpoint():
    """Restart the agent"""
    restart_agent()
    return JSONResponse({"success": True, "message": "Agent restarted"})

@app.post("/api/config/switch")
async def switch_config_endpoint(data: ConfigSwitch):
    """Switch to a different configuration"""
    switch_config(data.config_name)
    # Restart agent to apply new config
    restart_agent()
    return JSONResponse({
        "success": True,
        "message": f"Switched to {data.config_name} and restarted agent"
    })

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return JSONResponse({"status": "healthy", "service": "robostore-ai"})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")
