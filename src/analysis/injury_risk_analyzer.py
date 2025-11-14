"""
Injury Risk Analysis for Free Agents using Biomechanical Signals.

This module goes BEYOND standard aging curves by identifying injury risk signals:
- Velocity decline trends (pitchers)
- Exit velocity decline trends (hitters)
- Workload stress indicators
- Pitch mix evolution (compensation patterns)
- Sprint speed decline (soft tissue risk)
- HISTORICAL INJURY DATA (best predictor of future injuries)

Output: Injury-adjusted contract valuations with risk premiums.

Created: November 13, 2025
Updated: November 13, 2025 - Added historical injury tracking
Author: Baseball Analytics Portfolio
"""
import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# Import injury history fetcher
try:
    from ..data.injury_fetcher import InjuryFetcher
except ImportError:
    InjuryFetcher = None


class InjuryRiskAnalyzer:
    """
    Analyze injury risk for free agents using biomechanical signals.

    Goes beyond simple aging curves to quantify injury probability based on:
    - Performance trend deterioration
    - Workload accumulation
    - Velocity/exit velo declines
    """

    def __init__(self, injury_history_csv: Optional[str] = None):
        """
        Initialize injury risk analyzer.

        Args:
            injury_history_csv: Path to CSV with historical injury data (optional)
        """
        # Risk thresholds (based on literature and historical data)
        self.risk_thresholds = {
            'pitcher_velo_decline_mph': -2.0,      # 2+ mph decline = high risk
            'batter_exit_velo_decline_mph': -1.5,   # 1.5+ mph decline = high risk
            'pitcher_workload_ip': 650,             # 650+ IP over 3 years = fatigue risk
            'batter_sprint_speed_decline_fps': -0.5, # 0.5+ ft/s decline = injury risk
            'pitcher_k_rate_decline_pct': -5.0,     # 5+ point K% drop = stuff decline
        }

        # Initialize injury history fetcher if available
        self.injury_fetcher = InjuryFetcher() if InjuryFetcher else None
        self.injury_history = None

        # Load injury history if CSV provided
        if injury_history_csv and self.injury_fetcher:
            self.injury_history = self.injury_fetcher.load_injury_history_from_csv(
                injury_history_csv
            )

    def calculate_pitcher_injury_risk(
        self,
        pitcher_data: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Calculate injury risk score for pitchers.

        Risk signals:
        1. Velocity decline (2+ mph over 3 years)
        2. High workload (650+ IP cumulative)
        3. K% decline (stuff deterioration)
        4. Age (older = higher baseline risk)

        Args:
            pitcher_data: DataFrame with pitcher stats and trends

        Returns:
            DataFrame with injury risk scores added
        """
        result = pitcher_data.copy()
        result['injury_risk_score'] = 0.0
        result['injury_risk_factors'] = ''

        for idx, pitcher in result.iterrows():
            risk_score = 0
            risk_factors = []

            # Factor 1: Velocity decline
            velo_trend = pitcher.get('fastball_velo_trend_mph', 0)
            if pd.notna(velo_trend):
                if velo_trend <= self.risk_thresholds['pitcher_velo_decline_mph']:
                    risk_score += 30
                    risk_factors.append(f"Velo decline {velo_trend:.1f} mph")
                elif velo_trend <= -1.0:
                    risk_score += 15
                    risk_factors.append(f"Moderate velo decline {velo_trend:.1f} mph")

            # Factor 2: Workload
            cumulative_ip = pitcher.get('cumulative_ip_3yr', 0)
            if pd.notna(cumulative_ip):
                if cumulative_ip >= self.risk_thresholds['pitcher_workload_ip']:
                    risk_score += 20
                    risk_factors.append(f"High workload {cumulative_ip:.0f} IP")
                elif cumulative_ip >= 550:
                    risk_score += 10
                    risk_factors.append(f"Moderate workload {cumulative_ip:.0f} IP")

            # Factor 3: K% decline (stuff degradation)
            k_trend = pitcher.get('k_rate_trend_pct', 0)
            if pd.notna(k_trend):
                if k_trend <= self.risk_thresholds['pitcher_k_rate_decline_pct']:
                    risk_score += 25
                    risk_factors.append(f"K% decline {k_trend:.1f}%")
                elif k_trend <= -2.5:
                    risk_score += 10
                    risk_factors.append(f"Moderate K% decline {k_trend:.1f}%")

            # Factor 4: Age (35+ = elevated baseline risk)
            age = pitcher.get('Age', pitcher.get('age_2025', 30))
            if age >= 40:
                risk_score += 20
                risk_factors.append(f"Age {age}")
            elif age >= 35:
                risk_score += 20
                risk_factors.append(f"Age {age}")
            elif age >= 33:
                risk_score += 8
                risk_factors.append(f"Age {age}")

            # Factor 5: Previous injury history (if available in data)
            war_2025 = pitcher.get('2025_war', 0)
            if pd.notna(war_2025) and war_2025 < 0:
                risk_score += 25
                risk_factors.append("Negative WAR (injury/ineffective)")

            result.at[idx, 'injury_risk_score'] = risk_score
            result.at[idx, 'injury_risk_factors'] = '; '.join(risk_factors) if risk_factors else 'None'

        # Classify risk levels
        result['injury_risk_category'] = pd.cut(
            result['injury_risk_score'],
            bins=[-1, 20, 40, 60, 100],
            labels=['Low', 'Moderate', 'High', 'Very High']
        )

        return result

    def calculate_batter_injury_risk(
        self,
        batter_data: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Calculate injury risk score for batters.

        Risk signals:
        1. Exit velocity decline (1.5+ mph over 3 years)
        2. Sprint speed decline (0.5+ ft/s decline)
        3. Barrel rate decline
        4. Age (older = higher baseline risk)

        Args:
            batter_data: DataFrame with batter stats and trends

        Returns:
            DataFrame with injury risk scores added
        """
        result = batter_data.copy()
        result['injury_risk_score'] = 0.0
        result['injury_risk_factors'] = ''

        for idx, batter in result.iterrows():
            risk_score = 0
            risk_factors = []

            # Factor 1: Exit velocity decline (bat speed / strength decline)
            ev_trend = batter.get('exit_velo_trend_mph', 0)
            if pd.notna(ev_trend):
                if ev_trend <= self.risk_thresholds['batter_exit_velo_decline_mph']:
                    risk_score += 25
                    risk_factors.append(f"Exit velo decline {ev_trend:.1f} mph")
                elif ev_trend <= -0.8:
                    risk_score += 12
                    risk_factors.append(f"Moderate exit velo decline {ev_trend:.1f} mph")

            # Factor 2: Sprint speed decline (soft tissue risk indicator)
            speed_trend = batter.get('sprint_speed_decline_fps', batter.get('sprint_speed_trend_fps', 0))
            if pd.notna(speed_trend):
                if speed_trend <= self.risk_thresholds['batter_sprint_speed_decline_fps']:
                    risk_score += 20
                    risk_factors.append(f"Sprint speed decline {speed_trend:.1f} ft/s")
                elif speed_trend <= -0.3:
                    risk_score += 10
                    risk_factors.append(f"Moderate speed decline {speed_trend:.1f} ft/s")

            # Factor 3: Barrel rate decline (bat speed / contact quality)
            barrel_trend = batter.get('barrel_rate_trend_pct', 0)
            if pd.notna(barrel_trend):
                if barrel_trend <= -3.0:
                    risk_score += 20
                    risk_factors.append(f"Barrel rate decline {barrel_trend:.1f}%")
                elif barrel_trend <= -1.5:
                    risk_score += 10
                    risk_factors.append(f"Moderate barrel decline {barrel_trend:.1f}%")

            # Factor 4: Age (33+ = elevated risk for position players)
            age = batter.get('Age', batter.get('age_2025', 30))
            if age >= 36:
                risk_score += 15
                risk_factors.append(f"Age {age}")
            elif age >= 33:
                risk_score += 8
                risk_factors.append(f"Age {age}")

            # Factor 5: Negative WAR (injury/ineffective season)
            war_2025 = batter.get('2025_war', 0)
            if pd.notna(war_2025) and war_2025 < 0:
                risk_score += 20
                risk_factors.append("Negative WAR (injury/ineffective)")

            result.at[idx, 'injury_risk_score'] = risk_score
            result.at[idx, 'injury_risk_factors'] = '; '.join(risk_factors) if risk_factors else 'None'

        # Classify risk levels
        result['injury_risk_category'] = pd.cut(
            result['injury_risk_score'],
            bins=[-1, 20, 40, 60, 100],
            labels=['Low', 'Moderate', 'High', 'Very High']
        )

        return result

    def apply_injury_risk_discount(
        self,
        player_data: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Apply injury risk discount to contract values.

        Args:
            player_data: DataFrame with injury_risk_score and base_contract_value_millions columns

        Returns:
            DataFrame with injury_adjusted_value_millions column added
        """
        result = player_data.copy()

        # Ensure we have necessary columns
        if 'base_contract_value_millions' not in result.columns:
            raise ValueError("DataFrame must have 'base_contract_value_millions' column")

        if 'injury_risk_score' not in result.columns:
            raise ValueError("DataFrame must have 'injury_risk_score' column")

        # Calculate discount percentage based on risk score
        def calculate_discount(risk_score):
            if risk_score < 20:  # Low risk
                return 0.0
            elif risk_score < 40:  # Moderate risk
                return 0.10
            elif risk_score < 60:  # High risk
                return 0.25
            else:  # Very High risk (60+)
                return 0.40

        result['injury_discount_pct'] = result['injury_risk_score'].apply(calculate_discount)

        # Apply discount to contract value
        result['injury_adjusted_value_millions'] = (
            result['base_contract_value_millions'] * (1 - result['injury_discount_pct'])
        )

        return result

    def add_injury_history_risk(
        self,
        fa_data: pd.DataFrame,
        player_name_col: str = 'player_name',
        lookback_years: int = 3
    ) -> pd.DataFrame:
        """
        Add injury history risk scores to free agent data.

        Historical injuries are the BEST predictor of future injury risk.

        Args:
            fa_data: Free agent data
            player_name_col: Column with player names
            lookback_years: Years of injury history to consider

        Returns:
            DataFrame with injury history risk scores added
        """
        if self.injury_history is None or self.injury_fetcher is None:
            print("Warning: No injury history data loaded")
            fa_data['injury_history_score'] = 0
            return fa_data

        result = fa_data.copy()

        # Get injury metrics for all FAs
        player_names = result[player_name_col].unique().tolist()
        injury_metrics = self.injury_fetcher.calculate_injury_metrics_for_multiple_players(
            self.injury_history,
            player_names,
            lookback_years=lookback_years
        )

        # Merge injury metrics
        result = result.merge(
            injury_metrics[[
                'player_name', 'total_il_stints', 'total_days_missed',
                'major_injuries', 'recurrent_injuries', 'injury_score',
                'injury_risk_level', 'most_recent_injury'
            ]],
            left_on=player_name_col,
            right_on='player_name',
            how='left',
            suffixes=('', '_injury_history')
        )

        # Fill missing values (no injury history = 0 risk from history)
        result['injury_score'] = result['injury_score'].fillna(0)
        result['total_il_stints'] = result['total_il_stints'].fillna(0)
        result['total_days_missed'] = result['total_days_missed'].fillna(0)
        result['major_injuries'] = result['major_injuries'].fillna(0)

        # Convert injury score to risk points (scale to match other risk factors)
        # Injury score of 10+ = 40 risk points (very high)
        result['injury_history_risk_points'] = result['injury_score'].apply(
            lambda x: min(x * 4, 50)  # Cap at 50 points
        )

        return result

    def calculate_combined_injury_risk(
        self,
        fa_data: pd.DataFrame,
        include_history: bool = True
    ) -> pd.DataFrame:
        """
        Calculate combined injury risk from biomechanical signals + history.

        Args:
            fa_data: Free agent data with risk scores
            include_history: Whether to include injury history in risk

        Returns:
            DataFrame with combined risk scores
        """
        result = fa_data.copy()

        # Get existing injury risk score (biomechanical)
        biomech_risk = result.get('injury_risk_score', 0)

        # Add injury history risk if available
        if include_history and 'injury_history_risk_points' in result.columns:
            combined_risk = biomech_risk + result['injury_history_risk_points']
        else:
            combined_risk = biomech_risk

        result['combined_injury_risk_score'] = combined_risk

        # Re-categorize with combined score
        result['combined_injury_risk_category'] = pd.cut(
            result['combined_injury_risk_score'],
            bins=[-1, 20, 40, 70, 150],
            labels=['Low', 'Moderate', 'High', 'Very High']
        )

        return result

    def calculate_injury_adjusted_war(
        self,
        fa_data: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Adjust WAR projections for injury risk.

        High injury risk = apply discount to projected WAR.

        Args:
            fa_data: FA data with injury risk scores

        Returns:
            DataFrame with injury-adjusted WAR projections
        """
        result = fa_data.copy()

        # Calculate risk discount factor
        # Low risk = 0% discount
        # Moderate = 10% discount
        # High = 25% discount
        # Very High = 40% discount
        risk_discounts = {
            'Low': 0.00,
            'Moderate': 0.10,
            'High': 0.25,
            'Very High': 0.40
        }

        result['injury_risk_discount'] = result['injury_risk_category'].astype(str).map(risk_discounts).fillna(0)

        # Apply discount to 2025 WAR for projection
        result['injury_adjusted_war'] = result['2025_war'] * (1 - result['injury_risk_discount'])

        # Calculate expected games lost due to injury
        # Very High risk = expect 40+ games lost
        # High risk = 25 games
        # Moderate = 10 games
        # Low = 5 games
        games_lost_map = {
            'Very High': 40,
            'High': 25,
            'Moderate': 10,
            'Low': 5
        }

        result['expected_games_lost'] = result['injury_risk_category'].astype(str).map(games_lost_map).fillna(5)

        return result

    def generate_injury_risk_report(
        self,
        player_name: str,
        fa_data: pd.DataFrame
    ) -> Dict:
        """
        Generate detailed injury risk report for a specific player.

        Args:
            player_name: Player name
            fa_data: FA data with injury metrics

        Returns:
            Dictionary with injury risk analysis
        """
        player = fa_data[fa_data['player_name'] == player_name]

        if len(player) == 0:
            return {'error': f'Player {player_name} not found'}

        player = player.iloc[0]

        report = {
            'player_name': player_name,
            'position': player.get('position', 'N/A'),
            'age': player.get('age_2025', 'N/A'),
            'injury_risk_score': player.get('injury_risk_score', 0),
            'injury_risk_category': player.get('injury_risk_category', 'Unknown'),
            'injury_risk_factors': player.get('injury_risk_factors', 'None'),
            'injury_risk_discount': f"{player.get('injury_risk_discount', 0) * 100:.0f}%",
            'expected_games_lost': player.get('expected_games_lost', 'N/A'),
            '2025_war': player.get('2025_war', 'N/A'),
            'injury_adjusted_war': player.get('injury_adjusted_war', 'N/A')
        }

        # Add position-specific metrics
        if player.get('position') in ['SP', 'RP']:
            report['velocity_trend'] = player.get('fastball_velo_trend_mph', 'N/A')
            report['cumulative_ip_3yr'] = player.get('cumulative_ip_3yr', 'N/A')
            report['k_rate_trend'] = player.get('k_rate_trend_pct', 'N/A')
        else:
            report['exit_velo_trend'] = player.get('exit_velo_trend_mph', 'N/A')
            report['sprint_speed_trend'] = player.get('sprint_speed_trend_fps', 'N/A')
            report['barrel_rate_trend'] = player.get('barrel_rate_trend_pct', 'N/A')

        return report

    def rank_by_injury_risk(
        self,
        fa_data: pd.DataFrame,
        position_filter: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Rank free agents by injury risk.

        Args:
            fa_data: FA data with injury scores
            position_filter: Filter by position (e.g., 'SP', 'OF')

        Returns:
            DataFrame ranked by injury risk (lowest to highest)
        """
        result = fa_data.copy()

        if position_filter:
            result = result[result['position'] == position_filter]

        # Sort by injury risk score (ascending = lowest risk first)
        result = result.sort_values('injury_risk_score', ascending=True)

        # Select relevant columns
        cols = [
            'player_name', 'position', 'age_2025', '2025_war',
            'injury_risk_score', 'injury_risk_category',
            'injury_risk_factors', 'injury_adjusted_war',
            'expected_games_lost'
        ]

        return result[cols].reset_index(drop=True)

    def identify_hidden_injury_risks(
        self,
        fa_data: pd.DataFrame,
        min_war: float = 3.0
    ) -> pd.DataFrame:
        """
        Identify high-performing players with hidden injury risk.

        These are players who had good 2025 seasons but show concerning
        biomechanical signals that suggest imminent decline/injury.

        Args:
            fa_data: FA data
            min_war: Minimum 2025 WAR to consider

        Returns:
            DataFrame of "hidden risk" players
        """
        result = fa_data[
            (fa_data['2025_war'] >= min_war) &
            (fa_data['injury_risk_category'].isin(['High', 'Very High']))
        ].copy()

        result = result.sort_values('injury_risk_score', ascending=False)

        return result[[
            'player_name', 'position', 'age_2025', '2025_war',
            'injury_risk_score', 'injury_risk_category',
            'injury_risk_factors', 'injury_risk_discount'
        ]].reset_index(drop=True)

    def calculate_contract_risk_premium(
        self,
        base_contract_value_millions: float,
        injury_risk_score: float,
        years: int
    ) -> Dict:
        """
        Calculate how much to discount a contract due to injury risk.

        Args:
            base_contract_value_millions: Contract value without risk adjustment
            injury_risk_score: Injury risk score (0-100)
            years: Contract length

        Returns:
            Dictionary with adjusted contract values
        """
        # Risk premium increases with contract length
        # Longer contracts = more years at risk = higher premium
        length_multiplier = 1.0 + (years - 3) * 0.05  # 5% extra per year beyond 3

        # Calculate discount percentage
        if injury_risk_score < 20:  # Low risk
            discount_pct = 0.0
        elif injury_risk_score < 40:  # Moderate risk
            discount_pct = 0.10 * length_multiplier
        elif injury_risk_score < 60:  # High risk
            discount_pct = 0.25 * length_multiplier
        else:  # Very High risk
            discount_pct = 0.40 * length_multiplier

        discount_pct = min(discount_pct, 0.50)  # Cap at 50% discount

        adjusted_value = base_contract_value_millions * (1 - discount_pct)

        return {
            'base_contract_millions': base_contract_value_millions,
            'injury_discount_pct': f"{discount_pct * 100:.1f}%",
            'discount_amount_millions': base_contract_value_millions * discount_pct,
            'injury_adjusted_contract_millions': adjusted_value,
            'years': years,
            'recommendation': self._get_contract_recommendation(injury_risk_score, years)
        }

    def _get_contract_recommendation(
        self,
        injury_risk_score: float,
        years: int
    ) -> str:
        """Get contract recommendation based on injury risk."""
        if injury_risk_score >= 60:  # Very High risk
            if years >= 5:
                return "AVOID - Too risky for long-term deal"
            else:
                return "Short-term only (2-3 years max) with incentives"
        elif injury_risk_score >= 40:  # High risk
            if years >= 6:
                return "CAUTION - Shorten to 4-5 years or add opt-outs"
            else:
                return "Acceptable with performance incentives"
        elif injury_risk_score >= 20:  # Moderate risk
            return "Standard deal acceptable, monitor closely"
        else:  # Low risk
            return "Green light - Low injury risk"
