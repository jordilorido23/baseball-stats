"""Predictive models for baseball analytics."""
from .prospect_predictor import ProspectPredictor

# Time-series forecasting
try:
    from .timeseries_forecaster import TimeSeriesForecaster, PlayerProjector
    TIMESERIES_AVAILABLE = True
except ImportError:
    TIMESERIES_AVAILABLE = False
    TimeSeriesForecaster = None
    PlayerProjector = None

# Ensemble models
try:
    from .ensemble_models import EnsembleProspectPredictor, ModelCalibrator
    ENSEMBLE_AVAILABLE = True
except ImportError:
    ENSEMBLE_AVAILABLE = False
    EnsembleProspectPredictor = None
    ModelCalibrator = None

# Advanced statistical models (optional imports - require additional dependencies)
try:
    from .bayesian_prospect_model import BayesianProspectModel
    BAYESIAN_AVAILABLE = True
except ImportError:
    BAYESIAN_AVAILABLE = False
    BayesianProspectModel = None

try:
    from .survival_models import CareerSurvivalAnalyzer, ContractRiskAnalyzer
    SURVIVAL_AVAILABLE = True
except ImportError:
    SURVIVAL_AVAILABLE = False
    CareerSurvivalAnalyzer = None
    ContractRiskAnalyzer = None

__all__ = [
    # Core ML models
    'ProspectPredictor',
    'EnsembleProspectPredictor',
    'ModelCalibrator',
    # Time-series
    'TimeSeriesForecaster',
    'PlayerProjector',
    # Advanced statistical models
    'BayesianProspectModel',
    'CareerSurvivalAnalyzer',
    'ContractRiskAnalyzer'
]
