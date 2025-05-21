from typing import Dict

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QProgressBar, QGroupBox
)

from src.utils.formatting import format_size

class StorageUsageWidget(QWidget):
    """Widget for displaying storage usage information"""
    
    def __init__(self, theme: Dict, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI components"""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Storage Usage")
        title.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {self.theme['text']};")
        layout.addWidget(title)
        
        # Storage usage bar
        self.usage_bar = QProgressBar()
        self.usage_bar.setTextVisible(True)
        self.usage_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid {self.theme['border']};
                border-radius: 5px;
                text-align: center;
                height: 25px;
                color: {self.theme['text']};
                background-color: {self.theme['input_bg']};
            }}
            QProgressBar::chunk {{
                background-color: {self.theme['accent']};
                border-radius: 5px;
            }}
        """)
        layout.addWidget(self.usage_bar)
        
        # Usage details
        self.usage_details = QLabel()
        self.usage_details.setStyleSheet(f"color: {self.theme['text']};")
        layout.addWidget(self.usage_details)
        
        # Category breakdown
        category_group = self.create_styled_group_box("Category Breakdown")
        category_layout = QVBoxLayout(category_group)
        
        self.category_bars = {}
        for category, color in [
            ("LoRAs", "#5b9bd5"), 
            ("Checkpoints", "#ed7d31"), 
            ("Embeddings", "#70ad47"), 
            ("Other", "#7030a0")
        ]:
            cat_layout = QHBoxLayout()
            cat_label = QLabel(category)
            cat_label.setFixedWidth(100)
            cat_label.setStyleSheet(f"color: {self.theme['text']};")
            cat_bar = QProgressBar()
            cat_bar.setTextVisible(True)
            cat_bar.setStyleSheet(f"""
                QProgressBar {{
                    border: 1px solid {self.theme['border']};
                    border-radius: 3px;
                    text-align: center;
                    height: 18px;
                    color: {self.theme['text']};
                    background-color: {self.theme['input_bg']};
                }}
                QProgressBar::chunk {{
                    background-color: {color};
                    border-radius: 3px;
                }}
            """)
                
            cat_layout.addWidget(cat_label)
            cat_layout.addWidget(cat_bar)
            category_layout.addLayout(cat_layout)
            
            self.category_bars[category] = cat_bar
        
        layout.addWidget(category_group)
        
        # Refresh button
        refresh_btn = QPushButton("Refresh Storage Analysis")
        refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.theme['accent']};
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px;
            }}
            QPushButton:hover {{
                background-color: {self.theme['accent_hover']};
            }}
        """)
        refresh_btn.clicked.connect(self.refresh_requested)
        layout.addWidget(refresh_btn)
        
        layout.addStretch()
    
    def create_styled_group_box(self, title):
        """Create a styled group box"""
        group = QGroupBox(title)
        group.setStyleSheet(f"""
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
        return group
    
    def set_theme(self, theme):
        """Update the theme"""
        self.theme = theme
        
        # Update title
        for child in self.findChildren(QLabel):
            if "font-size: 16px" in child.styleSheet():
                child.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {self.theme['text']};")
            else:
                child.setStyleSheet(f"color: {self.theme['text']};")
        
        # Update usage bar
        self.usage_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid {self.theme['border']};
                border-radius: 5px;
                text-align: center;
                height: 25px;
                color: {self.theme['text']};
                background-color: {self.theme['input_bg']};
            }}
            QProgressBar::chunk {{
                background-color: {self.theme['accent']};
                border-radius: 5px;
            }}
        """)
        
        # Update category bars
        for category, color in [
            ("LoRAs", "#5b9bd5"), 
            ("Checkpoints", "#ed7d31"), 
            ("Embeddings", "#70ad47"), 
            ("Other", "#7030a0")
        ]:
            if category in self.category_bars:
                self.category_bars[category].setStyleSheet(f"""
                    QProgressBar {{
                        border: 1px solid {self.theme['border']};
                        border-radius: 3px;
                        text-align: center;
                        height: 18px;
                        color: {self.theme['text']};
                        background-color: {self.theme['input_bg']};
                    }}
                    QProgressBar::chunk {{
                        background-color: {color};
                        border-radius: 3px;
                    }}
                """)
        
        # Update refresh button
        for child in self.findChildren(QPushButton):
            child.setStyleSheet(f"""
                QPushButton {{
                    background-color: {self.theme['accent']};
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 8px;
                }}
                QPushButton:hover {{
                    background-color: {self.theme['accent_hover']};
                }}
            """)
        
        # Update group boxes
        for child in self.findChildren(QGroupBox):
            child.setStyleSheet(f"""
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
    
    def update_usage(self, total_size, free_size, category_sizes):
        """Update the storage usage display"""
        used_size = total_size - free_size
        usage_percent = int((used_size / total_size) * 100) if total_size > 0 else 0
        
        self.usage_bar.setValue(usage_percent)
        self.usage_details.setText(
            f"Used: {format_size(used_size)} of {format_size(total_size)} "
            f"({usage_percent}%) - Free: {format_size(free_size)}"
        )
        
        # Update category bars
        for category, size in category_sizes.items():
            if category in self.category_bars:
                percent = int((size / total_size) * 100) if total_size > 0 else 0
                self.category_bars[category].setValue(percent)
                self.category_bars[category].setFormat(f"{percent}% ({format_size(size)})")
    
    def refresh_requested(self):
        """Signal to parent to refresh storage analysis"""
        parent = self.parent()
        while parent and not hasattr(parent, "refresh_storage_analysis"):
            parent = parent.parent()
            
        if parent and hasattr(parent, "refresh_storage_analysis"):
            parent.refresh_storage_analysis()