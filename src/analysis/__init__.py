"""Analysis utilities and metrics."""
from .metrics import (
    calculate_woba,
    calculate_barrel_rate,
    calculate_hard_hit_rate,
    calculate_whiff_rate,
    calculate_chase_rate,
    calculate_zone_contact_rate,
    calculate_expected_stats,
    get_pitch_arsenal_summary,
    calculate_plate_discipline_metrics,
    calculate_batted_ball_profile
)

from .visualizations import (
    plot_pitch_location,
    plot_pitch_movement,
    plot_exit_velo_distribution,
    plot_spray_chart,
    plot_rolling_metric,
    plot_comparison_radar
)

from .breakout_detector import BreakoutDetector
from .free_agent_analyzer import FreeAgentAnalyzer
from .aging_curves import AgingCurveAnalyzer

# Player similarity
try:
    from .player_similarity import PlayerSimilarityFinder
    SIMILARITY_AVAILABLE = True
except ImportError:
    SIMILARITY_AVAILABLE = False
    PlayerSimilarityFinder = None

# Pitch clustering
try:
    from .pitch_clustering import PitchArsenalClusterer
    CLUSTERING_AVAILABLE = True
except ImportError:
    CLUSTERING_AVAILABLE = False
    PitchArsenalClusterer = None

# Causal inference (optional - requires statsmodels)
try:
    from .causal_inference import (
        PropensityScoreAnalyzer,
        DifferenceInDifferences,
        RegressionDiscontinuity,
        DoublyRobustEstimator
    )
    CAUSAL_AVAILABLE = True
except ImportError:
    CAUSAL_AVAILABLE = False
    PropensityScoreAnalyzer = None
    DifferenceInDifferences = None
    RegressionDiscontinuity = None
    DoublyRobustEstimator = None

__all__ = [
    # Metrics
    'calculate_woba',
    'calculate_barrel_rate',
    'calculate_hard_hit_rate',
    'calculate_whiff_rate',
    'calculate_chase_rate',
    'calculate_zone_contact_rate',
    'calculate_expected_stats',
    'get_pitch_arsenal_summary',
    'calculate_plate_discipline_metrics',
    'calculate_batted_ball_profile',
    # Visualizations
    'plot_pitch_location',
    'plot_pitch_movement',
    'plot_exit_velo_distribution',
    'plot_spray_chart',
    'plot_rolling_metric',
    'plot_comparison_radar',
    # Core Analyzers
    'BreakoutDetector',
    'FreeAgentAnalyzer',
    'AgingCurveAnalyzer',
    # Player Comparison
    'PlayerSimilarityFinder',
    'PitchArsenalClusterer',
    # Causal Inference
    'PropensityScoreAnalyzer',
    'DifferenceInDifferences',
    'RegressionDiscontinuity',
    'DoublyRobustEstimator'
]
