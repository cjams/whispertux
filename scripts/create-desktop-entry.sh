#!/bin/bash
set -e

# WhisperTux Desktop Entry Creator
# Creates desktop entries for GNOME and other desktop environments

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
WHISPERTUX_PATH="$PROJECT_DIR/whispertux"
ICON_PATH="$PROJECT_DIR/assets/whispertux.png"

echo "WhisperTux Desktop Entry Creator"
echo "================================"
echo ""

# Check if whispertux executable exists
if [[ ! -f "$WHISPERTUX_PATH" ]]; then
    echo "Error: WhisperTux executable not found at $WHISPERTUX_PATH"
    echo "Please build the project first:"
    echo "  python3 setup.py"
    echo "  # or"
    echo "  bash scripts/build-whisper.sh"
    exit 1
fi

# Make sure whispertux is executable
chmod +x "$WHISPERTUX_PATH"

# Create applications directory
APPLICATIONS_DIR="$HOME/.local/share/applications"
mkdir -p "$APPLICATIONS_DIR"

# Create autostart directory (for optional autostart)
AUTOSTART_DIR="$HOME/.config/autostart"
mkdir -p "$AUTOSTART_DIR"

DESKTOP_FILE="$APPLICATIONS_DIR/whispertux.desktop"
AUTOSTART_FILE="$AUTOSTART_DIR/whispertux.desktop"

echo "Creating desktop entry..."
echo "   Project location: $PROJECT_DIR"
echo "   Executable: $WHISPERTUX_PATH"
echo "   Icon: $ICON_PATH"
echo "   Desktop file: $DESKTOP_FILE"

# Create the main desktop entry
cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Type=Application
Name=WhisperTux
Comment=Voice dictation for Linux
Exec=$WHISPERTUX_PATH
Path=$PROJECT_DIR
Icon=$ICON_PATH
Terminal=false
StartupNotify=true
Categories=AudioVideo;Audio;Office;
Keywords=voice;dictation;speech;transcription;whisper;
StartupWMClass=whispertux
EOF

echo "Desktop entry created at $DESKTOP_FILE"

# Ask user about autostart
echo ""
echo "Autostart Options"
echo "================="
echo "Would you like WhisperTux to start automatically when you log in?"
echo ""
echo "1) Yes - Start WhisperTux automatically on login"
echo "2) No - Only add to applications menu"
echo ""
read -p "Choose option (1 or 2): " autostart_choice

case $autostart_choice in
    1)
        # Create autostart entry
        cat > "$AUTOSTART_FILE" << EOF
[Desktop Entry]
Type=Application
Name=WhisperTux
Comment=Voice dictation for Linux
Exec=$WHISPERTUX_PATH
Path=$PROJECT_DIR
Icon=$ICON_PATH
Terminal=false
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
StartupNotify=false
Categories=AudioVideo;Audio;Office;
Keywords=voice;dictation;speech;transcription;whisper;
StartupWMClass=whispertux
EOF
        echo "Autostart entry created at $AUTOSTART_FILE"
        echo "   WhisperTux will now start automatically when you log in"
        ;;
    2)
        # Remove autostart entry if it exists
        if [[ -f "$AUTOSTART_FILE" ]]; then
            rm "$AUTOSTART_FILE"
            echo "Removed existing autostart entry"
        fi
        echo "WhisperTux added to applications menu only"
        ;;
    *)
        echo "Invalid choice. Skipping autostart setup."
        ;;
esac

# Update desktop database
if command -v update-desktop-database &> /dev/null; then
    echo ""
    echo "Updating desktop database..."
    update-desktop-database "$APPLICATIONS_DIR"
    echo "Desktop database updated"
fi

# Check for icon
echo ""
echo "Icon Setup"
echo "=========="

# Check if the WhisperTux icon exists
if [[ -f "$ICON_PATH" ]]; then
    echo "Using WhisperTux icon: $ICON_PATH"
    echo "Desktop entries configured with custom WhisperTux icon"
else
    echo "Warning: WhisperTux icon not found at $ICON_PATH"
    echo "   The desktop entry may fall back to a generic icon"
    echo "   Make sure whispertux.png exists in the assets directory"
fi

echo ""
echo "Desktop Entry Setup Complete!"
echo "============================="
echo ""
echo "WhisperTux is now available in your applications menu"
echo "   Look for it in the 'Audio' or 'Office' category"
echo ""

if [[ $autostart_choice == "1" ]]; then
    echo "WhisperTux will start automatically on your next login"
    echo ""
fi

echo "What you can do now:"
echo "   - Launch from applications menu: Search for 'WhisperTux'"
echo "   - Launch from terminal: $WHISPERTUX_PATH"
echo "   - Right-click on desktop entries to edit properties"
echo ""

# Test desktop entry
echo "Testing desktop entry..."
if desktop-file-validate "$DESKTOP_FILE" 2>/dev/null; then
    echo "Desktop entry validation passed"
else
    echo "Warning: Desktop entry validation warnings (entry should still work)"
fi

echo ""
echo "Troubleshooting:"
echo "   - If WhisperTux doesn't appear in menu, try logging out and back in"
echo "   - Run 'update-desktop-database ~/.local/share/applications' manually"
echo "   - Check that $WHISPERTUX_PATH is executable and works"
echo ""
echo "   Remove desktop entries with:"
echo "     rm '$DESKTOP_FILE'"
if [[ -f "$AUTOSTART_FILE" ]]; then
    echo "     rm '$AUTOSTART_FILE'  # (autostart entry)"
fi

echo ""
echo "Happy dictating!"
