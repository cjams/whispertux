# WhisperTux Setup Guide

This guide walks you through setting up WhisperTux on your Linux system with dependency detection and installation.

## System Requirements

- **Operating System**: Ubuntu 20.04+, Fedora 35+, Arch Linux, or similar
- **Desktop Environment**: X11 or Wayland (both supported)
- **Python**: Version 3.8 or higher
- **Storage**: ~140MB for default base.en model

## Quick Start

The easiest way to get WhisperTux running:

```bash
# Clone the repository
git clone https://github.com/cjams/whispertux.git
cd whispertux

# One-command setup (handles everything automatically)
python3 setup.py
```

This command will:

- Detect your package manager (apt/dnf/pacman)
- Install system dependencies (build tools, ydotool)
- Create Python virtual environment
- Install Python dependencies
- Build and compile whisper.cpp
- Download AI models (base.en by default)
- Configure user permissions and services
- Run tests to verify everything works

## Manual Installation

If you prefer to see each step or have specific requirements:

### 1. Install System Prerequisites

The setup script will detect and install these automatically, but you can install manually:

**Ubuntu/Debian:**

```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv build-essential curl git ydotool
```

**Fedora/RHEL:**

```bash
sudo dnf install python3 python3-pip make gcc gcc-c++ curl git ydotool
```

**Arch Linux:**

```bash
sudo pacman -S python python-pip base-devel curl git ydotool
```

### 2. Clone and Setup

```bash
git clone https://github.com/cjams/whispertux.git
cd whispertux

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Build Whisper.cpp and download models
bash scripts/build-whisper.sh

# Start WhisperTux
python3 main.py
# or use the wrapper script
./whispertux
```

## Post-Installation Setup

### 1. Audio Permissions

WhisperTux needs microphone access. You can also verify audio setup:

```bash
# List audio devices
pactl list sources short

# Test microphone (speak for 3 seconds)
arecord -d 3 -f cd test.wav && aplay test.wav && rm test.wav
```
Your user should be in the audio group. The setup script will check and add the current user to the audio group

### 2. Text Injection Setup

WhisperTux uses `ydotool` for text injection, which works on both X11 and Wayland. The setup script handles this automatically, but you can set it up manually if needed:

**Install ydotool:**

```bash
# Ubuntu/Debian
sudo apt install ydotool

# Fedora
sudo dnf install ydotool

# Arch Linux
sudo pacman -S ydotool
```

**Configure permissions (automatically handled by setup script):**

```bash
# Add user to required groups
sudo usermod -a -G input,tty $USER

# Create udev rule for uinput device access
sudo tee /etc/udev/rules.d/99-uinput.rules << 'EOF'
# Allow members of the input group to access uinput device
KERNEL=="uinput", GROUP="input", MODE="0660"
EOF

# Reload udev rules
sudo udevadm control --reload-rules
sudo udevadm trigger --name-match=uinput
```

**Note:** You may need to log out and back in for group changes to take effect.

### 3. Verify Installation

Test WhisperTux functionality:

1. **Launch**: `python3 main.py` or `./whispertux`
2. **Look for**: WhisperTux GUI window appears
3. **Check status**: Should show "Ready" in the interface
4. **Test hotkey**: Press F12 (default) in any text field
5. **Speak**: Say a few words and see them appear as text

## Usage

### Basic Operation

1. **Start recording**: Click microphone button or press F12 (default hotkey)
2. **Speak clearly**
3. **Stop recording**: Press F12 again or click stop button
4. **Text injection**: Transcribed words appear in the currently focused text field

### Voice Commands for Punctuation

| Say This        | Get This | Say This           | Get This |
| --------------- | -------- | ------------------ | -------- |
| "period"        | .        | "comma"            | ,        |
| "question mark" | ?        | "exclamation mark" | !        |
| "colon"         | :        | "semicolon"        | ;        |
| "dash"          | -        | "underscore"       | \_       |
| "new line"      | ⏎        | "tab"              | ⭾        |
| "open paren"    | (        | "close paren"      | )        |

### Example Workflows

**Git Commands:**

```
Voice: "git add period and git commit dash m 'implement new feature'"
Output: git add . && git commit -m 'implement new feature'
```

**Code Documentation:**

```
Voice: "forward slash forward slash TODO colon add error handling here"
Output: // TODO: add error handling here
```

**General Text:**

```
Voice: "Create a React component that displays user profiles with avatar and name"
Output: Create a React component that displays user profiles with avatar and name
```

## Configuration

### Configuration File

Settings are stored in `~/.config/whispertux/config.json`:

```json
{
  "primary_shortcut": "F12",
  "model": "base",
  "typing_speed": 150,
  "use_clipboard": false,
  "window_position": null,
  "always_on_top": true,
  "theme": "darkly",
  "audio_device": null
}
```

### Model Selection

WhisperTux supports multiple Whisper models:

- **`base.en`** (default): Best balance of speed and accuracy (~140MB)
- **`small.en`**: Faster processing, slightly less accurate (~90MB)
- **`medium.en`**: Higher accuracy, slower processing (~760MB)
- **`large`**: Highest accuracy, slowest processing (~1.5GB)

To change models, edit the config file or use the GUI settings panel.

### Custom Hotkeys

Edit the configuration file to change the recording shortcut:

```json
{
  "primary_shortcut": "ctrl+alt+v"
}
```

Available key combinations:

- Single keys: F1-F12, letters, numbers
- Modifiers: ctrl, alt, shift
- Combined: "ctrl+shift+v", "alt+F12"

### Audio Device Selection

List available devices:

```bash
python3 -c "from src.audio_capture import AudioCapture; AudioCapture().list_devices()"
```

Set in configuration:

```json
{
  "audio_device": "default"
}
```

## Troubleshooting

### Installation Issues

**Build tools missing**

```bash
# The setup script will detect and offer to install these
# Or install manually based on your distro (see Manual Installation above)
```

**Whisper.cpp compilation fails**

```bash
# Try manual compilation with more verbose output
cd whisper.cpp
mkdir -p build
cd build

# Pass non-default cmake options here if you want
cmake ..
make clean
make -j$(nproc) VERBOSE=1
```

### Runtime Issues

**Microphone not detected**

1. Check audio devices: `pactl list sources short`
2. Test recording: `arecord -d 3 test.wav && aplay test.wav`
3. Verify Python audio modules: `python3 -c "import sounddevice; print('Audio OK')"`

**Text injection not working**

1. **Both X11 and Wayland**: Install `ydotool` package (should work automatically once installed)
2. **Test**: Try dictating into a simple text editor first
3. **Check permissions**: Ensure ydotool has proper permissions
4. **uinput permissions issue**: If you see `failed to open uinput device` errors:

   ```bash
   # Check if udev rule exists
   ls -la /etc/udev/rules.d/99-uinput.rules

   # Check current uinput permissions
   ls -la /dev/uinput

   # Should show: crw-rw---- 1 root input
   # If not, the udev rule needs to be created/reloaded

   # Verify you're in the input group
   groups $USER | grep input

   # If issues persist, you may need to reboot for udev changes to take effect
   ```

**Hotkeys not working**

1. Check if another application is using the same shortcuts
2. Test evdev access: Run `./scripts/fix-uinput-permissions.sh` if needed

## Advanced Setup

### Auto-start on Login

Create a desktop entry:

```bash
# Create autostart directory
mkdir -p ~/.config/autostart

# Create desktop file
cat > ~/.config/autostart/whispertux.desktop << EOF
[Desktop Entry]
Type=Application
Name=WhisperTux
Exec=$HOME/path/to/whispertux/whispertux
WorkingDirectory=$HOME/path/to/whispertux
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
EOF
```

You can also use the script [create-desktop-entry.sh](scripts/create-desktop-entry.sh)

### Development Mode

```bash
# Run with debug output
python3 main.py --debug

# Test individual components
python3 -c "from src.audio_capture import AudioCapture; AudioCapture().test()"
python3 -c "from src.whisper_manager import WhisperManager; print('Whisper OK')"
python3 -c "from src.global_shortcuts import GlobalShortcuts; print('Shortcuts OK')"
```

## Getting Help

If you encounter issues:

1. **Check the console**: WhisperTux outputs debug info when run from terminal
2. **Search issues**: [GitHub Issues](https://github.com/cjams/whispertux/issues)
3. **Create new issue**: Include your system info and error messages
4. **System info template**:

```bash
echo "System: $(uname -a)"
echo "Desktop: $XDG_CURRENT_DESKTOP"
echo "Session: $XDG_SESSION_TYPE"
echo "Python: $(python3 --version)"
echo "Audio: $(pactl info | grep 'Server Name')"
```
