
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QScrollArea, QFrame
)
from PySide6.QtCore import Qt, QDateTime
from PySide6.QtGui import QColor, QTextCharFormat, QBrush, QTextCursor

class LogWidget(QWidget):
    """Widget for displaying log messages"""
    
    def __init__(self, theme, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI components"""
        layout = QVBoxLayout(self)
        
        # Title and buttons
        header = QHBoxLayout()
        
        title = QLabel("Download Log")
        title.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {self.theme['text']};")
        
        clear_button = QPushButton("Clear Log")
        clear_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.theme['danger']};
                color: white;
                border: none;
                border-radius: 4px;
                padding: 4px 8px;
            }}
            QPushButton:hover {{
                background-color: {self.theme['danger_hover']};
            }}
        """)
        clear_button.clicked.connect(self.clear_log)
        
        header.addWidget(title)
        header.addStretch()
        header.addWidget(clear_button)
        
        layout.addLayout(header)
        
        # Log text area
        self.log_edit = QTextEdit()
        self.log_edit.setReadOnly(True)
        self.log_edit.setStyleSheet(f"""
            QTextEdit {{
                background-color: {self.theme['background']};
                color: {self.theme['text']};
                border: 1px solid {self.theme['border']};
                border-radius: 4px;
                padding: 5px;
                font-family: monospace;
            }}
        """)
        
        layout.addWidget(self.log_edit)
        
        # Set text colors
        self.log_formats = {
            "info": self._create_format(self.theme["text"]),
            "success": self._create_format(self.theme["success"]),
            "error": self._create_format(self.theme["danger"]),
            "warning": self._create_format(self.theme["warning"]),
            "download": self._create_format(self.theme["info"])
        }
    
    def _create_format(self, color):
        """Create a text format with the specified color"""
        fmt = QTextCharFormat()
        fmt.setForeground(QBrush(QColor(color)))
        return fmt
    
    def add_message(self, message, level="info"):
        """Add a message to the log"""
        # Get timestamp
        timestamp = QDateTime.currentDateTime().toString("HH:mm:ss")
        
        # Get format for level
        fmt = self.log_formats.get(level.lower(), self.log_formats["info"])
        
        # Format message
        formatted_message = f"[{timestamp}] {message}"
        
        # Add to log
        cursor = self.log_edit.textCursor()
        cursor.movePosition(QTextCursor.End)
        
        # Set the format and insert text
        cursor.setCharFormat(fmt)
        cursor.insertText(formatted_message + "\n")
        
        # Scroll to bottom
        self.log_edit.setTextCursor(cursor)
        self.log_edit.ensureCursorVisible()
    
    def clear_log(self):
        """Clear the log"""
        self.log_edit.clear()
    
    def set_theme(self, theme):
        """Update the theme"""
        self.theme = theme
        
        # Update colors
        self.log_formats = {
            "info": self._create_format(self.theme["text"]),
            "success": self._create_format(self.theme["success"]),
            "error": self._create_format(self.theme["danger"]),
            "warning": self._create_format(self.theme["warning"]),
            "download": self._create_format(self.theme["info"])
        }
        
        # Update title
        for child in self.findChildren(QLabel):
            if "font-size: 16px" in child.styleSheet():
                child.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {self.theme['text']};")
        
        # Update clear button
        for child in self.findChildren(QPushButton):
            if "Clear Log" in child.text():
                child.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {self.theme['danger']};
                        color: white;
                        border: none;
                        border-radius: 4px;
                        padding: 4px 8px;
                    }}
                    QPushButton:hover {{
                        background-color: {self.theme['danger_hover']};
                    }}
                """)
        
        # Update log edit
        self.log_edit.setStyleSheet(f"""
            QTextEdit {{
                background-color: {self.theme['background']};
                color: {self.theme['text']};
                border: 1px solid {self.theme['border']};
                border-radius: 4px;
                padding: 5px;
                font-family: monospace;
            }}
        """)
