# WhisperTux

Voice dictation application for Linux using whisper.cpp for offline speech-to-text transcription.

## Features

- Real-time audio recording with level monitoring
- Local speech-to-text processing via whisper.cpp (no cloud dependencies)
- Global keyboard shortcuts for system-wide operation
- Automatic text injection into focused applications
- Configurable whisper models and shortcuts
- Intelligent text preprocessing for punctuation commands

## Installation

Run the complete setup script:

```bash
git clone https://github.com/cjams/whispertux
cd whispertux
python3 setup.py
```

The setup script handles everything: system dependencies, creating Python virtual environment, building whisper.cpp, downloading models, configuring services, and testing the installation.

### Desktop Integration (Optional)

After building the project, you can add WhisperTux to your desktop environment's applications menu:

```bash
# Create desktop entry for GNOME/KDE/other desktop environments
bash scripts/create-desktop-entry.sh
```

This will:

- Add WhisperTux to your applications menu
- Optionally configure it to start automatically on login
- Create proper desktop integration for launching from GUI

## Usage

Start the application:

```bash
./whispertux
# or
python3 main.py
```

### Basic Operation

1. Press F12 to start recording
2. Speak clearly into your microphone
3. Press F12 again to stop recording
4. Transcribed text appears in the currently focused application

### Keyboard Shortcuts

- F12: Toggle recording (configurable)

### Voice Commands

Spoken punctuation is automatically converted:

- "period" becomes "."
- "comma" becomes ","
- "question mark" becomes "?"
- "new line" creates a line break
- "tab" inserts a tab character

## Configuration

Settings are stored in `~/.config/whispertux/config.json`:

```json
{
  "primary_shortcut": "F12",
  "model": "base",
  "typing_speed": 150,
  "use_clipboard": false,
  "always_on_top": true,
  "theme": "darkly",
  "audio_device": null
}
```

### Available Models

- base: Balanced speed and accuracy (recommended)
- small: Faster processing, reduced accuracy
- medium: Higher accuracy, slower processing
- large: Highest accuracy, slowest processing

## Requirements

- Linux (Ubuntu, Debian, Fedora, Arch Linux)
- Python 3.8+
- Microphone access

## Troubleshooting

### Global Shortcuts Not Working

Most commonly caused by Wayland desktop environment restrictions. Switch to X11 session for better compatibility:

```bash
echo $XDG_SESSION_TYPE  # Check if using Wayland
# Log out and select "Ubuntu on Xorg" at login
```

Test shortcut functionality:

```bash
python3 -c "from src.global_shortcuts import test_key_accessibility; test_key_accessibility()"
```

### Audio Issues

Check microphone access:

```bash
python3 -c "from src.audio_capture import AudioCapture; print(AudioCapture().is_available())"
```

List available audio devices:

```bash
python3 -c "from src.audio_capture import AudioCapture; AudioCapture().list_devices()"
```

### Text Injection Problems

If you see `failed to open uinput device` errors, run the fix script:

```bash
./scripts/fix-uinput-permissions.sh
```

This script will:

- Add your user to the `input` and `tty` groups
- Create the necessary udev rule for `/dev/uinput` access
- Reload udev rules

You may need to log out and back in for group changes to take effect.

Verify ydotoold service status:

```bash
systemctl status ydotoold
sudo systemctl restart ydotoold  # if needed
```

Test text injection directly:

```bash
ydotool type "test message"
```

### Whisper Model Issues

Check available models:

```bash
python3 -c "from src.whisper_manager import WhisperManager; print(WhisperManager().get_available_models())"
```

Download models manually:

```bash
cd whisper.cpp/models
bash download-ggml-model.sh base.en
```

## Documentation

- [Architecture](docs/architecture.md) - Technical architecture and component design
- [Development](docs/development.md) - Development setup and contribution guidelines
- [Setup Details](docs/setup.md) - Manual installation and system configuration

## License

MIT License
