#!/bin/bash
# Build .deb package on Jetson (ARM64 native build)
# Run this script ON THE JETSON after copying the package files

set -e

echo "========================================"
echo "  Lex Agent .deb Package Builder"
echo "  Running on: $(uname -m)"
echo "========================================"
echo ""

# Check if running on ARM64
if [ "$(uname -m)" != "aarch64" ]; then
    echo "❌ This script must run on ARM64 (Jetson)"
    echo "   Current arch: $(uname -m)"
    exit 1
fi

BUILD_DIR="lex_package"
PACKAGE_NAME="lex-agent"
PACKAGE_VERSION="1.0.0"
ARCH="arm64"

# Check if package directory exists
if [ ! -d "$BUILD_DIR/${PACKAGE_NAME}_${PACKAGE_VERSION}_${ARCH}" ]; then
    echo "❌ Package directory not found: $BUILD_DIR/${PACKAGE_NAME}_${PACKAGE_VERSION}_${ARCH}"
    echo "   Please run the Mac build script first and copy the folder to Jetson"
    exit 1
fi

# Install dpkg-dev if not present
if ! command -v dpkg-deb &> /dev/null; then
    echo "📦 Installing dpkg-dev..."
    sudo apt update
    sudo apt install -y dpkg-dev
fi

# Build the package
echo "🔨 Building .deb package..."
cd "$BUILD_DIR"
dpkg-deb --build "${PACKAGE_NAME}_${PACKAGE_VERSION}_${ARCH}"

if [ $? -eq 0 ]; then
    echo ""
    echo "========================================"
    echo "  ✅ Package Built Successfully!"
    echo "========================================"
    echo ""
    echo "📦 Package: ${PACKAGE_NAME}_${PACKAGE_VERSION}_${ARCH}.deb"
    echo ""
    echo "📊 Package Info:"
    dpkg-deb --info "${PACKAGE_NAME}_${PACKAGE_VERSION}_${ARCH}.deb"
    echo ""
    echo "📋 To Install:"
    echo "   sudo dpkg -i ${PACKAGE_NAME}_${PACKAGE_VERSION}_${ARCH}.deb"
    echo "   sudo apt install -f -y  # Fix any missing dependencies"
    echo "   sudo systemctl status lex-agent"
    echo ""
else
    echo "❌ Package build failed!"
    exit 1
fi
