"""
Configuration manager for WhisperTux
Handles loading, saving, and managing application settings
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional


class ConfigManager:
    """Manages application configuration and settings"""
    
    def __init__(self):
        # Default configuration values
        self.default_config = {
            'primary_shortcut': 'F12',
            'model': 'base',
            'typing_speed': 150,
            'use_clipboard': False,
            'window_position': None,
            'always_on_top': True,
            'theme': 'darkly',
            'audio_device': None  # None means use system default
        }
        
        # Set up config directory and file path
        self.config_dir = Path.home() / '.config' / 'whispertux'
        self.config_file = self.config_dir / 'config.json'
        
        # Current configuration (starts with defaults)
        self.config = self.default_config.copy()
        
        # Ensure config directory exists
        self._ensure_config_dir()
        
        # Load existing configuration
        self._load_config()
    
    def _ensure_config_dir(self):
        """Ensure the configuration directory exists"""
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            try:
                from .logger import log_warning
                log_warning(f"Could not create config directory: {e}", "CONFIG")
            except ImportError:
                print(f"Warning: Could not create config directory: {e}")
    
    def _load_config(self):
        """Load configuration from file"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    loaded_config = json.load(f)
                    
                # Merge loaded config with defaults (preserving any new default keys)
                self.config.update(loaded_config)
                print(f"Configuration loaded from {self.config_file}")
            else:
                print("No existing configuration found, using defaults")
                # Save default configuration
                self.save_config()
                
        except Exception as e:
            print(f"Warning: Could not load configuration: {e}")
            print("Using default configuration")
    
    def save_config(self) -> bool:
        """Save current configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            print(f"Configuration saved to {self.config_file}")
            return True
        except Exception as e:
            print(f"Error: Could not save configuration: {e}")
            return False
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a configuration setting"""
        return self.config.get(key, default)
    
    def set_setting(self, key: str, value: Any):
        """Set a configuration setting"""
        self.config[key] = value
    
    def get_all_settings(self) -> Dict[str, Any]:
        """Get all configuration settings"""
        return self.config.copy()
    
    def reset_to_defaults(self):
        """Reset configuration to default values"""
        self.config = self.default_config.copy()
        print("Configuration reset to defaults")
    
    def update_shortcuts(self, primary: Optional[str] = None, secondary: Optional[str] = None):
        """Update shortcut configuration"""
        if primary is not None:
            self.config['primary_shortcut'] = primary
            
        return self.save_config()
    
    def get_whisper_model_path(self, model_name: str) -> Path:
        """Get the path to a whisper model file"""
        # Construct path relative to the project root
        project_root = Path(__file__).parent.parent
        
        # Handle different model naming conventions
        if model_name.endswith('.en'):
            # English-only model
            model_filename = f"ggml-{model_name}.bin"
        else:
            # Multilingual model - check both .en.bin and .bin versions
            en_model_path = project_root / "whisper.cpp" / "models" / f"ggml-{model_name}.en.bin"
            multi_model_path = project_root / "whisper.cpp" / "models" / f"ggml-{model_name}.bin"
            
            # Prefer English-only version if both exist
            if en_model_path.exists():
                return en_model_path
            elif multi_model_path.exists():
                return multi_model_path
            else:
                # Default to English-only path for error messages
                return en_model_path
        
        model_path = project_root / "whisper.cpp" / "models" / model_filename
        return model_path
    
    def get_whisper_binary_path(self) -> Path:
        """Get the path to the whisper binary"""
        project_root = Path(__file__).parent.parent
        # Check a few possible locations for the whisper binary
        possible_paths = [
            project_root / "whisper.cpp" / "build" / "bin" / "whisper-cli",
            project_root / "whisper.cpp" / "main",
            project_root / "whisper.cpp" / "whisper"
        ]
        
        for path in possible_paths:
            if path.exists():
                return path
                
        # Return the most likely path even if it doesn't exist yet
        return possible_paths[0]
    
    def get_temp_directory(self) -> Path:
        """Get the temporary directory for audio files"""
        temp_dir = Path(__file__).parent.parent / "temp"
        temp_dir.mkdir(exist_ok=True)
        return temp_dir
