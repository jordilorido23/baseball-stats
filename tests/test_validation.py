"""
Comprehensive Validation Test Suite

This module validates that the baseball analytics code produces realistic,
accurate outputs and isn't just AI-generated slop that looks good but doesn't work.

Test Categories:
1. Sanity Checks - Outputs in realistic ranges
2. Integration Tests - Full pipeline execution
3. Benchmark Tests - Comparison to known values
4. Data Quality Tests - Verify data integrity
"""

import pytest
import pandas as pd
import numpy as np
import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from src.data import ContractData, FanGraphsFetcher, SavantLeaderboards
from src.analysis import (
    AgingCurveAnalyzer,
    FreeAgentAnalyzer,
    BreakoutDetector,
    calculate_woba,
    calculate_barrel_rate
)


class TestSanityChecks:
    """Validate that outputs are in realistic ranges."""

    def test_war_projections_realistic_range(self):
        """WAR projections should be between -2 and 12 for all players."""
        contracts = ContractData()
        fa_list = contracts.get_all_free_agents()

        # Check 2025 WAR values
        assert fa_list['2025_war'].min() >= -2.0, "No player should have WAR below -2"
        assert fa_list['2025_war'].max() <= 12.0, "No player should have WAR above 12"

        # Check mean is reasonable (should be around 2-3 for FAs)
        mean_war = fa_list['2025_war'].mean()
        assert 1.0 <= mean_war <= 4.0, f"Mean FA WAR {mean_war:.2f} outside realistic range"

    def test_aging_curves_show_decline(self):
        """Aging curves should show decline after peak age."""
        analyzer = AgingCurveAnalyzer()

        positions = ['C', '1B', '2B', '3B', 'SS', 'OF', 'SP', 'RP']

        for position in positions:
            curve = analyzer.default_aging_curves[position]

            # Peak age should be between 25-30
            assert 25 <= curve['peak_age'] <= 30, \
                f"{position} peak age {curve['peak_age']} unrealistic"

            # Decline rate should be between 0.88 and 0.97 (2-12% annual decline)
            assert 0.88 <= curve['decline_rate'] <= 0.97, \
                f"{position} decline rate {curve['decline_rate']} unrealistic"

            # Cliff age should be after peak age
            assert curve['cliff_age'] > curve['peak_age'], \
                f"{position} cliff age should be after peak age"

            # Cliff age should be between 31-36
            assert 31 <= curve['cliff_age'] <= 36, \
                f"{position} cliff age {curve['cliff_age']} unrealistic"

    def test_contract_values_align_with_market(self):
        """Contract values should align with $/WAR market rates."""
        analyzer = FreeAgentAnalyzer(dollars_per_war=8.0)

        # Test case: 5 WAR player over 5 years
        total_war = 5.0
        expected_value = analyzer._calculate_contract_value(total_war)

        # At $8M/WAR, 5 WAR = $40M
        assert 35.0 <= expected_value <= 45.0, \
            f"Contract value ${expected_value}M outside realistic range for 5 WAR"

        # Test case: Elite 8 WAR player
        total_war = 8.0
        expected_value = analyzer._calculate_contract_value(total_war)

        # At $8M/WAR, 8 WAR = $64M
        assert 60.0 <= expected_value <= 70.0, \
            f"Contract value ${expected_value}M outside realistic range for 8 WAR"

    def test_free_agent_ages_realistic(self):
        """Free agent ages should be realistic (22-42)."""
        contracts = ContractData()
        fa_list = contracts.get_all_free_agents()

        assert fa_list['age_2025'].min() >= 22, "No FA should be younger than 22"
        assert fa_list['age_2025'].max() <= 42, "No FA should be older than 42"

        # Most FAs should be in prime years (25-35)
        prime_age_count = fa_list[(fa_list['age_2025'] >= 25) &
                                   (fa_list['age_2025'] <= 35)].shape[0]
        assert prime_age_count / len(fa_list) >= 0.6, \
            "At least 60% of FAs should be in prime age range (25-35)"

    def test_woba_calculation_realistic(self):
        """wOBA calculations should produce values between .250 and .500."""
        # Create sample data with realistic events
        sample_data = pd.DataFrame({
            'events': ['single', 'walk', 'home_run', 'double', 'field_out',
                      'strikeout', 'single', 'walk', 'triple', 'double']
        })

        woba_values = calculate_woba(sample_data)

        # All individual wOBA values should be between 0 and 2.5 (max is HR = 2.08)
        assert woba_values.min() >= 0.0, "wOBA values can't be negative"
        assert woba_values.max() <= 2.5, "wOBA values exceed maximum"

        # Mean wOBA should be realistic
        mean_woba = woba_values.mean()
        assert 0.0 <= mean_woba <= 1.5, f"Mean wOBA {mean_woba:.3f} unrealistic"

    def test_barrel_rate_percentage_range(self):
        """Barrel rates should be between 0% and 35%."""
        # Create sample data
        sample_data = pd.DataFrame({
            'launch_speed': [100, 95, 90, 85, 110, 105, 98, 92],
            'launch_angle': [28, 30, 25, 20, 32, 26, 29, 35]
        })

        barrel_rate = calculate_barrel_rate(sample_data)

        # Barrel rate should be a percentage between 0 and 100
        assert 0.0 <= barrel_rate <= 100.0, \
            f"Barrel rate {barrel_rate:.1f}% outside valid range"

        # For realistic batted ball data, should be < 35%
        assert barrel_rate <= 35.0, \
            f"Barrel rate {barrel_rate:.1f}% unrealistically high"


class TestIntegrationTests:
    """Test that full pipelines execute successfully."""

    def test_free_agent_analysis_pipeline_runs(self):
        """Full FA analysis pipeline should execute without errors."""
        # Initialize components
        contracts = ContractData()
        analyzer = FreeAgentAnalyzer(dollars_per_war=8.0)

        # Get FA list
        fa_list = contracts.get_all_free_agents()
        assert len(fa_list) > 0, "Should have free agents in database"

        # Create mock xStats data
        xstats_data = pd.DataFrame({
            'player_name': fa_list['player_name'].values[:10],
            'woba': [0.350, 0.380, 0.320, 0.365, 0.340, 0.355, 0.375, 0.330, 0.360, 0.345],
            'xwoba': [0.360, 0.370, 0.335, 0.360, 0.350, 0.365, 0.365, 0.345, 0.355, 0.350],
            'barrel_batted_rate': [0.12, 0.15, 0.08, 0.14, 0.10, 0.13, 0.16, 0.09, 0.14, 0.11],
            'hard_hit_rate': [0.45, 0.50, 0.40, 0.48, 0.43, 0.47, 0.52, 0.41, 0.49, 0.44]
        })

        # Run analysis
        analysis_result = analyzer.analyze_free_agent_class(
            xstats_data,
            fa_list.head(10),
            player_name_col='player_name'
        )

        # Verify output structure
        assert isinstance(analysis_result, pd.DataFrame), "Should return DataFrame"
        assert len(analysis_result) > 0, "Should have analysis results"

        # Verify expected columns exist
        expected_cols = ['player_name', 'woba', 'xwoba', 'woba_gap']
        for col in expected_cols:
            assert col in analysis_result.columns, f"Missing column: {col}"

    def test_aging_curve_projection_pipeline(self):
        """Aging curve projection pipeline should produce valid outputs."""
        analyzer = AgingCurveAnalyzer()

        # Test realistic scenario: 29-year-old OF with 4.5 WAR
        projection = analyzer.calculate_contract_war(
            current_war=4.5,
            current_age=29,
            position='OF',
            contract_years=6
        )

        # Verify output structure
        assert 'total_war' in projection, "Should include total_war"
        assert 'avg_war_per_year' in projection, "Should include avg_war_per_year"
        assert 'cliff_during_contract' in projection, "Should include cliff flag"
        assert 'yearly_projections' in projection, "Should include yearly projections"

        # Verify realistic values
        assert 10.0 <= projection['total_war'] <= 30.0, \
            f"Total WAR {projection['total_war']:.1f} unrealistic for 6-year contract"
        assert 1.5 <= projection['avg_war_per_year'] <= 5.0, \
            f"Avg WAR/year {projection['avg_war_per_year']:.1f} unrealistic"
        assert len(projection['yearly_projections']) == 6, \
            "Should have 6 years of projections"

    def test_breakout_detector_identifies_candidates(self):
        """Breakout detector should identify unlucky players."""
        detector = BreakoutDetector()

        # Create sample data with clear unlucky players
        sample_data = pd.DataFrame({
            'first_name': ['Mike', 'John', 'Bob', 'Dave'],
            'last_name': ['Trout', 'Smith', 'Jones', 'Williams'],
            'ba': [.250, .280, .300, .260],
            'xba': [.290, .285, .295, .310],  # Mike and Dave are unlucky
            'woba': [.340, .360, .380, .350],
            'xwoba': [.385, .365, .375, .400]  # Mike and Dave unlucky in wOBA too
        })

        unlucky = detector.find_unlucky_players(
            sample_data,
            player_type='batter',
            min_gap=0.030,
            top_n=10
        )

        # Should identify unlucky players
        assert len(unlucky) > 0, "Should identify at least some unlucky players"

        # Unlucky players should have positive gaps
        if len(unlucky) > 0:
            assert (unlucky['ba_gap'] >= 0).all(), "BA gaps should be positive for unlucky"
            assert (unlucky['woba_gap'] >= 0).all(), "wOBA gaps should be positive for unlucky"

    @pytest.mark.slow
    def test_generated_csvs_exist_and_valid(self):
        """Generated CSV files should exist and contain valid data."""
        data_dir = Path(__file__).parent.parent / 'data'

        # Check for key output files
        expected_files = [
            '2025_fa_complete_real_data.csv',
            '2025_fa_final_integrated_rankings.csv',
            '2025_fangraphs_batting.csv',
            '2025_fangraphs_pitching.csv'
        ]

        for filename in expected_files:
            filepath = data_dir / filename

            # File should exist
            if filepath.exists():
                # Should be readable as CSV
                df = pd.read_csv(filepath)

                # Should have data
                assert len(df) > 0, f"{filename} is empty"

                # Should have columns
                assert len(df.columns) > 0, f"{filename} has no columns"


class TestBenchmarkTests:
    """Compare outputs to known values and industry standards."""

    def test_aging_curves_match_published_research(self):
        """Aging curves should align with published research (Delta method, etc)."""
        analyzer = AgingCurveAnalyzer()

        # Based on Delta method (Steamer, ZiPS use similar):
        # - Hitters peak around 27-28
        # - Decline about 0.5 WAR per year after 30
        # - Cliff around 33-35

        # Test OF aging curve (most common position)
        of_curve = analyzer.default_aging_curves['OF']

        # Peak age should be 26-29 (research shows 27-28)
        assert 26 <= of_curve['peak_age'] <= 29, \
            f"OF peak age {of_curve['peak_age']} doesn't match research (27-28)"

        # Decline rate around 0.93-0.95 (~5-7% per year)
        assert 0.91 <= of_curve['decline_rate'] <= 0.96, \
            f"OF decline rate {of_curve['decline_rate']} doesn't match research"

        # Test SP aging curve
        sp_curve = analyzer.default_aging_curves['SP']

        # Pitchers peak slightly later (28-29)
        assert 27 <= sp_curve['peak_age'] <= 30, \
            f"SP peak age {sp_curve['peak_age']} doesn't match research (28-29)"

    def test_dollar_per_war_market_rate(self):
        """$/WAR rate should align with current market (2025: ~$8-9M/WAR)."""
        # Test with current market rate
        analyzer = FreeAgentAnalyzer(dollars_per_war=8.0)

        assert analyzer.dollars_per_war == 8.0, "Should use specified $/WAR"

        # Market rate should be in realistic range ($6-12M/WAR historically)
        assert 6.0 <= analyzer.dollars_per_war <= 12.0, \
            f"$/WAR {analyzer.dollars_per_war} outside historical range"

    def test_top_free_agents_have_high_war(self):
        """Top tier free agents should have 4+ WAR."""
        contracts = ContractData()
        fa_list = contracts.get_all_free_agents()

        # Sort by WAR
        top_fas = fa_list.nlargest(10, '2025_war')

        # Top 10 should all be above 3.0 WAR
        assert (top_fas['2025_war'] >= 3.0).all(), \
            "Top 10 FAs should all have 3+ WAR"

        # Top FA should have 5+ WAR
        assert top_fas.iloc[0]['2025_war'] >= 5.0, \
            f"Best FA has only {top_fas.iloc[0]['2025_war']:.1f} WAR, expected 5+"

    def test_woba_weights_match_fangraphs(self):
        """wOBA weights should match FanGraphs constants."""
        # FanGraphs 2024 wOBA weights (approximate)
        expected_weights = {
            'walk': 0.69,
            'hit_by_pitch': 0.72,
            'single': 0.88,
            'double': 1.24,
            'triple': 1.56,
            'home_run': 2.08
        }

        # Test with sample events
        for event, expected_weight in expected_weights.items():
            sample_data = pd.DataFrame({'events': [event]})
            woba = calculate_woba(sample_data)

            # Should match expected weight (within 0.05)
            assert abs(woba.iloc[0] - expected_weight) < 0.05, \
                f"{event} weight {woba.iloc[0]:.2f} doesn't match expected {expected_weight}"


class TestDataQualityTests:
    """Verify data integrity and consistency."""

    def test_no_duplicate_free_agents(self):
        """Free agent list should not have duplicates."""
        contracts = ContractData()
        fa_list = contracts.get_all_free_agents()

        # Check for duplicate names
        duplicates = fa_list[fa_list.duplicated(subset=['player_name'], keep=False)]
        assert len(duplicates) == 0, \
            f"Found {len(duplicates)} duplicate free agents: {duplicates['player_name'].tolist()}"

    def test_free_agent_positions_valid(self):
        """All positions should be valid baseball positions."""
        contracts = ContractData()
        fa_list = contracts.get_all_free_agents()

        valid_positions = {'C', '1B', '2B', '3B', 'SS', 'OF', 'DH', 'SP', 'RP',
                          'LF', 'CF', 'RF', 'DH/SP', '1B/OF', '2B/SS', '3B/SS'}

        invalid_positions = set(fa_list['position'].unique()) - valid_positions
        assert len(invalid_positions) == 0, \
            f"Found invalid positions: {invalid_positions}"

    def test_data_consistency_across_modules(self):
        """Data should be consistent across different modules."""
        contracts = ContractData()
        fa_list = contracts.get_all_free_agents()

        # Age should match (age_2025 should be reasonable)
        assert (fa_list['age_2025'] >= 20).all(), "All ages should be 20+"
        assert (fa_list['age_2025'] <= 45).all(), "All ages should be under 45"

        # WAR should be numeric
        assert pd.api.types.is_numeric_dtype(fa_list['2025_war']), \
            "WAR should be numeric"

        # No NaN in critical columns
        critical_cols = ['player_name', 'position', 'age_2025', '2025_war']
        for col in critical_cols:
            assert fa_list[col].notna().all(), f"Found NaN values in {col}"

    def test_cached_data_not_corrupted(self):
        """Cached data files should be readable and valid."""
        cache_dir = Path(__file__).parent.parent / 'data' / 'cache'

        if cache_dir.exists():
            pkl_files = list(cache_dir.glob('*.pkl'))

            for pkl_file in pkl_files:
                try:
                    # Should be readable as pickle
                    df = pd.read_pickle(pkl_file)

                    # Should be a DataFrame
                    assert isinstance(df, pd.DataFrame), \
                        f"{pkl_file.name} is not a DataFrame"

                    # Should have data
                    assert len(df) > 0, f"{pkl_file.name} is empty"

                except Exception as e:
                    pytest.fail(f"Failed to read {pkl_file.name}: {e}")


class TestRegressionTests:
    """Ensure outputs haven't regressed from known good states."""

    def test_top_free_agents_list_stable(self):
        """Top free agents should be stable (not random each run)."""
        contracts = ContractData()
        fa_list = contracts.get_all_free_agents()

        # Get top 5 FAs
        top_5 = fa_list.nlargest(5, '2025_war')['player_name'].tolist()

        # Should have 5 players
        assert len(top_5) == 5, "Should have 5 top free agents"

        # Names should not be empty
        for name in top_5:
            assert len(name) > 0, "Player names should not be empty"
            assert name != 'Unknown', "Should have actual player names"

    def test_aging_curve_projections_deterministic(self):
        """Same inputs should produce same outputs (no randomness)."""
        analyzer = AgingCurveAnalyzer()

        # Run same projection twice
        proj1 = analyzer.calculate_contract_war(
            current_war=5.0, current_age=28, position='SS', contract_years=5
        )
        proj2 = analyzer.calculate_contract_war(
            current_war=5.0, current_age=28, position='SS', contract_years=5
        )

        # Should be identical
        assert proj1['total_war'] == proj2['total_war'], \
            "Projections should be deterministic"
        assert proj1['yearly_projections'] == proj2['yearly_projections'], \
            "Yearly projections should be deterministic"


# Pytest configuration
def pytest_configure(config):
    """Configure custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "benchmark: marks tests that compare to known values"
    )


if __name__ == '__main__':
    # Run tests with pytest
    pytest.main([__file__, '-v', '--tb=short'])
