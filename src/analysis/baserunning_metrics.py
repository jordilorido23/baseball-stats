"""
Baserunning Metrics and Analysis for Position Players.

Extracts and analyzes baserunning value from FanGraphs data:
- BsR (Baserunning Runs) - Total baserunning value
- wSB (weighted Stolen Base Runs) - Stolen base value
- UBR (Ultimate Base Running) - Advancement/extra bases taken
- Sprint Speed - Raw speed metric from Statcast

Baserunning contributes 0.5-2.0 WAR for elite runners.

Created: November 13, 2025
Author: Baseball Analytics Portfolio
"""
import pandas as pd
import numpy as np
from typing import Dict, Optional, Literal


class BaserunningMetrics:
    """
    Analyze baserunning contributions to player value.

    Uses FanGraphs baserunning stats and Statcast sprint speed.
    """

    def __init__(self):
        """Initialize baserunning analyzer."""
        # Baserunning value thresholds (runs per season)
        self.value_thresholds = {
            'elite': 5.0,      # +5 runs = elite baserunner
            'good': 2.0,       # +2 runs = above average
            'average': -1.0,   # 0 runs = average
            'poor': -3.0,      # -3 runs = poor
        }

        # Sprint speed thresholds (ft/s)
        self.speed_thresholds = {
            'elite': 30.0,     # 30+ ft/s = elite speed
            'above_avg': 28.0, # 28-30 ft/s = above average
            'average': 27.0,   # 27-28 ft/s = average
            'below_avg': 26.0, # 26-27 ft/s = below average
        }

    def extract_baserunning_stats(
        self,
        batting_stats: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Extract baserunning metrics from FanGraphs batting stats.

        Args:
            batting_stats: FanGraphs batting stats DataFrame

        Returns:
            DataFrame with baserunning columns
        """
        baserunning_cols = [
            'Name', 'playerid',
            'BsR',    # Total baserunning runs
            'wSB',    # Weighted stolen base runs
            'UBR',    # Ultimate base running (non-SB advancement)
            'wGDP',   # Grounded into double play runs
            'SB',     # Stolen bases (counting stat)
            'CS',     # Caught stealing (counting stat)
        ]

        # Filter to columns that exist
        available_cols = [col for col in baserunning_cols if col in batting_stats.columns]

        if len(available_cols) < 3:
            print("Warning: FanGraphs data missing baserunning columns")
            return pd.DataFrame()

        baserunning_data = batting_stats[available_cols].copy()

        # Calculate SB success rate if SB/CS available
        if 'SB' in baserunning_data.columns and 'CS' in baserunning_data.columns:
            baserunning_data['SB_attempts'] = baserunning_data['SB'] + baserunning_data['CS']
            baserunning_data['SB_success_rate'] = np.where(
                baserunning_data['SB_attempts'] > 0,
                baserunning_data['SB'] / baserunning_data['SB_attempts'],
                np.nan
            )

        return baserunning_data

    def categorize_baserunners(
        self,
        baserunning_stats: pd.DataFrame,
        metric: str = 'BsR'
    ) -> pd.DataFrame:
        """
        Categorize players by baserunning value.

        Args:
            baserunning_stats: DataFrame with baserunning metrics
            metric: Metric to use for categorization ('BsR', 'wSB', 'UBR')

        Returns:
            DataFrame with baserunning categories added
        """
        result = baserunning_stats.copy()

        if metric not in result.columns:
            print(f"Warning: {metric} not found in baserunning stats")
            return result

        # Categorize baserunning value
        bins = [-100, -3, -1, 2, 5, 100]
        labels = ['Poor', 'Below Avg', 'Average', 'Above Avg', 'Elite']

        result[f'{metric}_category'] = pd.cut(
            result[metric],
            bins=bins,
            labels=labels
        )

        return result

    def add_sprint_speed_categories(
        self,
        baserunning_stats: pd.DataFrame,
        sprint_speed_col: str = 'sprint_speed'
    ) -> pd.DataFrame:
        """
        Add sprint speed categories to baserunning data.

        Args:
            baserunning_stats: DataFrame with sprint speed
            sprint_speed_col: Column name for sprint speed

        Returns:
            DataFrame with speed categories
        """
        result = baserunning_stats.copy()

        if sprint_speed_col not in result.columns:
            return result

        # Categorize sprint speed
        bins = [0, 26, 27, 28, 30, 35]
        labels = ['Below Avg', 'Average', 'Above Avg', 'Elite', 'World Class']

        result['speed_category'] = pd.cut(
            result[sprint_speed_col],
            bins=bins,
            labels=labels
        )

        return result

    def calculate_baserunning_war_contribution(
        self,
        bsr_value: float,
        runs_per_win: float = 10.0
    ) -> float:
        """
        Convert baserunning runs to WAR contribution.

        Args:
            bsr_value: Baserunning runs (BsR)
            runs_per_win: Runs per win conversion factor

        Returns:
            WAR contribution from baserunning
        """
        return bsr_value / runs_per_win

    def project_baserunning_decline(
        self,
        current_bsr: float,
        current_speed: float,
        age: int,
        years_ahead: int = 3
    ) -> Dict:
        """
        Project baserunning decline based on age and speed.

        Speed declines ~0.1-0.2 ft/s per year after age 30.

        Args:
            current_bsr: Current baserunning runs
            current_speed: Current sprint speed
            age: Player's current age
            years_ahead: Years to project

        Returns:
            Dictionary with projections
        """
        projections = {}

        # Speed decline rate (ft/s per year)
        if age < 30:
            decline_rate = 0.05  # Minimal decline
        elif age < 33:
            decline_rate = 0.15  # Moderate decline
        else:
            decline_rate = 0.25  # Steep decline

        for year in range(1, years_ahead + 1):
            projected_age = age + year
            projected_speed = current_speed - (decline_rate * year)

            # Baserunning value declines proportionally to speed
            speed_ratio = projected_speed / current_speed if current_speed > 0 else 0
            projected_bsr = current_bsr * speed_ratio

            projections[f'year_{year}'] = {
                'age': projected_age,
                'sprint_speed': round(projected_speed, 1),
                'bsr': round(projected_bsr, 1),
                'baserunning_war': round(self.calculate_baserunning_war_contribution(projected_bsr), 2)
            }

        return projections

    def identify_elite_baserunners(
        self,
        baserunning_stats: pd.DataFrame,
        min_bsr: float = 3.0,
        min_sprint_speed: float = 28.0
    ) -> pd.DataFrame:
        """
        Identify elite baserunners (combine value + speed).

        Args:
            baserunning_stats: DataFrame with baserunning metrics
            min_bsr: Minimum BsR value
            min_sprint_speed: Minimum sprint speed

        Returns:
            DataFrame of elite baserunners
        """
        # Filter for elite metrics
        elite = baserunning_stats[
            (baserunning_stats.get('BsR', 0) >= min_bsr) |
            (baserunning_stats.get('sprint_speed', 0) >= min_sprint_speed)
        ].copy()

        # Sort by BsR value
        if 'BsR' in elite.columns:
            elite = elite.sort_values('BsR', ascending=False)

        return elite

    def combine_with_defensive_speed(
        self,
        baserunning_stats: pd.DataFrame,
        defensive_stats: pd.DataFrame,
        merge_col: str = 'Name'
    ) -> pd.DataFrame:
        """
        Combine baserunning and defensive metrics.

        Speed affects both offensive (baserunning) and defensive (range) value.

        Args:
            baserunning_stats: Baserunning metrics
            defensive_stats: Defensive metrics
            merge_col: Column to merge on

        Returns:
            Combined DataFrame
        """
        combined = baserunning_stats.merge(
            defensive_stats,
            on=merge_col,
            how='outer',
            suffixes=('_br', '_def')
        )

        # Calculate total speed-based value (baserunning + defense)
        if 'BsR' in combined.columns and 'Def' in combined.columns:
            combined['total_speed_value'] = (
                combined['BsR'].fillna(0) +
                combined['Def'].fillna(0)
            )

        return combined

    def rank_baserunners(
        self,
        baserunning_stats: pd.DataFrame,
        metric: str = 'BsR',
        top_n: int = 50
    ) -> pd.DataFrame:
        """
        Rank players by baserunning value.

        Args:
            baserunning_stats: DataFrame with baserunning metrics
            metric: Metric to rank by
            top_n: Number of players to return

        Returns:
            Ranked DataFrame
        """
        if metric not in baserunning_stats.columns:
            print(f"Warning: {metric} not found")
            return pd.DataFrame()

        ranked = baserunning_stats.sort_values(metric, ascending=False).head(top_n)

        return ranked.reset_index(drop=True)
