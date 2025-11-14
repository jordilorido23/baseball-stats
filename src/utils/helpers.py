"""
General utility functions for baseball analysis.
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Tuple, Optional
from difflib import get_close_matches


def get_current_season_dates() -> Tuple[str, str]:
    """
    Get start and end dates for the current MLB season.

    Returns:
        Tuple of (start_date, end_date) in 'YYYY-MM-DD' format
    """
    current_year = datetime.now().year
    current_month = datetime.now().month

    # MLB season typically runs April - October
    if current_month < 4:
        # Before season starts, use previous year
        season_year = current_year - 1
        start_date = f"{season_year}-04-01"
        end_date = f"{season_year}-10-31"
    elif current_month > 10:
        # After season ends
        start_date = f"{current_year}-04-01"
        end_date = f"{current_year}-10-31"
    else:
        # During season
        start_date = f"{current_year}-04-01"
        end_date = datetime.now().strftime("%Y-%m-%d")

    return start_date, end_date


def get_date_range(days: int) -> Tuple[str, str]:
    """
    Get date range for the last N days.

    Args:
        days: Number of days to look back

    Returns:
        Tuple of (start_date, end_date) in 'YYYY-MM-DD' format
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    return start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")


def filter_qualified_batters(df: pd.DataFrame, min_pa: int = 50) -> pd.DataFrame:
    """
    Filter to qualified batters based on minimum plate appearances.

    Args:
        df: DataFrame with batting data
        min_pa: Minimum plate appearances

    Returns:
        Filtered DataFrame
    """
    if 'PA' in df.columns:
        return df[df['PA'] >= min_pa].copy()
    return df


def filter_qualified_pitchers(df: pd.DataFrame, min_ip: int = 20) -> pd.DataFrame:
    """
    Filter to qualified pitchers based on minimum innings pitched.

    Args:
        df: DataFrame with pitching data
        min_ip: Minimum innings pitched

    Returns:
        Filtered DataFrame
    """
    if 'IP' in df.columns:
        return df[df['IP'] >= min_ip].copy()
    return df


def clean_statcast_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and prepare Statcast data for analysis.

    Args:
        df: Raw Statcast DataFrame

    Returns:
        Cleaned DataFrame
    """
    cleaned = df.copy()

    # Convert date column to datetime if it exists
    if 'game_date' in cleaned.columns:
        cleaned['game_date'] = pd.to_datetime(cleaned['game_date'])

    # Remove nulls from key columns
    key_cols = ['pitch_type', 'release_speed', 'events']
    existing_cols = [col for col in key_cols if col in cleaned.columns]

    if existing_cols:
        cleaned = cleaned.dropna(subset=existing_cols, how='all')

    return cleaned


def summarize_player_season(df: pd.DataFrame, player_type: str = 'batter') -> dict:
    """
    Create a summary of a player's season from Statcast data.

    Args:
        df: Player's Statcast data
        player_type: 'batter' or 'pitcher'

    Returns:
        Dictionary with season summary stats
    """
    summary = {
        'total_pitches': len(df),
        'games_played': df['game_date'].nunique() if 'game_date' in df.columns else 0
    }

    if player_type == 'batter':
        # Batted ball stats
        batted_balls = df[df['type'] == 'X']
        if len(batted_balls) > 0:
            summary.update({
                'batted_balls': len(batted_balls),
                'avg_exit_velo': batted_balls['launch_speed'].mean(),
                'max_exit_velo': batted_balls['launch_speed'].max(),
                'avg_launch_angle': batted_balls['launch_angle'].mean(),
            })

        # Count outcomes
        if 'events' in df.columns:
            events = df['events'].value_counts().to_dict()
            summary['outcomes'] = events

    elif player_type == 'pitcher':
        # Pitch velocity by type
        if 'pitch_type' in df.columns and 'release_speed' in df.columns:
            pitch_velos = df.groupby('pitch_type')['release_speed'].agg(['mean', 'count']).to_dict()
            summary['pitch_arsenal'] = pitch_velos

        # Strikeouts and walks
        if 'events' in df.columns:
            summary['strikeouts'] = (df['events'] == 'strikeout').sum()
            summary['walks'] = (df['events'] == 'walk').sum()

    return summary


def pitch_type_name_map() -> dict:
    """
    Get mapping of pitch type codes to readable names.

    Returns:
        Dictionary mapping codes to names
    """
    return {
        'FF': '4-Seam Fastball',
        'SI': 'Sinker',
        'FC': 'Cutter',
        'SL': 'Slider',
        'CH': 'Changeup',
        'CU': 'Curveball',
        'FS': 'Splitter',
        'KC': 'Knuckle Curve',
        'KN': 'Knuckleball',
        'EP': 'Eephus',
        'FO': 'Forkball',
        'SC': 'Screwball',
        'ST': 'Sweeper'
    }


def export_to_csv(df: pd.DataFrame, filename: str, output_dir: str = "data/exports"):
    """
    Export DataFrame to CSV in the exports directory.

    Args:
        df: DataFrame to export
        filename: Name of the file (with or without .csv extension)
        output_dir: Output directory
    """
    import os

    # Create directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Add .csv extension if not present
    if not filename.endswith('.csv'):
        filename += '.csv'

    filepath = os.path.join(output_dir, filename)
    df.to_csv(filepath, index=False)
    print(f"Exported to {filepath}")


def fuzzy_match_player_name(
    name: str,
    player_list: List[str],
    threshold: float = 0.6,
    max_results: int = 5
) -> List[str]:
    """
    Find player names that closely match the search term.

    Useful for handling name variations, typos, and partial names.

    Args:
        name: Name to search for
        player_list: List of all player names
        threshold: Similarity threshold (0-1, higher = more strict)
        max_results: Maximum number of matches to return

    Returns:
        List of matching player names
    """
    # Use difflib for fuzzy matching
    matches = get_close_matches(
        name,
        player_list,
        n=max_results,
        cutoff=threshold
    )

    # Also try matching if the search term is contained in any name
    contains_matches = [
        player for player in player_list
        if name.lower() in player.lower()
    ]

    # Combine and deduplicate
    all_matches = list(dict.fromkeys(matches + contains_matches))

    return all_matches[:max_results]


def find_player_in_dataframe(
    df: pd.DataFrame,
    player_name: str,
    name_column: str = 'Name',
    fuzzy: bool = True
) -> pd.DataFrame:
    """
    Find player(s) in a DataFrame by name with fuzzy matching support.

    Args:
        df: DataFrame containing player data
        player_name: Name to search for
        name_column: Column containing player names
        fuzzy: Whether to use fuzzy matching

    Returns:
        DataFrame with matching player(s)
    """
    if name_column not in df.columns:
        # Try common alternatives
        alternatives = ['name', 'player_name', 'Name', 'first_name', 'last_name']
        for alt in alternatives:
            if alt in df.columns:
                name_column = alt
                break

    # Try exact match first (case insensitive)
    exact_match = df[df[name_column].str.lower() == player_name.lower()]

    if len(exact_match) > 0:
        return exact_match

    # Try partial match
    partial_match = df[df[name_column].str.contains(player_name, case=False, na=False)]

    if len(partial_match) > 0:
        return partial_match

    # Try fuzzy matching if enabled
    if fuzzy:
        all_names = df[name_column].dropna().tolist()
        fuzzy_matches = fuzzy_match_player_name(player_name, all_names)

        if fuzzy_matches:
            return df[df[name_column].isin(fuzzy_matches)]

    # No matches found
    return pd.DataFrame()


def calculate_percentile_ranks(df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
    """
    Calculate percentile ranks for specified columns.

    Args:
        df: DataFrame with player data
        columns: Columns to calculate percentiles for

    Returns:
        DataFrame with percentile columns added (suffix: '_percentile')
    """
    result = df.copy()

    for col in columns:
        if col in result.columns:
            result[f'{col}_percentile'] = result[col].rank(pct=True) * 100

    return result


def get_percentile_thresholds(
    df: pd.DataFrame,
    column: str,
    percentiles: List[int] = [10, 25, 50, 75, 90]
) -> dict:
    """
    Get values at specific percentiles for a column.

    Args:
        df: DataFrame with data
        column: Column to analyze
        percentiles: List of percentiles to calculate

    Returns:
        Dictionary mapping percentiles to values
    """
    if column not in df.columns:
        return {}

    result = {}
    for pct in percentiles:
        result[f'{pct}th'] = df[column].quantile(pct / 100)

    return result


def categorize_by_percentile(
    value: float,
    thresholds: dict
) -> str:
    """
    Categorize a value based on percentile thresholds.

    Args:
        value: Value to categorize
        thresholds: Dictionary of percentile thresholds

    Returns:
        Category label
    """
    if pd.isna(value):
        return 'Unknown'

    if value >= thresholds.get('90th', float('inf')):
        return 'Elite'
    elif value >= thresholds.get('75th', float('inf')):
        return 'Above Average'
    elif value >= thresholds.get('50th', float('inf')):
        return 'Average'
    elif value >= thresholds.get('25th', float('-inf')):
        return 'Below Average'
    else:
        return 'Poor'


def compare_to_league_average(
    df: pd.DataFrame,
    metric_cols: List[str],
    player_id: Optional[str] = None,
    player_name: Optional[str] = None
) -> pd.DataFrame:
    """
    Compare a player's stats to league average.

    Args:
        df: DataFrame with player data
        metric_cols: Columns to compare
        player_id: Player ID to compare (optional)
        player_name: Player name to compare (optional)

    Returns:
        DataFrame with comparison stats
    """
    # Find player
    if player_id:
        player_data = df[df['playerid'] == player_id]
    elif player_name:
        player_data = find_player_in_dataframe(df, player_name)
    else:
        return pd.DataFrame()

    if len(player_data) == 0:
        return pd.DataFrame()

    # Calculate league averages
    league_avg = df[metric_cols].mean()

    # Get player stats
    player_stats = player_data[metric_cols].iloc[0]

    # Create comparison
    comparison = pd.DataFrame({
        'Metric': metric_cols,
        'Player': [player_stats[col] for col in metric_cols],
        'League Avg': [league_avg[col] for col in metric_cols],
        'Diff': [player_stats[col] - league_avg[col] for col in metric_cols],
        'Percentile': [
            df[col].rank(pct=True).loc[player_data.index[0]] * 100
            if col in df.columns else None
            for col in metric_cols
        ]
    })

    return comparison


def create_player_summary(
    df: pd.DataFrame,
    player_name: str,
    stat_categories: Optional[dict] = None
) -> dict:
    """
    Create a comprehensive summary for a player.

    Args:
        df: DataFrame with player data
        player_name: Name of player
        stat_categories: Dictionary of stat categories and column lists

    Returns:
        Dictionary with organized player stats
    """
    player_data = find_player_in_dataframe(df, player_name)

    if len(player_data) == 0:
        return {'error': f'Player "{player_name}" not found'}

    player = player_data.iloc[0]

    summary = {
        'name': player.get('Name', player_name),
        'age': player.get('Age', 'N/A'),
        'team': player.get('Team', 'N/A'),
    }

    if stat_categories:
        for category, cols in stat_categories.items():
            summary[category] = {
                col: player.get(col, 'N/A')
                for col in cols
                if col in player.index
            }
    else:
        # Include all available stats
        summary['stats'] = player.to_dict()

    return summary
