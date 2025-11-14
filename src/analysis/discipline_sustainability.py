"""
Plate Discipline Sustainability Analysis for Free Agents.

This module analyzes SUSTAINABLE SKILLS vs LUCKY OUTCOMES:
- Zone contact % (sustainable)
- Chase rate / O-Swing% (sustainable)
- Barrel rate (more volatile)
- BABIP luck vs true skill

Key hypothesis: Players with elite plate discipline age better than
high-barrel guys with poor discipline, because discipline is more stable.

Created: November 13, 2025
Author: Baseball Analytics Portfolio
"""
import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple
from scipy import stats
import warnings
warnings.filterwarnings('ignore')


class DisciplineSustainabilityAnalyzer:
    """
    Analyze plate discipline sustainability for free agent evaluation.

    Differentiates between:
    - Sustainable skills (zone contact, chase rate, plate discipline)
    - Volatile outcomes (barrel rate, BABIP, HR/FB ratio)

    Output: "Safe bet" vs "risky bet" classifications.
    """

    def __init__(self):
        """Initialize discipline analyzer."""
        # Discipline thresholds (league percentiles)
        self.elite_thresholds = {
            'z_contact_pct': 87.0,    # Top 25% zone contact
            'o_swing_pct': 25.0,       # Top 25% chase discipline (lower is better)
            'chase_pct': 25.0,         # Same as O-Swing
            'bb_pct': 10.0,            # Top 25% walk rate
            'k_pct': 20.0,             # Top 25% K avoidance (lower is better)
            'whiff_pct': 23.0          # Top 25% whiff avoidance (lower is better)
        }

        # Average thresholds
        self.average_thresholds = {
            'z_contact_pct': 83.0,
            'o_swing_pct': 30.0,
            'chase_pct': 30.0,
            'bb_pct': 8.0,
            'k_pct': 23.0,
            'whiff_pct': 26.0
        }

    def calculate_discipline_scores(
        self,
        batter_data: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Calculate comprehensive plate discipline scores.

        Components:
        1. Contact ability (Z-Contact%, Whiff%)
        2. Pitch recognition (O-Swing%, Chase%)
        3. Plate patience (BB%, K%)
        4. Sustainability rating

        Args:
            batter_data: DataFrame with FanGraphs plate discipline metrics

        Returns:
            DataFrame with discipline scores added
        """
        result = batter_data.copy()

        # Initialize discipline score components
        result['contact_ability_score'] = 0.0
        result['pitch_recognition_score'] = 0.0
        result['plate_patience_score'] = 0.0
        result['discipline_sustainability_score'] = 0.0

        for idx, batter in result.iterrows():
            scores = self._calculate_individual_discipline(batter)

            result.at[idx, 'contact_ability_score'] = scores['contact']
            result.at[idx, 'pitch_recognition_score'] = scores['recognition']
            result.at[idx, 'plate_patience_score'] = scores['patience']
            result.at[idx, 'discipline_sustainability_score'] = scores['overall']

        # Classify sustainability tiers
        result['discipline_tier'] = pd.cut(
            result['discipline_sustainability_score'],
            bins=[-1, 40, 60, 80, 100],
            labels=['Poor', 'Average', 'Good', 'Elite']
        )

        return result

    def _calculate_individual_discipline(
        self,
        batter: pd.Series
    ) -> Dict[str, float]:
        """
        Calculate individual discipline scores for a batter.

        Args:
            batter: Player data row

        Returns:
            Dictionary of scores
        """
        # Contact Ability Score (0-100)
        contact_score = 0

        z_contact = batter.get('Z-Contact%', np.nan)
        if pd.notna(z_contact):
            if z_contact >= self.elite_thresholds['z_contact_pct']:
                contact_score += 35
            elif z_contact >= self.average_thresholds['z_contact_pct']:
                contact_score += 20
            else:
                contact_score += 10

        whiff_pct = batter.get('SwStr%', np.nan)  # Swinging strike %
        if pd.notna(whiff_pct):
            if whiff_pct <= self.elite_thresholds['whiff_pct']:
                contact_score += 35
            elif whiff_pct <= self.average_thresholds['whiff_pct']:
                contact_score += 20
            else:
                contact_score += 5

        k_pct = batter.get('K%', np.nan)
        if pd.notna(k_pct):
            if k_pct <= self.elite_thresholds['k_pct']:
                contact_score += 30
            elif k_pct <= self.average_thresholds['k_pct']:
                contact_score += 15
            else:
                contact_score += 5

        # Normalize to 100
        contact_score = min(100, contact_score)

        # Pitch Recognition Score (0-100)
        recognition_score = 0

        o_swing = batter.get('O-Swing%', np.nan)
        if pd.notna(o_swing):
            if o_swing <= self.elite_thresholds['o_swing_pct']:
                recognition_score += 50
            elif o_swing <= self.average_thresholds['o_swing_pct']:
                recognition_score += 30
            else:
                recognition_score += 10

        chase = batter.get('Chase%', o_swing)  # Chase% often same as O-Swing%
        if pd.notna(chase):
            if chase <= self.elite_thresholds['chase_pct']:
                recognition_score += 50
            elif chase <= self.average_thresholds['chase_pct']:
                recognition_score += 30
            else:
                recognition_score += 10

        recognition_score = min(100, recognition_score)

        # Plate Patience Score (0-100)
        patience_score = 0

        bb_pct = batter.get('BB%', np.nan)
        if pd.notna(bb_pct):
            if bb_pct >= self.elite_thresholds['bb_pct']:
                patience_score += 50
            elif bb_pct >= self.average_thresholds['bb_pct']:
                patience_score += 30
            else:
                patience_score += 15

        # Swing% (lower can be better for patience)
        swing_pct = batter.get('Swing%', np.nan)
        if pd.notna(swing_pct):
            if swing_pct <= 43:  # Elite patience
                patience_score += 50
            elif swing_pct <= 47:  # Average
                patience_score += 30
            else:
                patience_score += 15

        patience_score = min(100, patience_score)

        # Overall Discipline Score (weighted average)
        # Contact 40%, Recognition 40%, Patience 20%
        overall_score = (
            contact_score * 0.40 +
            recognition_score * 0.40 +
            patience_score * 0.20
        )

        return {
            'contact': contact_score,
            'recognition': recognition_score,
            'patience': patience_score,
            'overall': overall_score
        }

    def compare_discipline_vs_power(
        self,
        batter_data: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Compare plate discipline sustainability vs power outcomes.

        Creates player archetypes:
        1. Elite discipline + elite power (unicorns)
        2. Elite discipline + poor power (grinders)
        3. Poor discipline + elite power (risky sluggers)
        4. Poor discipline + poor power (avoid)

        Args:
            batter_data: Batter data with discipline and power metrics

        Returns:
            DataFrame with archetype classifications
        """
        result = batter_data.copy()

        # Power score based on ISO, barrel rate, HR
        result['power_score'] = 0.0

        for idx, batter in result.iterrows():
            power_score = 0

            iso = batter.get('ISO', 0)
            if iso >= 0.200:
                power_score += 35
            elif iso >= 0.150:
                power_score += 20
            else:
                power_score += 5

            barrel_pct = batter.get('Barrel%', 0)
            if barrel_pct >= 12.0:
                power_score += 35
            elif barrel_pct >= 8.0:
                power_score += 20
            else:
                power_score += 5

            hr = batter.get('HR', 0)
            if hr >= 30:
                power_score += 30
            elif hr >= 20:
                power_score += 20
            elif hr >= 15:
                power_score += 10
            else:
                power_score += 5

            result.at[idx, 'power_score'] = power_score

        # Create archetypes
        def classify_archetype(row):
            disc = row.get('discipline_sustainability_score', 50)
            pwr = row.get('power_score', 50)

            if disc >= 70 and pwr >= 70:
                return 'Unicorn (Elite Disc + Elite Power)'
            elif disc >= 70 and pwr < 70:
                return 'Grinder (Elite Disc + Avg Power)'
            elif disc < 70 and pwr >= 70:
                return 'Risky Slugger (Poor Disc + Elite Power)'
            else:
                return 'Below Average (Poor Disc + Poor Power)'

        result['player_archetype'] = result.apply(classify_archetype, axis=1)

        # Sustainability rating
        # Hypothesis: Elite discipline players age better than power-only players
        def rate_sustainability(row):
            arch = row.get('player_archetype', '')

            if 'Unicorn' in arch:
                return 'Excellent'
            elif 'Grinder' in arch:
                return 'Good'
            elif 'Risky' in arch:
                return 'Poor'
            else:
                return 'Very Poor'

        result['aging_sustainability'] = result.apply(rate_sustainability, axis=1)

        return result

    def identify_discipline_trends(
        self,
        batter_data: pd.DataFrame,
        historical_data: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Calculate plate discipline trends over time.

        Stable or improving discipline = good sign
        Declining discipline = warning sign

        Args:
            batter_data: Current season batter data
            historical_data: Multi-year historical data

        Returns:
            DataFrame with discipline trend metrics
        """
        result = batter_data.copy()
        result['o_swing_trend'] = np.nan
        result['z_contact_trend'] = np.nan
        result['bb_k_trend'] = np.nan
        result['discipline_trend_category'] = 'Unknown'

        for idx, batter in result.iterrows():
            player_name = batter.get('player_name', '')
            if not player_name:
                player_name = batter.get('Name', '')

            # Get historical data for this player
            hist = historical_data[
                historical_data['Name'].str.contains(player_name, case=False, na=False)
            ].sort_values('season') if 'season' in historical_data.columns else pd.DataFrame()

            if len(hist) >= 2:
                # O-Swing trend (lower is better, so negative trend = improvement)
                if 'O-Swing%' in hist.columns:
                    o_swing_values = hist['O-Swing%'].values
                    if len(o_swing_values) >= 2:
                        trend = o_swing_values[-1] - o_swing_values[0]
                        result.at[idx, 'o_swing_trend'] = trend

                # Z-Contact trend (higher is better, so positive trend = improvement)
                if 'Z-Contact%' in hist.columns:
                    z_contact_values = hist['Z-Contact%'].values
                    if len(z_contact_values) >= 2:
                        trend = z_contact_values[-1] - z_contact_values[0]
                        result.at[idx, 'z_contact_trend'] = trend

                # BB/K ratio trend
                if 'BB%' in hist.columns and 'K%' in hist.columns:
                    bb_k_ratio = hist['BB%'] / hist['K%']
                    if len(bb_k_ratio) >= 2:
                        trend = bb_k_ratio.iloc[-1] - bb_k_ratio.iloc[0]
                        result.at[idx, 'bb_k_trend'] = trend

                # Classify trend
                o_swing_trend = result.at[idx, 'o_swing_trend']
                z_contact_trend = result.at[idx, 'z_contact_trend']

                if pd.notna(o_swing_trend) and pd.notna(z_contact_trend):
                    if o_swing_trend <= -2.0 and z_contact_trend >= 1.0:
                        result.at[idx, 'discipline_trend_category'] = 'Improving'
                    elif o_swing_trend >= 2.0 or z_contact_trend <= -1.0:
                        result.at[idx, 'discipline_trend_category'] = 'Declining'
                    else:
                        result.at[idx, 'discipline_trend_category'] = 'Stable'

        return result

    def identify_safe_bets(
        self,
        batter_data: pd.DataFrame,
        min_discipline_score: float = 70
    ) -> pd.DataFrame:
        """
        Identify "safe bet" free agents with elite, sustainable skills.

        Safe bets = elite discipline + stable/improving trends

        Args:
            batter_data: Batter data with discipline metrics
            min_discipline_score: Minimum discipline score

        Returns:
            DataFrame of safe bet candidates
        """
        result = batter_data[
            batter_data['discipline_sustainability_score'] >= min_discipline_score
        ].copy()

        # Further filter by trends if available
        if 'discipline_trend_category' in result.columns:
            result = result[
                result['discipline_trend_category'].isin(['Improving', 'Stable'])
            ]

        result = result.sort_values('discipline_sustainability_score', ascending=False)

        return result[[
            'player_name', 'position', 'age_2025', '2025_war',
            'discipline_sustainability_score', 'player_archetype',
            'aging_sustainability', 'discipline_tier'
        ]].reset_index(drop=True)

    def identify_risky_bets(
        self,
        batter_data: pd.DataFrame,
        max_discipline_score: float = 50
    ) -> pd.DataFrame:
        """
        Identify "risky bet" free agents with poor discipline.

        These players may have good results but unsustainable skills.

        Args:
            batter_data: Batter data
            max_discipline_score: Maximum discipline score for risky

        Returns:
            DataFrame of risky candidates
        """
        result = batter_data[
            (batter_data['discipline_sustainability_score'] <= max_discipline_score) &
            (batter_data.get('2025_war', 0) >= 2.0)  # Good results despite poor discipline
        ].copy()

        result = result.sort_values('discipline_sustainability_score', ascending=True)

        return result[[
            'player_name', 'position', 'age_2025', '2025_war',
            'discipline_sustainability_score', 'player_archetype',
            'aging_sustainability', 'discipline_tier'
        ]].reset_index(drop=True)

    def generate_discipline_report(
        self,
        player_name: str,
        batter_data: pd.DataFrame
    ) -> Dict:
        """
        Generate detailed discipline sustainability report.

        Args:
            player_name: Player name
            batter_data: Batter data

        Returns:
            Dictionary with discipline analysis
        """
        player = batter_data[batter_data['player_name'] == player_name]

        if len(player) == 0:
            # Try matching on FanGraphs Name column
            player = batter_data[batter_data.get('Name', '').str.contains(player_name, case=False, na=False)]

        if len(player) == 0:
            return {'error': f'Player {player_name} not found'}

        player = player.iloc[0]

        report = {
            'player_name': player_name,
            'position': player.get('position', 'N/A'),
            'age': player.get('age_2025', 'N/A'),
            'discipline_sustainability_score': player.get('discipline_sustainability_score', 'N/A'),
            'discipline_tier': player.get('discipline_tier', 'Unknown'),
            'player_archetype': player.get('player_archetype', 'Unknown'),
            'aging_sustainability': player.get('aging_sustainability', 'Unknown'),
            'contact_ability_score': player.get('contact_ability_score', 'N/A'),
            'pitch_recognition_score': player.get('pitch_recognition_score', 'N/A'),
            'plate_patience_score': player.get('plate_patience_score', 'N/A'),
            'power_score': player.get('power_score', 'N/A'),
        }

        # Add raw stats
        report['raw_stats'] = {
            'Z-Contact%': player.get('Z-Contact%', 'N/A'),
            'O-Swing%': player.get('O-Swing%', 'N/A'),
            'BB%': player.get('BB%', 'N/A'),
            'K%': player.get('K%', 'N/A'),
            'Chase%': player.get('Chase%', 'N/A'),
            'Barrel%': player.get('Barrel%', 'N/A'),
            'ISO': player.get('ISO', 'N/A')
        }

        # Add trends if available
        if 'o_swing_trend' in player.index:
            report['trends'] = {
                'o_swing_trend': player.get('o_swing_trend', 'N/A'),
                'z_contact_trend': player.get('z_contact_trend', 'N/A'),
                'bb_k_trend': player.get('bb_k_trend', 'N/A'),
                'trend_category': player.get('discipline_trend_category', 'Unknown')
            }

        return report

    def rank_by_sustainability(
        self,
        batter_data: pd.DataFrame,
        min_war: float = 1.0
    ) -> pd.DataFrame:
        """
        Rank batters by discipline sustainability.

        Args:
            batter_data: Batter data
            min_war: Minimum WAR filter

        Returns:
            Ranked DataFrame
        """
        result = batter_data[
            batter_data.get('2025_war', 0) >= min_war
        ].copy()

        result = result.sort_values('discipline_sustainability_score', ascending=False)

        cols = [
            'player_name', 'position', 'age_2025', '2025_war',
            'discipline_sustainability_score', 'discipline_tier',
            'player_archetype', 'aging_sustainability',
            'contact_ability_score', 'pitch_recognition_score',
            'power_score'
        ]

        return result[cols].reset_index(drop=True)
