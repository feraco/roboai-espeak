#!/bin/bash
# Git Cleanup Script - Remove platform-specific artifacts from git index
# Run this before pushing to GitHub

set -e

echo "=================================================="
echo "Git Cleanup - Remove Platform-Specific Artifacts"
echo "=================================================="
echo ""

# Navigate to project root (script can be run from anywhere)
cd "$(dirname "$0")"

echo "📂 Current directory: $(pwd)"
echo ""

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo "❌ Error: Not in a git repository!"
    exit 1
fi

echo "🧹 Removing tracked files that should be ignored..."
echo ""

# Remove virtual environments from git index (if tracked)
if git ls-files | grep -qE "(\.venv|venv|\.uv)"; then
    echo "  Removing .venv, venv, .uv directories..."
    git rm -r --cached .venv venv .uv 2>/dev/null || true
else
    echo "  ✅ No virtual environment directories tracked"
fi

# Remove __pycache__ from git index (if tracked)
if git ls-files | grep -q "__pycache__"; then
    echo "  Removing __pycache__ directories..."
    git rm -r --cached **/__pycache__ 2>/dev/null || true
else
    echo "  ✅ No __pycache__ directories tracked"
fi

# Remove .pyc files from git index (if tracked)
if git ls-files | grep -q "\.pyc$"; then
    echo "  Removing .pyc files..."
    git rm -r --cached **/*.pyc 2>/dev/null || true
else
    echo "  ✅ No .pyc files tracked"
fi

# Remove device_config.yaml from git index (platform-specific)
if git ls-files | grep -q "device_config\.yaml"; then
    echo "  Removing device_config.yaml (platform-specific)..."
    git rm --cached device_config.yaml 2>/dev/null || true
else
    echo "  ✅ device_config.yaml not tracked"
fi

# Remove .DS_Store files (macOS specific)
if git ls-files | grep -q "\.DS_Store"; then
    echo "  Removing .DS_Store files (macOS)..."
    git rm --cached **/.DS_Store 2>/dev/null || true
else
    echo "  ✅ No .DS_Store files tracked"
fi

# Remove log files from git index (if tracked)
if git ls-files | grep -qE "(\.log$|^logs/)"; then
    echo "  Removing log files..."
    git rm -r --cached logs/ 2>/dev/null || true
    git rm --cached **/*.log 2>/dev/null || true
else
    echo "  ✅ No log files tracked"
fi

echo ""
echo "=================================================="
echo "✅ Cleanup Complete!"
echo "=================================================="
echo ""
echo "📋 Summary of changes:"
git status --short | head -20
echo ""
echo "Next steps:"
echo "  1. Review changes: git status"
echo "  2. Commit changes: git commit -m 'cleanup: ignore platform-specific environments'"
echo "  3. Push to GitHub: git push origin main"
echo ""
echo "💡 Tip: Add .gitignore to commit if it was updated"
echo "   git add .gitignore"
echo ""
