"""
Time-Series Forecasting for Baseball Performance Metrics.

This module implements multiple forecasting approaches for in-season projections:
- ARIMA (AutoRegressive Integrated Moving Average)
- ETS (Exponential Smoothing)
- Prophet (Facebook's forecasting tool)
- Rolling averages with trend adjustment

Applications:
- Rest-of-season WAR projections for playoff race scenarios
- Mid-season performance forecasting for trade deadline decisions
- Injury impact assessment (pre vs post)
- Breakout/slump detection via forecast errors

Key Advantages:
- Multiple model comparison for robustness
- Handles seasonality in player performance
- Uncertainty quantification (prediction intervals)
- Adaptable to various metrics (WAR, wRC+, FIP, etc.)
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Union, Literal
import warnings

try:
    from statsmodels.tsa.arima.model import ARIMA
    from statsmodels.tsa.holtwinters import ExponentialSmoothing
    from statsmodels.tsa.statespace.sarimax import SARIMAX
    import statsmodels.api as sm
    STATSMODELS_AVAILABLE = True
except ImportError:
    STATSMODELS_AVAILABLE = False
    warnings.warn("statsmodels required. Install with: pip install statsmodels")

try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False
    warnings.warn("prophet optional. Install with: pip install prophet")

try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    PLOTTING_AVAILABLE = True
except ImportError:
    PLOTTING_AVAILABLE = False


class TimeSeriesForecaster:
    """
    Forecast player performance metrics using time-series models.

    Supports multiple forecasting methods:
    - ARIMA: Handles autocorrelation and trends
    - ETS (Exponential Smoothing): Simple and effective for smooth series
    - Prophet: Handles seasonality and holidays
    - Naive baselines: Moving averages, last value carried forward

    Example:
        >>> forecaster = TimeSeriesForecaster()
        >>>
        >>> # Forecast rest-of-season WAR
        >>> war_by_game = player_df.groupby('game_date')['WAR'].sum()
        >>> forecast = forecaster.forecast_arima(
        ...     data=war_by_game,
        ...     periods=50,  # Remaining games
        ...     order=(1, 1, 1)
        ... )
        >>>
        >>> print(f"Projected season total: {forecast['point_forecast'].sum():.1f} WAR")
        >>> print(f"95% range: {forecast['lower_95'].sum():.1f} - {forecast['upper_95'].sum():.1f}")
    """

    def __init__(self, random_state: int = 42):
        """
        Initialize forecaster.

        Args:
            random_state: Random seed for reproducibility
        """
        self.random_state = random_state
        self.fitted_models = {}

    def prepare_timeseries(
        self,
        df: pd.DataFrame,
        date_col: str,
        value_col: str,
        freq: str = 'D'
    ) -> pd.Series:
        """
        Prepare time series data with proper datetime index.

        Args:
            df: DataFrame with time series data
            date_col: Column with dates
            value_col: Column with values to forecast
            freq: Frequency string ('D'=daily, 'W'=weekly, 'M'=monthly)

        Returns:
            Series with datetime index and sorted chronologically
        """
        ts = df[[date_col, value_col]].copy()
        ts[date_col] = pd.to_datetime(ts[date_col])
        ts = ts.sort_values(date_col)
        ts = ts.set_index(date_col)

        # Ensure frequency
        ts = ts.asfreq(freq)

        return ts[value_col]

    def forecast_arima(
        self,
        data: pd.Series,
        periods: int,
        order: Tuple[int, int, int] = (1, 1, 1),
        seasonal_order: Optional[Tuple[int, int, int, int]] = None,
        confidence_level: float = 0.95
    ) -> pd.DataFrame:
        """
        Forecast using ARIMA model.

        ARIMA(p,d,q):
        - p: AR order (lag dependency)
        - d: Differencing order (for stationarity)
        - q: MA order (error term dependency)

        Args:
            data: Time series to forecast (pd.Series with DatetimeIndex)
            periods: Number of periods ahead to forecast
            order: (p, d, q) for ARIMA
            seasonal_order: (P, D, Q, s) for SARIMA (optional)
            confidence_level: Confidence level for prediction intervals

        Returns:
            DataFrame with columns:
                - point_forecast: Expected value
                - lower_XX: Lower bound of confidence interval
                - upper_XX: Upper bound of confidence interval
        """
        if not STATSMODELS_AVAILABLE:
            raise ImportError("statsmodels required for ARIMA")

        # Fit model
        if seasonal_order is not None:
            model = SARIMAX(data, order=order, seasonal_order=seasonal_order)
        else:
            model = ARIMA(data, order=order)

        fitted = model.fit()
        self.fitted_models['arima'] = fitted

        # Forecast
        forecast_result = fitted.get_forecast(steps=periods)
        forecast_df = forecast_result.summary_frame(alpha=1-confidence_level)

        # Rename columns for clarity
        alpha_pct = int((1 - confidence_level) * 100)
        forecast_df = forecast_df.rename(columns={
            'mean': 'point_forecast',
            f'mean_ci_lower': f'lower_{100-alpha_pct}',
            f'mean_ci_upper': f'upper_{100-alpha_pct}'
        })

        return forecast_df[['point_forecast', f'lower_{100-alpha_pct}', f'upper_{100-alpha_pct}']]

    def forecast_ets(
        self,
        data: pd.Series,
        periods: int,
        trend: Optional[Literal['add', 'mul']] = 'add',
        seasonal: Optional[Literal['add', 'mul']] = None,
        seasonal_periods: Optional[int] = None,
        confidence_level: float = 0.95
    ) -> pd.DataFrame:
        """
        Forecast using Exponential Smoothing (ETS).

        ETS models:
        - Simple: Only level (no trend/seasonal)
        - Holt: Level + trend
        - Holt-Winters: Level + trend + seasonal

        Args:
            data: Time series to forecast
            periods: Forecast horizon
            trend: 'add', 'mul', or None
            seasonal: 'add', 'mul', or None
            seasonal_periods: Period of seasonality (e.g., 7 for weekly)
            confidence_level: Confidence level for intervals

        Returns:
            DataFrame with point forecast and intervals
        """
        if not STATSMODELS_AVAILABLE:
            raise ImportError("statsmodels required for ETS")

        # Fit model
        model = ExponentialSmoothing(
            data,
            trend=trend,
            seasonal=seasonal,
            seasonal_periods=seasonal_periods
        )
        fitted = model.fit()
        self.fitted_models['ets'] = fitted

        # Forecast
        forecast = fitted.forecast(periods)

        # Simulate prediction intervals (ETS doesn't provide them directly)
        # Use residual standard deviation
        residuals = fitted.resid
        sigma = residuals.std()

        from scipy import stats
        z_score = stats.norm.ppf((1 + confidence_level) / 2)

        forecast_df = pd.DataFrame({
            'point_forecast': forecast.values,
            f'lower_{int(confidence_level*100)}': forecast.values - z_score * sigma,
            f'upper_{int(confidence_level*100)}': forecast.values + z_score * sigma
        }, index=forecast.index)

        return forecast_df

    def forecast_prophet(
        self,
        data: pd.Series,
        periods: int,
        freq: str = 'D',
        yearly_seasonality: bool = True,
        weekly_seasonality: bool = False,
        confidence_level: float = 0.95
    ) -> pd.DataFrame:
        """
        Forecast using Facebook Prophet.

        Prophet is robust to:
        - Missing data
        - Trend changes
        - Seasonality
        - Outliers

        Great for daily/weekly data with strong seasonal patterns.

        Args:
            data: Time series to forecast
            periods: Forecast horizon
            freq: Frequency ('D', 'W', 'M')
            yearly_seasonality: Model annual seasonality
            weekly_seasonality: Model weekly seasonality
            confidence_level: Confidence interval width

        Returns:
            DataFrame with forecast and intervals
        """
        if not PROPHET_AVAILABLE:
            raise ImportError(
                "prophet required. Install with: pip install prophet"
            )

        # Prepare data for Prophet (requires 'ds' and 'y' columns)
        prophet_df = pd.DataFrame({
            'ds': data.index,
            'y': data.values
        })

        # Initialize and fit model
        model = Prophet(
            interval_width=confidence_level,
            yearly_seasonality=yearly_seasonality,
            weekly_seasonality=weekly_seasonality
        )
        model.fit(prophet_df)
        self.fitted_models['prophet'] = model

        # Create future dataframe
        future = model.make_future_dataframe(periods=periods, freq=freq)

        # Forecast
        forecast = model.predict(future)

        # Extract forecast for future periods only
        forecast_future = forecast.tail(periods)

        forecast_df = pd.DataFrame({
            'point_forecast': forecast_future['yhat'].values,
            f'lower_{int(confidence_level*100)}': forecast_future['yhat_lower'].values,
            f'upper_{int(confidence_level*100)}': forecast_future['yhat_upper'].values
        }, index=pd.date_range(
            start=data.index[-1] + pd.Timedelta(days=1),
            periods=periods,
            freq=freq
        ))

        return forecast_df

    def forecast_naive_baseline(
        self,
        data: pd.Series,
        periods: int,
        method: Literal['last', 'mean', 'rolling'] = 'last',
        window: int = 10
    ) -> pd.DataFrame:
        """
        Simple baseline forecasts for comparison.

        Methods:
        - 'last': Last value carried forward
        - 'mean': Historical mean
        - 'rolling': Rolling average of last N periods

        Args:
            data: Time series
            periods: Forecast horizon
            method: Forecasting method
            window: Window size for rolling average

        Returns:
            DataFrame with naive forecast
        """
        if method == 'last':
            forecast_value = data.iloc[-1]
        elif method == 'mean':
            forecast_value = data.mean()
        elif method == 'rolling':
            forecast_value = data.tail(window).mean()
        else:
            raise ValueError(f"Unknown method: {method}")

        # Create forecast
        future_index = pd.date_range(
            start=data.index[-1] + pd.Timedelta(days=1),
            periods=periods,
            freq=data.index.freq
        )

        forecast_df = pd.DataFrame({
            'point_forecast': [forecast_value] * periods,
            'lower_95': [np.nan] * periods,
            'upper_95': [np.nan] * periods
        }, index=future_index)

        return forecast_df

    def compare_models(
        self,
        data: pd.Series,
        test_size: int = 10,
        models: List[str] = ['arima', 'ets', 'naive']
    ) -> pd.DataFrame:
        """
        Compare multiple forecasting models using walk-forward validation.

        Splits data into train/test, forecasts test period, computes errors.

        Args:
            data: Time series
            test_size: Number of periods to hold out for testing
            models: List of models to compare

        Returns:
            DataFrame with model comparison metrics (MAE, RMSE, MAPE)
        """
        # Split data
        train = data.iloc[:-test_size]
        test = data.iloc[-test_size:]

        results = []

        for model_name in models:
            try:
                if model_name == 'arima':
                    forecast_df = self.forecast_arima(train, periods=test_size)
                elif model_name == 'ets':
                    forecast_df = self.forecast_ets(train, periods=test_size)
                elif model_name == 'prophet':
                    forecast_df = self.forecast_prophet(train, periods=test_size)
                elif model_name == 'naive':
                    forecast_df = self.forecast_naive_baseline(
                        train, periods=test_size, method='last'
                    )
                else:
                    continue

                # Align forecast with test data
                forecast_values = forecast_df['point_forecast'].values
                test_values = test.values

                # Compute error metrics
                mae = np.mean(np.abs(forecast_values - test_values))
                rmse = np.sqrt(np.mean((forecast_values - test_values) ** 2))
                mape = np.mean(np.abs((test_values - forecast_values) / test_values)) * 100

                results.append({
                    'model': model_name,
                    'mae': mae,
                    'rmse': rmse,
                    'mape': mape
                })

            except Exception as e:
                warnings.warn(f"Model {model_name} failed: {e}")
                continue

        return pd.DataFrame(results).sort_values('mae')

    def plot_forecast(
        self,
        data: pd.Series,
        forecast_df: pd.DataFrame,
        title: str = "Time Series Forecast",
        save_path: Optional[str] = None
    ):
        """
        Plot historical data with forecast and prediction intervals.

        Args:
            data: Historical time series
            forecast_df: Forecast dataframe from forecast methods
            title: Plot title
            save_path: Path to save figure (optional)
        """
        if not PLOTTING_AVAILABLE:
            raise ImportError("matplotlib required for plotting")

        fig, ax = plt.subplots(figsize=(12, 6))

        # Plot historical data
        ax.plot(data.index, data.values, 'o-', label='Historical', color='black', alpha=0.7)

        # Plot forecast
        ax.plot(
            forecast_df.index,
            forecast_df['point_forecast'],
            'o-',
            label='Forecast',
            color='blue',
            linewidth=2
        )

        # Plot confidence interval
        ci_cols = [col for col in forecast_df.columns if col.startswith('lower') or col.startswith('upper')]
        if len(ci_cols) >= 2:
            lower_col = [c for c in ci_cols if 'lower' in c][0]
            upper_col = [c for c in ci_cols if 'upper' in c][0]

            ax.fill_between(
                forecast_df.index,
                forecast_df[lower_col],
                forecast_df[upper_col],
                alpha=0.2,
                color='blue',
                label='Prediction Interval'
            )

        ax.set_xlabel('Date', fontsize=12)
        ax.set_ylabel('Value', fontsize=12)
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.legend()
        ax.grid(alpha=0.3)

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')

        plt.tight_layout()
        return fig, ax


class PlayerProjector:
    """
    Project rest-of-season performance for individual players.

    Combines time-series forecasting with contextual adjustments:
    - Aging curves
    - Park factors
    - Platoon splits
    - Injury history
    """

    def __init__(self, forecaster: Optional[TimeSeriesForecaster] = None):
        """
        Initialize player projector.

        Args:
            forecaster: TimeSeriesForecaster instance (creates new if None)
        """
        self.forecaster = forecaster or TimeSeriesForecaster()

    def project_rest_of_season(
        self,
        player_data: pd.DataFrame,
        date_col: str,
        metric_col: str,
        games_remaining: int,
        model: Literal['arima', 'ets', 'prophet', 'ensemble'] = 'ensemble'
    ) -> Dict:
        """
        Project player's rest-of-season performance.

        Args:
            player_data: Player's game-by-game data
            date_col: Date column name
            metric_col: Metric to project (e.g., 'wRC+', 'WAR', 'FIP')
            games_remaining: Number of games left in season
            model: Forecasting model to use

        Returns:
            Dictionary with projection details
        """
        # Prepare time series
        ts = self.forecaster.prepare_timeseries(
            player_data, date_col, metric_col, freq='D'
        )

        # Forecast
        if model == 'ensemble':
            # Average multiple models for robustness
            forecasts = []

            for method in ['arima', 'ets']:
                try:
                    if method == 'arima':
                        fc = self.forecaster.forecast_arima(ts, periods=games_remaining)
                    elif method == 'ets':
                        fc = self.forecaster.forecast_ets(ts, periods=games_remaining)

                    forecasts.append(fc['point_forecast'].values)
                except:
                    continue

            if len(forecasts) > 0:
                ensemble_forecast = np.mean(forecasts, axis=0)
                forecast_df = pd.DataFrame({
                    'point_forecast': ensemble_forecast,
                    'lower_95': np.percentile(forecasts, 2.5, axis=0),
                    'upper_95': np.percentile(forecasts, 97.5, axis=0)
                })
            else:
                # Fallback to naive
                forecast_df = self.forecaster.forecast_naive_baseline(
                    ts, periods=games_remaining
                )
        else:
            if model == 'arima':
                forecast_df = self.forecaster.forecast_arima(ts, periods=games_remaining)
            elif model == 'ets':
                forecast_df = self.forecaster.forecast_ets(ts, periods=games_remaining)
            elif model == 'prophet':
                forecast_df = self.forecaster.forecast_prophet(ts, periods=games_remaining)

        # Aggregate projections
        current_total = ts.sum()
        projected_total = current_total + forecast_df['point_forecast'].sum()
        projected_lower = current_total + forecast_df[[c for c in forecast_df.columns if 'lower' in c]].values.sum()
        projected_upper = current_total + forecast_df[[c for c in forecast_df.columns if 'upper' in c]].values.sum()

        return {
            'current_total': float(current_total),
            'projected_addition': float(forecast_df['point_forecast'].sum()),
            'projected_season_total': float(projected_total),
            'projection_lower': float(projected_lower),
            'projection_upper': float(projected_upper),
            'forecast_detail': forecast_df
        }
