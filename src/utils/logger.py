
import logging
import os
import sys
from pathlib import Path
from datetime import datetime

# Configure logger
def setup_logger(log_level="INFO"):
    """Setup and configure logger"""
    # Create logs directory if it doesn't exist
    log_dir = Path.home() / ".civitai_manager" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Set log file path with timestamp
    log_file = log_dir / f"civitai_manager_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    # Convert string log level to logging level
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Configure root logger
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logger = logging.getLogger("civitai_manager")
    logger.info(f"Logger initialized. Log file: {log_file}")
    
    return logger

def get_logger(name=None):
    """Get a named logger"""
    if name:
        return logging.getLogger(f"civitai_manager.{name}")
    return logging.getLogger("civitai_manager")
