
"""
GUI for ComfyUI Model Manager
"""
import sys
import os
import re
import time
import threading
from pathlib import Path
from urllib.parse import urlparse

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QTextEdit, QSpinBox,
    QTabWidget, QGroupBox, QCheckBox, QFrame, QSplitter,
    QListWidget, QListWidgetItem, QProgressBar, QMenu, QFileDialog,
    QStatusBar, QMessageBox
)
from PySide6.QtCore import Qt, QSize, QUrl, QTimer, Signal, QObject
from PySide6.QtGui import QDesktopServices, QAction, QIcon, QPalette, QColor

from ComfyUI-MM.constants import get_theme, MODEL_TYPES
from ComfyUI-MM.config import ConfigManager
from ComfyUI-MM.models import DownloadTask
from ComfyUI-MM.download_manager import DownloadManager

class LoadingButton(QPushButton):
    """Button with loading animation"""
    
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.original_text = text
        self.dots = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_dots)
    
    def start_loading(self):
        """Start loading animation"""
        self.setEnabled(False)
        self.timer.start(500)
    
    def stop_loading(self):
        """Stop loading animation"""
        self.timer.stop()
        self.setText(self.original_text)
        self.setEnabled(True)
    
    def update_dots(self):
        """Update loading dots animation"""
        self.dots = (self.dots + 1) % 4
        dots_text = "." * self.dots
        self.setText(f"{self.original_text}{dots_text}")


class LogWidget(QWidget):
    """Widget for displaying logs"""
    
    def __init__(self, theme, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI components"""
        layout = QVBoxLayout(self)
        
        # Log display
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setPlaceholderText("Logs will appear here...")
        self.log_text.setStyleSheet(f"""
            QTextEdit {{
                background-color: {self.theme['primary']};
                color: {self.theme['text']};
                border: 1px solid {self.theme['border']};
                border-radius: 4px;
                padding: 5px;
            }}
        """)
        
        layout.addWidget(QLabel("Activity Log"))
        layout.addWidget(self.log_text)
    
    def add_message(self, message, level="info"):
        """Add a message to the log"""
        color = self.theme['text']
        if level == "error":
            color = self.theme['danger']
        elif level == "success":
            color = self.theme['success']
        elif level == "warning":
            color = self.theme['warning']
        elif level == "download":
            color = self.theme['accent']
            
        timestamp = time.strftime("%H:%M:%S")
        html = f"<div style='margin: 3px 0;'><span style='color: {self.theme['text_secondary']}; margin-right: 8px;'>[{timestamp}]</span> <span style='color: {color};'>{message}</span></div>"
        
        self.log_text.append(html)
        # Scroll to bottom
        scroll_bar = self.log_text.verticalScrollBar()
        scroll_bar.setValue(scroll_bar.maximum())


class QueueTaskWidget(QWidget):
    """Widget for displaying a download task in the queue"""
    
    def __init__(self, task, theme):
        super().__init__()
        self.task = task
        self.theme = theme
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI components"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)
        
        # URL display
        self.url_label = QLabel(self.task.url)
        self.url_label.setStyleSheet(f"color: {self.theme['text']}; font-weight: bold;")
        self.url_label.setWordWrap(True)
        
        # Add status row
        status_layout = QHBoxLayout()
        
        # Status indicator
        status_color = self.task.get_status_color(self.theme)
        self.status_indicator = QLabel("●")
        self.status_indicator.setStyleSheet(f"color: {status_color}; font-size: 16px;")
        
        # Status text
        self.status_text = QLabel(self.task.status.title())
        self.status_text.setStyleSheet(f"color: {self.theme['text_secondary']};")
        
        status_layout.addWidget(self.status_indicator)
        status_layout.addWidget(self.status_text)
        status_layout.addStretch()
        
        # Progress bar row - Model
        progress_layout = QVBoxLayout()
        
        # Model progress
        model_layout = QHBoxLayout()
        model_label = QLabel("Model:")
        model_label.setStyleSheet(f"color: {self.theme['text_secondary']};")
        self.model_progress = QProgressBar()
        self.model_progress.setRange(0, 100)
        self.model_progress.setValue(self.task.model_progress)
        self.model_progress.setStyleSheet(f"""
            QProgressBar {{
                background-color: {self.theme['primary']};
                border: 1px solid {self.theme['border']};
                border-radius: 4px;
                text-align: center;
            }}
            QProgressBar::chunk {{
                background-color: {self.theme['accent']};
                border-radius: 3px;
            }}
        """)
        
        model_layout.addWidget(model_label, 1)
        model_layout.addWidget(self.model_progress, 4)
        
        # Image progress
        image_layout = QHBoxLayout()
        image_label = QLabel("Images:")
        image_label.setStyleSheet(f"color: {self.theme['text_secondary']};")
        self.image_progress = QProgressBar()
        self.image_progress.setRange(0, 100)
        self.image_progress.setValue(self.task.image_progress)
        self.image_progress.setStyleSheet(f"""
            QProgressBar {{
                background-color: {self.theme['primary']};
                border: 1px solid {self.theme['border']};
                border-radius: 4px;
                text-align: center;
            }}
            QProgressBar::chunk {{
                background-color: {self.theme['accent']};
                border-radius: 3px;
            }}
        """)
        
        image_layout.addWidget(image_label, 1)
        image_layout.addWidget(self.image_progress, 4)
        
        progress_layout.addLayout(model_layout)
        progress_layout.addLayout(image_layout)
        
        # Add all components to main layout
        layout.addWidget(self.url_label)
        layout.addLayout(status_layout)
        layout.addLayout(progress_layout)
        
        # Set fixed height
        self.setFixedHeight(150)
        
        # Set frame style
        self.setStyleSheet(f"""
            QueueTaskWidget {{
                background-color: {self.theme['secondary']};
                border-radius: 6px;
                border: 1px solid {self.theme['border']};
            }}
        """)
        
        # Initial update
        self.update_task(self.task)
    
    def update_task(self, task):
        """Update the task display"""
        self.task = task
        
        # Update URL
        self.url_label.setText(task.url)
        
        # Update status
        status_color = task.get_status_color(self.theme)
        self.status_indicator.setStyleSheet(f"color: {status_color}; font-size: 16px;")
        self.status_text.setText(task.status.title())
        
        # Update progress
        self.model_progress.setValue(task.model_progress)
        self.image_progress.setValue(task.image_progress)
        
        # Update tooltip with error message if failed
        if task.status == "failed" and task.error_message:
            self.setToolTip(f"Error: {task.error_message}")
        else:
            self.setToolTip("")
    
    def contextMenuEvent(self, event):
        """Show context menu on right click"""
        menu = QMenu(self)
        
        # Add actions based on task status
        if self.task.status == "queued":
            menu.addAction("Cancel", lambda: self.parent().cancel_task(self.task.url))
        elif self.task.status == "completed" and self.task.model_info:
            menu.addAction("Open Folder", lambda: self.open_model_folder())
            menu.addAction("Open HTML Gallery", lambda: self.open_html_gallery())
        
        menu.exec_(event.globalPos())
    
    def open_model_folder(self):
        """Open the model folder"""
        if self.task.model_info and self.task.model_info.path:
            path = Path(self.task.model_info.path)
            if path.exists():
                QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))
    
    def open_html_gallery(self):
        """Open the HTML gallery"""
        if self.task.model_info and self.task.model_info.path:
            path = Path(self.task.model_info.path) / "gallery.html"
            if path.exists():
                QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))


class QueueWidget(QListWidget):
    """Widget for displaying the download queue"""
    
    def __init__(self, theme, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.task_widgets = {}  # url -> QueueTaskWidget
        self.setSelectionMode(QListWidget.SingleSelection)
        self.setStyleSheet(f"""
            QListWidget {{
                background-color: {self.theme['primary']};
                border: 1px solid {self.theme['border']};
                border-radius: 4px;
                padding: 5px;
            }}
            QListWidget::item {{
                padding: 5px;
                border: none;
                background-color: transparent;
            }}
        """)
    
    def update_task(self, task):
        """Update a task in the list"""
        url = task.url
        
        if url in self.task_widgets:
            # Update existing widget
            self.task_widgets[url].update_task(task)
        else:
            # Create new widget and add to list
            widget = QueueTaskWidget(task, self.theme)
            self.task_widgets[url] = widget
            
            # Add to list widget
            item = QListWidgetItem()
            item.setSizeHint(QSize(0, widget.height()))
            
            self.addItem(item)
            self.setItemWidget(item, widget)
    
    def update_tasks(self, tasks):
        """Update all tasks in the list"""
        for task in tasks:
            self.update_task(task)
    
    def cancel_task(self, url):
        """Signal to cancel a task"""
        self.parent().cancel_task(url)


class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        
        # Initialize config
        self.config = ConfigManager()
        
        # Set theme
        self.theme = get_theme(self.config.get("theme", "dark"))
        
        # Create download manager
        self.download_manager = DownloadManager(self.config)
        self.download_manager.add_listener(self)
        
        # Set up UI
        self.init_ui()
        
        # Add warning if ComfyUI path not set
        if not self.config.get("comfy_path"):
            self.log("ComfyUI path not set. Please set it in Settings tab.", "warning")
    
    def init_ui(self):
        """Initialize UI components"""
        self.setWindowTitle("ComfyUI Model Manager")
        self.resize(1000, 800)
        
        # Set up main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Create splitter for main content and queue
        self.splitter = QSplitter(Qt.Horizontal)
        
        # Create left panel with tabs
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # Create tabs
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {self.theme['border']};
                background-color: {self.theme['primary']};
                border-radius: 4px;
            }}
            QTabBar::tab {{
                background-color: {self.theme['secondary']};
                color: {self.theme['text_secondary']};
                border: 1px solid {self.theme['border']};
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }}
            QTabBar::tab:selected {{
                background-color: {self.theme['primary']};
                color: {self.theme['text']};
                border-bottom-color: {self.theme['primary']};
            }}
            QTabBar::tab:hover:!selected {{
                background-color: {self.theme['secondary']};
                color: {self.theme['text']};
            }}
        """)
        
        # Create download tab
        download_tab = QWidget()
        download_layout = QVBoxLayout(download_tab)
        
        # Log widget
        self.log_widget = LogWidget(self.theme)
        download_layout.addWidget(self.log_widget, 1)
        
        # URL input section
        url_section = self.create_url_input_section()
        download_layout.addWidget(url_section)
        
        # Create settings tab
        settings_tab = QWidget()
        settings_layout = QVBoxLayout(settings_tab)
        
        # ComfyUI path setting
        comfy_path_group = QGroupBox("ComfyUI Installation")
        comfy_path_layout = QVBoxLayout(comfy_path_group)
        
        comfy_path_help = QLabel("Select your ComfyUI installation directory:")
        comfy_path_help.setStyleSheet(f"color: {self.theme['text_secondary']};")
        
        comfy_path_row = QHBoxLayout()
        self.comfy_path_input = QLineEdit(self.config.get("comfy_path", ""))
        self.comfy_path_input.setPlaceholderText("ComfyUI installation path...")
        self.comfy_path_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {self.theme['input_bg']};
                color: {self.theme['text']};
                border: 1px solid {self.theme['border']};
                border-radius: 4px;
                padding: 5px;
            }}
        """)
        
        browse_button = QPushButton("Browse...")
        browse_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.theme['secondary']};
                color: {self.theme['text']};
                border: 1px solid {self.theme['border']};
                border-radius: 4px;
                padding: 5px 15px;
            }}
            QPushButton:hover {{
                background-color: {self.theme['border']};
            }}
        """)
        browse_button.clicked.connect(self.browse_comfy_path)
        
        comfy_path_row.addWidget(self.comfy_path_input)
        comfy_path_row.addWidget(browse_button)
        
        comfy_path_layout.addWidget(comfy_path_help)
        comfy_path_layout.addLayout(comfy_path_row)
        
        # Download settings group
        download_group = QGroupBox("Download Settings")
        download_layout = QVBoxLayout(download_group)
        
        # Max concurrent downloads
        max_downloads_row = QHBoxLayout()
        max_downloads_label = QLabel("Max Concurrent Downloads:")
        max_downloads_label.setStyleSheet(f"color: {self.theme['text']};")
        self.max_downloads_input = QSpinBox()
        self.max_downloads_input.setRange(1, 10)
        self.max_downloads_input.setValue(self.config.get("max_concurrent_downloads", 3))
        self.max_downloads_input.setStyleSheet(f"""
            QSpinBox {{
                background-color: {self.theme['input_bg']};
                color: {self.theme['text']};
                border: 1px solid {self.theme['border']};
                border-radius: 4px;
                padding: 5px;
            }}
        """)
        
        max_downloads_row.addWidget(max_downloads_label)
        max_downloads_row.addWidget(self.max_downloads_input)
        max_downloads_row.addStretch()
        
        # Download threads
        threads_row = QHBoxLayout()
        threads_label = QLabel("Download Threads:")
        threads_label.setStyleSheet(f"color: {self.theme['text']};")
        self.threads_input = QSpinBox()
        self.threads_input.setRange(1, 10)
        self.threads_input.setValue(self.config.get("download_threads", 3))
        self.threads_input.setStyleSheet(f"""
            QSpinBox {{
                background-color: {self.theme['input_bg']};
                color: {self.theme['text']};
                border: 1px solid {self.theme['border']};
                border-radius: 4px;
                padding: 5px;
            }}
        """)
        
        threads_row.addWidget(threads_label)
        threads_row.addWidget(self.threads_input)
        threads_row.addStretch()
        
        # Download options
        download_options_layout = QVBoxLayout()
        self.download_model_check = QCheckBox("Download model files")
        self.download_model_check.setChecked(self.config.get("download_model", True))
        self.download_model_check.setStyleSheet(f"color: {self.theme['text']};")
        
        self.download_images_check = QCheckBox("Download preview images")
        self.download_images_check.setChecked(self.config.get("download_images", True))
        self.download_images_check.setStyleSheet(f"color: {self.theme['text']};")
        
        self.download_nsfw_check = QCheckBox("Download NSFW images")
        self.download_nsfw_check.setChecked(self.config.get("download_nsfw", False))
        self.download_nsfw_check.setStyleSheet(f"color: {self.theme['text']};")
        
        self.create_html_check = QCheckBox("Create HTML gallery")
        self.create_html_check.setChecked(self.config.get("create_html", True))
        self.create_html_check.setStyleSheet(f"color: {self.theme['text']};")
        
        self.auto_open_html_check = QCheckBox("Auto-open HTML gallery after download")
        self.auto_open_html_check.setChecked(self.config.get("auto_open_html", False))
        self.auto_open_html_check.setStyleSheet(f"color: {self.theme['text']};")
        
        download_options_layout.addWidget(self.download_model_check)
        download_options_layout.addWidget(self.download_images_check)
        download_options_layout.addWidget(self.download_nsfw_check)
        download_options_layout.addWidget(self.create_html_check)
        download_options_layout.addWidget(self.auto_open_html_check)
        
        download_layout.addLayout(max_downloads_row)
        download_layout.addLayout(threads_row)
        download_layout.addLayout(download_options_layout)
        
        # API settings
        api_group = QGroupBox("API Settings")
        api_layout = QVBoxLayout(api_group)
        
        api_key_row = QHBoxLayout()
        api_key_label = QLabel("CivitAI API Key:")
        api_key_label.setStyleSheet(f"color: {self.theme['text']};")
        self.api_key_input = QLineEdit(self.config.get("api_key", ""))
        self.api_key_input.setPlaceholderText("Optional: Enter your CivitAI API key...")
        self.api_key_input.setEchoMode(QLineEdit.Password)
        self.api_key_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {self.theme['input_bg']};
                color: {self.theme['text']};
                border: 1px solid {self.theme['border']};
                border-radius: 4px;
                padding: 5px;
            }}
        """)
        
        api_key_row.addWidget(api_key_label)
        api_key_row.addWidget(self.api_key_input)
        
        api_help = QLabel("An API key may be required for downloading some models or if you hit rate limits.")
        api_help.setStyleSheet(f"color: {self.theme['text_secondary']}; font-style: italic;")
        api_help.setWordWrap(True)
        
        api_layout.addLayout(api_key_row)
        api_layout.addWidget(api_help)
        
        # Save settings button
        save_button = QPushButton("Save Settings")
        save_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.theme['accent']};
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {self.theme['accent_hover']};
            }}
            QPushButton:pressed {{
                background-color: {self.theme['accent']};
            }}
        """)
        save_button.clicked.connect(self.save_settings)
        
        # Add all settings groups
        settings_layout.addWidget(comfy_path_group)
        settings_layout.addWidget(download_group)
        settings_layout.addWidget(api_group)
        settings_layout.addWidget(save_button)
        settings_layout.addStretch()
        
        # Add tabs to tab widget
        self.tabs.addTab(download_tab, "Download")
        self.tabs.addTab(settings_tab, "Settings")
        
        left_layout.addWidget(self.tabs)
        
        # Create right panel with queue
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # Queue header
        queue_header = QHBoxLayout()
        queue_title = QLabel("Download Queue")
        queue_title.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {self.theme['text']};")
        
        clear_queue_btn = QPushButton("Clear Queue")
        clear_queue_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.theme['danger']};
                color: white;
                border: none;
                border-radius: 4px;
                padding: 5px 10px;
            }}
            QPushButton:hover {{
                background-color: {self.theme['danger_hover']};
            }}
        """)
        clear_queue_btn.clicked.connect(self.clear_queue)
        
        queue_header.addWidget(queue_title)
        queue_header.addStretch()
        queue_header.addWidget(clear_queue_btn)
        
        # Queue list
        self.queue_widget = QueueWidget(self.theme, self)
        
        right_layout.addLayout(queue_header)
        right_layout.addWidget(self.queue_widget)
        
        # Add panels to splitter
        self.splitter.addWidget(left_panel)
        self.splitter.addWidget(right_panel)
        
        # Set initial sizes (60% left, 40% right)
        self.splitter.setSizes([600, 400])
        
        main_layout.addWidget(self.splitter)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet(f"""
            QStatusBar {{
                background-color: {self.theme['secondary']};
                color: {self.theme['text']};
                border-top: 1px solid {self.theme['border']};
            }}
        """)
        self.setStatusBar(self.status_bar)
        
        # Initial status message
        self.status_bar.showMessage("Ready")
    
    def create_url_input_section(self):
        """Create URL input section with validation"""
        section = QFrame()
        section.setFrameShape(QFrame.StyledPanel)
        section.setStyleSheet(f"""
            QFrame {{
                background-color: {self.theme['secondary']};
                border-radius: 8px;
                border: 1px solid {self.theme['border']};
            }}
        """)
        
        layout = QVBoxLayout(section)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Title
        title = QLabel("Add Models to Download Queue")
        title.setStyleSheet(f"""
            font-size: 16px;
            font-weight: bold;
            color: {self.theme['text']};
        """)
        
        # URL input
        url_layout = QVBoxLayout()
        url_label = QLabel("CivitAI URLs (one per line)")
        url_label.setStyleSheet(f"color: {self.theme['text_secondary']};")
        
        self.url_input = QTextEdit()
        self.url_input.setPlaceholderText("https://civitai.com/models/...")
        self.url_input.setMinimumHeight(80)
        self.url_input.setAcceptDrops(True)
        self.url_input.setStyleSheet(f"""
            QTextEdit {{
                background-color: {self.theme['input_bg']};
                color: {self.theme['text']};
                border: 1px solid {self.theme['border']};
                border-radius: 4px;
                padding: 5px;
            }}
        """)
        
        # Example URL
        example_label = QLabel("Example: https://civitai.com/models/1234/cool-model")
        example_label.setStyleSheet(f"color: {self.theme['text_secondary']}; font-style: italic; font-size: 11px;")
        
        url_layout.addWidget(url_label)
        url_layout.addWidget(self.url_input)
        url_layout.addWidget(example_label)
        
        # Options row
        options_layout = QHBoxLayout()
        
        max_images_label = QLabel("Max Images:")
        max_images_label.setStyleSheet(f"color: {self.theme['text_secondary']};")
        
        self.max_images_input = QSpinBox()
        self.max_images_input.setRange(1, 100)
        self.max_images_input.setValue(self.config.get("top_image_count", 9))
        self.max_images_input.setStyleSheet(f"""
            QSpinBox {{
                background-color: {self.theme['input_bg']};
                color: {self.theme['text']};
                border: 1px solid {self.theme['border']};
                border-radius: 4px;
                padding: 5px;
                min-width: 60px;
            }}
        """)
        
        options_layout.addWidget(max_images_label)
        options_layout.addWidget(self.max_images_input)
        options_layout.addStretch()
        
        # Add button with loading animation
        self.add_button = LoadingButton("Add to Queue")
        self.add_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.theme['accent']};
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {self.theme['accent_hover']};
            }}
            QPushButton:pressed {{
                background-color: {self.theme['accent']};
            }}
            QPushButton:disabled {{
                background-color: {self.theme['text_secondary']};
            }}
        """)
        self.add_button.clicked.connect(self.add_urls)
        
        options_layout.addWidget(self.add_button)
        
        layout.addWidget(title)
        layout.addLayout(url_layout)
        layout.addLayout(options_layout)
        
        return section
    
    def extract_urls(self, text):
        """Extract CivitAI URLs from text"""
        urls = []
        lines = text.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if "civitai.com/models/" in line:
                # Extract URL using regex
                match = re.search(r'https://civitai\.com/models/\d+[^\s]*', line)
                if match:
                    urls.append(match.group(0))
        
        return urls
    
    def add_urls(self):
        """Process URLs from input and add to queue"""
        text = self.url_input.toPlainText().strip()
        if not text:
            return
        
        # Start loading animation
        self.add_button.start_loading()
        
        # Update max images in config
        self.config.set("top_image_count", self.max_images_input.value())
        
        # Extract URLs
        urls = self.extract_urls(text)
        
        if urls:
            # Start download
            added = self.download_manager.start_batch_download(urls)
            
            if added > 0:
                self.log(f"Added {added} model(s) to download queue", "success")
                self.url_input.clear()
            else:
                self.log("No new models added to queue", "warning")
        else:
            self.log("No valid Civitai URLs found in input", "error")
        
        # Stop loading animation (after a small delay to show animation)
        QTimer.singleShot(1000, self.add_button.stop_loading)
    
    def log(self, message, level="info"):
        """Add a message to the log"""
        self.log_widget.add_message(message, level)
    
    def browse_comfy_path(self):
        """Open file dialog to select ComfyUI path"""
        current_path = self.comfy_path_input.text()
        start_dir = current_path if os.path.exists(current_path) else os.path.expanduser("~")
        
        path = QFileDialog.getExistingDirectory(self, "Select ComfyUI Directory", start_dir)
        if path:
            self.comfy_path_input.setText(path)
    
    def save_settings(self):
        """Save settings to config"""
        # Update config with form values
        self.config.set("comfy_path", self.comfy_path_input.text())
        self.config.set("api_key", self.api_key_input.text())
        self.config.set("max_concurrent_downloads", self.max_downloads_input.value())
        self.config.set("download_threads", self.threads_input.value())
        self.config.set("download_model", self.download_model_check.isChecked())
        self.config.set("download_images", self.download_images_check.isChecked())
        self.config.set("download_nsfw", self.download_nsfw_check.isChecked())
        self.config.set("create_html", self.create_html_check.isChecked())
        self.config.set("auto_open_html", self.auto_open_html_check.isChecked())
        self.config.set("top_image_count", self.max_images_input.value())
        
        # Save config
        self.config.save()
        
        # Update status
        self.status_bar.showMessage("Settings saved", 3000)
        self.log("Settings saved", "success")
    
    def on_queue_updated(self, queue_size):
        """Handle queue update event"""
        # Update status bar
        if queue_size > 0:
            self.status_bar.showMessage(f"Download queue: {queue_size} items")
        else:
            self.status_bar.showMessage("Download queue empty")
    
    def on_task_updated(self, task):
        """Handle task update event"""
        # Update queue display
        self.queue_widget.update_task(task)
        
        # Log status changes
        if task.status == "completed":
            self.log(f"Download completed: {task.model_info.name if task.model_info else task.url}", "success")
        elif task.status == "failed":
            self.log(f"Download failed: {task.error_message or task.url}", "error")
    
    def cancel_task(self, url):
        """Cancel a download task"""
        if self.download_manager.cancel_download(url):
            self.log(f"Download canceled: {url}", "warning")
        
    def clear_queue(self):
        """Clear the download queue"""
        self.download_manager.clear_download_queue()
        self.log("Download queue cleared", "warning")
    
    def closeEvent(self, event):
        """Handle window close event"""
        # Save config
        self.config.save()
        
        # Shut down download manager
        self.download_manager.shutdown()
        
        # Accept the event
        event.accept()
