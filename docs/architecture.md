# WhisperTux Architecture

WhisperTux uses python and tkinter to provide a simple GUI wrapper around whisper.cpp.
The transcription process is split into several phases: audio capture, whisper transcription,
and text injection.

## Audio Capture

Global shortcuts trigger audio capture through direct hardware-level keyboard monitoring via evdev. The system registers keyboard combinations by accessing /dev/input/event\* devices, parsing key press events, and detecting modifier combinations without desktop environment dependencies.

The audio capture system provides real-time microphone input handling through the sounddevice Python library, which interfaces with the system's audio subsystem (sounddevice uses PortAudio under the hood). The AudioCapture class operates with a 16kHz sample rate in mono channel format using float32 precision, optimized for whisper.cpp's expected input format.

The capture process utilizes callback-based streaming to avoid blocking the main application thread. Audio data flows through a circular buffer where incoming samples are processed in 1024-sample chunks. The system maintains separate threads for recording and real-time level monitoring, allowing the GUI to remain responsive during capture operations.

Device management handles both automatic detection and manual selection of audio input devices. The system queries available devices through sounddevice's device enumeration, testing for input channel availability and accessibility.

Real-time audio level calculation uses root-mean-square (RMS) analysis of incoming samples, scaled for visualization in the waveform display. The monitoring system runs at approximately 20Hz update rate, providing smooth visual feedback without overwhelming the GUI thread.

Audio data accumulates in memory as numpy arrays until recording stops, at which point all chunks are concatenated into a single array for transcription processing.

## Whisper Transcription

The transcription system bridges Python audio data with the whisper.cpp binary through a subprocess-based interface. WhisperManager handles the complete pipeline from audio preprocessing to text output, managing model selection and binary execution.

Audio preprocessing converts numpy float32 arrays to 16-bit PCM WAV files using the standard wave library. The conversion process scales floating-point samples from the [-1, 1] range to 16-bit integer values, maintaining audio fidelity while meeting whisper.cpp's input requirements.

Model management operates through the file system, with support for multiple whisper model sizes (tiny, base, small, medium, large) in both English-only and multilingual variants. The system validates model availability before transcription and provides dynamic model switching without restart requirements.

Transcription execution spawns whisper.cpp certain command-line arguments. Different options could be passed but for now they are hardcoded. The binary runs with English language specification, multi-threading enabled, and text output formatting. A 30-second timeout prevents hung processes while accommodating longer audio segments.

Output parsing handles both stdout capture and temporary file-based output, depending on whisper.cpp's behavior. The system automatically cleans up temporary WAV and text files after processing, preventing disk space accumulation during extended use.

## Text Injection

Text injection operates primarily through ydotool, a userspace alternative to xdotool that works with Wayland/X11/TTYs. The TextInjector class implements text insertion.

The primary injection method executes ydotool as a subprocess with proper shell escaping to handle special characters safely. Text undergoes preprocessing to handle common voice-to-text corrections, converting spoken punctuation commands ("period", "comma") into their symbolic equivalents. This preprocessing layer enables natural speech input without requiring precise punctuation pronunciation.

Integration with the Linux input subsystem occurs through ydotool's uinput interface, which creates virtual input devices for text and key injection. This approach bypasses X11 limitations and works consistently across different display server implementations, providing reliable text injection in modern Linux environments.
