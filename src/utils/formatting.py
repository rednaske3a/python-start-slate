
import re
import os
from typing import Dict, List, Union
from datetime import datetime, timedelta


def format_size(size_bytes: Union[int, float]) -> str:
    """Format file size in bytes to human readable format
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Human readable size string
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ("B", "KB", "MB", "GB", "TB", "PB")
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.2f} {size_names[i]}"


def get_file_extension(filename: str) -> str:
    """Get file extension without the dot
    
    Args:
        filename: Filename to process
        
    Returns:
        File extension without the dot
    """
    return os.path.splitext(filename)[1][1:].lower()


def get_time_display(seconds: Union[int, float]) -> str:
    """Convert seconds to human readable time format (HH:MM:SS)
    
    Args:
        seconds: Time in seconds
        
    Returns:
        Formatted time string
    """
    if seconds < 60:
        return f"{int(seconds)}s"
    
    minutes, seconds = divmod(int(seconds), 60)
    hours, minutes = divmod(minutes, 60)
    
    if hours > 0:
        return f"{hours}h {minutes}m {seconds}s"
    else:
        return f"{minutes}m {seconds}s"


def calculate_reaction_score(stats: Dict) -> float:
    """Calculate a score for an image based on reactions
    
    Args:
        stats: Dictionary with reaction counts
        
    Returns:
        Score value (higher is better)
    """
    # Assign weights to different reactions
    like_weight = 1.0
    heart_weight = 2.0
    laugh_weight = 1.5
    dislike_weight = -1.0
    
    # Get reaction counts
    likes = stats.get("likeCount", 0)
    hearts = stats.get("heartCount", 0)
    laughs = stats.get("laughCount", 0)
    dislikes = stats.get("dislikeCount", 0)
    
    # Calculate score
    score = (
        like_weight * likes +
        heart_weight * hearts +
        laugh_weight * laughs +
        dislike_weight * dislikes
    )
    
    return max(0, score)  # Ensure score is not negative


def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text to a maximum length
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        
    Returns:
        Truncated text with ellipsis if needed
    """
    if not text:
        return ""
        
    if len(text) <= max_length:
        return text
    
    return text[:max_length - 3] + "..."


def extract_url_from_text(text: str) -> List[str]:
    """Extract CivitAI URLs from text
    
    Args:
        text: Text containing URLs
        
    Returns:
        List of extracted URLs
    """
    # Regular expression for Civitai model URLs
    pattern = r'https?://(?:www\.)?civitai\.com/models/\d+(?:/[\w-]+)?(?:/[\w-]+)?'
    
    # Find all matches
    matches = re.findall(pattern, text)
    
    # Remove duplicates while preserving order
    unique_matches = []
    for url in matches:
        if url not in unique_matches:
            unique_matches.append(url)
    
    return unique_matches

def estimate_download_time(file_size: int, speed_bps: float) -> str:
    """Estimate download time based on file size and speed
    
    Args:
        file_size: File size in bytes
        speed_bps: Speed in bytes per second
        
    Returns:
        Estimated time string
    """
    if speed_bps <= 0:
        return "Unknown"
    
    # Calculate seconds
    seconds = file_size / speed_bps
    
    # Format as readable time
    return get_time_display(seconds)
