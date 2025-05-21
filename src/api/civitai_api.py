
import re
import requests
import json
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Callable
from urllib.parse import urlparse

from src.models.model_info import ModelInfo
from src.utils.logger import get_logger

logger = get_logger(__name__)

class CivitaiAPI:
    """
    API client for interacting with Civitai
    """
    BASE_URL = "https://civitai.com/api/v1"
    
    def __init__(self, api_key: str = "", fetch_batch_size: int = 100, rate_limit_delay: float = 0.5):
        self.api_key = api_key
        self.fetch_batch_size = fetch_batch_size
        self.rate_limit_delay = rate_limit_delay  # Delay between API calls in seconds
        self.last_request_time = 0
    
    def get_headers(self) -> Dict:
        """Get request headers with API key if available"""
        headers = {
            "User-Agent": "CivitaiModelManager/2.0"
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers
    
    def _respect_rate_limit(self):
        """Respect rate limiting by adding delay between requests"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)
        self.last_request_time = time.time()
    
    def fetch_json(self, url: str, params: Dict = None) -> Dict:
        """
        Fetch JSON data from API with rate limiting
        
        Args:
            url: API endpoint URL
            params: Query parameters
            
        Returns:
            JSON response as dictionary
        """
        self._respect_rate_limit()
        
        try:
            r = requests.get(url, headers=self.get_headers(), params=params, timeout=30)
            r.raise_for_status()
            return r.json()
        except requests.RequestException as e:
            logger.error(f"API request failed: {str(e)}")
            return {}
    
    def parse_url(self, url: str) -> Tuple[Optional[int], Optional[int]]:
        """
        Extract model ID and version ID from Civitai URL
        
        Args:
            url: Civitai URL
            
        Returns:
            Tuple of (model_id, version_id)
        """
        # Match /models/{id}?modelVersionId={version_id}
        m = re.search(r"/models/(\d+).*?modelVersionId=(\d+)", url)
        if m: 
            return int(m.group(1)), int(m.group(2))
            
        # Match /models/{id}/versions/{version_id}
        m = re.search(r"/models/(\d+)/versions/(\d+)", url)
        if m: 
            return int(m.group(1)), int(m.group(2))
            
        # Match /models/{id}
        m = re.search(r"/models/(\d+)", url)
        if m: 
            return int(m.group(1)), None
            
        return None, None
    
    def fetch_model_info(self, model_id: int, version_id: Optional[int] = None, 
                        max_images: int = 500) -> Optional[ModelInfo]:
        """
        Fetch model information from Civitai API
        
        Args:
            model_id: Model ID
            version_id: Version ID (optional)
            max_images: Maximum number of images to fetch
            
        Returns:
            ModelInfo object or None if failed
        """
        logger.info(f"Fetching model information for model ID: {model_id}")
        
        # Fetch model data
        model_url = f"{self.BASE_URL}/models/{model_id}"
        model_data = self.fetch_json(model_url)
        
        if not model_data:
            logger.error("Failed to fetch model data")
            return None
            
        name = model_data.get("name", f"model_{model_id}")
        description = re.sub(r'<.*?>', '', model_data.get("description", ""))
        
        # Get model type and base model
        model_type = model_data.get("type", "Other")
        base_model = "unknown"
        nsfw = model_data.get("nsfw", False)
        creator = model_data.get("creator", {}).get("username", "Unknown")
        stats = model_data.get("stats", {})
        
        # If version_id is not provided, use the latest version
        if not version_id and model_data.get("modelVersions"):
            version_id = model_data["modelVersions"][0]["id"]
            logger.info(f"Using latest version ID: {version_id}")
        
        # Fetch version data
        version_url = f"{self.BASE_URL}/model-versions/{version_id}"
        version_data = self.fetch_json(version_url)
        
        if not version_data:
            logger.error("Failed to fetch version data")
            return None
            
        download_url = version_data.get("downloadUrl", "")
        tags = version_data.get("trainedWords", [])
        base_model = version_data.get("baseModel", "unknown")
        version_name = version_data.get("name", "")
        
        # Extract dependencies
        dependencies = []
        files = version_data.get("files", [])
        for file in files:
            # Look for required VAE or other requirements
            if file.get("type") == "VAE":
                dependencies.append({
                    "type": "VAE",
                    "name": file.get("name", "Unknown VAE"),
                    "required": True,
                    "download_url": None
                })
            
            # Look for metadata with dependencies
            metadata = file.get("metadata", {})
            if metadata:
                # Some models list dependencies in the metadata
                if "dependencies" in metadata:
                    deps = metadata["dependencies"]
                    if isinstance(deps, list):
                        for dep in deps:
                            if isinstance(dep, dict):
                                dependencies.append({
                                    "type": dep.get("type", "Unknown"),
                                    "name": dep.get("name", "Unknown Dependency"),
                                    "required": dep.get("required", False),
                                    "download_url": dep.get("url")
                                })
        
        # Fetch images
        logger.info("Fetching images...")
        images = self.fetch_images(model_id, version_id, max_images)
        logger.info(f"Found {len(images)} images")
        
        model_info = ModelInfo(
            id=model_id,
            name=name,
            description=description,
            type=model_type,
            base_model=base_model,
            version_id=version_id,
            version_name=version_name,
            download_url=download_url,
            tags=tags,
            images=images,
            nsfw=nsfw,
            creator=creator,
            stats=stats,
            dependencies=dependencies
        )
        
        # Calculate overall rating
        model_info.calculate_overall_rating()
        
        return model_info
    
    def fetch_images(self, model_id: int, version_id: Optional[int], 
                    max_images: int = 500) -> List[Dict]:
        """
        Fetch images for the model
        
        Args:
            model_id: Model ID
            version_id: Version ID (optional)
            max_images: Maximum number of images to fetch
            
        Returns:
            List of image dictionaries
        """
        def fetch_all_pages(nsfw_flag: bool) -> List[Dict]:
            items = []
            cursor = None
            
            while True:
                params = {
                    "modelId": model_id,
                    "limit": self.fetch_batch_size,
                    "nsfw": str(nsfw_flag).lower()
                }
                
                if version_id:
                    params["modelVersionId"] = version_id
                    
                if cursor:
                    params["cursor"] = cursor
                    
                logger.info(f"Fetching images page (nsfw={nsfw_flag})...")
                
                resp = self.fetch_json(f"{self.BASE_URL}/images", params)
                if not resp:
                    break
                    
                page = resp.get("items", [])
                if not page:
                    break
                    
                items.extend(page)
                logger.info(f"Fetched {len(page)} images (total: {len(items)})")
                
                # If we've reached the maximum number of images, stop fetching
                if len(items) >= max_images:
                    break
                
                cursor = resp.get("metadata", {}).get("nextCursor")
                if not cursor:
                    break
                    
            return items
        
        try:
            with ThreadPoolExecutor(max_workers=2) as executor:
                futures = {
                    executor.submit(fetch_all_pages, True): "nsfw",
                    executor.submit(fetch_all_pages, False): "sfw"
                }
                results = {v: f.result() for f, v in futures.items()}
            
            nsfw_items = results.get("nsfw", [])
            sfw_items = results.get("sfw", [])
            all_items = nsfw_items + sfw_items
            
            # Remove duplicates
            unique = {img["id"]: img for img in all_items}
            
            # Sort by reaction score (likes + hearts + laughs with weights)
            from src.utils.formatting import calculate_reaction_score
            
            def score(img):
                return calculate_reaction_score(img.get("stats", {}))
                
            sorted_items = sorted(unique.values(), key=score, reverse=True)
            
            # Limit to top N images
            return sorted_items[:max_images]
            
        except Exception as e:
            logger.error(f"Error fetching images: {str(e)}")
            return []
    
    def download_file(self, url: str, output_path: Path, 
                     progress_callback: Callable = None,
                     callback_interval: int = 5) -> Optional[Path]:
        """
        Download a file with progress reporting
        
        Args:
            url: URL to download
            output_path: Path to save the file
            progress_callback: Callback function for progress updates
            callback_interval: How often to call the progress callback (percent)
            
        Returns:
            Path to downloaded file if successful, None otherwise
        """
        try:
            r = requests.get(url, headers=self.get_headers(), stream=True)
            r.raise_for_status()
            
            # Get filename from content-disposition or URL
            cd = r.headers.get('content-disposition', '')
            if 'filename=' in cd:
                fname = cd.split('filename=')[1].strip('"; ')
            else:
                fname = Path(urlparse(url).path).name
                
            out_path = output_path / fname
            
            # Check if file already exists
            if out_path.exists():
                logger.info(f"File already exists: {out_path}")
                return out_path
                
            # Get file size for progress reporting
            total = int(r.headers.get('content-length', 0))
            downloaded = 0
            last_progress = 0
            last_report_time = 0
            current_chunk_size = 0  # To track bytes since last callback
            
            with open(out_path, 'wb') as f:
                for chunk in r.iter_content(8192):
                    if not chunk:
                        continue
                        
                    f.write(chunk)
                    downloaded += len(chunk)
                    current_chunk_size += len(chunk)
                    
                    if progress_callback and total:
                        progress = int(downloaded / total * 100)
                        
                        # Call the callback at every interval or if this is the first or last update
                        now = time.time()
                        if (progress >= 100 or 
                            progress - last_progress >= callback_interval or
                            now - last_report_time >= 1.0):  # Also update at least every second
                            
                            progress_callback(progress, current_chunk_size, total)
                            last_progress = progress
                            last_report_time = now
                            current_chunk_size = 0  # Reset chunk counter
            
            return out_path
            
        except Exception as e:
            logger.error(f"Error downloading file: {str(e)}")
            return None
    
    def search_models(self, query: str, tags: List[str] = None, types: List[str] = None,
                     base_models: List[str] = None, nsfw: bool = None, 
                     limit: int = 20) -> List[Dict]:
        """
        Search for models using Civitai API
        
        Args:
            query: Search query text
            tags: List of tags to filter by
            types: List of model types
            base_models: List of base models
            nsfw: Filter by NSFW status
            limit: Maximum number of results to return
            
        Returns:
            List of model dictionaries
        """
        params = {
            "query": query,
            "limit": limit
        }
        
        if tags:
            params["tags"] = tags
        
        if types:
            params["types"] = types
        
        if base_models:
            params["baseModels"] = base_models
        
        if nsfw is not None:
            params["nsfw"] = str(nsfw).lower()
        
        url = f"{self.BASE_URL}/models"
        
        result = self.fetch_json(url, params)
        return result.get("items", [])
