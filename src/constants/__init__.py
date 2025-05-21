
"""
Constants package initialization
Import all constants for easy access
"""

from src.constants.constants import (
    MODEL_TYPES,
    FILE_EXTENSIONS,
    DOWNLOAD_STATUS,
    DEFAULT_SETTINGS
)

from src.constants.theme import (
    DARK_THEME,
    LIGHT_THEME,
    get_theme
)

# Add missing application constants
from src.constants.application import (
    APP_NAME,
    APP_VERSION,
    API_BASE_URL,
    USER_AGENT,
    CACHE_DIR,
    REQUEST_TIMEOUT,
    MAX_RETRY_COUNT,
    API_RATE_LIMIT
)
