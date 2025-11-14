"""
Phase 4: Diamond Detector - Composite Scoring Algorithm

This module combines all physics, arsenal, and biomechanics signals
to identify hidden gems in the reliever free agent market.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple


class DiamondDetector:
    """
    Identifies undervalued relievers through multi-dimensional analysis.

    Combines:
    - Pitch physics edge (VAA, SSW, Tunneling)
    - Arsenal synergy edge (Gyro/Sweeper, Effective Velocity, Cognitive Load)
    - Market inefficiency edge (Role Mismatch, Nash Equilibrium, Release Strategy)
    - Durability/Risk assessment (FU, Mechanics Stability)
    """

    def __init__(self):
        # Weighting scheme for Diamond Score
        self.weights = {
            # Physics-based edge (50%)
            'vaa_zone_mismatch': 0.20,
            'ssw_movement': 0.15,
            'tunneling': 0.15,

            # Arsenal synergy edge (30%)
            'arsenal_synergy': 0.10,
            'effective_velocity': 0.10,
            'cognitive_load': 0.10,

            # Market inefficiency edge (20%)
            'role_mismatch': 0.10,
            'nash_equilibrium': 0.05,
            'release_strategy': 0.05,
        }

    def normalize_score(self, value: float, min_val: float = 0, max_val: float = 100) -> float:
        """Normalize a score to 0-100 range."""
        if pd.isna(value):
            return 50  # Neutral score for missing data

        # Clip to range
        value = max(min_val, min(max_val, value))

        # Normalize to 0-100
        if max_val == min_val:
            return 50

        return ((value - min_val) / (max_val - min_val)) * 100

    def calculate_role_mismatch_score(self, pitcher_data: Dict) -> float:
        """
        Calculate how mismatched a pitcher is from their current role.

        Elite closer talent stuck in setup role = high score

        Args:
            pitcher_data: Dictionary with performance and usage metrics

        Returns:
            Role mismatch score 0-100 (higher = more underutilized)
        """
        try:
            # Get closer talent indicators
            k_rate = pitcher_data.get('K_pct', 0)
            whiff_rate = pitcher_data.get('Whiff_pct', 0)
            stuff_plus = pitcher_data.get('Stuff_plus', 100)
            location_plus = pitcher_data.get('Location_plus', 100)

            # Calculate talent score
            talent_components = [
                self.normalize_score(k_rate, 15, 40),
                self.normalize_score(whiff_rate, 20, 40),
                self.normalize_score(stuff_plus, 80, 120),
                self.normalize_score(location_plus, 80, 120),
            ]

            talent_score = np.mean([c for c in talent_components if not pd.isna(c)])

            # Get actual role usage
            saves = pitcher_data.get('Saves', 0)
            appearances = pitcher_data.get('Appearances', 0)
            leverage_index = pitcher_data.get('gmLI', 1.0)

            # High talent + low saves = high mismatch
            # Closer talent threshold: ~75+
            # Closer usage threshold: >15 saves OR gmLI > 1.3

            if talent_score > 75:
                # Has closer talent
                if saves < 10 and leverage_index < 1.2:
                    # Not being used as closer
                    mismatch = talent_score - 30  # High mismatch
                elif saves < 20 and leverage_index < 1.4:
                    # Partial closer usage
                    mismatch = talent_score - 50  # Moderate mismatch
                else:
                    # Being used as closer
                    mismatch = 20  # Low mismatch
            else:
                # Not closer talent
                mismatch = 30  # Neutral

            return max(0, min(100, mismatch))

        except Exception as e:
            return 50

    def calculate_diamond_score(self, pitcher_data: Dict) -> float:
        """
        Calculate composite Diamond Score.

        Combines all edge signals with optimal weighting.

        Args:
            pitcher_data: Dictionary with all analysis metrics

        Returns:
            Diamond Score 0-100 (higher = better hidden gem)
        """
        try:
            # Extract and normalize component scores
            scores = {}

            # Physics-based edge
            scores['vaa_zone_mismatch'] = self.normalize_score(
                pitcher_data.get('VAA_Zone_Mismatch_Score', 50),
                0, 100
            )

            scores['ssw_movement'] = self.normalize_score(
                pitcher_data.get('SSW_Movement_FB', 0),
                0, 5  # SSW > 3 inches is elite
            )

            scores['tunneling'] = self.normalize_score(
                pitcher_data.get('Tunneling_Score', 50),
                0, 100
            )

            # Arsenal synergy edge
            scores['arsenal_synergy'] = self.normalize_score(
                pitcher_data.get('Arsenal_Synergy_Score', 50),
                0, 100
            )

            scores['effective_velocity'] = self.normalize_score(
                pitcher_data.get('Effective_Velocity_Composite', 93),
                90, 100  # EV range
            )

            scores['cognitive_load'] = self.normalize_score(
                pitcher_data.get('Cognitive_Load_Score', 50),
                0, 100
            )

            # Market inefficiency edge
            scores['role_mismatch'] = self.calculate_role_mismatch_score(pitcher_data)

            # Nash score: INVERT because low Nash = already optimized
            nash_score = pitcher_data.get('Nash_Equilibrium_Score', 50)
            scores['nash_equilibrium'] = self.normalize_score(nash_score, 0, 100)

            scores['release_strategy'] = self.normalize_score(
                pitcher_data.get('Release_Strategy_Score', 50),
                0, 100
            )

            # Calculate weighted composite
            diamond_score = sum(
                scores[component] * weight
                for component, weight in self.weights.items()
                if component in scores
            )

            return diamond_score

        except Exception as e:
            return 50

    def calculate_value_score(self, pitcher_data: Dict) -> float:
        """
        Calculate expected value vs. market price.

        Combines:
        - Diamond Score (talent level)
        - Bust Risk (durability concerns)
        - Projected AAV (market price)

        Returns:
            Value Score 0-100 (higher = better value)
        """
        try:
            diamond_score = pitcher_data.get('Diamond_Score', 50)
            bust_risk = pitcher_data.get('Bust_Risk_Score', 50)
            projected_aav = pitcher_data.get('Projected_AAV', 5)

            # True talent = Diamond Score adjusted for bust risk
            true_talent = diamond_score * (1 - bust_risk / 100) * 0.8 + diamond_score * 0.2

            # Expected value in millions (rough approximation)
            # Elite closer: $10-15M
            # Good setup: $5-8M
            # Middle reliever: $2-4M

            if true_talent > 80:
                expected_value = 12
            elif true_talent > 70:
                expected_value = 8
            elif true_talent > 60:
                expected_value = 5
            else:
                expected_value = 3

            # Value score = how much better than market price
            value_delta = expected_value - projected_aav

            # Scale to 0-100
            # +$5M undervalued = 100
            # Market price = 50
            # Overvalued = 0

            value_score = 50 + (value_delta * 10)

            return max(0, min(100, value_score))

        except Exception as e:
            return 50

    def identify_hidden_gems(self, all_pitchers: pd.DataFrame,
                            diamond_threshold: float = 75,
                            max_saves: int = 15,
                            max_bust_risk: float = 40,
                            max_aav: float = 6) -> pd.DataFrame:
        """
        Filter for true hidden gems based on criteria.

        Args:
            all_pitchers: DataFrame with all pitcher metrics
            diamond_threshold: Minimum Diamond Score
            max_saves: Maximum saves (lower = more underutilized)
            max_bust_risk: Maximum acceptable bust risk
            max_aav: Maximum projected AAV

        Returns:
            DataFrame of hidden gem pitchers
        """
        try:
            if all_pitchers.empty:
                return pd.DataFrame()

            # Apply filters
            hidden_gems = all_pitchers[
                (all_pitchers['Diamond_Score'] > diamond_threshold) &
                (all_pitchers['Saves'] < max_saves) &
                (all_pitchers['Bust_Risk_Score'] < max_bust_risk) &
                (all_pitchers['Projected_AAV'] < max_aav)
            ].copy()

            # Sort by Value Score (best values first)
            hidden_gems = hidden_gems.sort_values('Value_Score', ascending=False)

            return hidden_gems

        except Exception as e:
            print(f"Error identifying hidden gems: {e}")
            return pd.DataFrame()

    def categorize_pitchers(self, all_pitchers: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        """
        Categorize pitchers into tiers based on Diamond Score and value.

        Returns:
            Dictionary of DataFrames by category
        """
        try:
            categories = {}

            # Elite Hidden Gems (Diamond Score 80+, High Value, Low Bust Risk)
            categories['Elite_Hidden_Gems'] = all_pitchers[
                (all_pitchers['Diamond_Score'] > 80) &
                (all_pitchers['Value_Score'] > 70) &
                (all_pitchers['Bust_Risk_Score'] < 30)
            ].copy()

            # High-Upside Risks (Diamond Score 75+, High Bust Risk)
            categories['High_Upside_Risks'] = all_pitchers[
                (all_pitchers['Diamond_Score'] > 75) &
                (all_pitchers['Bust_Risk_Score'] > 50)
            ].copy()

            # Value Plays (Good Diamond Score, Great Value)
            categories['Value_Plays'] = all_pitchers[
                (all_pitchers['Diamond_Score'] > 65) &
                (all_pitchers['Value_Score'] > 75) &
                (all_pitchers['Bust_Risk_Score'] < 40)
            ].copy()

            # Avoid (Low Diamond Score or Very High Bust Risk)
            categories['Avoid'] = all_pitchers[
                (all_pitchers['Diamond_Score'] < 50) |
                (all_pitchers['Bust_Risk_Score'] > 70)
            ].copy()

            # Role Mismatch Opportunities (High Role Mismatch Score)
            categories['Role_Mismatch'] = all_pitchers[
                (all_pitchers['Role_Mismatch_Score'] > 70) &
                (all_pitchers['Bust_Risk_Score'] < 50)
            ].copy()

            # Sort each category
            for category, df in categories.items():
                if not df.empty:
                    categories[category] = df.sort_values('Diamond_Score', ascending=False)

            return categories

        except Exception as e:
            print(f"Error categorizing pitchers: {e}")
            return {}

    def generate_summary_stats(self, all_pitchers: pd.DataFrame) -> Dict:
        """
        Generate summary statistics for the analysis.

        Returns:
            Dictionary with summary metrics
        """
        try:
            if all_pitchers.empty:
                return {}

            summary = {
                'total_pitchers': len(all_pitchers),
                'avg_diamond_score': all_pitchers['Diamond_Score'].mean(),
                'avg_bust_risk': all_pitchers['Bust_Risk_Score'].mean(),
                'avg_projected_aav': all_pitchers['Projected_AAV'].mean(),

                # Top performers
                'highest_diamond_score': all_pitchers['Diamond_Score'].max(),
                'best_value_score': all_pitchers['Value_Score'].max(),
                'lowest_bust_risk': all_pitchers['Bust_Risk_Score'].min(),

                # Distribution
                'diamond_score_median': all_pitchers['Diamond_Score'].median(),
                'diamond_score_std': all_pitchers['Diamond_Score'].std(),

                # Hidden gems count
                'hidden_gems_count': len(all_pitchers[
                    (all_pitchers['Diamond_Score'] > 75) &
                    (all_pitchers['Bust_Risk_Score'] < 40) &
                    (all_pitchers['Projected_AAV'] < 6)
                ]),

                # Component analysis
                'avg_vaa_mismatch': all_pitchers['VAA_Zone_Mismatch_Score'].mean(),
                'avg_ssw_movement': all_pitchers['SSW_Movement_FB'].mean(),
                'avg_tunneling': all_pitchers['Tunneling_Score'].mean(),
                'avg_arsenal_synergy': all_pitchers['Arsenal_Synergy_Score'].mean(),
                'avg_cognitive_load': all_pitchers['Cognitive_Load_Score'].mean(),

                # Gyro/Sweeper detection
                'gyro_sweeper_combo_count': len(all_pitchers[
                    all_pitchers['Has_Gyro_Sweeper_Combo'] == True
                ]),
            }

            return summary

        except Exception as e:
            print(f"Error generating summary: {e}")
            return {}


def analyze_reliever_complete(physics_data: Dict, arsenal_data: Dict,
                              biomech_data: Dict, traditional_data: Dict) -> Dict:
    """
    Combine all analysis phases into complete pitcher profile.

    Args:
        physics_data: Results from pitch_physics_analyzer
        arsenal_data: Results from arsenal_synergy_analyzer
        biomech_data: Results from biomechanics_analyzer
        traditional_data: Traditional stats (K%, saves, etc.)

    Returns:
        Complete pitcher analysis dictionary
    """
    # Merge all data
    complete_data = {}
    complete_data.update(physics_data)
    complete_data.update(arsenal_data)
    complete_data.update(biomech_data)
    complete_data.update(traditional_data)

    # Calculate Diamond Score
    detector = DiamondDetector()

    complete_data['Diamond_Score'] = detector.calculate_diamond_score(complete_data)
    complete_data['Role_Mismatch_Score'] = detector.calculate_role_mismatch_score(complete_data)
    complete_data['Value_Score'] = detector.calculate_value_score(complete_data)

    return complete_data


def rank_free_agents(all_pitchers_data: List[Dict]) -> pd.DataFrame:
    """
    Rank all free agent relievers by Diamond Score and value.

    Args:
        all_pitchers_data: List of complete pitcher analysis dictionaries

    Returns:
        Ranked DataFrame
    """
    # Convert to DataFrame
    df = pd.DataFrame(all_pitchers_data)

    if df.empty:
        return df

    # Sort by Diamond Score
    df = df.sort_values('Diamond_Score', ascending=False)

    # Add rank column
    df['Diamond_Rank'] = range(1, len(df) + 1)

    # Add value rank
    df['Value_Rank'] = df['Value_Score'].rank(ascending=False, method='min').astype(int)

    return df


if __name__ == "__main__":
    # Test with sample data
    sample_pitcher = {
        'player_name': 'Hunter Harvey',
        'player_id': 663961,

        # Physics
        'VAA_Zone_Mismatch_Score': 75,
        'SSW_Movement_FB': 4.1,
        'Tunneling_Score': 82,

        # Arsenal
        'Arsenal_Synergy_Score': 70,
        'Effective_Velocity_Composite': 97.2,
        'Cognitive_Load_Score': 65,
        'Has_Gyro_Sweeper_Combo': True,
        'Nash_Equilibrium_Score': 42,

        # Biomechanics
        'Release_Strategy_Score': 90,
        'Durability_Score': 75,
        'Bust_Risk_Score': 25,

        # Traditional
        'K_pct': 32,
        'Whiff_pct': 35,
        'Stuff_plus': 115,
        'Location_plus': 105,
        'Saves': 0,
        'Appearances': 45,
        'gmLI': 0.9,
        'Projected_AAV': 4.0,
    }

    detector = DiamondDetector()

    diamond_score = detector.calculate_diamond_score(sample_pitcher)
    role_mismatch = detector.calculate_role_mismatch_score(sample_pitcher)
    value_score = detector.calculate_value_score(sample_pitcher)

    print(f"\nDiamond Detector Results for {sample_pitcher['player_name']}:")
    print(f"Diamond Score: {diamond_score:.1f}/100")
    print(f"Role Mismatch Score: {role_mismatch:.1f}/100")
    print(f"Value Score: {value_score:.1f}/100")
    print(f"Bust Risk: {sample_pitcher['Bust_Risk_Score']:.1f}/100")

    if diamond_score > 75 and value_score > 70:
        print("\n🔹 HIDDEN GEM IDENTIFIED 🔹")
