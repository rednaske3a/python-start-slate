
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGraphicsOpacityEffect
)
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QRect
from PySide6.QtGui import QColor

from typing import Dict, Optional, Callable

class ToastNotification(QWidget):
    """A single toast notification widget"""
    
    def __init__(self, message: str, type_: str, theme: Dict, 
                duration: int = 3000, parent=None, 
                action: Optional[Callable] = None,
                action_text: Optional[str] = None):
        super().__init__(parent)
        self.theme = theme
        self.message = message
        self.type = type_
        self.duration = duration
        self.action_callback = action
        self.action_text = action_text or "Action"
        
        # Set up widget properties
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setMinimumWidth(300)
        self.setMaximumWidth(400)
        
        # Set background color based on type
        self.background_color = self.get_background_color()
        
        # Create opacity effect
        self.opacity_effect = QGraphicsOpacityEffect()
        self.opacity_effect.setOpacity(0.0)
        self.setGraphicsEffect(self.opacity_effect)
        
        self.init_ui()
        self.setup_animations()
    
    def init_ui(self):
        """Initialize UI components"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Message
        message_layout = QHBoxLayout()
        message_layout.setSpacing(10)
        
        # Icon
        if self.type == "success":
            icon = "✓"
        elif self.type == "error":
            icon = "✕"
        elif self.type == "warning":
            icon = "!"
        else:
            icon = "i"
        
        icon_label = QLabel(icon)
        icon_label.setStyleSheet(f"""
            color: white;
            font-size: 14px;
            font-weight: bold;
        """)
        
        # Message text
        message_label = QLabel(self.message)
        message_label.setWordWrap(True)
        message_label.setStyleSheet("color: white;")
        
        message_layout.addWidget(icon_label, 0)
        message_layout.addWidget(message_label, 1)
        
        # Close button
        close_button = QPushButton("×")
        close_button.setFixedSize(20, 20)
        close_button.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: white;
                border: none;
                font-size: 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                color: rgba(255, 255, 255, 0.8);
            }}
        """)
        close_button.clicked.connect(self.close_animation)
        
        message_layout.addWidget(close_button, 0)
        
        # Add message layout
        layout.addLayout(message_layout)
        
        # Add action button if provided
        if self.action_callback:
            action_layout = QHBoxLayout()
            action_layout.setContentsMargins(0, 10, 0, 0)
            
            action_button = QPushButton(self.action_text)
            action_button.setStyleSheet(f"""
                QPushButton {{
                    background-color: rgba(255, 255, 255, 0.2);
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 5px 10px;
                }}
                QPushButton:hover {{
                    background-color: rgba(255, 255, 255, 0.3);
                }}
            """)
            action_button.clicked.connect(self.execute_action)
            
            action_layout.addStretch()
            action_layout.addWidget(action_button)
            
            layout.addLayout(action_layout)
        
        # Set widget style
        self.setStyleSheet(f"""
            ToastNotification {{
                background-color: {self.background_color};
                border-radius: 6px;
            }}
        """)
    
    def get_background_color(self) -> str:
        """Get background color based on notification type"""
        if self.type == "success":
            return self.theme["success"]
        elif self.type == "error":
            return self.theme["danger"]
        elif self.type == "warning":
            return self.theme["warning"]
        else:
            return self.theme["info"]
    
    def setup_animations(self):
        """Set up fade animations"""
        # Fade in animation
        self.fade_in = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_in.setDuration(300)
        self.fade_in.setStartValue(0.0)
        self.fade_in.setEndValue(1.0)
        self.fade_in.setEasingCurve(QEasingCurve.OutCubic)
        
        # Fade out animation
        self.fade_out = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_out.setDuration(300)
        self.fade_out.setStartValue(1.0)
        self.fade_out.setEndValue(0.0)
        self.fade_out.setEasingCurve(QEasingCurve.OutCubic)
        self.fade_out.finished.connect(self.close)
        
        # Auto close timer
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.setInterval(self.duration)
        self.timer.timeout.connect(self.close_animation)
    
    def show_animation(self):
        """Show the notification with animation"""
        self.fade_in.start()
        self.show()
        self.timer.start()
    
    def close_animation(self):
        """Close the notification with animation"""
        self.timer.stop()
        self.fade_out.start()
    
    def execute_action(self):
        """Execute the action callback"""
        if self.action_callback:
            self.action_callback()
            self.close_animation()
    
    def set_theme(self, theme):
        """Update theme"""
        self.theme = theme
        self.background_color = self.get_background_color()
        self.setStyleSheet(f"""
            ToastNotification {{
                background-color: {self.background_color};
                border-radius: 6px;
            }}
        """)


class ToastManager(QWidget):
    """Manager for toast notifications"""
    
    def __init__(self, parent=None, theme=None):
        super().__init__(parent)
        self.theme = theme or {}
        self.toast_spacing = 10
        self.toast_margin = 20
        self.active_toasts = []
        
        # Make widget transparent and frameless
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_NoSystemBackground)
        self.setStyleSheet("background: transparent;")
    
    def show_toast(self, message: str, type_: str = "info", duration: int = 3000,
                  action: Optional[Callable] = None, action_text: Optional[str] = None):
        """Show a toast notification
        
        Args:
            message: Message to display
            type_: Type of notification (info, success, error, warning)
            duration: Duration in milliseconds
            action: Optional callback function to execute when action button is clicked
            action_text: Optional text for the action button
        """
        # Create toast notification
        toast = ToastNotification(
            message, 
            type_,
            self.theme,
            duration,
            self,
            action,
            action_text
        )
        
        # Add to active toasts
        self.active_toasts.append(toast)
        
        # Position the toast
        self.position_toasts()
        
        # Show with animation
        toast.show_animation()
        
        # Connect close signal
        toast.fade_out.finished.connect(lambda: self.remove_toast(toast))
    
    def position_toasts(self):
        """Position all toast notifications"""
        if not self.parent():
            return
            
        # Get parent size
        parent_rect = self.parent().rect()
        
        # Position toasts from bottom up
        y = parent_rect.height() - self.toast_margin
        
        for toast in reversed(self.active_toasts):
            # Update toast width
            toast_width = min(400, parent_rect.width() - 2 * self.toast_margin)
            toast.setFixedWidth(toast_width)
            
            # Calculate toast height
            toast_height = toast.sizeHint().height()
            
            # Position toast
            x = parent_rect.width() - toast_width - self.toast_margin
            y -= toast_height + self.toast_spacing
            
            # Set position
            toast.setGeometry(x, y, toast_width, toast_height)
    
    def remove_toast(self, toast):
        """Remove a toast notification"""
        if toast in self.active_toasts:
            self.active_toasts.remove(toast)
            toast.deleteLater()
            
            # Reposition remaining toasts
            self.position_toasts()
    
    def set_theme(self, theme):
        """Update theme"""
        self.theme = theme
        
        # Update all active toasts
        for toast in self.active_toasts:
            toast.set_theme(theme)
