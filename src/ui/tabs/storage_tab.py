from typing import Dict, Optional, List
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QFormLayout, QTreeWidget, QTreeWidgetItem,
    QScrollArea, QSplitter, QFrame, QMessageBox, QFileDialog
)
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices

from src.ui.components.storage_usage_widget import StorageUsageWidget
from src.utils.formatting import format_size

class StorageTab(QWidget):
    """Storage management tab"""
    
    def __init__(self, theme: Dict, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.parent = parent
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI components"""
        layout = QVBoxLayout(self)
        
        # Title
        title_layout = QHBoxLayout()
        title = QLabel("Storage Manager")
        title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {self.theme['text']};")
        title_layout.addWidget(title)
        title_layout.addStretch()
        
        # Refresh button
        refresh_btn = QPushButton("Refresh")
        refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.theme['accent']};
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
            }}
            QPushButton:hover {{
                background-color: {self.theme['accent_hover']};
            }}
        """)
        refresh_btn.clicked.connect(self.refresh_storage)
        title_layout.addWidget(refresh_btn)
        
        layout.addLayout(title_layout)
        
        # Divider
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setFrameShadow(QFrame.Sunken)
        divider.setStyleSheet(f"background-color: {self.theme['border']};")
        layout.addWidget(divider)
        
        # Main content
        content_layout = QHBoxLayout()
        
        # Left panel - storage overview
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # Storage usage widget
        self.storage_usage_widget = StorageUsageWidget(self.theme)
        left_layout.addWidget(self.storage_usage_widget)
        
        # Storage actions
        actions_group = self.create_styled_group_box("Storage Actions")
        actions_layout = QVBoxLayout(actions_group)
        
        # Clean unused files button
        clean_btn = QPushButton("Clean Unused Files")
        clean_btn.setStyleSheet(self.get_action_button_style())
        clean_btn.clicked.connect(self.clean_unused_files)
        
        # Optimize storage button
        optimize_btn = QPushButton("Optimize Storage")
        optimize_btn.setStyleSheet(self.get_action_button_style())
        optimize_btn.clicked.connect(self.optimize_storage)
        
        # Batch delete button
        batch_delete_btn = QPushButton("Batch Delete")
        batch_delete_btn.setStyleSheet(self.get_danger_button_style())
        batch_delete_btn.clicked.connect(self.batch_delete)
        
        actions_layout.addWidget(clean_btn)
        actions_layout.addWidget(optimize_btn)
        actions_layout.addWidget(batch_delete_btn)
        
        left_layout.addWidget(actions_group)
        left_layout.addStretch()
        
        # Right panel - file browser
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # File tree
        self.file_tree = QTreeWidget()
        self.file_tree.setHeaderLabels(["Name", "Type", "Size", "Last Modified"])
        self.file_tree.setAlternatingRowColors(True)
        self.file_tree.setSelectionMode(QTreeWidget.ExtendedSelection)
        self.file_tree.setStyleSheet(f"""
            QTreeWidget {{
                background-color: {self.theme['input_bg']};
                color: {self.theme['text']};
                border: 1px solid {self.theme['border']};
                border-radius: 4px;
            }}
            QTreeWidget::item:selected {{
                background-color: {self.theme['accent']};
                color: white;
            }}
            QTreeWidget::item:hover {{
                background-color: {self.theme['card_hover']};
            }}
        """)
        
        right_layout.addWidget(self.file_tree)
        
        # File actions
        file_actions_layout = QHBoxLayout()
        
        open_btn = QPushButton("Open")
        open_btn.setStyleSheet(self.get_action_button_style())
        open_btn.clicked.connect(self.open_selected_file)
        
        delete_btn = QPushButton("Delete")
        delete_btn.setStyleSheet(self.get_danger_button_style())
        delete_btn.clicked.connect(self.delete_selected_files)
        
        file_actions_layout.addWidget(open_btn)
        file_actions_layout.addStretch()
        file_actions_layout.addWidget(delete_btn)
        
        right_layout.addLayout(file_actions_layout)
        
        # Add panels to content layout
        content_splitter = QSplitter(Qt.Horizontal)
        content_splitter.addWidget(left_panel)
        content_splitter.addWidget(right_panel)
        content_splitter.setStretchFactor(0, 1)
        content_splitter.setStretchFactor(1, 2)
        
        layout.addWidget(content_splitter)
        
        # Initialize storage data
        self.refresh_storage()
    
    def set_theme(self, theme):
        """Update the theme"""
        self.theme = theme
        
        # Update storage usage widget
        self.storage_usage_widget.set_theme(self.theme)
        
        # Update file tree
        self.file_tree.setStyleSheet(f"""
            QTreeWidget {{
                background-color: {self.theme['input_bg']};
                color: {self.theme['text']};
                border: 1px solid {self.theme['border']};
                border-radius: 4px;
            }}
            QTreeWidget::item:selected {{
                background-color: {self.theme['accent']};
                color: white;
            }}
            QTreeWidget::item:hover {{
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
    
    def get_action_button_style(self):
        """Get style for action buttons"""
        return f"""
            QPushButton {{
                background-color: {self.theme['accent']};
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px;
                margin-bottom: 8px;
            }}
            QPushButton:hover {{
                background-color: {self.theme['accent_hover']};
            }}
        """
    
    def get_danger_button_style(self):
        """Get style for danger buttons"""
        return f"""
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
        """
    
    def refresh_storage(self):
        """Refresh storage data and file tree"""
        self.refresh_storage_analysis()
        self.populate_file_tree()
    
    def refresh_storage_analysis(self):
        """Refresh storage usage analysis"""
        if self.parent and hasattr(self.parent, "storage_manager"):
            total, free, categories = self.parent.storage_manager.get_storage_usage()
            self.storage_usage_widget.update_usage(total, free, categories)
    
    def populate_file_tree(self):
        """Populate the file tree with files from the ComfyUI directory"""
        self.file_tree.clear()
        
        if not self.parent or not hasattr(self.parent, "config"):
            return
            
        comfy_path = self.parent.config.get("comfy_path", "")
        if not comfy_path:
            return
            
        from src.constants.constants import MODEL_TYPES
        
        # Create root items for each model type
        root_path = Path(comfy_path)
        if not root_path.exists():
            return
            
        model_type_items = {}
        for model_type, folder_path in MODEL_TYPES.items():
            type_path = root_path / folder_path
            if type_path.exists():
                item = QTreeWidgetItem(self.file_tree, [model_type, "Folder", "", ""])
                model_type_items[model_type] = item
                
                # Add base model folders
                for base_model_dir in type_path.iterdir():
                    if base_model_dir.is_dir():
                        base_model_name = base_model_dir.name
                        base_model_item = QTreeWidgetItem(item, [base_model_name, "Folder", "", ""])
                        
                        # Add model folders
                        for model_dir in base_model_dir.iterdir():
                            if model_dir.is_dir():
                                model_name = model_dir.name
                                
                                # Calculate folder size
                                if self.parent and hasattr(self.parent, "storage_manager"):
                                    folder_size = self.parent.storage_manager.get_folder_size(model_dir)
                                    size_str = format_size(folder_size)
                                else:
                                    size_str = "Unknown"
                                
                                # Get last modified time
                                from datetime import datetime
                                last_modified = datetime.fromtimestamp(model_dir.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
                                
                                model_item = QTreeWidgetItem(base_model_item, [model_name, "Model", size_str, last_modified])
                                model_item.setData(0, Qt.UserRole, str(model_dir))
                                
                                # Add model files
                                for file in model_dir.glob("*"):
                                    if file.is_file():
                                        file_name = file.name
                                        
                                        if self.parent and hasattr(self.parent, "storage_manager"):
                                            file_info = self.parent.storage_manager.get_file_info(file)
                                            file_type = file_info["type"]
                                            size_str = file_info["size_str"]
                                            last_modified = file_info["last_modified"]
                                        else:
                                            file_type = "File"
                                            size_str = "Unknown"
                                            last_modified = ""
                                        
                                        file_item = QTreeWidgetItem(model_item, [file_name, file_type, size_str, last_modified])
                                        file_item.setData(0, Qt.UserRole, str(file))
        
        # Expand the first level
        for i in range(self.file_tree.topLevelItemCount()):
            self.file_tree.topLevelItem(i).setExpanded(True)
    
    def open_selected_file(self):
        """Open the selected file or folder"""
        selected_items = self.file_tree.selectedItems()
        if not selected_items:
            return
            
        item = selected_items[0]  # Open only the first selected item
        file_path = item.data(0, Qt.UserRole)
        
        if file_path:
            QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))
    
    def delete_selected_files(self):
        """Delete the selected files or folders"""
        selected_items = self.file_tree.selectedItems()
        if not selected_items:
            return
            
        # Confirm deletion
        count = len(selected_items)
        reply = QMessageBox.question(
            self, 
            "Confirm Deletion", 
            f"Are you sure you want to delete {count} selected item(s)?\nThis cannot be undone!",
            QMessageBox.Yes | QMessageBox.No, 
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
            
        # Delete files
        deleted_count = 0
        for item in selected_items:
            file_path = item.data(0, Qt.UserRole)
            if file_path:
                path = Path(file_path)
                
                if self.parent and hasattr(self.parent, "storage_manager"):
                    if self.parent.storage_manager.delete_model(path):
                        deleted_count += 1
                else:
                    import shutil
                    try:
                        if path.is_dir():
                            shutil.rmtree(path)
                        else:
                            path.unlink()
                        deleted_count += 1
                    except Exception as e:
                        QMessageBox.warning(self, "Error", f"Failed to delete {path.name}: {str(e)}")
        
        # Refresh the file tree
        if deleted_count > 0:
            self.refresh_storage()
            QMessageBox.information(self, "Success", f"Successfully deleted {deleted_count} item(s).")
    
    def clean_unused_files(self):
        """Clean unused files (placeholder implementation)"""
        QMessageBox.information(
            self, 
            "Clean Unused Files", 
            "This feature would scan for and remove unused files like:\n"
            "- Orphaned model files\n"
            "- Duplicate images\n"
            "- Temporary files\n"
            "- Cache files\n\n"
            "This is a placeholder for the actual implementation."
        )
    
    def optimize_storage(self):
        """Optimize storage (placeholder implementation)"""
        QMessageBox.information(
            self, 
            "Optimize Storage", 
            "This feature would optimize storage by:\n"
            "- Compressing large files\n"
            "- Converting images to more efficient formats\n"
            "- Reorganizing folder structure\n"
            "- Removing redundant data\n\n"
            "This is a placeholder for the actual implementation."
        )
    
    def batch_delete(self):
        """Batch delete files (placeholder implementation)"""
        QMessageBox.information(
            self, 
            "Batch Delete", 
            "This feature would allow you to delete files in batch based on criteria like:\n"
            "- File type\n"
            "- Age\n"
            "- Size\n"
            "- Usage frequency\n\n"
            "This is a placeholder for the actual implementation."
        )