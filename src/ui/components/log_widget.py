
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QTextEdit, QHBoxLayout, QLabel
)
from PySide6.QtCore import Qt, QTime
from PySide6.QtGui import QFont, QColor, QTextCursor

import time
from datetime import datetime
from typing import Dict

class LogWidget(QWidget):
    """Widget for displaying log messages"""
    
    def __init__(self, theme: Dict, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI components"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header with title and clear button
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel("Download Log")
        title.setStyleSheet(f"""
            font-size: 16px;
            font-weight: bold;
            color: {self.theme['text']};
        """)
        
        clear_btn = QPushButton("Clear")
        clear_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.theme['secondary']};
                color: {self.theme['text']};
                border: 1px solid {self.theme['border']};
                border-radius: 4px;
                padding: 4px 8px;
            }}
            QPushButton:hover {{
                background-color: {self.theme['card_hover']};
                border-color: {self.theme['accent']};
            }}
        """)
        clear_btn.clicked.connect(self.clear_log)
        
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(clear_btn)
        
        # Log text area
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet(f"""
            QTextEdit {{
                background-color: {self.theme['secondary']};
                color: {self.theme['text']};
                border: 1px solid {self.theme['border']};
                border-radius: 4px;
                padding: 8px;
                font-family: monospace;
            }}
        """)
        
        # Add components to layout
        layout.addWidget(header)
        layout.addWidget(self.log_text)
    
    def add_message(self, message: str, level: str = "info"):
        """Add a message to the log"""
        # Get color for message level
        color = self.get_level_color(level)
        
        # Get current time
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Format message
        formatted = f"[{timestamp}] {message}"
        
        # Append to log with color
        self.log_text.setTextColor(QColor(color))
        self.log_text.append(formatted)
        
        # Scroll to bottom
        self.log_text.moveCursor(QTextCursor.End)
    
    def get_level_color(self, level: str) -> str:
        """Get color for log level"""
        if level == "error":
            return self.theme["danger"]
        elif level == "warning":
            return self.theme["warning"]
        elif level == "success":
            return self.theme["success"]
        elif level == "download":
            return self.theme["accent"]
        else:
            return self.theme["text"]
    
    def clear_log(self):
        """Clear the log"""
        self.log_text.clear()
    
    def set_theme(self, theme):
        """Update theme"""
        self.theme = theme
        
        # Update log text style
        self.log_text.setStyleSheet(f"""
            QTextEdit {{
                background-color: {self.theme['secondary']};
                color: {self.theme['text']};
                border: 1px solid {self.theme['border']};
                border-radius: 4px;
                padding: 8px;
                font-family: monospace;
            }}
        """)
        
        # Update header
        for label in self.findChildren(QLabel):
            if label.text() == "Download Log":
                label.setStyleSheet(f"""
                    font-size: 16px;
                    font-weight: bold;
                    color: {self.theme['text']};
                """)
        
        # Update clear button
        for button in self.findChildren(QPushButton):
            if button.text() == "Clear":
                button.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {self.theme['secondary']};
                        color: {self.theme['text']};
                        border: 1px solid {self.theme['border']};
                        border-radius: 4px;
                        padding: 4px 8px;
                    }}
                    QPushButton:hover {{
                        background-color: {self.theme['card_hover']};
                        border-color: {self.theme['accent']};
                    }}
                """)
