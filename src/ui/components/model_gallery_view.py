
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QGridLayout,
    QScrollArea, QFrame, QMenu, QToolButton, QGraphicsOpacityEffect,
    QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QSize, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QPixmap, QIcon, QColor, QPainter, QPalette, QImage, QCursor

import os
from pathlib import Path
from typing import Dict, List, Optional

from src.utils.logger import get_logger

logger = get_logger(__name__)


class ModelCard(QFrame):
    """Card widget for displaying a model"""
    
    clicked = Signal(dict)
    favorite_toggled = Signal(dict, bool)
    delete_requested = Signal(dict)
    update_requested = Signal(dict)
    
    def __init__(self, model_data: Dict, theme: Dict, parent=None):
        super().__init__(parent)
        self.model_data = model_data
        self.theme = theme
        self.setMouseTracking(True)
        
        # Set up frame styles
        self.setFrameShape(QFrame.StyledPanel)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(f"""
            ModelCard {{
                background-color: {self.theme['card']};
                border-radius: 8px;
                border: 1px solid {self.theme['border']};
            }}
            ModelCard:hover {{
                background-color: {self.theme['card_hover']};
                border-color: {self.theme['accent']};
            }}
        """)
        
        # Set fixed size for cards
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setFixedSize(220, 280)
        
        self.init_ui()
        
        # Add hover animation effect
        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(200)
        self.animation.setEasingCurve(QEasingCurve.OutCubic)
    
    def init_ui(self):
        """Initialize UI components"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        
        # Thumbnail
        self.thumbnail = QLabel()
        self.thumbnail.setFixedSize(200, 160)
        self.thumbnail.setScaledContents(True)
        self.thumbnail.setStyleSheet(f"background-color: {self.theme['secondary']}; border-radius: 4px;")
        self.setThumbnailFromData()
        
        # Model name
        self.name_label = QLabel(self.model_data.get("name", "Unknown Model"))
        self.name_label.setWordWrap(True)
        self.name_label.setAlignment(Qt.AlignCenter)
        self.name_label.setStyleSheet(f"""
            font-weight: bold;
            color: {self.theme['text']};
            font-size: 13px;
        """)
        
        # Info row
        info_layout = QHBoxLayout()
        info_layout.setSpacing(4)
        
        # Type badge
        self.type_badge = QLabel(self.model_data.get("type", "Unknown"))
        self.type_badge.setStyleSheet(f"""
            background-color: {self.theme['secondary']};
            color: {self.theme['text_secondary']};
            border-radius: 4px;
            padding: 2px 6px;
            font-size: 10px;
        """)
        
        # Rating stars
        rating = self.model_data.get("rating", 0)
        stars = min(5, max(0, int(rating / 20)))
        
        self.rating_label = QLabel("★" * stars + "☆" * (5 - stars))
        self.rating_label.setStyleSheet(f"color: #FFC107; font-size: 12px;")
        
        info_layout.addWidget(self.type_badge)
        info_layout.addStretch()
        info_layout.addWidget(self.rating_label)
        
        # Action buttons row
        actions_layout = QHBoxLayout()
        
        # Favorite button
        self.fav_button = QPushButton()
        self.fav_button.setCheckable(True)
        self.fav_button.setChecked(self.model_data.get("favorite", False))
        self.fav_button.setFixedSize(28, 28)
        self.fav_button.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                font-size: 16px;
                color: {self.theme['text_secondary']};
            }}
            QPushButton:hover {{
                color: {self.theme['accent']};
            }}
            QPushButton:checked {{
                color: {self.theme['accent']};
            }}
        """)
        self.fav_button.setText("♥" if self.model_data.get("favorite", False) else "♡")
        self.fav_button.clicked.connect(self.toggle_favorite)
        
        # Menu button
        self.menu_button = QPushButton("⋮")
        self.menu_button.setFixedSize(28, 28)
        self.menu_button.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                font-size: 16px;
                font-weight: bold;
                color: {self.theme['text_secondary']};
            }}
            QPushButton:hover {{
                color: {self.theme['text']};
            }}
        """)
        self.menu_button.clicked.connect(self.show_context_menu)
        
        actions_layout.addStretch()
        actions_layout.addWidget(self.fav_button)
        actions_layout.addWidget(self.menu_button)
        
        # Add components to layout
        layout.addWidget(self.thumbnail)
        layout.addWidget(self.name_label)
        layout.addLayout(info_layout)
        layout.addLayout(actions_layout)
    
    def setThumbnailFromData(self):
        """Set thumbnail from model data"""
        # Get thumbnail from model data
        thumbnail_path = self.model_data.get("thumbnail", "")
        
        if thumbnail_path and os.path.exists(thumbnail_path):
            # Local image
            pixmap = QPixmap(thumbnail_path)
            if not pixmap.isNull():
                # Crop to square if needed
                if pixmap.width() != pixmap.height():
                    size = min(pixmap.width(), pixmap.height())
                    x = (pixmap.width() - size) // 2
                    y = (pixmap.height() - size) // 2
                    pixmap = pixmap.copy(x, y, size, size)
                
                self.thumbnail.setPixmap(pixmap.scaled(
                    self.thumbnail.width(), 
                    self.thumbnail.height(),
                    Qt.KeepAspectRatio, 
                    Qt.SmoothTransformation
                ))
                return
        
        # If we got here, either no thumbnail or loading failed
        # Show first image from model if available
        images = self.model_data.get("images", [])
        if images and len(images) > 0:
            for img in images:
                if "local_path" in img and os.path.exists(img["local_path"]):
                    pixmap = QPixmap(img["local_path"])
                    if not pixmap.isNull():
                        self.thumbnail.setPixmap(pixmap.scaled(
                            self.thumbnail.width(), 
                            self.thumbnail.height(),
                            Qt.KeepAspectRatio, 
                            Qt.SmoothTransformation
                        ))
                        # Cache this image as thumbnail
                        self.model_data["thumbnail"] = img["local_path"]
                        return
        
        # If no images, use placeholder
        self.thumbnail.setText(self.model_data.get("type", "?"))
        self.thumbnail.setAlignment(Qt.AlignCenter)
        self.thumbnail.setStyleSheet(f"""
            background-color: {self.theme['secondary']};
            color: {self.theme['text_secondary']};
            font-size: 24px;
            font-weight: bold;
            border-radius: 4px;
        """)
    
    def toggle_favorite(self):
        """Toggle favorite status"""
        is_favorite = self.fav_button.isChecked()
        self.model_data["favorite"] = is_favorite
        self.fav_button.setText("♥" if is_favorite else "♡")
        self.favorite_toggled.emit(self.model_data, is_favorite)
    
    def show_context_menu(self):
        """Show context menu"""
        menu = QMenu(self)
        
        # Add menu actions
        view_action = menu.addAction("View Details")
        update_action = menu.addAction("Check for Updates")
        menu.addSeparator()
        delete_action = menu.addAction("Delete")
        
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
        
        # Show the menu and handle actions
        action = menu.exec_(QCursor.pos())
        if action == view_action:
            self.clicked.emit(self.model_data)
        elif action == delete_action:
            self.delete_requested.emit(self.model_data)
        elif action == update_action:
            self.update_requested.emit(self.model_data)
    
    def mousePressEvent(self, event):
        """Handle mouse press event"""
        if event.button() == Qt.LeftButton:
            # Ignore clicks on buttons
            if (self.fav_button.geometry().contains(event.pos()) or
                self.menu_button.geometry().contains(event.pos())):
                return
            
            self.clicked.emit(self.model_data)
        super().mousePressEvent(event)
    
    def enterEvent(self, event):
        """Handle mouse enter event"""
        # Animate card rise effect
        self.animation.stop()
        self.animation.setStartValue(self.geometry())
        raised_geom = self.geometry()
        raised_geom.setY(raised_geom.y() - 5)
        self.animation.setEndValue(raised_geom)
        self.animation.start()
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """Handle mouse leave event"""
        # Animate card drop effect
        self.animation.stop()
        self.animation.setStartValue(self.geometry())
        normal_geom = self.geometry()
        normal_geom.setY(normal_geom.y() + 5)
        self.animation.setEndValue(normal_geom)
        self.animation.start()
        super().leaveEvent(event)
    
    def set_theme(self, theme):
        """Update theme"""
        self.theme = theme
        
        # Update styles
        self.setStyleSheet(f"""
            ModelCard {{
                background-color: {self.theme['card']};
                border-radius: 8px;
                border: 1px solid {self.theme['border']};
            }}
            ModelCard:hover {{
                background-color: {self.theme['card_hover']};
                border-color: {self.theme['accent']};
            }}
        """)
        
        self.thumbnail.setStyleSheet(f"background-color: {self.theme['secondary']}; border-radius: 4px;")
        
        self.name_label.setStyleSheet(f"""
            font-weight: bold;
            color: {self.theme['text']};
            font-size: 13px;
        """)
        
        self.type_badge.setStyleSheet(f"""
            background-color: {self.theme['secondary']};
            color: {self.theme['text_secondary']};
            border-radius: 4px;
            padding: 2px 6px;
            font-size: 10px;
        """)
        
        self.fav_button.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                font-size: 16px;
                color: {self.theme['text_secondary']};
            }}
            QPushButton:hover {{
                color: {self.theme['accent']};
            }}
            QPushButton:checked {{
                color: {self.theme['accent']};
            }}
        """)
        
        self.menu_button.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                font-size: 16px;
                font-weight: bold;
                color: {self.theme['text_secondary']};
            }}
            QPushButton:hover {{
                color: {self.theme['text']};
            }}
        """)
    
    def update_model(self, model_data):
        """Update model data"""
        self.model_data = model_data
        
        # Update UI
        self.name_label.setText(model_data.get("name", "Unknown Model"))
        self.type_badge.setText(model_data.get("type", "Unknown"))
        
        # Update favorite button
        is_favorite = model_data.get("favorite", False)
        self.fav_button.setChecked(is_favorite)
        self.fav_button.setText("♥" if is_favorite else "♡")
        
        # Update thumbnail
        self.setThumbnailFromData()
        
        # Update rating stars
        rating = model_data.get("rating", 0)
        stars = min(5, max(0, int(rating / 20)))
        self.rating_label.setText("★" * stars + "☆" * (5 - stars))


class ModelGalleryView(QScrollArea):
    """Gallery view for models"""
    
    model_clicked = Signal(dict)
    model_deleted = Signal(dict)
    model_update_requested = Signal(dict)
    favorite_toggled = Signal(dict, bool)
    
    def __init__(self, theme: Dict, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.models = []
        self.filtered_models = []
        self.card_widgets = []
        
        # Set up scroll area
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setStyleSheet(f"""
            QScrollArea {{
                background-color: {self.theme['primary']};
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
        
        # Create container widget
        self.container = QWidget()
        self.setWidget(self.container)
        
        # Create grid layout for cards
        self.grid_layout = QGridLayout(self.container)
        self.grid_layout.setContentsMargins(20, 20, 20, 20)
        self.grid_layout.setSpacing(20)
        
        # No models message
        self.no_models_label = QLabel("No models found")
        self.no_models_label.setAlignment(Qt.AlignCenter)
        self.no_models_label.setStyleSheet(f"""
            color: {self.theme['text_secondary']};
            font-size: 16px;
            font-style: italic;
            padding: 40px;
        """)
        self.grid_layout.addWidget(self.no_models_label, 0, 0, 1, 4, Qt.AlignCenter)
        
        # Timer for delayed layout update
        self.layout_timer = QTimer(self)
        self.layout_timer.setSingleShot(True)
        self.layout_timer.timeout.connect(self.update_layout)
    
    def set_models(self, models: List[Dict]):
        """Set models data"""
        self.models = models
        self.filtered_models = models.copy()
        self.populate_grid()
    
    def apply_filter(self, filters: Dict):
        """Apply filters to models"""
        if not filters:
            self.filtered_models = self.models
            self.populate_grid()
            return
            
        filtered = []
        
        for model in self.models:
            include = True
            
            # Filter by text
            if "search" in filters and filters["search"]:
                search_text = filters["search"].lower()
                name_match = search_text in model.get("name", "").lower()
                desc_match = search_text in model.get("description", "").lower()
                tag_match = any(search_text in tag.lower() for tag in model.get("tags", []))
                
                if not (name_match or desc_match or tag_match):
                    include = False
            
            # Filter by type
            if include and "type" in filters and filters["type"]:
                if model.get("type") != filters["type"]:
                    include = False
            
            # Filter by base model
            if include and "base_model" in filters and filters["base_model"]:
                if model.get("base_model") != filters["base_model"]:
                    include = False
            
            # Filter by NSFW
            if include and "nsfw" in filters:
                if model.get("nsfw", False) != filters["nsfw"]:
                    include = False
            
            # Filter by favorite
            if include and "favorite" in filters and filters["favorite"]:
                if not model.get("favorite", False):
                    include = False
            
            if include:
                filtered.append(model)
        
        self.filtered_models = filtered
        self.populate_grid()
    
    def populate_grid(self):
        """Populate grid with model cards"""
        # Clear existing widgets
        for card in self.card_widgets:
            card.deleteLater()
        self.card_widgets.clear()
        
        # Show no models message if empty
        if not self.filtered_models:
            self.no_models_label.show()
            return
        else:
            self.no_models_label.hide()
        
        # Delay layout update to prevent flickering
        self.layout_timer.start(10)
    
    def update_layout(self):
        """Update layout with model cards"""
        # Calculate grid columns based on width
        width = self.viewport().width()
        card_width = 220 + 20  # Card width + spacing
        columns = max(1, width // card_width)
        
        # Add model cards to grid
        row, col = 0, 0
        for model in self.filtered_models:
            card = ModelCard(model, self.theme)
            card.clicked.connect(self.model_clicked)
            card.favorite_toggled.connect(self.favorite_toggled)
            card.delete_requested.connect(self.model_deleted)
            card.update_requested.connect(self.model_update_requested)
            
            self.grid_layout.addWidget(card, row, col)
            self.card_widgets.append(card)
            
            # Update grid position
            col += 1
            if col >= columns:
                col = 0
                row += 1
    
    def resizeEvent(self, event):
        """Handle resize event"""
        super().resizeEvent(event)
        
        # Update layout on resize
        if hasattr(self, "layout_timer"):
            self.layout_timer.start(100)
    
    def set_theme(self, theme):
        """Update theme"""
        self.theme = theme
        
        # Update scroll area style
        self.setStyleSheet(f"""
            QScrollArea {{
                background-color: {self.theme['primary']};
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
        
        self.no_models_label.setStyleSheet(f"""
            color: {self.theme['text_secondary']};
            font-size: 16px;
            font-style: italic;
            padding: 40px;
        """)
        
        # Update all card widgets
        for card in self.card_widgets:
            card.set_theme(theme)
    
    def update_model(self, model_data):
        """Update a specific model in the gallery"""
        model_id = model_data.get("id")
        if not model_id:
            return
        
        # Update model in the list
        for i, model in enumerate(self.models):
            if model.get("id") == model_id:
                self.models[i] = model_data
                break
        
        # Update model in filtered list
        for i, model in enumerate(self.filtered_models):
            if model.get("id") == model_id:
                self.filtered_models[i] = model_data
                break
        
        # Update card widget if it exists
        for card in self.card_widgets:
            if card.model_data.get("id") == model_id:
                card.update_model(model_data)
                break
