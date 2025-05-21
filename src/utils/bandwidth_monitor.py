
import time
from collections import deque


class BandwidthMonitor:
    """Monitor bandwidth usage over time"""
    
    def __init__(self, window_seconds=60, sample_rate=1):
        """Initialize bandwidth monitor
        
        Args:
            window_seconds: Time window in seconds to track
            sample_rate: Sample rate in seconds
        """
        self.window_seconds = window_seconds
        self.sample_rate = sample_rate
        self.window_samples = int(window_seconds / sample_rate)
        
        # Initialize data structures
        self.reset()
    
    def reset(self):
        """Reset monitor data"""
        # Store timestamps and corresponding bandwidth values
        self.timestamps = deque(maxlen=self.window_samples)
        self.values = deque(maxlen=self.window_samples)
        
        # Store current sample data
        self.current_bytes = 0
        self.last_sample_time = time.time()
    
    def add_data_point(self, bytes_transferred):
        """Add a data point for bandwidth calculation
        
        Args:
            bytes_transferred: Bytes transferred since last update
        """
        current_time = time.time()
        time_diff = current_time - self.last_sample_time
        
        # Accumulate bytes
        self.current_bytes += bytes_transferred
        
        # Check if we need to record a sample
        if time_diff >= self.sample_rate:
            # Calculate bandwidth (bytes per second)
            bandwidth = self.current_bytes / time_diff
            
            # Add to data
            self.timestamps.append(len(self.timestamps))  # Use sequence number instead of actual time
            self.values.append(bandwidth)
            
            # Reset for next sample
            self.current_bytes = 0
            self.last_sample_time = current_time
    
    def get_bandwidth_history(self):
        """Get bandwidth history for graphing
        
        Returns:
            Tuple of (timestamps, values)
        """
        return list(self.timestamps), list(self.values)
    
    def get_current_bandwidth(self):
        """Get the most recent bandwidth value
        
        Returns:
            Most recent bandwidth value in bytes per second, or 0 if no data
        """
        if not self.values:
            return 0
        return self.values[-1]
    
    def get_average_bandwidth(self):
        """Get average bandwidth over the window
        
        Returns:
            Average bandwidth in bytes per second, or 0 if no data
        """
        if not self.values:
            return 0
        return sum(self.values) / len(self.values)
