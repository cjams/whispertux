#!/bin/bash

# Setup script for ydotoold systemd service
# This script installs and manages the ydotoold service for WhisperTux

set -e

SERVICE_NAME="ydotoold"
SERVICE_FILE="systemd/ydotoold.service"
SYSTEM_SERVICE_DIR="/etc/systemd/system"

echo "WhisperTux - Setting up ydotoold system service"
echo ""

# Check if ydotoold is installed
if ! command -v ydotoold &> /dev/null; then
    echo "ERROR: ydotoold is not installed"
    echo "Please install ydotoold first:"
    echo "   Ubuntu/Debian: sudo apt install ydotoold"
    echo "   Fedora: sudo dnf install ydotoold"
    echo "   Arch: sudo pacman -S ydotoold"
    exit 1
fi

# Check if we have sudo access for system service installation
if ! sudo -n true 2>/dev/null; then
    echo "This script requires sudo access to install system services."
    echo "   You may be prompted for your password."
fi

# Check if service file exists
if [ ! -f "$SERVICE_FILE" ]; then
    echo "ERROR: Service file not found: $SERVICE_FILE"
    echo "   Please ensure you're running this from the WhisperTux project directory"
    exit 1
fi

# Stop any existing ydotoold processes
if pgrep -x "ydotoold" > /dev/null; then
    echo "Stopping existing ydotoold processes..."
    sudo pkill ydotoold || true
    sleep 1
fi

# Copy wrapper script to system location
echo "Installing ydotoold wrapper script..."
if [ -f "scripts/ydotoold-wrapper.sh" ]; then
    sudo cp "scripts/ydotoold-wrapper.sh" "/usr/local/bin/"
    sudo chmod +x "/usr/local/bin/ydotoold-wrapper.sh"
else
    echo "ERROR: Wrapper script not found: scripts/ydotoold-wrapper.sh"
    exit 1
fi

# Copy service file to system systemd directory
echo "Installing ydotoold system service..."
sudo cp "$SERVICE_FILE" "$SYSTEM_SERVICE_DIR/"

# Reload systemd daemon
echo "Reloading systemd daemon..."
sudo systemctl daemon-reload

# Enable the service
echo "Enabling ydotoold service..."
sudo systemctl enable "$SERVICE_NAME"

# Start the service
echo "Starting ydotoold service..."
sudo systemctl start "$SERVICE_NAME"

# Check service status
echo ""
echo "Service status:"
sudo systemctl status "$SERVICE_NAME" --no-pager -l

# Verify ydotoold is running
sleep 2
if pgrep -x "ydotoold" > /dev/null; then
    echo ""
    echo "ydotoold system service is running successfully!"
    echo "WhisperTux should now be able to inject text properly"
else
    echo ""
    echo "ERROR: ydotoold service failed to start"
    echo "Check the service logs: sudo systemctl logs $SERVICE_NAME"
    exit 1
fi

echo ""
echo "Service management commands (run as root/sudo):"
echo "   Start:   sudo systemctl start $SERVICE_NAME"
echo "   Stop:    sudo systemctl stop $SERVICE_NAME"
echo "   Status:  sudo systemctl status $SERVICE_NAME"
echo "   Logs:    sudo systemctl logs $SERVICE_NAME"
echo "   Restart: sudo systemctl restart $SERVICE_NAME"
echo ""
