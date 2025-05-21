
"""
Constants for the application theme
"""

# Theme colors
DARK_THEME = {
    "name": "dark",
    "primary": "#121212",          # Background
    "secondary": "#1E1E1E",        # Cards
    "accent": "#BB86FC",           # Interactive elements
    "accent_hover": "#A66DF0",     # Interactive elements hover
    "text": "#FFFFFF",             # Primary text
    "text_secondary": "#B3B3B3",   # Secondary text 
    "text_tertiary": "#8E8E8E",    # Tertiary text
    "success": "#4CAF50",          # Success status
    "warning": "#FFC107",          # Warning status
    "danger": "#F44336",           # Error/danger status
    "danger_hover": "#D32F2F",     # Error/danger hover
    "border": "#303030",           # Border color
    "border_hover": "#505050",     # Border hover color
    "input_bg": "#252525",         # Input background
    "input_border": "#3C3C3C",       # Input border color
    "card": "#1E1E1E",             # Card background
    "card_hover": "#252525",       # Card hover background
    "shadow": "#000000AA",         # Shadow color
    "background": "#121212",     # Background color for widgets
    "info": "#2196F3",            # Info status
    "accent_pressed": "#3700B3",     # Interactive elements pressed
    "sidebar_bg": "#1A1A1A",       # Sidebar background
    "scrollbar": "#3C3C3C",        # Scrollbar color
    "scrollbar_hover": "#505050",  # Scrollbar hover color
    "tooltip_bg": "#303030",       # Tooltip background
    "tooltip_text": "#FFFFFF",     # Tooltip text
    "selection_bg": "#3700B3AA",   # Selection background
    "progress_bg": "#252525",      # Progress bar background
    "disabled": "#666666",         # Disabled element color
    "header_bg": "#1E1E1E",        # Header background
    "footer_bg": "#1E1E1E",        # Footer background
}

LIGHT_THEME = {
    "name": "light",
    "primary": "#FAFAFA",          # Background
    "secondary": "#F0F0F0",        # Cards
    "accent": "#6200EE",           # Interactive elements
    "accent_hover": "#3700B3",     # Interactive elements hover
    "text": "#121212",             # Primary text
    "text_secondary": "#555555",   # Secondary text
    "text_tertiary": "#777777",    # Tertiary text
    "success": "#43A047",          # Success status
    "warning": "#FB8C00",          # Warning status
    "danger": "#E53935",           # Error/danger status
    "danger_hover": "#C62828",     # Error/danger hover
    "border": "#DDDDDD",           # Border color
    "border_hover": "#AAAAAA",     # Border hover color
    "input_bg": "#FFFFFF",         # Input background
    "input_border": "#CCCCCC",     # Input border color
    "card": "#FFFFFF",             # Card background
    "card_hover": "#F5F5F5",       # Card hover background
    "shadow": "#00000044",         # Shadow color
    "background": "#FAFAFA",     # Background color for widgets
    "info": "#2196F3",            # Info status
    "accent_pressed": "#BB86FC",     # Interactive elements pressed
    "sidebar_bg": "#F5F5F5",       # Sidebar background
    "scrollbar": "#CCCCCC",        # Scrollbar color
    "scrollbar_hover": "#AAAAAA",  # Scrollbar hover color
    "tooltip_bg": "#303030",       # Tooltip background
    "tooltip_text": "#FFFFFF",     # Tooltip text
    "selection_bg": "#6200EE44",   # Selection background
    "progress_bg": "#EEEEEE",      # Progress bar background
    "disabled": "#CCCCCC",         # Disabled element color
    "header_bg": "#F0F0F0",        # Header background
    "footer_bg": "#F0F0F0",        # Footer background
}

# Get theme based on name
def get_theme(name):
    """Get theme by name"""
    if name.lower() == "dark":
        return DARK_THEME
    else:
        return LIGHT_THEME

