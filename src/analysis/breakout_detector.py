"""
Breakout detection module - identifies players with strong underlying metrics
who may be poised for improved performance.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Literal


class BreakoutDetector:
    """
    Analyze players to identify breakout candidates and regression risks.

    Uses expected stats, quality of contact metrics, and trend analysis
    to find players whose underlying performance differs from results.
    """

    def __init__(self):
        """Initialize the breakout detector."""
        pass

    def calculate_xstat_gaps(
        self,
        df: pd.DataFrame,
        player_type: Literal['batter', 'pitcher'] = 'batter'
    ) -> pd.DataFrame:
        """
        Calculate gaps between expected and actual stats.

        Args:
            df: DataFrame with both actual and expected stats
            player_type: 'batter' or 'pitcher'

        Returns:
            DataFrame with gap columns added
        """
        result = df.copy()

        if player_type == 'batter':
            # Positive gap = player underperforming (unlucky)
            if 'xba' in result.columns and 'ba' in result.columns:
                result['ba_gap'] = result['xba'] - result['ba']

            if 'xslg' in result.columns and 'slg' in result.columns:
                result['slg_gap'] = result['xslg'] - result['slg']

            if 'xwoba' in result.columns and 'woba' in result.columns:
                result['woba_gap'] = result['xwoba'] - result['woba']

            if 'xobp' in result.columns and 'obp' in result.columns:
                result['obp_gap'] = result['xobp'] - result['obp']

        else:  # pitcher
            # For pitchers, negative gap = pitcher unlucky (allowing more than expected)
            if 'xba' in result.columns and 'ba' in result.columns:
                result['ba_gap'] = result['ba'] - result['xba']

            if 'xslg' in result.columns and 'slg' in result.columns:
                result['slg_gap'] = result['slg'] - result['xslg']

            if 'xwoba' in result.columns and 'woba' in result.columns:
                result['woba_gap'] = result['woba'] - result['xwoba']

            if 'xera' in result.columns and 'era' in result.columns:
                result['era_gap'] = result['era'] - result['xera']

        return result

    def find_unlucky_players(
        self,
        df: pd.DataFrame,
        player_type: Literal['batter', 'pitcher'] = 'batter',
        min_gap: float = 0.020,
        top_n: Optional[int] = 50
    ) -> pd.DataFrame:
        """
        Find players whose expected stats exceed actual stats (unlucky).

        These are buy-low candidates who should improve with regression to mean.

        Args:
            df: DataFrame with expected stats
            player_type: 'batter' or 'pitcher'
            min_gap: Minimum gap to be considered (0.020 = 20 points)
            top_n: Number of players to return (None = all above min_gap)

        Returns:
            DataFrame with unlucky players ranked by gap size
        """
        result = self.calculate_xstat_gaps(df, player_type)

        # Filter to significant gaps
        if player_type == 'batter':
            if 'woba_gap' in result.columns:
                unlucky = result[result['woba_gap'] >= min_gap].copy()
                unlucky = unlucky.sort_values('woba_gap', ascending=False)
            elif 'ba_gap' in result.columns:
                unlucky = result[result['ba_gap'] >= min_gap].copy()
                unlucky = unlucky.sort_values('ba_gap', ascending=False)
            else:
                return pd.DataFrame()
        else:
            if 'era_gap' in result.columns:
                unlucky = result[result['era_gap'] >= 0.50].copy()  # ERA uses different scale
                unlucky = unlucky.sort_values('era_gap', ascending=False)
            elif 'woba_gap' in result.columns:
                unlucky = result[result['woba_gap'] >= min_gap].copy()
                unlucky = unlucky.sort_values('woba_gap', ascending=False)
            else:
                return pd.DataFrame()

        if top_n:
            unlucky = unlucky.head(top_n)

        return unlucky

    def find_overperforming_players(
        self,
        df: pd.DataFrame,
        player_type: Literal['batter', 'pitcher'] = 'batter',
        min_gap: float = 0.020,
        top_n: Optional[int] = 50
    ) -> pd.DataFrame:
        """
        Find players whose actual stats exceed expected stats (lucky/overperforming).

        These are sell-high candidates who may regress.

        Args:
            df: DataFrame with expected stats
            player_type: 'batter' or 'pitcher'
            min_gap: Minimum gap to be considered
            top_n: Number of players to return

        Returns:
            DataFrame with overperforming players ranked by gap size
        """
        result = self.calculate_xstat_gaps(df, player_type)

        # For overperformers, we want negative gaps (actual > expected)
        if player_type == 'batter':
            if 'woba_gap' in result.columns:
                overperformers = result[result['woba_gap'] <= -min_gap].copy()
                overperformers = overperformers.sort_values('woba_gap', ascending=True)
            elif 'ba_gap' in result.columns:
                overperformers = result[result['ba_gap'] <= -min_gap].copy()
                overperformers = overperformers.sort_values('ba_gap', ascending=True)
            else:
                return pd.DataFrame()
        else:
            if 'era_gap' in result.columns:
                overperformers = result[result['era_gap'] <= -0.50].copy()
                overperformers = overperformers.sort_values('era_gap', ascending=True)
            elif 'woba_gap' in result.columns:
                overperformers = result[result['woba_gap'] <= -min_gap].copy()
                overperformers = overperformers.sort_values('woba_gap', ascending=True)
            else:
                return pd.DataFrame()

        if top_n:
            overperformers = overperformers.head(top_n)

        return overperformers

    def calculate_breakout_score(
        self,
        df: pd.DataFrame,
        player_type: Literal['batter', 'pitcher'] = 'batter'
    ) -> pd.DataFrame:
        """
        Calculate a composite breakout score based on multiple factors.

        Higher score = more likely to break out / improve.

        For batters, considers:
        - Expected stats gap (underperforming luck)
        - Quality of contact (barrel rate, hard hit rate, exit velo)
        - Plate discipline (K%, BB%, chase rate)
        - Age (younger = more room to grow)

        Args:
            df: DataFrame with player data
            player_type: 'batter' or 'pitcher'

        Returns:
            DataFrame with breakout_score column added
        """
        result = self.calculate_xstat_gaps(df, player_type)

        # Initialize score
        result['breakout_score'] = 0.0

        if player_type == 'batter':
            # Factor 1: Expected stats gap (40% weight)
            if 'woba_gap' in result.columns:
                # Normalize to 0-40 scale
                woba_component = (result['woba_gap'] / 0.050) * 40
                woba_component = woba_component.clip(upper=40)
                result['breakout_score'] += woba_component

            # Factor 2: Quality of contact (30% weight)
            qoc_score = 0
            if 'barrel_batted_rate' in result.columns:
                # Top 10% = 15 points, scale linearly
                barrel_pct = result['barrel_batted_rate'].rank(pct=True)
                qoc_score += barrel_pct * 15

            if 'avg_hit_speed' in result.columns:
                # Top exit velo = 15 points
                exit_velo_pct = result['avg_hit_speed'].rank(pct=True)
                qoc_score += exit_velo_pct * 15

            result['breakout_score'] += qoc_score

            # Factor 3: Plate discipline (20% weight)
            if 'k_percent' in result.columns and 'bb_percent' in result.columns:
                # Lower K% = better (inverted)
                k_component = (1 - result['k_percent'].rank(pct=True)) * 10

                # Higher BB% = better
                bb_component = result['bb_percent'].rank(pct=True) * 10

                result['breakout_score'] += k_component + bb_component

            # Factor 4: Age (10% weight - younger is better)
            if 'age' in result.columns:
                # Peak age ~27, younger gets bonus
                age_bonus = np.where(result['age'] <= 27, (27 - result['age']) * 1.0, 0)
                result['breakout_score'] += age_bonus

        else:  # pitcher
            # Similar logic for pitchers
            if 'woba_gap' in result.columns:
                woba_component = (result['woba_gap'] / 0.030) * 40
                woba_component = woba_component.clip(upper=40)
                result['breakout_score'] += woba_component

            # Stuff quality
            if 'whiff_percent' in result.columns:
                whiff_pct = result['whiff_percent'].rank(pct=True)
                result['breakout_score'] += whiff_pct * 30

            # Command
            if 'k_percent' in result.columns and 'bb_percent' in result.columns:
                k_component = result['k_percent'].rank(pct=True) * 10
                bb_component = (1 - result['bb_percent'].rank(pct=True)) * 10
                result['breakout_score'] += k_component + bb_component

            # Age
            if 'age' in result.columns:
                age_bonus = np.where(result['age'] <= 28, (28 - result['age']) * 1.0, 0)
                result['breakout_score'] += age_bonus

        return result

    def identify_breakout_candidates(
        self,
        df: pd.DataFrame,
        player_type: Literal['batter', 'pitcher'] = 'batter',
        min_score: float = 60,
        top_n: int = 30
    ) -> pd.DataFrame:
        """
        Identify top breakout candidates using composite scoring.

        Args:
            df: DataFrame with player data
            player_type: 'batter' or 'pitcher'
            min_score: Minimum breakout score
            top_n: Number of candidates to return

        Returns:
            DataFrame with top breakout candidates
        """
        result = self.calculate_breakout_score(df, player_type)

        # Filter and rank
        breakouts = result[result['breakout_score'] >= min_score].copy()
        breakouts = breakouts.sort_values('breakout_score', ascending=False)

        return breakouts.head(top_n)

    def analyze_trends(
        self,
        current_df: pd.DataFrame,
        previous_df: pd.DataFrame,
        metric_cols: List[str],
        player_id_col: str = 'player_id'
    ) -> pd.DataFrame:
        """
        Analyze trends by comparing current period to previous period.

        Args:
            current_df: Recent period data
            previous_df: Earlier period data
            metric_cols: Columns to compare
            player_id_col: Column to join on

        Returns:
            DataFrame with trend columns (improvement/decline)
        """
        # Merge datasets
        merged = current_df.merge(
            previous_df[[ player_id_col] + metric_cols],
            on=player_id_col,
            how='inner',
            suffixes=('_current', '_previous')
        )

        # Calculate changes
        for col in metric_cols:
            current_col = f"{col}_current"
            previous_col = f"{col}_previous"

            if current_col in merged.columns and previous_col in merged.columns:
                merged[f"{col}_change"] = merged[current_col] - merged[previous_col]
                merged[f"{col}_pct_change"] = (
                    (merged[current_col] - merged[previous_col]) / merged[previous_col] * 100
                )

        return merged

    def get_breakout_summary(
        self,
        df: pd.DataFrame,
        player_name: str,
        player_type: Literal['batter', 'pitcher'] = 'batter'
    ) -> Dict:
        """
        Get a detailed breakout summary for a specific player.

        Args:
            df: DataFrame with player data including expected stats
            player_name: Player name to analyze
            player_type: 'batter' or 'pitcher'

        Returns:
            Dictionary with breakout analysis
        """
        # Find player
        player_data = df[df['first_name'].str.contains(player_name, case=False, na=False) |
                         df['last_name'].str.contains(player_name, case=False, na=False)]

        if len(player_data) == 0:
            return {'error': 'Player not found'}

        player = player_data.iloc[0]

        summary = {
            'player_name': player.get('first_name', '') + ' ' + player.get('last_name', ''),
            'age': player.get('age', 'N/A'),
        }

        # Add expected stats gaps
        gaps_df = self.calculate_xstat_gaps(pd.DataFrame([player]), player_type)
        gaps = gaps_df.iloc[0]

        summary['expected_stats_gaps'] = {
            col: gaps.get(col, 'N/A')
            for col in gaps_df.columns
            if '_gap' in col
        }

        # Add quality metrics
        if player_type == 'batter':
            summary['quality_of_contact'] = {
                'barrel_rate': player.get('barrel_batted_rate', 'N/A'),
                'avg_exit_velo': player.get('avg_hit_speed', 'N/A'),
                'max_exit_velo': player.get('max_hit_speed', 'N/A'),
                'hard_hit_rate': player.get('hard_hit_percent', 'N/A')
            }

            summary['plate_discipline'] = {
                'k_percent': player.get('k_percent', 'N/A'),
                'bb_percent': player.get('bb_percent', 'N/A'),
                'chase_rate': player.get('chase_rate', 'N/A')
            }

        # Calculate breakout score
        score_df = self.calculate_breakout_score(pd.DataFrame([player]), player_type)
        summary['breakout_score'] = score_df.iloc[0]['breakout_score']

        return summary
