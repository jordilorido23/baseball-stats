"""
Configuration file for baseball analytics project.
Customize these settings for your analysis needs.
"""
from datetime import datetime, timedelta

# Data directories
DATA_DIR = "data"
CACHE_DIR = "data/cache"

# Default date ranges for analysis
DEFAULT_START_DATE = "2025-03-20"  # Start of 2025 season
DEFAULT_END_DATE = datetime.now().strftime("%Y-%m-%d")  # Today

# Cache settings
CACHE_MAX_AGE_DAYS = 1  # How long to keep cached data (in days)
MILB_CACHE_MAX_AGE_DAYS = 7  # MiLB data updates less frequently

# Default season for analysis
CURRENT_SEASON = 2025

# Minor league levels
MILB_LEVELS = ["AAA", "AA", "A+", "A", "Rk"]

# Visualization settings
PLOT_STYLE = "seaborn-v0_8-darkgrid"
FIGURE_SIZE = (12, 8)
DPI = 100

# Statistical thresholds
MIN_PLATE_APPEARANCES = 50  # Minimum PA for batter analysis
MIN_BATTERS_FACED = 50  # Minimum BF for pitcher analysis
MIN_PITCHES = 100  # Minimum pitches for pitch-level analysis

# Team colors (for visualizations)
MLB_TEAM_COLORS = {
    'NYY': '#003087',
    'BOS': '#BD3039',
    'LAD': '#005A9C',
    'SF': '#FD5A1E',
    # Add more as needed
}

# Analysis parameters
ROLLING_WINDOW = 10  # Games for rolling averages
PERCENTILE_THRESHOLDS = {
    'elite': 90,
    'above_average': 75,
    'average': 50,
    'below_average': 25,
    'poor': 10
}
