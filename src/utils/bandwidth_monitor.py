
"""
Bandwidth monitoring utility
"""
import time
from collections import deque
from typing import Dict, List, Deque
import threading

class BandwidthMonitor:
    """Monitor bandwidth usage for downloads"""
    
    def __init__(self, window_seconds=30, sample_rate=1):
        """
        Initialize bandwidth monitor
        
        Args:
            window_seconds: Number of seconds to keep in history
            sample_rate: Sampling rate in seconds
        """
        self.window_seconds = window_seconds
        self.sample_rate = sample_rate
        
        # Store timestamps and bytes
        self.timestamps: Deque[float] = deque(maxlen=int(window_seconds/sample_rate))
        self.bytes_values: Deque[int] = deque(maxlen=int(window_seconds/sample_rate))
        
        self.total_bytes = 0
        self.started_at = time.time()
        self.lock = threading.Lock()
    
    def add_data_point(self, bytes_transferred: int):
        """Add data point for bandwidth calculation"""
        with self.lock:
            now = time.time()
            self.timestamps.append(now)
            self.bytes_values.append(bytes_transferred)
            self.total_bytes += bytes_transferred
    
    def get_current_bandwidth(self) -> float:
        """
        Get current bandwidth in bytes per second
        
        Returns:
            Current bandwidth in bytes per second
        """
        with self.lock:
            if len(self.timestamps) < 2:
                return 0
                
            # Calculate bandwidth over the window
            time_diff = self.timestamps[-1] - self.timestamps[0]
            if time_diff <= 0:
                return 0
                
            bytes_sum = sum(self.bytes_values)
            return bytes_sum / time_diff
    
    def get_average_bandwidth(self) -> float:
        """
        Get average bandwidth since start in bytes per second
        
        Returns:
            Average bandwidth in bytes per second
        """
        with self.lock:
            elapsed = time.time() - self.started_at
            if elapsed <= 0:
                return 0
                
            return self.total_bytes / elapsed
    
    def get_bandwidth_history(self) -> tuple:
        """
        Get bandwidth history for plotting
        
        Returns:
            Tuple of (timestamps, bandwidth_values)
        """
        with self.lock:
            if len(self.timestamps) < 2:
                return [], []
                
            # Convert to relative times
            start_time = self.timestamps[0]
            relative_times = [(t - start_time) for t in self.timestamps]
            
            # Calculate bandwidth at each point
            bandwidth = []
            for i in range(1, len(self.timestamps)):
                time_diff = self.timestamps[i] - self.timestamps[i-1]
                if time_diff > 0:
                    bw = self.bytes_values[i] / time_diff
                    bandwidth.append(bw)
                else:
                    bandwidth.append(0)
                    
            # Prepend a zero for the first timestamp
            bandwidth.insert(0, 0)
            
            return relative_times, bandwidth
    
    def reset(self):
        """Reset bandwidth monitor"""
        with self.lock:
            self.timestamps.clear()
            self.bytes_values.clear()
            self.total_bytes = 0
            self.started_at = time.time()
