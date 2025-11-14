"""
Tests for Injury Risk Analyzer.

Tests injury risk scoring for pitchers and batters using biomechanical signals.
"""

import pytest
import pandas as pd
import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from src.analysis.injury_risk_analyzer import InjuryRiskAnalyzer


class TestInjuryRiskAnalyzer:
    """Test injury risk analysis functionality."""

    @pytest.fixture
    def analyzer(self):
        """Create InjuryRiskAnalyzer instance."""
        return InjuryRiskAnalyzer()

    @pytest.fixture
    def sample_pitcher_data(self):
        """Sample pitcher data with injury risk signals."""
        return pd.DataFrame({
            'Name': ['Gerrit Cole', 'Shane Bieber', 'Kevin Gausman', 'Max Scherzer'],
            'Age': [33, 29, 33, 40],
            'fastball_velo_trend_mph': [-0.5, -2.5, -1.0, -3.5],  # Bieber & Scherzer high risk
            'cumulative_ip_3yr': [620, 580, 650, 520],  # Gausman high workload
            'k_rate_decline_pct': [-2.0, -6.0, -1.5, -8.0],  # Bieber & Scherzer declining
            'pitch_count_stress': [3200, 2900, 3400, 2600]
        })

    @pytest.fixture
    def sample_batter_data(self):
        """Sample batter data with injury risk signals."""
        return pd.DataFrame({
            'Name': ['Mike Trout', 'Ronald Acuna', 'Mookie Betts', 'Pete Alonso'],
            'Age': [33, 27, 32, 30],
            'exit_velo_trend_mph': [-1.2, 0.5, -1.8, -0.3],  # Trout & Betts declining
            'sprint_speed_decline_fps': [-0.6, -0.2, -0.7, -0.1],  # Trout & Betts high risk
            'injury_prone_history': [True, True, False, False]
        })

    # Initialization Tests
    def test_analyzer_initialization(self, analyzer):
        """Test that analyzer initializes with correct thresholds."""
        assert analyzer.risk_thresholds['pitcher_velo_decline_mph'] == -2.0
        assert analyzer.risk_thresholds['batter_exit_velo_decline_mph'] == -1.5
        assert analyzer.risk_thresholds['pitcher_workload_ip'] == 650

    # Pitcher Injury Risk Tests
    def test_pitcher_injury_risk_calculation(self, analyzer, sample_pitcher_data):
        """Test pitcher injury risk scoring."""
        result = analyzer.calculate_pitcher_injury_risk(sample_pitcher_data)

        # Should have injury risk columns
        assert 'injury_risk_score' in result.columns
        assert 'injury_risk_factors' in result.columns

        # All risk scores should be numeric and non-negative
        assert (result['injury_risk_score'] >= 0).all()
        assert pd.api.types.is_numeric_dtype(result['injury_risk_score'])

    def test_pitcher_high_risk_detection(self, analyzer, sample_pitcher_data):
        """Test that high-risk pitchers are correctly identified."""
        result = analyzer.calculate_pitcher_injury_risk(sample_pitcher_data)

        # Shane Bieber should have high risk (velo decline -2.5 mph, K% decline -6%)
        bieber = result[result['Name'] == 'Shane Bieber'].iloc[0]
        assert bieber['injury_risk_score'] > 30, "Bieber should have elevated risk"

        # Max Scherzer should have highest risk (age 40, velo decline -3.5 mph, K% decline -8%)
        scherzer = result[result['Name'] == 'Max Scherzer'].iloc[0]
        assert scherzer['injury_risk_score'] > bieber['injury_risk_score'], \
            "Scherzer should have higher risk than Bieber"

    def test_pitcher_workload_risk(self, analyzer, sample_pitcher_data):
        """Test workload-based injury risk."""
        result = analyzer.calculate_pitcher_injury_risk(sample_pitcher_data)

        # Kevin Gausman has 650 IP (at threshold)
        gausman = result[result['Name'] == 'Kevin Gausman'].iloc[0]
        assert gausman['injury_risk_score'] > 0, "High workload should increase risk"

    def test_pitcher_low_risk(self, analyzer):
        """Test that healthy pitchers have low risk scores."""
        healthy_pitcher = pd.DataFrame({
            'Name': ['Healthy Pitcher'],
            'Age': [27],
            'fastball_velo_trend_mph': [0.5],  # Velo increasing
            'cumulative_ip_3yr': [500],  # Reasonable workload
            'k_rate_decline_pct': [2.0],  # K% improving
            'pitch_count_stress': [2500]
        })

        result = analyzer.calculate_pitcher_injury_risk(healthy_pitcher)
        assert result.iloc[0]['injury_risk_score'] < 20, "Healthy pitcher should have low risk"

    # Batter Injury Risk Tests
    def test_batter_injury_risk_calculation(self, analyzer, sample_batter_data):
        """Test batter injury risk scoring."""
        result = analyzer.calculate_batter_injury_risk(sample_batter_data)

        # Should have injury risk columns
        assert 'injury_risk_score' in result.columns
        assert 'injury_risk_factors' in result.columns

        # All risk scores should be numeric and non-negative
        assert (result['injury_risk_score'] >= 0).all()

    def test_batter_exit_velo_decline_risk(self, analyzer, sample_batter_data):
        """Test exit velocity decline detection."""
        result = analyzer.calculate_batter_injury_risk(sample_batter_data)

        # Mike Trout has -1.2 mph exit velo decline (above -1.5 threshold)
        trout = result[result['Name'] == 'Mike Trout'].iloc[0]

        # Mookie Betts has -1.8 mph decline (below threshold)
        betts = result[result['Name'] == 'Mookie Betts'].iloc[0]
        assert betts['injury_risk_score'] >= trout['injury_risk_score'], \
            "Betts should have higher or equal risk (more decline)"

    def test_batter_sprint_speed_decline_risk(self, analyzer, sample_batter_data):
        """Test sprint speed decline detection (soft tissue risk)."""
        result = analyzer.calculate_batter_injury_risk(sample_batter_data)

        # Mike Trout has -0.6 fps sprint speed decline (high risk)
        trout = result[result['Name'] == 'Mike Trout'].iloc[0]
        assert 'Sprint' in trout['injury_risk_factors'] or trout['injury_risk_score'] > 20

    def test_batter_low_risk(self, analyzer):
        """Test that healthy batters have low risk scores."""
        healthy_batter = pd.DataFrame({
            'Name': ['Healthy Batter'],
            'Age': [26],
            'exit_velo_trend_mph': [0.8],  # Exit velo increasing
            'sprint_speed_decline_fps': [0.1],  # Sprint speed stable
            'injury_prone_history': [False]
        })

        result = analyzer.calculate_batter_injury_risk(healthy_batter)
        assert result.iloc[0]['injury_risk_score'] < 15, "Healthy batter should have low risk"

    # Risk Factor Explanations
    def test_risk_factors_are_descriptive(self, analyzer, sample_pitcher_data):
        """Test that risk factors provide explanations."""
        result = analyzer.calculate_pitcher_injury_risk(sample_pitcher_data)

        # High-risk pitchers should have non-empty risk factor descriptions
        high_risk = result[result['injury_risk_score'] > 30]
        for _, pitcher in high_risk.iterrows():
            assert len(pitcher['injury_risk_factors']) > 0, \
                "High-risk pitchers should have risk factor explanations"

    # Edge Cases
    def test_missing_data_handling(self, analyzer):
        """Test that missing data is handled gracefully."""
        incomplete_data = pd.DataFrame({
            'Name': ['Missing Data Player'],
            'Age': [30],
            'fastball_velo_trend_mph': [np.nan],
            'cumulative_ip_3yr': [np.nan],
            'k_rate_decline_pct': [np.nan]
        })

        result = analyzer.calculate_pitcher_injury_risk(incomplete_data)

        # Should not crash and should have some default risk (age-based)
        assert pd.notna(result.iloc[0]['injury_risk_score'])
        assert result.iloc[0]['injury_risk_score'] >= 0

    def test_empty_dataframe(self, analyzer):
        """Test handling of empty DataFrame."""
        empty_df = pd.DataFrame()

        result = analyzer.calculate_pitcher_injury_risk(empty_df)
        assert len(result) == 0
        assert 'injury_risk_score' in result.columns

    # Risk Score Ranges
    def test_risk_score_realistic_range(self, analyzer, sample_pitcher_data, sample_batter_data):
        """Test that risk scores are in realistic range (0-100)."""
        pitcher_result = analyzer.calculate_pitcher_injury_risk(sample_pitcher_data)
        batter_result = analyzer.calculate_batter_injury_risk(sample_batter_data)

        # All scores should be between 0 and 100
        assert (pitcher_result['injury_risk_score'] >= 0).all()
        assert (pitcher_result['injury_risk_score'] <= 100).all()
        assert (batter_result['injury_risk_score'] >= 0).all()
        assert (batter_result['injury_risk_score'] <= 100).all()

    # Age-Based Risk
    def test_age_increases_risk(self, analyzer):
        """Test that older players have higher baseline risk."""
        young_pitcher = pd.DataFrame({
            'Name': ['Young'],
            'Age': [25],
            'fastball_velo_trend_mph': [0],
            'cumulative_ip_3yr': [500],
            'k_rate_decline_pct': [0]
        })

        old_pitcher = pd.DataFrame({
            'Name': ['Old'],
            'Age': [38],
            'fastball_velo_trend_mph': [0],
            'cumulative_ip_3yr': [500],
            'k_rate_decline_pct': [0]
        })

        young_result = analyzer.calculate_pitcher_injury_risk(young_pitcher)
        old_result = analyzer.calculate_pitcher_injury_risk(old_pitcher)

        assert old_result.iloc[0]['injury_risk_score'] > young_result.iloc[0]['injury_risk_score'], \
            "Older pitchers should have higher baseline risk"

    # Integration with Contract Valuation
    def test_injury_adjusted_valuation(self, analyzer, sample_pitcher_data):
        """Test injury-adjusted contract valuation."""
        # Add contract valuation columns
        data_with_contracts = sample_pitcher_data.copy()
        data_with_contracts['base_contract_value_millions'] = [180, 160, 140, 80]

        result = analyzer.calculate_pitcher_injury_risk(data_with_contracts)
        result = analyzer.apply_injury_risk_discount(result)

        # Should have adjusted contract values
        assert 'injury_adjusted_value_millions' in result.columns

        # High-risk players should have discounted contracts
        for _, player in result.iterrows():
            if player['injury_risk_score'] > 50:
                assert player['injury_adjusted_value_millions'] < player['base_contract_value_millions'], \
                    "High-risk players should have contract discount"

    # Multiple Risk Factors
    def test_multiple_risk_factors_compound(self, analyzer):
        """Test that multiple risk factors compound risk score."""
        single_risk = pd.DataFrame({
            'Name': ['Single Risk'],
            'Age': [28],
            'fastball_velo_trend_mph': [-2.5],  # Only velo decline
            'cumulative_ip_3yr': [500],
            'k_rate_decline_pct': [0]
        })

        multiple_risks = pd.DataFrame({
            'Name': ['Multiple Risks'],
            'Age': [28],
            'fastball_velo_trend_mph': [-2.5],  # Velo decline
            'cumulative_ip_3yr': [700],  # High workload
            'k_rate_decline_pct': [-6.0]  # K% decline
        })

        single_result = analyzer.calculate_pitcher_injury_risk(single_risk)
        multiple_result = analyzer.calculate_pitcher_injury_risk(multiple_risks)

        assert multiple_result.iloc[0]['injury_risk_score'] > single_result.iloc[0]['injury_risk_score'], \
            "Multiple risk factors should compound"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
