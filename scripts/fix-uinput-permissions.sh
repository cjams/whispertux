#!/bin/bash

# Fix uinput permissions for ydotool
# This script creates the necessary udev rule and adds the user to required groups

set -e

echo "WhisperTux - uinput Permissions Fix"
echo "=================================="
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo "ERROR: Do not run this script as root!"
    echo "Run as your normal user - the script will use sudo when needed."
    exit 1
fi

# Check if ydotool is installed
if ! command -v ydotool &> /dev/null; then
    echo "WARNING: ydotool is not installed!"
    echo "Please install ydotool first:"
    echo ""
    echo "Ubuntu/Debian: sudo apt install ydotool"
    echo "Fedora:        sudo dnf install ydotool" 
    echo "Arch:          sudo pacman -S ydotool"
    echo ""
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "Current situation:"
echo "------------------"

# Check current groups
echo "Your current groups: $(groups)"

# Check if in input group
if groups "$USER" | grep -q "\binput\b"; then
    echo "✓ You are already in the 'input' group"
else
    echo "✗ You are NOT in the 'input' group"
fi

# Check if in tty group
if groups "$USER" | grep -q "\btty\b"; then
    echo "✓ You are already in the 'tty' group"
else
    echo "✗ You are NOT in the 'tty' group"
fi

# Check udev rule
if [ -f "/etc/udev/rules.d/99-uinput.rules" ]; then
    echo "✓ uinput udev rule exists"
    echo "   Content: $(cat /etc/udev/rules.d/99-uinput.rules)"
else
    echo "✗ uinput udev rule does NOT exist"
fi

# Check /dev/uinput permissions
if [ -e "/dev/uinput" ]; then
    echo "Current /dev/uinput permissions: $(ls -la /dev/uinput)"
else
    echo "✗ /dev/uinput device does not exist"
fi

echo ""
echo "Applying fixes:"
echo "---------------"

# Add user to groups
groups_added=false
if ! groups "$USER" | grep -q "\binput\b"; then
    echo "Adding user $USER to 'input' group..."
    sudo usermod -a -G input "$USER"
    groups_added=true
fi

if ! groups "$USER" | grep -q "\btty\b"; then
    echo "Adding user $USER to 'tty' group..."
    sudo usermod -a -G tty "$USER"
    groups_added=true
fi

# Create udev rule
if [ ! -f "/etc/udev/rules.d/99-uinput.rules" ]; then
    echo "Creating uinput udev rule..."
    sudo tee /etc/udev/rules.d/99-uinput.rules << 'EOF'
# Allow members of the input group to access uinput device
KERNEL=="uinput", GROUP="input", MODE="0660"
EOF
    echo "✓ udev rule created"
    
    echo "Reloading udev rules..."
    sudo udevadm control --reload-rules
    sudo udevadm trigger --name-match=uinput
    echo "✓ udev rules reloaded"
else
    echo "✓ uinput udev rule already exists"
fi

echo ""
echo "Final status:"
echo "-------------"

# Check if uinput permissions changed
if [ -e "/dev/uinput" ]; then
    echo "New /dev/uinput permissions: $(ls -la /dev/uinput)"
    
    # Check if permissions look correct
    if ls -la /dev/uinput | grep -q "crw-rw----.*root input"; then
        echo "✓ /dev/uinput permissions look correct!"
    else
        echo "⚠ /dev/uinput permissions may not be correct yet"
        echo "  Expected: crw-rw---- 1 root input"
        echo "  You may need to reboot for the changes to take effect"
    fi
else
    echo "✗ /dev/uinput still does not exist"
fi

if [ "$groups_added" = true ]; then
    echo ""
    echo "IMPORTANT: Group changes have been made!"
    echo "========================================="
    echo ""
    echo "You MUST log out and back in (or reboot) for the group changes to take effect."
    echo ""
    echo "After logging back in, verify the fix worked:"
    echo "1. Check groups: groups"
    echo "2. Check uinput: ls -la /dev/uinput"
    echo "3. Test ydotool: echo 'test' | ydotool type --file -"
    echo ""
    echo "Then try WhisperTux again."
else
    echo ""
    echo "No group changes were needed."
    echo "Try running WhisperTux now - the uinput permissions should be fixed."
fi

echo ""
echo "If you still have issues:"
echo "- Reboot your system to ensure all changes take effect"
echo "- Check the troubleshooting section in docs/setup.md"
echo "- File an issue at: https://github.com/cjams/whispertux/issues"
