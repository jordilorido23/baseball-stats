"""
Phase 1: Pitch Trajectory & Deception Physics Analysis

This module analyzes:
- Vertical Approach Angle (VAA) - pitch trajectory physics
- Seam-Shifted Wake (SSW) - unexplained movement from seam effects
- Pitch Tunneling - deception through trajectory similarity
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
import pybaseball as pyb
from datetime import datetime


class PitchPhysicsAnalyzer:
    """Analyzes pitch trajectory physics, SSW effects, and tunneling."""

    def __init__(self):
        self.pitch_data = None

    def fetch_statcast_data(self, player_id: int, start_date: str, end_date: str) -> pd.DataFrame:
        """Fetch pitch-level Statcast data for a player."""
        try:
            # Use pybaseball's statcast_pitcher function
            data = pyb.statcast_pitcher(start_date, end_date, player_id)
            return data
        except Exception as e:
            print(f"Error fetching data for player {player_id}: {e}")
            return pd.DataFrame()

    def calculate_vaa(self, row: pd.Series) -> float:
        """
        Calculate Vertical Approach Angle (VAA) at plate crossing.

        VAA = arctan(vz / sqrt(vx^2 + vy^2))

        Args:
            row: Pandas Series with vx0, vy0, vz0 (velocity components at release)
                 and ax, ay, az (acceleration components)

        Returns:
            VAA in degrees (negative values = downward angle)
        """
        try:
            # Get velocity components at release point
            vx0 = row.get('vx0', np.nan)
            vy0 = row.get('vy0', np.nan)
            vz0 = row.get('vz0', np.nan)

            # Get acceleration components
            ax = row.get('ax', np.nan)
            ay = row.get('ay', np.nan)
            az = row.get('az', np.nan)

            # Get release extension and plate distance
            release_extension = row.get('release_extension', 6.0)
            plate_distance = 60.5 - release_extension  # Distance from release to plate

            # Check for missing values
            if any(pd.isna([vx0, vy0, vz0, ax, ay, az])):
                return np.nan

            # Calculate time to plate (solving quadratic equation)
            # Distance equation: y = vy0*t + 0.5*ay*t^2
            # Solve: 0.5*ay*t^2 + vy0*t - plate_distance = 0
            a_coef = 0.5 * ay
            b_coef = vy0
            c_coef = -plate_distance

            discriminant = b_coef**2 - 4*a_coef*c_coef
            if discriminant < 0:
                return np.nan

            t_plate = (-b_coef - np.sqrt(discriminant)) / (2*a_coef)

            if t_plate <= 0:
                return np.nan

            # Calculate velocity components at plate
            vx_plate = vx0 + ax * t_plate
            vy_plate = vy0 + ay * t_plate
            vz_plate = vz0 + az * t_plate

            # Calculate VAA in degrees
            horizontal_velocity = np.sqrt(vx_plate**2 + vy_plate**2)
            vaa_radians = np.arctan(vz_plate / horizontal_velocity)
            vaa_degrees = np.degrees(vaa_radians)

            return vaa_degrees

        except Exception as e:
            return np.nan

    def classify_vaa(self, vaa: float) -> str:
        """Classify VAA into categories."""
        if pd.isna(vaa):
            return 'Unknown'

        # Note: VAA is typically negative (downward angle)
        abs_vaa = abs(vaa)

        if abs_vaa < 4:
            return 'Flat'
        elif abs_vaa < 6:
            return 'Moderate'
        else:
            return 'Steep'

    def calculate_expected_movement(self, row: pd.Series) -> Tuple[float, float]:
        """
        Calculate expected pitch movement from spin parameters.

        Uses Magnus force equations to predict movement.

        Returns:
            (expected_pfx_x, expected_pfx_z) in inches
        """
        try:
            spin_rate = row.get('release_spin_rate', np.nan)
            velocity = row.get('release_speed', np.nan)
            spin_axis = row.get('spin_axis', np.nan)  # degrees

            if any(pd.isna([spin_rate, velocity, spin_axis])):
                return np.nan, np.nan

            # Convert spin axis to radians
            spin_axis_rad = np.radians(spin_axis)

            # Magnus force coefficient (simplified)
            # Movement ∝ spin_rate × velocity × sin(spin_axis)
            # Empirical scaling factor for Statcast data
            magnus_coefficient = 0.00004

            # Calculate expected movement components
            # pfx_x: horizontal movement (catcher's perspective, + = right)
            # pfx_z: vertical movement (+ = rise)

            # Time of flight (approximate, in seconds)
            distance = 60.5 - row.get('release_extension', 6.0)
            time_flight = distance / (velocity * 1.467)  # Convert mph to ft/s

            # Magnus force creates movement perpendicular to spin axis
            expected_pfx_x = magnus_coefficient * spin_rate * velocity * np.sin(spin_axis_rad) * time_flight * 12
            expected_pfx_z = magnus_coefficient * spin_rate * velocity * np.cos(spin_axis_rad) * time_flight * 12

            return expected_pfx_x, expected_pfx_z

        except Exception as e:
            return np.nan, np.nan

    def calculate_ssw_effect(self, row: pd.Series) -> Tuple[float, float, float]:
        """
        Calculate Seam-Shifted Wake (SSW) effect.

        SSW = Actual Movement - Expected Movement from Spin

        Returns:
            (ssw_x, ssw_z, ssw_total) in inches
        """
        try:
            # Get actual movement
            actual_pfx_x = row.get('pfx_x', np.nan)
            actual_pfx_z = row.get('pfx_z', np.nan)

            # Get expected movement
            expected_pfx_x, expected_pfx_z = self.calculate_expected_movement(row)

            if any(pd.isna([actual_pfx_x, actual_pfx_z, expected_pfx_x, expected_pfx_z])):
                return np.nan, np.nan, np.nan

            # Calculate SSW differential
            ssw_x = actual_pfx_x - expected_pfx_x
            ssw_z = actual_pfx_z - expected_pfx_z
            ssw_total = np.sqrt(ssw_x**2 + ssw_z**2)

            return ssw_x, ssw_z, ssw_total

        except Exception as e:
            return np.nan, np.nan, np.nan

    def calculate_tunneling_distance(self, trajectory1: np.ndarray, trajectory2: np.ndarray) -> float:
        """
        Calculate 3D Euclidean distance between two pitch trajectories at decision point.

        Decision point ≈ 150ms before contact ≈ 20 feet from plate

        Args:
            trajectory1, trajectory2: Arrays of [x, y, z] positions along trajectory

        Returns:
            Distance in inches at decision point
        """
        try:
            # Decision point is 20 feet from home plate
            decision_point_distance = 20.0

            # Find positions at decision point for both trajectories
            # This is a simplified version - in practice we'd interpolate
            pos1 = trajectory1  # [x, y, z] at decision point
            pos2 = trajectory2  # [x, y, z] at decision point

            # Calculate 3D Euclidean distance
            distance = np.sqrt(np.sum((pos1 - pos2)**2))

            return distance * 12  # Convert feet to inches

        except Exception as e:
            return np.nan

    def analyze_pitcher(self, player_id: int, start_date: str, end_date: str) -> Dict:
        """
        Perform complete pitch physics analysis for a pitcher.

        Returns dictionary with all physics metrics.
        """
        # Fetch pitch-level data
        pitch_data = self.fetch_statcast_data(player_id, start_date, end_date)

        if pitch_data.empty:
            return {}

        # Calculate VAA for each pitch
        pitch_data['vaa'] = pitch_data.apply(self.calculate_vaa, axis=1)
        pitch_data['vaa_classification'] = pitch_data['vaa'].apply(self.classify_vaa)

        # Calculate SSW effects
        ssw_results = pitch_data.apply(self.calculate_ssw_effect, axis=1, result_type='expand')
        pitch_data['ssw_x'] = ssw_results[0]
        pitch_data['ssw_z'] = ssw_results[1]
        pitch_data['ssw_total'] = ssw_results[2]

        # Group by pitch type for aggregation
        pitch_types = pitch_data['pitch_type'].dropna().unique()

        results = {
            'player_id': player_id,
            'total_pitches': len(pitch_data)
        }

        # Calculate metrics by pitch type
        for pitch_type in pitch_types:
            pt_data = pitch_data[pitch_data['pitch_type'] == pitch_type]

            prefix = f"{pitch_type}_"

            # VAA metrics
            results[f'{prefix}vaa_avg'] = pt_data['vaa'].mean()
            results[f'{prefix}vaa_std'] = pt_data['vaa'].std()

            # SSW metrics
            results[f'{prefix}ssw_x_avg'] = pt_data['ssw_x'].mean()
            results[f'{prefix}ssw_z_avg'] = pt_data['ssw_z'].mean()
            results[f'{prefix}ssw_total_avg'] = pt_data['ssw_total'].mean()

            # Count
            results[f'{prefix}count'] = len(pt_data)

        # Overall metrics (typically for fastballs)
        fb_data = pitch_data[pitch_data['pitch_type'].isin(['FF', 'SI', 'FC'])]

        if not fb_data.empty:
            results['VAA_FB_avg'] = fb_data['vaa'].mean()
            results['VAA_classification'] = fb_data['vaa'].apply(self.classify_vaa).mode()[0] if len(fb_data) > 0 else 'Unknown'
            results['SSW_Movement_FB'] = fb_data['ssw_total'].mean()

        # Calculate VAA-Zone mismatch score
        results['VAA_Zone_Mismatch_Score'] = self.calculate_vaa_zone_mismatch(pitch_data)

        # Calculate tunneling score (requires multiple pitch types)
        results['Tunneling_Score'] = self.calculate_tunneling_score(pitch_data)

        return results

    def calculate_vaa_zone_mismatch(self, pitch_data: pd.DataFrame) -> float:
        """
        Calculate how well pitcher is using their VAA profile.

        Flat VAA pitchers should throw high in zone.
        Steep VAA pitchers should throw low in zone.

        Returns score 0-100 (higher = better optimization)
        """
        try:
            fb_data = pitch_data[pitch_data['pitch_type'].isin(['FF', 'SI', 'FC'])]

            if fb_data.empty:
                return np.nan

            # Get average VAA
            avg_vaa = fb_data['vaa'].mean()

            if pd.isna(avg_vaa):
                return np.nan

            # Get average plate_z (vertical location)
            avg_plate_z = fb_data['plate_z'].mean()

            if pd.isna(avg_plate_z):
                return np.nan

            # Strike zone midpoint is approximately 2.5 feet
            zone_midpoint = 2.5

            # Flat VAA (< 4°) should throw high (plate_z > 2.8)
            # Steep VAA (> 6°) should throw low (plate_z < 2.2)

            abs_vaa = abs(avg_vaa)

            if abs_vaa < 4:  # Flat VAA
                # Score based on how high they throw
                optimal_zone = 3.0
                distance_from_optimal = abs(avg_plate_z - optimal_zone)
                score = max(0, 100 - (distance_from_optimal * 100))
            elif abs_vaa > 6:  # Steep VAA
                # Score based on how low they throw
                optimal_zone = 2.0
                distance_from_optimal = abs(avg_plate_z - optimal_zone)
                score = max(0, 100 - (distance_from_optimal * 100))
            else:  # Moderate VAA
                # Middle of zone is fine
                optimal_zone = 2.5
                distance_from_optimal = abs(avg_plate_z - optimal_zone)
                score = max(0, 100 - (distance_from_optimal * 80))

            return score

        except Exception as e:
            return np.nan

    def calculate_tunneling_score(self, pitch_data: pd.DataFrame) -> float:
        """
        Calculate pitch tunneling coherence score.

        Measures how well different pitches tunnel at the decision point.

        Returns score 0-100 (higher = better tunneling)
        """
        try:
            # Get most common pitch types
            pitch_types = pitch_data['pitch_type'].value_counts()

            if len(pitch_types) < 2:
                return np.nan

            # Focus on FB-SL tunneling as primary metric
            fb_data = pitch_data[pitch_data['pitch_type'].isin(['FF', 'SI', 'FC'])]
            sl_data = pitch_data[pitch_data['pitch_type'].isin(['SL', 'ST'])]

            if fb_data.empty or sl_data.empty:
                return np.nan

            # Calculate average release point for each pitch type
            fb_release_x = fb_data['release_pos_x'].mean()
            fb_release_z = fb_data['release_pos_z'].mean()
            sl_release_x = sl_data['release_pos_x'].mean()
            sl_release_z = sl_data['release_pos_z'].mean()

            # Calculate release point separation (smaller = better tunneling)
            release_separation = np.sqrt(
                (fb_release_x - sl_release_x)**2 +
                (fb_release_z - sl_release_z)**2
            )

            # Calculate plate location separation (larger = more deception after tunnel)
            fb_plate_x = fb_data['plate_x'].mean()
            fb_plate_z = fb_data['plate_z'].mean()
            sl_plate_x = sl_data['plate_x'].mean()
            sl_plate_z = sl_data['plate_z'].mean()

            plate_separation = np.sqrt(
                (fb_plate_x - sl_plate_x)**2 +
                (fb_plate_z - sl_plate_z)**2
            )

            # Good tunneling = small release separation, large plate separation
            # Tunneling Score = (plate_separation / (release_separation + 0.1)) * scaling

            if release_separation < 0.2:  # Very tight release point
                if plate_separation > 0.8:  # Good separation at plate
                    score = 90 + min(10, plate_separation * 5)
                elif plate_separation > 0.5:
                    score = 70 + (plate_separation - 0.5) * 40
                else:
                    score = 50 + plate_separation * 40
            else:
                # Penalize for loose release point
                score = max(0, 50 - (release_separation - 0.2) * 100)

            return min(100, max(0, score))

        except Exception as e:
            return np.nan

    def calculate_ssw_trend(self, player_id: int, years: List[int]) -> float:
        """
        Calculate multi-year trend in SSW movement.

        Declining SSW can indicate injury or mechanical issues.

        Args:
            player_id: MLB player ID
            years: List of years to analyze (e.g., [2023, 2024, 2025])

        Returns:
            Trend coefficient (negative = declining SSW)
        """
        try:
            ssw_by_year = []

            for year in years:
                start_date = f"{year}-03-01"
                end_date = f"{year}-11-01"

                pitch_data = self.fetch_statcast_data(player_id, start_date, end_date)

                if not pitch_data.empty:
                    ssw_results = pitch_data.apply(self.calculate_ssw_effect, axis=1, result_type='expand')
                    avg_ssw = ssw_results[2].mean()  # Total SSW
                    ssw_by_year.append(avg_ssw)
                else:
                    ssw_by_year.append(np.nan)

            # Calculate trend using linear regression
            valid_years = [(year, ssw) for year, ssw in zip(years, ssw_by_year) if not pd.isna(ssw)]

            if len(valid_years) < 2:
                return np.nan

            x = np.array([y[0] for y in valid_years])
            y = np.array([y[1] for y in valid_years])

            # Linear regression: y = mx + b
            coefficients = np.polyfit(x, y, 1)
            trend = coefficients[0]  # Slope

            return trend

        except Exception as e:
            return np.nan


def analyze_reliever_physics(player_id: int, player_name: str, season: int = 2025) -> Dict:
    """
    Convenience function to analyze a single reliever's pitch physics.

    Args:
        player_id: MLB player ID
        player_name: Player name (for logging)
        season: Season to analyze

    Returns:
        Dictionary of physics metrics
    """
    print(f"Analyzing pitch physics for {player_name} (ID: {player_id})...")

    analyzer = PitchPhysicsAnalyzer()

    start_date = f"{season}-03-01"
    end_date = f"{season}-11-01"

    results = analyzer.analyze_pitcher(player_id, start_date, end_date)
    results['player_name'] = player_name
    results['season'] = season

    # Calculate 3-year SSW trend
    results['SSW_Trend_3yr'] = analyzer.calculate_ssw_trend(player_id, [season-2, season-1, season])

    return results


if __name__ == "__main__":
    # Test with a sample pitcher (e.g., Hunter Harvey - player_id: 663961)
    test_results = analyze_reliever_physics(663961, "Hunter Harvey", 2024)

    print("\nPhysics Analysis Results:")
    for key, value in test_results.items():
        if isinstance(value, float):
            print(f"{key}: {value:.2f}")
        else:
            print(f"{key}: {value}")
