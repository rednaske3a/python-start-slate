
"""
Data class for model information
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime

@dataclass
class ModelInfo:
    """Data class for storing model information"""
    id: int
    name: str
    description: str = ""
    type: str = "Other"
    base_model: str = "unknown"
    version_id: Optional[int] = None
    version_name: str = ""
    download_url: str = ""
    tags: List[str] = field(default_factory=list)
    images: List[Dict] = field(default_factory=list)
    nsfw: bool = False
    creator: str = "Unknown"
    stats: Dict = field(default_factory=dict)
    download_date: str = ""
    last_updated: str = ""
    size: int = 0
    thumbnail: str = ""
    favorite: bool = False
    path: str = ""
    rating: int = 0
    dependencies: List[Dict] = field(default_factory=list)
    
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
            "favorite": self.favorite,
            "path": self.path,
            "rating": self.rating,
            "dependencies": self.dependencies
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'ModelInfo':
        """Create model info from dictionary"""
        return cls(
            id=data.get("id", 0),
            name=data.get("name", "Unknown"),
            description=data.get("description", ""),
            type=data.get("type", "Other"),
            base_model=data.get("base_model", "unknown"),
            version_id=data.get("version_id"),
            version_name=data.get("version_name", ""),
            download_url=data.get("download_url", ""),
            tags=data.get("tags", []),
            images=data.get("images", []),
            nsfw=data.get("nsfw", False),
            creator=data.get("creator", "Unknown"),
            stats=data.get("stats", {}),
            download_date=data.get("download_date", ""),
            last_updated=data.get("last_updated", ""),
            size=data.get("size", 0),
            thumbnail=data.get("thumbnail", ""),
            favorite=data.get("favorite", False),
            path=data.get("path", ""),
            rating=data.get("rating", 0),
            dependencies=data.get("dependencies", [])
        )
    
    def calculate_overall_rating(self):
        """Calculate overall rating based on stats and other factors"""
        if not self.stats:
            return 0
            
        # Basic rating from download count
        downloads = self.stats.get("downloadCount", 0)
        download_rating = min(50, downloads / 100)
        
        # Rating from comment count
        comments = self.stats.get("commentCount", 0)
        comment_rating = min(25, comments / 10)
        
        # Rating from favorites/likes
        rating_count = self.stats.get("ratingCount", 0)
        if rating_count > 0:
            rating_avg = self.stats.get("rating", 0)
            rating_score = min(25, (rating_avg * rating_count) / 20)
        else:
            rating_score = 0
            
        # Combine scores
        self.rating = int(download_rating + comment_rating + rating_score)
        return self.rating
        
    def get_highest_rated_images(self, count=9):
        """Get highest rated images based on reactions"""
        if not self.images:
            return []
            
        # Sort images by reaction score
        from src.utils.formatting import calculate_reaction_score
        sorted_images = sorted(
            self.images, 
            key=lambda img: calculate_reaction_score(img.get("stats", {})),
            reverse=True
        )
        
        # Return top N images
        return sorted_images[:count]
    
    def has_local_images(self):
        """Check if model has local images"""
        if not self.images:
            return False
            
        return any("local_path" in img for img in self.images)
