
"""
Module for downloading models and images from Civitai
"""

import os
import re
import time
import threading
import html
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
from typing import Dict, List, Optional, Callable, Any
import requests
import logging

from ComfyUI-MM.constants import MODEL_TYPES, DownloadStatus, CACHE_DIR, API_BASE_URL, USER_AGENT, REQUEST_TIMEOUT, MAX_RETRY_COUNT
from ComfyUI-MM.models import ModelInfo, DownloadTask, calculate_reaction_score

# Set up logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("download_manager")

class DownloadQueue:
    """Manages a queue of URLs to download"""
    
    def __init__(self):
        self.tasks = {}  # url -> DownloadTask
        self.queue = []  # List of URL strings in queue order
        self.current_url = None
        self.is_processing = False
        self._listeners = []
    
    def add_listener(self, listener):
        """Add a listener for queue events"""
        if listener not in self._listeners:
            self._listeners.append(listener)
    
    def remove_listener(self, listener):
        """Remove a listener"""
        if listener in self._listeners:
            self._listeners.remove(listener)
    
    def _notify_queue_updated(self):
        """Notify listeners about queue update"""
        for listener in self._listeners:
            if hasattr(listener, 'on_queue_updated'):
                listener.on_queue_updated(len(self.queue))
    
    def _notify_task_updated(self, task):
        """Notify listeners about task update"""
        for listener in self._listeners:
            if hasattr(listener, 'on_task_updated'):
                listener.on_task_updated(task)
    
    def add_url(self, url):
        """Add a URL to the queue"""
        url = url.strip()
        if not url:
            return False
            
        if url in self.tasks and self.tasks[url].status in [DownloadStatus.QUEUED, DownloadStatus.DOWNLOADING]:
            # URL already in queue and active
            logger.info(f"URL already in queue: {url}")
            return False
            
        # Add to queue
        self.queue.append(url)
        
        # Create a new task
        task = DownloadTask(url)
        task.priority = len(self.queue)
        self.tasks[url] = task
        
        self._notify_task_updated(task)
        self._notify_queue_updated()
        return True
    
    def add_urls(self, urls):
        """Add multiple URLs to the queue"""
        added_count = 0
        for url in urls:
            if self.add_url(url):
                added_count += 1
        return added_count
    
    def get_next_url(self):
        """Get the next URL from the queue based on priority"""
        if not self.queue:
            return None
            
        # Get the highest priority URL (first in queue)
        url = self.queue.pop(0)
        self.current_url = url
        
        # Update task status
        if url in self.tasks:
            task = self.tasks[url]
            task.status = DownloadStatus.DOWNLOADING
            task.start_time = time.time()
            self._notify_task_updated(task)
            
        self._notify_queue_updated()
        return url
    
    def update_task(self, url, **kwargs):
        """Update a task's properties"""
        if url in self.tasks:
            task = self.tasks[url]
            for key, value in kwargs.items():
                if hasattr(task, key):
                    setattr(task, key, value)
            self._notify_task_updated(task)
    
    def complete_task(self, url, success, message=None, model_info=None):
        """Mark a task as completed or failed"""
        if url in self.tasks:
            task = self.tasks[url]
            task.end_time = time.time()
            if success:
                task.status = DownloadStatus.COMPLETED
                task.model_info = model_info
                task.model_progress = 100
                task.image_progress = 100
            else:
                task.status = DownloadStatus.FAILED
                task.error_message = message or "Download failed"
            self._notify_task_updated(task)
    
    def cancel_task(self, url):
        """Cancel a task"""
        if url in self.tasks:
            task = self.tasks[url]
            
            # Remove from queue if it's still there
            if url in self.queue:
                self.queue.remove(url)
                self._notify_queue_updated()
                
            # Update task status
            task.status = DownloadStatus.CANCELED
            task.end_time = time.time()
            self._notify_task_updated(task)
            
            return True
        return False
    
    def clear(self):
        """Clear the queue"""
        # Mark all queued tasks as canceled
        for url in self.queue:
            if url in self.tasks and self.tasks[url].status == DownloadStatus.QUEUED:
                self.tasks[url].status = DownloadStatus.CANCELED
                self.tasks[url].end_time = time.time()
                self._notify_task_updated(self.tasks[url])
                
        # Clear the queue list
        self.queue.clear()
        self._notify_queue_updated()
    
    def is_empty(self):
        """Check if the queue is empty"""
        return len(self.queue) == 0
    
    def get_all_tasks(self):
        """Get all tasks"""
        return list(self.tasks.values())
    
    def get_queued_tasks(self):
        """Get all queued tasks in queue order"""
        return [self.tasks[url] for url in self.queue if url in self.tasks]


class CivitaiAPI:
    """API client for Civitai"""
    
    def __init__(self, api_key="", fetch_batch_size=100):
        self.api_key = api_key
        self.fetch_batch_size = fetch_batch_size
    
    def get_headers(self):
        """Get request headers with optional API key"""
        headers = {"User-Agent": USER_AGENT}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers
    
    def parse_url(self, url):
        """Parse model ID and version ID from Civitai URL"""
        # Check if it's a valid Civitai URL
        if "civitai.com" not in url:
            return None, None
            
        # Try to extract model ID
        model_match = re.search(r'models/(\d+)', url)
        model_id = int(model_match.group(1)) if model_match else None
        
        # Try to extract version ID
        version_match = re.search(r'modelVersions/(\d+)', url)
        version_id = int(version_match.group(1)) if version_match else None
        
        return model_id, version_id
    
    def fetch_model_info(self, model_id, version_id=None, max_images=9):
        """Fetch model information from Civitai API"""
        try:
            # Fetch model details
            model_url = f"{API_BASE_URL}/models/{model_id}"
            logger.info(f"Fetching model info: {model_url}")
            
            response = requests.get(model_url, headers=self.get_headers(), timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            model_data = response.json()
            
            # Create model info
            model_info = ModelInfo(
                model_id=model_data.get("id"),
                name=model_data.get("name"),
                description=model_data.get("description", ""),
                model_type=model_data.get("type", "Other"),
                base_model=model_data.get("baseModel", "unknown"),
            )
            
            # Add additional info
            model_info.creator = model_data.get("creator", {}).get("username", "Unknown")
            model_info.tags = model_data.get("tags", [])
            model_info.nsfw = model_data.get("nsfw", False)
            model_info.stats = model_data.get("stats", {})
            
            # Get the specific version (latest or requested)
            model_versions = model_data.get("modelVersions", [])
            if not model_versions:
                raise Exception("No model versions found")
                
            version = None
            if version_id:
                # Find specific version
                for v in model_versions:
                    if v.get("id") == version_id:
                        version = v
                        break
                if not version:
                    logger.warning(f"Version {version_id} not found, using latest")
            
            # If no version specified or not found, use latest
            if not version:
                version = model_versions[0]
                
            # Update model info with version details
            model_info.version_id = version.get("id")
            model_info.version_name = version.get("name", "")
            model_info.last_updated = version.get("updatedAt", "")
            
            # Get download URL
            files = version.get("files", [])
            if not files:
                raise Exception("No files available for this model")
                
            # Use primary file or first file
            primary_file = next((f for f in files if f.get("primary")), None)
            model_file = primary_file or files[0]
            model_info.download_url = model_file.get("downloadUrl", "")
            
            # Fetch images
            version_images = version.get("images", [])
            model_info.images = []
            
            # Process all images but limit to max_images for download
            for img in version_images:
                model_info.images.append({
                    "url": img.get("url", ""),
                    "nsfw": img.get("nsfw", False),
                    "width": img.get("width", 0),
                    "height": img.get("height", 0),
                    "hash": img.get("hash", ""),
                    "meta": img.get("meta", {}),
                    "stats": {
                        "likeCount": img.get("stats", {}).get("likeCount", 0),
                        "heartCount": img.get("stats", {}).get("heartCount", 0),
                        "laughCount": img.get("stats", {}).get("laughCount", 0),
                        "dislikeCount": img.get("stats", {}).get("dislikeCount", 0),
                        "commentCount": img.get("stats", {}).get("commentCount", 0),
                    }
                })
            
            logger.info(f"Successfully fetched model info for {model_info.name}")
            return model_info
            
        except Exception as e:
            logger.error(f"Error fetching model info: {str(e)}")
            return None
    
    def download_file(self, url, output_folder, filename=None, 
                      progress_callback=None, callback_interval=1):
        """Download a file with progress tracking"""
        try:
            headers = self.get_headers()
            
            # Send request with streaming
            response = requests.get(url, headers=headers, stream=True, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            
            # Get file name from URL if not provided
            if not filename:
                content_disposition = response.headers.get('Content-Disposition')
                if content_disposition:
                    filename = re.findall(r'filename="(.+)"', content_disposition)
                    if filename:
                        filename = filename[0]
                
                if not filename:
                    filename = os.path.basename(urlparse(url).path)
            
            # Ensure output folder exists
            output_folder.mkdir(parents=True, exist_ok=True)
            
            # Prepare file path
            file_path = output_folder / filename
            
            # Get total size
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            last_progress = 0
            
            # Download file
            with open(file_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        file.write(chunk)
                        
                        # Track progress
                        downloaded += len(chunk)
                        
                        # Report progress at intervals
                        if total_size > 0:
                            progress = int(downloaded * 100 / total_size)
                            if progress >= last_progress + callback_interval:
                                last_progress = progress
                                if progress_callback:
                                    progress_callback(progress, downloaded, total_size)
            
            # Final progress update
            if progress_callback:
                progress_callback(100, downloaded, total_size)
                
            return file_path
            
        except Exception as e:
            logger.error(f"Download error: {str(e)}")
            return None


class DownloadManager:
    """Manager for downloading models from Civitai"""
    
    def __init__(self, config):
        """Initialize the download manager"""
        self.config = config
        self.queue = DownloadQueue()
        self.active_downloads = {}  # url -> thread
        self.api = CivitaiAPI(
            api_key=config.get("api_key", ""),
            fetch_batch_size=config.get("fetch_batch_size", 100)
        )
        self.download_event = threading.Event()
        self.stop_event = threading.Event()
        self.processor_thread = threading.Thread(target=self._queue_processor, daemon=True)
        self.processor_thread.start()
    
    def add_listener(self, listener):
        """Add a listener for queue events"""
        self.queue.add_listener(listener)
    
    def remove_listener(self, listener):
        """Remove a listener"""
        self.queue.remove_listener(listener)
    
    def start_download(self, url):
        """Add a URL to the download queue"""
        if not url:
            return False
        
        if self.queue.add_url(url):
            self.download_event.set()
            return True
        return False
    
    def start_batch_download(self, urls):
        """Add multiple URLs to the download queue"""
        if not urls:
            return 0
        
        added = self.queue.add_urls(urls)
        if added > 0:
            self.download_event.set()
        return added
    
    def cancel_download(self, url):
        """Cancel a download"""
        # Cancel active download if it's currently downloading
        if url == self.queue.current_url and url in self.active_downloads:
            # Thread is already running, can't directly stop it
            # But we'll mark the task as canceled
            pass
            
        # Remove from queue
        return self.queue.cancel_task(url)
    
    def clear_download_queue(self):
        """Clear the download queue"""
        self.queue.clear()
    
    def get_active_downloads_count(self):
        """Get the number of active downloads"""
        return len(self.active_downloads)
    
    def shutdown(self):
        """Shutdown the download manager"""
        self.stop_event.set()
        self.download_event.set()  # Wake up the processor
        if self.processor_thread.is_alive():
            self.processor_thread.join(timeout=2)
    
    def _queue_processor(self):
        """Process the download queue in a separate thread"""
        while not self.stop_event.is_set():
            # Wait for download event or stop event
            self.download_event.wait()
            self.download_event.clear()
            
            if self.stop_event.is_set():
                break
                
            # Process downloads while there are URLs in the queue
            while not self.queue.is_empty() and not self.stop_event.is_set():
                # Check if maximum active downloads reached
                max_downloads = self.config.get("max_concurrent_downloads", 3)
                if len(self.active_downloads) >= max_downloads:
                    # Wait and check again
                    time.sleep(1)
                    continue
                    
                # Get next URL
                url = self.queue.get_next_url()
                if not url:
                    break
                    
                # Start download in a separate thread
                download_thread = threading.Thread(
                    target=self._download_worker,
                    args=(url,),
                    daemon=True
                )
                self.active_downloads[url] = download_thread
                download_thread.start()
            
            # If stop event is set, break loop
            if self.stop_event.is_set():
                break
                
            # Wait before checking queue again
            time.sleep(1)
    
    def _download_worker(self, url):
        """Download worker thread function"""
        try:
            # Extract model ID and version ID
            model_id, version_id = self.api.parse_url(url)
            
            if not model_id:
                self._log(url, f"Invalid URL format: {url}", "error")
                self.queue.complete_task(url, False, f"Invalid URL: {url}")
                return
                
            # Fetch model info
            self._log(url, f"Fetching model information for model ID: {model_id}", "info")
            model_info = self.api.fetch_model_info(
                model_id, 
                version_id,
                max_images=self.config.get("top_image_count", 9)
            )
            
            if not model_info:
                self._log(url, "Failed to fetch model information", "error")
                self.queue.complete_task(url, False, "Failed to fetch model information")
                return
            
            self._log(url, f"Processing model: {model_info.name}", "info")
            
            # Create folder structure
            folder_path = self._create_folder_structure(url, model_info)
            if not folder_path:
                self.queue.complete_task(url, False, "Failed to create folder structure")
                return
                
            # Download model file
            if self.config.get("download_model", True) and model_info.download_url:
                self._log(url, f"Downloading model file...", "download")
                try:
                    model_file = self.api.download_file(
                        model_info.download_url, 
                        folder_path, 
                        progress_callback=lambda p, c, t: self._model_progress_callback(url, p, c, t)
                    )
                    if model_file:
                        model_info.size = model_file.stat().st_size
                        self._log(url, "Model file downloaded successfully", "success")
                    else:
                        self._log(url, "Model file download failed", "error")
                except Exception as e:
                    self._log(url, f"Error downloading model file: {str(e)}", "error")
            
            # Download images
            if self.config.get("download_images", True) and model_info.images:
                # Filter by NSFW setting if needed
                if not self.config.get("download_nsfw", True):
                    original_count = len(model_info.images)
                    model_info.images = [img for img in model_info.images if not img.get("nsfw", False)]
                    self._log(url, f"Filtered out {original_count - len(model_info.images)} NSFW images", "info")
                
                # Sort images by reaction score
                model_info.images = sorted(
                    model_info.images,
                    key=lambda img: calculate_reaction_score(img.get("stats", {})),
                    reverse=True
                )
                
                # Limit to top_image_count
                top_image_count = self.config.get("top_image_count", 9)
                if top_image_count > 0 and top_image_count < len(model_info.images):
                    model_info.images = model_info.images[:top_image_count]
                
                # Download images
                image_count = len(model_info.images)
                if image_count > 0:
                    self._log(url, f"Downloading {image_count} images (sorted by reactions)...", "download")
                    self._download_images(url, model_info.images, folder_path)
                
                    # Set thumbnail from first image if available
                    if model_info.images and "local_path" in model_info.images[0]:
                        model_info.thumbnail = model_info.images[0]["local_path"]
            
            # Create HTML gallery
            if self.config.get("create_html", False):
                html_path = self._create_html_gallery(url, folder_path, model_info)
                self._log(url, f"Created HTML gallery: {html_path}", "success")
            
            # Set download date and path
            model_info.download_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            model_info.last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            model_info.path = str(folder_path)
            
            # Save model metadata
            self._save_metadata(url, folder_path, model_info)
            
            self.queue.complete_task(url, True, f"Successfully downloaded {model_info.name}", model_info)
            
        except Exception as e:
            logger.error(f"Download error for {url}: {str(e)}")
            self._log(url, f"Error: {str(e)}", "error")
            self.queue.complete_task(url, False, str(e))
            
        finally:
            # Clean up
            if url in self.active_downloads:
                del self.active_downloads[url]
    
    def _log(self, url, message, level="info"):
        """Log a message and update progress"""
        log_func = getattr(logger, level, logger.info)
        log_func(f"[{url}] {message}")
    
    def _model_progress_callback(self, url, progress, current, total):
        """Handle model download progress"""
        if progress != -1:
            self.queue.update_task(url, model_progress=progress)
    
    def _create_folder_structure(self, url, model_info):
        """Create folder structure based on model type"""
        try:
            # Determine the model type folder
            model_type_folder = MODEL_TYPES.get(model_info.type, MODEL_TYPES["Other"])
            
            # Create path: ComfyUI/models/type/base_model/model_name
            base_path = Path(self.config.get("comfy_path", ""))
            if not base_path.exists():
                self._log(url, f"ComfyUI directory not found: {base_path}", "error")
                return None
                
            model_path = base_path / model_type_folder / model_info.base_model
            
            # Sanitize model name for folder name
            safe_name = re.sub(r'[^A-Za-z0-9_.-]', '_', model_info.name)
            folder_path = model_path / safe_name
            
            # Create folders
            folder_path.mkdir(parents=True, exist_ok=True)
            
            self._log(url, f"Created folder structure: {folder_path}", "success")
            return folder_path
            
        except Exception as e:
            self._log(url, f"Error creating folder structure: {str(e)}", "error")
            return None
    
    def _download_images(self, url, images, folder):
        """Download images"""
        images_folder = folder / 'images'
        images_folder.mkdir(exist_ok=True)
        
        total_images = len(images)
        downloaded = 0
        
        with ThreadPoolExecutor(max_workers=self.config.get("download_threads", 3)) as executor:
            futures = []
            
            for img in images:
                image_url = img.get('url')
                if not image_url:
                    continue
                    
                fname = Path(urlparse(image_url).path).name
                out_path = images_folder / fname
                
                # Skip if image already exists
                if out_path.exists():
                    img['local_path'] = str(out_path)
                    downloaded += 1
                    self.queue.update_task(url, image_progress=int(downloaded / total_images * 100))
                    continue
                
                # Submit download task
                future = executor.submit(
                    self._download_single_image,
                    url,
                    image_url, 
                    out_path
                )
                futures.append((future, img))
            
            # Process results
            for future, img in futures:
                try:
                    result = future.result()
                    if result:
                        img['local_path'] = str(result)
                except Exception as e:
                    self._log(url, f"Error downloading image: {str(e)}", "error")
                
                downloaded += 1
                self.queue.update_task(url, image_progress=int(downloaded / total_images * 100))
    
    def _download_single_image(self, url, image_url, out_path):
        """Download a single image"""
        try:
            headers = {}
            if self.config.get("api_key"):
                headers["Authorization"] = f"Bearer {self.config.get('api_key')}"
                
            r = requests.get(image_url, headers=headers, timeout=REQUEST_TIMEOUT)
            r.raise_for_status()
            
            with open(out_path, 'wb') as f:
                f.write(r.content)
                
            return out_path
            
        except Exception as e:
            self._log(url, f"Failed to download image {image_url}: {str(e)}", "error")
            return None
    
    def _save_metadata(self, url, folder, model_info):
        """Save model metadata to JSON file"""
        try:
            metadata_path = folder / "metadata.json"
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(model_info.to_dict(), f, indent=2)
        except Exception as e:
            self._log(url, f"Error saving metadata: {str(e)}", "error")
    
    def _create_html_gallery(self, url, folder, model_info):
        """Generate HTML gallery with model information and images"""
        model_url = f"https://civitai.com/models/{model_info.id}"
        
        html_content = self._generate_gallery_html(model_info, model_url)
        
        out_path = folder / "gallery.html"
        with open(out_path, 'w', encoding="utf-8") as f:
            f.write(html_content)
        
        return out_path
    
    def _generate_gallery_html(self, model_info, model_url):
        """Generate HTML content for the gallery"""
        # Start with HTML template
        lines = [
            "<!DOCTYPE html>",
            "<html lang='en'>",
            "<head>",
            "    <meta charset='utf-8'>",
            "    <meta name='viewport' content='width=device-width, initial-scale=1'>",
            f"    <title>{html.escape(model_info.name)} - Model Gallery</title>",
            "    <style>",
            "        :root {",
            "            --bg-color: #121212;",
            "            --card-bg: #1E1E1E;",
            "            --text-color: #FFFFFF;",
            "            --text-secondary: #B3B3B3;",
            "            --accent: #BB86FC;",
            "            --accent-hover: #A66DF0;",
            "            --success: #4CAF50;",
            "            --warning: #FFC107;",
            "            --danger: #F44336;",
            "            --border: #303030;",
            "        }",
            "        body {",
            "            background: var(--bg-color);",
            "            color: var(--text-color);",
            "            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;",
            "            line-height: 1.6;",
            "            margin: 0;",
            "            padding: 0;",
            "        }",
            "        .container {",
            "            max-width: 1200px;",
            "            margin: 0 auto;",
            "            padding: 2rem 1rem;",
            "        }",
            "        header {",
            "            background: var(--card-bg);",
            "            padding: 1.5rem;",
            "            border-radius: 8px;",
            "            margin-bottom: 2rem;",
            "            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);",
            "        }",
            "        h1, h2, h3 {",
            "            margin-top: 0;",
            "            color: var(--text-color);",
            "        }",
            "        a {",
            "            color: var(--accent);",
            "            text-decoration: none;",
            "        }",
            "        a:hover {",
            "            color: var(--accent-hover);",
            "            text-decoration: underline;",
            "        }",
            "        .meta-section {",
            "            display: grid;",
            "            grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));",
            "            gap: 1rem;",
            "            margin-bottom: 2rem;",
            "        }",
            "        .meta-item {",
            "            background: var(--card-bg);",
            "            padding: 1rem;",
            "            border-radius: 6px;",
            "        }",
            "        .meta-item h3 {",
            "            margin-bottom: 0.5rem;",
            "            font-size: 1rem;",
            "            color: var(--text-secondary);",
            "        }",
            "        .meta-item p {",
            "            margin-top: 0.25rem;",
            "            font-size: 1.1rem;",
            "        }",
            "        .description {",
            "            background: var(--card-bg);",
            "            padding: 1.5rem;",
            "            border-radius: 8px;",
            "            margin-bottom: 2rem;",
            "        }",
            "        .tags {",
            "            display: flex;",
            "            flex-wrap: wrap;",
            "            gap: 0.5rem;",
            "            margin-bottom: 2rem;",
            "        }",
            "        .tag {",
            "            background: rgba(187, 134, 252, 0.1);",
            "            color: var(--accent);",
            "            padding: 0.25rem 0.75rem;",
            "            border-radius: 20px;",
            "            font-size: 0.9rem;",
            "            cursor: pointer;",
            "            border: 1px solid var(--accent);",
            "            transition: all 0.2s ease;",
            "        }",
            "        .tag:hover {",
            "            background: rgba(187, 134, 252, 0.2);",
            "            transform: translateY(-2px);",
            "        }",
            "        .gallery {",
            "            display: grid;",
            "            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));",
            "            gap: 1rem;",
            "            margin-bottom: 2rem;",
            "        }",
            "        .gallery-item {",
            "            position: relative;",
            "            overflow: hidden;",
            "            border-radius: 8px;",
            "            aspect-ratio: 1;",
            "            cursor: pointer;",
            "            transition: transform 0.3s ease;",
            "        }",
            "        .gallery-item:hover {",
            "            transform: scale(1.02);",
            "        }",
            "        .gallery-img {",
            "            width: 100%;",
            "            height: 100%;",
            "            object-fit: cover;",
            "            border-radius: 8px;",
            "        }",
            "        .nsfw-badge {",
            "            position: absolute;",
            "            top: 10px;",
            "            right: 10px;",
            "            background: var(--danger);",
            "            color: white;",
            "            padding: 0.25rem 0.5rem;",
            "            border-radius: 4px;",
            "            font-size: 0.8rem;",
            "            font-weight: bold;",
            "        }",
            "        .reactions {",
            "            position: absolute;",
            "            bottom: 10px;",
            "            left: 10px;",
            "            background: rgba(0, 0, 0, 0.7);",
            "            border-radius: 4px;",
            "            padding: 0.25rem 0.5rem;",
            "            font-size: 0.8rem;",
            "            display: flex;",
            "            gap: 0.5rem;",
            "        }",
            "        .modal {",
            "            display: none;",
            "            position: fixed;",
            "            top: 0;",
            "            left: 0;",
            "            width: 100%;",
            "            height: 100%;",
            "            background: rgba(0, 0, 0, 0.9);",
            "            z-index: 1000;",
            "            padding: 2rem;",
            "            box-sizing: border-box;",
            "            overflow-y: auto;",
            "        }",
            "        .modal-content {",
            "            margin: 0 auto;",
            "            max-width: 90%;",
            "            max-height: 90vh;",
            "            display: flex;",
            "            flex-direction: column;",
            "            gap: 1rem;",
            "        }",
            "        .modal-image {",
            "            max-width: 100%;",
            "            max-height: 70vh;",
            "            object-fit: contain;",
            "            margin: 0 auto;",
            "        }",
            "        .modal-info {",
            "            background: var(--card-bg);",
            "            padding: 1.5rem;",
            "            border-radius: 8px;",
            "        }",
            "        .modal-close {",
            "            position: absolute;",
            "            top: 1rem;",
            "            right: 1.5rem;",
            "            font-size: 2rem;",
            "            color: white;",
            "            cursor: pointer;",
            "        }",
            "        .prompt-container {",
            "            background: rgba(0, 0, 0, 0.3);",
            "            padding: 1rem;",
            "            border-radius: 6px;",
            "            margin-bottom: 1rem;",
            "            position: relative;",
            "        }",
            "        .prompt-container pre {",
            "            margin: 0;",
            "            white-space: pre-wrap;",
            "            word-wrap: break-word;",
            "        }",
            "        .copy-btn {",
            "            position: absolute;",
            "            top: 0.5rem;",
            "            right: 0.5rem;",
            "            background: var(--accent);",
            "            color: white;",
            "            border: none;",
            "            border-radius: 4px;",
            "            padding: 0.25rem 0.5rem;",
            "            font-size: 0.8rem;",
            "            cursor: pointer;",
            "            transition: background 0.2s ease;",
            "        }",
            "        .copy-btn:hover {",
            "            background: var(--accent-hover);",
            "        }",
            "        @media (max-width: 768px) {",
            "            .gallery {",
            "                grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));",
            "            }",
            "            .meta-section {",
            "                grid-template-columns: 1fr;",
            "            }",
            "            .modal-content {",
            "                max-width: 100%;",
            "            }",
            "        }",
            "    </style>",
            "</head>",
            "<body>",
            "    <div class='container'>",
            "        <header>",
            f"            <h1>{html.escape(model_info.name)}</h1>",
            f"            <p>by <strong>{html.escape(model_info.creator)}</strong> • <a href='{html.escape(model_url)}' target='_blank'>View on Civitai</a></p>",
            "        </header>",
            "",
            "        <div class='meta-section'>",
            f"            <div class='meta-item'><h3>Type</h3><p>{html.escape(model_info.type)}</p></div>",
            f"            <div class='meta-item'><h3>Base Model</h3><p>{html.escape(model_info.base_model)}</p></div>",
            f"            <div class='meta-item'><h3>Version</h3><p>{html.escape(model_info.version_name)}</p></div>",
            f"            <div class='meta-item'><h3>Downloaded</h3><p>{html.escape(model_info.download_date)}</p></div>",
            "        </div>",
            "",
            "        <div class='description'>",
            f"            <h2>Description</h2>",
            f"            <div>{html.escape(model_info.description)}</div>",
            "        </div>",
            "",
            "        <h2>Tags</h2>",
            "        <div class='tags'>",
        ]
        
        # Add tags
        for tag in model_info.tags:
            lines.append(f"            <div class='tag' onclick=\"navigator.clipboard.writeText('{html.escape(tag)}'); this.textContent = 'Copied!'\">{html.escape(tag)}</div>")
        
        lines.append("        </div>")
        
        # Add images section
        lines.append("        <h2>Images</h2>")
        lines.append("        <div class='gallery'>")
        
        # Add images
        for idx, img in enumerate(model_info.images):
            img_url = ""
            if 'local_path' in img:
                img_url = f"images/{Path(img['local_path']).name}"
            else:
                img_url = img.get('url', '')
                
            if not img_url:
                continue
                
            is_nsfw = img.get('nsfw', False)
            stats = img.get('stats', {})
            likes = stats.get('likeCount', 0)
            hearts = stats.get('heartCount', 0)
            score = calculate_reaction_score(stats)
            
            lines.append(f"            <div class='gallery-item' onclick='showModal({idx})'>")
            lines.append(f"                <img src='{img_url}' class='gallery-img' alt='Model preview {idx+1}' loading='lazy'>")
            
            if is_nsfw:
                lines.append(f"                <div class='nsfw-badge'>NSFW</div>")
                
            lines.append(f"                <div class='reactions'>👍 {likes} ❤️ {hearts} • Score: {int(score)}</div>")
            lines.append(f"            </div>")
        
        lines.append("        </div>")
        
        # Add modal for image details
        lines.append("        <div id='imageModal' class='modal'>")
        lines.append("            <span class='modal-close' onclick='closeModal()'>&times;</span>")
        lines.append("            <div class='modal-content'>")
        lines.append("                <img id='modalImage' class='modal-image' src='' alt='Enlarged preview'>")
        lines.append("                <div class='modal-info'>")
        lines.append("                    <h3>Prompt</h3>")
        lines.append("                    <div class='prompt-container'>")
        lines.append("                        <pre id='promptText'></pre>")
        lines.append("                        <button class='copy-btn' onclick='copyToClipboard(\"promptText\")'>Copy</button>")
        lines.append("                    </div>")
        lines.append("                    <h3>Negative Prompt</h3>")
        lines.append("                    <div class='prompt-container'>")
        lines.append("                        <pre id='negativePromptText'></pre>")
        lines.append("                        <button class='copy-btn' onclick='copyToClipboard(\"negativePromptText\")'>Copy</button>")
        lines.append("                    </div>")
        lines.append("                    <div id='metadataSection'></div>")
        lines.append("                </div>")
        lines.append("            </div>")
        lines.append("        </div>")
        
        # Add JavaScript
        lines.append("        <script>")
        lines.append("            // Image data")
        lines.append("            const images = [")
        
        # Add image data as JSON
        for img in model_info.images:
            img_url = ""
            if 'local_path' in img:
                img_url = f"images/{Path(img['local_path']).name}"
            else:
                img_url = img.get('url', '')
                
            if not img_url:
                continue
                
            meta = img.get('meta', {})
            prompt = meta.get('prompt', '')
            negative_prompt = meta.get('negativePrompt', '')
            
            metadata = {}
            for key, value in meta.items():
                if key not in ['prompt', 'negativePrompt']:
                    metadata[key] = value
            
            lines.append("                {")
            lines.append(f"                    url: '{img_url}',")
            lines.append(f"                    prompt: `{html.escape(prompt)}`,")
            lines.append(f"                    negativePrompt: `{html.escape(negative_prompt)}`,")
            lines.append(f"                    metadata: {json.dumps(metadata)}")
            lines.append("                },")
            
        lines.append("            ];")
        
        # Add JavaScript functions
        lines.append("""
            // Modal functions
            function showModal(index) {
                const img = images[index];
                document.getElementById('modalImage').src = img.url;
                document.getElementById('promptText').textContent = img.prompt;
                document.getElementById('negativePromptText').textContent = img.negativePrompt;
                
                // Add metadata
                let metadataHTML = '';
                for (const [key, value] of Object.entries(img.metadata)) {
                    if (typeof value === 'object') {
                        metadataHTML += `<h3>${key}</h3><pre>${JSON.stringify(value, null, 2)}</pre>`;
                    } else {
                        metadataHTML += `<h3>${key}</h3><p>${value}</p>`;
                    }
                }
                document.getElementById('metadataSection').innerHTML = metadataHTML;
                
                document.getElementById('imageModal').style.display = 'block';
                document.body.style.overflow = 'hidden'; // Prevent scrolling
            }
            
            function closeModal() {
                document.getElementById('imageModal').style.display = 'none';
                document.body.style.overflow = 'auto'; // Re-enable scrolling
            }
            
            function copyToClipboard(elementId) {
                const text = document.getElementById(elementId).textContent;
                navigator.clipboard.writeText(text).then(() => {
                    const btn = event.target;
                    const originalText = btn.textContent;
                    btn.textContent = 'Copied!';
                    setTimeout(() => {
                        btn.textContent = originalText;
                    }, 2000);
                });
            }
            
            // Close modal when clicking outside or pressing Escape
            window.onclick = function(event) {
                const modal = document.getElementById('imageModal');
                if (event.target === modal) {
                    closeModal();
                }
            }
            
            document.addEventListener('keydown', function(event) {
                if (event.key === 'Escape') {
                    closeModal();
                }
            });
        """)
        
        lines.append("        </script>")
        lines.append("    </div>")
        lines.append("</body>")
        lines.append("</html>")
        
        return "\n".join(lines)
