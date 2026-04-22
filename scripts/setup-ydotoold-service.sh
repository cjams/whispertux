#!/bin/bash

# Setup script for ydotoold systemd service
# This script installs and manages the ydotoold service for WhisperTux

set -e

SERVICE_NAME="ydotoold"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SERVICE_FILE="$PROJECT_ROOT/systemd/ydotoold.service"
WRAPPER_FILE="$PROJECT_ROOT/scripts/ydotoold-wrapper.sh"
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
    exit 1
fi

# Copy wrapper script to system location
echo "Installing ydotoold wrapper script..."
if [ -f "$WRAPPER_FILE" ]; then
    sudo cp "$WRAPPER_FILE" "/usr/local/bin/"
    sudo chmod +x "/usr/local/bin/ydotoold-wrapper.sh"
else
    echo "ERROR: Wrapper script not found: $WRAPPER_FILE"
    exit 1
fi

# Copy service file to system systemd directory
echo "Installing ydotoold system service..."
sudo cp "$SERVICE_FILE" "$SYSTEM_SERVICE_DIR/"

# Reload systemd daemon
echo "Reloading systemd daemon..."
sudo systemctl daemon-reload

# Stop any old package-provided service before starting the corrected unit.
echo "Stopping existing ydotoold service/processes..."
sudo systemctl stop "$SERVICE_NAME" || true
if YDOTOOLD_PIDS="$(pgrep -x ydotoold || true)" && [ -n "$YDOTOOLD_PIDS" ]; then
    echo "$YDOTOOLD_PIDS" | xargs -r sudo kill
    sleep 1
fi

# Enable the service
echo "Enabling ydotoold service..."
sudo systemctl enable "$SERVICE_NAME"

# Clear any previous start-limit failure before starting the corrected unit.
sudo systemctl reset-failed "$SERVICE_NAME" || true

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
    echo "Check the service logs: sudo journalctl -u $SERVICE_NAME --no-pager -n 100"
    exit 1
fi

echo ""
echo "Service management commands (run as root/sudo):"
echo "   Start:   sudo systemctl start $SERVICE_NAME"
echo "   Stop:    sudo systemctl stop $SERVICE_NAME"
echo "   Status:  sudo systemctl status $SERVICE_NAME"
echo "   Logs:    sudo journalctl -u $SERVICE_NAME --no-pager -n 100"
echo "   Restart: sudo systemctl restart $SERVICE_NAME"
echo ""
