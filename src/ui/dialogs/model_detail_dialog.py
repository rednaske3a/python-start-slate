
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QScrollArea, QGridLayout, QSplitter, QTextEdit, QWidget
)
from PySide6.QtCore import Qt, Signal, QSize, QRect, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QPixmap, QIcon, QColor, QPainter, QFont, QCursor

import os
import sys
from pathlib import Path
import subprocess
import shutil
from typing import Dict, List, Optional

from src.utils.formatting import format_size, truncate_text
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ImageThumbnail(QLabel):
    """Clickable image thumbnail widget"""
    
    clicked = Signal(dict)  # image data
    
    def __init__(self, image_data: Dict, theme: Dict, parent=None):
        super().__init__(parent)
        self.image_data = image_data
        self.theme = theme
        
        # Set up widget
        self.setCursor(Qt.PointingHandCursor)
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumSize(120, 120)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {self.theme['secondary']};
                border-radius: 4px;
                border: 1px solid {self.theme['border']};
            }}
            QLabel:hover {{
                border: 2px solid {self.theme['accent']};
            }}
        """)
        
        # Load image
        self.load_image()
    
    def load_image(self):
        """Load image from data"""
        # Get path to image
        if "local_path" in self.image_data and os.path.exists(self.image_data["local_path"]):
            image_path = self.image_data["local_path"]
            
            # Load pixmap
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                # Scale pixmap to fit widget while maintaining aspect ratio
                self.setPixmap(pixmap.scaled(
                    self.size(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                ))
                return
        
        # If we get here, image loading failed
        self.setText("No Image")
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {self.theme['secondary']};
                color: {self.theme['text_secondary']};
                border-radius: 4px;
                border: 1px solid {self.theme['border']};
            }}
        """)
    
    def mousePressEvent(self, event):
        """Handle mouse press events"""
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.image_data)
        super().mousePressEvent(event)
    
    def resizeEvent(self, event):
        """Handle resize events"""
        # Reload image at new size
        if hasattr(self, 'image_data'):
            self.load_image()
        super().resizeEvent(event)
    
    def set_theme(self, theme):
        """Update theme"""
        self.theme = theme
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {self.theme['secondary']};
                border-radius: 4px;
                border: 1px solid {self.theme['border']};
            }}
            QLabel:hover {{
                border: 2px solid {self.theme['accent']};
            }}
        """)
        
        # Reload image
        self.load_image()


class ImageViewerPanel(QFrame):
    """Panel for viewing image details"""
    
    closed = Signal()
    
    def __init__(self, image_data: Dict, theme: Dict, parent=None):
        super().__init__(parent)
        self.image_data = image_data
        self.theme = theme
        
        # Set up frame
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {self.theme['card']};
                border-radius: 8px;
                border: 1px solid {self.theme['border']};
            }}
        """)
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI components"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # Header with close button
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)
        
        # Title
        title = QLabel("Image Details")
        title.setStyleSheet(f"""
            font-size: 16px;
            font-weight: bold;
            color: {self.theme['text']};
        """)
        
        # Close button
        close_btn = QPushButton("×")
        close_btn.setFixedSize(24, 24)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {self.theme['text_secondary']};
                border: none;
                font-size: 18px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                color: {self.theme['danger']};
            }}
        """)
        close_btn.clicked.connect(self.closed.emit)
        
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(close_btn)
        
        # Image preview
        self.image_preview = QLabel()
        self.image_preview.setAlignment(Qt.AlignCenter)
        self.image_preview.setMinimumHeight(200)
        self.image_preview.setStyleSheet(f"background-color: {self.theme['secondary']};")
        self.load_image()
        
        # Prompt section
        prompt_section = QFrame()
        prompt_section.setFrameShape(QFrame.StyledPanel)
        prompt_section.setStyleSheet(f"background-color: {self.theme['secondary']}; border-radius: 4px;")
        prompt_layout = QVBoxLayout(prompt_section)
        
        # Prompt label
        prompt_label = QLabel("Prompt")
        prompt_label.setStyleSheet(f"color: {self.theme['text']}; font-weight: bold; font-size: 14px;")
        
        # Get prompt text from image data
        prompt_text = ""
        if "meta" in self.image_data and self.image_data["meta"]:
            prompt_text = self.image_data["meta"].get("prompt", "")
        
        # Prompt text edit
        self.prompt_edit = QTextEdit()
        self.prompt_edit.setPlainText(prompt_text)
        self.prompt_edit.setReadOnly(True)
        self.prompt_edit.setStyleSheet(f"""
            QTextEdit {{
                background-color: {self.theme['input_bg']};
                color: {self.theme['text']};
                border: 1px solid {self.theme['border']};
                border-radius: 4px;
            }}
        """)
        
        # Add widgets to layout
        prompt_layout.addWidget(prompt_label)
        prompt_layout.addWidget(self.prompt_edit)
        
        # Stats section
        stats_section = self.create_stats_section()
        
        # Add components to main layout
        layout.addLayout(header_layout)
        layout.addWidget(self.image_preview, 1)  # Give image preview more space
        layout.addWidget(prompt_section)
        layout.addWidget(stats_section)
    
    def create_stats_section(self):
        """Create section with image stats"""
        section = QFrame()
        section.setFrameShape(QFrame.StyledPanel)
        section.setStyleSheet(f"background-color: {self.theme['secondary']}; border-radius: 4px;")
        layout = QHBoxLayout(section)
        
        # Get stats from image data
        stats = self.image_data.get("stats", {})
        reactions = [
            ("👍", stats.get("likeCount", 0)),
            ("❤️", stats.get("heartCount", 0)),
            ("😂", stats.get("laughCount", 0))
        ]
        
        # Add reaction stats
        for emoji, count in reactions:
            stat_label = QLabel(f"{emoji} {count}")
            stat_label.setStyleSheet(f"color: {self.theme['text']}; font-size: 14px;")
            layout.addWidget(stat_label)
        
        layout.addStretch()
        
        return section
    
    def load_image(self):
        """Load image from data"""
        # Get path to image
        if "local_path" in self.image_data and os.path.exists(self.image_data["local_path"]):
            image_path = self.image_data["local_path"]
            
            # Load pixmap
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                # Scale pixmap to fit widget while maintaining aspect ratio
                self.image_preview.setPixmap(pixmap.scaled(
                    self.image_preview.width(), 
                    self.image_preview.height(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                ))
                return
        
        # If we get here, image loading failed
        self.image_preview.setText("Image not found")
        self.image_preview.setStyleSheet(f"""
            background-color: {self.theme['secondary']};
            color: {self.theme['text_secondary']};
        """)
    
    def resizeEvent(self, event):
        """Handle resize events"""
        # Reload image at new size
        if hasattr(self, 'image_data'):
            self.load_image()
        super().resizeEvent(event)
    
    def set_theme(self, theme):
        """Update theme"""
        self.theme = theme
        
        # Update frame style
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {self.theme['card']};
                border-radius: 8px;
                border: 1px solid {self.theme['border']};
            }}
        """)
        
        # Update components
        title = self.findChild(QLabel, "", Qt.FindChildrenRecursively)
        if title and title.text() == "Image Details":
            title.setStyleSheet(f"""
                font-size: 16px;
                font-weight: bold;
                color: {self.theme['text']};
            """)
        
        # Update close button
        for button in self.findChildren(QPushButton):
            if button.text() == "×":
                button.setStyleSheet(f"""
                    QPushButton {{
                        background-color: transparent;
                        color: {self.theme['text_secondary']};
                        border: none;
                        font-size: 18px;
                        font-weight: bold;
                    }}
                    QPushButton:hover {{
                        color: {self.theme['danger']};
                    }}
                """)
        
        # Update image preview
        self.image_preview.setStyleSheet(f"background-color: {self.theme['secondary']};")
        self.load_image()
        
        # Update prompt section
        for frame in self.findChildren(QFrame):
            frame.setStyleSheet(f"background-color: {self.theme['secondary']}; border-radius: 4px;")
        
        # Update text edit
        self.prompt_edit.setStyleSheet(f"""
            QTextEdit {{
                background-color: {self.theme['input_bg']};
                color: {self.theme['text']};
                border: 1px solid {self.theme['border']};
                border-radius: 4px;
            }}
        """)
        
        # Update labels
        for label in self.findChildren(QLabel):
            if label != self.image_preview and label.text() != "Image Details":
                if "font-weight: bold" in label.styleSheet():
                    label.setStyleSheet(f"color: {self.theme['text']}; font-weight: bold; font-size: 14px;")
                else:
                    label.setStyleSheet(f"color: {self.theme['text']}; font-size: 14px;")


class ModelDetailDialog(QDialog):
    """Dialog for displaying model details"""
    
    def __init__(self, model_data: Dict, theme: Dict, parent=None):
        super().__init__(parent)
        self.model_data = model_data
        self.theme = theme
        self.parent_window = parent
        self.current_image_panel = None
        
        # Set up dialog
        self.setWindowTitle(f"Model Details: {model_data.get('name', 'Unknown')}")
        self.resize(900, 700)
        self.setStyleSheet(f"background-color: {self.theme['primary']};")
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI components"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Create splitter for main content
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setChildrenCollapsible(False)
        
        # Left side - image gallery
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        # Gallery title
        gallery_title = QLabel("Image Gallery")
        gallery_title.setStyleSheet(f"""
            font-size: 16px;
            font-weight: bold;
            color: {self.theme['text']};
            margin-bottom: 10px;
        """)
        left_layout.addWidget(gallery_title)
        
        # Image grid
        self.image_grid = QWidget()
        grid_layout = QGridLayout(self.image_grid)
        grid_layout.setContentsMargins(0, 0, 0, 0)
        grid_layout.setSpacing(10)
        
        # Add images to grid
        images = self.model_data.get("images", [])
        if images:
            row, col = 0, 0
            cols = 3  # 3x3 grid
            
            for i, image in enumerate(images[:9]):  # Limit to 9 images
                thumbnail = ImageThumbnail(image, self.theme)
                thumbnail.clicked.connect(self.show_image_details)
                grid_layout.addWidget(thumbnail, row, col)
                
                col += 1
                if col >= cols:
                    col = 0
                    row += 1
        else:
            # No images message
            no_images = QLabel("No images available")
            no_images.setAlignment(Qt.AlignCenter)
            no_images.setStyleSheet(f"color: {self.theme['text_secondary']}; font-style: italic;")
            grid_layout.addWidget(no_images, 0, 0, 1, 3)
        
        # Add image grid to scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.image_grid)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                background-color: {self.theme['primary']};
                border: none;
            }}
            QScrollBar:vertical {{
                background: {self.theme['primary']};
                width: 14px;
                margin: 0px;
            }}
            QScrollBar::handle:vertical {{
                background: {self.theme['secondary']};
                min-height: 20px;
                border-radius: 7px;
                margin: 2px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical {{
                height: 0px;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
            }}
        """)
        
        left_layout.addWidget(scroll)
        
        # Right side - model info
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(15)
        
        # Model title section
        title_section = QFrame()
        title_section.setFrameShape(QFrame.StyledPanel)
        title_section.setStyleSheet(f"""
            background-color: {self.theme['card']};
            border-radius: 8px;
            border: 1px solid {self.theme['border']};
            padding: 10px;
        """)
        title_layout = QVBoxLayout(title_section)
        
        # Model name
        name_label = QLabel(self.model_data.get("name", "Unknown Model"))
        name_label.setWordWrap(True)
        name_label.setStyleSheet(f"""
            font-size: 18px;
            font-weight: bold;
            color: {self.theme['text']};
        """)
        
        # Model creator
        creator_label = QLabel(f"By: {self.model_data.get('creator', 'Unknown')}")
        creator_label.setStyleSheet(f"color: {self.theme['text_secondary']};")
        
        title_layout.addWidget(name_label)
        title_layout.addWidget(creator_label)
        
        # Model info section
        info_section = QFrame()
        info_section.setFrameShape(QFrame.StyledPanel)
        info_section.setStyleSheet(f"""
            background-color: {self.theme['card']};
            border-radius: 8px;
            border: 1px solid {self.theme['border']};
            padding: 10px;
        """)
        info_layout = QVBoxLayout(info_section)
        
        # Info title
        info_title = QLabel("Model Information")
        info_title.setStyleSheet(f"""
            font-size: 16px;
            font-weight: bold;
            color: {self.theme['text']};
            margin-bottom: 10px;
        """)
        info_layout.addWidget(info_title)
        
        # Info grid
        info_grid = QGridLayout()
        info_grid.setColumnStretch(1, 1)
        info_grid.setVerticalSpacing(8)
        info_grid.setHorizontalSpacing(15)
        
        # Add info rows
        info_items = [
            ("Type:", self.model_data.get("type", "Unknown")),
            ("Base Model:", self.model_data.get("base_model", "Unknown")),
            ("Version:", self.model_data.get("version_name", "Unknown")),
            ("Size:", format_size(self.model_data.get("size", 0))),
            ("Downloaded:", self.model_data.get("download_date", "Unknown")),
            ("Last Updated:", self.model_data.get("last_updated", "Unknown")),
            ("Path:", self.model_data.get("path", "Unknown"))
        ]
        
        for i, (label_text, value_text) in enumerate(info_items):
            label = QLabel(label_text)
            label.setStyleSheet(f"color: {self.theme['text_secondary']};")
            
            value = QLabel(value_text)
            value.setStyleSheet(f"color: {self.theme['text']};")
            value.setWordWrap(True)
            
            info_grid.addWidget(label, i, 0)
            info_grid.addWidget(value, i, 1)
        
        info_layout.addLayout(info_grid)
        
        # Add open folder button for path
        path_layout = QHBoxLayout()
        path_layout.setContentsMargins(0, 10, 0, 0)
        
        open_folder_btn = QPushButton("Open Folder")
        open_folder_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.theme['secondary']};
                color: {self.theme['text']};
                border: 1px solid {self.theme['border']};
                border-radius: 4px;
                padding: 8px 16px;
            }}
            QPushButton:hover {{
                background-color: {self.theme['card_hover']};
                border-color: {self.theme['accent']};
            }}
        """)
        open_folder_btn.clicked.connect(self.open_model_folder)
        
        copy_path_btn = QPushButton("Copy Path")
        copy_path_btn.setStyleSheet(open_folder_btn.styleSheet())
        copy_path_btn.clicked.connect(self.copy_model_path)
        
        path_layout.addWidget(open_folder_btn)
        path_layout.addWidget(copy_path_btn)
        path_layout.addStretch()
        
        info_layout.addLayout(path_layout)
        
        # Description section
        desc_section = QFrame()
        desc_section.setFrameShape(QFrame.StyledPanel)
        desc_section.setStyleSheet(info_section.styleSheet())
        desc_layout = QVBoxLayout(desc_section)
        
        # Description title
        desc_title = QLabel("Description")
        desc_title.setStyleSheet(info_title.styleSheet())
        desc_layout.addWidget(desc_title)
        
        # Description text
        desc_text = QTextEdit()
        desc_text.setReadOnly(True)
        desc_text.setPlainText(self.model_data.get("description", "No description available."))
        desc_text.setStyleSheet(f"""
            QTextEdit {{
                background-color: {self.theme['input_bg']};
                color: {self.theme['text']};
                border: 1px solid {self.theme['border']};
                border-radius: 4px;
            }}
        """)
        desc_layout.addWidget(desc_text)
        
        # Tags section
        tags_section = QFrame()
        tags_section.setFrameShape(QFrame.StyledPanel)
        tags_section.setStyleSheet(info_section.styleSheet())
        tags_layout = QVBoxLayout(tags_section)
        
        # Tags title
        tags_title = QLabel("Tags")
        tags_title.setStyleSheet(info_title.styleSheet())
        tags_layout.addWidget(tags_title)
        
        # Tags flow layout
        tags_flow = QHBoxLayout()
        tags_flow.setSpacing(5)
        
        # Add tags
        tags = self.model_data.get("tags", [])
        tag_count = 0
        
        for tag in tags:
            # Create tag chip
            tag_chip = QFrame()
            tag_chip.setStyleSheet(f"""
                background-color: {self.theme['secondary']};
                border-radius: 4px;
                padding: 3px;
            """)
            tag_layout = QHBoxLayout(tag_chip)
            tag_layout.setContentsMargins(8, 3, 8, 3)
            tag_layout.setSpacing(0)
            
            tag_label = QLabel(tag)
            tag_label.setStyleSheet(f"color: {self.theme['text_secondary']};")
            tag_layout.addWidget(tag_label)
            
            tags_flow.addWidget(tag_chip)
            tag_count += 1
            
            # Wrap to next line if too many tags
            if tag_count % 3 == 0:
                tags_flow.addStretch()
                tags_layout.addLayout(tags_flow)
                tags_flow = QHBoxLayout()
                tags_flow.setSpacing(5)
        
        # Add remaining tags
        if tags_flow.count() > 0:
            tags_flow.addStretch()
            tags_layout.addLayout(tags_flow)
        
        if not tags:
            # No tags message
            no_tags = QLabel("No tags available")
            no_tags.setStyleSheet(f"color: {self.theme['text_secondary']}; font-style: italic;")
            tags_layout.addWidget(no_tags)
        
        # Add sections to right panel
        right_layout.addWidget(title_section)
        right_layout.addWidget(info_section)
        right_layout.addWidget(desc_section)
        right_layout.addWidget(tags_section)
        
        # Add panels to splitter
        self.splitter.addWidget(left_panel)
        self.splitter.addWidget(right_panel)
        
        # Set initial splitter sizes (40% left, 60% right)
        self.splitter.setSizes([350, 550])
        
        # Add splitter to layout
        layout.addWidget(self.splitter)
        
        # Add close button at bottom
        button_layout = QHBoxLayout()
        close_btn = QPushButton("Close")
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.theme['accent']};
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 30px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {self.theme['accent_hover']};
            }}
        """)
        close_btn.clicked.connect(self.accept)
        
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        layout.addLayout(button_layout)
    
    def show_image_details(self, image_data):
        """Show image details panel"""
        # Remove existing panel if any
        if self.current_image_panel:
            self.current_image_panel.deleteLater()
            self.current_image_panel = None
        
        # Create new panel
        self.current_image_panel = ImageViewerPanel(image_data, self.theme, self)
        self.current_image_panel.closed.connect(self.close_image_details)
        
        # Position panel
        self.current_image_panel.setGeometry(
            self.width() // 4,
            self.height() // 4,
            self.width() // 2,
            self.height() // 2
        )
        
        # Show with animation
        self.current_image_panel.show()
    
    def close_image_details(self):
        """Close image details panel"""
        if self.current_image_panel:
            self.current_image_panel.deleteLater()
            self.current_image_panel = None
    
    def open_model_folder(self):
        """Open model folder in file explorer"""
        path = self.model_data.get("path", "")
        if not path or not os.path.exists(path):
            return
        
        # Open folder based on platform
        try:
            if sys.platform == "win32":
                os.startfile(path)
            elif sys.platform == "darwin":  # macOS
                subprocess.call(["open", path])
            else:  # Linux
                subprocess.call(["xdg-open", path])
        except Exception as e:
            logger.error(f"Error opening folder: {str(e)}")
    
    def copy_model_path(self):
        """Copy model path to clipboard"""
        path = self.model_data.get("path", "")
        if not path:
            return
            
        # Copy to clipboard
        from PySide6.QtGui import QGuiApplication
        clipboard = QGuiApplication.clipboard()
        clipboard.setText(path)
        
        # Show toast notification if available
        if self.parent_window and hasattr(self.parent_window, "toast_manager"):
            self.parent_window.toast_manager.show_toast(
                "Path copied to clipboard",
                "success",
                duration=2000
            )
