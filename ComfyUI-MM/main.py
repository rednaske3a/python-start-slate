
#!/usr/bin/env python3
"""
ComfyUI Model Manager - A tool for downloading models from Civitai
"""
import sys
import os
import platform
import logging
from pathlib import Path
from PySide6.QtWidgets import QApplication, QStyleFactory
from PySide6.QtCore import Qt
from PySide6.QtGui import QPalette, QColor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(Path.home() / ".comfyui_mm" / "app.log")
    ]
)

logger = logging.getLogger("main")

def main():
    """Main entry point"""
    try:
        # Add root directory to path
        sys.path.insert(0, str(Path(__file__).parent.parent))
        
        # Import the GUI module
        from ComfyUI-MM.gui import MainWindow
        
        # Set up Qt application
        app = QApplication(sys.argv)
        
        # Enable high DPI scaling
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )
        if hasattr(Qt, 'AA_EnableHighDpiScaling'):
            QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
            QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
        
        # Set application style to Fusion for consistent look
        app.setStyle(QStyleFactory.create("Fusion"))
        
        # Set application info
        app.setApplicationName("ComfyUI Model Manager")
        app.setApplicationVersion("1.0.0")
        app.setOrganizationName("ComfyUI-MM")
        
        # Create main window
        main_window = MainWindow()
        main_window.show()
        
        # Run the application
        sys.exit(app.exec())
        
    except Exception as e:
        logger.exception(f"Error in main function: {e}")
        raise

if __name__ == "__main__":
    main()
