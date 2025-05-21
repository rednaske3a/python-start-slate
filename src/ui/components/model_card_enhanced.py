
"""
Enhanced model card widget with animations and more features
"""
from typing import Dict, Any

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QSizePolicy, QMenu, QApplication, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, Signal, QSize, QPropertyAnimation, QEasingCurve, QTimer, QPoint, QEvent, QRect
from PySide6.QtGui import QPixmap, QColor, QPainter, QPainterPath, QLinearGradient, QBrush

from src.utils.formatting import truncate_text, format_size, format_date, format_rating

class ModelCard(QWidget):
    """Enhanced model card widget"""
    
    clicked = Signal(dict)  # model data
    delete_requested = Signal(dict)  # model data
    update_requested = Signal(dict)  # model data
    favorite_toggled = Signal(dict, bool)  # model data, is_favorite
    
    def __init__(self, model_data: Dict[str, Any], theme: Dict[str, str], parent=None):
        super().__init__(parent)
        self.model_data = model_data
        self.theme = theme
        self.hover = False
        self.is_favorite = model_data.get("favorite", False)
        self.init_ui()
        
        # Install event filter for hover effects
        self.installEventFilter(self)
        
        # Animation properties
        self.scale_animation = QPropertyAnimation(self, b"geometry")
        self.scale_animation.setDuration(150)
        self.scale_animation.setEasingCurve(QEasingCurve.OutCubic)
    
    def init_ui(self):
        """Initialize UI components"""
        # Set fixed size and styling
        self.setFixedSize(200, 260)
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {self.theme['card']};
                border-radius: 8px;
                border: 1px solid {self.theme['border']};
            }}
            QWidget:hover {{
                border: 1px solid {self.theme['border_hover']};
            }}
        """)
        
        # Add shadow effect
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(self.theme["shadow"]))
        shadow.setOffset(0, 3)
        self.setGraphicsEffect(shadow)
        
        # Create layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 10)
        layout.setSpacing(5)
        
        # Thumbnail area
        self.thumbnail_container = QWidget()
        self.thumbnail_container.setFixedSize(200, 150)
        self.thumbnail_container.setStyleSheet(f"""
            QWidget {{
                background-color: {self.theme['secondary']};
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                border-bottom: 1px solid {self.theme['border']};
            }}
        """)
        thumbnail_layout = QVBoxLayout(self.thumbnail_container)
        thumbnail_layout.setContentsMargins(0, 0, 0, 0)
        
        # Thumbnail image (default placeholder)
        self.thumbnail = QLabel()
        self.thumbnail.setAlignment(Qt.AlignCenter)
        self.thumbnail.setStyleSheet("background-color: transparent;")
        self.thumbnail.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.set_thumbnail(self.model_data.get("thumbnail", ""))
        
        thumbnail_layout.addWidget(self.thumbnail)
        layout.addWidget(self.thumbnail_container)
        
        # Info area
        info_layout = QVBoxLayout()
        info_layout.setContentsMargins(10, 0, 10, 0)
        info_layout.setSpacing(5)
        
        # Model name
        name = self.model_data.get("name", "Unknown")
        self.name_label = QLabel(truncate_text(name, 25))
        self.name_label.setToolTip(name)
        self.name_label.setStyleSheet(f"""
            color: {self.theme['text']};
            font-size: 14px;
            font-weight: bold;
        """)
        self.name_label.setWordWrap(True)
        self.name_label.setAlignment(Qt.AlignLeft)
        info_layout.addWidget(self.name_label)
        
        # Type and base model
        type_base = f"{self.model_data.get('type', 'Unknown')} • {self.model_data.get('base_model', 'Unknown')}"
        type_label = QLabel(type_base)
        type_label.setStyleSheet(f"color: {self.theme['text_secondary']}; font-size: 12px;")
        type_label.setAlignment(Qt.AlignLeft)
        info_layout.addWidget(type_label)
        
        # Bottom row with stats
        stats_layout = QHBoxLayout()
        
        # Rating
        rating = self.model_data.get("rating", 0)
        rating_text = format_rating(rating)
        
        rating_label = QLabel(rating_text)
        rating_label.setStyleSheet(f"""
            color: {self.theme['text_secondary']};
            font-size: 12px;
            padding-right: 5px;
        """)
        stats_layout.addWidget(rating_label)
        
        # Add spacer to push the favorite button to the right
        stats_layout.addStretch()
        
        # Favorite button
        self.favorite_btn = QPushButton("★" if self.is_favorite else "☆")
        self.favorite_btn.setToolTip("Remove from Favorites" if self.is_favorite else "Add to Favorites")
        self.favorite_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {self.theme['accent'] if self.is_favorite else self.theme['text_secondary']};
                font-size: 16px;
                border: none;
                padding: 0px;
                width: 20px;
                height: 20px;
            }}
            QPushButton:hover {{
                color: {self.theme['accent']};
            }}
        """)
        self.favorite_btn.clicked.connect(self.toggle_favorite)
        stats_layout.addWidget(self.favorite_btn)
        
        info_layout.addLayout(stats_layout)
        layout.addLayout(info_layout)
        
        # Set cursor to pointer
        self.setCursor(Qt.PointingHandCursor)
    
    def set_thumbnail(self, path):
        """Set the thumbnail image"""
        if not path:
            # Default placeholder
            self.thumbnail.setText("No Image")
            self.thumbnail.setStyleSheet(f"""
                background-color: {self.theme['secondary']};
                color: {self.theme['text_tertiary']};
                font-size: 14px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
            """)
            return
            
        try:
            pixmap = QPixmap(path)
            if not pixmap.isNull():
                # Resize to fit while maintaining aspect ratio
                pixmap = pixmap.scaled(
                    self.thumbnail.size(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                self.thumbnail.setPixmap(pixmap)
                self.thumbnail.setStyleSheet("background-color: transparent;")
            else:
                # Fallback if image can't be loaded
                self.thumbnail.setText("Image Error")
                self.thumbnail.setStyleSheet(f"""
                    background-color: {self.theme['secondary']};
                    color: {self.theme['text_tertiary']};
                    font-size: 14px;
                    border-top-left-radius: 8px;
                    border-top-right-radius: 8px;
                """)
        except Exception as e:
            print(f"Error setting thumbnail: {e}")
            self.thumbnail.setText("Image Error")
            self.thumbnail.setStyleSheet(f"""
                background-color: {self.theme['secondary']};
                color: {self.theme['text_tertiary']};
                font-size: 14px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
            """)
    
    def toggle_favorite(self):
        """Toggle favorite status"""
        self.is_favorite = not self.is_favorite
        self.favorite_btn.setText("★" if self.is_favorite else "☆")
        self.favorite_btn.setToolTip("Remove from Favorites" if self.is_favorite else "Add to Favorites")
        self.favorite_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {self.theme['accent'] if self.is_favorite else self.theme['text_secondary']};
                font-size: 16px;
                border: none;
                padding: 0px;
                width: 20px;
                height: 20px;
            }}
            QPushButton:hover {{
                color: {self.theme['accent']};
            }}
        """)
        self.favorite_toggled.emit(self.model_data, self.is_favorite)
    
    def mousePressEvent(self, event):
        """Handle mouse press event"""
        if event.button() == Qt.RightButton:
            self.show_context_menu(event.globalPos())
        super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release event"""
        if event.button() == Qt.LeftButton:
            # Only emit clicked if mouse was released within the widget
            if self.rect().contains(event.pos()):
                self.clicked.emit(self.model_data)
        super().mouseReleaseEvent(event)
    
    def show_context_menu(self, global_pos):
        """Show context menu"""
        menu = QMenu(self)
        
        # View details action
        view_action = menu.addAction("View Details")
        view_action.triggered.connect(lambda: self.clicked.emit(self.model_data))
        
        # Favorite action
        fav_text = "Remove from Favorites" if self.is_favorite else "Add to Favorites"
        fav_action = menu.addAction(fav_text)
        fav_action.triggered.connect(self.toggle_favorite)
        
        # Check for updates
        menu.addAction("Check for Updates").triggered.connect(
            lambda: self.update_requested.emit(self.model_data)
        )
        
        # Separator
        menu.addSeparator()
        
        # Delete action
        delete_action = menu.addAction("Delete")
        delete_action.setToolTip("Delete this model and its files")
        delete_action.triggered.connect(lambda: self.delete_requested.emit(self.model_data))
        
        menu.exec(global_pos)
    
    def eventFilter(self, obj, event):
        """Event filter for hover effects"""
        if obj == self:
            if event.type() == QEvent.Enter:
                self.hover = True
                self.start_hover_animation(True)
                return True
            elif event.type() == QEvent.Leave:
                self.hover = False
                self.start_hover_animation(False)
                return True
        return super().eventFilter(obj, event)
    
    def start_hover_animation(self, hover_in):
        """Start hover animation"""
        if hover_in:
            # Scale up slightly
            current_geo = self.geometry()
            target_geo = current_geo.adjusted(-3, -3, 3, 3)
            
            self.scale_animation.setStartValue(current_geo)
            self.scale_animation.setEndValue(target_geo)
        else:
            # Scale back to original size
            current_geo = self.geometry()
            target_geo = current_geo.adjusted(3, 3, -3, -3)
            
            self.scale_animation.setStartValue(current_geo)
            self.scale_animation.setEndValue(target_geo)
            
        self.scale_animation.start()
    
    def set_theme(self, theme):
        """Update the theme"""
        self.theme = theme
        
        # Update main widget style
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {self.theme['card']};
                border-radius: 8px;
                border: 1px solid {self.theme['border']};
            }}
            QWidget:hover {{
                border: 1px solid {self.theme['border_hover']};
            }}
        """)
        
        # Update shadow
        shadow = self.graphicsEffect()
        if shadow and isinstance(shadow, QGraphicsDropShadowEffect):
            shadow.setColor(QColor(self.theme["shadow"]))
        
        # Update thumbnail container
        self.thumbnail_container.setStyleSheet(f"""
            QWidget {{
                background-color: {self.theme['secondary']};
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                border-bottom: 1px solid {self.theme['border']};
            }}
        """)
        
        # Update labels
        self.name_label.setStyleSheet(f"""
            color: {self.theme['text']};
            font-size: 14px;
            font-weight: bold;
        """)
        
        # Find and update type label
        for child in self.findChildren(QLabel):
            if child != self.name_label and child != self.thumbnail:
                child.setStyleSheet(f"color: {self.theme['text_secondary']}; font-size: 12px;")
        
        # Update favorite button
        self.favorite_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {self.theme['accent'] if self.is_favorite else self.theme['text_secondary']};
                font-size: 16px;
                border: none;
                padding: 0px;
                width: 20px;
                height: 20px;
            }}
            QPushButton:hover {{
                color: {self.theme['accent']};
            }}
        """)
        
        # Update thumbnail if it's showing placeholder text
        if not self.thumbnail.pixmap():
            self.thumbnail.setStyleSheet(f"""
                background-color: {self.theme['secondary']};
                color: {self.theme['text_tertiary']};
                font-size: 14px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
            """)
    
    def paintEvent(self, event):
        """Custom paint event to create rounded corners"""
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Create rounded corner path
        path = QPainterPath()
        path.addRoundedRect(self.rect(), 8, 8)
        
        # Use path as clipping mask
        painter.setClipPath(path)
        
        # Draw NSFW indicator if needed
        if self.model_data.get("nsfw", False):
            nsfw_rect = QRect(self.width() - 50, 0, 50, 25)
            painter.fillRect(nsfw_rect, QColor(self.theme["danger"]))
            painter.setPen(QColor("white"))
            painter.drawText(nsfw_rect, Qt.AlignCenter, "NSFW")
