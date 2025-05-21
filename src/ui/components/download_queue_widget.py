
from typing import Dict, List, Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QMenu, QAbstractItemView, QApplication
)
from PySide6.QtCore import Qt, Signal, QEvent, QMimeData, QPoint
from PySide6.QtGui import QDrag, QMouseEvent

from src.models.download_task import DownloadTask
from src.ui.components.download_task_card import DownloadTaskCard

class DownloadQueueWidget(QWidget):
    """Widget for displaying the download queue"""
    
    cancel_requested = Signal(str)  # url
    clear_requested = Signal()
    move_to_top_requested = Signal(str)  # url
    move_up_requested = Signal(str)  # url
    move_down_requested = Signal(str)  # url
    
    def __init__(self, theme: Dict, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.task_cards = {}  # url -> DownloadTaskCard
        self.drag_start_position = None
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI components"""
        layout = QVBoxLayout(self)
        
        # Title
        title_layout = QHBoxLayout()
        title = QLabel("Download Queue")
        title.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {self.theme['text']};")
        
        self.queue_count = QLabel("0 items")
        self.queue_count.setStyleSheet(f"color: {self.theme['text_secondary']};")
        
        title_layout.addWidget(title)
        title_layout.addWidget(self.queue_count)
        title_layout.addStretch()
        
        # Clear button
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
        
        title_layout.addWidget(clear_btn)
        
        layout.addLayout(title_layout)
        
        # Scroll area for task cards
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background-color: transparent; border: none;")
        
        self.tasks_widget = QWidget()
        self.tasks_layout = QVBoxLayout(self.tasks_widget)
        self.tasks_layout.setAlignment(Qt.AlignTop)
        self.tasks_layout.setContentsMargins(0, 0, 0, 0)
        self.tasks_layout.setSpacing(10)
        
        scroll.setWidget(self.tasks_widget)
        
        layout.addWidget(scroll)
    
    def set_theme(self, theme):
        """Update the theme"""
        self.theme = theme
        
        # Update title and count
        for child in self.findChildren(QLabel):
            if "font-size: 16px" in child.styleSheet():
                child.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {self.theme['text']};")
            else:
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
        
        # Update task cards
        for card in self.task_cards.values():
            card.set_theme(self.theme)
    
    def update_task(self, task: DownloadTask):
        """Update a task in the queue"""
        if task.url in self.task_cards:
            # Update existing card
            self.task_cards[task.url].update_task(task)
        else:
            # Create new card
            card = DownloadTaskCard(task, self.theme)
            card.cancel_requested.connect(self.cancel_requested.emit)
            card.move_to_top_requested.connect(self.move_to_top_requested.emit)
            card.move_up_requested.connect(self.move_up_requested.emit)
            card.move_down_requested.connect(self.move_down_requested.emit)
            card.setObjectName(f"card_{task.url}")
            card.installEventFilter(self)
            self.task_cards[task.url] = card
            self.tasks_layout.addWidget(card)
    
    def update_tasks(self, tasks: List[DownloadTask]):
        """Update all tasks"""
        # Update active task count
        active_count = sum(1 for task in tasks if task.status in ["queued", "downloading"])
        self.queue_count.setText(f"{active_count} items")
        
        # Update existing cards and add new ones
        for task in tasks:
            self.update_task(task)
        
        # Remove cards for tasks that no longer exist
        task_urls = {task.url for task in tasks}
        for url in list(self.task_cards.keys()):
            if url not in task_urls:
                self.task_cards[url].deleteLater()
                del self.task_cards[url]
    
    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press events for drag and drop"""
        if event.button() == Qt.LeftButton:
            self.drag_start_position = event.pos()
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """Handle mouse move events for drag and drop"""
        if not (event.buttons() & Qt.LeftButton) or not self.drag_start_position:
            return
            
        # Check if the mouse has moved far enough to be a drag
        if (event.pos() - self.drag_start_position).manhattanLength() < QApplication.startDragDistance():
            return
        
        # Find the card under the mouse
        child = self.childAt(self.drag_start_position)
        while child and not isinstance(child, DownloadTaskCard):
            child = child.parentWidget()
        
        if not child:
            return
            
        # Get the task URL
        task_url = child.task.url
        
        # Create drag
        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setText(task_url)
        drag.setMimeData(mime_data)
        
        # Execute drag
        drag.exec_(Qt.MoveAction)
    
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
            target_pos = event.pos()
            target_card = None
            
            for card in self.task_cards.values():
                card_rect = card.geometry()
                if card_rect.contains(target_pos):
                    target_card = card
                    break
            
            if target_card and target_card.task.url != url:
                # Emit move signals based on drop position
                self.move_to_position_requested.emit(url, target_card.task.url)
                
            event.acceptProposedAction()
    
    def eventFilter(self, watched, event):
        """Event filter for context menu on task cards"""
        if event.type() == QEvent.ContextMenu and isinstance(watched, DownloadTaskCard):
            menu = QMenu(self)
            
            # Get task URL
            task_url = watched.task.url
            
            # Add context menu actions
            cancel_action = menu.addAction("Cancel")
            cancel_action.triggered.connect(lambda: self.cancel_requested.emit(task_url))
            
            menu.addSeparator()
            
            top_action = menu.addAction("Move to Top")
            top_action.triggered.connect(lambda: self.move_to_top_requested.emit(task_url))
            
            up_action = menu.addAction("Move Up")
            up_action.triggered.connect(lambda: self.move_up_requested.emit(task_url))
            
            down_action = menu.addAction("Move Down")
            down_action.triggered.connect(lambda: self.move_down_requested.emit(task_url))
            
            # Show the menu
            menu.exec_(event.globalPos())
            return True
            
        return super().eventFilter(watched, event)
