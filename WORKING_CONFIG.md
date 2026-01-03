# WhisperTux Working Configuration

> **Note:** This document shares a real-world optimized configuration for WhisperTux on AMD Ryzen 7 8845HS. Your optimal settings may differ based on your hardware. Use this as a reference for performance tuning on your system.

**Date:** 2025-10-21 17:16 (FINAL)
**Status:** ⚡ BLAZING FAST - Optimized to 1 second transcription on test hardware

## Current Configuration

### whisper.cpp
- **Version:** Latest master (commit 23c19308 - post v1.8.2)
- **Build Flags:**
  - `CMAKE_BUILD_TYPE=Release`
  - `GGML_NATIVE=ON` (enables -march=native, all CPU features including AVX-512)
  - `GGML_OPENMP=ON` (threading enabled)
- **Binary:** `/home/e/opt/wispr-tux2/whisper.cpp/build/bin/whisper-cli`

### Model
- **Model:** base.en (FINAL CHOICE)
- **Size:** 148MB
- **Location:** `/home/e/.local/share/ai-models/whisper/ggml-base.en.bin`
- **Symlink:** `/home/e/opt/wispr-tux2/whisper.cpp/models/ggml-base.en.bin`
- **Config:** Set in `~/.config/whispertux/config.json`

### Threading Configuration
- **Threads:** 12 (OPTIMAL - configured in src/whisper_manager.py)
- **Benchmark Results:**
  - 4 threads: 4.4 seconds
  - 8 threads: 3.2 seconds
  - 12 threads: 3.0 seconds ⭐ (with small.en)
  - 16 threads: 19.0 seconds (completely broken)

### Performance
- **JFK Sample (11 seconds audio):** ~1.0 second with base.en + 12 threads ⚡
- **User-reported:** "Blazing fast! Really good and accurate."
- **Status:** FINAL - Fast and accurate enough for technical dictation

### Model Comparison (all with 12 threads)
- **base.en** (148MB): 1.0s ⚡ **USING THIS**
- **small.en** (488MB): 3.0s (better quality, slower)
- **large-v3-turbo** (3GB): 20+ seconds (NOT recommended for CPU)

## Backup Locations
- **FINAL (12 threads):** `~/whispertux-12threads-final.tar.gz`
- **Previous (4 threads):** `~/whispertux-WORKING-4threads-20251021.tar.gz`

Contains:
- whisper.cpp/build directory (compiled binaries)
- src/whisper_manager.py (with thread configuration)

## How to Build from Scratch

```bash
cd /home/e/opt/wispr-tux2

# Remove old whisper.cpp if exists
rm -rf whisper.cpp

# Clone latest whisper.cpp
git clone https://github.com/ggerganov/whisper.cpp.git
cd whisper.cpp

# Build with native optimizations
mkdir -p build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release -DGGML_NATIVE=ON -DGGML_OPENMP=ON
make -j$(nproc)

# Verify binary
./bin/whisper-cli --help

# Create model symlink
cd ../models
ln -sf /home/e/.local/share/ai-models/whisper/ggml-small.en.bin .
```

## whisper_manager.py Configuration

File: `/home/e/opt/wispr-tux2/src/whisper_manager.py`

Key settings (around line 147):
```python
'--threads', '4',  # Optimal thread count - more causes cache thrashing
'--no-prints',     # Reduce overhead from printing progress
'--no-timestamps'  # Faster processing without timestamps
```

## Known Issues & Notes

1. **Not as fast as original:** User reports it was faster before (likely with old whisper.cpp version + 16 threads)
2. **Thread count mystery:** 16 threads worked fine before, but now causes 5-6x slowdown
3. **Lost original working binary:** Conversation rewind broke Claude Code and we lost the working backup
4. **Usable but not ideal:** Current configuration is acceptable for use, but there's room for improvement

## What Changed from "Perfect" State

We don't know the exact original configuration because:
- Conversation rewind broke Claude Code
- Backup that was created was of BROKEN state (after upgrade to v1.8.2)
- Original working whisper.cpp binary was lost

Likely differences:
- Original was probably older whisper.cpp version (exact version unknown)
- Original may have had different build flags
- Original worked fine with 16 threads (current doesn't)

## Next Steps to Improve

If you want to try to get back to "perfect" performance:

1. **Try different whisper.cpp versions:**
   - Could try v1.7.5, v1.7.4, v1.7.3, etc.
   - Original working version is unknown

2. **Experiment with thread counts:**
   - Try 8 threads (middle ground between 4 and 16)
   - Test on actual usage, not just JFK sample

3. **Try different build flags:**
   - Could disable AVX-512 explicitly
   - Try without NATIVE flag and specify exact optimizations

4. **Test with different models:**
   - Current: small.en (v1)
   - Could try: base.en (smaller/faster)

## Restore from Backup

If something breaks, restore this working state:

```bash
cd /home/e/opt/wispr-tux2
rm -rf whisper.cpp
tar -xzf ~/whispertux-WORKING-4threads-20251021.tar.gz
# Recreate model symlink if needed
ln -sf /home/e/.local/share/ai-models/whisper/ggml-small.en.bin whisper.cpp/models/
```

## CPU Information

- **Model:** AMD Ryzen 7 8845HS w/ Radeon 780M Graphics
- **Cores:** 16 (8 physical cores with SMT)
- **AVX-512 Support:** Yes (full support)
- **Features:** avx512f, avx512dq, avx512cd, avx512bw, avx512vl, avx512_bf16, avx512vbmi, avx512_vbmi2, avx512_vnni

## Additional Directories

- `/home/e/opt/whisper.cpp` - Old directory from September 25th (leftover, not used)
- `/home/e/opt/wispr-tux2/whisper.cpp` - Active whisper.cpp installation (current)
