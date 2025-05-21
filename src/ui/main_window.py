
from PySide6.QtWidgets import (
    QMainWindow, QTabWidget, QVBoxLayout, QHBoxLayout, QWidget,
    QLabel, QPushButton, QToolBar, QStatusBar, QMenu,
    QDialog, QFileDialog, QMessageBox, QInputDialog, QSplitter,
    QStackedWidget, QCheckBox, QComboBox, QSpinBox
)
from PySide6.QtCore import Qt, Signal, QTimer, QSize
from PySide6.QtGui import QIcon, QKeySequence

import os
import sys
from pathlib import Path
import time

from src.constants.theme import get_theme
from src.core.download_manager import DownloadManager, DownloadQueue
from src.core.storage_manager import StorageManager
from src.db.models_db import ModelsDatabase
from src.ui.components.toast_manager import ToastManager
from src.ui.tabs.download_tab import DownloadTab
from src.ui.tabs.gallery_tab import GalleryTab
from src.ui.tabs.settings_tab import SettingsTab
from src.ui.tabs.storage_tab import StorageTab
from src.utils.logger import get_logger
from src.utils.bandwidth_monitor import BandwidthMonitor

logger = get_logger(__name__)

class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.theme = get_theme(config.get("theme", "dark"))
        self.init_ui()
        self.setup_services()
    
    def init_ui(self):
        """Initialize UI components"""
        self.setWindowTitle("Civitai Model Manager")
        self.resize(1280, 800)
        
        # Create main layout with central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create tab widget
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {self.theme['border']};
                background-color: {self.theme['primary']};
            }}
            QTabBar::tab {{
                background-color: {self.theme['secondary']};
                color: {self.theme['text_secondary']};
                border: 1px solid {self.theme['border']};
                padding: 8px 16px;
                margin-right: 2px;
            }}
            QTabBar::tab:selected {{
                background-color: {self.theme['primary']};
                color: {self.theme['text']};
                border-bottom-color: {self.theme['primary']};
            }}
            QTabBar::tab:hover:!selected {{
                background-color: {self.theme['card_hover']};
            }}
        """)
        
        # Create tabs
        self.gallery_tab = GalleryTab(self.theme, self)
        self.download_tab = DownloadTab(self.theme, self)
        self.settings_tab = SettingsTab(self.theme, self)
        self.storage_tab = StorageTab(self.theme, self)
        
        # Add tabs to widget
        self.tabs.addTab(self.gallery_tab, "Gallery")
        self.tabs.addTab(self.download_tab, "Download")
        self.tabs.addTab(self.storage_tab, "Storage")
        self.tabs.addTab(self.settings_tab, "Settings")
        
        # Add tab widget to main layout
        main_layout.addWidget(self.tabs)
        
        # Create status bar
        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet(f"""
            QStatusBar {{
                background-color: {self.theme['secondary']};
                color: {self.theme['text']};
                border-top: 1px solid {self.theme['border']};
            }}
        """)
        self.setStatusBar(self.status_bar)
        
        # Create toast manager for notifications
        self.toast_manager = ToastManager(self, self.theme)
    
    def setup_services(self):
        """Set up background services"""
        # Database
        self.models_db = ModelsDatabase()
        self.models_db.load()
        
        # Storage manager
        comfy_path = self.config.get("comfy_path", "")
        self.storage_manager = StorageManager(comfy_path, )
        
        # Download queue
        self.download_queue = DownloadQueue()
        self.download_queue.queue_updated.connect(self.on_queue_updated)
        self.download_queue.task_updated.connect(self.on_task_updated)
        
        # Download manager
        self.download_manager = DownloadManager(self.config)
        
        # Process downloads timer
        self.process_timer = QTimer(self)
        self.process_timer.setInterval(1000)  # Check every second
        self.process_timer.timeout.connect(self.process_download_queue)
        self.process_timer.start()
        
        # Bandwidth monitor update timer
        self.bandwidth_timer = QTimer(self)
        self.bandwidth_timer.setInterval(1000)  # Update every second
        self.bandwidth_timer.timeout.connect(self.update_bandwidth_graph)
        self.bandwidth_timer.start()
        
        # Scan for new models
        self.scan_for_models()
        
        # Refresh gallery
        self.gallery_tab.refresh_gallery()
        
        # Show welcome toast
        self.toast_manager.show_toast(
            "Welcome to Civitai Model Manager",
            "info",
            duration=5000
        )
    
    def scan_for_models(self):
        """Scan for models in the ComfyUI directory"""
        comfy_path = self.config.get("comfy_path", "")
        if not comfy_path or not os.path.isdir(comfy_path):
            self.status_bar.showMessage("ComfyUI directory not set or invalid", 5000)
            return
            
        try:
            count = self.storage_manager.scan_for_models(callback=self.on_model_found)
            self.status_bar.showMessage(f"Found {count} models", 5000)
        except Exception as e:
            logger.error(f"Error scanning for models: {e}")
            self.status_bar.showMessage(f"Error scanning for models: {str(e)}", 5000)
    
    def on_model_found(self, model_data):
        """Callback when a model is found during scanning"""
        if model_data:
            model_id = model_data.get("id")
            if model_id:
                self.models_db.add_or_update_model(model_id, model_data)
    
    def on_queue_updated(self, queue_size):
        """Handle queue update signal"""
        # Update download tab
        self.download_tab.set_queue_status(queue_size)
        
        # Update status bar
        if queue_size > 0:
            self.status_bar.showMessage(f"Download queue: {queue_size} items")
        else:
            self.status_bar.showMessage("Download queue empty")
    
    def on_task_updated(self, task):
        """Handle task update signal"""
        # Update download tab
        self.download_tab.update_download_task(task)
        
        # If task was completed, add to database
        if task.status == "completed" and task.model_info:
            model_info = task.model_info
            model_id = model_info.id
            
            # Convert to dictionary for database
            model_data = model_info.to_dict()
            
            # Add to database
            self.models_db.add_or_update_model(model_id, model_data)
            self.models_db.save()
            
            # Refresh gallery if needed
            self.gallery_tab.refresh_gallery()
            
            # Show toast notification
            self.toast_manager.show_toast(
                f"Model downloaded: {model_info.name}",
                "success",
                duration=5000,
                action=lambda: self.show_model_details(model_data),
                action_text="View"
            )
    
    def process_download_queue(self):
        """Process downloads in the queue"""
        # Skip if already processing
        if self.download_queue.is_processing:
            return
            
        # Skip if maximum active downloads reached
        max_downloads = self.config.get("max_concurrent_downloads", 3)
        if self.download_manager.get_active_downloads_count() >= max_downloads:
            return
            
        # Skip if queue is empty
        if self.download_queue.is_empty():
            return
            
        # Set processing flag
        self.download_queue.is_processing = True
        
        try:
            # Get next URL from queue
            url = self.download_queue.get_next_url()
            if not url:
                self.download_queue.is_processing = False
                return
                
            # Start download
            self.download_manager.start_download(
                url,
                self.on_download_progress,
                self.on_download_complete
            )
            
        except Exception as e:
            logger.error(f"Error processing download queue: {e}")
            self.download_queue.is_processing = False
            
        # Reset processing flag
        self.download_queue.is_processing = False
    
    def on_download_progress(self, message, model_progress, image_progress, status, bytes_transferred):
        """Handle download progress updates"""
        url = self.download_queue.current_url
        if not url:
            return
            
        # Update task with progress
        updates = {}
        if message:
            self.download_tab.log(message, status)
            
        if model_progress != -1:
            updates["model_progress"] = model_progress
            
        if image_progress != -1:
            updates["image_progress"] = image_progress
            
        if updates:
            self.download_queue.update_task(url, **updates)
    
    def on_download_complete(self, success, message, model_info):
        """Handle download completion"""
        url = self.download_queue.current_url
        if not url:
            return
            
        # Mark task as completed or failed
        self.download_queue.complete_task(url, success, message, model_info)
        
        # Log result
        if success:
            self.download_tab.log(f"Download completed: {message}", "success")
        else:
            self.download_tab.log(f"Download failed: {message}", "error")
            
            # Show error toast
            self.toast_manager.show_toast(
                f"Download failed: {message}",
                "error",
                duration=8000
            )
        
        # Reset current URL
        self.download_queue.current_url = None
    
    def start_batch_download(self, urls):
        """Start batch download of models"""
        if not urls:
            return
            
        # Add URLs to queue
        added = self.download_queue.add_urls(urls)
        
        # Show notification
        if added > 0:
            self.toast_manager.show_toast(
                f"Added {added} models to download queue",
                "success",
                duration=3000
            )
    
    def cancel_download(self, url):
        """Cancel a download"""
        # Cancel active download if it's currently downloading
        if url == self.download_queue.current_url:
            self.download_manager.cancel_download(url)
            
        # Remove from queue
        self.download_queue.cancel_task(url)
    
    def clear_download_queue(self):
        """Clear the download queue"""
        self.download_queue.clear()
    
    def move_download_in_queue(self, url, new_position):
        """Move a download in the queue"""
        if self.download_queue.move_to_position(url, new_position):
            self.toast_manager.show_toast(
                "Queue order updated",
                "info",
                duration=2000
            )
    
    def update_bandwidth_graph(self):
        """Update bandwidth graph with current data"""
        # Get bandwidth history from download manager
        times, values = self.download_manager.get_bandwidth_stats()
        
        # Update graph in download tab
        self.download_tab.update_bandwidth_graph(times, values)
    
    def show_model_details(self, model_data):
        """Show model details dialog"""
        self.gallery_tab.show_model_details(model_data)
        
        # Switch to gallery tab
        self.tabs.setCurrentWidget(self.gallery_tab)
    
    def set_theme(self, theme_name):
        """Set application theme"""
        self.theme = get_theme(theme_name)
        self.config["theme"] = theme_name
        
        # Update tab styles
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {self.theme['border']};
                background-color: {self.theme['primary']};
            }}
            QTabBar::tab {{
                background-color: {self.theme['secondary']};
                color: {self.theme['text_secondary']};
                border: 1px solid {self.theme['border']};
                padding: 8px 16px;
                margin-right: 2px;
            }}
            QTabBar::tab:selected {{
                background-color: {self.theme['primary']};
                color: {self.theme['text']};
                border-bottom-color: {self.theme['primary']};
            }}
            QTabBar::tab:hover:!selected {{
                background-color: {self.theme['card_hover']};
            }}
        """)
        
        # Update status bar
        self.status_bar.setStyleSheet(f"""
            QStatusBar {{
                background-color: {self.theme['secondary']};
                color: {self.theme['text']};
                border-top: 1px solid {self.theme['border']};
            }}
        """)
        
        # Update tab widgets
        self.gallery_tab.set_theme(self.theme)
        self.download_tab.set_theme(self.theme)
        self.settings_tab.set_theme(self.theme)
        self.storage_tab.set_theme(self.theme)
        
        # Update toast manager
        self.toast_manager.set_theme(self.theme)
        
        # Save config
        self.config.save()
    
    def closeEvent(self, event):
        """Handle window close event"""
        # Save config
        self.config.save()
        
        # Save database
        self.models_db.save()
        
        # Cancel all active downloads
        self.download_manager.cancel_all_downloads()
        
        # Accept the event
        event.accept()
