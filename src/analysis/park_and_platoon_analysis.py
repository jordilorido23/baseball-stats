"""
Park Factors and Platoon Splits Analysis for MLB Players.

Provides context for player performance:
- Park factors: Adjust stats for hitter/pitcher-friendly ballparks
- Platoon splits: vs LHP/RHP performance differences
- Home/Away splits
- Situational performance metrics

Park-adjusted stats help identify players who benefited from environment vs skill.

Created: November 13, 2025
Author: Baseball Analytics Portfolio
"""
import pandas as pd
import numpy as np
from typing import Dict, Optional, Literal, Tuple


class ParkAndPlatoonAnalysis:
    """
    Analyze park effects and platoon splits for player evaluation.

    Uses FanGraphs park factors and split statistics.
    """

    def __init__(self):
        """Initialize park and platoon analyzer."""
        # 2024 Park Factors (FanGraphs) - 100 = neutral
        # Higher = more hitter-friendly, Lower = more pitcher-friendly
        self.park_factors_2024 = {
            'COL': 115,  # Coors Field - most hitter-friendly
            'TEX': 108,  # Globe Life Field
            'BAL': 106,  # Camden Yards
            'CHC': 105,  # Wrigley Field
            'CIN': 104,  # Great American Ball Park
            'NYY': 103,  # Yankee Stadium
            'BOS': 103,  # Fenway Park
            'MIN': 102,  # Target Field
            'PHI': 101,  # Citizens Bank Park
            'MIL': 100,  # American Family Field
            'HOU': 100,  # Minute Maid Park
            'ATL': 99,   # Truist Park
            'WSH': 99,   # Nationals Park
            'TOR': 98,   # Rogers Centre
            'KC': 98,    # Kauffman Stadium
            'AZ': 98,    # Chase Field
            'LAD': 97,   # Dodger Stadium
            'DET': 96,   # Comerica Park
            'CLE': 96,   # Progressive Field
            'TB': 95,    # Tropicana Field
            'SF': 95,    # Oracle Park
            'CHW': 95,   # Guaranteed Rate Field
            'MIA': 94,   # loanDepot Park
            'SD': 93,    # Petco Park
            'SEA': 92,   # T-Mobile Park
            'NYM': 92,   # Citi Field
            'LAA': 92,   # Angel Stadium
            'STL': 92,   # Busch Stadium
            'OAK': 89,   # Oakland Coliseum - most pitcher-friendly
            'PIT': 91,   # PNC Park
        }

        # Platoon advantage thresholds
        self.extreme_platoon = 50  # OPS difference of 50+ points
        self.significant_platoon = 30  # OPS difference of 30+ points

    def get_park_factor(self, team: str) -> int:
        """
        Get park factor for a team.

        Args:
            team: Team abbreviation

        Returns:
            Park factor (100 = neutral)
        """
        return self.park_factors_2024.get(team, 100)

    def adjust_stats_for_park(
        self,
        batting_stats: pd.DataFrame,
        team_col: str = 'Team',
        stats_to_adjust: list = ['HR', 'AVG', 'OPS']
    ) -> pd.DataFrame:
        """
        Adjust batting stats for park factors.

        Args:
            batting_stats: Batting stats DataFrame
            team_col: Column with team abbreviations
            stats_to_adjust: List of stats to adjust

        Returns:
            DataFrame with park-adjusted stats
        """
        result = batting_stats.copy()

        # Add park factor column
        result['park_factor'] = result[team_col].map(self.park_factors_2024).fillna(100)

        # Adjust stats (divide by park factor / 100)
        for stat in stats_to_adjust:
            if stat in result.columns:
                result[f'{stat}_park_adj'] = result[stat] / (result['park_factor'] / 100)

        return result

    def extract_platoon_splits(
        self,
        batting_stats: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Extract platoon split data from FanGraphs batting stats.

        FanGraphs includes vs LHP and vs RHP columns.

        Args:
            batting_stats: FanGraphs batting stats

        Returns:
            DataFrame with platoon metrics
        """
        platoon_cols = [
            'Name', 'playerid',
            'wRC+ vs L',  # wRC+ vs left-handed pitchers
            'wRC+ vs R',  # wRC+ vs right-handed pitchers
            'BA vs L',    # Batting average vs LHP
            'BA vs R',    # Batting average vs RHP
            'OBP vs L',   # On-base vs LHP
            'OBP vs R',   # On-base vs RHP
            'SLG vs L',   # Slugging vs LHP
            'SLG vs R',   # Slugging vs RHP
        ]

        # Filter to columns that exist
        available_cols = [col for col in platoon_cols if col in batting_stats.columns]

        if len(available_cols) < 3:
            print("Warning: FanGraphs data missing platoon split columns")
            return pd.DataFrame()

        platoon_data = batting_stats[available_cols].copy()

        # Calculate platoon advantages
        if 'wRC+ vs L' in platoon_data.columns and 'wRC+ vs R' in platoon_data.columns:
            platoon_data['platoon_advantage_wRC'] = (
                platoon_data['wRC+ vs L'] - platoon_data['wRC+ vs R']
            )

        if 'OBP vs L' in platoon_data.columns and 'OBP vs R' in platoon_data.columns:
            if 'SLG vs L' in platoon_data.columns and 'SLG vs R' in platoon_data.columns:
                platoon_data['OPS_vs_L'] = platoon_data['OBP vs L'] + platoon_data['SLG vs L']
                platoon_data['OPS_vs_R'] = platoon_data['OBP vs R'] + platoon_data['SLG vs R']
                platoon_data['platoon_advantage_OPS'] = (
                    platoon_data['OPS_vs_L'] - platoon_data['OPS_vs_R']
                )

        return platoon_data

    def categorize_platoon_splits(
        self,
        platoon_data: pd.DataFrame,
        metric: str = 'platoon_advantage_OPS'
    ) -> pd.DataFrame:
        """
        Categorize players by platoon advantage.

        Args:
            platoon_data: DataFrame with platoon splits
            metric: Metric to use for categorization

        Returns:
            DataFrame with platoon categories
        """
        result = platoon_data.copy()

        if metric not in result.columns:
            print(f"Warning: {metric} not found")
            return result

        # Categorize platoon advantage
        # Positive = better vs LHP, Negative = better vs RHP
        result['platoon_category'] = pd.cut(
            result[metric],
            bins=[-2.0, -0.05, -0.02, 0.02, 0.05, 2.0],
            labels=['Severe Reverse', 'Moderate Reverse', 'Balanced', 'Moderate Advantage', 'Severe Advantage']
        )

        # Flag extreme platoon players (affects playing time)
        result['extreme_platoon'] = result[metric].abs() >= (self.extreme_platoon / 1000)

        return result

    def identify_extreme_platoon_players(
        self,
        platoon_data: pd.DataFrame,
        min_advantage: float = 0.05
    ) -> pd.DataFrame:
        """
        Identify players with extreme platoon splits.

        These players may be platoon candidates (reduced playing time).

        Args:
            platoon_data: Platoon splits data
            min_advantage: Minimum OPS advantage threshold

        Returns:
            DataFrame of extreme platoon players
        """
        if 'platoon_advantage_OPS' not in platoon_data.columns:
            return pd.DataFrame()

        extreme = platoon_data[
            platoon_data['platoon_advantage_OPS'].abs() >= min_advantage
        ].copy()

        extreme = extreme.sort_values('platoon_advantage_OPS', ascending=False)

        return extreme

    def analyze_park_beneficiaries(
        self,
        batting_stats: pd.DataFrame,
        team_col: str = 'Team',
        min_hr: int = 15
    ) -> pd.DataFrame:
        """
        Identify players who significantly benefited from their home park.

        Args:
            batting_stats: Batting stats with park factors
            team_col: Team column
            min_hr: Minimum home runs to analyze

        Returns:
            DataFrame of park beneficiaries
        """
        # Add park factors
        stats_with_park = self.adjust_stats_for_park(batting_stats, team_col)

        # Filter to power hitters
        if 'HR' in stats_with_park.columns:
            power_hitters = stats_with_park[stats_with_park['HR'] >= min_hr].copy()
        else:
            power_hitters = stats_with_park.copy()

        # Calculate park benefit (higher factor = more benefit)
        power_hitters['park_benefit_score'] = power_hitters['park_factor'] - 100

        # Sort by park benefit
        beneficiaries = power_hitters[
            power_hitters['park_benefit_score'] > 0
        ].sort_values('park_benefit_score', ascending=False)

        return beneficiaries

    def calculate_home_road_splits(
        self,
        batting_stats: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Extract home/road splits from FanGraphs data.

        Args:
            batting_stats: FanGraphs batting stats

        Returns:
            DataFrame with home/road metrics
        """
        home_road_cols = [
            'Name', 'playerid',
            'Home AVG', 'Away AVG',
            'Home HR', 'Away HR',
            'Home OPS', 'Away OPS',
        ]

        # Filter to existing columns
        available_cols = [col for col in home_road_cols if col in batting_stats.columns]

        if len(available_cols) < 3:
            print("Warning: Home/road split data not available")
            return pd.DataFrame()

        splits_data = batting_stats[available_cols].copy()

        # Calculate home/road ratios
        if 'Home OPS' in splits_data.columns and 'Away OPS' in splits_data.columns:
            splits_data['home_road_ops_ratio'] = (
                splits_data['Home OPS'] / splits_data['Away OPS']
            )

        if 'Home HR' in splits_data.columns and 'Away HR' in splits_data.columns:
            splits_data['home_road_hr_ratio'] = (
                splits_data['Home HR'] / (splits_data['Away HR'] + 0.1)  # Avoid division by zero
            )

        return splits_data

    def create_park_adjustment_report(
        self,
        player_name: str,
        batting_stats: pd.DataFrame,
        team_col: str = 'Team'
    ) -> Dict:
        """
        Create detailed park adjustment report for a player.

        Args:
            player_name: Player name
            batting_stats: Batting stats
            team_col: Team column

        Returns:
            Dictionary with park adjustment analysis
        """
        player_stats = batting_stats[batting_stats['Name'] == player_name]

        if len(player_stats) == 0:
            return {'error': f'Player {player_name} not found'}

        player = player_stats.iloc[0]
        team = player.get(team_col, 'Unknown')
        park_factor = self.get_park_factor(team)

        # Determine park environment
        if park_factor >= 105:
            park_env = 'Very Hitter-Friendly'
        elif park_factor >= 102:
            park_env = 'Hitter-Friendly'
        elif park_factor >= 98:
            park_env = 'Neutral'
        elif park_factor >= 95:
            park_env = 'Pitcher-Friendly'
        else:
            park_env = 'Very Pitcher-Friendly'

        report = {
            'player_name': player_name,
            'team': team,
            'park_factor': park_factor,
            'park_environment': park_env,
            'park_benefit': park_factor - 100,
        }

        # Add raw and adjusted stats if available
        if 'HR' in player:
            report['HR_raw'] = player['HR']
            report['HR_park_adjusted'] = round(player['HR'] / (park_factor / 100), 1)

        if 'AVG' in player:
            report['AVG_raw'] = player['AVG']
            report['AVG_park_adjusted'] = round(player['AVG'] / (park_factor / 100), 3)

        if 'OPS' in player:
            report['OPS_raw'] = player['OPS']
            report['OPS_park_adjusted'] = round(player['OPS'] / (park_factor / 100), 3)

        # Recommendation
        if park_factor >= 105:
            report['recommendation'] = 'Exercise caution - Stats may be inflated by park'
        elif park_factor <= 95:
            report['recommendation'] = 'Could see improvement in neutral/hitter-friendly park'
        else:
            report['recommendation'] = 'Park neutral - stats should travel'

        return report
