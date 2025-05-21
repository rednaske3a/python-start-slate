from typing import Dict

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QCheckBox, QComboBox, QGroupBox
)
from PySide6.QtCore import Signal

from src.constants.constants import BASE_MODELS, MODEL_TYPES

class FilterPanel(QWidget):
    """Panel for filtering models in the gallery"""
    
    filter_changed = Signal(dict)
    
    def __init__(self, theme: Dict, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.filters = {
            "type": "all",
            "base_model": "all",
            "favorite": False,
            "nsfw": "all",
            "search": "",
            "sort": "date"
        }
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI components"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Title
        title = QLabel("Filter Models")
        title.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {self.theme['text']};")
        layout.addWidget(title)
        
        # Search
        search_layout = QHBoxLayout()
        search_label = QLabel("Search:")
        search_label.setStyleSheet(f"color: {self.theme['text']};")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by name, tag, or creator...")
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {self.theme['input_bg']};
                color: {self.theme['text']};
                border: 1px solid {self.theme['input_border']};
                border-radius: 4px;
                padding: 4px 8px;
            }}
        """)
        self.search_input.textChanged.connect(self.update_filters)
        
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)
        
        # Model Type
        type_group = self.create_styled_group_box("Model Type")
        type_layout = QVBoxLayout(type_group)
        
        self.type_combo = QComboBox()
        self.type_combo.addItem("All Types", "all")
        for model_type in MODEL_TYPES.keys():
            self.type_combo.addItem(model_type, model_type)
        
        self.type_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {self.theme['input_bg']};
                color: {self.theme['text']};
                border: 1px solid {self.theme['input_border']};
                border-radius: 4px;
                padding: 4px 8px;
            }}
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 15px;
                border-left-width: 1px;
                border-left-color: {self.theme['border']};
                border-left-style: solid;
            }}
        """)
        self.type_combo.currentIndexChanged.connect(self.update_filters)
        
        type_layout.addWidget(self.type_combo)
        layout.addWidget(type_group)
        
        # Base Model
        base_group = self.create_styled_group_box("Base Model")
        base_layout = QVBoxLayout(base_group)
        
        self.base_combo = QComboBox()
        self.base_combo.addItem("All Base Models", "all")
        for base_model in BASE_MODELS:
            self.base_combo.addItem(base_model, base_model)
        
        self.base_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {self.theme['input_bg']};
                color: {self.theme['text']};
                border: 1px solid {self.theme['input_border']};
                border-radius: 4px;
                padding: 4px 8px;
            }}
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 15px;
                border-left-width: 1px;
                border-left-color: {self.theme['border']};
                border-left-style: solid;
            }}
        """)
        self.base_combo.currentIndexChanged.connect(self.update_filters)
        
        base_layout.addWidget(self.base_combo)
        layout.addWidget(base_group)
        
        # Sort By
        sort_group = self.create_styled_group_box("Sort By")
        sort_layout = QVBoxLayout(sort_group)
        
        self.sort_combo = QComboBox()
        self.sort_combo.addItem("Date (Newest First)", "date")
        self.sort_combo.addItem("Name (A-Z)", "name")
        self.sort_combo.addItem("Size (Largest First)", "size")
        self.sort_combo.addItem("Type", "type")
        
        self.sort_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {self.theme['input_bg']};
                color: {self.theme['text']};
                border: 1px solid {self.theme['input_border']};
                border-radius: 4px;
                padding: 4px 8px;
            }}
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 15px;
                border-left-width: 1px;
                border-left-color: {self.theme['border']};
                border-left-style: solid;
            }}
        """)
        self.sort_combo.currentIndexChanged.connect(self.update_filters)
        
        sort_layout.addWidget(self.sort_combo)
        layout.addWidget(sort_group)
        
        # Additional Filters
        filter_group = self.create_styled_group_box("Additional Filters")
        filter_layout = QVBoxLayout(filter_group)
        
        # Favorites only
        self.favorites_check = QCheckBox("Favorites Only")
        self.favorites_check.setStyleSheet(f"color: {self.theme['text']};")
        self.favorites_check.stateChanged.connect(self.update_filters)
        
        # NSFW filter
        nsfw_layout = QHBoxLayout()
        nsfw_label = QLabel("NSFW Content:")
        nsfw_label.setStyleSheet(f"color: {self.theme['text']};")
        
        self.nsfw_combo = QComboBox()
        self.nsfw_combo.addItem("Show All", "all")
        self.nsfw_combo.addItem("Hide NSFW", "hide")
        self.nsfw_combo.addItem("NSFW Only", "only")
        
        self.nsfw_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {self.theme['input_bg']};
                color: {self.theme['text']};
                border: 1px solid {self.theme['input_border']};
                border-radius: 4px;
                padding: 4px 8px;
            }}
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 15px;
                border-left-width: 1px;
                border-left-color: {self.theme['border']};
                border-left-style: solid;
            }}
        """)
        self.nsfw_combo.currentIndexChanged.connect(self.update_filters)
        
        nsfw_layout.addWidget(nsfw_label)
        nsfw_layout.addWidget(self.nsfw_combo)
        
        filter_layout.addWidget(self.favorites_check)
        filter_layout.addLayout(nsfw_layout)
        layout.addWidget(filter_group)
        
        # Reset button
        reset_btn = QPushButton("Reset Filters")
        reset_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.theme['accent']};
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px;
            }}
            QPushButton:hover {{
                background-color: {self.theme['accent_hover']};
            }}
        """)
        reset_btn.clicked.connect(self.reset_filters)
        layout.addWidget(reset_btn)
        
        layout.addStretch()
    
    def create_styled_group_box(self, title):
        """Create a styled group box"""
        group = QGroupBox(title)
        group.setStyleSheet(f"""
            QGroupBox {{
                border: 1px solid {self.theme['border']};
                border-radius: 8px;
                margin-top: 1ex;
                font-weight: bold;
                color: {self.theme['text']};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }}
        """)
        return group
    
    def set_theme(self, theme):
        """Update the theme"""
        self.theme = theme
        
        # Update UI styles
        for child in self.findChildren(QLabel):
            child.setStyleSheet(f"color: {self.theme['text']};")
            if "Filter Models" in child.text():
                child.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {self.theme['text']};")
        
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {self.theme['input_bg']};
                color: {self.theme['text']};
                border: 1px solid {self.theme['input_border']};
                border-radius: 4px;
                padding: 4px 8px;
            }}
        """)
        
        combo_style = f"""
            QComboBox {{
                background-color: {self.theme['input_bg']};
                color: {self.theme['text']};
                border: 1px solid {self.theme['input_border']};
                border-radius: 4px;
                padding: 4px 8px;
            }}
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 15px;
                border-left-width: 1px;
                border-left-color: {self.theme['border']};
                border-left-style: solid;
            }}
        """
        
        self.type_combo.setStyleSheet(combo_style)
        self.base_combo.setStyleSheet(combo_style)
        self.sort_combo.setStyleSheet(combo_style)
        self.nsfw_combo.setStyleSheet(combo_style)
        
        self.favorites_check.setStyleSheet(f"color: {self.theme['text']};")
        
        # Update reset button
        for child in self.findChildren(QPushButton):
            child.setStyleSheet(f"""
                QPushButton {{
                    background-color: {self.theme['accent']};
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 8px;
                }}
                QPushButton:hover {{
                    background-color: {self.theme['accent_hover']};
                }}
            """)
        
        # Update group boxes
        for child in self.findChildren(QGroupBox):
            child.setStyleSheet(f"""
                QGroupBox {{
                    border: 1px solid {self.theme['border']};
                    border-radius: 8px;
                    margin-top: 1ex;
                    font-weight: bold;
                    color: {self.theme['text']};
                }}
                QGroupBox::title {{
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 5px;
                }}
            """)
    
    def update_filters(self):
        """Update filters based on UI state"""
        self.filters["type"] = self.type_combo.currentData()
        self.filters["base_model"] = self.base_combo.currentData()
        self.filters["favorite"] = self.favorites_check.isChecked()
        self.filters["nsfw"] = self.nsfw_combo.currentData()
        self.filters["search"] = self.search_input.text()
        self.filters["sort"] = self.sort_combo.currentData()
        
        self.filter_changed.emit(self.filters)
    
    def reset_filters(self):
        """Reset all filters to default values"""
        self.type_combo.setCurrentIndex(0)
        self.base_combo.setCurrentIndex(0)
        self.favorites_check.setChecked(False)
        self.nsfw_combo.setCurrentIndex(0)
        self.search_input.clear()
        self.sort_combo.setCurrentIndex(0)
        
        self.update_filters()
    
    def get_filters(self):
        """Get current filters"""
        return self.filters