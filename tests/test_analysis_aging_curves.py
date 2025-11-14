"""
Unit tests for src/analysis/aging_curves.py
"""
import pytest
import pandas as pd
import numpy as np
from src.analysis.aging_curves import AgingCurveAnalyzer


class TestAgingCurveInit:
    """Tests for AgingCurveAnalyzer initialization."""

    def test_init(self):
        """Test initialization."""
        analyzer = AgingCurveAnalyzer()
        assert hasattr(analyzer, 'default_aging_curves')
        assert 'SP' in analyzer.default_aging_curves
        assert 'OF' in analyzer.default_aging_curves

    def test_all_positions_have_curves(self):
        """Test that all positions have aging curves."""
        analyzer = AgingCurveAnalyzer()
        positions = ['C', '1B', '2B', '3B', 'SS', 'OF', 'DH', 'SP', 'RP']

        for pos in positions:
            assert pos in analyzer.default_aging_curves
            curve = analyzer.default_aging_curves[pos]
            assert 'peak_age' in curve
            assert 'decline_rate' in curve
            assert 'cliff_age' in curve


class TestPerformanceProjections:
    """Tests for performance projections."""

    def test_project_performance_basic(self):
        """Test basic performance projection."""
        analyzer = AgingCurveAnalyzer()
        projections = analyzer.project_performance(
            current_performance=5.0,
            current_age=28,
            position='OF',
            years_forward=5
        )

        assert len(projections) == 5
        assert all('year' in p for p in projections)
        assert all('age' in p for p in projections)
        assert all('projected_value' in p for p in projections)

    def test_project_performance_decline(self):
        """Test that performance declines with age."""
        analyzer = AgingCurveAnalyzer()
        projections = analyzer.project_performance(
            current_performance=5.0,
            current_age=30,
            position='OF',
            years_forward=5
        )

        # Performance should decline year over year (post-peak)
        values = [p['projected_value'] for p in projections]
        assert values[4] < values[0]

    def test_project_performance_pre_peak(self):
        """Test projection for player before peak age."""
        analyzer = AgingCurveAnalyzer()
        projections = analyzer.project_performance(
            current_performance=4.0,
            current_age=24,
            position='OF',
            years_forward=3
        )

        # Should improve or stay flat when approaching peak
        assert projections[0]['years_from_peak'] < 0

    def test_project_performance_war_floor(self):
        """Test that WAR doesn't go negative."""
        analyzer = AgingCurveAnalyzer()
        projections = analyzer.project_performance(
            current_performance=1.0,
            current_age=38,
            position='SP',
            years_forward=5,
            metric_type='WAR'
        )

        values = [p['projected_value'] for p in projections]
        assert all(v >= 0 for v in values)

    def test_project_performance_rate_stat_floor(self):
        """Test floor for rate stats like wRC+."""
        analyzer = AgingCurveAnalyzer()
        projections = analyzer.project_performance(
            current_performance=80,
            current_age=38,
            position='DH',
            years_forward=5,
            metric_type='wRC+'
        )

        values = [p['projected_value'] for p in projections]
        assert all(v >= 70 for v in values)

    def test_project_performance_cliff_age(self):
        """Test accelerated decline after cliff age."""
        analyzer = AgingCurveAnalyzer()

        # Project for player at cliff age
        pre_cliff = analyzer.project_performance(5.0, 32, 'SP', 1)
        post_cliff = analyzer.project_performance(5.0, 34, 'SP', 1)

        # Decline should be steeper post-cliff
        assert post_cliff[0]['decline_factor'] < pre_cliff[0]['decline_factor']


class TestContractWAR:
    """Tests for contract WAR calculations."""

    def test_calculate_contract_war_basic(self):
        """Test basic contract WAR calculation."""
        analyzer = AgingCurveAnalyzer()
        result = analyzer.calculate_contract_war(
            current_war=5.0,
            current_age=28,
            position='OF',
            contract_years=5
        )

        assert 'total_war' in result
        assert 'avg_war_per_year' in result
        assert 'peak_years' in result
        assert 'decline_years' in result
        assert 'years_to_cliff' in result
        assert 'cliff_during_contract' in result
        assert 'year_by_year' in result

    def test_calculate_contract_war_values(self):
        """Test contract WAR values make sense."""
        analyzer = AgingCurveAnalyzer()
        result = analyzer.calculate_contract_war(5.0, 28, 'OF', 5)

        assert result['total_war'] > 0
        assert result['avg_war_per_year'] > 0
        assert result['peak_years'] + result['decline_years'] == 5
        assert len(result['year_by_year']) == 5

    def test_calculate_contract_war_cliff_detection(self):
        """Test cliff detection during contract."""
        analyzer = AgingCurveAnalyzer()

        # Young player - no cliff
        young_result = analyzer.calculate_contract_war(5.0, 26, 'OF', 5)
        assert not young_result['cliff_during_contract']

        # Older player - cliff during contract
        old_result = analyzer.calculate_contract_war(5.0, 32, 'OF', 5)
        assert old_result['cliff_during_contract']


class TestSurplusValue:
    """Tests for surplus value calculations."""

    def test_estimate_surplus_value_basic(self):
        """Test basic surplus value calculation."""
        analyzer = AgingCurveAnalyzer()
        war_projections = [5.0, 4.5, 4.0, 3.5, 3.0]
        contract_aav = 25.0

        result = analyzer.estimate_surplus_value(
            war_projections,
            contract_aav,
            dollars_per_war=8.0
        )

        assert 'total_surplus_millions' in result
        assert 'total_market_value_millions' in result
        assert 'total_cost_millions' in result
        assert 'surplus_per_year' in result
        assert 'value_ratio' in result
        assert 'yearly_breakdown' in result

    def test_estimate_surplus_value_calculations(self):
        """Test surplus value calculations are correct."""
        analyzer = AgingCurveAnalyzer()
        war_projections = [5.0, 5.0, 5.0]
        contract_aav = 40.0  # $40M per year
        dollars_per_war = 8.0

        result = analyzer.estimate_surplus_value(
            war_projections,
            contract_aav,
            dollars_per_war=dollars_per_war,
            inflation_rate=0.0  # No inflation for simple test
        )

        # 5 WAR * $8M = $40M market value
        # $40M AAV = $40M cost
        # Surplus = $0M
        assert result['total_cost_millions'] == 120.0  # 3 years * $40M
        assert abs(result['total_surplus_millions']) < 5  # Should be close to 0

    def test_estimate_surplus_value_with_inflation(self):
        """Test surplus value with inflation."""
        analyzer = AgingCurveAnalyzer()
        war_projections = [5.0, 5.0, 5.0]
        contract_aav = 40.0

        with_inflation = analyzer.estimate_surplus_value(
            war_projections,
            contract_aav,
            dollars_per_war=8.0,
            inflation_rate=0.05
        )
        without_inflation = analyzer.estimate_surplus_value(
            war_projections,
            contract_aav,
            dollars_per_war=8.0,
            inflation_rate=0.0
        )

        # With inflation, market value should be higher
        assert with_inflation['total_market_value_millions'] > without_inflation['total_market_value_millions']

    def test_estimate_surplus_value_yearly_breakdown(self):
        """Test yearly breakdown."""
        analyzer = AgingCurveAnalyzer()
        war_projections = [5.0, 4.0, 3.0]
        contract_aav = 30.0

        result = analyzer.estimate_surplus_value(war_projections, contract_aav)

        assert len(result['yearly_breakdown']) == 3
        for year_data in result['yearly_breakdown']:
            assert 'year' in year_data
            assert 'war' in year_data
            assert 'market_value_millions' in year_data
            assert 'surplus_millions' in year_data


class TestContractScenarios:
    """Tests for contract scenario comparisons."""

    def test_compare_contract_scenarios_basic(self):
        """Test basic scenario comparison."""
        analyzer = AgingCurveAnalyzer()
        scenarios = [
            {'years': 3, 'aav': 25.0},
            {'years': 5, 'aav': 30.0},
            {'years': 7, 'aav': 35.0}
        ]

        result = analyzer.compare_contract_scenarios(
            current_war=5.0,
            current_age=28,
            position='OF',
            scenarios=scenarios
        )

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 3
        assert 'scenario' in result.columns
        assert 'total_surplus_millions' in result.columns

    def test_compare_contract_scenarios_columns(self):
        """Test that all expected columns are present."""
        analyzer = AgingCurveAnalyzer()
        scenarios = [{'years': 5, 'aav': 30.0}]

        result = analyzer.compare_contract_scenarios(5.0, 28, 'OF', scenarios)

        expected_columns = [
            'scenario', 'years', 'aav_millions', 'total_cost_millions',
            'total_war', 'avg_war_per_year', 'total_surplus_millions',
            'surplus_per_year', 'value_ratio', 'cliff_during_contract'
        ]

        for col in expected_columns:
            assert col in result.columns


class TestRiskyContracts:
    """Tests for risky contract identification."""

    def test_identify_risky_contracts_basic(self):
        """Test basic risky contract identification."""
        analyzer = AgingCurveAnalyzer()
        df = pd.DataFrame({
            'player_name': ['Player A', 'Player B', 'Player C'],
            'age_2025': [32, 27, 34],
            'position': ['SP', 'OF', 'SP']
        })

        result = analyzer.identify_risky_contracts(df)

        assert isinstance(result, pd.DataFrame)
        # Older players should be flagged
        assert len(result) > 0

    def test_identify_risky_contracts_cliff_detection(self):
        """Test that players near cliff are identified."""
        analyzer = AgingCurveAnalyzer()
        df = pd.DataFrame({
            'player_name': ['Old SP', 'Young OF'],
            'age_2025': [31, 25],
            'position': ['SP', 'OF']  # SP cliff at 33
        })

        result = analyzer.identify_risky_contracts(
            df,
            min_years=5,
            cliff_threshold=2
        )

        # Old SP should be flagged (31 + 5 years > 33 cliff)
        assert 'Old SP' in result['player_name'].values

    def test_identify_risky_contracts_risk_levels(self):
        """Test risk level assignment."""
        analyzer = AgingCurveAnalyzer()
        df = pd.DataFrame({
            'player_name': ['Very Old', 'Somewhat Old'],
            'age_2025': [32, 30],
            'position': ['SP', 'SP']  # Cliff at 33
        })

        result = analyzer.identify_risky_contracts(df)

        # Very old player should be high risk
        very_old = result[result['player_name'] == 'Very Old'].iloc[0]
        assert very_old['risk_level'] == 'High'

    def test_identify_risky_contracts_sorted(self):
        """Test that results are sorted by years to cliff."""
        analyzer = AgingCurveAnalyzer()
        df = pd.DataFrame({
            'player_name': ['Player A', 'Player B', 'Player C'],
            'age_2025': [32, 30, 31],
            'position': ['SP', 'SP', 'SP']
        })

        result = analyzer.identify_risky_contracts(df)

        # Should be sorted with closest to cliff first
        years_to_cliff = result['years_to_cliff'].tolist()
        assert years_to_cliff == sorted(years_to_cliff)
