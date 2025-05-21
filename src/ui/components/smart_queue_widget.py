
"""
Smart queue widget with drag and drop functionality
"""
from typing import Dict, List, Optional
import time

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QMenu, QFrame, QSplitter, QApplication
)
from PySide6.QtCore import Qt, Signal, QEvent, QMimeData, QPoint, QTimer
from PySide6.QtGui import QDrag, QMouseEvent

from src.constants.constants import DOWNLOAD_STATUS
from src.models.download_task import DownloadTask
from src.ui.components.download_task_card import DownloadTaskCard
from src.ui.components.bandwidth_graph import BandwidthGraph
from src.utils.formatting import format_duration

class SmartQueueWidget(QWidget):
    """Smart queue widget with bandwidth monitoring and ETA"""
    
    cancel_requested = Signal(str)  # url
    clear_requested = Signal()
    move_requested = Signal(str, int)  # url, new_position
    
    def __init__(self, theme: Dict, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.task_cards = {}  # url -> DownloadTaskCard
        self.drag_start_position = None
        self.total_size = 0
        self.completed_size = 0
        self.start_time = time.time()
        
        # Create update timer
        self.update_timer = QTimer(self)
        self.update_timer.setInterval(1000)  # 1 second
        self.update_timer.timeout.connect(self.update_eta)
        self.update_timer.start()
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI components"""
        main_layout = QVBoxLayout(self)
        
        # Create header
        header_layout = QHBoxLayout()
        
        title = QLabel("Download Queue")
        title.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {self.theme['text']};")
        
        self.queue_count = QLabel("0 items")
        self.queue_count.setStyleSheet(f"color: {self.theme['text_secondary']};")
        
        header_layout.addWidget(title)
        header_layout.addWidget(self.queue_count)
        header_layout.addStretch()
        
        # Clear queue button
        clear_btn = QPushButton("Clear Queue")
        clear_btn.setStyleSheet(f"""
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
        clear_btn.clicked.connect(self.clear_requested.emit)
        
        header_layout.addWidget(clear_btn)
        main_layout.addLayout(header_layout)
        
        # Create splitter for stats and tasks
        splitter = QSplitter(Qt.Vertical)
        splitter.setHandleWidth(1)
        splitter.setChildrenCollapsible(False)
        
        # Create stats panel
        stats_panel = QFrame()
        stats_panel.setFrameShape(QFrame.StyledPanel)
        stats_panel.setStyleSheet(f"""
            QFrame {{
                background-color: {self.theme['card']};
                border: 1px solid {self.theme['border']};
                border-radius: 8px;
                padding: 8px;
            }}
        """)
        
        stats_layout = QVBoxLayout(stats_panel)
        
        # ETA display
        eta_layout = QHBoxLayout()
        
        eta_label = QLabel("Estimated Time:")
        eta_label.setStyleSheet(f"color: {self.theme['text_secondary']};")
        
        self.eta_value = QLabel("Calculating...")
        self.eta_value.setStyleSheet(f"color: {self.theme['text']};")
        
        eta_layout.addWidget(eta_label)
        eta_layout.addWidget(self.eta_value)
        eta_layout.addStretch()
        
        stats_layout.addLayout(eta_layout)
        
        # Bandwidth graph
        self.bandwidth_graph = BandwidthGraph(self.theme)
        stats_layout.addWidget(self.bandwidth_graph)
        
        splitter.addWidget(stats_panel)
        
        # Create tasks panel
        tasks_panel = QScrollArea()
        tasks_panel.setWidgetResizable(True)
        tasks_panel.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background-color: transparent;
            }}
        """)
        
        self.tasks_widget = QWidget()
        self.tasks_layout = QVBoxLayout(self.tasks_widget)
        self.tasks_layout.setAlignment(Qt.AlignTop)
        self.tasks_layout.setContentsMargins(0, 0, 0, 0)
        self.tasks_layout.setSpacing(10)
        
        tasks_panel.setWidget(self.tasks_widget)
        splitter.addWidget(tasks_panel)
        
        # Set initial sizes
        splitter.setSizes([150, 350])
        
        main_layout.addWidget(splitter)
    
    def set_theme(self, theme):
        """Update the theme"""
        self.theme = theme
        
        # Update header
        for child in self.findChildren(QLabel):
            if "font-size: 16px" in child.styleSheet():
                child.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {self.theme['text']};")
            elif child == self.queue_count:
                child.setStyleSheet(f"color: {self.theme['text_secondary']};")
            elif child == self.eta_value:
                child.setStyleSheet(f"color: {self.theme['text']};")
            elif "Estimated Time" in child.text():
                child.setStyleSheet(f"color: {self.theme['text_secondary']};")
        
        # Update clear button
        for child in self.findChildren(QPushButton):
            if "Clear Queue" in child.text():
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
        
        # Update stats panel
        for frame in self.findChildren(QFrame):
            if frame != self and isinstance(frame, QFrame):
                frame.setStyleSheet(f"""
                    QFrame {{
                        background-color: {self.theme['card']};
                        border: 1px solid {self.theme['border']};
                        border-radius: 8px;
                        padding: 8px;
                    }}
                """)
        
        # Update bandwidth graph
        self.bandwidth_graph.set_theme(theme)
        
        # Update task cards
        for card in self.task_cards.values():
            card.set_theme(theme)
    
    def update_task(self, task: DownloadTask):
        """Update a task in the queue"""
        if task.url in self.task_cards:
            # Update existing card
            self.task_cards[task.url].update_task(task)
        else:
            # Create new card
            card = DownloadTaskCard(task, self.theme)
            card.cancel_requested.connect(self.cancel_requested.emit)
            card.setObjectName(f"card_{task.url}")
            card.installEventFilter(self)
            self.task_cards[task.url] = card
            
            # Insert in correct position based on priority
            position = task.priority
            if position >= self.tasks_layout.count():
                self.tasks_layout.addWidget(card)
            else:
                self.tasks_layout.insertWidget(position, card)
    
    def update_tasks(self, tasks: List[DownloadTask]):
        """Update all tasks"""
        # Update active task count
        active_count = sum(1 for task in tasks if task.status in [DOWNLOAD_STATUS["QUEUED"], DOWNLOAD_STATUS["DOWNLOADING"]])
        self.queue_count.setText(f"{active_count} items")
        
        # Update task cards
        task_urls = set()
        for task in tasks:
            self.update_task(task)
            task_urls.add(task.url)
        
        # Remove cards for tasks that no longer exist
        for url in list(self.task_cards.keys()):
            if url not in task_urls:
                self.task_cards[url].deleteLater()
                del self.task_cards[url]
        
        # Update ETA
        self.update_eta()
    
    def update_eta(self):
        """Update estimated time to completion"""
        # Count active downloads
        active_tasks = []
        completed_size = 0
        total_size = 0
        
        for url, card in self.task_cards.items():
            task = card.task
            if task.status == DOWNLOAD_STATUS["DOWNLOADING"]:
                active_tasks.append(task)
            elif task.status == DOWNLOAD_STATUS["COMPLETED"]:
                completed_size += task.model_progress  # Use progress as size estimate
            
            # Count all tasks for total size
            total_size += 100  # Each task is 100% when complete
        
        self.completed_size = completed_size
        self.total_size = total_size
        
        # Calculate ETA based on progress
        if not active_tasks or total_size == 0:
            self.eta_value.setText("N/A")
            return
        
        # Calculate elapsed time and progress
        elapsed = time.time() - self.start_time
        progress = completed_size / total_size if total_size > 0 else 0
        
        if progress <= 0:
            self.eta_value.setText("Calculating...")
            return
        
        # Estimate remaining time
        remaining = elapsed * (1 - progress) / progress
        
        # Format and display ETA
        eta_text = format_duration(remaining)
        self.eta_value.setText(eta_text)
    
    def update_bandwidth_graph(self, times, values):
        """Update bandwidth graph with new data"""
        self.bandwidth_graph.update_data(times, values)
    
    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press events for drag and drop"""
        if event.button() == Qt.LeftButton:
            self.drag_start_position = event.position()
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """Handle mouse move events for drag and drop"""
        if not (event.buttons() & Qt.LeftButton) or not self.drag_start_position:
            return
            
        # Calculate distance moved
        distance = (event.position() - self.drag_start_position).manhattanLength()
        if distance < QApplication.startDragDistance():
            return
        
        # Find the task card under the mouse
        widget = self.childAt(int(self.drag_start_position.x()), int(self.drag_start_position.y()))
        while widget and not isinstance(widget, DownloadTaskCard):
            if widget.parent() == self:
                widget = None
                break
            widget = widget.parent()
        
        if not widget:
            return
            
        # Get the task URL
        task_url = widget.task.url
        
        # Create drag
        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setText(task_url)
        drag.setMimeData(mime_data)
        
        # Execute drag
        result = drag.exec(Qt.MoveAction)
    
    def dragEnterEvent(self, event):
        """Handle drag enter events"""
        if event.mimeData().hasText():
            event.acceptProposedAction()
    
    def dragMoveEvent(self, event):
        """Handle drag move events"""
        if event.mimeData().hasText():
            event.acceptProposedAction()
    
    def dropEvent(self, event):
        """Handle drop events to reorder tasks"""
        if event.mimeData().hasText():
            url = event.mimeData().text()
            
            # Find the card under the drop position
            pos = event.position()
            drop_y = int(pos.y())
            
            # Find the closest task card
            target_idx = -1
            for i in range(self.tasks_layout.count()):
                item = self.tasks_layout.itemAt(i)
                if item and item.widget():
                    card = item.widget()
                    card_rect = card.geometry()
                    
                    # Check if drop is in the card's area
                    if card_rect.top() <= drop_y <= card_rect.bottom():
                        target_idx = i
                        break
                    
                    # If drop is before this card
                    if drop_y < card_rect.top():
                        target_idx = i
                        break
            
            # If drop is after the last card
            if target_idx == -1 and self.tasks_layout.count() > 0:
                target_idx = self.tasks_layout.count()
            
            # Emit signal with the new position
            if target_idx != -1:
                self.move_requested.emit(url, target_idx)
            
            event.acceptProposedAction()
    
    def eventFilter(self, watched, event):
        """Event filter for context menu on task cards"""
        if event.type() == QEvent.ContextMenu and isinstance(watched, DownloadTaskCard):
            menu = QMenu(self)
            
            # Get task URL
            task_url = watched.task.url
            task = watched.task
            
            # Only show menu for queued or downloading tasks
            if task.status in [DOWNLOAD_STATUS["QUEUED"], DOWNLOAD_STATUS["DOWNLOADING"]]:
                # Add context menu actions
                cancel_action = menu.addAction("Cancel")
                cancel_action.triggered.connect(lambda: self.cancel_requested.emit(task_url))
                
                menu.addSeparator()
                
                move_top = menu.addAction("Move to Top")
                move_top.triggered.connect(lambda: self.move_requested.emit(task_url, 0))
                
                # If this isn't the first task
                current_index = -1
                for i in range(self.tasks_layout.count()):
                    if self.tasks_layout.itemAt(i).widget() == watched:
                        current_index = i
                        break
                
                if current_index > 0:
                    move_up = menu.addAction("Move Up")
                    move_up.triggered.connect(lambda: self.move_requested.emit(task_url, current_index - 1))
                    
                if current_index < self.tasks_layout.count() - 1 and current_index != -1:
                    move_down = menu.addAction("Move Down")
                    move_down.triggered.connect(lambda: self.move_requested.emit(task_url, current_index + 1))
                
                # Show the menu
                menu.exec(event.globalPos())
                return True
            
        return super().eventFilter(watched, event)
    
    def reset_timer(self):
        """Reset the timer for ETA calculation"""
        self.start_time = time.time()
        self.completed_size = 0
        self.total_size = 0
