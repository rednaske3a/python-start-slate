from typing import Dict, List, Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFormLayout, QGroupBox, QSpinBox, QCheckBox, QComboBox,
    QLineEdit, QFileDialog, QListWidget, QStackedWidget,
    QPlainTextEdit, QButtonGroup, QRadioButton
)
from PySide6.QtCore import Signal, Qt

from src.constants.constants import APP_THEMES, BASE_MODELS

class SettingsTab(QWidget):
    """Settings tab for configuring the application"""
    
    settings_saved = Signal()
    theme_changed = Signal(str)
    
    def __init__(self, theme: Dict, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.parent = parent
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI components"""
        layout = QHBoxLayout(self)
        
        # Left panel - settings categories
        left_panel = QWidget()
        left_panel.setMinimumWidth(200)
        left_panel.setMaximumWidth(250)
        left_layout = QVBoxLayout(left_panel)
        
        # Settings categories list
        self.settings_list = QListWidget()
        self.settings_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {self.theme['card']};
                color: {self.theme['text']};
                border: 1px solid {self.theme['border']};
                border-radius: 4px;
            }}
            QListWidget::item {{
                padding: 8px;
                border-bottom: 1px solid {self.theme['border']};
            }}
            QListWidget::item:selected {{
                background-color: {self.theme['accent']};
                color: white;
            }}
            QListWidget::item:hover {{
                background-color: {self.theme['card_hover']};
            }}
        """)
        
        # Add settings categories
        self.settings_list.addItem("General Settings")
        self.settings_list.addItem("Download Settings")
        self.settings_list.addItem("Gallery Settings")
        self.settings_list.addItem("Appearance")
        self.settings_list.addItem("Advanced")
        
        self.settings_list.currentRowChanged.connect(self.change_settings_page)
        
        left_layout.addWidget(self.settings_list)
        
        # Right panel - settings content
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # Settings stack
        self.settings_stack = QStackedWidget()
        
        self.create_general_settings_page()
        self.create_download_settings_page()
        self.create_gallery_settings_page()
        self.create_appearance_settings_page()
        self.create_advanced_settings_page()
        
        right_layout.addWidget(self.settings_stack)
        
        # Save button
        save_btn = QPushButton("Save Settings")
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.theme['accent']};
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {self.theme['accent_hover']};
            }}
            QPushButton:pressed {{
                background-color: {self.theme['accent_pressed']};
            }}
        """)
        save_btn.clicked.connect(self.save_settings)
        
        right_layout.addWidget(save_btn)
        
        # Add panels to layout
        layout.addWidget(left_panel)
        layout.addWidget(right_panel, 1)
        
        # Select first item in settings list
        self.settings_list.setCurrentRow(0)
    
    def set_theme(self, theme):
        """Update the theme"""
        self.theme = theme
        
        # Update list widget
        self.settings_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {self.theme['card']};
                color: {self.theme['text']};
                border: 1px solid {self.theme['border']};
                border-radius: 4px;
            }}
            QListWidget::item {{
                padding: 8px;
                border-bottom: 1px solid {self.theme['border']};
            }}
            QListWidget::item:selected {{
                background-color: {self.theme['accent']};
                color: white;
            }}
            QListWidget::item:hover {{
                background-color: {self.theme['card_hover']};
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
        
        # Update labels
        for child in self.findChildren(QLabel):
            child.setStyleSheet(f"color: {self.theme['text']};")
        
        # Update checkboxes
        for child in self.findChildren(QCheckBox):
            child.setStyleSheet(f"color: {self.theme['text']};")
        
        # Update radio buttons
        for child in self.findChildren(QRadioButton):
            child.setStyleSheet(f"color: {self.theme['text']};")
        
        # Update line edits
        for child in self.findChildren(QLineEdit):
            child.setStyleSheet(f"""
                QLineEdit {{
                    background-color: {self.theme['input_bg']};
                    color: {self.theme['text']};
                    border: 1px solid {self.theme['input_border']};
                    border-radius: 4px;
                    padding: 4px 8px;
                }}
            """)
        
        # Update plain text edits
        for child in self.findChildren(QPlainTextEdit):
            child.setStyleSheet(f"""
                QPlainTextEdit {{
                    background-color: {self.theme['input_bg']};
                    color: {self.theme['text']};
                    border: 1px solid {self.theme['input_border']};
                    border-radius: 4px;
                    padding: 4px;
                }}
            """)
        
        # Update spin boxes
        for child in self.findChildren(QSpinBox):
            child.setStyleSheet(f"""
                QSpinBox {{
                    background-color: {self.theme['input_bg']};
                    color: {self.theme['text']};
                    border: 1px solid {self.theme['input_border']};
                    border-radius: 4px;
                    padding: 4px;
                }}
            """)
        
        # Update combo boxes
        for child in self.findChildren(QComboBox):
            child.setStyleSheet(f"""
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
        
        # Update buttons
        for child in self.findChildren(QPushButton):
            if "Save Settings" in child.text():
                child.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {self.theme['accent']};
                        color: white;
                        border: none;
                        border-radius: 4px;
                        padding: 8px;
                        font-weight: bold;
                    }}
                    QPushButton:hover {{
                        background-color: {self.theme['accent_hover']};
                    }}
                    QPushButton:pressed {{
                        background-color: {self.theme['accent_pressed']};
                    }}
                """)
            elif "Browse" in child.text():
                child.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {self.theme['text_tertiary']};
                        color: white;
                        border: none;
                        border-radius: 4px;
                        padding: 4px 8px;
                    }}
                    QPushButton:hover {{
                        background-color: {self.theme['text_secondary']};
                    }}
                """)
            elif "Filters" in child.text():
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
            elif "Database" in child.text():
                child.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {self.theme['danger']};
                        color: white;
                        border: none;
                        border-radius: 4px;
                        padding: 8px;
                    }}
                    QPushButton:hover {{
                        background-color: {self.theme['danger_hover']};
                    }}
                """)
            else:
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
        
        # Update theme preview
        if hasattr(self, 'theme_preview'):
            self.update_theme_preview()
    
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
    
    def change_settings_page(self, index):
        """Change the settings page based on list selection"""
        self.settings_stack.setCurrentIndex(index)
    
    def create_general_settings_page(self):
        """Create general settings page"""
        general_page = QWidget()
        general_layout = QVBoxLayout(general_page)
        
        # ComfyUI Path
        comfy_group = self.create_styled_group_box("ComfyUI Path")
        comfy_layout = QVBoxLayout(comfy_group)
        
        comfy_path_layout = QHBoxLayout()
        self.comfy_path_input = QLineEdit()
        if self.parent and hasattr(self.parent, "config"):
            self.comfy_path_input.setText(self.parent.config.get("comfy_path", ""))
        self.comfy_path_input.setPlaceholderText("Path to your ComfyUI directory...")
        self.comfy_path_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {self.theme['input_bg']};
                color: {self.theme['text']};
                border: 1px solid {self.theme['input_border']};
                border-radius: 4px;
                padding: 4px 8px;
            }}
        """)
        
        self.comfy_path_btn = QPushButton("Browse")
        self.comfy_path_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.theme['text_tertiary']};
                color: white;
                border: none;
                border-radius: 4px;
                padding: 4px 8px;
            }}
            QPushButton:hover {{
                background-color: {self.theme['text_secondary']};
            }}
        """)
        self.comfy_path_btn.clicked.connect(self.browse_comfy_path)
        
        comfy_path_layout.addWidget(self.comfy_path_input)
        comfy_path_layout.addWidget(self.comfy_path_btn)
        
        comfy_layout.addLayout(comfy_path_layout)
        
        # API Key
        api_group = self.create_styled_group_box("Civitai API Key")
        api_layout = QVBoxLayout(api_group)
        
        api_label = QLabel("API Key (optional):")
        api_label.setStyleSheet(f"color: {self.theme['text']};")
        
        self.api_key_input = QLineEdit()
        if self.parent and hasattr(self.parent, "config"):
            self.api_key_input.setText(self.parent.config.get("api_key", ""))
        self.api_key_input.setPlaceholderText("Your Civitai API Key (optional)")
        self.api_key_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {self.theme['input_bg']};
                color: {self.theme['text']};
                border: 1px solid {self.theme['input_border']};
                border-radius: 4px;
                padding: 4px 8px;
            }}
        """)
        
        api_layout.addWidget(api_label)
        api_layout.addWidget(self.api_key_input)
        
        general_layout.addWidget(comfy_group)
        general_layout.addWidget(api_group)
        general_layout.addStretch()
        
        self.settings_stack.addWidget(general_page)
    
    def create_download_settings_page(self):
        """Create download settings page"""
        download_page = QWidget()
        download_layout = QVBoxLayout(download_page)
        
        # Image settings
        image_group = self.create_styled_group_box("Image Settings")
        image_layout = QFormLayout(image_group)
        
        # Top Image Count
        self.top_image_count_input = QSpinBox()
        self.top_image_count_input.setRange(10, 2000)
        if self.parent and hasattr(self.parent, "config"):
            self.top_image_count_input.setValue(self.parent.config.get("top_image_count", 500))
        self.top_image_count_input.setStyleSheet(f"""
            QSpinBox {{
                background-color: {self.theme['input_bg']};
                color: {self.theme['text']};
                border: 1px solid {self.theme['input_border']};
                border-radius: 4px;
                padding: 4px;
            }}
        """)
        
        # Download Threads
        self.download_threads_input = QSpinBox()
        self.download_threads_input.setRange(1, 10)
        if self.parent and hasattr(self.parent, "config"):
            self.download_threads_input.setValue(self.parent.config.get("download_threads", 5))
        self.download_threads_input.setStyleSheet(f"""
            QSpinBox {{
                background-color: {self.theme['input_bg']};
                color: {self.theme['text']};
                border: 1px solid {self.theme['input_border']};
                border-radius: 4px;
                padding: 4px;
            }}
        """)
        
        # Checkboxes
        self.download_images_checkbox = QCheckBox("Download Images")
        if self.parent and hasattr(self.parent, "config"):
            self.download_images_checkbox.setChecked(self.parent.config.get("download_images", True))
        self.download_images_checkbox.setStyleSheet(f"color: {self.theme['text']};")
        
        self.download_model_checkbox = QCheckBox("Download Model")
        if self.parent and hasattr(self.parent, "config"):
            self.download_model_checkbox.setChecked(self.parent.config.get("download_model", True))
        self.download_model_checkbox.setStyleSheet(f"color: {self.theme['text']};")
        
        self.create_html_checkbox = QCheckBox("Create HTML Summary")
        if self.parent and hasattr(self.parent, "config"):
            self.create_html_checkbox.setChecked(self.parent.config.get("create_html", False))
        self.create_html_checkbox.setStyleSheet(f"color: {self.theme['text']};")
        
        self.download_nsfw_checkbox = QCheckBox("Download NSFW Images")
        if self.parent and hasattr(self.parent, "config"):
            self.download_nsfw_checkbox.setChecked(self.parent.config.get("download_nsfw", True))
        self.download_nsfw_checkbox.setStyleSheet(f"color: {self.theme['text']};")
        
        self.auto_organize_checkbox = QCheckBox("Auto Organize")
        if self.parent and hasattr(self.parent, "config"):
            self.auto_organize_checkbox.setChecked(self.parent.config.get("auto_organize", True))
        self.auto_organize_checkbox.setStyleSheet(f"color: {self.theme['text']};")
        
        self.auto_open_html_checkbox = QCheckBox("Auto Open HTML")
        if self.parent and hasattr(self.parent, "config"):
            self.auto_open_html_checkbox.setChecked(self.parent.config.get("auto_open_html", False))
        self.auto_open_html_checkbox.setStyleSheet(f"color: {self.theme['text']};")
        
        image_layout.addRow("Max Image Count:", self.top_image_count_input)
        image_layout.addRow("Download Threads:", self.download_threads_input)
        image_layout.addRow(self.download_images_checkbox)
        image_layout.addRow(self.download_model_checkbox)
        image_layout.addRow(self.create_html_checkbox)
        image_layout.addRow(self.download_nsfw_checkbox)
        image_layout.addRow(self.auto_organize_checkbox)
        image_layout.addRow(self.auto_open_html_checkbox)
        
        download_layout.addWidget(image_group)
        download_layout.addStretch()
        
        self.settings_stack.addWidget(download_page)
    
    def create_gallery_settings_page(self):
        """Create gallery settings page"""
        gallery_page = QWidget()
        gallery_layout = QVBoxLayout(gallery_page)
        
        # Gallery display settings
        gallery_group = self.create_styled_group_box("Gallery Display")
        gallery_settings_layout = QFormLayout(gallery_group)
        
        # Gallery Columns
        self.gallery_columns_input = QSpinBox()
        self.gallery_columns_input.setRange(2, 8)
        if self.parent and hasattr(self.parent, "config"):
            self.gallery_columns_input.setValue(self.parent.config.get("gallery_columns", 4))
        self.gallery_columns_input.setStyleSheet(f"""
            QSpinBox {{
                background-color: {self.theme['input_bg']};
                color: {self.theme['text']};
                border: 1px solid {self.theme['input_border']};
                border-radius: 4px;
                padding: 4px;
            }}
        """)
        
        # Default sort
        self.default_sort_combo = QComboBox()
        self.default_sort_combo.addItem("Date (Newest First)", "date")
        self.default_sort_combo.addItem("Name (A-Z)", "name")
        self.default_sort_combo.addItem("Size (Largest First)", "size")
        self.default_sort_combo.addItem("Type", "type")
        
        # Set current index based on config
        if self.parent and hasattr(self.parent, "config"):
            default_sort = self.parent.config.get("default_sort", "date")
            for i in range(self.default_sort_combo.count()):
                if self.default_sort_combo.itemData(i) == default_sort:
                    self.default_sort_combo.setCurrentIndex(i)
                    break
        
        self.default_sort_combo.setStyleSheet(f"""
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
        
        gallery_settings_layout.addRow("Gallery Columns:", self.gallery_columns_input)
        gallery_settings_layout.addRow("Default Sort:", self.default_sort_combo)
        
        gallery_layout.addWidget(gallery_group)
        
        # Favorite tags
        favorites_group = self.create_styled_group_box("Favorite Tags")
        favorites_layout = QVBoxLayout(favorites_group)
        
        favorites_label = QLabel("Add your favorite tags for quick filtering (one per line):")
        favorites_label.setStyleSheet(f"color: {self.theme['text']};")
        
        self.favorite_tags_input = QPlainTextEdit()
        if self.parent and hasattr(self.parent, "config"):
            self.favorite_tags_input.setPlainText("\n".join(self.parent.config.get("favorite_tags", [])))
        self.favorite_tags_input.setStyleSheet(f"""
            QPlainTextEdit {{
                background-color: {self.theme['input_bg']};
                color: {self.theme['text']};
                border: 1px solid {self.theme['input_border']};
                border-radius: 4px;
                padding: 4px;
            }}
        """)
        
        favorites_layout.addWidget(favorites_label)
        favorites_layout.addWidget(self.favorite_tags_input)
        
        gallery_layout.addWidget(favorites_group)
        gallery_layout.addStretch()
        
        self.settings_stack.addWidget(gallery_page)
    
    def create_appearance_settings_page(self):
        """Create appearance settings page"""
        appearance_page = QWidget()
        appearance_layout = QVBoxLayout(appearance_page)
        
        # Theme selection
        theme_group = self.create_styled_group_box("Application Theme")
        theme_layout = QVBoxLayout(theme_group)
        
        self.theme_buttons = QButtonGroup(self)
        
        current_theme_id = "dark"
        if self.parent and hasattr(self.parent, "current_theme_id"):
            current_theme_id = self.parent.current_theme_id
        
        for theme_id, theme_data in APP_THEMES.items():
            radio = QRadioButton(theme_data["name"])
            radio.setStyleSheet(f"color: {self.theme['text']};")
            if theme_id == current_theme_id:
                radio.setChecked(True)
            radio.setProperty("theme_id", theme_id)
            self.theme_buttons.addButton(radio)
            theme_layout.addWidget(radio)
        
        self.theme_buttons.buttonClicked.connect(self.on_theme_changed)
        
        appearance_layout.addWidget(theme_group)
        
        # Theme preview
        preview_group = self.create_styled_group_box("Theme Preview")
        preview_layout = QVBoxLayout(preview_group)
        
        self.theme_preview = QWidget()
        self.theme_preview.setMinimumHeight(150)
        self.update_theme_preview()
        
        preview_layout.addWidget(self.theme_preview)
        
        appearance_layout.addWidget(preview_group)
        appearance_layout.addStretch()
        
        self.settings_stack.addWidget(appearance_page)
    
    def update_theme_preview(self):
        """Update the theme preview"""
        current_theme_id = "dark"
        if self.parent and hasattr(self.parent, "current_theme_id"):
            current_theme_id = self.parent.current_theme_id
        theme = APP_THEMES.get(current_theme_id, APP_THEMES["dark"])
        
        # Create preview layout
        preview_layout = QVBoxLayout(self.theme_preview)
        preview_layout.setContentsMargins(10, 10, 10, 10)
        
        # Clear existing widgets
        while preview_layout.count():
            item = preview_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Set background color
        self.theme_preview.setStyleSheet(f"background-color: {theme['background']}; border-radius: 8px;")
        
        # Add sample elements
        title = QLabel("Sample Title")
        title.setStyleSheet(f"color: {theme['text']}; font-weight: bold; font-size: 14px;")
        
        text = QLabel("This is how text will appear with this theme.")
        text.setStyleSheet(f"color: {theme['text_secondary']};")
        
        button = QPushButton("Sample Button")
        button.setStyleSheet(f"""
            QPushButton {{
                background-color: {theme['accent']};
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px;
            }}
        """)
        
        input_field = QLineEdit("Sample input")
        input_field.setStyleSheet(f"""
            QLineEdit {{
                background-color: {theme['input_bg']};
                color: {theme['text']};
                border: 1px solid {theme['input_border']};
                border-radius: 4px;
                padding: 4px;
            }}
        """)
        
        preview_layout.addWidget(title)
        preview_layout.addWidget(text)
        preview_layout.addWidget(input_field)
        preview_layout.addWidget(button)
        preview_layout.addStretch()
    
    def create_advanced_settings_page(self):
        """Create advanced settings page"""
        advanced_page = QWidget()
        advanced_layout = QVBoxLayout(advanced_page)
        
        # Database management
        db_group = self.create_styled_group_box("Database Management")
        db_layout = QVBoxLayout(db_group)
        
        db_buttons_layout = QHBoxLayout()
        
        rescan_btn = QPushButton("Rescan Models")
        rescan_btn.setStyleSheet(f"""
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
        rescan_btn.clicked.connect(self.rescan_models)
        
        clear_db_btn = QPushButton("Clear Database")
        clear_db_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.theme['danger']};
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px;
            }}
            QPushButton:hover {{
                background-color: {self.theme['danger_hover']};
            }}
        """)
        clear_db_btn.clicked.connect(self.clear_database)
        
        db_buttons_layout.addWidget(rescan_btn)
        db_buttons_layout.addWidget(clear_db_btn)
        
        db_layout.addLayout(db_buttons_layout)
        
        # Logging
        log_group = self.create_styled_group_box("Logging")
        log_layout = QFormLayout(log_group)
        
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItem("Error", "error")
        self.log_level_combo.addItem("Warning", "warning")
        self.log_level_combo.addItem("Info", "info")
        self.log_level_combo.addItem("Debug", "debug")
        
        # Set current index based on config
        if self.parent and hasattr(self.parent, "config"):
            log_level = self.parent.config.get("log_level", "info")
            for i in range(self.log_level_combo.count()):
                if self.log_level_combo.itemData(i) == log_level:
                    self.log_level_combo.setCurrentIndex(i)
                    break
        
        self.log_level_combo.setStyleSheet(f"""
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
        
        # Auto check updates
        self.auto_check_updates_checkbox = QCheckBox("Automatically check for updates")
        if self.parent and hasattr(self.parent, "config"):
            self.auto_check_updates_checkbox.setChecked(self.parent.config.get("auto_check_updates", True))
        self.auto_check_updates_checkbox.setStyleSheet(f"color: {self.theme['text']};")
        
        log_layout.addRow("Log Level:", self.log_level_combo)
        log_layout.addRow(self.auto_check_updates_checkbox)
        
        advanced_layout.addWidget(db_group)
        advanced_layout.addWidget(log_group)
        advanced_layout.addStretch()
        
        self.settings_stack.addWidget(advanced_page)
    
    def browse_comfy_path(self):
        """Browse for ComfyUI directory"""
        directory = QFileDialog.getExistingDirectory(self, "Select ComfyUI Directory")
        if directory:
            self.comfy_path_input.setText(directory)
    
    def on_theme_changed(self, button):
        """Handle theme change"""
        theme_id = button.property("theme_id")
        
        current_theme_id = "dark"
        if self.parent and hasattr(self.parent, "current_theme_id"):
            current_theme_id = self.parent.current_theme_id
            
        if theme_id != current_theme_id:
            self.update_theme_preview()
            self.theme_changed.emit(theme_id)
    
    def rescan_models(self):
        """Rescan models"""
        if self.parent and hasattr(self.parent, "scan_for_models"):
            self.parent.scan_for_models()
    
    def clear_database(self):
        """Clear the database"""
        if self.parent and hasattr(self.parent, "models_db"):
            from PySide6.QtWidgets import QMessageBox
            
            reply = QMessageBox.question(
                self, "Clear Database", 
                "Are you sure you want to clear the entire models database? This will not delete any files.",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.parent.models_db.clear()
                self.parent.models_db.save()
                
                # Refresh gallery
                if hasattr(self.parent, "gallery_tab"):
                    self.parent.gallery_tab.refresh_gallery()
                
                if hasattr(self.parent, "status_bar"):
                    self.parent.status_bar.showMessage("Models database cleared", 3000)
    
    def save_settings(self):
        """Save settings"""
        if not self.parent or not hasattr(self.parent, "config") or not hasattr(self.parent, "config_manager"):
            return
        
        config = self.parent.config
        
        # General settings
        config["comfy_path"] = self.comfy_path_input.text()
        config["api_key"] = self.api_key_input.text()
        
        # Download settings
        config["top_image_count"] = self.top_image_count_input.value()
        config["download_threads"] = self.download_threads_input.value()
        config["download_images"] = self.download_images_checkbox.isChecked()
        config["download_model"] = self.download_model_checkbox.isChecked()
        config["create_html"] = self.create_html_checkbox.isChecked()
        config["download_nsfw"] = self.download_nsfw_checkbox.isChecked()
        config["auto_organize"] = self.auto_organize_checkbox.isChecked()
        config["auto_open_html"] = self.auto_open_html_checkbox.isChecked()
        
        # Gallery settings
        config["gallery_columns"] = self.gallery_columns_input.value()
        config["default_sort"] = self.default_sort_combo.currentData()
        
        # Get favorite tags
        favorite_tags = self.favorite_tags_input.toPlainText().split("\n")
        favorite_tags = [tag.strip() for tag in favorite_tags if tag.strip()]
        config["favorite_tags"] = favorite_tags
        
        # Advanced settings
        config["log_level"] = self.log_level_combo.currentData()
        config["auto_check_updates"] = self.auto_check_updates_checkbox.isChecked()
        
        # Save and signal
        self.parent.config_manager.save()
        self.settings_saved.emit()