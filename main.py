
#!/usr/bin/env python3
import sys
import os
from PySide6.QtWidgets import QApplication, QStyleFactory
from PySide6.QtCore import QSettings, Qt
from PySide6.QtGui import QPalette, QColor

from src.ui.main_window import MainWindow
from src.utils.logger import setup_logger
from src.utils.config_manager import ConfigManager
from src.constants.theme import get_theme

def set_dark_palette(app):
    """Set dark palette for the application"""
    palette = QPalette()
    theme = get_theme("dark")
    
    # Set colors
    palette.setColor(QPalette.Window, QColor(theme["primary"]))
    palette.setColor(QPalette.WindowText, QColor(theme["text"]))
    palette.setColor(QPalette.Base, QColor(theme["secondary"]))
    palette.setColor(QPalette.AlternateBase, QColor(theme["input_bg"]))
    palette.setColor(QPalette.ToolTipBase, QColor(theme["card"]))
    palette.setColor(QPalette.ToolTipText, QColor(theme["text"]))
    palette.setColor(QPalette.Text, QColor(theme["text"]))
    palette.setColor(QPalette.Button, QColor(theme["secondary"]))
    palette.setColor(QPalette.ButtonText, QColor(theme["text"]))
    palette.setColor(QPalette.BrightText, QColor(theme["accent"]))
    palette.setColor(QPalette.Link, QColor(theme["accent"]))
    palette.setColor(QPalette.Highlight, QColor(theme["accent"]))
    palette.setColor(QPalette.HighlightedText, QColor(theme["text"]))
    
    app.setPalette(palette)

if __name__ == "__main__":
    # Set up logging
    logger = setup_logger()
    
    # Load configuration
    config = ConfigManager()
    
    # Enable high DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    if hasattr(Qt, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    # Create Qt application
    app = QApplication(sys.argv)
    
    # Set application style to Fusion for consistent look
    app.setStyle(QStyleFactory.create("Fusion"))
    
    # Set dark theme
    if config.get("theme", "dark") == "dark":
        set_dark_palette(app)
    
    # Set application info
    app.setApplicationName("Civitai Model Manager")
    app.setApplicationVersion("2.0")
    app.setOrganizationName("CivitaiManager")
    app.setOrganizationDomain("civitaimanager.org")
    
    # Create main window
    main_window = MainWindow(config)
    main_window.show()
    
    sys.exit(app.exec())
