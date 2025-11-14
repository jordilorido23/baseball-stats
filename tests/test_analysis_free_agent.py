"""
Unit tests for src/analysis/free_agent_analyzer.py
"""
import pytest
import pandas as pd
import numpy as np
from src.analysis.free_agent_analyzer import FreeAgentAnalyzer


class TestFreeAgentAnalyzerInit:
    """Tests for FreeAgentAnalyzer initialization."""

    def test_init_default(self):
        """Test default initialization."""
        analyzer = FreeAgentAnalyzer()
        assert analyzer.dollars_per_war == 8.0
        assert 'SP' in analyzer.aging_curves
        assert 'OF' in analyzer.aging_curves

    def test_init_custom_dollars(self):
        """Test with custom $/WAR."""
        analyzer = FreeAgentAnalyzer(dollars_per_war=10.0)
        assert analyzer.dollars_per_war == 10.0

    def test_aging_curves_complete(self):
        """Test that all positions have aging curves."""
        analyzer = FreeAgentAnalyzer()
        positions = ['SP', 'RP', 'C', '1B', '2B', '3B', 'SS', 'OF', 'DH']
        for pos in positions:
            assert pos in analyzer.aging_curves
            assert 0 < analyzer.aging_curves[pos] < 1.0


class TestXStatGaps:
    """Tests for expected stats gap calculation."""

    def test_calculate_xstat_gaps_batting(self):
        """Test batting stats gaps."""
        analyzer = FreeAgentAnalyzer()
        df = pd.DataFrame({
            'xba': [0.280, 0.300],
            'ba': [0.260, 0.310],
            'xslg': [0.500, 0.550],
            'slg': [0.480, 0.560],
            'xwoba': [0.350, 0.400],
            'woba': [0.340, 0.405]
        })

        result = analyzer._calculate_xstat_gaps(df)

        assert 'ba_gap' in result.columns
        assert 'slg_gap' in result.columns
        assert 'woba_gap' in result.columns
        assert result.iloc[0]['ba_gap'] == 0.020
        assert result.iloc[1]['ba_gap'] == -0.010

    def test_calculate_xstat_gaps_pitching(self):
        """Test pitching stats gaps."""
        analyzer = FreeAgentAnalyzer()
        df = pd.DataFrame({
            'xera': [3.50, 4.00],
            'era': [3.80, 3.90],
            'xfip': [3.60, 3.70],
            'fip': [3.70, 3.65]
        })

        result = analyzer._calculate_xstat_gaps(df)

        assert 'era_gap' in result.columns
        assert 'fip_gap' in result.columns


class TestFAValueScore:
    """Tests for FA value score calculation."""

    def test_calculate_fa_value_score_with_war(self):
        """Test value score with WAR."""
        analyzer = FreeAgentAnalyzer()
        df = pd.DataFrame({
            'WAR': [5.0, 3.0, 7.0],
            'woba_gap': [0.020, -0.015, 0.030],
            'age_2025': [27, 33, 29],
            'barrel_batted_rate': [0.15, 0.08, 0.20]
        })

        result = analyzer._calculate_fa_value_score(df)

        assert 'fa_value_score' in result.columns
        assert all(result['fa_value_score'] >= 0)
        # Highest WAR + good age + unlucky should score highest
        assert result.iloc[2]['fa_value_score'] > result.iloc[1]['fa_value_score']

    def test_calculate_fa_value_score_age_bonus(self):
        """Test age component of value score."""
        analyzer = FreeAgentAnalyzer()
        df = pd.DataFrame({
            'WAR': [5.0, 5.0, 5.0],
            'age_2025': [27, 30, 35]
        })

        result = analyzer._calculate_fa_value_score(df)

        # Younger players should score higher
        assert result.iloc[0]['fa_value_score'] > result.iloc[1]['fa_value_score']
        assert result.iloc[1]['fa_value_score'] > result.iloc[2]['fa_value_score']


class TestContractTierClassification:
    """Tests for contract tier classification."""

    def test_classify_contract_tier_max(self):
        """Test max contract classification."""
        analyzer = FreeAgentAnalyzer()
        row = pd.Series({'fa_value_score': 85, 'age_2025': 27})
        tier = analyzer._classify_contract_tier(row)
        assert tier == 'Max Contract'

    def test_classify_contract_tier_premium(self):
        """Test premium tier."""
        analyzer = FreeAgentAnalyzer()
        row = pd.Series({'fa_value_score': 72, 'age_2025': 30})
        tier = analyzer._classify_contract_tier(row)
        assert tier == 'Premium'

    def test_classify_contract_tier_mid(self):
        """Test mid-tier."""
        analyzer = FreeAgentAnalyzer()
        row = pd.Series({'fa_value_score': 60, 'age_2025': 28})
        tier = analyzer._classify_contract_tier(row)
        assert tier == 'Mid-Tier'

    def test_classify_contract_tier_value(self):
        """Test value tier."""
        analyzer = FreeAgentAnalyzer()
        row = pd.Series({'fa_value_score': 45, 'age_2025': 31})
        tier = analyzer._classify_contract_tier(row)
        assert tier == 'Value'

    def test_classify_contract_tier_avoid(self):
        """Test avoid tier."""
        analyzer = FreeAgentAnalyzer()
        row = pd.Series({'fa_value_score': 30, 'age_2025': 35})
        tier = analyzer._classify_contract_tier(row)
        assert tier == 'Avoid'


class TestMultiYearProjections:
    """Tests for multi-year WAR projections."""

    def test_project_multi_year_war_basic(self):
        """Test basic WAR projection."""
        analyzer = FreeAgentAnalyzer()
        projections = analyzer.project_multi_year_war(
            current_war=5.0,
            age=28,
            position='OF',
            years=5
        )

        assert len(projections) == 5
        assert projections[0] == 5.0  # Year 1 should match current
        # Should decline each year
        assert projections[1] < projections[0]
        assert projections[4] < projections[1]

    def test_project_multi_year_war_floor(self):
        """Test that WAR doesn't go negative."""
        analyzer = FreeAgentAnalyzer()
        projections = analyzer.project_multi_year_war(
            current_war=1.0,
            age=36,
            position='SP',
            years=10
        )

        # All values should be >= 0
        assert all(war >= 0 for war in projections)

    def test_project_multi_year_war_different_positions(self):
        """Test projections for different positions."""
        analyzer = FreeAgentAnalyzer()

        # SP declines faster than OF
        sp_proj = analyzer.project_multi_year_war(5.0, 28, 'SP', 5)
        of_proj = analyzer.project_multi_year_war(5.0, 28, 'OF', 5)

        # SP should decline more
        assert sp_proj[-1] < of_proj[-1]


class TestContractValuation:
    """Tests for contract value estimation."""

    def test_estimate_contract_value_basic(self):
        """Test basic contract value estimation."""
        analyzer = FreeAgentAnalyzer()
        war_projections = [5.0, 4.5, 4.0, 3.5, 3.0]

        result = analyzer.estimate_contract_value(war_projections)

        assert 'total_value_millions' in result
        assert 'aav_millions' in result
        assert 'total_projected_war' in result
        assert 'years' in result
        assert result['years'] == 5
        assert result['total_projected_war'] == 20.0

    def test_estimate_contract_value_with_inflation(self):
        """Test value estimation with inflation."""
        analyzer = FreeAgentAnalyzer(dollars_per_war=8.0)
        war_projections = [5.0, 5.0, 5.0]

        with_inflation = analyzer.estimate_contract_value(
            war_projections,
            include_inflation=True,
            inflation_rate=0.05
        )
        without_inflation = analyzer.estimate_contract_value(
            war_projections,
            include_inflation=False
        )

        # With inflation should be worth more
        assert with_inflation['total_value_millions'] > without_inflation['total_value_millions']

    def test_estimate_contract_value_empty_projections(self):
        """Test with empty projections."""
        analyzer = FreeAgentAnalyzer()
        result = analyzer.estimate_contract_value([])

        assert result['aav_millions'] == 0
        assert result['total_value_millions'] == 0


class TestBuyLowCandidates:
    """Tests for buy-low candidate identification."""

    def test_identify_buy_low_candidates(self):
        """Test buy-low candidate identification."""
        analyzer = FreeAgentAnalyzer()
        df = pd.DataFrame({
            'player_name': ['Player A', 'Player B', 'Player C'],
            'woba_gap': [0.030, 0.015, 0.025],
            'age_2025': [28, 33, 29],
            'barrel_batted_rate': [0.15, 0.12, 0.18],
            'fa_value_score': [70, 55, 75]
        })

        candidates = analyzer.identify_buy_low_candidates(
            df,
            min_woba_gap=0.020,
            max_age=32
        )

        # Should include Player A and C (woba_gap >= 0.020 and age <= 32)
        assert len(candidates) == 2
        assert 'Player A' in candidates['player_name'].values
        assert 'Player C' in candidates['player_name'].values

    def test_identify_buy_low_candidates_sorted(self):
        """Test that candidates are sorted by value score."""
        analyzer = FreeAgentAnalyzer()
        df = pd.DataFrame({
            'player_name': ['Player A', 'Player B'],
            'woba_gap': [0.025, 0.030],
            'age_2025': [28, 27],
            'barrel_batted_rate': [0.15, 0.12],
            'fa_value_score': [65, 80]
        })

        candidates = analyzer.identify_buy_low_candidates(df, min_woba_gap=0.020)

        # Should be sorted by value score descending
        assert candidates.iloc[0]['player_name'] == 'Player B'


class TestRegressionRisks:
    """Tests for regression risk identification."""

    def test_identify_regression_risks(self):
        """Test regression risk identification."""
        analyzer = FreeAgentAnalyzer()
        df = pd.DataFrame({
            'player_name': ['Player A', 'Player B', 'Player C'],
            'woba_gap': [-0.030, 0.020, -0.025],
            'barrel_batted_rate': [0.07, 0.15, 0.08]
        })

        risks = analyzer.identify_regression_risks(
            df,
            min_woba_gap=-0.020,
            quality_threshold=0.08
        )

        # Should include Player A (negative gap + low barrel rate)
        assert len(risks) >= 1
        assert 'Player A' in risks['player_name'].values

    def test_identify_regression_risks_sorted(self):
        """Test that risks are sorted by gap size."""
        analyzer = FreeAgentAnalyzer()
        df = pd.DataFrame({
            'player_name': ['Player A', 'Player B'],
            'woba_gap': [-0.025, -0.035],
            'barrel_batted_rate': [0.07, 0.06]
        })

        risks = analyzer.identify_regression_risks(df, min_woba_gap=-0.020)

        # Most overperforming (largest negative gap) should be first
        assert risks.iloc[0]['player_name'] == 'Player B'


class TestFAReport:
    """Tests for FA report generation."""

    def test_generate_fa_report_basic(self):
        """Test basic FA report generation."""
        analyzer = FreeAgentAnalyzer()
        df = pd.DataFrame({
            'player_name': ['Aaron Judge'],
            'position': ['OF'],
            'age_2025': [32],
            'tier': ['elite'],
            'fa_value_score': [85.0],
            'ba': [0.291],
            'xba': [0.285],
            'ba_gap': [-0.006],
            'woba': [0.458],
            'xwoba': [0.445],
            'woba_gap': [-0.013],
            'barrel_batted_rate': [0.245],
            'avg_hit_speed': [95.2],
            'hard_hit_percent': [56.3],
            'contract_recommendation': ['Max Contract']
        })

        report = analyzer.generate_fa_report('Aaron Judge', df, current_war=10.6, contract_years=5)

        assert 'player_name' in report
        assert report['player_name'] == 'Aaron Judge'
        assert 'position' in report
        assert 'expected_stats' in report
        assert 'quality' in report
        assert 'contract_projection' in report

    def test_generate_fa_report_player_not_found(self):
        """Test report when player not found."""
        analyzer = FreeAgentAnalyzer()
        df = pd.DataFrame({'player_name': ['Aaron Judge']})

        report = analyzer.generate_fa_report('Mike Trout', df, current_war=8.0)

        assert 'error' in report
