#!/bin/bash
# Setup script for Lex Channel Chief offline control system
# Follows OM1 UV package management patterns

set -e

echo "🤖 Setting up Lex Channel Chief Offline Control System"
echo "==============================================" 

# Check if we're in the right directory
if [ ! -f "src/run.py" ] || [ ! -f "pyproject.toml" ]; then
    echo "❌ Must be run from OM1 project root"
    echo "   Expected: src/run.py and pyproject.toml present"
    exit 1
fi

echo "✅ Found OM1 project structure"

# Check UV is installed (OM1 standard package manager)
if ! command -v uv &> /dev/null; then
    echo "❌ UV package manager not found"
    echo "   Install with: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

echo "✅ UV package manager found"

# Install offline control dependencies
echo "📦 Installing offline control dependencies..."

# Add dependencies to pyproject.toml if not present
if ! grep -q "fastapi" pyproject.toml; then
    echo "   Adding FastAPI dependencies to pyproject.toml..."
    
    # Backup original
    cp pyproject.toml pyproject.toml.backup
    
    # Add dependencies using UV (OM1 pattern)
    uv add fastapi
    uv add uvicorn
    uv add jinja2
    uv add typer
    uv add psutil
    
    echo "✅ Dependencies added to project"
else
    echo "   Dependencies already in pyproject.toml, syncing..."
    uv sync
fi

# Create control system directories
echo "📁 Creating control system directories..."
mkdir -p src/control/templates
mkdir -p src/control/static
mkdir -p logs

# Create templates directory with HTML files
echo "🎨 Creating web dashboard templates..."

# Create base template
cat > src/control/templates/base.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Lex Channel Chief{% endblock %}</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 3px solid #667eea;
        }
        .logo {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        .status-badge {
            display: inline-block;
            padding: 8px 16px;
            border-radius: 20px;
            font-weight: bold;
            margin: 5px;
        }
        .status-running { background: #4CAF50; color: white; }
        .status-stopped { background: #f44336; color: white; }
        .btn {
            background: #667eea;
            color: white;
            padding: 12px 24px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 16px;
            margin: 5px;
            text-decoration: none;
            display: inline-block;
        }
        .btn:hover { background: #5a67d8; }
        .btn-danger { background: #f44336; }
        .btn-danger:hover { background: #d32f2f; }
        .btn-success { background: #4CAF50; }
        .btn-success:hover { background: #45a049; }
        .info-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }
        .info-card {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }
        .info-card h3 {
            margin-top: 0;
            color: #333;
        }
        .log-output {
            background: #1e1e1e;
            color: #d4d4d4;
            padding: 15px;
            border-radius: 6px;
            font-family: 'Monaco', 'Menlo', monospace;
            font-size: 14px;
            max-height: 400px;
            overflow-y: auto;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">🤖 Lex Channel Chief</div>
            <div>OM1 Offline Control Dashboard</div>
        </div>
        {% block content %}{% endblock %}
    </div>
</body>
</html>
EOF

# Create main dashboard template
cat > src/control/templates/dashboard.html << 'EOF'
{% extends "base.html" %}

{% block content %}
<div class="info-grid">
    <div class="info-card">
        <h3>🔄 Agent Status</h3>
        <div class="status-badge {{ 'status-running' if is_running else 'status-stopped' }}">
            {{ 'Running' if is_running else 'Stopped' }}
        </div>
        {% if is_running and pid %}
        <p><strong>PID:</strong> {{ pid }}</p>
        {% endif %}
        {% if uptime %}
        <p><strong>Uptime:</strong> {{ uptime }}</p>
        {% endif %}
    </div>
    
    <div class="info-card">
        <h3>⚙️ Configuration</h3>
        <p><strong>Agent:</strong> {{ config.name }}</p>
        <p><strong>Hertz:</strong> {{ config.hertz }}</p>
        <p><strong>LLM:</strong> {{ config.cortex_llm.type }}</p>
        {% if config.knowledge_file %}
        <p><strong>Knowledge:</strong> ✅ External file</p>
        {% else %}
        <p><strong>Knowledge:</strong> System prompts only</p>
        {% endif %}
    </div>
</div>

<div style="text-align: center; margin: 30px 0;">
    {% if is_running %}
    <a href="/stop" class="btn btn-danger">🛑 Stop Agent</a>
    <a href="/restart" class="btn">🔄 Restart Agent</a>
    {% else %}
    <a href="/start" class="btn btn-success">🚀 Start Agent</a>
    {% endif %}
    
    <a href="/logs" class="btn">📝 View Logs</a>
    <a href="/config" class="btn">⚙️ Configuration</a>
</div>

<div class="info-card">
    <h3>📊 System Information</h3>
    <p><strong>OM1 Structure:</strong> {{ '✅ Valid' if valid_structure else '❌ Invalid' }}</p>
    <p><strong>Config Valid:</strong> {{ '✅ Yes' if valid_config else '❌ No' }}</p>
    {% if memory_mb %}
    <p><strong>Memory Usage:</strong> {{ memory_mb }}MB</p>
    {% endif %}
    {% if cpu_percent %}
    <p><strong>CPU Usage:</strong> {{ cpu_percent }}%</p>
    {% endif %}
</div>

<script>
// Auto-refresh every 5 seconds
setTimeout(() => {
    window.location.reload();
}, 5000);
</script>
{% endblock %}
EOF

# Create logs template
cat > src/control/templates/logs.html << 'EOF'
{% extends "base.html" %}

{% block title %}Logs - Lex Channel Chief{% endblock %}

{% block content %}
<div style="margin-bottom: 20px;">
    <a href="/" class="btn">← Back to Dashboard</a>
    <button onclick="window.location.reload()" class="btn">🔄 Refresh Logs</button>
</div>

<div class="info-card">
    <h3>📝 Recent Agent Logs</h3>
    <div class="log-output">
        {% if logs %}
{{ logs }}
        {% else %}
No logs available. Agent may not be running or logs not configured.
        {% endif %}
    </div>
</div>

<script>
// Auto-refresh logs every 3 seconds
setTimeout(() => {
    window.location.reload();
}, 3000);
</script>
{% endblock %}
EOF

# Create config template
cat > src/control/templates/config.html << 'EOF'
{% extends "base.html" %}

{% block title %}Configuration - Lex Channel Chief{% endblock %}

{% block content %}
<div style="margin-bottom: 20px;">
    <a href="/" class="btn">← Back to Dashboard</a>
</div>

<div class="info-card">
    <h3>⚙️ Agent Configuration</h3>
    <form method="post" style="margin-top: 20px;">
        <div style="margin-bottom: 15px;">
            <label style="display: block; margin-bottom: 5px; font-weight: bold;">
                🔊 Voice Volume (0.0 - 1.0):
            </label>
            <input type="number" name="volume" min="0" max="1" step="0.1" 
                   value="{{ current_volume or 0.8 }}" 
                   style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px;">
        </div>
        
        <div style="margin-bottom: 15px;">
            <label style="display: block; margin-bottom: 5px; font-weight: bold;">
                ⚡ Response Speed (0.5 - 2.0):
            </label>
            <input type="number" name="speed" min="0.5" max="2.0" step="0.1" 
                   value="{{ current_speed or 1.0 }}" 
                   style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px;">
            <small style="color: #666;">Higher values = faster responses (affects cortex hertz)</small>
        </div>
        
        <div style="margin-bottom: 15px;">
            <label style="display: block; margin-bottom: 5px; font-weight: bold;">
                💬 System Prompt:
            </label>
            <textarea name="prompt" rows="4" 
                      style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px;"
                      placeholder="Enter custom system prompt...">{{ current_prompt or '' }}</textarea>
            <small style="color: #666;">Used by fuser for system context</small>
        </div>
        
        <button type="submit" class="btn btn-success">💾 Save Configuration</button>
    </form>
</div>

{% if message %}
<div class="info-card" style="margin-top: 20px;">
    <p style="color: {{ 'green' if success else 'red' }};">{{ message }}</p>
    {% if success and is_running %}
    <p style="color: orange;">⚠️ Restart agent to apply changes (fuser caches system context)</p>
    {% endif %}
</div>
{% endif %}

<div class="info-card" style="margin-top: 20px;">
    <h3>📋 Current OM1 Configuration</h3>
    <div class="log-output" style="max-height: 300px;">
{{ config_json }}
    </div>
</div>
{% endblock %}
EOF

echo "✅ Web templates created"

# Create CLI executable script
echo "🔧 Creating CLI executable..."
cat > lex << 'EOF'
#!/bin/bash
# Lex Channel Chief CLI launcher following OM1 patterns
cd "$(dirname "$0")"
exec uv run python src/control/lex_cli.py "$@"
EOF

chmod +x lex

# Create desktop launcher (if on Linux/macOS with GUI)
if [[ "$OSTYPE" == "linux-gnu"* ]] || [[ "$OSTYPE" == "darwin"* ]]; then
    echo "🖥️  Creating desktop launcher..."
    cat > start_lex_dashboard.sh << 'EOF'
#!/bin/bash
# Desktop launcher for Lex dashboard
cd "$(dirname "$0")"

echo "🚀 Starting Lex Channel Chief Dashboard..."
echo "📱 Dashboard will open at http://localhost:8080"
echo "🛑 Press Ctrl+C to stop the dashboard"

# Start dashboard
exec uv run python src/control/local_dashboard.py
EOF

    chmod +x start_lex_dashboard.sh
    echo "✅ Desktop launcher created: ./start_lex_dashboard.sh"
fi

# Test the installation
echo "🧪 Testing installation..."

# Test UV dependencies
echo "   Checking UV dependencies..."
if uv run python -c "import fastapi, uvicorn, typer; print('✅ All dependencies available')"; then
    echo "✅ Dependencies test passed"
else
    echo "❌ Dependencies test failed"
    exit 1
fi

# Test OM1 structure validation
echo "   Testing OM1 structure validation..."
if uv run python -c "
import sys
sys.path.append('src/control')
from lex_cli import LexCLI
cli = LexCLI()
if cli.validate_om1_structure():
    print('✅ OM1 structure validation passed')
else:
    print('❌ OM1 structure validation failed')
    sys.exit(1)
"; then
    echo "✅ OM1 validation test passed"
else
    echo "❌ OM1 validation test failed"
    exit 1
fi

# Test config validation if config exists
if [ -f "config/lex_channel_chief.json5" ]; then
    echo "   Testing config validation..."
    if uv run python -c "
import sys
sys.path.append('src/control')
from lex_cli import LexCLI
cli = LexCLI()
if cli.validate_config():
    print('✅ Config validation passed')
else:
    print('❌ Config validation failed')
    sys.exit(1)
"; then
        echo "✅ Config validation test passed"
    else
        echo "⚠️  Config validation test failed - check your lex_channel_chief.json5"
    fi
else
    echo "⚠️  No lex_channel_chief.json5 found - create one to enable full functionality"
fi

echo ""
echo "🎉 Lex Channel Chief Offline Control Setup Complete!"
echo "================================================"
echo ""
echo "🚀 Quick Start:"
echo "   ./lex status          # Check agent status"
echo "   ./lex start           # Start Lex agent" 
echo "   ./lex stop            # Stop Lex agent"
echo ""
echo "🌐 Web Dashboard:"
echo "   ./start_lex_dashboard.sh    # Start web interface"
echo "   Then visit: http://localhost:8080"
echo ""
echo "⚙️  Configuration:"
echo "   ./lex config --help   # See config options"
echo "   Web dashboard config page for GUI editing"
echo ""
echo "📚 All commands work offline - no internet required!"
echo ""

# Save installation info
cat > .lex_control_info << EOF
# Lex Channel Chief Offline Control
# Installation completed: $(date)
# OM1 compatible: Yes
# Dependencies: FastAPI, Uvicorn, Typer, PSUtil, Jinja2
# CLI: ./lex [command]
# Dashboard: ./start_lex_dashboard.sh
EOF

echo "💾 Installation info saved to .lex_control_info"