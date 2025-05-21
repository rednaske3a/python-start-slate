
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QScrollArea, QGridLayout, QFileDialog, QMessageBox, QProgressBar,
    QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap, QIcon, QColor

import pyqtgraph as pg
import os
import shutil
from typing import Dict, List, Optional

from src.core.storage_manager import StorageManager
from src.ui.components.storage_info_widget import StorageInfoWidget
from src.utils.logger import get_logger

logger = get_logger(__name__)

class StorageTab(QWidget):
    """Tab for storage management"""
    
    def __init__(self, theme: Dict, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.parent = parent
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI components"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create storage overview section
        self.storage_info_widget = StorageInfoWidget(self.theme)
        
        # Create tabs for different storage views
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {self.theme['border']};
                background: {self.theme['secondary']};
            }}
            QTabBar::tab {{
                background: {self.theme['secondary']};
                color: {self.theme['text_secondary']};
                padding: 8px 16px;
                border: 1px solid {self.theme['border']};
                margin-right: 2px;
            }}
            QTabBar::tab:selected {{
                background: {self.theme['primary']};
                color: {self.theme['text']};
                border-bottom-color: {self.theme['primary']};
            }}
            QTabBar::tab:hover:!selected {{
                background: {self.theme['card_hover']};
            }}
        """)
        
        # Create models tab
        self.models_tab = QWidget()
        models_layout = QVBoxLayout(self.models_tab)
        
        # Add table for model list
        self.models_table = QTableWidget(0, 5)  # Rows will be added dynamically, 5 columns
        self.models_table.setHorizontalHeaderLabels(["Name", "Type", "Size", "Base Model", "Actions"])
        self.models_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.models_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.models_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.models_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.models_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.models_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.models_table.setSelectionMode(QTableWidget.ExtendedSelection)
        self.models_table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {self.theme['secondary']};
                gridline-color: {self.theme['border']};
                color: {self.theme['text']};
                border: none;
            }}
            QTableWidget::item {{
                padding: 4px;
            }}
            QTableWidget::item:selected {{
                background-color: {self.theme['accent']};
                color: white;
            }}
            QHeaderView::section {{
                background-color: {self.theme['card']};
                color: {self.theme['text']};
                padding: 6px;
                border: 1px solid {self.theme['border']};
            }}
        """)
        
        # Add toolbar for batch operations
        toolbar = QFrame()
        toolbar.setFrameShape(QFrame.StyledPanel)
        toolbar.setStyleSheet(f"background-color: {self.theme['card']}; border-radius: 4px;")
        toolbar_layout = QHBoxLayout(toolbar)
        
        # Add toolbar buttons
        self.delete_btn = QPushButton("Delete Selected")
        self.delete_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.theme['danger']};
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {self.theme['danger_hover']};
            }}
        """)
        self.delete_btn.clicked.connect(self.delete_selected_models)
        
        self.export_btn = QPushButton("Export Selected")
        self.export_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.theme['accent']};
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {self.theme['accent_hover']};
            }}
        """)
        self.export_btn.clicked.connect(self.export_selected_models)
        
        self.find_duplicates_btn = QPushButton("Find Duplicates")
        self.find_duplicates_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.theme['secondary']};
                color: {self.theme['text']};
                border: 1px solid {self.theme['border']};
                padding: 8px 16px;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {self.theme['card_hover']};
            }}
        """)
        self.find_duplicates_btn.clicked.connect(self.find_duplicates)
        
        # Add buttons to toolbar
        toolbar_layout.addWidget(self.delete_btn)
        toolbar_layout.addWidget(self.export_btn)
        toolbar_layout.addWidget(self.find_duplicates_btn)
        toolbar_layout.addStretch()
        
        # Add scan button
        self.scan_btn = QPushButton("Scan for Models")
        self.scan_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.theme['info']};
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {self.theme['accent_hover']};
            }}
        """)
        self.scan_btn.clicked.connect(self.scan_for_models)
        toolbar_layout.addWidget(self.scan_btn)
        
        # Add components to models tab
        models_layout.addWidget(toolbar)
        models_layout.addWidget(self.models_table)
        
        # Create disk usage tab
        self.disk_tab = QWidget()
        disk_layout = QVBoxLayout(self.disk_tab)
        
        # Create pie chart
        self.chart_widget = pg.PlotWidget()
        self.chart_widget.setBackground(self.theme["secondary"])
        self.chart_widget.setMinimumHeight(300)
        
        # Add to layout
        disk_layout.addWidget(self.chart_widget)
        disk_layout.addWidget(self.storage_info_widget)
        
        # Add tabs to tab widget
        self.tabs.addTab(self.models_tab, "Models")
        self.tabs.addTab(self.disk_tab, "Disk Usage")
        
        # Add components to main layout
        layout.addWidget(self.tabs)
        
        # Refresh data
        self.refresh_storage_data()
    
    def refresh_storage_data(self):
        """Refresh storage data"""
        if not self.parent or not hasattr(self.parent, "storage_manager"):
            return
            
        # Update storage widget
        total, free, categories = self.parent.storage_manager.get_storage_usage()
        self.storage_info_widget.update_usage(total, free, categories)
        
        # Update pie chart
        self.update_pie_chart(categories)
        
        # Update models table
        self.refresh_models_table()
    
    def update_pie_chart(self, categories):
        """Update pie chart with storage data"""
        self.chart_widget.clear()
        
        # Skip if no data
        if not categories:
            return
            
        # Prepare data
        labels = list(categories.keys())
        sizes = list(categories.values())
        colors = [
            "#BB86FC",  # Purple
            "#4CAF50",  # Green
            "#F44336",  # Red
            "#2196F3",  # Blue
            "#FFC107",  # Yellow
            "#FF5722",  # Orange
            "#9C27B0",  # Purple
            "#00BCD4",  # Cyan
        ]
        
        # Create pie chart
        pie = pg.PlotItem()
        pie.hideAxis('left')
        pie.hideAxis('bottom')
        
        # Create legend
        legend = pg.LegendItem()
        legend.setParentItem(pie)
        legend.anchor((1, 0), (1, 0))
        
        # Calculate total and percentages
        total = sum(sizes)
        if total == 0:
            return
            
        # Add pie sectors
        start_angle = 0
        for i, (label, size) in enumerate(zip(labels, sizes)):
            if size == 0:
                continue
                
            # Calculate angle
            angle = size / total * 360
            
            # Create sector
            sector = pg.PlotCurveItem()
            sector_color = colors[i % len(colors)]
            
            # Add to legend
            percent = size / total * 100
            from src.utils.formatting import format_size
            legend.addItem(
                sector, 
                f"{label}: {format_size(size)} ({percent:.1f}%)"
            )
            
            # Next angle
            start_angle += angle
        
        self.chart_widget.addItem(pie)
    
    def refresh_models_table(self):
        """Refresh models table"""
        if not self.parent or not hasattr(self.parent, "models_db"):
            return
            
        # Clear table
        self.models_table.setRowCount(0)
        
        # Get models from database
        models = self.parent.models_db.list_models()
        
        # Add rows
        for i, model in enumerate(models):
            self.models_table.insertRow(i)
            
            # Model name
            name_item = QTableWidgetItem(model.get("name", "Unknown"))
            name_item.setData(Qt.UserRole, model.get("id"))
            self.models_table.setItem(i, 0, name_item)
            
            # Model type
            type_item = QTableWidgetItem(model.get("type", "Unknown"))
            self.models_table.setItem(i, 1, type_item)
            
            # Model size
            from src.utils.formatting import format_size
            size = model.get("size", 0)
            size_item = QTableWidgetItem(format_size(size))
            size_item.setData(Qt.UserRole, size)  # Store raw size for sorting
            self.models_table.setItem(i, 2, size_item)
            
            # Base model
            base_model_item = QTableWidgetItem(model.get("base_model", "Unknown"))
            self.models_table.setItem(i, 3, base_model_item)
            
            # Actions cell
            actions_cell = QWidget()
            actions_layout = QHBoxLayout(actions_cell)
            actions_layout.setContentsMargins(2, 2, 2, 2)
            
            # Delete button
            delete_btn = QPushButton("🗑️")
            delete_btn.setToolTip("Delete")
            delete_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {self.theme['text_secondary']};
                    border: none;
                }}
                QPushButton:hover {{
                    color: {self.theme['danger']};
                }}
            """)
            delete_btn.clicked.connect(lambda _, mid=model.get("id"): self.delete_model(mid))
            
            # View button
            view_btn = QPushButton("👁️")
            view_btn.setToolTip("View Details")
            view_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {self.theme['text_secondary']};
                    border: none;
                }}
                QPushButton:hover {{
                    color: {self.theme['accent']};
                }}
            """)
            view_btn.clicked.connect(lambda _, m=model: self.view_model_details(m))
            
            # Add buttons to layout
            actions_layout.addWidget(view_btn)
            actions_layout.addWidget(delete_btn)
            actions_layout.addStretch()
            
            # Set cell widget
            self.models_table.setCellWidget(i, 4, actions_cell)
    
    def delete_model(self, model_id):
        """Delete a single model"""
        if not self.parent or not hasattr(self.parent, "models_db"):
            return
            
        # Confirm deletion
        msgbox = QMessageBox()
        msgbox.setIcon(QMessageBox.Warning)
        msgbox.setText("Are you sure you want to delete this model?")
        msgbox.setInformativeText("This action cannot be undone.")
        msgbox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msgbox.setDefaultButton(QMessageBox.No)
        
        if msgbox.exec_() == QMessageBox.Yes:
            # Get model path first
            model_data = self.parent.models_db.get_model(model_id)
            
            # Delete model
            if self.parent.storage_manager.delete_model(model_id, model_data):
                # Remove from database
                self.parent.models_db.remove_model(model_id)
                self.parent.models_db.save()
                
                # Show success message
                if hasattr(self.parent, "toast_manager"):
                    self.parent.toast_manager.show_toast(
                        "Model deleted successfully", 
                        "success"
                    )
                
                # Refresh data
                self.refresh_storage_data()
    
    def delete_selected_models(self):
        """Delete selected models"""
        if not self.parent or not hasattr(self.parent, "models_db"):
            return
            
        # Get selected rows
        selected_rows = self.models_table.selectionModel().selectedRows()
        if not selected_rows:
            return
            
        # Confirm deletion
        msgbox = QMessageBox()
        msgbox.setIcon(QMessageBox.Warning)
        msgbox.setText(f"Delete {len(selected_rows)} model(s)?")
        msgbox.setInformativeText("This action cannot be undone.")
        msgbox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msgbox.setDefaultButton(QMessageBox.No)
        
        if msgbox.exec_() == QMessageBox.Yes:
            # Delete models
            deleted_count = 0
            
            for row in selected_rows:
                model_id = self.models_table.item(row.row(), 0).data(Qt.UserRole)
                model_data = self.parent.models_db.get_model(model_id)
                
                # Delete model
                if self.parent.storage_manager.delete_model(model_id, model_data):
                    # Remove from database
                    self.parent.models_db.remove_model(model_id)
                    deleted_count += 1
            
            # Save database
            self.parent.models_db.save()
            
            # Show success message
            if hasattr(self.parent, "toast_manager"):
                self.parent.toast_manager.show_toast(
                    f"Deleted {deleted_count} model(s)", 
                    "success"
                )
            
            # Refresh data
            self.refresh_storage_data()
    
    def export_selected_models(self):
        """Export selected models"""
        if not self.parent or not hasattr(self.parent, "models_db"):
            return
            
        # Get selected rows
        selected_rows = self.models_table.selectionModel().selectedRows()
        if not selected_rows:
            return
            
        # Get export directory
        export_dir = QFileDialog.getExistingDirectory(
            self, 
            "Select Export Directory",
            "",
            QFileDialog.ShowDirsOnly
        )
        
        if not export_dir:
            return
            
        # Export models
        model_paths = []
        for row in selected_rows:
            model_id = self.models_table.item(row.row(), 0).data(Qt.UserRole)
            model_data = self.parent.models_db.get_model(model_id)
            
            # Get path
            if "path" in model_data:
                model_paths.append(model_data["path"])
        
        # Perform export
        if model_paths:
            results = self.parent.storage_manager.export_models(model_paths, export_dir)
            
            # Show result
            if hasattr(self.parent, "toast_manager"):
                self.parent.toast_manager.show_toast(
                    f"Exported {results['success']} model(s). Failed: {results['failed']}",
                    "success" if results["success"] > 0 else "error"
                )
    
    def view_model_details(self, model):
        """View model details"""
        if self.parent and hasattr(self.parent, "gallery_tab"):
            self.parent.gallery_tab.show_model_details(model)
            
            # Switch to gallery tab
            for i in range(self.parent.tabs.count()):
                if self.parent.tabs.widget(i) == self.parent.gallery_tab:
                    self.parent.tabs.setCurrentIndex(i)
                    break
    
    def find_duplicates(self):
        """Find duplicate models"""
        if not self.parent or not hasattr(self.parent, "storage_manager"):
            return
            
        # Find duplicates
        duplicates = self.parent.storage_manager.find_duplicates()
        
        # Show results
        if not duplicates:
            if hasattr(self.parent, "toast_manager"):
                self.parent.toast_manager.show_toast(
                    "No duplicate models found",
                    "info"
                )
            return
            
        # TODO: Implement duplicate viewer dialog
        if hasattr(self.parent, "toast_manager"):
            self.parent.toast_manager.show_toast(
                f"Found {len(duplicates)} duplicate model groups",
                "warning"
            )
    
    def scan_for_models(self):
        """Scan for models"""
        if not self.parent:
            return
            
        # Show scanning toast
        if hasattr(self.parent, "toast_manager"):
            self.parent.toast_manager.show_toast(
                "Scanning for models...",
                "info"
            )
            
        # Perform scan
        self.parent.scan_for_models()
        
        # Refresh data
        self.refresh_storage_data()
    
    def set_theme(self, theme):
        """Set theme"""
        self.theme = theme
        
        # Update storage info widget
        self.storage_info_widget.set_theme(theme)
        
        # Update chart colors
        self.chart_widget.setBackground(theme["secondary"])
        
        # Refresh pie chart
        total, free, categories = self.parent.storage_manager.get_storage_usage()
        self.update_pie_chart(categories)
        
        # Update table styles
        self.models_table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {self.theme['secondary']};
                gridline-color: {self.theme['border']};
                color: {self.theme['text']};
                border: none;
            }}
            QTableWidget::item {{
                padding: 4px;
            }}
            QTableWidget::item:selected {{
                background-color: {self.theme['accent']};
                color: white;
            }}
            QHeaderView::section {{
                background-color: {self.theme['card']};
                color: {self.theme['text']};
                padding: 6px;
                border: 1px solid {self.theme['border']};
            }}
        """)
        
        # Update buttons
        self.delete_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.theme['danger']};
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {self.theme['danger_hover']};
            }}
        """)
        
        self.export_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.theme['accent']};
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {self.theme['accent_hover']};
            }}
        """)
        
        self.find_duplicates_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.theme['secondary']};
                color: {self.theme['text']};
                border: 1px solid {self.theme['border']};
                padding: 8px 16px;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {self.theme['card_hover']};
            }}
        """)
        
        self.scan_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.theme['info']};
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {self.theme['accent_hover']};
            }}
        """)
        
        # Update tabs
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {self.theme['border']};
                background: {self.theme['secondary']};
            }}
            QTabBar::tab {{
                background: {self.theme['secondary']};
                color: {self.theme['text_secondary']};
                padding: 8px 16px;
                border: 1px solid {self.theme['border']};
                margin-right: 2px;
            }}
            QTabBar::tab:selected {{
                background: {self.theme['primary']};
                color: {self.theme['text']};
                border-bottom-color: {self.theme['primary']};
            }}
            QTabBar::tab:hover:!selected {{
                background: {self.theme['card_hover']};
            }}
        """)
