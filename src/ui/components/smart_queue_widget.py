
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QScrollArea, QGridLayout, QProgressBar, QSizePolicy, QMenu
)
from PySide6.QtCore import Qt, Signal, QSize, QMimeData, QRect
from PySide6.QtGui import QPixmap, QIcon, QColor, QPainter, QPalette, QImage, QCursor, QDrag

import pyqtgraph as pg
import time
from typing import Dict, List

from src.constants.constants import DOWNLOAD_STATUS
from src.models.download_task import DownloadTask
from src.utils.logger import get_logger
from src.utils.formatting import format_size, get_time_display

logger = get_logger(__name__)


class QueueItemCard(QFrame):
    """Card widget for a queue item"""

    cancel_requested = Signal(str)  # url
    move_requested = Signal(str, int)  # url, new_position
    
    def __init__(self, task: DownloadTask, position: int, theme: Dict, parent=None):
        super().__init__(parent)
        self.task = task
        self.position = position
        self.theme = theme
        self.drag_start_position = None
        
        # Set up frame styles
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {self.theme['card']};
                border-radius: 8px;
                border: 1px solid {self.theme['border']};
                padding: 8px;
            }}
            QFrame:hover {{
                background-color: {self.theme['card_hover']};
                border-color: {self.theme['border_hover']};
            }}
        """)
        
        self.setAcceptDrops(True)  # Enable drop events
        self.setMouseTracking(True)  # Track mouse for dragging
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI components"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        
        # Header row with title and cancel button
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)
        
        # Position indicator
        self.position_label = QLabel(f"#{self.position + 1}")
        self.position_label.setStyleSheet(f"""
            color: {self.theme['text_tertiary']};
            font-size: 12px;
            font-weight: bold;
            background-color: {self.theme['secondary']};
            padding: 2px 6px;
            border-radius: 8px;
        """)
        self.position_label.setFixedWidth(30)
        self.position_label.setAlignment(Qt.AlignCenter)
        
        # Title label
        model_info = self.task.model_info
        title = model_info.name if model_info else "Loading..."
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet(f"""
            color: {self.theme['text']};
            font-weight: bold;
        """)
        self.title_label.setWordWrap(True)
        self.title_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        
        # Status indicator
        self.status_indicator = QLabel(self.task.status)
        status_color = self.task.get_status_color(self.theme)
        self.status_indicator.setStyleSheet(f"""
            color: white;
            background-color: {status_color};
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 11px;
        """)
        
        # Cancel button
        self.cancel_btn = QPushButton("✕")
        self.cancel_btn.setFixedSize(24, 24)
        self.cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                color: {self.theme['text_secondary']};
                font-weight: bold;
                font-size: 14px;
            }}
            QPushButton:hover {{
                color: {self.theme['danger']};
            }}
        """)
        self.cancel_btn.clicked.connect(self.cancel_download)
        
        header_layout.addWidget(self.position_label)
        header_layout.addWidget(self.title_label)
        header_layout.addWidget(self.status_indicator)
        header_layout.addWidget(self.cancel_btn)
        
        # Progress bars
        progress_layout = QVBoxLayout()
        progress_layout.setSpacing(4)
        
        # Model progress bar
        model_progress_layout = QHBoxLayout()
        self.model_progress = QProgressBar()
        self.model_progress.setRange(0, 100)
        self.model_progress.setValue(self.task.model_progress)
        self.model_progress.setTextVisible(True)
        self.model_progress.setStyleSheet(f"""
            QProgressBar {{
                border: none;
                background-color: {self.theme['input_bg']};
                color: {self.theme['text']};
                text-align: center;
                border-radius: 3px;
            }}
            QProgressBar::chunk {{
                background-color: {self.theme['accent']};
                border-radius: 3px;
            }}
        """)
        model_progress_layout.addWidget(QLabel("Model:"))
        model_progress_layout.addWidget(self.model_progress)
        
        # Images progress bar
        image_progress_layout = QHBoxLayout()
        self.image_progress = QProgressBar()
        self.image_progress.setRange(0, 100)
        self.image_progress.setValue(self.task.image_progress)
        self.image_progress.setTextVisible(True)
        self.image_progress.setStyleSheet(f"""
            QProgressBar {{
                border: none;
                background-color: {self.theme['input_bg']};
                color: {self.theme['text']};
                text-align: center;
                border-radius: 3px;
            }}
            QProgressBar::chunk {{
                background-color: {self.theme['info']};
                border-radius: 3px;
            }}
        """)
        image_progress_layout.addWidget(QLabel("Images:"))
        image_progress_layout.addWidget(self.image_progress)
        
        progress_layout.addLayout(model_progress_layout)
        progress_layout.addLayout(image_progress_layout)
        
        layout.addLayout(header_layout)
        layout.addLayout(progress_layout)
        
        # Error message
        if self.task.error_message:
            self.error_label = QLabel(self.task.error_message)
            self.error_label.setWordWrap(True)
            self.error_label.setStyleSheet(f"color: {self.theme['danger']};")
            layout.addWidget(self.error_label)
    
    def update_task(self, task):
        """Update task data"""
        self.task = task
        
        # Update title if model info is available
        if task.model_info:
            self.title_label.setText(task.model_info.name)
        
        # Update progress bars
        self.model_progress.setValue(task.model_progress)
        self.image_progress.setValue(task.image_progress)
        
        # Update status indicator
        self.status_indicator.setText(task.status)
        status_color = task.get_status_color(self.theme)
        self.status_indicator.setStyleSheet(f"""
            color: white;
            background-color: {status_color};
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 11px;
        """)
        
        # Update error message
        if task.error_message:
            if hasattr(self, 'error_label'):
                self.error_label.setText(task.error_message)
            else:
                self.error_label = QLabel(task.error_message)
                self.error_label.setWordWrap(True)
                self.error_label.setStyleSheet(f"color: {self.theme['danger']};")
                self.layout().addWidget(self.error_label)
    
    def set_position(self, position):
        """Set position indicator"""
        self.position = position
        self.position_label.setText(f"#{position + 1}")
    
    def cancel_download(self):
        """Emit cancel signal"""
        self.cancel_requested.emit(self.task.url)
    
    def mousePressEvent(self, event):
        """Track mouse press for drag start"""
        if event.button() == Qt.LeftButton and self.task.status == DOWNLOAD_STATUS["QUEUED"]:
            self.drag_start_position = event.pos()
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """Handle mouse move for drag operations"""
        if not (event.buttons() & Qt.LeftButton and self.drag_start_position):
            return
            
        if self.task.status != DOWNLOAD_STATUS["QUEUED"]:
            return
        
        # Check if the movement is large enough to initiate drag
        distance = (event.pos() - self.drag_start_position).manhattanLength()
        if distance < QApplication.startDragDistance():
            return
        
        # Create drag object
        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setText(self.task.url)  # Store the URL for identification
        drag.setMimeData(mime_data)
        
        # Create a pixmap with card preview
        pixmap = QPixmap(self.size())
        self.render(pixmap)
        drag.setPixmap(pixmap.scaledToWidth(200, Qt.SmoothTransformation))
        drag.setHotSpot(event.pos())
        
        # Execute drag and handle result
        result = drag.exec_(Qt.MoveAction)
    
    def dragEnterEvent(self, event):
        """Handle drag enter event"""
        if event.mimeData().hasText() and self.task.status == DOWNLOAD_STATUS["QUEUED"]:
            event.acceptProposedAction()
    
    def dropEvent(self, event):
        """Handle drop event"""
        if event.mimeData().hasText() and self.task.status == DOWNLOAD_STATUS["QUEUED"]:
            source_url = event.mimeData().text()
            self.move_requested.emit(source_url, self.position)
            event.acceptProposedAction()
    
    def contextMenuEvent(self, event):
        """Show context menu on right click"""
        menu = QMenu(self)
        
        # Only show move options for queued tasks
        if self.task.status == DOWNLOAD_STATUS["QUEUED"]:
            # Add priority actions
            top = menu.addAction("Move to Top")
            up = menu.addAction("Move Up")
            down = menu.addAction("Move Down")
            bottom = menu.addAction("Move to Bottom")
            menu.addSeparator()
        
        # Add cancel action
        cancel = menu.addAction("Cancel")
        
        # Style the menu
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {self.theme['secondary']};
                color: {self.theme['text']};
                border: 1px solid {self.theme['border']};
                border-radius: 4px;
                padding: 4px;
            }}
            QMenu::item {{
                padding: 6px 24px;
                border-radius: 2px;
            }}
            QMenu::item:selected {{
                background-color: {self.theme['accent']};
                color: white;
            }}
            QMenu::separator {{
                height: 1px;
                background-color: {self.theme['border']};
                margin: 6px 0px;
            }}
        """)
        
        # Show menu and handle actions
        action = menu.exec_(event.globalPos())
        
        if not action:
            return
            
        if self.task.status == DOWNLOAD_STATUS["QUEUED"]:
            if action == top:
                self.move_requested.emit(self.task.url, 0)
            elif action == up and self.position > 0:
                self.move_requested.emit(self.task.url, self.position - 1)
            elif action == down:
                self.move_requested.emit(self.task.url, self.position + 1)
            elif action == bottom:
                self.move_requested.emit(self.task.url, 999)  # Large number for bottom
        
        if action == cancel:
            self.cancel_requested.emit(self.task.url)
    
    def set_theme(self, theme):
        """Update theme colors"""
        self.theme = theme
        
        # Update styles
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {self.theme['card']};
                border-radius: 8px;
                border: 1px solid {self.theme['border']};
                padding: 8px;
            }}
            QFrame:hover {{
                background-color: {self.theme['card_hover']};
                border-color: {self.theme['border_hover']};
            }}
        """)
        
        # Position indicator
        self.position_label.setStyleSheet(f"""
            color: {self.theme['text_tertiary']};
            font-size: 12px;
            font-weight: bold;
            background-color: {self.theme['secondary']};
            padding: 2px 6px;
            border-radius: 8px;
        """)
        
        # Title label
        self.title_label.setStyleSheet(f"""
            color: {self.theme['text']};
            font-weight: bold;
        """)
        
        # Status indicator
        status_color = self.task.get_status_color(self.theme)
        self.status_indicator.setStyleSheet(f"""
            color: white;
            background-color: {status_color};
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 11px;
        """)
        
        # Cancel button
        self.cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                color: {self.theme['text_secondary']};
                font-weight: bold;
                font-size: 14px;
            }}
            QPushButton:hover {{
                color: {self.theme['danger']};
            }}
        """)
        
        # Progress bars
        self.model_progress.setStyleSheet(f"""
            QProgressBar {{
                border: none;
                background-color: {self.theme['input_bg']};
                color: {self.theme['text']};
                text-align: center;
                border-radius: 3px;
            }}
            QProgressBar::chunk {{
                background-color: {self.theme['accent']};
                border-radius: 3px;
            }}
        """)
        
        self.image_progress.setStyleSheet(f"""
            QProgressBar {{
                border: none;
                background-color: {self.theme['input_bg']};
                color: {self.theme['text']};
                text-align: center;
                border-radius: 3px;
            }}
            QProgressBar::chunk {{
                background-color: {self.theme['info']};
                border-radius: 3px;
            }}
        """)
        
        # Error label
        if hasattr(self, 'error_label'):
            self.error_label.setStyleSheet(f"color: {self.theme['danger']};")
        
        # Update progress label colors
        for label in self.findChildren(QLabel):
            if label != self.title_label and label != self.position_label and label != self.status_indicator:
                if hasattr(self, 'error_label') and label == self.error_label:
                    continue
                label.setStyleSheet(f"color: {self.theme['text_secondary']};")


class SmartQueueWidget(QWidget):
    """Widget for displaying and managing the download queue"""
    
    cancel_requested = Signal(str)  # url
    clear_requested = Signal()  # No parameters
    move_requested = Signal(str, int)  # url, new_position
    
    def __init__(self, theme: Dict, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.task_widgets = {}  # url -> QueueItemCard
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI components"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        # Header with title and clear button
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel("Download Queue")
        title.setStyleSheet(f"""
            font-size: 16px;
            font-weight: bold;
            color: {self.theme['text']};
        """)
        
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.setStyleSheet(f"""
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
        self.clear_btn.clicked.connect(self.clear_queue)
        
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(self.clear_btn)
        
        # Queue items scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setStyleSheet(f"""
            QScrollArea {{
                background-color: transparent;
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
        
        # Container widget for queue items
        self.queue_container = QWidget()
        self.queue_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.queue_layout = QVBoxLayout(self.queue_container)
        self.queue_layout.setContentsMargins(10, 0, 10, 10)
        self.queue_layout.setSpacing(10)
        self.queue_layout.setAlignment(Qt.AlignTop)
        
        # Add empty state message
        self.empty_label = QLabel("Queue is empty")
        self.empty_label.setAlignment(Qt.AlignCenter)
        self.empty_label.setStyleSheet(f"""
            color: {self.theme['text_secondary']};
            font-style: italic;
            padding: 20px;
        """)
        self.queue_layout.addWidget(self.empty_label)
        
        scroll_area.setWidget(self.queue_container)
        
        # Bandwidth graph
        self.graph_container = QWidget()
        graph_layout = QVBoxLayout(self.graph_container)
        graph_layout.setContentsMargins(10, 0, 10, 10)
        
        graph_title = QLabel("Bandwidth Usage")
        graph_title.setStyleSheet(f"""
            font-size: 14px;
            font-weight: bold;
            color: {self.theme['text']};
            margin-bottom: 5px;
        """)
        
        self.bandwidth_graph = pg.PlotWidget()
        self.bandwidth_graph.setBackground(self.theme["card"])
        self.bandwidth_graph.setMinimumHeight(100)
        self.bandwidth_graph.setMaximumHeight(120)
        self.bandwidth_curve = self.bandwidth_graph.plot(
            [], [], pen=pg.mkPen(color=self.theme["accent"], width=2)
        )
        
        # Set axis labels
        self.bandwidth_graph.setLabel('left', 'MB/s')
        self.bandwidth_graph.setLabel('bottom', 'Time (s)')
        self.bandwidth_graph.getAxis('left').setTextPen(self.theme["text"])
        self.bandwidth_graph.getAxis('bottom').setTextPen(self.theme["text"])
        
        # Set grid
        self.bandwidth_graph.showGrid(x=True, y=True, alpha=0.3)
        
        graph_layout.addWidget(graph_title)
        graph_layout.addWidget(self.bandwidth_graph)
        
        # Add all components to main layout
        layout.addWidget(header)
        layout.addWidget(scroll_area, 1)  # Give scroll area all available space
        layout.addWidget(self.graph_container)
    
    def update_tasks(self, tasks: List[DownloadTask]):
        """Update all tasks in the queue"""
        # Sort tasks by priority
        queued_tasks = [t for t in tasks if t.status == DOWNLOAD_STATUS["QUEUED"]]
        queued_tasks.sort(key=lambda t: t.priority)
        
        active_task = next((t for t in tasks if t.status == DOWNLOAD_STATUS["DOWNLOADING"]), None)
        completed_tasks = [t for t in tasks if t.status in [DOWNLOAD_STATUS["COMPLETED"], DOWNLOAD_STATUS["FAILED"], DOWNLOAD_STATUS["CANCELED"]]]
        
        # Clear existing widgets
        self.clear_queue_widgets()
        
        # Show empty state if no tasks
        if not queued_tasks and not active_task and not completed_tasks:
            self.empty_label.show()
            return
        else:
            self.empty_label.hide()
        
        # Add active task first if any
        if active_task:
            self.add_task_widget(active_task, 0)
        
        # Add queued tasks
        for i, task in enumerate(queued_tasks):
            position = i + (1 if active_task else 0)
            self.add_task_widget(task, position)
            
        # Add completed tasks (limit to most recent 5)
        for task in completed_tasks[:5]:
            # Add at the bottom without specific position
            self.add_task_widget(task, -1)
    
    def add_task_widget(self, task: DownloadTask, position: int):
        """Add a task widget to the queue"""
        # Create widget if it doesn't exist
        if task.url not in self.task_widgets:
            card = QueueItemCard(task, position, self.theme)
            card.cancel_requested.connect(self.cancel_requested)
            card.move_requested.connect(self.move_requested)
            self.task_widgets[task.url] = card
        else:
            # Update existing widget
            card = self.task_widgets[task.url]
            card.update_task(task)
            if position >= 0:
                card.set_position(position)
        
        # Add to layout if not already added
        if card.parent() is None:
            self.queue_layout.addWidget(card)
    
    def update_task(self, task: DownloadTask):
        """Update a specific task"""
        if task.url in self.task_widgets:
            self.task_widgets[task.url].update_task(task)
        else:
            # Get all tasks and find position for this one
            self.add_task_widget(task, -1)
    
    def clear_queue_widgets(self):
        """Remove all queue widgets"""
        # Hide all widgets (we keep them for reuse)
        for widget in self.task_widgets.values():
            widget.setParent(None)
    
    def clear_queue(self):
        """Clear the queue"""
        self.clear_requested.emit()
    
    def update_bandwidth_graph(self, times, values):
        """Update bandwidth graph with new data"""
        if not times or not values:
            return
            
        # Convert bytes/sec to MB/sec
        mb_values = [v / (1024 * 1024) for v in values]
        
        # Update the graph
        self.bandwidth_curve.setData(times, mb_values)
        
        # Auto scale the graph
        max_value = max(mb_values) if mb_values else 1
        self.bandwidth_graph.setYRange(0, max_value * 1.1)
        
        # Set nice round X range
        self.bandwidth_graph.setXRange(min(times), max(times))
    
    def set_theme(self, theme):
        """Update theme colors"""
        self.theme = theme
        
        # Update title style
        title = self.findChild(QLabel, "", Qt.FindChildrenRecursively)
        if title and title.text() == "Download Queue":
            title.setStyleSheet(f"""
                font-size: 16px;
                font-weight: bold;
                color: {self.theme['text']};
            """)
        
        # Update clear button style
        self.clear_btn.setStyleSheet(f"""
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
        
        # Update empty label style
        self.empty_label.setStyleSheet(f"""
            color: {self.theme['text_secondary']};
            font-style: italic;
            padding: 20px;
        """)
        
        # Update bandwidth graph
        self.bandwidth_graph.setBackground(self.theme["card"])
        self.bandwidth_curve.setPen(pg.mkPen(color=self.theme["accent"], width=2))
        self.bandwidth_graph.getAxis('left').setTextPen(self.theme["text"])
        self.bandwidth_graph.getAxis('bottom').setTextPen(self.theme["text"])
        
        # Update graph title
        for label in self.graph_container.findChildren(QLabel):
            if label.text() == "Bandwidth Usage":
                label.setStyleSheet(f"""
                    font-size: 14px;
                    font-weight: bold;
                    color: {self.theme['text']};
                    margin-bottom: 5px;
                """)
        
        # Update all queue item cards
        for card in self.task_widgets.values():
            card.set_theme(theme)
        
        # Update scroll area style
        for scroll in self.findChildren(QScrollArea):
            scroll.setStyleSheet(f"""
                QScrollArea {{
                    background-color: transparent;
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
