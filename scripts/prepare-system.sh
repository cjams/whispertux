#!/bin/bash

# WhisperTux - System Preparation Script
# This script installs system dependencies required BEFORE npm install

set -e  # Exit on any error

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "WhisperTux - Preparing System Dependencies"
echo "Project root: $PROJECT_ROOT"

# Check and install system dependencies
prepare_system() {
    echo "Checking system dependencies..."

    local missing_deps=()

    # Detect package manager
    if command -v apt &> /dev/null; then
        PKG_MANAGER="apt"
        INSTALL_CMD="sudo apt install -y"
        UPDATE_CMD="sudo apt update"
    elif command -v dnf &> /dev/null; then
        PKG_MANAGER="dnf"
        INSTALL_CMD="sudo dnf install -y"
        UPDATE_CMD="sudo dnf check-update"
    elif command -v pacman &> /dev/null; then
        PKG_MANAGER="pacman"
        INSTALL_CMD="sudo pacman -S --noconfirm"
        UPDATE_CMD="sudo pacman -Sy"
    else
        echo "ERROR: Unsupported package manager. Please install dependencies manually:"
        echo "  - git, make, gcc, g++, curl, X11/Wayland development headers"
        exit 1
    fi

    echo "Detected package manager: $PKG_MANAGER"

    if ! command -v make &> /dev/null; then
        echo "WARNING: make not found"
        if [ "$PKG_MANAGER" = "apt" ]; then
            missing_deps+=("build-essential")
        elif [ "$PKG_MANAGER" = "dnf" ]; then
            missing_deps+=("make" "gcc" "gcc-c++" "pkgconfig")
        elif [ "$PKG_MANAGER" = "pacman" ]; then
            missing_deps+=("base-devel")
        fi
    elif ! command -v gcc &> /dev/null || ! command -v g++ &> /dev/null; then
        echo "WARNING: gcc/g++ not found"
        if [ "$PKG_MANAGER" = "apt" ]; then
            missing_deps+=("build-essential")
        elif [ "$PKG_MANAGER" = "dnf" ]; then
            missing_deps+=("gcc" "gcc-c++" "pkgconfig")
        elif [ "$PKG_MANAGER" = "pacman" ]; then
            missing_deps+=("base-devel")
        fi
    fi

    # Check for git
    if ! command -v git &> /dev/null; then
        echo "WARNING: git not found"
        missing_deps+=("git")
    fi

    # Check for curl
    if ! command -v curl &> /dev/null; then
        echo "WARNING: curl not found"
        missing_deps+=("curl")
    fi

    # Check for ydotool and ydotoold (required for text injection)
    echo "Checking for ydotool and ydotoold (required for text injection)..."
    if ! command -v ydotool &> /dev/null; then
        echo "WARNING: ydotool not found (required for text injection)"
        missing_deps+=("ydotool")
    fi

    # Check for ydotoold daemon
    if ! command -v ydotoold &> /dev/null; then
        echo "WARNING: ydotoold not found (required for text injection daemon)"
        missing_deps+=("ydotoold")
    fi

    # Install missing system dependencies
    if [ ${#missing_deps[@]} -gt 0 ]; then
        echo ""
        echo "Missing system dependencies:"
        for dep in "${missing_deps[@]}"; do
            echo "   - $dep"
        done
        echo ""
        echo "These dependencies are required for:"
        echo "   - ydotool for text injection"
        echo "   - whisper.cpp compilation"
        echo ""

        # Ask user permission
        read -p "Install required system dependencies now? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo "Updating package lists..."
            $UPDATE_CMD || true

            echo "Installing system dependencies: ${missing_deps[*]}"
            $INSTALL_CMD "${missing_deps[@]}"

            echo "System dependencies installed successfully"
        else
            echo "ERROR: Cannot continue without system dependencies"
            exit 1
        fi
    else
        echo "All required system dependencies found"
    fi

    # Verify ydotool is available and set up ydotoold service
    echo "Verifying ydotool is available..."
    if ! command -v ydotool &> /dev/null; then
        echo "ERROR: ydotool still not available"
        echo "   Text injection will not work without ydotool"
        exit 1
    fi

    # Add user to required groups for ydotool functionality
    echo "Checking user group memberships..."
    local groups_added=false
    if ! groups "$USER" | grep -q "\binput\b"; then
        echo "Adding user $USER to input group..."
        sudo usermod -a -G input "$USER"
        groups_added=true
    fi

    if ! groups "$USER" | grep -q "\btty\b"; then
        echo "Adding user $USER to tty group..."
        sudo usermod -a -G tty "$USER"
        groups_added=true
    fi

    if [ "$groups_added" = true ]; then
        echo "WARNING: You may need to log out and back in for group changes to take effect"
    fi

    # Set up ydotoold system service
    echo "Setting up ydotoold system service..."
    if ! pgrep -x "ydotoold" > /dev/null; then
        echo "WARNING: ydotoold service is not running"
        echo "   Setting up system service for ydotoold..."

        # Create udev rule for uinput device access
        echo "Setting up uinput device permissions..."
        if [ ! -f "/etc/udev/rules.d/99-uinput.rules" ]; then
            echo "Creating udev rule for uinput device access..."
            sudo tee /etc/udev/rules.d/99-uinput.rules << 'EOF'
# Allow members of the input group to access uinput device
KERNEL=="uinput", GROUP="input", MODE="0660"
EOF
            echo "Reloading udev rules..."
            sudo udevadm control --reload-rules
            sudo udevadm trigger --name-match=uinput
            echo "uinput permissions configured successfully"
        else
            echo "uinput udev rule already exists"
        fi

        # Run the ydotoold service setup script
        if [ -f "$PROJECT_ROOT/scripts/setup-ydotoold-service.sh" ]; then
            echo "Installing ydotoold system service..."
            "$PROJECT_ROOT/scripts/setup-ydotoold-service.sh"
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

    echo "System verified - ydotool is ready for text injection"
}

# Main execution
main() {
    echo "Preparing system for WhisperTux installation..."
    prepare_system

    echo ""
    echo "System preparation complete!"
    echo ""
    echo "Next steps:"
    echo "  1. Run: npm install"
    echo "  2. Run: npm run build-whisper"
    echo "  3. Run: npm start"
    echo ""
    echo "Or run everything at once with: npm run setup"
}

# Check if script is being run directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
