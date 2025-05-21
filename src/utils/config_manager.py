
import json
import os
from pathlib import Path
from typing import Dict, Any

from src.utils.logger import get_logger

logger = get_logger(__name__)

class ConfigManager:
    """Manages application configuration"""
    
    def __init__(self):
        """Initialize configuration manager"""
        # Set up config directory
        self.config_dir = Path.home() / ".civitai_manager"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Config file path
        self.config_path = self.config_dir / "config.json"
        
        # Default configuration
        self.default_config = {
            "theme": "dark",
            "comfy_path": "",
            "download_path": str(self.config_dir / "downloads"),
            "top_image_count": 9,
            "download_model": True,
            "download_images": True,
            "download_nsfw": True,
            "create_html": True,
            "auto_open_html": False,
            "api_key": "",
            "download_threads": 3,
            "fetch_batch_size": 100,
            "log_level": "info"
        }
        
        # Load or create configuration
        self.config = self.load_config()
        
        # Create download directory if it doesn't exist
        download_path = Path(self.config.get("download_path", self.default_config["download_path"]))
        download_path.mkdir(parents=True, exist_ok=True)
        
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                logger.info("Configuration loaded successfully")
                
                # Ensure all default values are present
                for key, value in self.default_config.items():
                    if key not in config:
                        config[key] = value
                        
                return config
            except Exception as e:
                logger.error(f"Error loading configuration: {e}")
                return self.default_config.copy()
        else:
            logger.info("Configuration file not found, using defaults")
            self.save_config(self.default_config)
            return self.default_config.copy()
    
    def save_config(self, config=None) -> bool:
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
    
    def set(self, key, value) -> bool:
        """Set configuration value and save"""
        self.config[key] = value
        return self.save_config()
