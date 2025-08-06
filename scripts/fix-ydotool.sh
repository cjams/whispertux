#!/bin/bash

# Quick fix for ydotoold service
echo "WhisperTux - Fixing ydotool service"

# Check if ydotool is installed
if ! command -v ydotool &> /dev/null; then
    echo "ERROR: ydotool is not installed. Please run: npm run prepare-system"
    exit 1
fi

# Check if ydotoold daemon is installed
if ! command -v ydotoold &> /dev/null; then
    echo "ERROR: ydotoold daemon is not installed"
    echo "Installing ydotoold..."
    
    if command -v apt &> /dev/null; then
        sudo apt update
        sudo apt install -y ydotoold
    elif command -v dnf &> /dev/null; then
        sudo dnf install -y ydotoold
    elif command -v pacman &> /dev/null; then
        sudo pacman -S --noconfirm ydotoold
    else
        echo "ERROR: Unsupported package manager. Please install ydotoold manually"
        exit 1
    fi
    
    echo "ydotoold installed"
fi

# Check if ydotoold service is running
if ! pgrep -x "ydotoold" > /dev/null; then
    echo "WARNING: ydotoold service is not running"
    echo "   Setting up system service for ydotoold..."
    
    # Add user to input group if not already
    if ! groups "$USER" | grep -q "\binput\b"; then
        echo "Adding user $USER to input group..."
        sudo usermod -a -G input "$USER"
        echo "WARNING: You may need to log out and back in for group changes to take effect"
    fi
    
    # Get project directory
    PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    
    # Use the ydotoold service setup script if available
    if [ -f "$PROJECT_DIR/scripts/setup-ydotoold-service.sh" ]; then
        echo "Installing ydotoold system service..."
        "$PROJECT_DIR/scripts/setup-ydotoold-service.sh"
    else
        echo "ERROR: ydotoold service setup script not found"
        echo "   Falling back to manual startup..."
        sudo ydotoold &
        sleep 2
        if pgrep -x "ydotoold" > /dev/null; then
            echo "ydotoold started manually"
        else
            echo "ERROR: Failed to start ydotoold"
            echo "   You may need to start it manually: sudo ydotoold &"
        fi
    fi
else
    echo "ydotoold service is already running"
fi

echo ""
echo "ydotool should now be working!"
echo "Try WhisperTux again with: npm start"
