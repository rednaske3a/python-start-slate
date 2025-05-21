from typing import Dict

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QProgressBar, QGroupBox
)

from src.utils.formatting import format_size

class StorageInfoWidget(QWidget):
    """Compact widget for displaying storage info in the gallery tab"""
    
    def __init__(self, theme: Dict, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI components"""
        layout = QVBoxLayout(self)
        
        # Storage usage bar
        storage_group = self.create_styled_group_box("Disk Space")
        storage_layout = QVBoxLayout(storage_group)
        
        # Usage bar
        self.usage_bar = QProgressBar()
        self.usage_bar.setTextVisible(True)
        self.usage_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid {self.theme['border']};
                border-radius: 5px;
                text-align: center;
                height: 20px;
                color: {self.theme['text']};
                background-color: {self.theme['input_bg']};
            }}
            QProgressBar::chunk {{
                background-color: {self.theme['accent']};
                border-radius: 4px;
            }}
        """)
        
        # Usage text
        self.usage_text = QLabel("Loading storage information...")
        self.usage_text.setStyleSheet(f"color: {self.theme['text']};")
        
        storage_layout.addWidget(self.usage_bar)
        storage_layout.addWidget(self.usage_text)
        
        layout.addWidget(storage_group)
        
        # Category breakdown
        model_group = self.create_styled_group_box("Model Types")
        model_layout = QVBoxLayout(model_group)
        
        # Category bars
        self.category_bars = {}
        for category, color in [
            ("Checkpoints", "#ed7d31"),
            ("LoRAs", "#5b9bd5"),
            ("Embeddings", "#70ad47")
        ]:
            cat_bar = QProgressBar()
            cat_bar.setFormat(f"{category}: %p% (0 MB)")
            cat_bar.setTextVisible(True)
            cat_bar.setStyleSheet(f"""
                QProgressBar {{
                    border: 1px solid {self.theme['border']};
                    border-radius: 4px;
                    text-align: center;
                    height: 16px;
                    color: {self.theme['text']};
                    background-color: {self.theme['input_bg']};
                    margin-bottom: 5px;
                }}
                QProgressBar::chunk {{
                    background-color: {color};
                    border-radius: 3px;
                }}
            """)
            
            model_layout.addWidget(cat_bar)
            self.category_bars[category] = cat_bar
        
        layout.addWidget(model_group)
    
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
        
        # Update usage bar
        self.usage_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid {self.theme['border']};
                border-radius: 5px;
                text-align: center;
                height: 20px;
                color: {self.theme['text']};
                background-color: {self.theme['input_bg']};
            }}
            QProgressBar::chunk {{
                background-color: {self.theme['accent']};
                border-radius: 4px;
            }}
        """)
        
        # Update usage text
        self.usage_text.setStyleSheet(f"color: {self.theme['text']};")
        
        # Update category bars
        for category, color in [
            ("Checkpoints", "#ed7d31"),
            ("LoRAs", "#5b9bd5"),
            ("Embeddings", "#70ad47")
        ]:
            if category in self.category_bars:
                self.category_bars[category].setStyleSheet(f"""
                    QProgressBar {{
                        border: 1px solid {self.theme['border']};
                        border-radius: 4px;
                        text-align: center;
                        height: 16px;
                        color: {self.theme['text']};
                        background-color: {self.theme['input_bg']};
                        margin-bottom: 5px;
                    }}
                    QProgressBar::chunk {{
                        background-color: {color};
                        border-radius: 3px;
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
        self.usage_text.setText(
            f"Used: {format_size(used_size)} of {format_size(total_size)} "
            f"({usage_percent}%) - Free: {format_size(free_size)}"
        )
        
        # Update category bars
        for category, size in category_sizes.items():
            if category in self.category_bars:
                percent = int((size / total_size) * 100) if total_size > 0 else 0
                self.category_bars[category].setValue(percent)
                self.category_bars[category].setFormat(f"{category}: {percent}% ({format_size(size)})")