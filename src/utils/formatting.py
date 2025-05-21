
def format_size(size_bytes):
    """Format file size from bytes to human-readable string"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes/1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes/(1024*1024):.1f} MB"
    else:
        return f"{size_bytes/(1024*1024*1024):.2f} GB"

def format_duration(seconds):
    """Format seconds into human-readable duration"""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"

def truncate_text(text, max_length=50):
    """Truncate text to specified length with ellipsis"""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."

def format_rating(rating):
    """Format rating as star value (out of 5)"""
    if not rating:
        return "N/A"
    
    # Convert to 5-star scale
    stars = min(5, rating / 20)  # Assuming rating is 0-100
    return f"{stars:.1f}★"

def format_date(date_str, short=False):
    """Format date string to readable format"""
    if not date_str:
        return "N/A"
    
    try:
        from datetime import datetime
        date_obj = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        
        if short:
            return date_obj.strftime("%Y-%m-%d")
        else:
            return date_obj.strftime("%b %d, %Y at %H:%M")
    except:
        return date_str

def sanitize_filename(name):
    """Sanitize filename to be valid on all platforms"""
    import re
    return re.sub(r'[\\/*?:"<>|]', "_", name)

def extract_url_from_text(text):
    """Extract Civitai URLs from text"""
    import re
    pattern = r'https?://civitai\.com/models/\S+'
    matches = re.findall(pattern, text)
    return matches

def get_image_dimensions(path):
    """Get image dimensions using PIL"""
    try:
        from PIL import Image
        with Image.open(path) as img:
            return img.size
    except:
        return (0, 0)
        
def calculate_reaction_score(stats):
    """Calculate reaction score based on likes, hearts, and laughs"""
    if not stats:
        return 0
    
    likes = stats.get("likeCount", 0)
    hearts = stats.get("heartCount", 0) * 2  # Hearts weighted more
    laughs = stats.get("laughCount", 0)
    
    return likes + hearts + laughs

def format_prompt(prompt, max_length=100):
    """Format prompt text with highlighting and truncation"""
    if not prompt:
        return "No prompt available"
    
    if len(prompt) > max_length:
        return prompt[:max_length] + "..."
    
    return prompt

def calculate_eta(total_size, downloaded_size, elapsed_time):
    """Calculate estimated time of arrival based on download speed"""
    if elapsed_time == 0 or downloaded_size == 0:
        return "Calculating..."
    
    speed = downloaded_size / elapsed_time  # bytes per second
    remaining_size = total_size - downloaded_size
    
    if speed <= 0:
        return "Unknown"
    
    eta_seconds = remaining_size / speed
    
    return format_duration(eta_seconds)
