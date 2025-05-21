
"""
Constants used throughout the application
"""

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

# File extensions by type
FILE_EXTENSIONS = {
    "model": [".safetensors", ".ckpt", ".pt", ".pth", ".bin"],
    "image": [".png", ".jpg", ".jpeg", ".webp", ".avif", ".gif"],
    "video": [".mp4", ".webm", ".mov"],
    "text": [".txt", ".json", ".html", ".md"],
    "archive": [".zip", ".7z", ".rar", ".tar", ".gz"]
}

# Download status values
DOWNLOAD_STATUS = {
    "QUEUED": "queued",
    "DOWNLOADING": "downloading",
    "COMPLETED": "completed",
    "FAILED": "failed",
    "CANCELED": "canceled"
}

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
