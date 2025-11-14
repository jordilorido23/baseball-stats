"""
Phase 3: Biomechanical Precision & Durability Analysis

This module analyzes:
- Release Point Deception Strategy (consistency vs variability)
- Fatigue Units (FU) model for injury risk
- Extension & Release Height optimization
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
import pybaseball as pyb
from datetime import datetime, timedelta


class BiomechanicsAnalyzer:
    """Analyzes pitcher biomechanics, durability, and mechanical consistency."""

    # Fatigue Unit coefficients by pitch type and velocity
    FU_COEFFICIENTS = {
        'high_velo': 1.5,    # >95 mph
        'breaking': 1.2,      # Sliders, curves
        'normal': 1.0,        # <95 mph fastballs, changeups
    }

    # FU decay rates
    FU_HALFLIFE_MINUTES = 3.0    # Within-game decay
    FU_RESET_HOURS = 24.0         # Between-game reset

    def __init__(self):
        self.pitch_data = None
        self.game_data = None

    def calculate_release_point_consistency(self, pitch_data: pd.DataFrame) -> Dict:
        """
        Calculate release point standard deviation and classify strategy.

        Consistency (<3 inch SD) = tunneling strategy
        Variability (>6 inch SD) = deception through changing arm slot
        Middle ground (3-6 inch SD) = worst of both worlds

        Args:
            pitch_data: Pitch-level data with release_pos_x, release_pos_z

        Returns:
            Dictionary with release point metrics
        """
        try:
            if pitch_data.empty:
                return {}

            # Calculate standard deviation of release point
            release_x_std = pitch_data['release_pos_x'].std()
            release_z_std = pitch_data['release_pos_z'].std()

            # Combined release point variability (3D distance)
            release_sd = np.sqrt(release_x_std**2 + release_z_std**2)

            # Convert to inches
            release_sd_inches = release_sd * 12

            # Classify strategy
            if release_sd_inches < 3:
                strategy = 'Consistency'
                strategy_score = 90  # Good for tunneling
            elif release_sd_inches > 6:
                strategy = 'Variability'
                strategy_score = 85  # Good for deception
            else:
                strategy = 'Middle'
                strategy_score = 50  # Worst of both worlds

            # Calculate release point drift game-to-game
            game_drift = self.calculate_game_to_game_drift(pitch_data)

            return {
                'Release_Point_SD': release_sd_inches,
                'Release_Point_X_SD': release_x_std * 12,
                'Release_Point_Z_SD': release_z_std * 12,
                'Release_Strategy_Classification': strategy,
                'Release_Strategy_Score': strategy_score,
                'Release_Drift_Game_to_Game': game_drift,
                'Mechanics_Stability': 100 - min(100, game_drift * 10)  # Lower drift = more stable
            }

        except Exception as e:
            return {}

    def calculate_game_to_game_drift(self, pitch_data: pd.DataFrame) -> float:
        """
        Calculate release point drift between games.

        Large drift (>6 inches) indicates mechanical instability.

        Args:
            pitch_data: Pitch data with game_date and release positions

        Returns:
            Average drift in inches between consecutive games
        """
        try:
            if 'game_date' not in pitch_data.columns:
                return np.nan

            # Group by game date
            game_avg_release = pitch_data.groupby('game_date').agg({
                'release_pos_x': 'mean',
                'release_pos_z': 'mean'
            }).reset_index()

            # Sort by date
            game_avg_release = game_avg_release.sort_values('game_date')

            if len(game_avg_release) < 2:
                return np.nan

            # Calculate drift between consecutive games
            drifts = []
            for i in range(1, len(game_avg_release)):
                prev_game = game_avg_release.iloc[i-1]
                curr_game = game_avg_release.iloc[i]

                drift = np.sqrt(
                    (curr_game['release_pos_x'] - prev_game['release_pos_x'])**2 +
                    (curr_game['release_pos_z'] - prev_game['release_pos_z'])**2
                )

                drifts.append(drift * 12)  # Convert to inches

            return np.mean(drifts) if drifts else np.nan

        except Exception as e:
            return np.nan

    def calculate_fatigue_units(self, row: pd.Series) -> float:
        """
        Calculate Fatigue Units (FU) for a single pitch.

        FU accumulation:
        - High-velo pitches (>95 mph) = 1.5 FU
        - Breaking balls = 1.2 FU
        - Fastballs <95 mph, changeups = 1.0 FU

        Args:
            row: Pitch data row

        Returns:
            FU value for this pitch
        """
        try:
            velocity = row.get('release_speed', np.nan)
            pitch_type = row.get('pitch_type', 'FF')

            if pd.isna(velocity):
                return 1.0  # Default FU

            # High velocity threshold
            if velocity > 95:
                return self.FU_COEFFICIENTS['high_velo']

            # Breaking balls
            if pitch_type in ['SL', 'ST', 'CU', 'KC']:
                return self.FU_COEFFICIENTS['breaking']

            # Normal pitches
            return self.FU_COEFFICIENTS['normal']

        except Exception as e:
            return 1.0

    def calculate_fu_load(self, pitch_data: pd.DataFrame, include_decay: bool = True) -> Dict:
        """
        Calculate cumulative Fatigue Unit load with decay modeling.

        FU decay:
        - 3-minute half-life within game
        - 24-hour full reset between games

        Args:
            pitch_data: Pitch-level data with timestamps
            include_decay: Whether to apply decay model

        Returns:
            Dictionary with FU metrics
        """
        try:
            if pitch_data.empty:
                return {}

            # Calculate FU for each pitch
            pitch_data['fu'] = pitch_data.apply(self.calculate_fatigue_units, axis=1)

            # Sort by game_date and pitch time
            pitch_data = pitch_data.sort_values(['game_date', 'at_bat_number', 'pitch_number'])

            if not include_decay:
                # Simple sum
                total_fu = pitch_data['fu'].sum()
                avg_fu_per_game = pitch_data.groupby('game_date')['fu'].sum().mean()

                return {
                    'Fatigue_Units_Total': total_fu,
                    'FU_Per_Game_Avg': avg_fu_per_game,
                }

            # Apply decay model
            cumulative_fu = 0
            fu_by_game = []
            current_game_date = None
            game_fu = 0
            last_pitch_time = None

            for idx, pitch in pitch_data.iterrows():
                game_date = pitch['game_date']

                # Check if new game
                if current_game_date is None or game_date != current_game_date:
                    # New game - reset
                    if current_game_date is not None:
                        fu_by_game.append(game_fu)

                    current_game_date = game_date
                    game_fu = 0
                    last_pitch_time = None
                    cumulative_fu = 0  # Full reset between games (24hr recovery assumed)

                # Add current pitch FU
                pitch_fu = pitch['fu']

                # Apply within-game decay if not first pitch
                if last_pitch_time is not None:
                    # Estimate time between pitches (rough approximation)
                    # Average ~20 seconds between pitches
                    time_delta_minutes = 0.33  # ~20 seconds

                    # Decay: FU_remaining = FU_initial * (0.5)^(time / halflife)
                    decay_factor = 0.5 ** (time_delta_minutes / self.FU_HALFLIFE_MINUTES)
                    cumulative_fu *= decay_factor

                cumulative_fu += pitch_fu
                game_fu += pitch_fu
                last_pitch_time = True  # Placeholder

            # Add last game
            if game_fu > 0:
                fu_by_game.append(game_fu)

            avg_fu_per_game = np.mean(fu_by_game) if fu_by_game else 0

            # Calculate FU risk score (higher = more injury risk)
            # Based on: high total FU + high per-game average
            total_fu = pitch_data['fu'].sum()
            fu_risk_score = min(100, (avg_fu_per_game - 20) * 3)  # Scale so 20 FU/game = 0, 50+ = 100

            return {
                'Fatigue_Units_Total': total_fu,
                'FU_Per_Game_Avg': avg_fu_per_game,
                'FU_Per_Game_Max': max(fu_by_game) if fu_by_game else 0,
                'FU_Risk_Score': max(0, fu_risk_score),
                'Games_Analyzed': len(fu_by_game),
            }

        except Exception as e:
            return {}

    def calculate_extension_metrics(self, pitch_data: pd.DataFrame) -> Dict:
        """
        Calculate extension and release height metrics.

        Extension + Release Height = Plate Distance Advantage

        High extension + low release = flatter VAA (fastball "rise")
        High extension + high release = steeper VAA (downhill plane)

        Args:
            pitch_data: Pitch data with release_extension, release_pos_z

        Returns:
            Dictionary with extension metrics
        """
        try:
            if pitch_data.empty:
                return {}

            # Calculate average extension and release height
            avg_extension = pitch_data['release_extension'].mean()
            avg_release_height = pitch_data['release_pos_z'].mean()

            # Calculate plate distance advantage
            # Extension moves release point closer to plate
            plate_distance = 60.5 - avg_extension

            # Calculate advantage score
            # Elite extension > 6.5 ft
            extension_percentile = self.calculate_percentile(avg_extension, 6.5, 5.5, higher_better=True)

            # Release height optimal range depends on pitch type
            # For fastballs: higher = better (overhand)
            # For breaking balls: moderate height optimal
            fb_data = pitch_data[pitch_data['pitch_type'].isin(['FF', 'SI', 'FC'])]

            if not fb_data.empty:
                fb_release_height = fb_data['release_pos_z'].mean()
                release_height_percentile = self.calculate_percentile(fb_release_height, 6.0, 5.0, higher_better=True)
            else:
                fb_release_height = avg_release_height
                release_height_percentile = 50

            # Plate distance advantage score
            plate_advantage = extension_percentile * 0.7 + release_height_percentile * 0.3

            return {
                'Extension_ft': avg_extension,
                'Extension_Percentile': extension_percentile,
                'Release_Height_ft': avg_release_height,
                'Release_Height_FB_ft': fb_release_height if not fb_data.empty else avg_release_height,
                'Plate_Distance_ft': plate_distance,
                'Plate_Distance_Advantage': plate_advantage,
            }

        except Exception as e:
            return {}

    def calculate_percentile(self, value: float, elite_threshold: float,
                            poor_threshold: float, higher_better: bool = True) -> float:
        """
        Calculate percentile score for a metric.

        Args:
            value: Metric value
            elite_threshold: Value for 90th percentile
            poor_threshold: Value for 10th percentile
            higher_better: Whether higher values are better

        Returns:
            Percentile score 0-100
        """
        try:
            if pd.isna(value):
                return 50

            if higher_better:
                if value >= elite_threshold:
                    return 95
                elif value <= poor_threshold:
                    return 10
                else:
                    # Linear interpolation
                    range_size = elite_threshold - poor_threshold
                    position = (value - poor_threshold) / range_size
                    return 10 + (position * 85)
            else:
                if value <= elite_threshold:
                    return 95
                elif value >= poor_threshold:
                    return 10
                else:
                    # Linear interpolation (inverted)
                    range_size = poor_threshold - elite_threshold
                    position = (value - elite_threshold) / range_size
                    return 95 - (position * 85)

        except Exception as e:
            return 50

    def calculate_durability_score(self, fu_metrics: Dict, release_metrics: Dict) -> float:
        """
        Calculate overall durability score.

        Combines:
        - FU risk (lower = more durable)
        - Mechanics stability (higher = more durable)
        - Extension (higher = biomechanical advantage)

        Returns:
            Durability score 0-100 (higher = more durable)
        """
        try:
            # FU risk (invert so lower risk = higher score)
            fu_risk = fu_metrics.get('FU_Risk_Score', 50)
            fu_score = 100 - fu_risk

            # Mechanics stability
            mechanics_stability = release_metrics.get('Mechanics_Stability', 50)

            # Extension advantage
            extension_score = release_metrics.get('Extension_Percentile', 50)

            # Weighted average
            durability = (
                fu_score * 0.5 +
                mechanics_stability * 0.3 +
                extension_score * 0.2
            )

            return durability

        except Exception as e:
            return 50

    def analyze_pitcher_biomechanics(self, pitch_data: pd.DataFrame, player_name: str) -> Dict:
        """
        Perform complete biomechanics analysis.

        Args:
            pitch_data: Pitch-level Statcast data
            player_name: Player name for logging

        Returns:
            Dictionary with all biomechanics metrics
        """
        print(f"Analyzing biomechanics for {player_name}...")

        results = {'player_name': player_name}

        if pitch_data.empty:
            return results

        # Release point consistency
        release_metrics = self.calculate_release_point_consistency(pitch_data)
        results.update(release_metrics)

        # Fatigue units
        fu_metrics = self.calculate_fu_load(pitch_data, include_decay=True)
        results.update(fu_metrics)

        # Extension metrics
        extension_metrics = self.calculate_extension_metrics(pitch_data)
        results.update(extension_metrics)

        # Overall durability score
        results['Durability_Score'] = self.calculate_durability_score(fu_metrics, release_metrics)

        # Bust risk score (inverse of durability)
        results['Bust_Risk_Score'] = 100 - results['Durability_Score']

        return results

    def analyze_multi_year_fu_trend(self, player_id: int, years: List[int]) -> Dict:
        """
        Calculate multi-year Fatigue Unit trends.

        Increasing FU load over time = injury risk
        Decreasing FU load = reduced usage or mechanics changes

        Args:
            player_id: MLB player ID
            years: List of years to analyze

        Returns:
            Dictionary with trend metrics
        """
        try:
            fu_by_year = {}

            for year in years:
                start_date = f"{year}-03-01"
                end_date = f"{year}-11-01"

                try:
                    pitch_data = pyb.statcast_pitcher(start_date, end_date, player_id)
                    if not pitch_data.empty:
                        fu_metrics = self.calculate_fu_load(pitch_data, include_decay=False)
                        fu_by_year[year] = fu_metrics.get('Fatigue_Units_Total', 0)
                except Exception as e:
                    print(f"Could not fetch data for {year}: {e}")
                    continue

            if len(fu_by_year) < 2:
                return {'FU_Trend_3yr': np.nan}

            # Calculate trend
            years_list = sorted(fu_by_year.keys())
            fu_list = [fu_by_year[y] for y in years_list]

            # Linear regression
            coefficients = np.polyfit(years_list, fu_list, 1)
            trend = coefficients[0]  # Slope

            return {
                'FU_Trend_3yr': trend,
                'FU_By_Year': fu_by_year,
                'FU_Trend_Direction': 'Increasing' if trend > 0 else 'Decreasing'
            }

        except Exception as e:
            return {'FU_Trend_3yr': np.nan}


def analyze_reliever_biomechanics(player_id: int, player_name: str, season: int = 2025) -> Dict:
    """
    Convenience function to analyze a single reliever's biomechanics.

    Args:
        player_id: MLB player ID
        player_name: Player name
        season: Season to analyze

    Returns:
        Dictionary of biomechanics metrics
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

    analyzer = BiomechanicsAnalyzer()
    results = analyzer.analyze_pitcher_biomechanics(pitch_data, player_name)
    results['player_id'] = player_id
    results['season'] = season

    # Add multi-year FU trend
    fu_trend = analyzer.analyze_multi_year_fu_trend(player_id, [season-2, season-1, season])
    results.update(fu_trend)

    return results


if __name__ == "__main__":
    # Test with a sample pitcher
    test_results = analyze_reliever_biomechanics(663961, "Hunter Harvey", 2024)

    print("\nBiomechanics Analysis Results:")
    for key, value in test_results.items():
        if isinstance(value, float):
            print(f"{key}: {value:.2f}")
        elif isinstance(value, dict):
            print(f"{key}:")
            for k, v in value.items():
                print(f"  {k}: {v}")
        else:
            print(f"{key}: {value}")
