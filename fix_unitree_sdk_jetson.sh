#!/bin/bash
# Unitree SDK Installation Fix for Jetson with UV
# Run this script on your Jetson Orin to fix the "no module named unitree" error

echo "=========================================="
echo "Unitree SDK Installation for UV - Jetson"
echo "=========================================="
echo ""

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Error: Not in project directory"
    echo "Please run this script from ~/roboai-espeak/"
    exit 1
fi

PROJECT_DIR=$(pwd)
echo "✓ Project directory: $PROJECT_DIR"
echo ""

# Step 1: Check if SDK is already cloned
echo "Step 1: Checking for Unitree SDK..."
if [ -d ~/unitree_sdk2_python ]; then
    echo "✓ SDK already cloned at ~/unitree_sdk2_python"
else
    echo "→ Cloning Unitree SDK..."
    cd ~
    git clone https://github.com/unitreerobotics/unitree_sdk2_python.git
    if [ $? -eq 0 ]; then
        echo "✓ SDK cloned successfully"
    else
        echo "❌ Failed to clone SDK"
        exit 1
    fi
fi
echo ""

# Step 2: Check UV installation
echo "Step 2: Checking UV..."
if command -v uv &> /dev/null; then
    echo "✓ UV is installed: $(uv --version)"
else
    echo "❌ UV not found. Installing..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
fi
echo ""

# Step 3: Try Method 1 - Install from local directory
echo "Step 3: Installing SDK into UV environment..."
cd $PROJECT_DIR

echo "→ Method 1: Installing from local clone..."
uv pip install ~/unitree_sdk2_python/

if [ $? -eq 0 ]; then
    echo "✓ Installation successful (Method 1)"
else
    echo "⚠ Method 1 failed, trying Method 2..."
    
    # Method 2: Install directly from git
    echo "→ Method 2: Installing from git..."
    uv pip install git+https://github.com/unitreerobotics/unitree_sdk2_python.git
    
    if [ $? -eq 0 ]; then
        echo "✓ Installation successful (Method 2)"
    else
        echo "⚠ Method 2 failed, trying Method 3..."
        
        # Method 3: Manual installation into venv
        echo "→ Method 3: Manual installation into .venv..."
        source .venv/bin/activate
        cd ~/unitree_sdk2_python
        python setup.py install
        deactivate
        cd $PROJECT_DIR
        
        if [ $? -eq 0 ]; then
            echo "✓ Installation successful (Method 3)"
        else
            echo "❌ All installation methods failed"
            exit 1
        fi
    fi
fi
echo ""

# Step 4: Verify installation
echo "Step 4: Verifying installation..."
echo "→ Testing import..."

uv run python -c "from unitree.unitree_sdk2py.g1.arm.g1_arm_action_client import G1ArmActionClient; print('✅ Unitree SDK is working!')" 2>&1

if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "✅ SUCCESS! Unitree SDK is installed"
    echo "=========================================="
    echo ""
    echo "You can now run your agent with arm movements:"
    echo "  uv run src/run.py astra_vein_receptionist"
    echo ""
else
    echo ""
    echo "=========================================="
    echo "❌ Installation completed but import test failed"
    echo "=========================================="
    echo ""
    echo "Troubleshooting steps:"
    echo "1. Check if you have the correct SDK version:"
    echo "   cd ~/unitree_sdk2_python && git pull"
    echo ""
    echo "2. Try reinstalling manually:"
    echo "   cd $PROJECT_DIR"
    echo "   source .venv/bin/activate"
    echo "   cd ~/unitree_sdk2_python"
    echo "   python setup.py install"
    echo "   deactivate"
    echo ""
    echo "3. Check for Python version compatibility:"
    echo "   uv run python --version"
    echo "   (Should be Python 3.8 or higher)"
    echo ""
fi

# Show what's installed
echo ""
echo "Installed packages in UV environment:"
uv pip list | grep -i unitree || echo "  (unitree package not found in list)"
