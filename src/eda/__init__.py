"""SkyGuard AI Exploratory Data Analysis (EDA) Package."""

from .quality import analyze_data_quality
from .statistics import calculate_sensor_statistics, calculate_station_statistics
from .temporal import analyze_sampling_intervals, analyze_temporal_patterns
from .station import analyze_stations, analyze_cross_station
from .correlations import analyze_correlations
from .suspicious import identify_potentially_suspicious
from .plots import generate_all_eda_plots

__all__ = [
    "analyze_data_quality",
    "calculate_sensor_statistics",
    "calculate_station_statistics",
    "analyze_sampling_intervals",
    "analyze_temporal_patterns",
    "analyze_stations",
    "analyze_cross_station",
    "analyze_correlations",
    "identify_potentially_suspicious",
    "generate_all_eda_plots",
]
