from typing import Dict

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QProgressBar
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QPixmap, QColor
from PySide6.QtWidgets import QGraphicsDropShadowEffect


from src.constants.constants import DOWNLOAD_STATUS
from src.models.download_task import DownloadTask

class DownloadTaskCard(QWidget):
    """Widget for displaying a download task in the queue"""
    
    cancel_requested = Signal(str)  # url
    
    def __init__(self, task: DownloadTask, theme: Dict, parent=None):
        super().__init__(parent)
        self.task = task
        self.theme = theme
        self.init_ui()
        
    def init_ui(self):
        """Initialize UI components"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Card frame
        self.setObjectName("downloadTaskCard")
        self.apply_theme()
        
        # Add shadow effect
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(self.theme["shadow"]))
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)
        
        # URL and status
        url_layout = QHBoxLayout()
        
        # URL label (truncated)
        url_text = self.task.url
        if len(url_text) > 40:
            url_text = url_text[:37] + "..."
        url_label = QLabel(url_text)
        url_label.setToolTip(self.task.url)
        url_label.setStyleSheet(f"font-weight: bold; color: {self.theme['text']};")
        
        # Status label
        self.status_label = QLabel(self.task.status.capitalize())
        self.status_label.setStyleSheet(f"color: {self.task.get_status_color(self.theme)};")
        
        url_layout.addWidget(url_label)
        url_layout.addStretch()
        url_layout.addWidget(self.status_label)
        
        layout.addLayout(url_layout)
        
        # Progress bars
        progress_layout = QVBoxLayout()
        
        # Model progress
        model_layout = QHBoxLayout()
        model_label = QLabel("Model:")
        model_label.setStyleSheet(f"color: {self.theme['text_secondary']};")
        model_label.setFixedWidth(50)
        
        self.model_progress = QProgressBar()
        self.model_progress.setRange(0, 100)
        self.model_progress.setValue(self.task.model_progress)
        self.model_progress.setTextVisible(True)
        self.model_progress.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid {self.theme['border']};
                border-radius: 4px;
                text-align: center;
                height: 16px;
                color: {self.theme['text']};
                background-color: {self.theme['input_bg']};
            }}
            QProgressBar::chunk {{
                background-color: {self.theme['accent']};
                border-radius: 3px;
            }}
        """)
        
        model_layout.addWidget(model_label)
        model_layout.addWidget(self.model_progress)
        
        # Image progress
        image_layout = QHBoxLayout()
        image_label = QLabel("Images:")
        image_label.setStyleSheet(f"color: {self.theme['text_secondary']};")
        image_label.setFixedWidth(50)
        
        self.image_progress = QProgressBar()
        self.image_progress.setRange(0, 100)
        self.image_progress.setValue(self.task.image_progress)
        self.image_progress.setTextVisible(True)
        self.image_progress.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid {self.theme['border']};
                border-radius: 4px;
                text-align: center;
                height: 16px;
                color: {self.theme['text']};
                background-color: {self.theme['input_bg']};
            }}
            QProgressBar::chunk {{
                background-color: {self.theme['success']};
                border-radius: 3px;
            }}
        """)
        
        image_layout.addWidget(image_label)
        image_layout.addWidget(self.image_progress)
        
        progress_layout.addLayout(model_layout)
        progress_layout.addLayout(image_layout)
        
        layout.addLayout(progress_layout)
        
        # Info section (model name, time, etc.)
        self.info_label = QLabel()
        self.info_label.setStyleSheet(f"color: {self.theme['text_secondary']}; font-size: 12px;")
        self.update_info_label()
        
        layout.addWidget(self.info_label)
        
        # Cancel button (only for queued or downloading tasks)
        if self.task.status in [DOWNLOAD_STATUS["QUEUED"], DOWNLOAD_STATUS["DOWNLOADING"]]:
            self.cancel_btn = QPushButton("Cancel")
            self.cancel_btn.setStyleSheet(f"""
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
            self.cancel_btn.clicked.connect(self.request_cancel)
            layout.addWidget(self.cancel_btn)
        
        self.setFixedHeight(150)
        self.setMinimumWidth(300)
        
    def apply_theme(self):
        """Apply the current theme to the widget"""
        self.setStyleSheet(f"""
            #downloadTaskCard {{
                background-color: {self.theme["card"]};
                border-radius: 8px;
                border: 1px solid {self.theme["border"]};
            }}
            #downloadTaskCard:hover {{
                border: 1px solid {self.theme["border_hover"]};
                background-color: {self.theme["card_hover"]};
            }}
        """)
    
    def set_theme(self, theme):
        """Update the theme"""
        self.theme = theme
        self.apply_theme()
        
        # Update status label
        self.status_label.setStyleSheet(f"color: {self.task.get_status_color(self.theme)};")
        
        # Update progress bars
        self.model_progress.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid {self.theme['border']};
                border-radius: 4px;
                text-align: center;
                height: 16px;
                color: {self.theme['text']};
                background-color: {self.theme['input_bg']};
            }}
            QProgressBar::chunk {{
                background-color: {self.theme['accent']};
                border-radius: 3px;
            }}
        """)
        
        self.image_progress.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid {self.theme['border']};
                border-radius: 4px;
                text-align: center;
                height: 16px;
                color: {self.theme['text']};
                background-color: {self.theme['input_bg']};
            }}
            QProgressBar::chunk {{
                background-color: {self.theme['success']};
                border-radius: 3px;
            }}
        """)
        
        # Update info label
        self.info_label.setStyleSheet(f"color: {self.theme['text_secondary']}; font-size: 12px;")
        
        # Update cancel button if it exists
        if hasattr(self, 'cancel_btn'):
            self.cancel_btn.setStyleSheet(f"""
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
    
    def update_task(self, task: DownloadTask):
        """Update the task and refresh the UI"""
        self.task = task
        self.status_label.setText(self.task.status.capitalize())
        self.status_label.setStyleSheet(f"color: {self.task.get_status_color(self.theme)};")
        
        self.model_progress.setValue(self.task.model_progress)
        self.image_progress.setValue(self.task.image_progress)
        
        self.update_info_label()
        
        # Update cancel button visibility
        if hasattr(self, 'cancel_btn'):
            if self.task.status not in [DOWNLOAD_STATUS["QUEUED"], DOWNLOAD_STATUS["DOWNLOADING"]]:
                self.cancel_btn.setVisible(False)
    
    def update_info_label(self):
        """Update the info label with task details"""
        info_text = ""
        
        # Add model name if available
        if self.task.model_info:
            info_text += f"Model: {self.task.model_info.name}\n"
        
        # Add duration
        duration = self.task.get_duration()
        if duration > 0:
            if duration < 60:
                duration_text = f"{duration:.1f} seconds"
            else:
                minutes = int(duration / 60)
                seconds = int(duration % 60)
                duration_text = f"{minutes}m {seconds}s"
            
            if self.task.status in [DOWNLOAD_STATUS["COMPLETED"], DOWNLOAD_STATUS["FAILED"], DOWNLOAD_STATUS["CANCELED"]]:
                info_text += f"Total time: {duration_text}"
            else:
                info_text += f"Elapsed: {duration_text}"
        
        # Add error message if failed
        if self.task.status == DOWNLOAD_STATUS["FAILED"] and self.task.error_message:
            info_text += f"\nError: {self.task.error_message}"
        
        self.info_label.setText(info_text)
    
    def request_cancel(self):
        """Request to cancel the download"""
        self.cancel_requested.emit(self.task.url)