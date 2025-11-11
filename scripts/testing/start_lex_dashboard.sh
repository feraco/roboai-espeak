#!/bin/bash
# Desktop launcher for Lex dashboard
cd "$(dirname "$0")"

echo "🚀 Starting Lex Channel Chief Dashboard..."
echo "📱 Dashboard will open at http://localhost:8080"
echo "🛑 Press Ctrl+C to stop the dashboard"

# Start dashboard
exec uv run python src/control/local_dashboard.py
