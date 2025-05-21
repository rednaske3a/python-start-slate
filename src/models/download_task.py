
from dataclasses import dataclass
import time
from typing import Optional, Dict

from src.constants.constants import DOWNLOAD_STATUS
from src.models.model_info import ModelInfo

@dataclass
class DownloadTask:
    """
    Data class for a download task
    """
    url: str
    status: str = DOWNLOAD_STATUS["QUEUED"]
    model_info: Optional[ModelInfo] = None
    model_progress: int = 0
    image_progress: int = 0
    error_message: str = ""
    start_time: float = 0
    end_time: float = 0
    priority: int = 0  # Lower number = higher priority
    
    def get_duration(self) -> float:
        """Get the duration of the download in seconds"""
        if self.start_time == 0:
            return 0
        if self.end_time == 0:
            return time.time() - self.start_time
        return self.end_time - self.start_time
    
    def get_status_color(self, theme: Dict) -> str:
        """Get the color for the status based on the current theme"""
        if self.status == DOWNLOAD_STATUS["COMPLETED"]:
            return theme["success"]
        elif self.status == DOWNLOAD_STATUS["FAILED"] or self.status == DOWNLOAD_STATUS["CANCELED"]:
            return theme["danger"]
        elif self.status == DOWNLOAD_STATUS["DOWNLOADING"]:
            return theme["accent"]
        else:
            return theme["text_secondary"]
