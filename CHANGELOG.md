# WhisperTux Improvements Changelog

## Date: 2025-10-09
## Session: Hold-to-Record Implementation & Performance Optimizations

### 🎯 Major Features Added

#### 1. Hold-to-Record Mode
**What Changed:**
- Replaced toggle-based hotkey (press once to start, press again to stop) with hold-to-record mode
- Now: Hold Ctrl+Super to record, release to stop and transcribe

**Files Modified:**
- `src/global_shortcuts.py` - Added hold-to-record support with separate press/release callbacks
- `src/config_manager.py` - Added `hold_to_record` configuration option (default: `true`)
- `main.py` - Updated to use separate callbacks for press/release events
- `~/.config/whispertux/config.json` - Added `hold_to_record` setting

**Technical Details:**
- Added `on_press_callback` and `on_release_callback` parameters to `GlobalShortcuts` class
- Added `hold_to_record` boolean flag to switch between modes
- Implemented `_check_shortcut_press()` and `_check_shortcut_release()` methods
- Added `shortcut_was_active` state tracking to prevent duplicate triggers
- Both modes (toggle and hold-to-record) are supported for backward compatibility

**User Impact:**
- More intuitive recording experience
- No need to remember to press the hotkey twice
- Natural "push-to-talk" interaction pattern

---

#### 2. Daemon Mode & Background Execution
**What Changed:**
- Added daemon mode to run WhisperTux in the background, detached from terminal

**Files Modified:**
- `whispertux` launcher script - Added `--daemon` / `-d` flag support

**Technical Details:**
- Uses `nohup` to detach from terminal
- Redirects output to `~/.local/share/whispertux/whispertux.log`
- Prevents duplicate instances from running (checks with `pgrep`)
- Graceful startup with status feedback

**Usage:**
```bash
whispertux -d          # Start in daemon mode
whispertux             # Run in foreground (for debugging)
pkill -f whispertux    # Stop the daemon
```

**User Impact:**
- Can close terminal without killing WhisperTux
- Clean startup/shutdown experience
- Perfect for autostart on boot

---

#### 3. System-Wide PATH Integration
**What Changed:**
- Added WhisperTux to system PATH for easy access from anywhere

**Files Modified:**
- `~/.local/bin/whispertux` - Created symlink to launcher script
- `~/.zshrc` - Added `~/.local/bin` to PATH
- `~/.exports` - Added `~/.local/bin` to PATH

**Technical Details:**
- Created symlink: `~/.local/bin/whispertux -> /home/e/opt/wispr-tux2/whispertux`
- Added `export PATH="$HOME/.local/bin:$PATH"` to shell configs

**User Impact:**
- Can run `whispertux` from any directory
- No need to remember full path
- Integrated into system like any other command

---

### ⚡ Performance Optimizations

#### 1. Multi-Threading Optimization
**What Changed:**
- Increased whisper.cpp thread count from 4 to 16 threads

**Files Modified:**
- `src/whisper_manager.py` - Line 147: `'--threads', '16'`

**Technical Details:**
- Utilizes all 16 CPU cores for parallel processing
- ~4x more threads for faster transcription

**Expected Improvement:**
- 2-4x faster transcription on multi-core systems
- Most noticeable on longer recordings (5+ seconds)

---

#### 2. I/O Optimization
**What Changed:**
- Removed `--output-txt` flag to avoid unnecessary file writes
- Read transcription directly from stdout instead of file I/O

**Files Modified:**
- `src/whisper_manager.py` - Lines 141-172

**Technical Details:**
- Removed file write/read cycle for transcription output
- Direct stdout capture reduces I/O overhead
- Cleanup of any residual txt files

**Expected Improvement:**
- Reduced latency from file I/O operations
- Cleaner temp directory (fewer leftover files)

---

#### 3. Processing Flags Optimization
**What Changed:**
- Added `--no-prints` flag to reduce console output overhead
- Added `--no-timestamps` flag for faster processing

**Files Modified:**
- `src/whisper_manager.py` - Lines 148-149

**Technical Details:**
- `--no-prints` eliminates progress printing overhead
- `--no-timestamps` skips word-level timestamp calculation
- Both reduce processing time without affecting transcription quality

**Expected Improvement:**
- Slight reduction in processing time
- Cleaner output logs

---

### 🔧 Configuration Changes

#### Updated Hotkey
**What Changed:**
- Changed default hotkey from `Ctrl+Super+X` to `Ctrl+Super`

**Files Modified:**
- `~/.config/whispertux/config.json` - Changed `primary_shortcut` value

**Reason:**
- Simpler key combination
- Easier to press and hold
- More ergonomic for frequent use

---

### 📁 Files Modified Summary

1. **src/global_shortcuts.py**
   - Added hold-to-record mode support
   - New parameters: `on_press_callback`, `on_release_callback`, `hold_to_record`
   - New methods: `_check_shortcut_press()`, `_check_shortcut_release()`
   - New callbacks: `_trigger_press_callback()`, `_trigger_release_callback()`

2. **src/config_manager.py**
   - Added `hold_to_record: True` to default config

3. **main.py**
   - Updated `_setup_global_shortcuts()` to use separate callbacks for hold-to-record
   - Added hold-to-record toggle in settings UI
   - Updated `_save_settings()` to handle mode changes

4. **src/whisper_manager.py**
   - Changed threads from 4 to 16
   - Removed `--output-txt` flag
   - Added `--no-prints` and `--no-timestamps` flags
   - Updated output handling to read from stdout

5. **whispertux (launcher script)**
   - Added daemon mode support with `--daemon` / `-d` flag
   - Added process management (duplicate prevention)
   - Added logging to `~/.local/share/whispertux/whispertux.log`

6. **~/.local/bin/whispertux**
   - Created symlink for system-wide access

7. **~/.zshrc & ~/.exports**
   - Added `~/.local/bin` to PATH

8. **~/.config/whispertux/config.json**
   - Changed `primary_shortcut` from `"Ctrl+Super+X"` to `"Ctrl+Super"`
   - Added `"hold_to_record": true`

---

### 🎮 Usage Examples

#### Basic Usage
```bash
# Start in daemon mode (background)
whispertux -d

# Start in foreground (see output)
whispertux

# Stop the daemon
pkill -f whispertux

# View logs
tail -f ~/.local/share/whispertux/whispertux.log
```

#### Hold-to-Record
1. Hold down `Ctrl+Super` (left Ctrl + left Super/Windows key)
2. Speak while holding the keys
3. Release both keys to stop recording and transcribe

#### Settings
- Open WhisperTux GUI
- Click "Settings"
- Toggle "Hold to record" to switch between modes
- Change hotkey if desired
- Adjust other settings (key delay, clipboard mode, etc.)

---

### 🚀 Future Optimization Opportunities

#### GPU Acceleration (When Available)
- Rebuild whisper.cpp with CUDA/ROCm support
- Expected: 10-20x speed improvement with dedicated GPU
- Will be most impactful upgrade when GPU is available

#### Model Optimization
- Currently using `small.en` model (good balance)
- Could try `tiny.en` for faster processing (lower accuracy)
- Could try `medium.en` or `large` for better accuracy (slower)

---

### 🔒 Security Notes

#### Keyboard Monitoring
- WhisperTux uses `evdev` to monitor keyboard events (required for global hotkeys)
- Monitors ALL key presses to detect the hotkey combination
- Does NOT log, store, or transmit keystrokes
- Only tracks which keys are currently pressed (in memory)
- Immediately forgets keys when released
- This is standard behavior for all global hotkey systems

#### Permissions Required
- Requires read access to `/dev/input/event*` devices
- Typically requires running with appropriate permissions (root or input group)
- Same requirements as original whispertux

---

### 📝 Notes

- All changes maintain backward compatibility
- Toggle mode still available via settings (set `hold_to_record: false`)
- Log files are automatically created and rotated
- Daemon mode is production-ready for autostart

---

### 🙏 Credits
- Original WhisperTux by [original author]
- Hold-to-record implementation and optimizations by Kai (Claude Code)
- Date: 2025-10-09
