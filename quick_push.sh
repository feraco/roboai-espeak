#!/bin/bash
# Quick Push Script - Safe deployment to GitHub
# Run this after making changes and testing locally

set -e

echo "🚀 Quick Push to GitHub"
echo "======================="
echo ""

# Check if in git repo
if [ ! -d ".git" ]; then
    echo "❌ Not in a git repository!"
    exit 1
fi

# Run cleanup
echo "1️⃣  Running cleanup script..."
./git_cleanup.sh
echo ""

# Show status
echo "2️⃣  Current git status:"
git status --short
echo ""

# Confirm
read -p "📝 Enter commit message (or 'cancel' to abort): " commit_msg

if [ "$commit_msg" = "cancel" ] || [ -z "$commit_msg" ]; then
    echo "❌ Push cancelled"
    exit 1
fi

# Stage all changes
echo ""
echo "3️⃣  Staging all changes..."
git add .
echo ""

# Show what will be committed
echo "4️⃣  Files to be committed:"
git diff --cached --name-status
echo ""

# Confirm push
read -p "✅ Ready to commit and push? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "❌ Push cancelled"
    git reset
    exit 1
fi

# Commit
echo ""
echo "5️⃣  Committing changes..."
git commit -m "$commit_msg"
echo ""

# Push
echo "6️⃣  Pushing to GitHub..."
git push origin main
echo ""

echo "=================================================="
echo "✅ Successfully pushed to GitHub!"
echo "=================================================="
echo ""
echo "📋 Next steps for Jetson deployment:"
echo "  1. SSH to Jetson: ssh jetson@<ip-address>"
echo "  2. Pull changes: cd ~/roboai-espeak && git pull origin main"
echo "  3. Rebuild: uv sync"
echo "  4. Verify: python diagnostics_audio.py"
echo "  5. Start: uv run src/run.py astra_vein_receptionist"
echo ""
