"""
Phase 2: Arsenal Synergy & Cognitive Load Analysis

This module analyzes:
- Gyro/Sweeper arsenal combinations
- Effective Velocity by location
- Swing Decision Disruption Index
- Nash Equilibrium score for pitch mix optimization
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
import pybaseball as pyb
from scipy.optimize import linprog


class ArsenalSynergyAnalyzer:
    """Analyzes pitch arsenal synergies and cognitive load optimization."""

    # Discrimination timing factors (milliseconds)
    DISCRIMINATION_TIMES = {
        'FF': 300,  # Fastball
        'SI': 300,  # Sinker
        'FC': 300,  # Cutter
        'SL': 425,  # Slider
        'ST': 425,  # Sweeper
        'CU': 500,  # Curveball
        'KC': 500,  # Knuckle Curve
        'CH': 400,  # Changeup
        'FS': 400,  # Splitter
    }

    def __init__(self):
        self.pitch_data = None

    def classify_breaking_ball_type(self, row: pd.Series) -> str:
        """
        Classify breaking balls by spin axis.

        Gyro slider: spin axis 180-200° (bullet spin)
        Sweeper: spin axis 220-260° (horizontal break)
        Traditional slider: spin axis 200-220°

        Args:
            row: Pitch data row with pitch_type and spin_axis

        Returns:
            Classification: 'Gyro', 'Sweeper', 'Traditional', or original pitch type
        """
        try:
            pitch_type = row.get('pitch_type', '')
            spin_axis = row.get('spin_axis', np.nan)

            # Only classify sliders/sweepers
            if pitch_type not in ['SL', 'ST']:
                return pitch_type

            if pd.isna(spin_axis):
                return pitch_type

            # Normalize spin axis to 0-360
            spin_axis = spin_axis % 360

            # Classify by spin axis
            if 180 <= spin_axis <= 200:
                return 'Gyro'
            elif 220 <= spin_axis <= 260:
                return 'Sweeper'
            else:
                return 'Traditional'

        except Exception as e:
            return row.get('pitch_type', 'Unknown')

    def calculate_arsenal_completeness(self, pitch_data: pd.DataFrame) -> float:
        """
        Calculate how well pitch shapes cover the swing plane matrix.

        Ideal arsenal covers:
        - High/Low vertical zones
        - Arm-side/Glove-side horizontal zones
        - Fast/Slow velocity ranges

        Returns:
            Score 0-100 (higher = more complete arsenal)
        """
        try:
            if pitch_data.empty:
                return np.nan

            # Get pitch locations and movements
            pitch_summary = {}

            for pitch_type in pitch_data['pitch_type'].unique():
                pt_data = pitch_data[pitch_data['pitch_type'] == pitch_type]

                pitch_summary[pitch_type] = {
                    'avg_velo': pt_data['release_speed'].mean(),
                    'avg_pfx_x': pt_data['pfx_x'].mean(),
                    'avg_pfx_z': pt_data['pfx_z'].mean(),
                    'count': len(pt_data)
                }

            # Check coverage dimensions
            score = 0

            # 1. Velocity spread (30 points)
            velocities = [p['avg_velo'] for p in pitch_summary.values() if not pd.isna(p['avg_velo'])]
            if len(velocities) >= 2:
                velo_spread = max(velocities) - min(velocities)
                score += min(30, velo_spread * 2)  # 15+ mph spread = full points

            # 2. Horizontal movement diversity (30 points)
            h_movements = [p['avg_pfx_x'] for p in pitch_summary.values() if not pd.isna(p['avg_pfx_x'])]
            if len(h_movements) >= 2:
                h_spread = max(h_movements) - min(h_movements)
                score += min(30, h_spread * 2)  # 15+ inches spread = full points

            # 3. Vertical movement diversity (30 points)
            v_movements = [p['avg_pfx_z'] for p in pitch_summary.values() if not pd.isna(p['avg_pfx_z'])]
            if len(v_movements) >= 2:
                v_spread = max(v_movements) - min(v_movements)
                score += min(30, v_spread * 2)  # 15+ inches spread = full points

            # 4. Pitch count bonus (10 points)
            num_pitches = len(pitch_summary)
            if num_pitches >= 4:
                score += 10
            elif num_pitches >= 3:
                score += 5

            return min(100, score)

        except Exception as e:
            return np.nan

    def detect_gyro_sweeper_combo(self, pitch_data: pd.DataFrame) -> Dict:
        """
        Detect if pitcher has both gyro slider and sweeper.

        This is a rare and valuable combination (Luke Jackson profile).

        Returns:
            Dictionary with detection results
        """
        try:
            # Classify all breaking balls
            pitch_data['bb_classification'] = pitch_data.apply(
                self.classify_breaking_ball_type, axis=1
            )

            # Count each type
            has_gyro = 'Gyro' in pitch_data['bb_classification'].values
            has_sweeper = 'Sweeper' in pitch_data['bb_classification'].values

            gyro_count = len(pitch_data[pitch_data['bb_classification'] == 'Gyro'])
            sweeper_count = len(pitch_data[pitch_data['bb_classification'] == 'Sweeper'])

            return {
                'Has_Gyro': has_gyro,
                'Has_Sweeper': has_sweeper,
                'Has_Gyro_Sweeper_Combo': has_gyro and has_sweeper,
                'Gyro_Count': gyro_count,
                'Sweeper_Count': sweeper_count,
                'Gyro_Usage_Pct': gyro_count / len(pitch_data) * 100 if len(pitch_data) > 0 else 0,
                'Sweeper_Usage_Pct': sweeper_count / len(pitch_data) * 100 if len(pitch_data) > 0 else 0,
            }

        except Exception as e:
            return {
                'Has_Gyro': False,
                'Has_Sweeper': False,
                'Has_Gyro_Sweeper_Combo': False,
                'Gyro_Count': 0,
                'Sweeper_Count': 0,
                'Gyro_Usage_Pct': 0,
                'Sweeper_Usage_Pct': 0,
            }

    def calculate_effective_velocity(self, row: pd.Series) -> float:
        """
        Calculate location-adjusted perceived velocity.

        Inside pitches: +2-3 mph perceived
        Outside pitches: -1-2 mph perceived
        High pitches: +1 mph perceived
        Low pitches: -1 mph perceived

        Args:
            row: Pitch data with release_speed, plate_x, plate_z

        Returns:
            Effective velocity in mph
        """
        try:
            velocity = row.get('release_speed', np.nan)
            plate_x = row.get('plate_x', np.nan)
            plate_z = row.get('plate_z', np.nan)
            stand = row.get('stand', 'R')  # Batter handedness

            if any(pd.isna([velocity, plate_x, plate_z])):
                return np.nan

            # Start with actual velocity
            ev = velocity

            # Horizontal adjustment (relative to batter)
            # Negative plate_x = inside to RHH, outside to LHH
            # Positive plate_x = outside to RHH, inside to LHH

            if stand == 'R':
                # Negative plate_x = inside
                if plate_x < -0.5:  # Inside
                    ev += 2.5
                elif plate_x < 0:  # Slight inside
                    ev += 1.5
                elif plate_x > 0.5:  # Outside
                    ev -= 1.5
                elif plate_x > 0:  # Slight outside
                    ev -= 0.5
            else:  # LHH
                # Positive plate_x = inside
                if plate_x > 0.5:  # Inside
                    ev += 2.5
                elif plate_x > 0:  # Slight inside
                    ev += 1.5
                elif plate_x < -0.5:  # Outside
                    ev -= 1.5
                elif plate_x < 0:  # Slight outside
                    ev -= 0.5

            # Vertical adjustment
            # Strike zone: roughly 1.5 - 3.5 feet
            if plate_z > 3.0:  # High
                ev += 1.0
            elif plate_z < 2.0:  # Low
                ev -= 1.0

            return ev

        except Exception as e:
            return np.nan

    def calculate_swing_decision_disruption(self, pitch_sequence: pd.DataFrame) -> float:
        """
        Calculate timing disruption score based on pitch sequencing.

        Uses cognitive discrimination times for different pitch types.
        Larger velocity differentials × longer discrimination times = more disruption

        Args:
            pitch_sequence: Sequential pitch data for at-bats

        Returns:
            Disruption index score
        """
        try:
            if len(pitch_sequence) < 2:
                return np.nan

            # Sort by game_date and at_bat_number to get proper sequence
            pitch_sequence = pitch_sequence.sort_values(['game_date', 'at_bat_number', 'pitch_number'])

            disruption_scores = []

            for i in range(1, len(pitch_sequence)):
                prev_pitch = pitch_sequence.iloc[i-1]
                curr_pitch = pitch_sequence.iloc[i]

                # Get velocity differential
                prev_velo = prev_pitch.get('release_speed', np.nan)
                curr_velo = curr_pitch.get('release_speed', np.nan)

                if pd.isna(prev_velo) or pd.isna(curr_velo):
                    continue

                velo_diff = abs(curr_velo - prev_velo)

                # Get discrimination times
                prev_type = prev_pitch.get('pitch_type', 'FF')
                curr_type = curr_pitch.get('pitch_type', 'FF')

                prev_disc_time = self.DISCRIMINATION_TIMES.get(prev_type, 350)
                curr_disc_time = self.DISCRIMINATION_TIMES.get(curr_type, 350)

                # Calculate disruption for this sequence
                # Higher discrimination time + larger velocity differential = more disruption
                avg_disc_time = (prev_disc_time + curr_disc_time) / 2
                disruption = velo_diff * (avg_disc_time / 300)  # Normalize to fastball baseline

                disruption_scores.append(disruption)

            if not disruption_scores:
                return np.nan

            # Return average disruption per pitch
            return np.mean(disruption_scores)

        except Exception as e:
            return np.nan

    def calculate_nash_equilibrium_score(self, pitch_data: pd.DataFrame) -> Dict:
        """
        Calculate Nash Equilibrium score for pitch mix optimization.

        Model pitch selection as zero-sum game:
        - Pitcher's goal: minimize wOBA against
        - Hitter's goal: maximize wOBA

        Returns:
            Dictionary with Nash score and optimization suggestions
        """
        try:
            if pitch_data.empty:
                return {'Nash_Equilibrium_Score': np.nan, 'Pitch_Mix_Efficiency': np.nan}

            # Get pitch type distribution and results
            pitch_summary = {}

            for pitch_type in pitch_data['pitch_type'].unique():
                pt_data = pitch_data[pitch_data['pitch_type'] == pitch_type]

                # Calculate wOBA against this pitch type
                # Use estimated_woba_using_speedangle if available, else calculate from outcomes
                if 'estimated_woba_using_speedangle' in pt_data.columns:
                    avg_woba = pt_data['estimated_woba_using_speedangle'].mean()
                else:
                    # Simplified wOBA calculation from outcomes
                    outcomes = pt_data['events'].value_counts()
                    # This is simplified - real wOBA requires weights
                    avg_woba = 0.3  # Placeholder

                usage_pct = len(pt_data) / len(pitch_data)

                pitch_summary[pitch_type] = {
                    'usage': usage_pct,
                    'woba_against': avg_woba if not pd.isna(avg_woba) else 0.3,
                    'count': len(pt_data)
                }

            # Current weighted average wOBA
            current_woba = sum(
                p['usage'] * p['woba_against']
                for p in pitch_summary.values()
            )

            # Optimal strategy: weight pitches inversely to their wOBA
            # Better pitches (lower wOBA) should be used more
            total_inverse_woba = sum(
                1 / max(p['woba_against'], 0.1)  # Avoid division by zero
                for p in pitch_summary.values()
            )

            optimal_mix = {
                pt: (1 / max(data['woba_against'], 0.1)) / total_inverse_woba
                for pt, data in pitch_summary.items()
            }

            # Calculate optimal wOBA
            optimal_woba = sum(
                optimal_mix[pt] * data['woba_against']
                for pt, data in pitch_summary.items()
            )

            # Nash score: how far from optimal?
            # Lower score = further from optimal = more room for improvement
            woba_improvement_potential = current_woba - optimal_woba

            # Scale to 0-100 (lower = more optimized already)
            nash_score = min(100, max(0, woba_improvement_potential * 500))

            # Efficiency score (inverse of Nash score)
            efficiency = 100 - nash_score

            return {
                'Nash_Equilibrium_Score': nash_score,
                'Pitch_Mix_Efficiency': efficiency,
                'Current_wOBA': current_woba,
                'Optimal_wOBA': optimal_woba,
                'Improvement_Potential': woba_improvement_potential,
                'Current_Mix': {pt: data['usage'] for pt, data in pitch_summary.items()},
                'Optimal_Mix': optimal_mix
            }

        except Exception as e:
            return {'Nash_Equilibrium_Score': np.nan, 'Pitch_Mix_Efficiency': np.nan}

    def calculate_cognitive_load_score(self, pitch_data: pd.DataFrame) -> float:
        """
        Overall cognitive load optimization score.

        Combines:
        - Velocity differentials
        - Timing disruption
        - Arsenal diversity

        Returns:
            Score 0-100 (higher = better cognitive load optimization)
        """
        try:
            score = 0

            # 1. Velocity spread (25 points)
            velocities = pitch_data.groupby('pitch_type')['release_speed'].mean()
            if len(velocities) >= 2:
                velo_spread = velocities.max() - velocities.min()
                score += min(25, velo_spread * 1.5)

            # 2. Timing disruption (35 points)
            disruption = self.calculate_swing_decision_disruption(pitch_data)
            if not pd.isna(disruption):
                # Disruption typically ranges 0-20
                score += min(35, disruption * 2)

            # 3. Arsenal completeness (25 points)
            completeness = self.calculate_arsenal_completeness(pitch_data)
            if not pd.isna(completeness):
                score += completeness * 0.25

            # 4. Effective velocity optimization (15 points)
            pitch_data['effective_velocity'] = pitch_data.apply(
                self.calculate_effective_velocity, axis=1
            )
            ev_std = pitch_data['effective_velocity'].std()
            if not pd.isna(ev_std):
                score += min(15, ev_std * 2)  # Higher variance = better

            return min(100, score)

        except Exception as e:
            return np.nan

    def analyze_pitcher_arsenal(self, pitch_data: pd.DataFrame, player_name: str) -> Dict:
        """
        Perform complete arsenal synergy analysis.

        Args:
            pitch_data: Pitch-level Statcast data
            player_name: Player name for logging

        Returns:
            Dictionary with all arsenal metrics
        """
        print(f"Analyzing arsenal synergy for {player_name}...")

        results = {'player_name': player_name}

        if pitch_data.empty:
            return results

        # Gyro/Sweeper detection
        gyro_sweeper = self.detect_gyro_sweeper_combo(pitch_data)
        results.update(gyro_sweeper)

        # Arsenal completeness
        results['Arsenal_Completeness'] = self.calculate_arsenal_completeness(pitch_data)

        # Effective velocity metrics
        pitch_data['effective_velocity'] = pitch_data.apply(
            self.calculate_effective_velocity, axis=1
        )

        # Overall effective velocity composite
        results['Effective_Velocity_Composite'] = pitch_data['effective_velocity'].mean()
        results['Effective_Velocity_Max'] = pitch_data['effective_velocity'].max()

        # Fastball effective velocity (inside)
        fb_data = pitch_data[pitch_data['pitch_type'].isin(['FF', 'SI', 'FC'])]
        if not fb_data.empty:
            inside_fb = fb_data[
                ((fb_data['stand'] == 'R') & (fb_data['plate_x'] < -0.3)) |
                ((fb_data['stand'] == 'L') & (fb_data['plate_x'] > 0.3))
            ]
            if not inside_fb.empty:
                results['Effective_Velocity_FB_Inside'] = inside_fb['effective_velocity'].mean()

        # Swing decision disruption
        results['Swing_Decision_Disruption_Index'] = self.calculate_swing_decision_disruption(pitch_data)

        # Cognitive load score
        results['Cognitive_Load_Score'] = self.calculate_cognitive_load_score(pitch_data)

        # Nash equilibrium
        nash_results = self.calculate_nash_equilibrium_score(pitch_data)
        results.update(nash_results)

        # Arsenal synergy composite score
        synergy_components = [
            results.get('Arsenal_Completeness', 0) * 0.3,
            results.get('Cognitive_Load_Score', 0) * 0.3,
            (100 - results.get('Nash_Equilibrium_Score', 50)) * 0.2,  # Lower Nash = better
            (results.get('Has_Gyro_Sweeper_Combo', False) * 20),  # Bonus for combo
        ]
        results['Arsenal_Synergy_Score'] = sum(synergy_components)

        return results


def analyze_reliever_arsenal(player_id: int, player_name: str, season: int = 2025) -> Dict:
    """
    Convenience function to analyze a single reliever's arsenal synergy.

    Args:
        player_id: MLB player ID
        player_name: Player name
        season: Season to analyze

    Returns:
        Dictionary of arsenal synergy metrics
    """
    import pybaseball as pyb

    print(f"Fetching data for {player_name}...")

    start_date = f"{season}-03-01"
    end_date = f"{season}-11-01"

    try:
        pitch_data = pyb.statcast_pitcher(start_date, end_date, player_id)
    except Exception as e:
        print(f"Error fetching data: {e}")
        return {'player_name': player_name, 'error': str(e)}

    analyzer = ArsenalSynergyAnalyzer()
    results = analyzer.analyze_pitcher_arsenal(pitch_data, player_name)
    results['player_id'] = player_id
    results['season'] = season

    return results


if __name__ == "__main__":
    # Test with a sample pitcher
    test_results = analyze_reliever_arsenal(663961, "Hunter Harvey", 2024)

    print("\nArsenal Synergy Results:")
    for key, value in test_results.items():
        if isinstance(value, float):
            print(f"{key}: {value:.2f}")
        elif isinstance(value, dict):
            print(f"{key}:")
            for k, v in value.items():
                print(f"  {k}: {v}")
        else:
            print(f"{key}: {value}")
