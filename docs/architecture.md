# WhisperTux Architecture

This document explains the technical architecture, design decisions, and implementation details of WhisperTux's Python-based voice dictation system.

## Overview

WhisperTux is built as a Python application using tkinter for the GUI and integrating multiple technologies to provide seamless voice-to-text functionality across any Linux application.

## Core Components

### 1. Python Application Framework

**Main Application** (`main.py`)

- tkinter GUI application with threading
- Global shortcut registration (F12 via evdev)
- Audio recording coordination and state management
- Window management (floating, always-on-top)
- Configuration and settings management

**Component Modules:**

- `src/audio_capture.py` - Audio recording and processing
- `src/global_shortcuts.py` - System-wide hotkey detection
- `src/whisper_manager.py` - Speech recognition processing
- `src/text_injector.py` - Text injection via ydotool
- `src/config_manager.py` - Configuration management

### 2. Audio Processing Pipeline

#### Step 1: Audio Capture (`src/audio_capture.py`)

```python
import sounddevice as sd
import numpy as np

class AudioCapture:
    def start_recording(self):
        """Start recording audio using sounddevice"""
        with sd.InputStream(
            samplerate=16000,  # Whisper.cpp optimal rate
            channels=1,        # Mono audio
            dtype=np.float32,
            callback=self.audio_callback
        ) as stream:
            self.recording = True
            self.audio_data = []
```

**Features:**

- Real-time audio recording via sounddevice (PortAudio)
- Direct NumPy array handling for efficiency
- Automatic device selection with fallback options
- Live audio level monitoring for UI feedback

#### Step 2: Audio Processing

```python
def process_audio(self, audio_data):
    """Process recorded audio for Whisper.cpp"""
    # Ensure proper sample rate
    if self.sample_rate != 16000:
        audio_data = self.resample_audio(audio_data, 16000)

    # Convert to 16-bit WAV format
    wav_data = (audio_data * 32767).astype(np.int16)
    return wav_data
```

**Process:**

1. Capture audio continuously during recording
2. Store in NumPy float32 arrays
3. Resample to 16kHz if necessary
4. Convert to 16-bit integer format
5. Write to temporary WAV file for Whisper.cpp

### 3. Speech Recognition (`src/whisper_manager.py`)

#### Whisper.cpp Integration

```bash
# Command executed for each transcription
./whisper.cpp/build/bin/whisper-cli \
  -m whisper.cpp/models/ggml-base.en.bin \
  -f temp/audio_123456.wav \
  --output-txt \
  --language en \
  --threads 4
```

**Model Selection:**

- **`ggml-base.en.bin`** (default): 140MB, balanced speed/accuracy
- **`ggml-small.en.bin`** (optional): 90MB, faster processing
- **`ggml-medium.en.bin`** (optional): 760MB, higher accuracy
- **`ggml-large.bin`** (optional): 1.5GB, highest accuracy

**Python Integration:**

```python
class WhisperManager:
    def transcribe_audio(self, audio_file_path):
        """Transcribe audio using whisper.cpp binary"""
        cmd = [
            str(self.whisper_binary),
            '-m', str(self.model_path),
            '-f', str(audio_file_path),
            '--output-txt',
            '--language', 'en',
            '--threads', str(self.thread_count)
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        return self.parse_whisper_output(result.stdout)
```

### 4. Text Processing (`src/text_injector.py`)

#### Smart Text Preprocessing

```python
class TextInjector:
    def preprocess_text(self, text):
        """Convert voice commands to symbols"""
        replacements = {
            r'\bperiod\b': '.',
            r'\bcomma\b': ',',
            r'\bquestion mark\b': '?',
            r'\bexclamation mark\b': '!',
            r'\bdash\b': '-',
            r'\bnew line\b': '\n',
            r'\btab\b': '\t'
        }

        processed = text
        for pattern, replacement in replacements.items():
            processed = re.sub(pattern, replacement, processed, flags=re.IGNORECASE)

        return processed
```

#### Text Injection Methods

**Primary Method: ydotool**

```python
def inject_via_ydotool(self, text):
    """Inject text using ydotool (works on both X11 and Wayland)"""
    try:
        # Escape text for shell safety
        escaped_text = shlex.quote(text)
        cmd = f"ydotool type --delay {self.typing_speed} -- {escaped_text}"

        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            return True
        else:
            raise Exception(f"ydotool failed: {result.stderr}")
    except Exception as e:
        return False
```

**Fallback Method: Clipboard**

```python
def inject_via_clipboard(self, text):
    """Fallback clipboard-based injection"""
    try:
        # Copy to clipboard
        subprocess.run(['wl-copy', text], check=True)
        # Paste via ydotool key simulation
        subprocess.run(['ydotool', 'key', '29:1', '47:1', '47:0', '29:0'], check=True)
        return True
    except subprocess.CalledProcessError:
        return False
```

## System Architecture

### Cross-Platform Design

WhisperTux is designed to work on both X11 and Wayland-based Linux desktops:

```python
class TextInjector:
    def inject_text(self, text):
        """Universal text injection using ydotool"""
        try:
            success = self.inject_via_ydotool(text)
            if not success:
                # Fallback to clipboard method
                return self.inject_via_clipboard(text)
            return success
        except Exception as e:
            self.logger.error(f"Text injection failed: {e}")
            return False
```

**ydotool Advantages:**

- Works on both X11 and Wayland display servers
- No complex display server dependencies or compilation issues
- Simplified installation process without native module compilation
- Does require user to be in in input and have uinput access to avoid running as root

### Threading Architecture

WhisperTux uses Python threading for non-blocking operation:

```python
import threading
from tkinter import Tk

class WhisperTuxApp:
    def __init__(self):
        self.root = Tk()
        self.audio_thread = None
        self.processing_thread = None

    def start_recording(self):
        """Start audio recording in separate thread"""
        self.audio_thread = threading.Thread(
            target=self.audio_capture.start_recording,
            daemon=True
        )
        self.audio_thread.start()

    def process_transcription(self, audio_file):
        """Process transcription in background thread"""
        self.processing_thread = threading.Thread(
            target=self._transcribe_and_inject,
            args=(audio_file,),
            daemon=True
        )
        self.processing_thread.start()
```

**Thread Management:**

1. Main thread handles GUI events and user interaction
2. Audio thread manages continuous recording
3. Processing thread handles Whisper.cpp execution
4. All threads communicate via thread-safe queues

## Performance Considerations

### Memory Management

**Audio Buffers:**

```python
class AudioCapture:
    def __init__(self):
        self.audio_buffer = collections.deque(maxlen=1000)  # Circular buffer
        self.temp_files = []

    def cleanup_temp_files(self):
        """Clean up temporary audio files"""
        for temp_file in self.temp_files:
            if temp_file.exists():
                temp_file.unlink()
        self.temp_files.clear()
```

- Circular buffer for efficient audio storage
- Automatic cleanup of temporary audio files
- Efficient NumPy array handling
- Memory-mapped model loading for Whisper.cpp

**Model Loading:**

- Whisper models loaded once at startup
- Memory mapping for efficient model access
- ~150MB RAM usage for base model

### Processing Optimization

**CPU Usage:**

```python
import multiprocessing

class WhisperManager:
    def __init__(self):
        # Use optimal thread count for system
        self.thread_count = min(4, multiprocessing.cpu_count())

    def transcribe_audio(self, audio_file):
        cmd = [
            self.whisper_binary,
            '--threads', str(self.thread_count),
            # ... other parameters
        ]
```

**Latency Reduction:**

- Chunked audio recording for responsiveness
- Parallel processing where possible
- Minimal UI updates during transcription

### Real-time Visualization

**Audio Level Monitoring:**

```python
class AudioCapture:
    def audio_callback(self, indata, frames, time, status):
        """Real-time audio level calculation"""
        if status:
            self.logger.warning(f'Audio callback status: {status}')

        # Calculate RMS for level display
        rms = np.sqrt(np.mean(indata**2))
        self.current_level = min(1.0, rms * 10)  # Scale for UI

        # Store audio data
        self.audio_buffer.extend(indata[:, 0])
```

**Features:**

- Real-time audio level feedback
- Efficient RMS calculation for visualization
- Non-blocking UI updates
- Minimal CPU overhead for visualization

## Security & Privacy

### Local Processing

**No Cloud Dependencies:**

- All speech recognition happens locally
- No data sent to external servers
- Complete offline operation

**File System Security:**

```python
import tempfile
import os

class AudioCapture:
    def create_temp_file(self):
        """Create secure temporary file"""
        fd, temp_path = tempfile.mkstemp(suffix='.wav', prefix='whisper_')
        os.close(fd)  # Close file descriptor, keep path
        self.temp_files.append(Path(temp_path))
        return temp_path

    def cleanup_temp_files(self):
        """Securely delete temporary files"""
        for temp_file in self.temp_files:
            if temp_file.exists():
                temp_file.unlink()
```

### System Permissions

**Required Permissions:**

- Microphone access (sounddevice/PortAudio)
- uinput device access (ydotool for text injection)
- evdev access (global keyboard shortcuts)

**Permission Handling:**

```python
def check_permissions(self):
    """Check system permissions before starting"""
    # Check audio access
    try:
        sd.query_devices()
    except Exception as e:
        self.show_error("Microphone access denied")

    # Check uinput access
    if not Path('/dev/uinput').exists():
        self.show_error("uinput device not available")

    # Check user groups
    import grp
    user_groups = [g.gr_name for g in grp.getgrall() if self.username in g.gr_mem]
    if 'input' not in user_groups:
        self.show_error("User not in 'input' group")
```

## Error Handling & Resilience

### Graceful Degradation

**Audio Capture Failures:**

```python
class AudioCapture:
    def start_recording(self):
        try:
            with sd.InputStream(**self.stream_params) as stream:
                self.recording = True
        except sd.PortAudioError as e:
            self.logger.error(f"Audio device error: {e}")
            # Try fallback device
            return self.try_fallback_device()
        except Exception as e:
            self.logger.error(f"Unexpected audio error: {e}")
            return False
```

**Text Injection Failures:**

- Primary ydotool injection with clipboard fallback
- Proper error handling and user feedback
- Graceful degradation to copy-paste method

**Whisper.cpp Issues:**

```python
def transcribe_audio(self, audio_file):
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            raise WhisperError(f"Whisper failed: {result.stderr}")
        return self.parse_output(result.stdout)
    except subprocess.TimeoutExpired:
        self.logger.error("Whisper transcription timeout")
        return "Transcription timeout - please try shorter audio"
    except Exception as e:
        self.logger.error(f"Transcription failed: {e}")
        return "Transcription failed"
```

### Logging & Debugging

```python
import logging
from src.logger import setup_logger

class WhisperTuxApp:
    def __init__(self):
        self.logger = setup_logger(__name__)

    def debug_info(self):
        """Log system information for debugging"""
        self.logger.info(f"Python version: {sys.version}")
        self.logger.info(f"tkinter version: {self.root.tk.eval('info patchlevel')}")
        self.logger.info(f"Audio devices: {sd.query_devices()}")
        self.logger.info(f"Session type: {os.environ.get('XDG_SESSION_TYPE')}")
```

## Build System

### Python Environment Setup

The setup script (`setup.py`) handles:

1. **Virtual Environment Creation:**

```python
import subprocess
import sys
import venv

def create_virtual_environment():
    """Create and activate Python virtual environment"""
    venv_path = Path('./venv')
    if not venv_path.exists():
        venv.create(venv_path, with_pip=True)

    # Activate and install requirements
    pip_path = venv_path / 'bin' / 'pip'
    subprocess.run([pip_path, 'install', '-r', 'requirements.txt'])
```

2. **System Dependency Detection:**

```bash
# In scripts/prepare-system.sh
detect_package_manager() {
    if command -v apt >/dev/null 2>&1; then
        echo "apt"
    elif command -v dnf >/dev/null 2>&1; then
        echo "dnf"
    elif command -v pacman >/dev/null 2>&1; then
        echo "pacman"
    else
        echo "unknown"
    fi
}
```

3. **Whisper.cpp Compilation:**

```bash
# Multi-core compilation with error checking
cd whisper.cpp
make clean
make -j$(nproc) || {
    echo "Compilation failed"
    exit 1
}
```

4. **Permission Configuration:**

```bash
# Add user to required groups
sudo usermod -a -G input,tty "$USER"

# Create udev rule for uinput access
sudo tee /etc/udev/rules.d/99-uinput.rules << 'EOF'
KERNEL=="uinput", GROUP="input", MODE="0660"
EOF
```

## Extension Points

### Custom Voice Commands

Adding new voice commands is straightforward:

````python
class TextInjector:
    def __init__(self):
        self.voice_commands = {
            r'\bcode block\b': '```\n\n```',
            r'\bpython function\b': 'def function_name():\n    pass',
            r'\bgit add all\b': 'git add .',
            r'\bgit commit\b': 'git commit -m ""',
        }

    def add_custom_command(self, pattern, replacement):
        """Add user-defined voice command"""
        self.voice_commands[pattern] = replacement
````

### Additional Models

Support for different Whisper models:

```python
class WhisperManager:
    AVAILABLE_MODELS = {
        'tiny.en': 'ggml-tiny.en.bin',
        'small.en': 'ggml-small.en.bin',
        'base.en': 'ggml-base.en.bin',
        'medium.en': 'ggml-medium.en.bin',
        'large': 'ggml-large.bin'
    }

    def switch_model(self, model_name):
        """Switch to different Whisper model"""
        if model_name in self.AVAILABLE_MODELS:
            self.current_model = self.model_dir / self.AVAILABLE_MODELS[model_name]
```

### UI Customization

The tkinter interface can be easily customized:

```python
import tkinter as tk
from tkinter import ttk

class WhisperTuxGUI:
    def setup_styles(self):
        """Configure custom UI styles"""
        style = ttk.Style()
        style.theme_use('clam')  # Modern theme

        # Custom colors
        style.configure('Recording.TButton',
                       background='red',
                       foreground='white')
```

## Future Enhancements

### Planned Features

1. **Multiple Language Support:** Easy to add with different Whisper models
2. **Custom Vocabulary:** User-defined word replacements
3. **Continuous Recording:** Always-listening mode with wake words
4. **Plugin System:** Extensible voice command architecture
5. **GUI Improvements:** Better visualization and controls

### Technical Improvements

1. **Streaming Recognition:** Real-time transcription as you speak
2. **Voice Activity Detection:** Automatic start/stop based on speech
3. **Model Quantization:** Smaller, faster models
4. **GPU Acceleration:** CUDA support for faster processing

## Troubleshooting Architecture

### Common Issues & Solutions

**Audio Pipeline Problems:**

```python
def diagnose_audio_issues(self):
    """Comprehensive audio system diagnosis"""
    try:
        devices = sd.query_devices()
        self.logger.info(f"Available devices: {len(devices)}")

        # Test default device
        test_recording = sd.rec(1024, samplerate=16000, channels=1)
        sd.wait()

        if np.max(np.abs(test_recording)) < 0.001:
            return "No audio input detected"
        return "Audio system OK"

    except Exception as e:
        return f"Audio error: {e}"
```

**Text Injection Issues:**

- Display server detection → Automatic method selection
- Permission problems → Clear setup instructions
- Application compatibility → Multiple injection strategies

**Performance Issues:**

- Memory usage → Streaming processing and cleanup
- CPU usage → Configurable threading
- Latency → Optimized processing pipeline

## Contributing to Architecture

### Code Organization

```
whispertux/
├── main.py                  # Main application entry point
├── src/                     # Core modules
│   ├── audio_capture.py     # Audio recording and processing
│   ├── global_shortcuts.py  # System-wide hotkey detection
│   ├── whisper_manager.py   # Speech recognition coordination
│   ├── text_injector.py     # Text input simulation
│   ├── config_manager.py    # Configuration management
│   └── logger.py           # Logging utilities
├── scripts/                # Build and setup scripts, utilities and fixes
└── docs/                   # Documentation
```

### Development Guidelines

1. **Separation of Concerns:** Each module has a single responsibility
2. **Error Boundaries:** Graceful failure handling at each layer
3. **Performance First:** Minimize latency and resource usage
4. **Cross-Platform:** Support multiple Linux distributions
5. **User Experience:** Clear feedback and intuitive controls
6. **Privacy First:** Local processing with no external dependencies

---

This architecture provides a solid foundation for reliable, performant voice dictation while maintaining privacy and cross-platform compatibility. The modular Python design makes it easy to extend and customize for different use cases.
