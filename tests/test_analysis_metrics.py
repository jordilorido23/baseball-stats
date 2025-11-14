"""
Unit tests for src/analysis/metrics.py
"""
import pytest
import pandas as pd
import numpy as np
from src.analysis.metrics import (
    calculate_woba,
    calculate_barrel_rate,
    calculate_hard_hit_rate,
    calculate_whiff_rate,
    calculate_chase_rate,
    calculate_zone_contact_rate,
    calculate_expected_stats,
    get_pitch_arsenal_summary,
    calculate_plate_discipline_metrics,
    calculate_batted_ball_profile
)


class TestWOBA:
    """Tests for wOBA calculation."""

    def test_calculate_woba_basic(self):
        """Test basic wOBA calculation."""
        df = pd.DataFrame({
            'events': ['single', 'walk', 'home_run', 'strikeout', 'double']
        })
        result = calculate_woba(df)

        assert isinstance(result, pd.Series)
        assert len(result) == len(df)
        assert result.iloc[0] == 0.88  # single
        assert result.iloc[1] == 0.69  # walk
        assert result.iloc[2] == 2.08  # home run

    def test_calculate_woba_with_nulls(self):
        """Test wOBA with null events."""
        df = pd.DataFrame({
            'events': ['single', np.nan, 'home_run', 'strikeout']
        })
        result = calculate_woba(df)

        assert result.iloc[1] == 0.0  # null treated as 0

    def test_calculate_woba_all_outs(self):
        """Test wOBA with all outs."""
        df = pd.DataFrame({
            'events': ['strikeout', 'field_out', 'groundout', 'flyout']
        })
        result = calculate_woba(df)

        assert all(result == 0.0)


class TestBarrelRate:
    """Tests for barrel rate calculation."""

    def test_calculate_barrel_rate_basic(self):
        """Test basic barrel rate."""
        df = pd.DataFrame({
            'launch_speed': [100, 102, 95, 88, 101],
            'launch_angle': [28, 27, 29, 15, 26]
        })
        result = calculate_barrel_rate(df)

        assert isinstance(result, float)
        assert 0 <= result <= 100
        # First 4 balls meet criteria (EV >= 98, LA 26-30)
        assert result == 80.0

    def test_calculate_barrel_rate_no_barrels(self):
        """Test with no barrels."""
        df = pd.DataFrame({
            'launch_speed': [85, 88, 90, 87],
            'launch_angle': [10, 15, 20, 5]
        })
        result = calculate_barrel_rate(df)

        assert result == 0.0

    def test_calculate_barrel_rate_all_barrels(self):
        """Test with all barrels."""
        df = pd.DataFrame({
            'launch_speed': [100, 102, 105, 98],
            'launch_angle': [28, 27, 29, 26]
        })
        result = calculate_barrel_rate(df)

        assert result == 100.0

    def test_calculate_barrel_rate_empty_data(self):
        """Test with empty data."""
        df = pd.DataFrame({
            'launch_speed': [],
            'launch_angle': []
        })
        result = calculate_barrel_rate(df)

        assert result == 0.0

    def test_calculate_barrel_rate_with_nulls(self):
        """Test with null values."""
        df = pd.DataFrame({
            'launch_speed': [100, np.nan, 102],
            'launch_angle': [28, 27, 29]
        })
        result = calculate_barrel_rate(df)

        # Should drop nulls first
        assert result == 100.0  # 2 out of 2 valid balls


class TestHardHitRate:
    """Tests for hard hit rate calculation."""

    def test_calculate_hard_hit_rate_basic(self):
        """Test basic hard hit rate."""
        df = pd.DataFrame({
            'launch_speed': [98, 92, 102, 88, 95]
        })
        result = calculate_hard_hit_rate(df, threshold=95.0)

        assert isinstance(result, float)
        assert 0 <= result <= 100
        # 3 out of 5 are >= 95
        assert result == 60.0

    def test_calculate_hard_hit_rate_custom_threshold(self):
        """Test with custom threshold."""
        df = pd.DataFrame({
            'launch_speed': [98, 92, 102, 88, 95]
        })
        result = calculate_hard_hit_rate(df, threshold=100.0)

        # Only 1 out of 5 is >= 100
        assert result == 20.0

    def test_calculate_hard_hit_rate_empty_data(self):
        """Test with empty data."""
        df = pd.DataFrame({'launch_speed': []})
        result = calculate_hard_hit_rate(df)

        assert result == 0.0

    def test_calculate_hard_hit_rate_with_nulls(self):
        """Test with null values."""
        df = pd.DataFrame({
            'launch_speed': [98, np.nan, 102, np.nan, 95]
        })
        result = calculate_hard_hit_rate(df, threshold=95.0)

        # 3 out of 3 valid values
        assert result == 100.0


class TestWhiffRate:
    """Tests for whiff rate calculation."""

    def test_calculate_whiff_rate_basic(self):
        """Test basic whiff rate."""
        df = pd.DataFrame({
            'description': [
                'swinging_strike',
                'foul',
                'hit_into_play',
                'swinging_strike',
                'foul'
            ]
        })
        result = calculate_whiff_rate(df)

        assert isinstance(result, float)
        # 2 whiffs out of 5 swings = 40%
        assert result == 40.0

    def test_calculate_whiff_rate_no_swings(self):
        """Test with no swings."""
        df = pd.DataFrame({
            'description': ['ball', 'called_strike', 'ball']
        })
        result = calculate_whiff_rate(df)

        assert result == 0.0

    def test_calculate_whiff_rate_all_whiffs(self):
        """Test with all whiffs."""
        df = pd.DataFrame({
            'description': ['swinging_strike', 'swinging_strike_blocked', 'missed_bunt']
        })
        result = calculate_whiff_rate(df)

        assert result == 100.0

    def test_calculate_whiff_rate_no_whiffs(self):
        """Test with no whiffs."""
        df = pd.DataFrame({
            'description': ['foul', 'hit_into_play', 'foul_tip']
        })
        result = calculate_whiff_rate(df)

        assert result == 0.0


class TestChaseRate:
    """Tests for chase rate calculation."""

    def test_calculate_chase_rate_basic(self):
        """Test basic chase rate."""
        df = pd.DataFrame({
            'zone': [11, 12, 5, 13, 10],  # 11-13 are outside, 5 is inside
            'description': [
                'swinging_strike',  # chase
                'ball',              # no chase
                'swinging_strike',  # swing in zone
                'foul',              # chase
                'ball'               # no chase
            ]
        })
        result = calculate_chase_rate(df)

        # 2 chases out of 4 pitches outside = 50%
        assert result == 50.0

    def test_calculate_chase_rate_no_outside_pitches(self):
        """Test with no pitches outside zone."""
        df = pd.DataFrame({
            'zone': [1, 2, 3, 5],
            'description': ['swinging_strike', 'foul', 'ball', 'hit_into_play']
        })
        result = calculate_chase_rate(df)

        assert result == 0.0

    def test_calculate_chase_rate_never_chases(self):
        """Test when never chasing."""
        df = pd.DataFrame({
            'zone': [11, 12, 13, 14],
            'description': ['ball', 'ball', 'ball', 'ball']
        })
        result = calculate_chase_rate(df)

        assert result == 0.0

    def test_calculate_chase_rate_always_chases(self):
        """Test when always chasing."""
        df = pd.DataFrame({
            'zone': [11, 12, 13, 14],
            'description': ['swinging_strike', 'foul', 'swinging_strike', 'foul_tip']
        })
        result = calculate_chase_rate(df)

        assert result == 100.0


class TestZoneContactRate:
    """Tests for zone contact rate calculation."""

    def test_calculate_zone_contact_rate_basic(self):
        """Test basic zone contact rate."""
        df = pd.DataFrame({
            'zone': [1, 2, 3, 4, 5],
            'description': [
                'foul',              # contact
                'swinging_strike',   # no contact
                'hit_into_play',     # contact
                'foul_tip',          # contact
                'swinging_strike'    # no contact
            ]
        })
        result = calculate_zone_contact_rate(df)

        # 3 contacts out of 5 swings = 60%
        assert result == 60.0

    def test_calculate_zone_contact_rate_no_zone_swings(self):
        """Test with no swings in zone."""
        df = pd.DataFrame({
            'zone': [11, 12, 13],
            'description': ['swinging_strike', 'foul', 'ball']
        })
        result = calculate_zone_contact_rate(df)

        assert result == 0.0

    def test_calculate_zone_contact_rate_perfect_contact(self):
        """Test with perfect contact."""
        df = pd.DataFrame({
            'zone': [1, 2, 3, 4],
            'description': ['foul', 'hit_into_play', 'foul_tip', 'foul']
        })
        result = calculate_zone_contact_rate(df)

        assert result == 100.0


class TestExpectedStats:
    """Tests for expected stats calculation."""

    def test_calculate_expected_stats_basic(self):
        """Test basic expected stats."""
        df = pd.DataFrame({
            'launch_speed': [95, 92, 98, 88, 94],
            'launch_angle': [15, 20, 25, 30, 18]
        })
        result = calculate_expected_stats(df)

        assert isinstance(result, dict)
        assert 'xBA' in result
        assert 'xSLG' in result
        assert 'xwOBA' in result
        assert 0 <= result['xBA'] <= 1
        assert 0 <= result['xSLG'] <= 4
        assert 0 <= result['xwOBA'] <= 1

    def test_calculate_expected_stats_empty_data(self):
        """Test with empty data."""
        df = pd.DataFrame({
            'launch_speed': [],
            'launch_angle': []
        })
        result = calculate_expected_stats(df)

        assert result == {'xBA': 0.0, 'xSLG': 0.0, 'xwOBA': 0.0}

    def test_calculate_expected_stats_poor_contact(self):
        """Test with poor contact."""
        df = pd.DataFrame({
            'launch_speed': [70, 72, 75, 68],
            'launch_angle': [5, 60, -10, 70]
        })
        result = calculate_expected_stats(df)

        # Should have low expected stats
        assert result['xBA'] < 0.2
        assert result['xwOBA'] < 0.35

    def test_calculate_expected_stats_elite_contact(self):
        """Test with elite contact."""
        df = pd.DataFrame({
            'launch_speed': [105, 102, 108, 100],
            'launch_angle': [20, 25, 22, 28]
        })
        result = calculate_expected_stats(df)

        # Should have high expected stats
        assert result['xBA'] > 0.5
        assert result['xwOBA'] > 0.4


class TestPitchArsenal:
    """Tests for pitch arsenal summary."""

    def test_get_pitch_arsenal_summary_basic(self):
        """Test basic pitch arsenal."""
        df = pd.DataFrame({
            'pitch_type': ['FF', 'FF', 'SL', 'SL', 'CH'],
            'release_speed': [95.0, 94.5, 86.0, 87.0, 84.0],
            'release_spin_rate': [2200, 2250, 2500, 2450, 1800]
        })
        result = get_pitch_arsenal_summary(df)

        assert isinstance(result, pd.DataFrame)
        assert 'avg_velo' in result.columns
        assert 'avg_spin' in result.columns
        assert 'usage_pct' in result.columns
        assert len(result) == 3  # Three pitch types

    def test_get_pitch_arsenal_summary_usage_pct(self):
        """Test that usage percentages sum to 100."""
        df = pd.DataFrame({
            'pitch_type': ['FF'] * 5 + ['SL'] * 3 + ['CH'] * 2,
            'release_speed': [95.0] * 10,
            'release_spin_rate': [2200] * 10
        })
        result = get_pitch_arsenal_summary(df)

        assert abs(result['usage_pct'].sum() - 100.0) < 0.1

    def test_get_pitch_arsenal_summary_sorted(self):
        """Test that results are sorted by usage."""
        df = pd.DataFrame({
            'pitch_type': ['FF'] * 5 + ['SL'] * 2 + ['CH'] * 8,
            'release_speed': [95.0] * 15,
            'release_spin_rate': [2200] * 15
        })
        result = get_pitch_arsenal_summary(df)

        # CH should be first (most used)
        assert result.index[0] == 'CH'


class TestPlateDiscipline:
    """Tests for plate discipline metrics."""

    def test_calculate_plate_discipline_metrics_basic(self):
        """Test basic plate discipline metrics."""
        df = pd.DataFrame({
            'zone': [1, 2, 11, 3, 12],
            'description': [
                'swinging_strike',
                'foul',
                'swinging_strike',  # chase
                'hit_into_play',
                'ball'
            ]
        })
        result = calculate_plate_discipline_metrics(df)

        assert isinstance(result, dict)
        assert 'whiff_rate' in result
        assert 'chase_rate' in result
        assert 'zone_contact_rate' in result

    def test_calculate_plate_discipline_metrics_types(self):
        """Test that all metrics are floats."""
        df = pd.DataFrame({
            'zone': [1, 2, 3],
            'description': ['foul', 'swinging_strike', 'hit_into_play']
        })
        result = calculate_plate_discipline_metrics(df)

        assert isinstance(result['whiff_rate'], float)
        assert isinstance(result['chase_rate'], float)
        assert isinstance(result['zone_contact_rate'], float)


class TestBattedBallProfile:
    """Tests for batted ball profile."""

    def test_calculate_batted_ball_profile_basic(self):
        """Test basic batted ball profile."""
        df = pd.DataFrame({
            'launch_speed': [95, 98, 102, 88, 92],
            'launch_angle': [15, 20, 28, 10, 18]
        })
        result = calculate_batted_ball_profile(df)

        assert isinstance(result, dict)
        assert 'avg_exit_velo' in result
        assert 'max_exit_velo' in result
        assert 'avg_launch_angle' in result
        assert 'hard_hit_rate' in result
        assert 'barrel_rate' in result

    def test_calculate_batted_ball_profile_values(self):
        """Test batted ball profile values."""
        df = pd.DataFrame({
            'launch_speed': [90, 95, 100],
            'launch_angle': [20, 25, 30]
        })
        result = calculate_batted_ball_profile(df)

        assert result['avg_exit_velo'] == 95.0
        assert result['max_exit_velo'] == 100.0
        assert abs(result['avg_launch_angle'] - 25.0) < 0.1

    def test_calculate_batted_ball_profile_empty_data(self):
        """Test with empty data."""
        df = pd.DataFrame({
            'launch_speed': [],
            'launch_angle': []
        })
        result = calculate_batted_ball_profile(df)

        assert result['avg_exit_velo'] == 0.0
        assert result['max_exit_velo'] == 0.0
        assert result['avg_launch_angle'] == 0.0

    def test_calculate_batted_ball_profile_with_nulls(self):
        """Test with null values."""
        df = pd.DataFrame({
            'launch_speed': [95, np.nan, 100, 90],
            'launch_angle': [20, 25, np.nan, 15]
        })
        result = calculate_batted_ball_profile(df)

        # Should only include rows without nulls
        assert result['avg_exit_velo'] == 95.0
        assert result['max_exit_velo'] == 95.0
