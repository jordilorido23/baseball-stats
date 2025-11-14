"""
Visualization utilities for baseball analysis.
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Optional, List, Tuple


def plot_pitch_location(
    df: pd.DataFrame,
    pitch_type: Optional[str] = None,
    title: Optional[str] = None,
    figsize: Tuple[int, int] = (10, 10)
) -> plt.Figure:
    """
    Plot pitch locations from catcher's perspective.

    Args:
        df: DataFrame with Statcast data (plate_x, plate_z columns)
        pitch_type: Filter to specific pitch type (e.g., 'FF', 'SL')
        title: Plot title
        figsize: Figure size

    Returns:
        matplotlib Figure object
    """
    # Filter data
    plot_df = df.dropna(subset=['plate_x', 'plate_z']).copy()
    if pitch_type:
        plot_df = plot_df[plot_df['pitch_type'] == pitch_type]

    # Create figure
    fig, ax = plt.subplots(figsize=figsize)

    # Draw strike zone
    # Standard strike zone: 17 inches wide (±8.5 inches from center)
    # Height varies by batter, using typical zone
    strike_zone_x = [-8.5/12, 8.5/12, 8.5/12, -8.5/12, -8.5/12]
    strike_zone_z = [1.5, 1.5, 3.5, 3.5, 1.5]
    ax.plot(strike_zone_x, strike_zone_z, 'k-', linewidth=2, label='Strike Zone')

    # Plot pitches
    if 'pitch_type' in plot_df.columns and not pitch_type:
        # Color by pitch type
        for ptype in plot_df['pitch_type'].unique():
            mask = plot_df['pitch_type'] == ptype
            ax.scatter(
                plot_df[mask]['plate_x'],
                plot_df[mask]['plate_z'],
                alpha=0.5,
                s=50,
                label=ptype
            )
        ax.legend()
    else:
        # Single color
        ax.scatter(
            plot_df['plate_x'],
            plot_df['plate_z'],
            alpha=0.5,
            s=50,
            c='blue'
        )

    # Set limits and labels
    ax.set_xlim(-2, 2)
    ax.set_ylim(0, 5)
    ax.set_xlabel('Horizontal Location (ft, catcher view)', fontsize=12)
    ax.set_ylabel('Height (ft)', fontsize=12)
    ax.set_title(title or 'Pitch Locations', fontsize=14, fontweight='bold')
    ax.grid(alpha=0.3)
    ax.set_aspect('equal')

    plt.tight_layout()
    return fig


def plot_pitch_movement(
    df: pd.DataFrame,
    figsize: Tuple[int, int] = (12, 10)
) -> plt.Figure:
    """
    Plot pitch movement (horizontal and vertical break).

    Args:
        df: DataFrame with Statcast data (pfx_x, pfx_z columns)
        figsize: Figure size

    Returns:
        matplotlib Figure object
    """
    # Filter data
    plot_df = df.dropna(subset=['pfx_x', 'pfx_z', 'pitch_type']).copy()

    # Convert inches to feet
    plot_df['pfx_x_ft'] = plot_df['pfx_x'] / 12
    plot_df['pfx_z_ft'] = plot_df['pfx_z'] / 12

    # Create figure
    fig, ax = plt.subplots(figsize=figsize)

    # Plot by pitch type
    for ptype in plot_df['pitch_type'].unique():
        mask = plot_df['pitch_type'] == ptype
        ax.scatter(
            plot_df[mask]['pfx_x_ft'],
            plot_df[mask]['pfx_z_ft'],
            alpha=0.6,
            s=80,
            label=ptype
        )

    # Add reference lines
    ax.axhline(y=0, color='k', linestyle='--', alpha=0.3)
    ax.axvline(x=0, color='k', linestyle='--', alpha=0.3)

    ax.set_xlabel('Horizontal Break (ft, from pitcher perspective)', fontsize=12)
    ax.set_ylabel('Induced Vertical Break (ft)', fontsize=12)
    ax.set_title('Pitch Movement Profile', fontsize=14, fontweight='bold')
    ax.legend()
    ax.grid(alpha=0.3)
    ax.set_aspect('equal')

    plt.tight_layout()
    return fig


def plot_exit_velo_distribution(
    df: pd.DataFrame,
    bins: int = 30,
    figsize: Tuple[int, int] = (12, 6)
) -> plt.Figure:
    """
    Plot exit velocity distribution with percentiles.

    Args:
        df: DataFrame with 'launch_speed' column
        bins: Number of histogram bins
        figsize: Figure size

    Returns:
        matplotlib Figure object
    """
    # Filter data
    exit_velos = df['launch_speed'].dropna()

    # Create figure
    fig, ax = plt.subplots(figsize=figsize)

    # Histogram
    ax.hist(exit_velos, bins=bins, alpha=0.7, edgecolor='black')

    # Add percentile lines
    percentiles = [10, 25, 50, 75, 90]
    colors = ['red', 'orange', 'green', 'blue', 'purple']

    for pct, color in zip(percentiles, colors):
        value = np.percentile(exit_velos, pct)
        ax.axvline(
            value,
            color=color,
            linestyle='--',
            linewidth=2,
            alpha=0.7,
            label=f'{pct}th percentile: {value:.1f} mph'
        )

    # Add reference lines
    ax.axvline(95, color='black', linestyle=':', linewidth=2, alpha=0.5, label='Hard Hit (95 mph)')

    ax.set_xlabel('Exit Velocity (mph)', fontsize=12)
    ax.set_ylabel('Frequency', fontsize=12)
    ax.set_title('Exit Velocity Distribution', fontsize=14, fontweight='bold')
    ax.legend()
    ax.grid(axis='y', alpha=0.3)

    plt.tight_layout()
    return fig


def plot_spray_chart(
    df: pd.DataFrame,
    figsize: Tuple[int, int] = (12, 10)
) -> plt.Figure:
    """
    Plot spray chart showing where batted balls landed.

    Args:
        df: DataFrame with 'hc_x' and 'hc_y' columns (hit coordinates)
        figsize: Figure size

    Returns:
        matplotlib Figure object
    """
    # Filter data
    plot_df = df.dropna(subset=['hc_x', 'hc_y']).copy()

    # Create figure
    fig, ax = plt.subplots(figsize=figsize)

    # Plot batted balls, colored by outcome if available
    if 'events' in plot_df.columns:
        event_colors = {
            'single': 'blue',
            'double': 'green',
            'triple': 'orange',
            'home_run': 'red',
            'field_out': 'gray',
            'force_out': 'gray',
            'grounded_into_double_play': 'darkgray'
        }

        for event, color in event_colors.items():
            mask = plot_df['events'] == event
            if mask.sum() > 0:
                ax.scatter(
                    plot_df[mask]['hc_x'],
                    -plot_df[mask]['hc_y'],  # Flip y for proper orientation
                    c=color,
                    alpha=0.6,
                    s=100,
                    label=event.replace('_', ' ').title(),
                    edgecolors='black',
                    linewidth=0.5
                )
        ax.legend(loc='upper left')
    else:
        ax.scatter(
            plot_df['hc_x'],
            -plot_df['hc_y'],
            alpha=0.6,
            s=100,
            c='blue',
            edgecolors='black',
            linewidth=0.5
        )

    # Draw basic field outline
    # This is a simplified version
    ax.plot([125, 125], [125, 200], 'g-', linewidth=2)  # Left field line
    ax.plot([125, 125], [-125, -200], 'g-', linewidth=2)  # Right field line

    ax.set_xlim(0, 250)
    ax.set_ylim(-250, 0)
    ax.set_xlabel('', fontsize=12)
    ax.set_ylabel('', fontsize=12)
    ax.set_title('Spray Chart', fontsize=14, fontweight='bold')
    ax.set_aspect('equal')
    ax.grid(alpha=0.3)

    plt.tight_layout()
    return fig


def plot_rolling_metric(
    df: pd.DataFrame,
    metric_col: str,
    window: int = 10,
    player_name: Optional[str] = None,
    figsize: Tuple[int, int] = (14, 6)
) -> plt.Figure:
    """
    Plot rolling average of a metric over time.

    Args:
        df: DataFrame sorted by date with metric column
        metric_col: Column name to plot
        window: Rolling window size
        player_name: Player name for title
        figsize: Figure size

    Returns:
        matplotlib Figure object
    """
    # Sort by date if game_date exists
    if 'game_date' in df.columns:
        plot_df = df.sort_values('game_date').copy()
    else:
        plot_df = df.copy()

    # Calculate rolling average
    rolling_avg = plot_df[metric_col].rolling(window=window, min_periods=1).mean()

    # Create figure
    fig, ax = plt.subplots(figsize=figsize)

    # Plot raw values
    ax.plot(range(len(plot_df)), plot_df[metric_col], alpha=0.3, label='Individual', marker='o')

    # Plot rolling average
    ax.plot(range(len(plot_df)), rolling_avg, linewidth=2, label=f'{window}-Game Rolling Avg', color='red')

    # Add mean line
    ax.axhline(
        plot_df[metric_col].mean(),
        color='green',
        linestyle='--',
        linewidth=2,
        alpha=0.7,
        label=f'Season Avg: {plot_df[metric_col].mean():.2f}'
    )

    title = f'Rolling {metric_col}'
    if player_name:
        title += f' - {player_name}'

    ax.set_xlabel('Game Number', fontsize=12)
    ax.set_ylabel(metric_col, fontsize=12)
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.legend()
    ax.grid(alpha=0.3)

    plt.tight_layout()
    return fig


def plot_comparison_radar(
    players_data: dict,
    metrics: List[str],
    figsize: Tuple[int, int] = (10, 10)
) -> plt.Figure:
    """
    Create a radar chart comparing multiple players across metrics.

    Args:
        players_data: Dictionary with player names as keys and metric dicts as values
        metrics: List of metric names to compare
        figsize: Figure size

    Returns:
        matplotlib Figure object
    """
    # Number of metrics
    num_vars = len(metrics)

    # Compute angle for each metric
    angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
    angles += angles[:1]  # Complete the circle

    # Create figure
    fig, ax = plt.subplots(figsize=figsize, subplot_kw=dict(projection='polar'))

    # Plot each player
    for player_name, player_metrics in players_data.items():
        values = [player_metrics.get(m, 0) for m in metrics]
        values += values[:1]  # Complete the circle

        ax.plot(angles, values, 'o-', linewidth=2, label=player_name)
        ax.fill(angles, values, alpha=0.15)

    # Fix axis to go in the right order
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)

    # Draw axis lines for each angle and label
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(metrics)

    ax.set_title('Player Comparison', fontsize=14, fontweight='bold', pad=20)
    ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))
    ax.grid(True)

    plt.tight_layout()
    return fig
