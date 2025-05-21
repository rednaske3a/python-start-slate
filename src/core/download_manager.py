
import os
import re
import time
import threading
import shutil
import html
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from queue import Queue
from typing import Dict, Optional, List, Callable, Any
from urllib.parse import urlparse
import requests
import json
import logging

from PySide6.QtCore import QObject, Signal

from src.api.civitai_api import CivitaiAPI
from src.constants.constants import MODEL_TYPES, DOWNLOAD_STATUS
from src.models.download_task import DownloadTask
from src.models.model_info import ModelInfo
from src.utils.logger import get_logger
from src.utils.bandwidth_monitor import BandwidthMonitor

logger = get_logger(__name__)

class DownloadQueue(QObject):
    """
    Manages a queue of URLs to download
    """
    queue_updated = Signal(int)  # queue size
    download_started = Signal(str)  # url
    task_updated = Signal(DownloadTask)  # task
    queue_reordered = Signal()  # Emitted when queue is reordered
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tasks = {}  # url -> DownloadTask
        self.queue = []  # List of URL strings in queue order
        self.current_url = None
        self.is_processing = False
    
    def add_url(self, url):
        """Add a URL to the queue"""
        url = url.strip()
        if not url:
            return False
            
        if url in self.tasks and self.tasks[url].status in [DOWNLOAD_STATUS["QUEUED"], DOWNLOAD_STATUS["DOWNLOADING"]]:
            # URL already in queue and active
            logger.info(f"URL already in queue: {url}")
            return False
            
        # Add to queue
        self.queue.append(url)
        
        # Create a new task
        task = DownloadTask(url=url, priority=len(self.queue))
        self.tasks[url] = task
        self.task_updated.emit(task)
        self.queue_updated.emit(len(self.queue))
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
            task.status = DOWNLOAD_STATUS["DOWNLOADING"]
            task.start_time = time.time()
            self.task_updated.emit(task)
            
        self.queue_updated.emit(len(self.queue))
        return url
    
    def move_to_position(self, url, position):
        """Move a URL to a specific position in the queue"""
        if url not in self.queue:
            return False
            
        # Remove from current position
        self.queue.remove(url)
        
        # Insert at new position, ensuring it's within bounds
        position = min(max(0, position), len(self.queue))
        self.queue.insert(position, url)
        
        # Update priorities
        self._update_priorities()
        
        self.queue_reordered.emit()
        return True
    
    def _update_priorities(self):
        """Update task priorities based on queue order"""
        for i, url in enumerate(self.queue):
            if url in self.tasks:
                self.tasks[url].priority = i
                self.task_updated.emit(self.tasks[url])
    
    def update_task(self, url, **kwargs):
        """Update a task's properties"""
        if url in self.tasks:
            task = self.tasks[url]
            for key, value in kwargs.items():
                if hasattr(task, key):
                    setattr(task, key, value)
            self.task_updated.emit(task)
    
    def complete_task(self, url, success, message=None, model_info=None):
        """Mark a task as completed or failed"""
        if url in self.tasks:
            task = self.tasks[url]
            task.end_time = time.time()
            if success:
                task.status = DOWNLOAD_STATUS["COMPLETED"]
                task.model_info = model_info
                task.model_progress = 100
                task.image_progress = 100
            else:
                task.status = DOWNLOAD_STATUS["FAILED"]
                task.error_message = message or "Download failed"
            self.task_updated.emit(task)
    
    def cancel_task(self, url):
        """Cancel a task"""
        if url in self.tasks:
            task = self.tasks[url]
            
            # Remove from queue if it's still there
            if url in self.queue:
                self.queue.remove(url)
                self.queue_updated.emit(len(self.queue))
                
            # Update task status
            task.status = DOWNLOAD_STATUS["CANCELED"]
            task.end_time = time.time()
            self.task_updated.emit(task)
            
            return True
        return False
    
    def clear(self):
        """Clear the queue"""
        # Mark all queued tasks as canceled
        for url in self.queue:
            if url in self.tasks and self.tasks[url].status == DOWNLOAD_STATUS["QUEUED"]:
                self.tasks[url].status = DOWNLOAD_STATUS["CANCELED"]
                self.tasks[url].end_time = time.time()
                self.task_updated.emit(self.tasks[url])
                
        # Clear the queue list
        self.queue.clear()
        self.queue_updated.emit(0)
    
    def size(self):
        """Get the size of the queue"""
        return len(self.queue)
    
    def is_empty(self):
        """Check if the queue is empty"""
        return len(self.queue) == 0
    
    def get_all_tasks(self):
        """Get all tasks"""
        return list(self.tasks.values())
    
    def get_queued_tasks(self):
        """Get all queued tasks in queue order"""
        return [self.tasks[url] for url in self.queue if url in self.tasks]


class DownloadWorker(threading.Thread):
    """Worker for downloading models and images from Civitai"""
    
    def __init__(self, url: str, config: Dict, 
                 progress_callback: Callable[[str, int, int, str, int], None],
                 completion_callback: Callable[[bool, str, Optional[ModelInfo]], None],
                 bandwidth_monitor: BandwidthMonitor):
        super().__init__()
        self.url = url
        self.config = config
        self.progress_callback = progress_callback
        self.completion_callback = completion_callback
        self.is_cancelled = False
        self.bandwidth_monitor = bandwidth_monitor
        self.api = CivitaiAPI(
            api_key=config.get("api_key", ""),
            fetch_batch_size=config.get("fetch_batch_size", 100)
        )
        
    def run(self):
        try:
            self.log(f"Processing URL: {self.url}", "info")
            model_id, version_id = self.api.parse_url(self.url)
            
            if not model_id:
                self.log("Invalid URL format. Could not extract model ID.", "error")
                self.completion_callback(False, "Invalid URL", None)
                return
                
            # Fetch model info
            model_info = self.api.fetch_model_info(
                model_id, 
                version_id,
                max_images=self.config.get("top_image_count", 9)
            )
            
            if not model_info:
                self.completion_callback(False, "Failed to fetch model info", None)
                return
                
            # Create folder structure
            folder_path = self.create_folder_structure(model_info)
            if not folder_path:
                self.completion_callback(False, "Failed to create folder structure", None)
                return
                
            # Download model file
            if self.config.get("download_model", True) and model_info.download_url:
                self.log(f"Downloading model file...", "download")
                try:
                    model_file = self.api.download_file(
                        model_info.download_url, 
                        folder_path, 
                        progress_callback=lambda p, c, t: self.model_progress_callback(p, c, t),
                        callback_interval=1  # Update progress every 1% for smoother updates
                    )
                    if model_file:
                        model_info.size = model_file.stat().st_size
                        self.log("Model file downloaded successfully", "success")
                    else:
                        self.log("Model file download failed", "error")
                except Exception as e:
                    self.log(f"Error downloading model file: {str(e)}", "error")
            
            # Download images
            if self.config.get("download_images", True) and model_info.images:
                # Skip NSFW images if configured
                if not self.config.get("download_nsfw", True):
                    original_count = len(model_info.images)
                    model_info.images = [img for img in model_info.images if not img.get("nsfw", False)]
                    self.log(f"Filtered out {original_count - len(model_info.images)} NSFW images", "info")
                
                self.log(f"Downloading {len(model_info.images)} images...", "download")
                self.download_images(
                    model_info.images, 
                    folder_path, 
                    progress_callback=lambda p: self.progress_callback("", -1, p, "", 0)
                )
                
                # Set thumbnail from first image if available
                if model_info.images and len(model_info.images) > 0 and "local_path" in model_info.images[0]:
                    model_info.thumbnail = model_info.images[0]["local_path"]
                
            # Create HTML summary
            if self.config.get("create_html", False):
                html_path = self.save_html(folder_path, model_info)
                self.log(f"Created HTML summary: {html_path}", "success")
                
                # Auto-open HTML if enabled
                if self.config.get("auto_open_html", False):
                    from PySide6.QtGui import QDesktopServices
                    from PySide6.QtCore import QUrl
                    QDesktopServices.openUrl(QUrl.fromLocalFile(str(html_path)))
            
            # Set download date and path
            model_info.download_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            model_info.last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            model_info.path = str(folder_path)
            
            # Save model metadata
            self.save_metadata(folder_path, model_info)
            
            self.completion_callback(True, f"Successfully downloaded {model_info.name}", model_info)
            
        except Exception as e:
            logger.error(f"Download error: {str(e)}")
            self.log(f"Error: {str(e)}", "error")
            self.completion_callback(False, str(e), None)
    
    def model_progress_callback(self, progress, current_bytes, total_bytes):
        """Handle model download progress with bandwidth tracking"""
        if progress != -1:
            self.progress_callback("", progress, -1, "", current_bytes)
        
        # Add data point for bandwidth calculation
        self.bandwidth_monitor.add_data_point(current_bytes)
    
    def cancel(self):
        """Cancel the download"""
        self.is_cancelled = True
        self.log("Download cancelled", "warning")
    
    def log(self, message, status="info"):
        """Log a message"""
        logger.log(getattr(logging, status.upper(), logging.INFO), message)
        self.progress_callback(message, -1, -1, status, 0)
    
    def create_folder_structure(self, model_info: ModelInfo) -> Optional[Path]:
        """Create folder structure based on model type and base model"""
        try:
            # Determine the model type folder
            model_type_folder = MODEL_TYPES.get(model_info.type, MODEL_TYPES["Other"])
            
            # Create path: ComfyUI/models/type/base_model/model_name
            base_path = Path(self.config.get("comfy_path", ""))
            if not base_path.exists():
                self.log(f"ComfyUI directory not found: {base_path}", "error")
                return None
                
            model_path = base_path / model_type_folder / model_info.base_model
            
            # Sanitize model name for folder name
            safe_name = re.sub(r'[^A-Za-z0-9_.-]', '_', model_info.name)
            folder_path = model_path / safe_name
            
            # Create folders
            folder_path.mkdir(parents=True, exist_ok=True)
            
            self.log(f"Created folder structure: {folder_path}", "success")
            return folder_path
            
        except Exception as e:
            self.log(f"Error creating folder structure: {str(e)}", "error")
            return None
    
    def download_images(self, images: List[Dict], folder: Path, 
                       progress_callback = None) -> None:
        """Download images with progress reporting"""
        images_folder = folder / 'images'
        images_folder.mkdir(exist_ok=True)
        
        total_images = len(images)
        downloaded = 0
        
        with ThreadPoolExecutor(max_workers=self.config.get("download_threads", 3)) as executor:
            futures = []
            
            for img in images:
                if self.is_cancelled:
                    break
                    
                url = img['url']
                fname = Path(urlparse(url).path).name
                out_path = images_folder / fname
                
                # Skip if image already exists
                if out_path.exists():
                    img['local_path'] = str(out_path)
                    downloaded += 1
                    if progress_callback:
                        progress_callback(int(downloaded / total_images * 100))
                    continue
                
                # Submit download task
                future = executor.submit(
                    self.download_single_image, 
                    url, 
                    out_path
                )
                futures.append((future, img))
            
            # Process results
            for future, img in futures:
                if self.is_cancelled:
                    break
                    
                try:
                    result = future.result()
                    if result:
                        img['local_path'] = str(result)
                except Exception as e:
                    self.log(f"Error downloading image: {str(e)}", "error")
                
                downloaded += 1
                if progress_callback:
                    progress_callback(int(downloaded / total_images * 100))
    
    def download_single_image(self, url: str, out_path: Path) -> Optional[Path]:
        """Download a single image"""
        try:
            headers = {}
            if self.config.get("api_key"):
                headers["Authorization"] = f"Bearer {self.config.get('api_key')}"
                
            r = requests.get(url, headers=headers, timeout=30)
            r.raise_for_status()
            
            with open(out_path, 'wb') as f:
                f.write(r.content)
                
            return out_path
            
        except Exception as e:
            self.log(f"Failed to download image {url}: {str(e)}", "error")
            return None
    
    def save_metadata(self, folder: Path, model_info: ModelInfo) -> None:
        """Save model metadata to JSON file"""
        try:
            metadata_path = folder / "metadata.json"
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(model_info.to_dict(), f, indent=2)
        except Exception as e:
            self.log(f"Error saving metadata: {str(e)}", "error")
    
    def save_html(self, folder: Path, model_info: ModelInfo) -> Path:
        """Generate HTML summary file with image gallery and metadata"""
        model_url = f"https://civitai.com/models/{model_info.id}"
        
        lines = [
            "<!DOCTYPE html>",
            "<html lang='en'>",
            "<head>",
            "<meta charset='utf-8'>",
            "<meta name='viewport' content='width=device-width,initial-scale=1'>",
            f"<title>{html.escape(model_info.name)} - Model Gallery</title>",
            # Bootstrap + Google Fonts
            "<link href='https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css' rel='stylesheet'>",
            "<link href='https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap' rel='stylesheet'>",
            "<style>",
            "body { background: #181a1b; color: #e0e0e0; font-family: 'Inter', sans-serif; }",
            ".container { max-width: 1200px; }",
            "h2, h5 { font-weight: 600; }",
            ".badge { cursor: pointer; user-select: all; font-size: 1rem; margin-bottom: 6px; }",
            ".gallery-row { display: flex; flex-wrap: wrap; gap: 20px; }",
            ".gallery-img { flex: 1 0 18%; max-width: 18%; aspect-ratio: 1/1; object-fit: cover; border-radius: 10px; cursor: pointer; transition: box-shadow .2s, transform .2s; box-shadow: 0 2px 8px #0004; }",
            ".gallery-img:hover { box-shadow: 0 4px 24px #0007; transform: scale(1.03); }",
            "@media (max-width: 1200px) { .gallery-img { max-width: 23%; } }",
            "@media (max-width: 900px) { .gallery-img { max-width: 31%; } }",
            "@media (max-width: 600px) { .gallery-img { max-width: 48%; } }",
            ".overlay-bg { display: none; position: fixed; z-index: 10000; top: 0; left: 0; width: 100vw; height: 100vh; background: rgba(0,0,0,0.85); align-items: center; justify-content: center; }",
            ".overlay-bg.active { display: flex; }",
            ".overlay-img { max-height: 80vh; max-width: 55vw; border-radius: 12px 0 0 12px; box-shadow: 0 0 32px #000a; background: #222; }",
            ".overlay-panel { width: 350px; max-width: 90vw; background: #222; color: #fff; padding: 32px 24px; border-radius: 0 12px 12px 0; box-shadow: 0 0 32px #000a; display: flex; flex-direction: column; gap: 18px; }",
            ".overlay-close { position: absolute; top: 22px; right: 32px; font-size: 2rem; color: #fff; cursor: pointer; opacity: 0.75; transition: opacity .2s; z-index: 10001; }",
            ".overlay-close:hover { opacity: 1; }",
            ".panel-label { font-size: 0.98rem; color: #aaa; margin-bottom: 2px; }",
            ".panel-content { font-size: 1.08rem; word-break: break-word; }",
            "</style>",
            "</head>",
            "<body>",
            "<div class='container py-4'>",
            f"<h2 class='text-info mb-2'>Model: {html.escape(model_info.name)}</h2>",
            f"<p><strong>URL:</strong> <a href='{html.escape(model_url)}' class='text-info' target='_blank'>{html.escape(model_url)}</a></p>",
            f"<p><strong>Type:</strong> {html.escape(model_info.type)} | <strong>Base Model:</strong> {html.escape(model_info.base_model)}</p>",
            f"<p><strong>Creator:</strong> {html.escape(model_info.creator)} | <strong>Version:</strong> {html.escape(model_info.version_name)}</p>",
            "<h5>Description</h5>",
            f"<p style='max-width: 800px;'>{html.escape(model_info.description)}</p>",
            "<h5>Activation Tags</h5>",
            "<div class='mb-3'>"
        ]
        
        # Add tags
        for tag in model_info.tags:
            lines.append(
                f"<span class='badge bg-secondary me-1 mb-1' "
                f"onclick=\"navigator.clipboard.writeText('{html.escape(tag)}');\" title='Copy tag'>"
                f"{html.escape(tag)}</span>"
            )
        
        lines.append("</div>")
        lines.append("<h5 class='mb-3'>Images</h5>")
        lines.append("<div class='gallery-row mb-5'>")
        
        # Add images
        for idx, img in enumerate(model_info.images):
            if 'local_path' in img:
                # Use local path if available
                img_path = img['local_path']
                img_url = f"images/{Path(img_path).name}"
            else:
                # Use remote URL
                img_url = img['url']
                
            prompt = html.escape((img.get('meta') or {}).get('prompt', 'N/A'))
            chk = html.escape((img.get('meta') or {}).get('Model', 'N/A'))
            loras = html.escape(', '.join(
                r.get('name') for r in (img.get('meta') or {}).get('resources', [])
                if r.get('type') == 'lora'
            ))
            
            stats = img.get('stats', {})
            score = stats.get('likeCount', 0) + stats.get('heartCount', 0) + stats.get('laughCount', 0)
            stats_str = f"👍 {stats.get('likeCount',0)} | ❤️ {stats.get('heartCount',0)} | 😂 {stats.get('laughCount',0)} | Score: {score}"
            
            is_video = img_url.lower().endswith('.mp4')
            if is_video:
                lines.append(
                    f"<video src='{img_url}' class='gallery-img' controls "
                    f"data-idx='{idx}' "
                    f"data-prompt=\"{prompt}\" "
                    f"data-chk=\"{chk}\" "
                    f"data-loras=\"{loras}\" "
                    f"data-stats=\"{stats_str}\" "
                    f"tabindex='0' preload='metadata' poster=''>"
                    "Sorry, your browser doesn't support embedded videos."
                    "</video>"
                )
            else:
                lines.append(
                    f"<img src='{img_url}' class='gallery-img' "
                    f"data-idx='{idx}' "
                    f"data-prompt=\"{prompt}\" "
                    f"data-chk=\"{chk}\" "
                    f"data-loras=\"{loras}\" "
                    f"data-stats=\"{stats_str}\" "
                    f"alt='Model image {idx+1}' tabindex='0'/>"
                )
        
        lines.append("</div>")  # end gallery-row
        
        # Add overlay and JavaScript
        lines.append("""
<div class='overlay-bg' id='overlayBg' tabindex='-1'>
<span class='overlay-close' id='overlayClose' title='Close'>&times;</span>
<img src='/placeholder.svg' class='overlay-img' id='overlayImg' alt='Enlarged image' style='display:none;'/>
<video src='' class='overlay-video' id='overlayVideo' controls style='display:none;max-height:80vh;max-width:55vw;border-radius:12px 0 0 12px;box-shadow:0 0 32px #000a;background:#222;'></video>
<div class='overlay-panel' id='overlayPanel'>
  <div>
    <div class='panel-label'>Prompt</div>
    <div class='panel-content' id='panelPrompt'></div>
  </div>
  <div>
    <div class='panel-label'>Checkpoint</div>
    <div class='panel-content' id='panelChk'></div>
  </div>
  <div>
    <div class='panel-label'>Loras</div>
    <div class='panel-content' id='panelLoras'></div>
  </div>
  <div>
    <div class='panel-label'>Reactions</div>
    <div class='panel-content' id='panelStats'></div>
  </div>
</div>
</div>

<script>
const overlayBg = document.getElementById('overlayBg');
const overlayImg = document.getElementById('overlayImg');
const overlayVideo = document.getElementById('overlayVideo');
const overlayPanel = document.getElementById('overlayPanel');
const overlayClose = document.getElementById('overlayClose');
const panelPrompt = document.getElementById('panelPrompt');
const panelChk = document.getElementById('panelChk');
const panelLoras = document.getElementById('panelLoras');
const panelStats = document.getElementById('panelStats');

function showOverlay(mediaEl) {
  if (mediaEl.tagName === "VIDEO") {
      overlayImg.style.display = "none";
      overlayVideo.style.display = "";
      overlayVideo.src = mediaEl.src;
      overlayVideo.load();
      overlayVideo.play();
  } else {
      overlayVideo.pause();
      overlayVideo.style.display = "none";
      overlayImg.style.display = "";
      overlayImg.src = mediaEl.src;
  }
  panelPrompt.textContent = mediaEl.dataset.prompt || '';
  panelChk.textContent = mediaEl.dataset.chk || '';
  panelLoras.textContent = mediaEl.dataset.loras || '';
  panelStats.textContent = mediaEl.dataset.stats || '';
  overlayBg.classList.add('active');
  document.body.style.overflow = 'hidden';
}

function hideOverlay() {
  overlayBg.classList.remove('active');
  overlayImg.src = '';
  overlayImg.style.display = "none";
  overlayVideo.pause();
  overlayVideo.src = '';
  overlayVideo.style.display = "none";
  document.body.style.overflow = '';
}

document.querySelectorAll('.gallery-img').forEach(media => {
  media.addEventListener('click', () => showOverlay(media));
  media.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') showOverlay(media);
  });
});

// Close overlay on background or close button click
overlayBg.addEventListener('click', (e) => {
  if (e.target === overlayBg || e.target === overlayClose) hideOverlay();
});
// Prevent closing when clicking inside the panel or image
overlayPanel.addEventListener('click', e => e.stopPropagation());
overlayImg.addEventListener('click', e => e.stopPropagation());
overlayVideo.addEventListener('click', e => e.stopPropagation());

// Accessibility: close on Escape key
document.addEventListener('keydown', (e) => {
  if (overlayBg.classList.contains('active') && e.key === 'Escape') hideOverlay();
});
</script>
</body></html>
""")
        
        out_path = folder / "model_card.html"
        with open(out_path, 'w', encoding="utf-8") as f:
            f.write("\n".join(lines))
        
        return out_path


class DownloadManager:
    """Manager for downloading models from Civitai"""
    
    def __init__(self, config):
        """Initialize the download manager"""
        self.config = config
        self.active_downloads = {}  # url -> DownloadWorker
        self.bandwidth_monitor = BandwidthMonitor(window_seconds=60, sample_rate=1)
        
    def start_download(self, url, progress_callback, completion_callback):
        """
        Start downloading a model
        
        Args:
            url: URL to download
            progress_callback: Callback for progress updates (message, model_progress, image_progress, status, bytes)
            completion_callback: Callback for download completion (success, message, model_info)
            
        Returns:
            True if download started successfully, False otherwise
        """
        if url in self.active_downloads:
            logger.warning(f"Download already in progress for {url}")
            return False
            
        # Create download worker
        worker = DownloadWorker(url, self.config, progress_callback, completion_callback, self.bandwidth_monitor)
        
        # Store worker
        self.active_downloads[url] = worker
        
        # Start download
        worker.start()
        logger.info(f"Started download: {url}")
        
        return True
    
    def cancel_download(self, url):
        """
        Cancel a download
        
        Args:
            url: URL to cancel
            
        Returns:
            True if cancelled successfully, False otherwise
        """
        if url in self.active_downloads:
            self.active_downloads[url].cancel()
            del self.active_downloads[url]
            logger.info(f"Download cancelled: {url}")
            return True
        return False
    
    def cancel_all_downloads(self):
        """Cancel all active downloads"""
        for url, worker in list(self.active_downloads.items()):
            worker.cancel()
        self.active_downloads.clear()
        logger.info("All downloads cancelled")
    
    def get_active_downloads_count(self):
        """Get the number of active downloads"""
        return len(self.active_downloads)
    
    def get_bandwidth_stats(self):
        """Get bandwidth statistics for graphing"""
        return self.bandwidth_monitor.get_bandwidth_history()
    
    def reset_bandwidth_monitor(self):
        """Reset the bandwidth monitor"""
        self.bandwidth_monitor.reset()
