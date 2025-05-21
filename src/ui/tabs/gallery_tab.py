
from typing import Dict, List, Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QGridLayout, QDialog, QSplitter
)
from PySide6.QtCore import Qt, Signal

from src.ui.components.filter_panel import FilterPanel
from src.ui.components.model_gallery_view import ModelGalleryView
from src.ui.components.storage_info_widget import StorageInfoWidget
from src.ui.dialogs.model_detail_dialog import ModelDetailDialog

class GalleryTab(QWidget):
    """Gallery tab for browsing and managing models"""
    
    def __init__(self, theme: Dict, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.parent = parent
        self.filter_status_text = ""
        self.storage_info_widget = None
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI components"""
        layout = QHBoxLayout(self)
        
        # Left panel - filters
        left_panel = QWidget()
        left_panel.setMinimumWidth(250)
        left_panel.setMaximumWidth(300)
        
        # Create filter panel
        self.filter_panel = FilterPanel(self.theme)
        self.filter_panel.filter_changed.connect(self.apply_filters)
        
        left_layout = QVBoxLayout(left_panel)
        left_layout.addWidget(self.filter_panel)
        
        # Right panel - gallery with splitter for details panel
        right_splitter = QSplitter(Qt.Horizontal)
        
        # Main gallery area
        gallery_panel = QWidget()
        gallery_layout = QVBoxLayout(gallery_panel)
        gallery_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create gallery view
        self.gallery_view = ModelGalleryView(self.theme)
        self.gallery_view.model_clicked.connect(self.show_model_details)
        self.gallery_view.model_deleted.connect(self.delete_model)
        self.gallery_view.model_update_requested.connect(self.update_model)
        self.gallery_view.favorite_toggled.connect(self.toggle_favorite)
        
        gallery_layout.addWidget(self.gallery_view)
        
        right_splitter.addWidget(gallery_panel)
        
        # Add splitter to main layout
        layout.addWidget(left_panel)
        layout.addWidget(right_splitter, 1)  # Give the right panel more space
        
        # Create storage info widget (not added to layout, used in dialog)
        self.storage_info_widget = StorageInfoWidget(self.theme)
    
    def set_theme(self, theme):
        """Update the theme"""
        self.theme = theme
        
        # Update UI styles
        self.filter_panel.set_theme(self.theme)
        self.gallery_view.set_theme(self.theme)
        self.storage_info_widget.set_theme(self.theme)
    
    def apply_filters(self, filters):
        """Apply filters to the gallery"""
        if self.parent and hasattr(self.parent, "models_db"):
            # Get all models from database
            all_models = list(self.parent.models_db.models.values())
            
            # Pass filters to gallery view
            self.gallery_view.set_models(all_models)
            self.gallery_view.apply_filter(filters)
    
    def refresh_gallery(self):
        """Refresh the gallery"""
        # Apply current filters to refresh display
        if hasattr(self, 'filter_panel'):
            self.apply_filters(self.filter_panel.get_filters())
    
    def show_model_details(self, model_data):
        """Show model details dialog"""
        dialog = ModelDetailDialog(model_data, self.theme, self.parent)
        dialog.exec_()
    
    def delete_model(self, model_data):
        """Delete a model"""
        if self.parent and hasattr(self.parent, "models_db"):
            parent = self.parent
            model_id = model_data.get("id")
            
            if model_id and parent.models_db.remove_model(model_id):
                parent.models_db.save()
                self.refresh_gallery()
                
                # Show toast notification
                if hasattr(parent, "toast_manager"):
                    parent.toast_manager.show_toast(
                        f"Model '{model_data.get('name', 'Unknown')}' deleted",
                        "success"
                    )
                # Fallback to status bar
                elif hasattr(parent, "status_bar"):
                    parent.status_bar.showMessage(f"Model '{model_data.get('name', 'Unknown')}' deleted", 3000)
    
    def update_model(self, model_data):
        """Check for model updates"""
        # Not implemented yet
        # Show toast notification
        if hasattr(self.parent, "toast_manager"):
            self.parent.toast_manager.show_toast(
                f"Checking for updates to '{model_data.get('name', 'Unknown')}'",
                "info"
            )
        # Fallback to status bar
        elif hasattr(self.parent, "status_bar"):
            self.parent.status_bar.showMessage(f"Update check not implemented yet", 3000)
    
    def toggle_favorite(self, model_data, is_favorite):
        """Toggle favorite status for a model"""
        if self.parent and hasattr(self.parent, "models_db"):
            parent = self.parent
            model_id = model_data.get("id")
            
            if model_id:
                parent.models_db.update_model_field(model_id, "favorite", is_favorite)
                parent.models_db.save()
                
                # Update model in gallery view
                model_data["favorite"] = is_favorite
                self.gallery_view.update_model(model_data)
                
                status = "added to" if is_favorite else "removed from"
                
                # Show toast notification
                if hasattr(parent, "toast_manager"):
                    parent.toast_manager.show_toast(
                        f"'{model_data.get('name', 'Unknown')}' {status} favorites",
                        "success"
                    )
                # Fallback to status bar
                elif hasattr(parent, "status_bar"):
                    parent.status_bar.showMessage(f"'{model_data.get('name', 'Unknown')}' {status} favorites", 3000)
    
    def show_storage_dialog(self):
        """Show storage usage dialog"""
        if self.storage_info_widget:
            dialog = QDialog(self)
            dialog.setWindowTitle("Storage Usage")
            dialog.setMinimumSize(500, 600)
            
            layout = QVBoxLayout(dialog)
            layout.addWidget(self.storage_info_widget)
            
            close_btn = QPushButton("Close")
            close_btn.setStyleSheet(f"""
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
            close_btn.clicked.connect(dialog.accept)
            
            layout.addWidget(close_btn)
            
            # Refresh storage analysis
            if self.parent and hasattr(self.parent, "storage_manager"):
                total, free, categories = self.parent.storage_manager.get_storage_usage()
                self.storage_info_widget.update_usage(total, free, categories)
            
            dialog.exec_()
