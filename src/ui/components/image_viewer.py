from typing import Dict, List, Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QScrollArea, QApplication, QGroupBox
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QPixmap
from pathlib import Path


class ImageViewer(QWidget):
    """Widget for viewing images with metadata"""
    
    prompt_copied = Signal(str)
    
    def __init__(self, theme: Dict, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.current_image_index = 0
        self.images = []
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI components"""
        layout = QVBoxLayout(self)
        
        # Image display
        image_container = QWidget()
        image_container.setMinimumSize(600, 400)
        image_container.setStyleSheet(f"background-color: {self.theme['background']}; border-radius: 8px;")
        self.image_container = image_container
        
        image_layout = QVBoxLayout(image_container)
        
        # Image label
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("background-color: transparent;")
        
        image_layout.addWidget(self.image_label)
        
        layout.addWidget(image_container)
        
        # Navigation controls
        nav_layout = QHBoxLayout()
        
        self.prev_btn = QPushButton("Previous")
        self.prev_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.theme['accent']};
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
            }}
            QPushButton:hover {{
                background-color: {self.theme['accent_hover']};
            }}
            QPushButton:disabled {{
                background-color: {self.theme['text_tertiary']};
                color: {self.theme['text_secondary']};
            }}
        """)
        self.prev_btn.clicked.connect(self.show_previous_image)
        
        self.image_counter = QLabel("0 / 0")
        self.image_counter.setAlignment(Qt.AlignCenter)
        self.image_counter.setStyleSheet(f"font-size: 14px; color: {self.theme['text_secondary']};")
        
        self.next_btn = QPushButton("Next")
        self.next_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.theme['accent']};
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
            }}
            QPushButton:hover {{
                background-color: {self.theme['accent_hover']};
            }}
            QPushButton:disabled {{
                background-color: {self.theme['text_tertiary']};
                color: {self.theme['text_secondary']};
            }}
        """)
        self.next_btn.clicked.connect(self.show_next_image)
        
        nav_layout.addWidget(self.prev_btn)
        nav_layout.addWidget(self.image_counter)
        nav_layout.addWidget(self.next_btn)
        
        layout.addLayout(nav_layout)
        
        # Image metadata
        self.metadata_group = QGroupBox("Image Details")
        self.metadata_group.setStyleSheet(f"""
            QGroupBox {{
                border: 1px solid {self.theme['border']};
                border-radius: 8px;
                margin-top: 1ex;
                font-weight: bold;
                color: {self.theme['text']};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }}
        """)
        
        metadata_layout = QVBoxLayout(self.metadata_group)
        
        # Prompt
        prompt_layout = QVBoxLayout()
        prompt_header = QHBoxLayout()
        
        prompt_label = QLabel("Prompt:")
        prompt_label.setStyleSheet(f"font-weight: bold; color: {self.theme['text_secondary']};")
        
        self.copy_prompt_btn = QPushButton("Copy")
        self.copy_prompt_btn.setToolTip("Copy prompt to clipboard")
        self.copy_prompt_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.theme['accent']};
                color: white;
                border: none;
                border-radius: 4px;
                padding: 2px 8px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {self.theme['accent_hover']};
            }}
        """)
        self.copy_prompt_btn.clicked.connect(self.copy_prompt)
        
        prompt_header.addWidget(prompt_label)
        prompt_header.addStretch()
        prompt_header.addWidget(self.copy_prompt_btn)
        
        self.prompt_text = QTextEdit()
        self.prompt_text.setReadOnly(True)
        self.prompt_text.setStyleSheet(f"""
            QTextEdit {{
                background-color: {self.theme['input_bg']};
                color: {self.theme['text']};
                border: 1px solid {self.theme['input_border']};
                border-radius: 4px;
                padding: 4px;
            }}
        """)
        self.prompt_text.setMaximumHeight(100)
        
        prompt_layout.addLayout(prompt_header)
        prompt_layout.addWidget(self.prompt_text)
        
        # Other metadata
        info_layout = QHBoxLayout()
        
        # Left column
        left_info = QVBoxLayout()
        
        checkpoint_label = QLabel("Checkpoint:")
        checkpoint_label.setStyleSheet(f"font-weight: bold; color: {self.theme['text_secondary']};")
        
        self.checkpoint_value = QLabel("N/A")
        self.checkpoint_value.setStyleSheet(f"color: {self.theme['text']};")
        self.checkpoint_value.setTextInteractionFlags(Qt.TextSelectableByMouse)
        
        loras_label = QLabel("LoRAs:")
        loras_label.setStyleSheet(f"font-weight: bold; color: {self.theme['text_secondary']};")
        
        self.loras_value = QLabel("N/A")
        self.loras_value.setStyleSheet(f"color: {self.theme['text']};")
        self.loras_value.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.loras_value.setWordWrap(True)
        
        left_info.addWidget(checkpoint_label)
        left_info.addWidget(self.checkpoint_value)
        left_info.addWidget(loras_label)
        left_info.addWidget(self.loras_value)
        
        # Right column
        right_info = QVBoxLayout()
        
        stats_label = QLabel("Stats:")
        stats_label.setStyleSheet(f"font-weight: bold; color: {self.theme['text_secondary']};")
        
        self.stats_value = QLabel("N/A")
        self.stats_value.setStyleSheet(f"color: {self.theme['text']};")
        
        right_info.addWidget(stats_label)
        right_info.addWidget(self.stats_value)
        right_info.addStretch()
        
        info_layout.addLayout(left_info)
        info_layout.addLayout(right_info)
        
        metadata_layout.addLayout(prompt_layout)
        metadata_layout.addLayout(info_layout)
        
        layout.addWidget(self.metadata_group)
        
        # Initialize with empty state
        self.clear_display()
    
    def set_theme(self, theme):
        """Update the theme"""
        self.theme = theme
        
        # Update image container
        self.image_container.setStyleSheet(f"background-color: {self.theme['background']}; border-radius: 8px;")
        
        # Update navigation buttons
        nav_button_style = f"""
            QPushButton {{
                background-color: {self.theme['accent']};
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
            }}
            QPushButton:hover {{
                background-color: {self.theme['accent_hover']};
            }}
            QPushButton:disabled {{
                background-color: {self.theme['text_tertiary']};
                color: {self.theme['text_secondary']};
            }}
        """
        self.prev_btn.setStyleSheet(nav_button_style)
        self.next_btn.setStyleSheet(nav_button_style)
        
        # Update image counter
        self.image_counter.setStyleSheet(f"font-size: 14px; color: {self.theme['text_secondary']};")
        
        # Update metadata group
        self.metadata_group.setStyleSheet(f"""
            QGroupBox {{
                border: 1px solid {self.theme['border']};
                border-radius: 8px;
                margin-top: 1ex;
                font-weight: bold;
                color: {self.theme['text']};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }}
        """)
        
        # Update prompt text
        self.prompt_text.setStyleSheet(f"""
            QTextEdit {{
                background-color: {self.theme['input_bg']};
                color: {self.theme['text']};
                border: 1px solid {self.theme['input_border']};
                border-radius: 4px;
                padding: 4px;
            }}
        """)
        
        # Update copy button
        self.copy_prompt_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.theme['accent']};
                color: white;
                border: none;
                border-radius: 4px;
                padding: 2px 8px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {self.theme['accent_hover']};
            }}
        """)
        
        # Update labels
        for label in self.findChildren(QLabel):
            if "font-weight: bold" in label.styleSheet():
                label.setStyleSheet(f"font-weight: bold; color: {self.theme['text_secondary']};")
            else:
                label.setStyleSheet(f"color: {self.theme['text']};")
    
    def set_images(self, images: List[Dict]):
        """Set the images to display"""
        self.images = images
        self.current_image_index = 0
        self.update_navigation()
        if self.images:
            self.show_image(0)
        else:
            self.clear_display()
    
    def show_image(self, index):
        """Show the image at the specified index"""
        if not self.images or index < 0 or index >= len(self.images):
            return
            
        img = self.images[index]
        
        # Load and display image
        if 'local_path' in img and Path(img['local_path']).exists():
            pixmap = QPixmap(img['local_path'])
            self.image_label.setPixmap(pixmap.scaled(
                self.image_container.width() - 20, 
                self.image_container.height() - 20,
                Qt.KeepAspectRatio, 
                Qt.SmoothTransformation
            ))
        else:
            self.image_label.setText("Image not available")
            
        # Update metadata
        prompt = (img.get('meta') or {}).get('prompt', 'N/A')
        self.prompt_text.setText(prompt)
        
        checkpoint = (img.get('meta') or {}).get('Model', 'N/A')
        self.checkpoint_value.setText(checkpoint)
        
        loras = ', '.join(
            r.get('name') for r in (img.get('meta') or {}).get('resources', [])
            if r.get('type') == 'lora'
        )
        self.loras_value.setText(loras if loras else 'N/A')
        
        stats = img.get('stats', {})
        stats_str = f"👍 {stats.get('likeCount',0)} | ❤️ {stats.get('heartCount',0)} | 😂 {stats.get('laughCount',0)}"
        self.stats_value.setText(stats_str)
        
        # Update counter
        self.image_counter.setText(f"{index + 1} / {len(self.images)}")
        
        # Update current index
        self.current_image_index = index
        
        # Update navigation buttons
        self.update_navigation()
    
    def show_next_image(self):
        """Show the next image"""
        if self.current_image_index < len(self.images) - 1:
            self.show_image(self.current_image_index + 1)
    
    def show_previous_image(self):
        """Show the previous image"""
        if self.current_image_index > 0:
            self.show_image(self.current_image_index - 1)
    
    def update_navigation(self):
        """Update navigation button states"""
        self.prev_btn.setEnabled(self.current_image_index > 0)
        self.next_btn.setEnabled(self.current_image_index < len(self.images) - 1)
        
        if not self.images:
            self.image_counter.setText("0 / 0")
            self.prev_btn.setEnabled(False)
            self.next_btn.setEnabled(False)
    
    def clear_display(self):
        """Clear the image display"""
        self.image_label.clear()
        self.image_label.setText("No images available")
        self.prompt_text.clear()
        self.checkpoint_value.setText("N/A")
        self.loras_value.setText("N/A")
        self.stats_value.setText("N/A")
        self.image_counter.setText("0 / 0")
        self.prev_btn.setEnabled(False)
        self.next_btn.setEnabled(False)
    
    def copy_prompt(self):
        """Copy the current prompt to clipboard"""
        prompt = self.prompt_text.toPlainText()
        if prompt and prompt != 'N/A':
            clipboard = QApplication.clipboard()
            clipboard.setText(prompt)
            self.prompt_copied.emit(prompt)
    
    def resizeEvent(self, event):
        """Handle resize event to update image scaling"""
        super().resizeEvent(event)
        if self.images and self.current_image_index < len(self.images):
            img = self.images[self.current_image_index]
            if 'local_path' in img and Path(img['local_path']).exists():
                pixmap = QPixmap(img['local_path'])
                self.image_label.setPixmap(pixmap.scaled(
                    self.image_container.width() - 20, 
                    self.image_container.height() - 20,
                    Qt.KeepAspectRatio, 
                    Qt.SmoothTransformation
                ))