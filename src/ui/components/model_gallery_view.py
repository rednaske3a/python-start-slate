
"""
Model gallery view component supporting both card and list views
"""
from typing import Dict, List, Optional
from enum import Enum

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, 
    QGridLayout, QTableWidget, QTableWidgetItem, QAbstractItemView,
    QHeaderView, QPushButton, QLabel, QMenu, QFileDialog,
    QFrame, QToolBar, QComboBox, QSizePolicy, QApplication
)
from PySide6.QtCore import Qt, Signal, QSize, QUrl
from PySide6.QtGui import QAction, QIcon, QPixmap, QImage, QColor, QPainter, QClipboard, QGuiApplication, QDesktopServices

from src.constants.constants import VIEW_MODE, SORT_OPTIONS
from src.ui.components.model_card import ModelCard
from src.utils.formatting import format_size, format_date, format_rating

class ModelGalleryView(QWidget):
    """Gallery view for displaying model cards or list"""
    
    model_clicked = Signal(dict)  # model data
    favorite_toggled = Signal(dict, bool)  # model data, is_favorite
    model_deleted = Signal(dict)  # model data
    model_update_requested = Signal(dict)  # model data
    filter_changed = Signal(dict)  # filter settings
    
    def __init__(self, theme: Dict, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.models = []
        self.filtered_models = []
        self.current_view_mode = VIEW_MODE["CARD"]
        self.column_count = 4
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI components"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create toolbar with view options
        self.toolbar = self.create_toolbar()
        layout.addWidget(self.toolbar)
        
        # Stack for different views
        self.stack_layout = QVBoxLayout()
        
        # Card view
        self.card_scroll = QScrollArea()
        self.card_scroll.setWidgetResizable(True)
        self.card_scroll.setStyleSheet("background-color: transparent; border: none;")
        
        self.card_widget = QWidget()
        self.card_layout = QGridLayout(self.card_widget)
        self.card_layout.setContentsMargins(10, 10, 10, 10)
        self.card_layout.setSpacing(15)
        
        self.card_scroll.setWidget(self.card_widget)
        
        # List view
        self.list_view = QTableWidget()
        # ... (all your list_view setup code) ...
        
        # Add views to layout but only show the active one
        self.stack_layout.addWidget(self.card_scroll)
        self.stack_layout.addWidget(self.list_view)
        
        layout.addLayout(self.stack_layout)
        
        # --- MOVE THIS BLOCK UP HERE, BEFORE set_view_mode! ---
        self.empty_label = QLabel("No models found matching your filters.")
        self.empty_label.setAlignment(Qt.AlignCenter)
        self.empty_label.setStyleSheet(f"""
            color: {self.theme['text_tertiary']};
            font-size: 16px;
            padding: 40px;
        """)
        self.empty_label.hide()
        layout.addWidget(self.empty_label)
        # ------------------------------------------------------
        
        # Set initial view
        self.set_view_mode(VIEW_MODE["CARD"])

    
    def create_toolbar(self):
        """Create toolbar with view and sort options"""
        toolbar = QToolBar()
        toolbar.setStyleSheet(f"""
            QToolBar {{
                background-color: {self.theme['secondary']};
                border: none;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                spacing: 5px;
                padding: 5px;
            }}
            QToolButton {{
                background-color: transparent;
                color: {self.theme['text']};
                border: none;
                padding: 5px;
                border-radius: 4px;
            }}
            QToolButton:hover {{
                background-color: {self.theme['card_hover']};
            }}
            QToolButton:checked {{
                background-color: {self.theme['accent']}40;
            }}
            QComboBox {{
                background-color: {self.theme['card']};
                color: {self.theme['text']};
                border: 1px solid {self.theme['border']};
                padding: 5px;
                border-radius: 4px;
                min-width: 120px;
            }}
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 15px;
                border-left: 1px solid {self.theme['border']};
            }}
        """)
        
        # View mode group
        view_label = QLabel("View:")
        view_label.setStyleSheet(f"color: {self.theme['text_secondary']};")
        toolbar.addWidget(view_label)
        
        # Card view button
        self.card_view_action = QAction("Cards", self)
        self.card_view_action.setCheckable(True)
        self.card_view_action.setChecked(True)
        self.card_view_action.triggered.connect(lambda: self.set_view_mode(VIEW_MODE["CARD"]))
        toolbar.addAction(self.card_view_action)
        
        # List view button
        self.list_view_action = QAction("List", self)
        self.list_view_action.setCheckable(True)
        self.list_view_action.triggered.connect(lambda: self.set_view_mode(VIEW_MODE["LIST"]))
        toolbar.addAction(self.list_view_action)
        
        toolbar.addSeparator()
        
        # Sort options
        sort_label = QLabel("Sort by:")
        sort_label.setStyleSheet(f"color: {self.theme['text_secondary']};")
        toolbar.addWidget(sort_label)
        
        self.sort_combo = QComboBox()
        self.sort_combo.addItem("Date", SORT_OPTIONS["DATE"])
        self.sort_combo.addItem("Name", SORT_OPTIONS["NAME"])
        self.sort_combo.addItem("Size", SORT_OPTIONS["SIZE"])
        self.sort_combo.addItem("Type", SORT_OPTIONS["TYPE"])
        self.sort_combo.addItem("Rating", SORT_OPTIONS["RATING"])
        self.sort_combo.currentIndexChanged.connect(self.on_sort_changed)
        toolbar.addWidget(self.sort_combo)
        
        toolbar.addSeparator()
        
        # Column count for card view
        columns_label = QLabel("Columns:")
        columns_label.setStyleSheet(f"color: {self.theme['text_secondary']};")
        toolbar.addWidget(columns_label)
        
        self.columns_combo = QComboBox()
        self.columns_combo.addItem("2", 2)
        self.columns_combo.addItem("3", 3)
        self.columns_combo.addItem("4", 4)
        self.columns_combo.addItem("5", 5)
        self.columns_combo.addItem("6", 6)
        self.columns_combo.setCurrentText(str(self.column_count))
        self.columns_combo.currentIndexChanged.connect(self.on_columns_changed)
        toolbar.addWidget(self.columns_combo)
        
        # Spacer to push the next items to the right
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        toolbar.addWidget(spacer)
        
        # Results count
        self.results_label = QLabel("0 models")
        self.results_label.setStyleSheet(f"color: {self.theme['text_secondary']};")
        toolbar.addWidget(self.results_label)
        
        return toolbar
    
    def set_view_mode(self, mode):
        """Set the current view mode"""
        self.current_view_mode = mode
        
        # Update actions
        self.card_view_action.setChecked(mode == VIEW_MODE["CARD"])
        self.list_view_action.setChecked(mode == VIEW_MODE["LIST"])
        
        # Show the appropriate view
        if mode == VIEW_MODE["CARD"]:
            self.card_scroll.show()
            self.list_view.hide()
            self.columns_combo.setEnabled(True)
        else:
            self.card_scroll.hide()
            self.list_view.show()
            self.columns_combo.setEnabled(False)
        
        # Refresh the view
        self.refresh_view()
    
    def on_sort_changed(self, index):
        """Handle sort option change"""
        sort_value = self.sort_combo.currentData()
        self.sort_models(sort_value)
    
    def on_columns_changed(self, index):
        """Handle column count change"""
        self.column_count = self.columns_combo.currentData()
        self.refresh_view()
    
    def on_header_sort(self, column, order):
        """Handle sorting when clicking on table header"""
        # Map column indices to sort options
        column_sort_map = {
            0: SORT_OPTIONS["NAME"],    # Name
            1: SORT_OPTIONS["TYPE"],    # Type
            2: SORT_OPTIONS["SIZE"],    # Size
            3: SORT_OPTIONS["DATE"],    # Date
            4: SORT_OPTIONS["RATING"]   # Rating
        }
        
        if column in column_sort_map:
            # Update combo box to match table header
            sort_option = column_sort_map[column]
            index = self.sort_combo.findData(sort_option)
            if index >= 0:
                self.sort_combo.setCurrentIndex(index)
            
            # Sort models
            self.sort_models(sort_option, order == Qt.AscendingOrder)
    
    def sort_models(self, sort_option, ascending=False):
        """Sort models based on the selected option"""
        if not self.filtered_models:
            return
        
        # Sort models
        if sort_option == SORT_OPTIONS["NAME"]:
            self.filtered_models.sort(key=lambda m: m.get("name", "").lower(), reverse=not ascending)
        elif sort_option == SORT_OPTIONS["SIZE"]:
            self.filtered_models.sort(key=lambda m: m.get("size", 0), reverse=not ascending)
        elif sort_option == SORT_OPTIONS["TYPE"]:
            self.filtered_models.sort(key=lambda m: m.get("type", ""), reverse=not ascending)
        elif sort_option == SORT_OPTIONS["RATING"]:
            self.filtered_models.sort(key=lambda m: m.get("rating", 0), reverse=not ascending)
        else:  # Default to DATE
            self.filtered_models.sort(key=lambda m: m.get("download_date", ""), reverse=not ascending)
        
        # Refresh view
        self.refresh_view()
    
    def set_models(self, models):
        """Set the models to display"""
        self.models = models
        self.filtered_models = models.copy()
        self.results_label.setText(f"{len(self.filtered_models)} models")
        self.refresh_view()
    
    def apply_filter(self, filter_dict):
        """Apply filters to the models"""
        self.filtered_models = self.models.copy()
        
        # Type filter
        if filter_dict.get("type") and filter_dict["type"] != "all":
            self.filtered_models = [m for m in self.filtered_models if m.get("type") == filter_dict["type"]]
        
        # Base model filter
        if filter_dict.get("base_model") and filter_dict["base_model"] != "all":
            self.filtered_models = [m for m in self.filtered_models if m.get("base_model") == filter_dict["base_model"]]
        
        # NSFW filter
        if filter_dict.get("nsfw") == "hide":
            self.filtered_models = [m for m in self.filtered_models if not m.get("nsfw", False)]
        elif filter_dict.get("nsfw") == "only":
            self.filtered_models = [m for m in self.filtered_models if m.get("nsfw", False)]
        
        # Favorite filter
        if filter_dict.get("favorite"):
            self.filtered_models = [m for m in self.filtered_models if m.get("favorite", False)]
        
        # Text search
        if filter_dict.get("search"):
            search = filter_dict["search"].lower()
            self.filtered_models = [
                m for m in self.filtered_models if (
                    search in m.get("name", "").lower() or
                    search in m.get("creator", "").lower() or
                    search in m.get("description", "").lower() or
                    any(search in tag.lower() for tag in m.get("tags", []))
                )
            ]
        
        # Update result count
        self.results_label.setText(f"{len(self.filtered_models)} models")
        
        # Sort models with current sort option
        sort_value = self.sort_combo.currentData()
        self.sort_models(sort_value)
    
    def refresh_view(self):
        """Refresh the current view with filtered models"""
        if self.current_view_mode == VIEW_MODE["CARD"]:
            self.refresh_card_view()
        else:
            self.refresh_list_view()
            
        # Show/hide empty state
        if not self.filtered_models:
            self.empty_label.show()
        else:
            self.empty_label.hide()
    
    def refresh_card_view(self):
        """Refresh the card view"""
        # Clear existing cards
        while self.card_layout.count():
            item = self.card_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Create new cards
        row, col = 0, 0
        for model in self.filtered_models:
            card = ModelCard(model, self.theme)
            card.clicked.connect(lambda m=model: self.model_clicked.emit(m))
            card.favorite_toggled.connect(self.favorite_toggled.emit)
            card.delete_requested.connect(self.model_deleted.emit)
            card.update_requested.connect(self.model_update_requested.emit)
            
            self.card_layout.addWidget(card, row, col)
            
            col += 1
            if col >= self.column_count:
                col = 0
                row += 1
    
    def refresh_list_view(self):
        """Refresh the list view"""
        # Disconnect signal during refresh
        self.list_view.blockSignals(True)
        
        # Clear existing items
        self.list_view.setRowCount(0)
        
        # Add rows for each model
        self.list_view.setRowCount(len(self.filtered_models))
        
        for i, model in enumerate(self.filtered_models):
            # Name
            name_item = QTableWidgetItem(model.get("name", "Unknown"))
            name_item.setData(Qt.UserRole, model)
            self.list_view.setItem(i, 0, name_item)
            
            # Type
            type_item = QTableWidgetItem(model.get("type", "Other"))
            self.list_view.setItem(i, 1, type_item)
            
            # Size
            size = model.get("size", 0)
            size_item = QTableWidgetItem(format_size(size))
            size_item.setData(Qt.UserRole, size)  # Store raw size for sorting
            self.list_view.setItem(i, 2, size_item)
            
            # Date
            date = model.get("download_date", "")
            date_item = QTableWidgetItem(format_date(date, short=True))
            date_item.setData(Qt.UserRole, date)  # Store raw date for sorting
            self.list_view.setItem(i, 3, date_item)
            
            # Rating
            rating = model.get("rating", 0)
            rating_item = QTableWidgetItem(format_rating(rating))
            rating_item.setData(Qt.UserRole, rating)  # Store raw rating for sorting
            self.list_view.setItem(i, 4, rating_item)
        
        # Reconnect signal
        self.list_view.blockSignals(False)
    
    def show_list_context_menu(self, position):
        """Show context menu for list view"""
        row = self.list_view.rowAt(position.y())
        if row < 0:
            return
            
        # Get model data
        model_data = self.list_view.item(row, 0).data(Qt.UserRole)
        if not model_data:
            return
            
        # Create context menu
        menu = QMenu(self)
        
        # Open action
        open_action = menu.addAction("View Details")
        open_action.triggered.connect(lambda: self.model_clicked.emit(model_data))
        
        # Favorite action
        is_favorite = model_data.get("favorite", False)
        fav_action = menu.addAction("Remove from Favorites" if is_favorite else "Add to Favorites")
        fav_action.triggered.connect(lambda: self.favorite_toggled.emit(model_data, not is_favorite))
        
        menu.addSeparator()
        
        # Location action
        path = model_data.get("path", "")
        if path:
            location_action = menu.addAction("Open Location")
            location_action.triggered.connect(lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(path)))
            
            copy_path_action = menu.addAction("Copy Path")
            copy_path_action.triggered.connect(lambda: QGuiApplication.clipboard().setText(path))
        
        menu.addSeparator()
        
        # Delete action
        delete_action = menu.addAction("Delete")
        delete_action.triggered.connect(lambda: self.model_deleted.emit(model_data))
        
        # Execute menu
        menu.exec(self.list_view.viewport().mapToGlobal(position))
    
    def update_model(self, model_data):
        """Update a specific model's data"""
        # Find and update model in both lists
        for i, model in enumerate(self.models):
            if model.get("id") == model_data.get("id"):
                self.models[i] = model_data
                break
                
        for i, model in enumerate(self.filtered_models):
            if model.get("id") == model_data.get("id"):
                self.filtered_models[i] = model_data
                break
        
        # Refresh view
        self.refresh_view()
    
    def set_theme(self, theme):
        """Update the theme"""
        self.theme = theme
        
        # Update list view style
        self.list_view.setStyleSheet(f"""
            QTableWidget {{
                background-color: transparent;
                border: none;
                gridline-color: {self.theme['border']};
            }}
            QHeaderView::section {{
                background-color: {self.theme['secondary']};
                color: {self.theme['text']};
                padding: 5px;
                border: 1px solid {self.theme['border']};
            }}
            QTableWidget::item {{
                border-bottom: 1px solid {self.theme['border']};
                color: {self.theme['text']};
            }}
            QTableWidget::item:selected {{
                background-color: {self.theme['accent']}40;
                color: {self.theme['text']};
            }}
        """)
        
        # Update toolbar style
        self.toolbar.setStyleSheet(f"""
            QToolBar {{
                background-color: {self.theme['secondary']};
                border: none;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                spacing: 5px;
                padding: 5px;
            }}
            QToolButton {{
                background-color: transparent;
                color: {self.theme['text']};
                border: none;
                padding: 5px;
                border-radius: 4px;
            }}
            QToolButton:hover {{
                background-color: {self.theme['card_hover']};
            }}
            QToolButton:checked {{
                background-color: {self.theme['accent']}40;
            }}
            QComboBox {{
                background-color: {self.theme['card']};
                color: {self.theme['text']};
                border: 1px solid {self.theme['border']};
                padding: 5px;
                border-radius: 4px;
                min-width: 120px;
            }}
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 15px;
                border-left: 1px solid {self.theme['border']};
            }}
        """)
        
        # Update labels
        for label in self.findChildren(QLabel):
            if label == self.empty_label:
                label.setStyleSheet(f"""
                    color: {self.theme['text_tertiary']};
                    font-size: 16px;
                    padding: 40px;
                """)
            elif label == self.results_label:
                label.setStyleSheet(f"color: {self.theme['text_secondary']};")
            else:
                label.setStyleSheet(f"color: {self.theme['text_secondary']};")
        
        # Refresh view to update model cards
        self.refresh_view()
