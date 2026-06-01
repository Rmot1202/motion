# Configuration file for Thermocouple Dashboard
# Device settings
DEVICE_NAME = "MCC E-TC-001"
DEFAULT_FURNACE_NUMBER = 1
DEVICE_IP = "192.168.10.101"   # Set to device IP if known

# Default bounds
DEFAULT_SETPOINT = 75.0
DEFAULT_LOWER_BOUND = 70.0
DEFAULT_UPPER_BOUND = 80.0
DEFAULT_Y_MIN = 60
DEFAULT_Y_MAX = 90

# Data sampling
DEFAULT_SAMPLING_FREQUENCY = 1  # Hz
GRAPH_WINDOW_SECONDS = 300  # Show the last 5 minutes of data

# TUS text output
DEFAULT_OUTPUT_DIRECTORY = "./recordings"
LABVIEW_OUTPUT_CHANNELS = 3

# UI settings
POLLING_INTERVAL = 1000  # milliseconds
GRAPH_HEIGHT = 400  # pixels

# Color scheme for channels
CHANNEL_COLORS = {
    1: "#1f77b4",  # Blue
    2: "#d62728",  # Red
    3: "#ff00ff",  # Magenta
}

# Reference line colors
SETPOINT_COLOR = "red"
LOWER_BOUND_COLOR = "orange"
UPPER_BOUND_COLOR = "purple"
