
from typing import Dict, Optional
import os

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QWidget, QTabWidget, QTableWidget, QTableWidgetItem,
    QGridLayout, QFrame, QMenu, QLineEdit, QFileDialog,
    QToolBar, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QSize, QUrl
from PySide6.QtGui import QPixmap, QIcon, QDesktopServices, QGuiApplication, QAction

from src.ui.components.image_viewer import ImageViewer
from src.utils.formatting import format_size, format_date

class ModelDetailDialog(QDialog):
    """Dialog for displaying detailed model information"""
    
    def __init__(self, model_data: Dict, theme: Dict, parent=None):
        super().__init__(parent)
        self.model_data = model_data
        self.theme = theme
        self.parent = parent
        
        # Set window properties
        self.setWindowTitle(f"Model: {model_data.get('name', 'Unknown')}")
        self.setMinimumSize(900, 600)
        
        # Initialize UI components
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI components"""
        layout = QVBoxLayout(self)
        
        # Create a horizontal splitter layout
        content_layout = QHBoxLayout()
        
        # Left side: Image gallery
        left_panel = self.create_left_panel()
        
        # Right side: Model info tabs
        right_panel = self.create_right_panel()
        
        # Add panels to content layout with 2:1 ratio
        content_layout.addWidget(left_panel, 2)
        content_layout.addWidget(right_panel, 1)
        
        # Add content to main layout
        layout.addLayout(content_layout)
        
        # Bottom toolbar with actions
        toolbar = self.create_toolbar()
        layout.addWidget(toolbar)
    
    def create_left_panel(self):
        """Create left panel with image gallery"""
        panel = QFrame()
        panel.setFrameShape(QFrame.StyledPanel)
        panel.setStyleSheet(f"""
            QFrame {{
                background-color: {self.theme['card']};
                border: 1px solid {self.theme['border']};
                border-radius: 8px;
            }}
        """)
        
        layout = QVBoxLayout(panel)
        
        # Create image gallery using grid layout
        gallery_widget = QWidget()
        gallery_layout = QGridLayout(gallery_widget)
        gallery_layout.setContentsMargins(0, 0, 0, 0)
        gallery_layout.setSpacing(10)
        
        # Get top images from model info
        images = self.model_data.get("images", [])
        max_images = min(9, len(images))  # 3x3 grid max
        
        # Place images in grid (3x3)
        row, col = 0, 0
        for i in range(max_images):
            image = images[i]
            
            if "local_path" in image:
                # Create image viewer
                viewer = ImageViewer(self.theme)
                viewer.setFixedSize(200, 200)
                
                # Load image
                viewer.load_image(image["local_path"])
                
                # Store image data for details panel
                viewer.image_data = image
                
                # Connect click signal
                viewer.clicked.connect(self.on_image_clicked)
                
                gallery_layout.addWidget(viewer, row, col)
                
                col += 1
                if col >= 3:  # 3 columns
                    col = 0
                    row += 1
        
        # Add gallery to layout
        gallery_scroll = QScrollArea()
        gallery_scroll.setWidgetResizable(True)
        gallery_scroll.setWidget(gallery_widget)
        gallery_scroll.setStyleSheet("background: transparent; border: none;")
        
        layout.addWidget(gallery_scroll)
        
        return panel
    
    def create_right_panel(self):
        """Create right panel with model info tabs"""
        panel = QTabWidget()
        panel.setStyleSheet(f"""
            QTabWidget {{
                background-color: {self.theme['card']};
                border: 1px solid {self.theme['border']};
                border-radius: 8px;
            }}
            QTabWidget::pane {{
                border: 1px solid {self.theme['border']};
                border-radius: 8px;
                top: -1px;
            }}
            QTabBar::tab {{
                background-color: {self.theme['secondary']};
                color: {self.theme['text_secondary']};
                border: 1px solid {self.theme['border']};
                border-bottom: none;
                padding: 6px 12px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }}
            QTabBar::tab:selected {{
                background-color: {self.theme['card']};
                color: {self.theme['text']};
            }}
            QTabBar::tab:hover:!selected {{
                background-color: {self.theme['card_hover']};
            }}
        """)
        
        # Info tab
        info_tab = self.create_info_tab()
        panel.addTab(info_tab, "Info")
        
        # Description tab
        desc_tab = self.create_description_tab()
        panel.addTab(desc_tab, "Description")
        
        # Tags tab
        tags_tab = self.create_tags_tab()
        panel.addTab(tags_tab, "Tags")
        
        # Dependencies tab
        if self.model_data.get("dependencies"):
            dependencies_tab = self.create_dependencies_tab()
            panel.addTab(dependencies_tab, "Dependencies")
        
        return panel
    
    def create_info_tab(self):
        """Create info tab with model details"""
        tab = QScrollArea()
        tab.setWidgetResizable(True)
        tab.setStyleSheet("background: transparent; border: none;")
        
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(10)
        
        # Create info table
        table = QTableWidget()
        table.setColumnCount(2)
        table.setHorizontalHeaderLabels(["Property", "Value"])
        table.horizontalHeader().setStretchLastSection(True)
        table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {self.theme['card']};
                gridline-color: {self.theme['border']};
                border: none;
            }}
            QHeaderView::section {{
                background-color: {self.theme['secondary']};
                color: {self.theme['text']};
                padding: 5px;
                border: 1px solid {self.theme['border']};
            }}
            QTableWidget::item {{
                padding: 5px;
                color: {self.theme['text']};
            }}
        """)
        
        # Add info rows
        info = [
            ("Name", self.model_data.get("name", "Unknown")),
            ("Type", self.model_data.get("type", "Unknown")),
            ("Base Model", self.model_data.get("base_model", "Unknown")),
            ("Creator", self.model_data.get("creator", "Unknown")),
            ("Version", self.model_data.get("version_name", "Unknown")),
            ("Size", format_size(self.model_data.get("size", 0))),
            ("Downloaded", format_date(self.model_data.get("download_date", ""))),
            ("Last Updated", format_date(self.model_data.get("last_updated", ""))),
            ("NSFW", "Yes" if self.model_data.get("nsfw", False) else "No")
        ]
        
        table.setRowCount(len(info))
        for i, (key, value) in enumerate(info):
            key_item = QTableWidgetItem(key)
            key_item.setFlags(key_item.flags() & ~Qt.ItemIsEditable)  # Make read-only
            
            value_item = QTableWidgetItem(str(value))
            value_item.setFlags(value_item.flags() & ~Qt.ItemIsEditable)  # Make read-only
            
            table.setItem(i, 0, key_item)
            table.setItem(i, 1, value_item)
        
        layout.addWidget(table)
        
        # Storage location
        location_frame = QFrame()
        location_frame.setFrameShape(QFrame.StyledPanel)
        location_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {self.theme['secondary']};
                border: 1px solid {self.theme['border']};
                border-radius: 4px;
                padding: 10px;
            }}
        """)
        
        location_layout = QVBoxLayout(location_frame)
        
        location_label = QLabel("Storage Location:")
        location_label.setStyleSheet(f"color: {self.theme['text']}; font-weight: bold;")
        location_layout.addWidget(location_label)
        
        # Path with copy button
        path_layout = QHBoxLayout()
        
        path_field = QLineEdit(self.model_data.get("path", ""))
        path_field.setReadOnly(True)
        path_field.setStyleSheet(f"""
            QLineEdit {{
                background-color: {self.theme['input_bg']};
                color: {self.theme['text']};
                border: 1px solid {self.theme['border']};
                border-radius: 4px;
                padding: 5px;
            }}
        """)
        path_layout.addWidget(path_field)
        
        copy_btn = QPushButton("Copy")
        copy_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.theme['accent']};
                color: white;
                border: none;
                border-radius: 4px;
                padding: 5px 10px;
            }}
            QPushButton:hover {{
                background-color: {self.theme['accent_hover']};
            }}
        """)
        copy_btn.clicked.connect(lambda: QGuiApplication.clipboard().setText(path_field.text()))
        path_layout.addWidget(copy_btn)
        
        open_btn = QPushButton("Open")
        open_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.theme['accent']};
                color: white;
                border: none;
                border-radius: 4px;
                padding: 5px 10px;
            }}
            QPushButton:hover {{
                background-color: {self.theme['accent_hover']};
            }}
        """)
        if self.model_data.get("path", ""):
            open_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(self.model_data["path"])))
        else:
            open_btn.setEnabled(False)
        path_layout.addWidget(open_btn)
        
        location_layout.addLayout(path_layout)
        layout.addWidget(location_frame)
        
        # Stats section
        if self.model_data.get("stats"):
            stats_frame = QFrame()
            stats_frame.setFrameShape(QFrame.StyledPanel)
            stats_frame.setStyleSheet(f"""
                QFrame {{
                    background-color: {self.theme['secondary']};
                    border: 1px solid {self.theme['border']};
                    border-radius: 4px;
                    padding: 10px;
                }}
            """)
            
            stats_layout = QVBoxLayout(stats_frame)
            
            stats_label = QLabel("Civitai Stats:")
            stats_label.setStyleSheet(f"color: {self.theme['text']}; font-weight: bold;")
            stats_layout.addWidget(stats_label)
            
            stats = self.model_data.get("stats", {})
            stats_grid = QGridLayout()
            stats_grid.setColumnStretch(1, 1)
            
            row = 0
            stat_items = [
                ("Rating", f"{stats.get('rating', 0):.1f} / 5 ({stats.get('ratingCount', 0)} ratings)"),
                ("Downloads", f"{stats.get('downloadCount', 0):,}"),
                ("Comments", f"{stats.get('commentCount', 0):,}"),
                ("Favorites", f"{stats.get('favoriteCount', 0):,}")
            ]
            
            for key, value in stat_items:
                key_label = QLabel(key + ":")
                key_label.setStyleSheet(f"color: {self.theme['text_secondary']};")
                
                value_label = QLabel(value)
                value_label.setStyleSheet(f"color: {self.theme['text']};")
                
                stats_grid.addWidget(key_label, row, 0)
                stats_grid.addWidget(value_label, row, 1)
                row += 1
            
            stats_layout.addLayout(stats_grid)
            layout.addWidget(stats_frame)
        
        # Set content and return
        tab.setWidget(content)
        return tab
    
    def create_description_tab(self):
        """Create description tab"""
        tab = QScrollArea()
        tab.setWidgetResizable(True)
        tab.setStyleSheet("background: transparent; border: none;")
        
        content = QWidget()
        layout = QVBoxLayout(content)
        
        description = self.model_data.get("description", "No description available.")
        
        # Description text
        desc_label = QLabel(description)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet(f"color: {self.theme['text']}; font-size: 14px;")
        desc_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        
        layout.addWidget(desc_label)
        layout.addStretch()
        
        tab.setWidget(content)
        return tab
    
    def create_tags_tab(self):
        """Create tags tab"""
        tab = QScrollArea()
        tab.setWidgetResizable(True)
        tab.setStyleSheet("background: transparent; border: none;")
        
        content = QWidget()
        layout = QVBoxLayout(content)
        
        # Title
        title = QLabel("Activation Tags")
        title.setStyleSheet(f"color: {self.theme['text']}; font-size: 16px; font-weight: bold;")
        layout.addWidget(title)
        
        # Tag grid
        tags_layout = QGridLayout()
        tags_layout.setColumnStretch(0, 1)
        tags_layout.setColumnStretch(1, 1)
        tags_layout.setColumnStretch(2, 1)
        
        # Add tags in columns
        tags = self.model_data.get("tags", [])
        row, col = 0, 0
        
        for tag in tags:
            tag_btn = QPushButton(tag)
            tag_btn.setCursor(Qt.PointingHandCursor)
            tag_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {self.theme['secondary']};
                    color: {self.theme['text']};
                    border: 1px solid {self.theme['border']};
                    border-radius: 4px;
                    padding: 5px 10px;
                    text-align: left;
                    margin: 3px;
                }}
                QPushButton:hover {{
                    background-color: {self.theme['accent']};
                    color: white;
                }}
            """)
            
            # Copy tag on click
            tag_btn.clicked.connect(lambda _, t=tag: QGuiApplication.clipboard().setText(t))
            
            tags_layout.addWidget(tag_btn, row, col)
            
            col += 1
            if col >= 3:  # 3 columns
                col = 0
                row += 1
        
        layout.addLayout(tags_layout)
        layout.addStretch()
        
        # Add a note about clicking to copy
        note = QLabel("Click on a tag to copy it to clipboard")
        note.setStyleSheet(f"color: {self.theme['text_secondary']}; font-style: italic;")
        layout.addWidget(note)
        
        tab.setWidget(content)
        return tab
    
    def create_dependencies_tab(self):
        """Create dependencies tab"""
        tab = QScrollArea()
        tab.setWidgetResizable(True)
        tab.setStyleSheet("background: transparent; border: none;")
        
        content = QWidget()
        layout = QVBoxLayout(content)
        
        # Title
        title = QLabel("Model Dependencies")
        title.setStyleSheet(f"color: {self.theme['text']}; font-size: 16px; font-weight: bold;")
        layout.addWidget(title)
        
        # Dependencies table
        table = QTableWidget()
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels(["Name", "Type", "Required"])
        table.horizontalHeader().setStretchLastSection(True)
        table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {self.theme['card']};
                gridline-color: {self.theme['border']};
                border: none;
            }}
            QHeaderView::section {{
                background-color: {self.theme['secondary']};
                color: {self.theme['text']};
                padding: 5px;
                border: 1px solid {self.theme['border']};
            }}
            QTableWidget::item {{
                padding: 5px;
                color: {self.theme['text']};
            }}
        """)
        
        # Add dependencies
        dependencies = self.model_data.get("dependencies", [])
        table.setRowCount(len(dependencies))
        
        for i, dep in enumerate(dependencies):
            name_item = QTableWidgetItem(dep.get("name", "Unknown"))
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)  # Make read-only
            
            type_item = QTableWidgetItem(dep.get("type", "Unknown"))
            type_item.setFlags(type_item.flags() & ~Qt.ItemIsEditable)  # Make read-only
            
            required = "Yes" if dep.get("required", False) else "No"
            required_item = QTableWidgetItem(required)
            required_item.setFlags(required_item.flags() & ~Qt.ItemIsEditable)  # Make read-only
            
            table.setItem(i, 0, name_item)
            table.setItem(i, 1, type_item)
            table.setItem(i, 2, required_item)
        
        layout.addWidget(table)
        
        tab.setWidget(content)
        return tab
    
    def create_toolbar(self):
        """Create bottom toolbar with actions"""
        toolbar = QToolBar()
        toolbar.setStyleSheet(f"""
            QToolBar {{
                background-color: {self.theme['secondary']};
                border-top: 1px solid {self.theme['border']};
                border-bottom: none;
                border-left: none;
                border-right: none;
                spacing: 10px;
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
        """)
        
        # Favorite action
        is_favorite = self.model_data.get("favorite", False)
        self.fav_action = QAction("★ Remove from Favorites" if is_favorite else "☆ Add to Favorites", self)
        self.fav_action.triggered.connect(self.toggle_favorite)
        toolbar.addAction(self.fav_action)
        
        toolbar.addSeparator()
        
        # Open in browser action
        if "id" in self.model_data:
            browser_action = QAction("Open in Browser", self)
            browser_action.triggered.connect(lambda: QDesktopServices.openUrl(QUrl(f"https://civitai.com/models/{self.model_data['id']}")))
            toolbar.addAction(browser_action)
        
        # Add spacer
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        toolbar.addWidget(spacer)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.theme['accent']};
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                min-width: 80px;
            }}
            QPushButton:hover {{
                background-color: {self.theme['accent_hover']};
            }}
        """)
        close_btn.clicked.connect(self.accept)
        toolbar.addWidget(close_btn)
        
        return toolbar
    
    def toggle_favorite(self):
        """Toggle favorite status"""
        is_favorite = not self.model_data.get("favorite", False)
        self.model_data["favorite"] = is_favorite
        
        # Update action text
        self.fav_action.setText("★ Remove from Favorites" if is_favorite else "☆ Add to Favorites")
        
        # Update in database if parent exists
        if self.parent and hasattr(self.parent, "models_db"):
            model_id = self.model_data.get("id")
            if model_id:
                self.parent.models_db.update_model_field(model_id, "favorite", is_favorite)
                self.parent.models_db.save()
                
                # Show toast notification
                status = "added to" if is_favorite else "removed from"
                if hasattr(self.parent, "toast_manager"):
                    self.parent.toast_manager.show_toast(
                        f"'{self.model_data.get('name', 'Unknown')}' {status} favorites",
                        "success"
                    )
    
    def on_image_clicked(self, image_viewer):
        """Handle image clicked"""
        if not hasattr(image_viewer, "image_data"):
            return
            
        image_path = image_viewer.image_path
        image_data = image_viewer.image_data
        
        # Show image in larger viewer or with metadata
        if os.path.exists(image_path):
            # Get image details
            meta = image_data.get("meta", {})
            prompt = meta.get("prompt", "No prompt available")
            
            # Create image dialog
            self.show_image_dialog(image_path, prompt, image_data)
    
    def show_image_dialog(self, image_path, prompt, image_data):
        """Show image in a dialog with metadata"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Image Details")
        dialog.setMinimumSize(800, 600)
        
        layout = QHBoxLayout(dialog)
        
        # Left side: Image
        left_layout = QVBoxLayout()
        
        image_viewer = ImageViewer(self.theme)
        image_viewer.load_image(image_path)
        left_layout.addWidget(image_viewer)
        
        # Right side: Metadata
        right_layout = QVBoxLayout()
        
        # Get image metadata
        meta = image_data.get("meta", {})
        stats = image_data.get("stats", {})
        
        # Add sections
        sections = [
            ("Prompt", meta.get("prompt", "No prompt available")),
            ("Negative Prompt", meta.get("negativePrompt", "No negative prompt available")),
            ("Model", meta.get("Model", "Unknown")),
            ("Sampler", meta.get("Sampler", "Unknown")),
            ("Steps", str(meta.get("Steps", "Unknown"))),
            ("CFG Scale", str(meta.get("CFG scale", "Unknown"))),
            ("Size", f"{meta.get('Width', 'Unknown')}x{meta.get('Height', 'Unknown')}"),
            ("Seed", str(meta.get("Seed", "Unknown")))
        ]
        
        for title, content in sections:
            section = QFrame()
            section.setFrameShape(QFrame.StyledPanel)
            section.setStyleSheet(f"""
                QFrame {{
                    background-color: {self.theme['secondary']};
                    border: 1px solid {self.theme['border']};
                    border-radius: 4px;
                    padding: 5px;
                    margin-bottom: 5px;
                }}
            """)
            
            section_layout = QVBoxLayout(section)
            
            title_label = QLabel(title)
            title_label.setStyleSheet(f"color: {self.theme['text_secondary']}; font-weight: bold; font-size: 12px;")
            
            content_label = QLabel(content)
            content_label.setWordWrap(True)
            content_label.setStyleSheet(f"color: {self.theme['text']}; font-size: 14px;")
            content_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            
            section_layout.addWidget(title_label)
            section_layout.addWidget(content_label)
            
            right_layout.addWidget(section)
        
        # Add reactions
        reactions = QFrame()
        reactions.setFrameShape(QFrame.StyledPanel)
        reactions.setStyleSheet(f"""
            QFrame {{
                background-color: {self.theme['secondary']};
                border: 1px solid {self.theme['border']};
                border-radius: 4px;
                padding: 5px;
            }}
        """)
        
        reactions_layout = QHBoxLayout(reactions)
        
        like_label = QLabel(f"👍 {stats.get('likeCount', 0)}")
        like_label.setStyleSheet(f"color: {self.theme['text']}; font-size: 14px;")
        
        heart_label = QLabel(f"❤️ {stats.get('heartCount', 0)}")
        heart_label.setStyleSheet(f"color: {self.theme['text']}; font-size: 14px;")
        
        laugh_label = QLabel(f"😂 {stats.get('laughCount', 0)}")
        laugh_label.setStyleSheet(f"color: {self.theme['text']}; font-size: 14px;")
        
        reactions_layout.addWidget(like_label)
        reactions_layout.addWidget(heart_label)
        reactions_layout.addWidget(laugh_label)
        
        right_layout.addWidget(reactions)
        right_layout.addStretch()
        
        # Add sections to main layout
        layout.addLayout(left_layout, 3)  # 3:1 ratio
        layout.addLayout(right_layout, 1)
        
        dialog.exec_()
