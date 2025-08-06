#!/usr/bin/env python3
"""
Complete setup script for WhisperTux
Handles all dependencies, builds whisper.cpp, sets up services, and configures the application
"""

import sys
import subprocess
import os
import shutil
from pathlib import Path
import urllib.request
import platform

# Import rich logging after checking if it's available
try:
    from src.logger import logger, log_step, log_success, log_error, log_warning, log_info
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    # Fallback to plain print for initial setup
    class DummyLogger:
        def step(self, msg, prefix="SETUP"): print(f"[{prefix}] → {msg}")
        def success(self, msg, prefix="SETUP"): print(f"[{prefix}] ✓ {msg}")
        def error(self, msg, prefix="SETUP"): print(f"[{prefix}] ✗ {msg}")
        def warning(self, msg, prefix="SETUP"): print(f"[{prefix}] ⚠ {msg}")
        def info(self, msg, prefix="SETUP"): print(f"[{prefix}] {msg}")
        def header(self, title, subtitle=None): print(f"\n=== {title} ===\n{subtitle or ''}")
        def section(self, title): print(f"\n=== {title} ===")

    logger = DummyLogger()


def run_command(cmd, description, check=True, capture_output=True):
    """Run a shell command with error handling"""
    logger.step(description, "SETUP")
    try:
        if isinstance(cmd, str):
            if capture_output:
                result = subprocess.run(cmd, shell=True, check=check, capture_output=True, text=True)
            else:
                result = subprocess.run(cmd, shell=True, check=check, text=True)
        else:
            if capture_output:
                result = subprocess.run(cmd, check=check, capture_output=True, text=True)
            else:
                result = subprocess.run(cmd, check=check, text=True)

        if capture_output and result.stdout and result.stdout.strip():
            logger.info(result.stdout.strip(), "OUTPUT")

        if check and result.returncode == 0:
            logger.success(f"{description} completed successfully", "SETUP")
        elif not check:
            logger.info(f"Command completed with return code: {result.returncode}", "SETUP")

        return result.returncode == 0

    except subprocess.CalledProcessError as e:
        logger.error(f"{description} failed: {e}", "SETUP")
        if capture_output and e.stderr:
            logger.error(f"Error: {e.stderr.strip()}", "SETUP")
        return False
    except Exception as e:
        logger.error(f"{description} failed: {e}", "SETUP")
        return False


def check_os_compatibility():
    """Check if running on supported OS"""
    logger.step("Checking operating system compatibility", "SETUP")
    if not sys.platform.startswith('linux'):
        logger.error("This application is designed for Linux systems only", "SETUP")
        return False

    # Detect distribution
    try:
        with open('/etc/os-release', 'r') as f:
            content = f.read()
            if 'ubuntu' in content.lower() or 'debian' in content.lower():
                distro = 'debian'
            elif 'fedora' in content.lower() or 'centos' in content.lower() or 'rhel' in content.lower():
                distro = 'fedora'
            elif 'arch' in content.lower():
                distro = 'arch'
            else:
                distro = 'unknown'
    except:
        distro = 'unknown'

    logger.success(f"Running on Linux ({distro} family)", "SETUP")
    return distro


def check_python_version():
    """Check if Python version is adequate"""
    logger.step("Checking Python version", "SETUP")
    if sys.version_info < (3, 8):
        logger.error("Python 3.8+ is required", "SETUP")
        return False
    logger.success(f"Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro} found", "SETUP")
    return True


def install_system_dependencies(distro):
    """Install required system dependencies"""
    logger.step("Installing system dependencies", "SETUP")

    if distro == 'debian':
        packages = [
            'python3-pip', 'python3-dev', 'python3-venv',
            'portaudio19-dev', 'ydotool',
            'build-essential', 'cmake', 'git',
            'libasound2-dev', 'pkg-config'
        ]
        cmd = f"sudo apt update && sudo apt install -y {' '.join(packages)}"

    elif distro == 'fedora':
        packages = [
            'python3-pip', 'python3-devel',
            'portaudio-devel', 'ydotool',
            'gcc', 'gcc-c++', 'cmake', 'git',
            'alsa-lib-devel', 'pkg-config'
        ]
        cmd = f"sudo dnf install -y {' '.join(packages)}"

    elif distro == 'arch':
        packages = [
            'python-pip', 'python-dev-tools',
            'portaudio', 'ydotool',
            'base-devel', 'cmake', 'git',
            'alsa-lib', 'pkg-config'
        ]
        cmd = f"sudo pacman -S --noconfirm {' '.join(packages)}"

    else:
        logger.warning("Unknown distribution. Please install manually:", "SETUP")
        logger.info("- Python 3.8+ with pip and dev headers", "MANUAL")
        logger.info("- portaudio development files", "MANUAL")
        logger.info("- ydotool", "MANUAL")
        logger.info("- build-essential, cmake, git", "MANUAL")
        return False

    return run_command(cmd, "Installing system packages", capture_output=False)


def setup_user_groups():
    """Add current user to audio and input groups for non-root access"""
    logger.step("Adding user to audio and input groups", "SETUP")
    
    import getpass
    current_user = getpass.getuser()
    
    # Commands to add user to necessary groups
    commands = [
        f"sudo usermod -a -G audio {current_user}",
        f"sudo usermod -a -G input {current_user}"
    ]
    
    success = True
    for cmd in commands:
        group_name = cmd.split()[-2]  # Extract group name from command
        if not run_command(cmd, f"Adding user to {group_name} group"):
            logger.warning(f"Failed to add user to {group_name} group", "SETUP")
            success = False
        else:
            logger.success(f"Added user '{current_user}' to {group_name} group", "SETUP")
    
    if success:
        logger.info("User groups updated. You may need to log out and log back in for changes to take effect.", "SETUP")
        logger.info("After relogging, WhisperTux should work without root privileges.", "SETUP")
    
    return success


def setup_ydotoold_service():
    """Set up and enable ydotoold service"""
    logger.step("Setting up ydotoold service", "SETUP")

    # Create service file
    service_content = """[Unit]
Description=ydotool daemon
Documentation=man:ydotoold(8)
Wants=systemd-udev-settle.service
After=systemd-udev-settle.service

[Service]
Type=simple
Restart=always
ExecStart=/usr/bin/ydotoold
ExecReload=/bin/kill -HUP $MAINPID
KillMode=process
TimeoutSec=180

[Install]
WantedBy=multi-user.target
"""

    service_file = Path(__file__).parent / "ydotoold.service"
    with open(service_file, 'w') as f:
        f.write(service_content)

    # Install and enable service
    commands = [
        f"sudo cp {service_file} /etc/systemd/system/",
        "sudo systemctl daemon-reload",
        "sudo systemctl enable ydotoold",
        "sudo systemctl start ydotoold"
    ]

    for cmd in commands:
        if not run_command(cmd, f"Service setup: {cmd.split()[-1]}"):
            logger.warning("ydotoold service setup failed - text injection may not work optimally", "SETUP")
            return False

    return True


def build_whisper_cpp():
    """Build whisper.cpp from source"""
    logger.step("Building whisper.cpp", "SETUP")

    project_root = Path(__file__).parent
    whisper_dir = project_root / "whisper.cpp"

    # Clone whisper.cpp if not present
    if not whisper_dir.exists():
        logger.info("Cloning whisper.cpp repository...", "BUILD")
        if not run_command(
            f"git clone https://github.com/ggerganov/whisper.cpp.git {whisper_dir}",
            "Cloning whisper.cpp"
        ):
            return False

    # Build whisper.cpp
    build_commands = [
        f"cd {whisper_dir} && mkdir -p build",
        f"cd {whisper_dir}/build && cmake ..",
        f"cd {whisper_dir}/build && make -j$(nproc)"
    ]

    for cmd in build_commands:
        if not run_command(cmd, f"Building: {cmd.split('&&')[-1].strip()}", capture_output=False):
            return False

    # Verify binary was created
    binary_path = whisper_dir / "build" / "bin" / "whisper-cli"
    if not binary_path.exists():
        # Try alternative location
        binary_path = whisper_dir / "main"
        if not binary_path.exists():
            logger.error("whisper binary not found after build", "BUILD")
            return False

    logger.success(f"whisper.cpp built successfully at {binary_path}", "BUILD")
    return True


def download_whisper_models():
    """Download whisper models"""
    logger.step("Downloading whisper models", "SETUP")

    project_root = Path(__file__).parent
    models_dir = project_root / "whisper.cpp" / "models"
    models_dir.mkdir(exist_ok=True)

    # Download models using whisper.cpp script
    script_path = models_dir / "download-ggml-model.sh"

    if not script_path.exists():
        logger.warning("Model download script not found, trying alternative method...", "MODELS")
        # Alternative: download models directly
        models = ['base.en']
        base_url = "https://huggingface.co/ggerganov/whisper.cpp/resolve/main"

        for model in models:
            model_file = models_dir / f"ggml-{model}.bin"
            if not model_file.exists():
                url = f"{base_url}/ggml-{model}.bin"
                logger.info(f"Downloading {model} model...", "MODELS")
                try:
                    urllib.request.urlretrieve(url, model_file)
                    logger.success(f"Downloaded {model} model", "MODELS")
                except Exception as e:
                    logger.error(f"Failed to download {model} model: {e}", "MODELS")
                    return False
    else:
        # Use the official download script
        if not run_command(
            f"cd {models_dir} && bash download-ggml-model.sh base.en",
            "Downloading base.en model",
            capture_output=False
        ):
            return False

    return True


def setup_virtual_environment():
    """Set up Python virtual environment and install dependencies"""
    logger.step("Setting up Python virtual environment", "SETUP")

    project_root = Path(__file__).parent
    venv_path = project_root / "venv"
    requirements_file = project_root / "requirements.txt"

    if not requirements_file.exists():
        logger.error("requirements.txt not found", "SETUP")
        return False

    # Create virtual environment
    if not venv_path.exists():
        logger.info("Creating virtual environment...", "VENV")
        if not run_command([sys.executable, "-m", "venv", str(venv_path)], "Creating virtual environment"):
            return False
    else:
        logger.info("Virtual environment already exists", "VENV")

    # Determine paths for venv
    if platform.system() == "Windows":
        venv_python = venv_path / "Scripts" / "python.exe"
        venv_pip = venv_path / "Scripts" / "pip.exe"
    else:
        venv_python = venv_path / "bin" / "python"
        venv_pip = venv_path / "bin" / "pip"

    # Upgrade pip in virtual environment
    logger.info("Upgrading pip in virtual environment...", "VENV")
    if not run_command([str(venv_python), "-m", "pip", "install", "--upgrade", "pip"], "Upgrading pip"):
        logger.warning("Failed to upgrade pip, continuing...", "VENV")

    # Install requirements in virtual environment
    logger.info("Installing Python packages in virtual environment...", "VENV")
    if not run_command([str(venv_pip), "install", "-r", str(requirements_file)], "Installing Python packages"):
        return False

    logger.success(f"Virtual environment set up at {venv_path}", "VENV")
    return True


def install_python_dependencies():
    """Install Python dependencies using virtual environment"""
    return setup_virtual_environment()


def setup_configuration():
    """Set up initial configuration"""
    logger.step("Setting up configuration", "SETUP")

    try:
        from src.config_manager import ConfigManager
        config = ConfigManager()

        # This will create the config directory and default config file
        config.save_config()
        logger.success(f"Configuration created at {config.config_file}", "CONFIG")
        return True

    except Exception as e:
        logger.error(f"Failed to setup configuration: {e}", "CONFIG")
        return False


def run_system_tests():
    """Run comprehensive system tests using virtual environment"""
    logger.section("Running System Tests")

    tests_passed = 0
    total_tests = 4

    project_root = Path(__file__).parent
    venv_python = project_root / "venv" / "bin" / "python"

    # Test audio system
    logger.step("Testing audio system", "TEST")
    test_code = """
try:
    import sys
    sys.path.insert(0, '.')
    from src.audio_capture import AudioCapture
    audio = AudioCapture()
    if audio.is_available():
        print("PASS: Audio system is working")
    else:
        print("FAIL: Audio system not available")
except Exception as e:
    print(f"FAIL: Audio system test failed: {e}")
"""
    
    try:
        result = subprocess.run([str(venv_python), "-c", test_code], 
                               capture_output=True, text=True, cwd=project_root)
        if "PASS:" in result.stdout:
            logger.success("Audio system is working", "TEST")
            tests_passed += 1
        else:
            logger.error("Audio system not available", "TEST")
            if result.stdout.strip():
                logger.info(result.stdout.strip(), "TEST")
    except Exception as e:
        logger.error(f"Audio system test failed: {e}", "TEST")

    # Test whisper.cpp
    logger.step("Testing whisper.cpp", "TEST")
    test_code = """
try:
    import sys
    sys.path.insert(0, '.')
    from src.whisper_manager import WhisperManager
    whisper = WhisperManager()
    if whisper.initialize():
        available_models = whisper.get_available_models()
        print(f"PASS: Whisper.cpp is working. Available models: {', '.join(available_models) if available_models else 'none'}")
    else:
        print("FAIL: Whisper.cpp initialization failed")
except Exception as e:
    print(f"FAIL: Whisper test failed: {e}")
"""
    
    try:
        result = subprocess.run([str(venv_python), "-c", test_code], 
                               capture_output=True, text=True, cwd=project_root)
        if "PASS:" in result.stdout:
            logger.success("Whisper.cpp is working", "TEST")
            if "Available models:" in result.stdout:
                models_info = result.stdout.split("Available models:")[1].strip()
                logger.info(f"Available models: {models_info}", "TEST")
            tests_passed += 1
        else:
            logger.error("Whisper.cpp initialization failed", "TEST")
            if result.stdout.strip():
                logger.info(result.stdout.strip(), "TEST")
    except Exception as e:
        logger.error(f"Whisper test failed: {e}", "TEST")

    # Test global shortcuts
    logger.step("Testing global shortcuts", "TEST")
    test_code = """
try:
    import sys
    sys.path.insert(0, '.')
    from src.global_shortcuts import GlobalShortcuts
    # Basic test - just try to import and create
    gs = GlobalShortcuts('<f12>', lambda: None)
    print("PASS: Global shortcuts should work")
except Exception as e:
    print(f"FAIL: Global shortcuts test failed: {e}")
"""
    
    try:
        result = subprocess.run([str(venv_python), "-c", test_code], 
                               capture_output=True, text=True, cwd=project_root)
        if "PASS:" in result.stdout:
            logger.success("Global shortcuts should work", "TEST")
            tests_passed += 1
        else:
            logger.warning("Global shortcuts may not work properly", "TEST")
            logger.info("This might be due to desktop environment restrictions", "TEST")
            if result.stdout.strip():
                logger.info(result.stdout.strip(), "TEST")
    except Exception as e:
        logger.error(f"Global shortcuts test failed: {e}", "TEST")

    # Test text injection
    logger.step("Testing text injection", "TEST")
    test_code = """
try:
    import sys
    sys.path.insert(0, '.')
    from src.text_injector import TextInjector
    injector = TextInjector()
    status = injector.get_status()
    if status['ydotool_available']:
        print("PASS: Text injection (ydotool) is available")
    else:
        print("WARN: ydotool not available - will use clipboard fallback")
except Exception as e:
    print(f"FAIL: Text injection test failed: {e}")
"""
    
    try:
        result = subprocess.run([str(venv_python), "-c", test_code], 
                               capture_output=True, text=True, cwd=project_root)
        if "PASS:" in result.stdout:
            logger.success("Text injection (ydotool) is available", "TEST")
            tests_passed += 1
        elif "WARN:" in result.stdout:
            logger.warning("ydotool not available - will use clipboard fallback", "TEST")
            logger.info("Text injection may require manual paste (Ctrl+V)", "TEST")
            tests_passed += 1  # Still count as working
        else:
            logger.error("Text injection test failed", "TEST")
            if result.stdout.strip():
                logger.info(result.stdout.strip(), "TEST")
    except Exception as e:
        logger.error(f"Text injection test failed: {e}", "TEST")

    return tests_passed, total_tests


def create_launcher_script():
    """Create a convenient launcher script"""
    logger.step("Creating launcher script", "SETUP")

    project_root = Path(__file__).parent
    launcher_script = project_root / "whispertux"
    venv_python = project_root / "venv" / "bin" / "python"

    script_content = f"""#!/bin/bash
# WhisperTux Launcher Script
cd "{project_root}"

# Check if virtual environment exists
if [ -f "{venv_python}" ]; then
    "{venv_python}" main.py "$@"
else
    echo "Error: Virtual environment not found. Please run setup.py first."
    echo "python3 setup.py"
    exit 1
fi
"""

    with open(launcher_script, 'w') as f:
        f.write(script_content)

    os.chmod(launcher_script, 0o755)
    logger.success(f"Launcher script created: {launcher_script}", "SETUP")
    logger.info("You can run WhisperTux with: ./whispertux", "SETUP")
    logger.info("Virtual environment will be used automatically", "SETUP")

    return True


def main():
    """Main setup function"""
    logger.header("WhisperTux Setup",
                  "This will install all dependencies, build whisper.cpp, and set up services.")

    # Detect OS
    distro = check_os_compatibility()
    if not distro:
        sys.exit(1)

    # Check Python
    if not check_python_version():
        sys.exit(1)

    # Install system dependencies
    logger.section(f"Installing system dependencies for {distro} system")
    if not install_system_dependencies(distro):
        logger.warning("Please install system dependencies manually and re-run this script", "SETUP")
        # Don't exit - continue with other setup steps

    # Set up user groups for non-root access
    logger.section("Setting up user permissions")
    setup_user_groups()  # Don't fail if this doesn't work

    # Set up ydotoold service
    logger.section("Setting up ydotoold service")
    setup_ydotoold_service()  # Don't fail if this doesn't work

    # Build whisper.cpp
    logger.section("Building whisper.cpp")
    if not build_whisper_cpp():
        logger.error("Failed to build whisper.cpp - speech recognition won't work", "BUILD")
        logger.info("You may need to install build dependencies manually", "BUILD")
        # Don't exit - let user see what else works

    # Download models
    logger.section("Downloading whisper models")
    if not download_whisper_models():
        logger.error("Failed to download whisper models", "MODELS")
        logger.info("You can try downloading them manually later", "MODELS")

    # Install Python dependencies
    logger.section("Installing Python dependencies")
    if not install_python_dependencies():
        logger.error("Failed to install Python dependencies", "SETUP")
        sys.exit(1)

    # Set up configuration
    logger.section("Setting up configuration")
    if not setup_configuration():
        logger.error("Failed to setup configuration", "CONFIG")
        sys.exit(1)

    # Create launcher
    create_launcher_script()

    # Run tests
    tests_passed, total_tests = run_system_tests()

    # Final results
    logger.section("Setup Complete!")

    logger.info(f"Tests passed: {tests_passed}/{total_tests}", "RESULT")

    if tests_passed >= 3:
        logger.success("WhisperTux is ready to use!", "RESULT")
        logger.info("To start the application:", "USAGE")
        logger.info("  ./whispertux", "USAGE")
        logger.info("  or: python3 main.py", "USAGE")
        logger.info("Usage:", "HELP")
        logger.info("  - Press F12 to start/stop voice recording", "HELP")
        logger.info("  - Speak clearly and transcribed text will appear in focused app", "HELP")
        logger.info("  - Check settings in the GUI for model selection and shortcuts", "HELP")

    else:
        logger.warning("Setup completed but some features may not work properly", "RESULT")
        logger.info("Check the test results above and install missing dependencies", "RESULT")
        logger.info("You can still try to run the application:", "USAGE")
        logger.info("  python3 main.py", "USAGE")

    if tests_passed < total_tests:
        logger.info("Troubleshooting:", "HELP")
        if distro == 'unknown':
            logger.info("  - Install missing system packages manually for your distribution", "HELP")
        logger.info("  - For Wayland users: Switch to X11 for better global shortcut support", "HELP")
        logger.info("  - Run 'systemctl --user status ydotoold' to check ydotool service", "HELP")


if __name__ == "__main__":
    main()
