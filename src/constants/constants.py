
"""
Constants for the application
"""
from src.constants.theme import DARK_THEME, LIGHT_THEME
# Download status
DOWNLOAD_STATUS = {
    "QUEUED": "queued",
    "DOWNLOADING": "downloading",
    "COMPLETED": "completed",
    "FAILED": "failed",
    "CANCELED": "canceled"
}

# Model types
MODEL_TYPES = {
    "Checkpoint": "checkpoints",
    "LORA": "loras",
    "LoCon": "locons",
    "TextualInversion": "embeddings",
    "Hypernetwork": "hypernetworks",
    "AestheticGradient": "aesthetics",
    "MotionModule": "motionmodules",
    "VAE": "vae",
    "Upscaler": "upscalers",
    "ControlNet": "controlnet",
    "Poses": "poses",
    "Wildcards": "wildcards",
    "Workflows": "workflows",
    "Other": "others"
}

# Base models
BASE_MODELS = [
    "SD 1.5",
    "SD 2.0",
    "SD 2.1",
    "SDXL 1.0",
    "SDXL Turbo",
    "Stable Cascade",
    "PixArt Σ",
    "Stable Video Diffusion",
    "PDXL",
    "Illustrious",
    "Other"
]

# Supported image formats
IMAGE_FORMATS = [".png", ".jpg", ".jpeg", ".webp", ".gif"]

# Supported video formats
VIDEO_FORMATS = [".mp4", ".webm", ".mkv"]

# Application name
APP_NAME = "Civitai Model Manager"

# Application version
APP_VERSION = "2.0"

# Organization name
ORG_NAME = "CivitaiManager"

# Maximum concurrent downloads
MAX_CONCURRENT_DOWNLOADS = 3

# Default ComfyUI folder structure paths
DEFAULT_PATHS = {
    "checkpoints": "models/checkpoints",
    "loras": "models/loras",
    "locons": "models/loras",
    "embeddings": "models/embeddings",
    "hypernetworks": "models/hypernetworks",
    "aesthetics": "models/aesthetic_embeddings",
    "controlnet": "models/controlnet",
    "vae": "models/vae",
    "upscalers": "models/upscalers",
    "poses": "models/poses",
    "motionmodules": "models/motion",
    "wildcards": "wildcards",
    "workflows": "workflows",
    "others": "models/other"
}

# Cache expiration time (in seconds)
CACHE_EXPIRATION = 86400  # 24 hours

# Image thumbnails size
THUMBNAIL_SIZE = (256, 256)

# Gallery columns default
DEFAULT_GALLERY_COLUMNS = 4

# Gallery view modes
VIEW_MODE = {
    "CARD": "card",
    "LIST": "list"
}

# Sort options
SORT_OPTIONS = {
    "DATE": "date",
    "NAME": "name",
    "SIZE": "size",
    "TYPE": "type",
    "RATING": "rating"
}

# Filter options
FILTER_NSFW = {
    "ALL": "all",
    "HIDE": "hide",
    "ONLY": "only"
}

# Batch operations
BATCH_OPERATIONS = {
    "DELETE": "delete",
    "EXPORT": "export",
    "MOVE": "move"
}

FILE_EXTENSIONS = {
    "model": [".ckpt", ".safetensors", ".pt", ".pth"],
    "image": IMAGE_FORMATS,
    "video": VIDEO_FORMATS,
    "json": [".json"],
    "txt": [".txt"],
    "zip": [".zip", ".rar"]
}

APP_THEMES = {
    "dark": DARK_THEME,
    "light": LIGHT_THEME
}