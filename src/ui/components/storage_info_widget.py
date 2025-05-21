
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar
)
from PySide6.QtCore import Qt
from typing import Dict

from src.utils.formatting import format_size


class StorageInfoWidget(QWidget):
    """Widget for displaying storage usage information"""
    
    def __init__(self, theme: Dict, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI components"""
        layout = QVBoxLayout(self)
        
        # Storage usage title
        title = QLabel("Storage Usage")
        title.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {self.theme['text']};")
        layout.addWidget(title)
        
        # Storage usage bar
        self.usage_layout = QVBoxLayout()
        self.usage_bar = QProgressBar()
        self.usage_bar.setRange(0, 100)
        self.usage_bar.setValue(0)
        self.usage_bar.setTextVisible(True)
        self.usage_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid {self.theme['border']};
                border-radius: 4px;
                background-color: {self.theme['secondary']};
                color: {self.theme['text']};
                text-align: center;
                height: 24px;
            }}
            QProgressBar::chunk {{
                background-color: {self.theme['accent']};
                border-radius: 3px;
            }}
        """)
        
        self.usage_label = QLabel("0 B / 0 B (0%)")
        self.usage_label.setStyleSheet(f"color: {self.theme['text']};")
        self.usage_layout.addWidget(self.usage_bar)
        self.usage_layout.addWidget(self.usage_label)
        
        layout.addLayout(self.usage_layout)
        
        # Model type breakdown
        self.breakdown_title = QLabel("Model Type Breakdown")
        self.breakdown_title.setStyleSheet(f"font-size: 14px; font-weight: bold; margin-top: 16px; color: {self.theme['text']};")
        layout.addWidget(self.breakdown_title)
        
        # Breakdown list
        self.breakdown_layout = QVBoxLayout()
        layout.addLayout(self.breakdown_layout)
        
        # Set margins
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Add stretch to push everything to the top
        layout.addStretch()
    
    def update_usage(self, total_size: int, free_size: int, categories: Dict[str, int]):
        """Update storage usage information"""
        # Calculate usage percentage
        used_size = total_size - free_size
        if total_size > 0:
            percentage = (used_size / total_size) * 100
        else:
            percentage = 0
        
        # Update progress bar
        self.usage_bar.setValue(int(percentage))
        
        # Update usage label
        self.usage_label.setText(
            f"{format_size(used_size)} / {format_size(total_size)} ({percentage:.1f}%)"
        )
        
        # Clear breakdown layout
        while self.breakdown_layout.count():
            item = self.breakdown_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Add category items
        for category, size in sorted(categories.items(), key=lambda x: x[1], reverse=True):
            if size == 0:
                continue
                
            # Create layout for this category
            item_layout = QHBoxLayout()
            
            # Create label with category name
            name_label = QLabel(category)
            name_label.setStyleSheet(f"color: {self.theme['text']};")
            
            # Create label with size
            size_label = QLabel(format_size(size))
            size_label.setStyleSheet(f"color: {self.theme['text_secondary']}; text-align: right;")
            size_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            
            # Add to item layout
            item_layout.addWidget(name_label)
            item_layout.addWidget(size_label)
            
            # Add to breakdown layout
            self.breakdown_layout.addLayout(item_layout)
    
    def set_theme(self, theme):
        """Update theme"""
        self.theme = theme
        
        # Update styles
        title = self.findChild(QLabel, "", Qt.FindDirectChildrenOnly)
        if title:
            title.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {self.theme['text']};")
        
        self.usage_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid {self.theme['border']};
                border-radius: 4px;
                background-color: {self.theme['secondary']};
                color: {self.theme['text']};
                text-align: center;
                height: 24px;
            }}
            QProgressBar::chunk {{
                background-color: {self.theme['accent']};
                border-radius: 3px;
            }}
        """)
        
        self.usage_label.setStyleSheet(f"color: {self.theme['text']};")
        
        self.breakdown_title.setStyleSheet(
            f"font-size: 14px; font-weight: bold; margin-top: 16px; color: {self.theme['text']};"
        )
        
        # Update all category labels
        for i in range(self.breakdown_layout.count()):
            layout_item = self.breakdown_layout.itemAt(i)
            if isinstance(layout_item, QHBoxLayout):
                for j in range(layout_item.count()):
                    widget = layout_item.itemAt(j).widget()
                    if isinstance(widget, QLabel):
                        if j == 0:  # Name label
                            widget.setStyleSheet(f"color: {self.theme['text']};")
                        else:  # Size label
                            widget.setStyleSheet(f"color: {self.theme['text_secondary']}; text-align: right;")
