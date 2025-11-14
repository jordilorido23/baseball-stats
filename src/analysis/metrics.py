"""
Advanced baseball metrics and statistical calculations.
"""
import pandas as pd
import numpy as np
from typing import Union, Optional


def calculate_woba(df: pd.DataFrame) -> pd.Series:
    """
    Calculate wOBA (weighted On-Base Average) from Statcast data.

    wOBA weights different hitting outcomes by their run value.

    Args:
        df: DataFrame with Statcast data containing 'events' column

    Returns:
        Series with wOBA values
    """
    # Standard wOBA weights (2024 approximation)
    weights = {
        'walk': 0.69,
        'hit_by_pitch': 0.72,
        'single': 0.88,
        'double': 1.24,
        'triple': 1.56,
        'home_run': 2.08
    }

    # Calculate wOBA for each plate appearance
    woba_values = df['events'].map(weights).fillna(0)

    return woba_values


def calculate_barrel_rate(df: pd.DataFrame) -> float:
    """
    Calculate barrel rate from Statcast data.

    A barrel is defined as a batted ball with ideal launch angle (26-30 degrees)
    and exit velocity (98+ mph) combination.

    Args:
        df: DataFrame with 'launch_speed' and 'launch_angle' columns

    Returns:
        Barrel rate as a percentage
    """
    batted_balls = df.dropna(subset=['launch_speed', 'launch_angle'])

    if len(batted_balls) == 0:
        return 0.0

    # Simplified barrel definition
    # More precise definition would use a curve based on exit velo
    barrels = (
        (batted_balls['launch_speed'] >= 98) &
        (batted_balls['launch_angle'] >= 26) &
        (batted_balls['launch_angle'] <= 30)
    )

    return (barrels.sum() / len(batted_balls)) * 100


def calculate_hard_hit_rate(df: pd.DataFrame, threshold: float = 95.0) -> float:
    """
    Calculate hard hit rate (percentage of batted balls >= threshold mph).

    Args:
        df: DataFrame with 'launch_speed' column
        threshold: Exit velocity threshold for "hard hit" (default 95 mph)

    Returns:
        Hard hit rate as a percentage
    """
    batted_balls = df.dropna(subset=['launch_speed'])

    if len(batted_balls) == 0:
        return 0.0

    hard_hit = batted_balls['launch_speed'] >= threshold
    return (hard_hit.sum() / len(batted_balls)) * 100


def calculate_whiff_rate(df: pd.DataFrame) -> float:
    """
    Calculate whiff rate (swings and misses / total swings).

    Args:
        df: DataFrame with 'description' column from Statcast

    Returns:
        Whiff rate as a percentage
    """
    # Swing descriptions
    swings = df['description'].isin([
        'swinging_strike',
        'swinging_strike_blocked',
        'foul',
        'foul_tip',
        'hit_into_play',
        'foul_bunt',
        'missed_bunt'
    ])

    # Whiff descriptions
    whiffs = df['description'].isin([
        'swinging_strike',
        'swinging_strike_blocked',
        'missed_bunt'
    ])

    total_swings = swings.sum()
    if total_swings == 0:
        return 0.0

    return (whiffs.sum() / total_swings) * 100


def calculate_chase_rate(df: pd.DataFrame) -> float:
    """
    Calculate chase rate (swings at pitches outside the zone / pitches outside zone).

    Args:
        df: DataFrame with 'zone' and 'description' columns

    Returns:
        Chase rate as a percentage
    """
    # Pitches outside the zone (zone > 9 in Statcast data)
    outside_zone = df['zone'] > 9

    # Swings (same as whiff rate)
    swings = df['description'].isin([
        'swinging_strike',
        'swinging_strike_blocked',
        'foul',
        'foul_tip',
        'hit_into_play',
        'foul_bunt',
        'missed_bunt'
    ])

    pitches_outside = outside_zone.sum()
    if pitches_outside == 0:
        return 0.0

    chases = (outside_zone & swings).sum()
    return (chases / pitches_outside) * 100


def calculate_zone_contact_rate(df: pd.DataFrame) -> float:
    """
    Calculate contact rate on pitches inside the strike zone.

    Args:
        df: DataFrame with 'zone' and 'description' columns

    Returns:
        Zone contact rate as a percentage
    """
    # Pitches in the zone (zone 1-9)
    in_zone = (df['zone'] >= 1) & (df['zone'] <= 9)

    # Swings
    swings = df['description'].isin([
        'swinging_strike',
        'swinging_strike_blocked',
        'foul',
        'foul_tip',
        'hit_into_play',
        'foul_bunt',
        'missed_bunt'
    ])

    # Contact (not a whiff)
    contact = df['description'].isin([
        'foul',
        'foul_tip',
        'hit_into_play',
        'foul_bunt'
    ])

    zone_swings = (in_zone & swings).sum()
    if zone_swings == 0:
        return 0.0

    zone_contact = (in_zone & contact).sum()
    return (zone_contact / zone_swings) * 100


def calculate_expected_stats(df: pd.DataFrame) -> dict:
    """
    Calculate expected batting average, slugging, and wOBA based on
    batted ball quality (simplified version).

    Args:
        df: DataFrame with Statcast batted ball data

    Returns:
        Dictionary with xBA, xSLG, xwOBA
    """
    batted_balls = df.dropna(subset=['launch_speed', 'launch_angle'])

    if len(batted_balls) == 0:
        return {'xBA': 0.0, 'xSLG': 0.0, 'xwOBA': 0.0}

    # Simplified expected stats based on exit velo and launch angle
    # Real xStats use more sophisticated models

    # xBA - rough approximation
    hard_optimal_angle = (
        (batted_balls['launch_speed'] >= 90) &
        (batted_balls['launch_angle'] >= 10) &
        (batted_balls['launch_angle'] <= 35)
    )
    xBA = hard_optimal_angle.mean()

    # xSLG - rough approximation
    elite_contact = (
        (batted_balls['launch_speed'] >= 95) &
        (batted_balls['launch_angle'] >= 20) &
        (batted_balls['launch_angle'] <= 35)
    )
    xSLG = xBA + (elite_contact.mean() * 1.5)  # Simplified

    # xwOBA - rough approximation
    xwOBA = 0.3 + (hard_optimal_angle.mean() * 0.3)

    return {
        'xBA': round(xBA, 3),
        'xSLG': round(xSLG, 3),
        'xwOBA': round(xwOBA, 3)
    }


def get_pitch_arsenal_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Summarize a pitcher's arsenal with average velocity, spin, and usage.

    Args:
        df: DataFrame with pitcher's Statcast data

    Returns:
        DataFrame with pitch type summary
    """
    pitch_summary = df.groupby('pitch_type').agg({
        'release_speed': ['mean', 'std'],
        'release_spin_rate': 'mean',
        'pitch_type': 'count'
    }).round(1)

    # Flatten column names
    pitch_summary.columns = ['avg_velo', 'velo_std', 'avg_spin', 'count']

    # Calculate usage percentage
    pitch_summary['usage_pct'] = (pitch_summary['count'] / pitch_summary['count'].sum() * 100).round(1)

    # Sort by usage
    pitch_summary = pitch_summary.sort_values('usage_pct', ascending=False)

    return pitch_summary


def calculate_plate_discipline_metrics(df: pd.DataFrame) -> dict:
    """
    Calculate comprehensive plate discipline metrics for a batter.

    Args:
        df: DataFrame with batter's Statcast data

    Returns:
        Dictionary with various plate discipline metrics
    """
    return {
        'whiff_rate': round(calculate_whiff_rate(df), 1),
        'chase_rate': round(calculate_chase_rate(df), 1),
        'zone_contact_rate': round(calculate_zone_contact_rate(df), 1),
    }


def calculate_batted_ball_profile(df: pd.DataFrame) -> dict:
    """
    Calculate batted ball profile metrics.

    Args:
        df: DataFrame with Statcast batted ball data

    Returns:
        Dictionary with batted ball metrics
    """
    batted_balls = df.dropna(subset=['launch_speed', 'launch_angle'])

    if len(batted_balls) == 0:
        return {
            'avg_exit_velo': 0.0,
            'max_exit_velo': 0.0,
            'avg_launch_angle': 0.0,
            'hard_hit_rate': 0.0,
            'barrel_rate': 0.0
        }

    return {
        'avg_exit_velo': round(batted_balls['launch_speed'].mean(), 1),
        'max_exit_velo': round(batted_balls['launch_speed'].max(), 1),
        'avg_launch_angle': round(batted_balls['launch_angle'].mean(), 1),
        'hard_hit_rate': round(calculate_hard_hit_rate(batted_balls), 1),
        'barrel_rate': round(calculate_barrel_rate(batted_balls), 1)
    }
