
"""
Configuration manager for ComfyUI Model Manager
"""
import json
import os
from pathlib import Path
import logging

from ComfyUI-MM.constants import CONFIG_DIR, DEFAULT_SETTINGS

# Set up logging
logger = logging.getLogger("config")

class ConfigManager:
    """Configuration manager for the application"""
    
    def __init__(self):
        """Initialize configuration manager"""
        self.config_path = CONFIG_DIR / "config.json"
        self.config = self._load_config()
    
    def _load_config(self):
        """Load configuration from file or create default"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                logger.info("Configuration loaded successfully")
                
                # Ensure all default values are present
                for key, value in DEFAULT_SETTINGS.items():
                    if key not in config:
                        config[key] = value
                        
                return config
            except Exception as e:
                logger.error(f"Error loading configuration: {e}")
                return DEFAULT_SETTINGS.copy()
        else:
            logger.info("Configuration file not found, using defaults")
            self._save_config(DEFAULT_SETTINGS)
            return DEFAULT_SETTINGS.copy()
    
    def _save_config(self, config=None):
        """Save configuration to file"""
        if config is None:
            config = self.config
        
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
            logger.info("Configuration saved successfully")
            return True
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
            return False
    
    def get(self, key, default=None):
        """Get configuration value by key"""
        return self.config.get(key, default)
    
    def set(self, key, value):
        """Set configuration value and save"""
        self.config[key] = value
        return self._save_config()
    
    def save(self):
        """Save current configuration"""
        return self._save_config()
