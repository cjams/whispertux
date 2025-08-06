#!/bin/bash

# WhisperTux - Whisper.cpp Build Script
# This script downloads, compiles, and sets up whisper.cpp with the required models

set -e  # Exit on any error

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WHISPER_DIR="$PROJECT_ROOT/whisper.cpp"
MODELS_DIR="$WHISPER_DIR/models"

echo "WhisperTux - Setting up Whisper.cpp"
echo "Project root: $PROJECT_ROOT"

# Check and install dependencies
check_dependencies() {
    echo "Checking dependencies..."

    local missing_deps=()
    local install_commands=()

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
        echo "  - git, make, gcc, g++, curl"
        exit 1
    fi

    echo "Detected package manager: $PKG_MANAGER"

    # Check for git
    if ! command -v git &> /dev/null; then
        echo "WARNING: git not found"
        missing_deps+=("git")
    fi

    # Check for essential build tools (required for whisper.cpp compilation)
    BUILD_TOOLS_MISSING=false
    
    if ! command -v make &> /dev/null; then
        echo "WARNING: make not found (required for whisper.cpp build)"
        BUILD_TOOLS_MISSING=true
    fi
    
    if ! command -v gcc &> /dev/null || ! command -v g++ &> /dev/null; then
        echo "WARNING: gcc/g++ not found (required for whisper.cpp build)"
        BUILD_TOOLS_MISSING=true
    fi
    
    if [ "$BUILD_TOOLS_MISSING" = true ]; then
        if [ "$PKG_MANAGER" = "apt" ]; then
            missing_deps+=("build-essential")
        elif [ "$PKG_MANAGER" = "dnf" ]; then
            missing_deps+=("make" "gcc" "gcc-c++" "pkgconfig")
        elif [ "$PKG_MANAGER" = "pacman" ]; then
            missing_deps+=("base-devel")
        fi
    fi
    
    # Check for cmake (sometimes needed for whisper.cpp)
    if ! command -v cmake &> /dev/null; then
        echo "WARNING: cmake not found (may be needed for whisper.cpp)"
        if [ "$PKG_MANAGER" = "apt" ]; then
            missing_deps+=("cmake")
        elif [ "$PKG_MANAGER" = "dnf" ]; then
            missing_deps+=("cmake")
        elif [ "$PKG_MANAGER" = "pacman" ]; then
            missing_deps+=("cmake")
        fi
    fi

    # Check for curl
    if ! command -v curl &> /dev/null; then
        echo "WARNING: curl not found"
        missing_deps+=("curl")
    fi
    
    # Check for ydotool (required for text injection)
    echo "Checking for ydotool (required for text injection)..."
    if ! command -v ydotool &> /dev/null; then
        echo "WARNING: ydotool not found (required for text injection)"
        missing_deps+=("ydotool")
    fi
    
    # Install missing dependencies (required before building whisper.cpp)
    if [ ${#missing_deps[@]} -gt 0 ]; then
        echo ""
        echo "Missing dependencies required for WhisperTux build:"
        for dep in "${missing_deps[@]}"; do
            echo "   - $dep"
        done
        echo ""
        echo "These dependencies are required for:"
        echo "   - Compiling whisper.cpp from source"
        echo "   - Text injection capabilities (ydotool)"
        echo "   - Downloading models and resources"
        echo ""

        # Ask user permission
        read -p "Install missing dependencies now? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo "Updating package lists..."
            $UPDATE_CMD || true

            echo "Installing dependencies: ${missing_deps[*]}"
            $INSTALL_CMD "${missing_deps[@]}"

            echo "All dependencies installed successfully"
        else
            echo "ERROR: Cannot continue without required build dependencies"
            echo "   Please install manually: ${missing_deps[*]}"
            exit 1
        fi
    else
        echo "All build dependencies found"
    fi

    # Verify critical build tools are now available
    echo "Verifying build environment..."
    VERIFICATION_FAILED=false
    
    if ! command -v git &> /dev/null; then
        echo "ERROR: git still not available"
        VERIFICATION_FAILED=true
    fi
    
    if ! command -v make &> /dev/null; then
        echo "ERROR: make still not available"
        VERIFICATION_FAILED=true
    fi
    
    if ! command -v gcc &> /dev/null || ! command -v g++ &> /dev/null; then
        echo "ERROR: gcc/g++ still not available"
        VERIFICATION_FAILED=true
    fi
    
    if ! command -v curl &> /dev/null; then
        echo "ERROR: curl still not available"
        VERIFICATION_FAILED=true
    fi
    
    if [ "$VERIFICATION_FAILED" = true ]; then
        echo "ERROR: Critical build tools are still missing after installation"
        echo "   Please check your package manager and install manually"
        exit 1
    fi
    
    echo "Build environment verified - ready to compile whisper.cpp"
}

# Clone or update whisper.cpp repository
setup_whisper_repo() {
    echo "Setting up whisper.cpp repository..."

    if [ -d "$WHISPER_DIR" ]; then
        echo "whisper.cpp directory exists, updating..."
        cd "$WHISPER_DIR"
        git pull origin master
    else
        echo "Cloning whisper.cpp repository..."
        cd "$PROJECT_ROOT"
        git clone https://github.com/ggerganov/whisper.cpp.git
        cd "$WHISPER_DIR"
    fi

    echo "Repository ready"
}

# Compile whisper.cpp
compile_whisper() {
    echo "Compiling whisper.cpp..."
    cd "$WHISPER_DIR"

    # Clean previous build
    rm -rf build || true

    # Create build directory and compile using cmake
    mkdir -p build
    cd build
    cmake ..
    make -j$(nproc)

    # Check if whisper-cli binary was created
    if [ ! -f "bin/whisper-cli" ]; then
        echo "ERROR: Failed to compile whisper.cpp binary"
        exit 1
    fi

    echo "whisper.cpp compiled successfully"
}

# Download required models
download_models() {
    echo "Downloading Whisper models..."

    cd "$WHISPER_DIR"

    # Download base.en model using official script
    BASE_MODEL_FILE="$MODELS_DIR/ggml-base.en.bin"
    if [ ! -f "$BASE_MODEL_FILE" ]; then
        echo "Downloading base.en model using official script..."
        sh ./models/download-ggml-model.sh base.en

        if [ ! -f "$BASE_MODEL_FILE" ]; then
            echo "ERROR: Failed to download base.en model"
            exit 1
        fi

        echo "Downloaded base.en model"
    else
        echo "base.en model already exists"
    fi

    # Download small.en model using official script  
    SMALL_MODEL_FILE="$MODELS_DIR/ggml-small.en.bin"
    if [ ! -f "$SMALL_MODEL_FILE" ]; then
        echo "Downloading small.en model using official script..."
        sh ./models/download-ggml-model.sh small.en

        if [ ! -f "$SMALL_MODEL_FILE" ]; then
            echo "ERROR: Failed to download small.en model"
            exit 1
        fi

        echo "Downloaded small.en model"
    else
        echo "small.en model already exists"
    fi

    echo "Models ready"
}

# Test the installation
test_installation() {
    echo "Testing whisper.cpp installation..."

    cd "$WHISPER_DIR"

    # Create a test audio file (silence)
    echo "Creating test audio file..."
    # We'll create a small WAV file with silence for testing
    python3 -c "
import wave
import struct

# Create a 1-second silence WAV file
sample_rate = 16000
duration = 1.0
num_samples = int(sample_rate * duration)

with wave.open('test_audio.wav', 'w') as wav_file:
    wav_file.setnchannels(1)  # mono
    wav_file.setsampwidth(2)  # 16-bit
    wav_file.setframerate(sample_rate)

    # Write silence
    for _ in range(num_samples):
        wav_file.writeframes(struct.pack('<h', 0))

print('Test audio file created')
" 2>/dev/null || echo "Python not available for test audio creation"

    # Test whisper with the model
    if [ -f "test_audio.wav" ]; then
        echo "Testing transcription..."
        ./build/bin/whisper-cli -m "$MODELS_DIR/ggml-base.en.bin" -f test_audio.wav --no-prints --language en
        rm -f test_audio.wav test_audio.wav.txt
        echo "Whisper.cpp test successful"
    else
        echo "WARNING: Skipping audio test (Python not available)"
    fi
}

# Set up directory structure
setup_directories() {
    echo "Setting up project directories..."

    # Create temp directory for audio processing
    mkdir -p "$PROJECT_ROOT/temp"

    echo "Directories created"
}

# Main execution
main() {
    echo "Starting WhisperTux setup..."

    check_dependencies
    setup_whisper_repo
    compile_whisper
    download_models
    test_installation
    setup_directories

    echo ""
    echo "WhisperTux setup complete!"
    echo ""
    echo "Models available:"
    echo "  Base model: $MODELS_DIR/ggml-base.en.bin (good balance)"
    [ -f "$MODELS_DIR/ggml-small.en.bin" ] && echo "  Small model: $MODELS_DIR/ggml-small.en.bin (faster)"
    echo ""
    echo "Global shortcuts:"
    echo "  Ctrl+Shift+V - Toggle voice dictation"
    echo "  F12 - Toggle voice dictation"
}

# Check if script is being run directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
