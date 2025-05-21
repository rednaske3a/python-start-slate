
"""
Toast notification manager for displaying non-intrusive messages
"""
from typing import Dict, List, Optional

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QPushButton
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QRect, QObject
from PySide6.QtGui import QColor, QPalette, QPainter, QPainterPath, QBrush, QPen

class Toast(QWidget):
    """Individual toast notification widget"""
    
    def __init__(self, message: str, theme: Dict, toast_type: str = "info", 
                 parent=None, duration: int = 5000, action=None, action_text=None):
        """
        Initialize the toast widget
        
        Args:
            message: Message text to display
            theme: Theme colors dictionary
            toast_type: Type of toast (info, success, error)
            parent: Parent widget
            duration: Display duration in milliseconds
            action: Action callback function
            action_text: Action button text
        """
        super().__init__(parent)
        self.message = message
        self.theme = theme
        self.toast_type = toast_type
        self.duration = duration
        self.action = action
        self.action_text = action_text
        self.init_ui()
        
        # Set up auto-hide timer
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.hide_toast)
        
        # Animation
        self.show_animation = QPropertyAnimation(self, b"geometry")
        self.show_animation.setDuration(300)
        self.show_animation.setEasingCurve(QEasingCurve.OutCubic)
        
        self.hide_animation = QPropertyAnimation(self, b"geometry")
        self.hide_animation.setDuration(300)
        self.hide_animation.setEasingCurve(QEasingCurve.InCubic)
        self.hide_animation.finished.connect(self.deleteLater)
    
    def init_ui(self):
        """Initialize UI components"""
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        
        # Set minimum/maximum size
        self.setMinimumWidth(300)
        self.setMaximumWidth(400)
        
        # Create layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Toast message
        message_label = QLabel(self.message)
        message_label.setWordWrap(True)
        message_label.setStyleSheet(f"color: {self.theme['text']}; font-size: 13px;")
        
        layout.addWidget(message_label)
        layout.addStretch()
        
        # Add action button if provided
        if self.action and self.action_text:
            action_btn = QPushButton(self.action_text)
            action_btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    color: {self.theme['accent']};
                    border: none;
                    font-weight: bold;
                    padding: 5px;
                }}
                QPushButton:hover {{
                    text-decoration: underline;
                }}
            """)
            action_btn.clicked.connect(self.action)
            action_btn.clicked.connect(self.hide_toast)
            layout.addWidget(action_btn)
        
        # Add close button
        close_btn = QPushButton("×")
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {self.theme['text_secondary']};
                border: none;
                font-size: 16px;
                font-weight: bold;
                padding: 2px 5px;
            }}
            QPushButton:hover {{
                color: {self.theme['text']};
            }}
        """)
        close_btn.clicked.connect(self.hide_toast)
        
        layout.addWidget(close_btn)
    
    def show_toast(self):
        """Show toast with animation"""
        parent = self.parent()
        if not parent:
            return
        
        # Position at the top-right corner
        parent_rect = parent.geometry()
        self.adjustSize()
        
        # Animation values for sliding in from right
        start_x = parent_rect.width()
        end_x = parent_rect.width() - self.width() - 20
        
        # Set geometry for animation
        self.setGeometry(start_x, 20, self.width(), self.height())
        
        # Show the widget before animation starts
        self.show()
        
        # Configure and start the animation
        self.show_animation.setStartValue(QRect(start_x, 20, self.width(), self.height()))
        self.show_animation.setEndValue(QRect(end_x, 20, self.width(), self.height()))
        self.show_animation.start()
        
        # Start the auto-hide timer
        self.timer.start(self.duration)
    
    def hide_toast(self):
        """Hide toast with animation"""
        self.timer.stop()
        
        parent_rect = self.parentWidget().geometry()
        end_x = parent_rect.width()
        
        # Configure and start the animation
        self.hide_animation.setStartValue(self.geometry())
        self.hide_animation.setEndValue(QRect(end_x, self.y(), self.width(), self.height()))
        self.hide_animation.start()
    
    def enterEvent(self, event):
        """Pause timer when mouse enters"""
        self.timer.stop()
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """Resume timer when mouse leaves"""
        self.timer.start(self.duration)
        super().leaveEvent(event)
    
    def paintEvent(self, event):
        """Custom paint event for rounded corners and shadow"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Create rounded rectangle path
        path = QPainterPath()
        rect = self.rect()
        path.addRoundedRect(rect, 10, 10)
        
        # Set background color based on toast type
        if self.toast_type == "success":
            bg_color = QColor(self.theme["success"])
            bg_color.setAlpha(40)  # Semi-transparent
        elif self.toast_type == "error":
            bg_color = QColor(self.theme["danger"])
            bg_color.setAlpha(40)  # Semi-transparent
        else:  # info or default
            bg_color = QColor(self.theme["secondary"])
            
        # Draw rounded background
        painter.fillPath(path, bg_color)
        
        # Draw border
        border_color = QColor(self.theme["border"])
        painter.setPen(QPen(border_color, 1))
        painter.drawPath(path)


class ToastManager(QObject):
    """Manager for creating and displaying toast notifications"""
    
    def __init__(self, parent_widget, theme):
        """
        Initialize toast manager
        
        Args:
            parent_widget: Widget to display toasts on
            theme: Theme colors dictionary
        """
        super().__init__(parent_widget)
        self.parent_widget = parent_widget
        self.theme = theme
        self.active_toasts = []
        
    def show_toast(self, message, toast_type="info", duration=5000, action=None, action_text=None):
        """
        Show a toast notification
        
        Args:
            message: Message text to display
            toast_type: Type of toast (info, success, error)
            duration: Display duration in milliseconds
            action: Action callback function
            action_text: Action button text
        """
        # Create new toast
        toast = Toast(
            message=message,
            theme=self.theme,
            toast_type=toast_type,
            parent=self.parent_widget,
            duration=duration,
            action=action,
            action_text=action_text
        )
        
        # Show the toast
        toast.show_toast()
        
        # Add to active toasts
        self.active_toasts.append(toast)
        
        # Clean up when toast is destroyed
        toast.destroyed.connect(lambda: self._remove_toast(toast))
        
    def _remove_toast(self, toast):
        """Remove toast from active list"""
        if toast in self.active_toasts:
            self.active_toasts.remove(toast)
    
    def clear_all(self):
        """Clear all active toasts"""
        for toast in self.active_toasts[:]:  # Work on a copy of the list
            toast.hide_toast()
    
    def set_theme(self, theme):
        """Update theme for the toast manager"""
        self.theme = theme
