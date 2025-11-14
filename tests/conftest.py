"""
Shared pytest fixtures for baseball-stats tests.
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


@pytest.fixture
def sample_statcast_data():
    """
    Create sample Statcast data for testing.
    """
    np.random.seed(42)
    n_pitches = 100

    data = {
        'game_date': [datetime(2024, 7, 1) + timedelta(days=i % 30) for i in range(n_pitches)],
        'player_name': ['Test Player'] * n_pitches,
        'pitch_type': np.random.choice(['FF', 'SL', 'CH', 'CU'], n_pitches),
        'release_speed': np.random.normal(92, 3, n_pitches),
        'release_spin_rate': np.random.normal(2200, 200, n_pitches),
        'launch_speed': np.random.normal(88, 8, n_pitches),
        'launch_angle': np.random.normal(15, 12, n_pitches),
        'zone': np.random.randint(1, 14, n_pitches),
        'description': np.random.choice([
            'swinging_strike', 'foul', 'hit_into_play', 'ball',
            'called_strike', 'swinging_strike_blocked'
        ], n_pitches),
        'events': np.random.choice([
            'single', 'double', 'home_run', 'walk', 'strikeout',
            'field_out', 'groundout', np.nan
        ], n_pitches),
        'type': np.random.choice(['X', 'S', 'B'], n_pitches)
    }

    return pd.DataFrame(data)


@pytest.fixture
def sample_batting_data():
    """
    Create sample batting statistics data.
    """
    data = {
        'Name': ['Aaron Judge', 'Mike Trout', 'Shohei Ohtani', 'Mookie Betts', 'Ronald Acuna Jr.'],
        'Team': ['NYY', 'LAA', 'LAD', 'LAD', 'ATL'],
        'Age': [31, 32, 29, 31, 26],
        'PA': [650, 520, 600, 620, 640],
        'AVG': [.291, .283, .304, .307, .337],
        'OBP': [.404, .369, .412, .408, .416],
        'SLG': [.686, .516, .654, .579, .596],
        'HR': [62, 26, 44, 39, 41],
        'wOBA': [.458, .376, .442, .419, .431],
        'xBA': [.285, .276, .298, .301, .330],
        'xSLG': [.650, .505, .632, .565, .585],
        'xwOBA': [.445, .368, .430, .410, .422],
        'Barrel%': [24.5, 16.2, 22.1, 18.9, 20.3],
        'HardHit%': [56.3, 48.2, 54.1, 51.7, 53.2],
        'EV': [95.2, 91.4, 94.8, 92.3, 93.1],
        'LA': [14.2, 12.8, 13.5, 11.9, 12.4],
        'K%': [26.1, 18.7, 23.4, 19.2, 21.8],
        'BB%': [14.8, 11.5, 13.9, 12.8, 11.3]
    }

    return pd.DataFrame(data)


@pytest.fixture
def sample_pitching_data():
    """
    Create sample pitching statistics data.
    """
    data = {
        'Name': ['Gerrit Cole', 'Spencer Strider', 'Blake Snell', 'Zack Wheeler', 'Corbin Burnes'],
        'Team': ['NYY', 'ATL', 'SDP', 'PHI', 'MIL'],
        'Age': [33, 25, 31, 34, 29],
        'IP': [209.0, 186.2, 180.0, 192.1, 193.2],
        'ERA': [2.63, 3.86, 2.25, 3.61, 3.39],
        'FIP': [3.12, 3.24, 2.98, 3.45, 3.42],
        'WHIP': [1.02, 1.20, 1.12, 1.08, 1.15],
        'K/9': [11.8, 13.9, 11.2, 10.4, 10.9],
        'BB/9': [2.1, 3.4, 2.8, 2.3, 2.5],
        'HR/9': [1.2, 1.5, 0.9, 1.1, 1.3]
    }

    return pd.DataFrame(data)


@pytest.fixture
def sample_free_agents():
    """
    Create sample free agent data.
    """
    data = {
        'name': ['Shohei Ohtani', 'Aaron Judge', 'Cody Bellinger', 'Matt Chapman'],
        'position': ['DH/SP', '1B/OF', 'OF', '3B'],
        'age': [29, 31, 28, 30],
        'previous_war': [8.2, 10.6, 4.1, 5.2],
        'contract_years': [10, 9, 3, 3],
        'tier': ['elite', 'elite', 'above-average', 'above-average']
    }

    return pd.DataFrame(data)


@pytest.fixture
def sample_player_names():
    """
    List of player names for testing fuzzy matching.
    """
    return [
        'Aaron Judge',
        'Mike Trout',
        'Shohei Ohtani',
        'Mookie Betts',
        'Ronald Acuna Jr.',
        'Freddie Freeman',
        'Juan Soto',
        'Vladimir Guerrero Jr.',
        'Jose Ramirez',
        'Kyle Tucker'
    ]


@pytest.fixture
def mock_statcast_response():
    """
    Mock response from pybaseball statcast query.
    """
    return pd.DataFrame({
        'pitch_type': ['FF', 'SL', 'CH'],
        'release_speed': [95.2, 87.3, 84.1],
        'events': ['single', 'strikeout', 'field_out'],
        'description': ['hit_into_play', 'swinging_strike', 'hit_into_play'],
        'zone': [5, 11, 3],
        'launch_speed': [98.5, np.nan, 85.2],
        'launch_angle': [18.0, np.nan, 35.0],
        'game_date': ['2024-07-01', '2024-07-01', '2024-07-02']
    })
