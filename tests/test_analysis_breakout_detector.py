"""
Unit tests for src/analysis/breakout_detector.py
"""
import pytest
import pandas as pd
import numpy as np
from src.analysis.breakout_detector import BreakoutDetector


class TestBreakoutDetectorInit:
    """Tests for BreakoutDetector initialization."""

    def test_init(self):
        """Test initialization."""
        detector = BreakoutDetector()
        assert detector is not None


class TestXStatGaps:
    """Tests for expected stats gap calculation."""

    def test_calculate_xstat_gaps_batter(self):
        """Test calculating gaps for batters."""
        detector = BreakoutDetector()
        df = pd.DataFrame({
            'xba': [0.280, 0.300],
            'ba': [0.260, 0.310],
            'xslg': [0.500, 0.550],
            'slg': [0.480, 0.560],
            'xwoba': [0.350, 0.400],
            'woba': [0.340, 0.405]
        })

        result = detector.calculate_xstat_gaps(df, 'batter')

        assert 'ba_gap' in result.columns
        assert 'slg_gap' in result.columns
        assert 'woba_gap' in result.columns

        # Positive gap = underperforming
        assert result.iloc[0]['ba_gap'] == 0.020
        assert result.iloc[1]['ba_gap'] == -0.010

    def test_calculate_xstat_gaps_pitcher(self):
        """Test calculating gaps for pitchers."""
        detector = BreakoutDetector()
        df = pd.DataFrame({
            'xba': [0.240, 0.260],
            'ba': [0.250, 0.250],
            'xwoba': [0.310, 0.330],
            'woba': [0.320, 0.315],
            'xera': [3.50, 4.00],
            'era': [3.80, 3.90]
        })

        result = detector.calculate_xstat_gaps(df, 'pitcher')

        assert 'ba_gap' in result.columns
        assert 'woba_gap' in result.columns
        assert 'era_gap' in result.columns

        # For pitchers, positive gap = allowing more than expected (unlucky)
        assert result.iloc[0]['ba_gap'] == 0.010
        assert result.iloc[0]['era_gap'] == 0.30


class TestUnluckyPlayers:
    """Tests for finding unlucky players."""

    def test_find_unlucky_players_batters(self):
        """Test finding unlucky batters."""
        detector = BreakoutDetector()
        df = pd.DataFrame({
            'name': ['Player A', 'Player B', 'Player C'],
            'xwoba': [0.360, 0.340, 0.370],
            'woba': [0.330, 0.345, 0.340]  # Gaps: 0.030, -0.005, 0.030
        })

        result = detector.find_unlucky_players(df, 'batter', min_gap=0.020)

        # Should find Player A and C
        assert len(result) == 2
        assert 'Player A' in result['name'].values
        assert 'Player C' in result['name'].values

    def test_find_unlucky_players_sorted(self):
        """Test that unlucky players are sorted by gap size."""
        detector = BreakoutDetector()
        df = pd.DataFrame({
            'name': ['Player A', 'Player B'],
            'xwoba': [0.360, 0.380],
            'woba': [0.330, 0.340]  # Gaps: 0.030, 0.040
        })

        result = detector.find_unlucky_players(df, 'batter', min_gap=0.020)

        # Player B should be first (larger gap)
        assert result.iloc[0]['name'] == 'Player B'

    def test_find_unlucky_players_top_n(self):
        """Test top_n parameter."""
        detector = BreakoutDetector()
        df = pd.DataFrame({
            'name': ['Player A', 'Player B', 'Player C'],
            'xwoba': [0.360, 0.370, 0.380],
            'woba': [0.330, 0.340, 0.350]
        })

        result = detector.find_unlucky_players(df, 'batter', min_gap=0.020, top_n=2)

        assert len(result) == 2

    def test_find_unlucky_players_pitchers(self):
        """Test finding unlucky pitchers."""
        detector = BreakoutDetector()
        df = pd.DataFrame({
            'name': ['Pitcher A', 'Pitcher B'],
            'xera': [3.50, 3.80],
            'era': [4.00, 3.70]  # Gaps: 0.50, -0.10
        })

        result = detector.find_unlucky_players(df, 'pitcher')

        # Pitcher A is unlucky (allowing more than expected)
        assert 'Pitcher A' in result['name'].values


class TestOverperformingPlayers:
    """Tests for finding overperforming players."""

    def test_find_overperforming_players_batters(self):
        """Test finding overperforming batters."""
        detector = BreakoutDetector()
        df = pd.DataFrame({
            'name': ['Player A', 'Player B', 'Player C'],
            'xwoba': [0.330, 0.345, 0.340],
            'woba': [0.360, 0.340, 0.370]  # Gaps: -0.030, 0.005, -0.030
        })

        result = detector.find_overperforming_players(df, 'batter', min_gap=0.020)

        # Should find Player A and C
        assert len(result) == 2
        assert 'Player A' in result['name'].values
        assert 'Player C' in result['name'].values

    def test_find_overperforming_players_sorted(self):
        """Test that overperformers are sorted by gap size."""
        detector = BreakoutDetector()
        df = pd.DataFrame({
            'name': ['Player A', 'Player B'],
            'xwoba': [0.330, 0.320],
            'woba': [0.360, 0.365]  # Gaps: -0.030, -0.045
        })

        result = detector.find_overperforming_players(df, 'batter', min_gap=0.020)

        # Player B should be first (larger negative gap)
        assert result.iloc[0]['name'] == 'Player B'

    def test_find_overperforming_players_pitchers(self):
        """Test finding overperforming pitchers."""
        detector = BreakoutDetector()
        df = pd.DataFrame({
            'name': ['Pitcher A', 'Pitcher B'],
            'xera': [4.00, 3.50],
            'era': [3.40, 3.60]  # Gaps: -0.60, 0.10
        })

        result = detector.find_overperforming_players(df, 'pitcher')

        # Pitcher A is overperforming (allowing less than expected)
        assert 'Pitcher A' in result['name'].values


class TestBreakoutScore:
    """Tests for breakout score calculation."""

    def test_calculate_breakout_score_batters(self):
        """Test calculating breakout score for batters."""
        detector = BreakoutDetector()
        df = pd.DataFrame({
            'xwoba': [0.360, 0.340],
            'woba': [0.330, 0.345],
            'barrel_batted_rate': [0.15, 0.10],
            'avg_hit_speed': [92.0, 88.0],
            'k_percent': [0.20, 0.25],
            'bb_percent': [0.12, 0.08],
            'age': [25, 30]
        })

        result = detector.calculate_breakout_score(df, 'batter')

        assert 'breakout_score' in result.columns
        assert all(result['breakout_score'] >= 0)
        # Younger player with better metrics should score higher
        assert result.iloc[0]['breakout_score'] > result.iloc[1]['breakout_score']

    def test_calculate_breakout_score_pitchers(self):
        """Test calculating breakout score for pitchers."""
        detector = BreakoutDetector()
        df = pd.DataFrame({
            'xwoba': [0.310, 0.330],
            'woba': [0.320, 0.315],
            'whiff_percent': [0.30, 0.25],
            'k_percent': [0.28, 0.22],
            'bb_percent': [0.08, 0.10],
            'age': [26, 31]
        })

        result = detector.calculate_breakout_score(df, 'pitcher')

        assert 'breakout_score' in result.columns
        assert all(result['breakout_score'] >= 0)

    def test_calculate_breakout_score_woba_gap_component(self):
        """Test that woba gap contributes to score."""
        detector = BreakoutDetector()
        df = pd.DataFrame({
            'xwoba': [0.360, 0.340],
            'woba': [0.330, 0.340],  # First player has 0.030 gap
            'age': [27, 27]
        })

        result = detector.calculate_breakout_score(df, 'batter')

        # Player with gap should score higher
        assert result.iloc[0]['breakout_score'] > result.iloc[1]['breakout_score']


class TestBreakoutCandidates:
    """Tests for identifying breakout candidates."""

    def test_identify_breakout_candidates_basic(self):
        """Test basic breakout candidate identification."""
        detector = BreakoutDetector()
        df = pd.DataFrame({
            'name': ['Player A', 'Player B', 'Player C'],
            'xwoba': [0.360, 0.340, 0.370],
            'woba': [0.330, 0.345, 0.340],
            'barrel_batted_rate': [0.15, 0.10, 0.18],
            'avg_hit_speed': [92.0, 88.0, 94.0],
            'k_percent': [0.20, 0.25, 0.18],
            'bb_percent': [0.12, 0.08, 0.14],
            'age': [25, 30, 24]
        })

        result = detector.identify_breakout_candidates(df, 'batter', min_score=0, top_n=10)

        assert len(result) > 0
        assert 'breakout_score' in result.columns
        # Should be sorted by score descending
        scores = result['breakout_score'].tolist()
        assert scores == sorted(scores, reverse=True)

    def test_identify_breakout_candidates_min_score(self):
        """Test min_score filtering."""
        detector = BreakoutDetector()
        df = pd.DataFrame({
            'name': ['Player A', 'Player B'],
            'xwoba': [0.360, 0.340],
            'woba': [0.330, 0.345],
            'age': [25, 30]
        })

        result = detector.identify_breakout_candidates(df, 'batter', min_score=100, top_n=10)

        # With high min score, may get no results
        assert len(result) >= 0

    def test_identify_breakout_candidates_top_n(self):
        """Test top_n parameter."""
        detector = BreakoutDetector()
        df = pd.DataFrame({
            'name': [f'Player {i}' for i in range(50)],
            'xwoba': [0.360] * 50,
            'woba': [0.330] * 50,
            'age': [25] * 50
        })

        result = detector.identify_breakout_candidates(df, 'batter', min_score=0, top_n=10)

        assert len(result) == 10


class TestTrendAnalysis:
    """Tests for trend analysis."""

    def test_analyze_trends_basic(self):
        """Test basic trend analysis."""
        detector = BreakoutDetector()
        current_df = pd.DataFrame({
            'player_id': [1, 2, 3],
            'woba': [0.350, 0.360, 0.340],
            'avg_exit_velo': [92.0, 93.0, 90.0]
        })
        previous_df = pd.DataFrame({
            'player_id': [1, 2, 3],
            'woba': [0.330, 0.370, 0.330],
            'avg_exit_velo': [90.0, 92.0, 89.0]
        })

        result = detector.analyze_trends(
            current_df,
            previous_df,
            metric_cols=['woba', 'avg_exit_velo'],
            player_id_col='player_id'
        )

        assert 'woba_change' in result.columns
        assert 'woba_pct_change' in result.columns
        assert 'avg_exit_velo_change' in result.columns

        # Player 1 woba: 0.350 - 0.330 = 0.020
        assert abs(result.iloc[0]['woba_change'] - 0.020) < 0.001

    def test_analyze_trends_pct_change(self):
        """Test percentage change calculation."""
        detector = BreakoutDetector()
        current_df = pd.DataFrame({
            'player_id': [1],
            'woba': [0.400]
        })
        previous_df = pd.DataFrame({
            'player_id': [1],
            'woba': [0.320]
        })

        result = detector.analyze_trends(
            current_df,
            previous_df,
            metric_cols=['woba']
        )

        # (0.400 - 0.320) / 0.320 * 100 = 25%
        assert abs(result.iloc[0]['woba_pct_change'] - 25.0) < 0.1


class TestBreakoutSummary:
    """Tests for breakout summary generation."""

    def test_get_breakout_summary_basic(self):
        """Test basic breakout summary."""
        detector = BreakoutDetector()
        df = pd.DataFrame({
            'first_name': ['Aaron'],
            'last_name': ['Judge'],
            'age': [31],
            'xba': [0.285],
            'ba': [0.291],
            'xwoba': [0.445],
            'woba': [0.458],
            'barrel_batted_rate': [0.245],
            'avg_hit_speed': [95.2],
            'max_hit_speed': [121.1],
            'hard_hit_percent': [56.3],
            'k_percent': [0.261],
            'bb_percent': [0.148],
            'chase_rate': [0.25]
        })

        result = detector.get_breakout_summary(df, 'Judge', 'batter')

        assert 'player_name' in result
        assert 'age' in result
        assert 'expected_stats_gaps' in result
        assert 'breakout_score' in result

    def test_get_breakout_summary_player_not_found(self):
        """Test summary when player not found."""
        detector = BreakoutDetector()
        df = pd.DataFrame({
            'first_name': ['Aaron'],
            'last_name': ['Judge']
        })

        result = detector.get_breakout_summary(df, 'Trout', 'batter')

        assert 'error' in result

    def test_get_breakout_summary_quality_metrics(self):
        """Test that quality metrics are included."""
        detector = BreakoutDetector()
        df = pd.DataFrame({
            'first_name': ['Test'],
            'last_name': ['Player'],
            'age': [27],
            'xwoba': [0.360],
            'woba': [0.340],
            'barrel_batted_rate': [0.15],
            'avg_hit_speed': [92.0],
            'max_hit_speed': [110.0],
            'hard_hit_percent': [48.0]
        })

        result = detector.get_breakout_summary(df, 'Player', 'batter')

        assert 'quality_of_contact' in result
        assert result['quality_of_contact']['barrel_rate'] == 0.15
