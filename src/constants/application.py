
"""
Application-wide constants
"""

import os
import platform
from pathlib import Path

# Application identity
APP_NAME = "CivitAI Manager"
APP_VERSION = "1.0.0"

# API configuration
API_BASE_URL = "https://civitai.com/api/v1"
USER_AGENT = f"{APP_NAME}/{APP_VERSION} ({platform.system()}; {platform.release()})"

# Request configuration
REQUEST_TIMEOUT = 30  # seconds
MAX_RETRY_COUNT = 3  # maximum number of retry attempts
API_RATE_LIMIT = 2   # requests per second

# Paths and directories
HOME_DIR = Path.home()
CACHE_DIR = HOME_DIR / ".civitai_manager" / "cache"

# Ensure cache directory exists
os.makedirs(CACHE_DIR, exist_ok=True)

# Import after defining the above constants to avoid circular imports
from src.constants.constants import MODEL_TYPES

# Ratings and filtering
NSFW_LEVELS = {
    "NONE": 0,     # No mature content
    "SOFT": 1,     # Suggestive content
    "MATURE": 2,   # Mature content
    "X": 3         # Explicit content
}

# Model sorting options
SORT_OPTIONS = {
    "Highest Rated": "Highest Rated",
    "Most Downloaded": "Most Downloaded",
    "Newest": "Newest", 
    "Most Liked": "Most Liked"
}

# Filter options
FILTER_OPTIONS = {
    "type": list(MODEL_TYPES.keys()),
    "nsfw_allowed": [True, False],
    "sort": list(SORT_OPTIONS.keys())
}

# Image formats for preview and thumbnails
IMAGE_FORMATS = {
    "preview": "webp",
    "thumbnail": "jpg"
}

# Thumbnail sizes
THUMBNAIL_SIZES = {
    "small": 100,
    "medium": 256,
    "large": 512
}

# Context menu actions
CONTEXT_MENU_ACTIONS = {
    "VIEW_DETAILS": "View Details",
    "DOWNLOAD": "Download",
    "OPEN_FOLDER": "Open Folder",
    "COPY_PATH": "Copy Path",
    "DELETE": "Delete"
}

# Status message types
STATUS_MESSAGE_TYPES = {
    "INFO": "info",
    "SUCCESS": "success",
    "WARNING": "warning",
    "ERROR": "error",
    "DOWNLOAD": "download"
}
