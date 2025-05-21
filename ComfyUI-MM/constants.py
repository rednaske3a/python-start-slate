
"""
Application-wide constants
"""

import os
import platform
from pathlib import Path
from enum import Enum

# Application identity
APP_NAME = "ComfyUI Model Manager"
APP_VERSION = "1.0.0"
USER_AGENT = f"{APP_NAME}/{APP_VERSION} ({platform.system()}; {platform.release()})"

# API configuration
API_BASE_URL = "https://civitai.com/api/v1"
REQUEST_TIMEOUT = 30  # seconds
MAX_RETRY_COUNT = 3
API_RATE_LIMIT = 2   # requests per second

# Paths and directories
HOME_DIR = Path.home()
CONFIG_DIR = HOME_DIR / ".comfyui_mm"
CACHE_DIR = CONFIG_DIR / "cache"
os.makedirs(CACHE_DIR, exist_ok=True)
os.makedirs(CONFIG_DIR, exist_ok=True)

# Default settings
DEFAULT_SETTINGS = {
    "theme": "dark",
    "comfy_path": "",
    "api_key": "",
    "max_concurrent_downloads": 3,
    "download_threads": 3,
    "download_model": True,
    "download_images": True,
    "download_nsfw": False,
    "create_html": True,
    "auto_open_html": False,
    "top_image_count": 9,
    "default_save_location": "",
    "fetch_batch_size": 100
}

# Download status values
class DownloadStatus(str, Enum):
    QUEUED = "queued"
    DOWNLOADING = "downloading"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"

# Model type to folder path mapping
MODEL_TYPES = {
    "Checkpoint": "models/checkpoints",
    "LORA": "models/lora",
    "LoCon": "models/lora",
    "TextualInversion": "models/embeddings",
    "VAE": "models/vae",
    "Controlnet": "models/controlnet",
    "Upscaler": "models/upscalers",
    "Other": "models/other"
}

# Theme colors
DARK_THEME = {
    "primary": "#121212",          # Background
    "secondary": "#1E1E1E",        # Cards
    "accent": "#BB86FC",           # Interactive elements
    "accent_hover": "#A66DF0",     # Interactive elements hover
    "text": "#FFFFFF",             # Primary text
    "text_secondary": "#B3B3B3",   # Secondary text 
    "success": "#4CAF50",          # Success status
    "warning": "#FFC107",          # Warning status
    "danger": "#F44336",           # Error/danger status
    "border": "#303030",           # Border color
    "input_bg": "#252525",         # Input background
}

LIGHT_THEME = {
    "primary": "#FAFAFA",          # Background
    "secondary": "#F0F0F0",        # Cards
    "accent": "#6200EE",           # Interactive elements
    "accent_hover": "#3700B3",     # Interactive elements hover
    "text": "#121212",             # Primary text
    "text_secondary": "#555555",   # Secondary text
    "success": "#43A047",          # Success status
    "warning": "#FB8C00",          # Warning status
    "danger": "#E53935",           # Error/danger status
    "border": "#DDDDDD",           # Border color
    "input_bg": "#FFFFFF",         # Input background
}

def get_theme(name):
    """Get theme by name"""
    if name.lower() == "dark":
        return DARK_THEME
    else:
        return LIGHT_THEME
