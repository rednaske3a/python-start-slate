
"""
Bandwidth graph widget for displaying download speeds
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt
import pyqtgraph as pg
import numpy as np

from src.utils.formatting import format_size

class BandwidthGraph(QWidget):
    """Bandwidth graph widget for displaying download speeds"""
    
    def __init__(self, theme, parent=None):
        """Initialize bandwidth graph widget"""
        super().__init__(parent)
        self.theme = theme
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI components"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create title label
        self.title_label = QLabel("Bandwidth Usage")
        self.title_label.setStyleSheet(f"""
            font-size: 14px;
            font-weight: bold;
            color: {self.theme['text']};
        """)
        
        # Create current bandwidth label
        self.bandwidth_label = QLabel("0 B/s")
        self.bandwidth_label.setAlignment(Qt.AlignCenter)
        self.bandwidth_label.setStyleSheet(f"""
            font-size: 16px;
            font-weight: bold;
            color: {self.theme['accent']};
            margin-bottom: 8px;
        """)
        
        # Create graph widget
        pg.setConfigOptions(antialias=True)
        self.graph_widget = pg.PlotWidget()
        
        # Configure graph appearance
        self.graph_widget.setBackground(self.theme["secondary"])
        self.graph_widget.showGrid(x=True, y=True, alpha=0.3)
        
        # Create plot items
        self.plot = self.graph_widget.plot(
            [], [], 
            pen=pg.mkPen(color=self.theme["accent"], width=2)
        )
        
        # Set axis labels
        self.graph_widget.setLabel('left', 'Speed', 'B/s')
        self.graph_widget.setLabel('bottom', 'Time', 's')
        
        # Set axis colors
        axis_pen = pg.mkPen(color=self.theme["text_secondary"])
        for axis in [self.graph_widget.getAxis('left'), self.graph_widget.getAxis('bottom')]:
            axis.setPen(axis_pen)
            axis.setTextPen(axis_pen)
        
        # Add widgets to layout
        layout.addWidget(self.title_label)
        layout.addWidget(self.bandwidth_label)
        layout.addWidget(self.graph_widget)
        
    def update_data(self, times, values):
        """Update graph with new data"""
        if not times or not values:
            return
            
        # Convert bytes/s to appropriate unit for better visualization
        if values and max(values) > 0:
            # Use current bandwidth for label
            current_bw = values[-1] if values else 0
            self.bandwidth_label.setText(f"{format_size(current_bw)}/s")
            
            # Update plot data
            self.plot.setData(times, values)
            
            # Update y axis range with some padding
            max_value = max(values) * 1.1  # 10% padding
            self.graph_widget.setYRange(0, max_value)
    
    def set_theme(self, theme):
        """Update the theme"""
        self.theme = theme
        
        # Update styles
        self.title_label.setStyleSheet(f"""
            font-size: 14px;
            font-weight: bold;
            color: {self.theme['text']};
        """)
        
        self.bandwidth_label.setStyleSheet(f"""
            font-size: 16px;
            font-weight: bold;
            color: {self.theme['accent']};
            margin-bottom: 8px;
        """)
        
        # Update graph appearance
        self.graph_widget.setBackground(self.theme["secondary"])
        self.plot.setPen(pg.mkPen(color=self.theme["accent"], width=2))
        
        # Update axis colors
        axis_pen = pg.mkPen(color=self.theme["text_secondary"])
        for axis in [self.graph_widget.getAxis('left'), self.graph_widget.getAxis('bottom')]:
            axis.setPen(axis_pen)
            axis.setTextPen(axis_pen)
    
    def clear(self):
        """Clear the graph"""
        self.plot.clear()
        self.bandwidth_label.setText("0 B/s")
