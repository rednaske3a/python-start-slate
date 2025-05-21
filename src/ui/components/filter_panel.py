
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QLineEdit, QComboBox, QCheckBox, QGroupBox, QScrollArea
)
from PySide6.QtCore import Qt, Signal
from typing import Dict, List, Optional

class FilterPanel(QWidget):
    """Panel with filters for the gallery"""
    
    filter_changed = Signal(dict)
    
    def __init__(self, theme: Dict, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.filters = {}
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI components"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setStyleSheet(f"""
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
        container = QWidget()
        scroll.setWidget(container)
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(15, 15, 15, 15)
        
        # Title
        title = QLabel("Filter Models")
        title.setStyleSheet(f"""
            font-size: 16px;
            font-weight: bold;
            color: {self.theme['text']};
            margin-bottom: 10px;
        """)
        container_layout.addWidget(title)
        
        # Search box
        search_label = QLabel("Search")
        search_label.setStyleSheet(f"color: {self.theme['text']};")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search models...")
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {self.theme['input_bg']};
                color: {self.theme['text']};
                border: 1px solid {self.theme['border']};
                border-radius: 4px;
                padding: 6px;
            }}
            QLineEdit:focus {{
                border: 1px solid {self.theme['accent']};
            }}
        """)
        self.search_input.textChanged.connect(self.update_filters)
        container_layout.addWidget(search_label)
        container_layout.addWidget(self.search_input)
        container_layout.addSpacing(15)
        
        # Model type filter
        type_label = QLabel("Model Type")
        type_label.setStyleSheet(f"color: {self.theme['text']};")
        self.type_combo = QComboBox()
        self.type_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {self.theme['input_bg']};
                color: {self.theme['text']};
                border: 1px solid {self.theme['border']};
                border-radius: 4px;
                padding: 5px;
                padding-left: 10px;
                min-height: 24px;
            }}
            QComboBox::drop-down {{
                border: none;
                width: 24px;
            }}
            QComboBox::down-arrow {{
                image: url(resources/icons/chevron-down.png);
                width: 16px;
                height: 16px;
            }}
            QComboBox:focus {{
                border: 1px solid {self.theme['accent']};
            }}
            QComboBox QAbstractItemView {{
                background-color: {self.theme['input_bg']};
                color: {self.theme['text']};
                border: 1px solid {self.theme['border']};
                selection-background-color: {self.theme['accent']};
                selection-color: white;
            }}
        """)
        self.type_combo.addItem("All Types", "")
        self.type_combo.currentIndexChanged.connect(self.update_filters)
        container_layout.addWidget(type_label)
        container_layout.addWidget(self.type_combo)
        container_layout.addSpacing(15)
        
        # Base model filter
        base_label = QLabel("Base Model")
        base_label.setStyleSheet(f"color: {self.theme['text']};")
        self.base_combo = QComboBox()
        self.base_combo.setStyleSheet(self.type_combo.styleSheet())
        self.base_combo.addItem("All Base Models", "")
        self.base_combo.currentIndexChanged.connect(self.update_filters)
        container_layout.addWidget(base_label)
        container_layout.addWidget(self.base_combo)
        container_layout.addSpacing(15)
        
        # Checkboxes group
        options_group = QFrame()
        options_group.setStyleSheet(f"""
            QFrame {{
                background-color: {self.theme['card']};
                border-radius: 4px;
                padding: 5px;
            }}
        """)
        options_layout = QVBoxLayout(options_group)
        options_layout.setContentsMargins(10, 10, 10, 10)
        options_layout.setSpacing(10)
        
        # NSFW filter
        self.nsfw_check = QCheckBox("Show NSFW Models")
        self.nsfw_check.setStyleSheet(f"""
            QCheckBox {{
                color: {self.theme['text']};
                spacing: 8px;
            }}
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
                border-radius: 2px;
                border: 1px solid {self.theme['border']};
            }}
            QCheckBox::indicator:unchecked {{
                background-color: {self.theme['input_bg']};
            }}
            QCheckBox::indicator:checked {{
                background-color: {self.theme['accent']};
                border: 1px solid {self.theme['accent']};
            }}
        """)
        self.nsfw_check.stateChanged.connect(self.update_filters)
        options_layout.addWidget(self.nsfw_check)
        
        # Favorites filter
        self.favorites_check = QCheckBox("Show Only Favorites")
        self.favorites_check.setStyleSheet(self.nsfw_check.styleSheet())
        self.favorites_check.stateChanged.connect(self.update_filters)
        options_layout.addWidget(self.favorites_check)
        
        container_layout.addWidget(options_group)
        container_layout.addSpacing(15)
        
        # Reset button
        self.reset_button = QPushButton("Reset Filters")
        self.reset_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.theme['secondary']};
                color: {self.theme['text']};
                border: 1px solid {self.theme['border']};
                padding: 8px;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {self.theme['card_hover']};
                border-color: {self.theme['accent']};
            }}
        """)
        self.reset_button.clicked.connect(self.reset_filters)
        container_layout.addWidget(self.reset_button)
        
        # Add stretch to bottom
        container_layout.addStretch(1)
        
        # Add scroll area to layout
        layout.addWidget(scroll)
    
    def update_model_types(self, types: List[str]):
        """Update available model types"""
        current = self.type_combo.currentText()
        
        # Clear and re-add all option
        self.type_combo.clear()
        self.type_combo.addItem("All Types", "")
        
        # Add model types
        for model_type in sorted(types):
            self.type_combo.addItem(model_type, model_type)
        
        # Try to restore selection
        index = self.type_combo.findText(current)
        if index > 0:
            self.type_combo.setCurrentIndex(index)
    
    def update_base_models(self, base_models: List[str]):
        """Update available base models"""
        current = self.base_combo.currentText()
        
        # Clear and re-add all option
        self.base_combo.clear()
        self.base_combo.addItem("All Base Models", "")
        
        # Add base models
        for base in sorted(base_models):
            self.base_combo.addItem(base, base)
        
        # Try to restore selection
        index = self.base_combo.findText(current)
        if index > 0:
            self.base_combo.setCurrentIndex(index)
    
    def update_filters(self):
        """Update filters and emit signal"""
        filters = {}
        
        # Get search text
        search_text = self.search_input.text().strip()
        if search_text:
            filters["search"] = search_text
        
        # Get model type
        type_index = self.type_combo.currentIndex()
        if type_index > 0:
            filters["type"] = self.type_combo.itemData(type_index)
        
        # Get base model
        base_index = self.base_combo.currentIndex()
        if base_index > 0:
            filters["base_model"] = self.base_combo.itemData(base_index)
        
        # Get NSFW filter
        filters["nsfw"] = self.nsfw_check.isChecked()
        
        # Get favorites filter
        if self.favorites_check.isChecked():
            filters["favorite"] = True
        
        self.filters = filters
        self.filter_changed.emit(filters)
    
    def reset_filters(self):
        """Reset all filters to defaults"""
        self.search_input.clear()
        self.type_combo.setCurrentIndex(0)
        self.base_combo.setCurrentIndex(0)
        self.nsfw_check.setChecked(False)
        self.favorites_check.setChecked(False)
        
        self.update_filters()
    
    def get_filters(self):
        """Get current filters"""
        return self.filters
    
    def set_theme(self, theme):
        """Update theme"""
        self.theme = theme
        
        # Update title style
        title = self.findChild(QLabel, "", Qt.FindChildrenRecursively)
        if title and title.text() == "Filter Models":
            title.setStyleSheet(f"""
                font-size: 16px;
                font-weight: bold;
                color: {self.theme['text']};
                margin-bottom: 10px;
            """)
        
        # Update search input style
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {self.theme['input_bg']};
                color: {self.theme['text']};
                border: 1px solid {self.theme['border']};
                border-radius: 4px;
                padding: 6px;
            }}
            QLineEdit:focus {{
                border: 1px solid {self.theme['accent']};
            }}
        """)
        
        # Update combo boxes style
        combo_style = f"""
            QComboBox {{
                background-color: {self.theme['input_bg']};
                color: {self.theme['text']};
                border: 1px solid {self.theme['border']};
                border-radius: 4px;
                padding: 5px;
                padding-left: 10px;
                min-height: 24px;
            }}
            QComboBox::drop-down {{
                border: none;
                width: 24px;
            }}
            QComboBox::down-arrow {{
                image: url(resources/icons/chevron-down.png);
                width: 16px;
                height: 16px;
            }}
            QComboBox:focus {{
                border: 1px solid {self.theme['accent']};
            }}
            QComboBox QAbstractItemView {{
                background-color: {self.theme['input_bg']};
                color: {self.theme['text']};
                border: 1px solid {self.theme['border']};
                selection-background-color: {self.theme['accent']};
                selection-color: white;
            }}
        """
        self.type_combo.setStyleSheet(combo_style)
        self.base_combo.setStyleSheet(combo_style)
        
        # Update checkboxes style
        checkbox_style = f"""
            QCheckBox {{
                color: {self.theme['text']};
                spacing: 8px;
            }}
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
                border-radius: 2px;
                border: 1px solid {self.theme['border']};
            }}
            QCheckBox::indicator:unchecked {{
                background-color: {self.theme['input_bg']};
            }}
            QCheckBox::indicator:checked {{
                background-color: {self.theme['accent']};
                border: 1px solid {self.theme['accent']};
            }}
        """
        self.nsfw_check.setStyleSheet(checkbox_style)
        self.favorites_check.setStyleSheet(checkbox_style)
        
        # Update reset button style
        self.reset_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.theme['secondary']};
                color: {self.theme['text']};
                border: 1px solid {self.theme['border']};
                padding: 8px;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {self.theme['card_hover']};
                border-color: {self.theme['accent']};
            }}
        """)
        
        # Update options group style
        for frame in self.findChildren(QFrame):
            if frame.layout() and frame.layout().count() > 0:
                if isinstance(frame.layout().itemAt(0).widget(), QCheckBox):
                    frame.setStyleSheet(f"""
                        QFrame {{
                            background-color: {self.theme['card']};
                            border-radius: 4px;
                            padding: 5px;
                        }}
                    """)
        
        # Update scroll area style
        scroll = self.findChild(QScrollArea)
        if scroll:
            scroll.setStyleSheet(f"""
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
        
        # Update label styles
        for label in self.findChildren(QLabel):
            if label.text() != "Filter Models":
                label.setStyleSheet(f"color: {self.theme['text']};")
