
"""
Data models for the application
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
import time
import json

class ModelInfo:
    """Class for storing model information"""
    
    def __init__(self, model_id, name, description="", model_type="Other", 
                 base_model="unknown", version_id=None, version_name="", download_url=""):
        self.id = model_id
        self.name = name
        self.description = description
        self.type = model_type
        self.base_model = base_model
        self.version_id = version_id
        self.version_name = version_name
        self.download_url = download_url
        self.tags = []
        self.images = []
        self.nsfw = False
        self.creator = "Unknown"
        self.stats = {}
        self.download_date = ""
        self.last_updated = ""
        self.size = 0
        self.thumbnail = ""
        self.path = ""
    
    def to_dict(self) -> Dict:
        """Convert model info to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "type": self.type,
            "base_model": self.base_model,
            "version_id": self.version_id,
            "version_name": self.version_name,
            "download_url": self.download_url,
            "tags": self.tags,
            "images": self.images,
            "nsfw": self.nsfw,
            "creator": self.creator,
            "stats": self.stats,
            "download_date": self.download_date,
            "last_updated": self.last_updated,
            "size": self.size,
            "thumbnail": self.thumbnail,
            "path": self.path
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ModelInfo':
        """Create model info from dictionary"""
        model = cls(
            model_id=data.get("id", 0),
            name=data.get("name", "Unknown"),
            description=data.get("description", ""),
            model_type=data.get("type", "Other"),
            base_model=data.get("base_model", "unknown"),
            version_id=data.get("version_id"),
            version_name=data.get("version_name", ""),
            download_url=data.get("download_url", "")
        )
        model.tags = data.get("tags", [])
        model.images = data.get("images", [])
        model.nsfw = data.get("nsfw", False)
        model.creator = data.get("creator", "Unknown")
        model.stats = data.get("stats", {})
        model.download_date = data.get("download_date", "")
        model.last_updated = data.get("last_updated", "")
        model.size = data.get("size", 0)
        model.thumbnail = data.get("thumbnail", "")
        model.path = data.get("path", "")
        return model

    def get_highest_rated_images(self, count=9):
        """Get highest rated images based on reactions"""
        if not self.images:
            return []
            
        # Sort images by reaction score
        sorted_images = sorted(
            self.images, 
            key=lambda img: calculate_reaction_score(img.get("stats", {})),
            reverse=True
        )
        
        # Return top N images
        return sorted_images[:count]


class DownloadTask:
    """Class for tracking download tasks"""
    
    def __init__(self, url):
        self.url = url
        self.status = "queued"
        self.model_info = None
        self.model_progress = 0
        self.image_progress = 0
        self.error_message = ""
        self.start_time = 0
        self.end_time = 0
        self.priority = 0  # Lower number = higher priority
    
    def get_duration(self) -> float:
        """Get the duration of the download in seconds"""
        if self.start_time == 0:
            return 0
        if self.end_time == 0:
            return time.time() - self.start_time
        return self.end_time - self.start_time
    
    def get_status_color(self, theme: Dict) -> str:
        """Get the color for the status based on the current theme"""
        if self.status == "completed":
            return theme["success"]
        elif self.status == "failed" or self.status == "canceled":
            return theme["danger"]
        elif self.status == "downloading":
            return theme["accent"]
        else:
            return theme["text_secondary"]


def calculate_reaction_score(stats):
    """Calculate a score based on image reactions"""
    # Weights for different reaction types
    weights = {
        "likeCount": 1.0,
        "heartCount": 1.5,
        "laughCount": 0.8,
        "dislikeCount": -1.0,
        "commentCount": 1.2
    }
    
    score = 0
    for reaction, weight in weights.items():
        score += stats.get(reaction, 0) * weight
        
    return score
