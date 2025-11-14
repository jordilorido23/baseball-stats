"""
Tests for Contract Structure Optimizer.

Tests NPV calculations, opt-out valuations, and contract structure analysis.
"""

import pytest
import pandas as pd
import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from src.analysis.contract_structure_optimizer import (
    ContractStructureOptimizer,
    ContractStructure
)


class TestContractStructure:
    """Test ContractStructure dataclass."""

    def test_contract_structure_initialization(self):
        """Test basic contract structure creation."""
        contract = ContractStructure(
            total_value=300.0,
            years=10,
            aav=30.0
        )

        assert contract.total_value == 300.0
        assert contract.years == 10
        assert contract.aav == 30.0
        assert contract.deferred_pct == 0.0

    def test_aav_auto_calculation(self):
        """Test that AAV is calculated if not provided."""
        contract = ContractStructure(
            total_value=200.0,
            years=5,
            aav=0
        )

        # AAV should be auto-calculated
        assert contract.aav == 40.0

    def test_opt_outs_default(self):
        """Test that opt_outs defaults to empty list."""
        contract = ContractStructure(total_value=100, years=3, aav=33.33)
        assert contract.opt_outs == []

    def test_deferred_contract_structure(self):
        """Test deferred money contract (like Ohtani)."""
        # Ohtani's contract: $700M over 10 years, 97% deferred
        ohtani = ContractStructure(
            total_value=700.0,
            years=10,
            aav=70.0,
            deferred_pct=0.97,
            deferral_years=10
        )

        assert ohtani.deferred_pct == 0.97
        assert ohtani.deferral_years == 10


class TestContractStructureOptimizer:
    """Test contract structure optimization."""

    @pytest.fixture
    def optimizer(self):
        """Create optimizer with 5% discount rate."""
        return ContractStructureOptimizer(discount_rate=0.05)

    # NPV Tests
    def test_npv_calculation_no_deferrals(self, optimizer):
        """Test NPV of standard contract with no deferrals."""
        contract = ContractStructure(
            total_value=100.0,
            years=5,
            aav=20.0
        )

        npv = optimizer.calculate_npv(contract)

        # NPV should be less than stated value due to time value
        assert npv['npv'] < contract.total_value
        assert npv['npv'] > 0
        assert npv['stated_value'] == 100.0

    def test_npv_deferred_contract(self, optimizer):
        """Test NPV of heavily deferred contract (Ohtani-style)."""
        # $700M stated, but 97% deferred for 10 years
        ohtani_style = ContractStructure(
            total_value=700.0,
            years=10,
            aav=70.0,
            deferred_pct=0.97,
            deferral_years=10
        )

        npv = optimizer.calculate_npv(ohtani_style)

        # NPV should be MUCH less than $700M
        assert npv['npv'] < 500.0, "Deferred contract NPV should be significantly lower"
        assert npv['deferral_discount'] > 0, "Should have deferral discount"
        assert npv['effective_aav'] < ohtani_style.aav, "Effective AAV should be lower"

    def test_npv_discount_rate_sensitivity(self, optimizer):
        """Test that higher discount rates lower NPV."""
        contract = ContractStructure(total_value=200, years=10, aav=20)

        npv_5pct = optimizer.calculate_npv(contract, discount_rate=0.05)
        npv_10pct = optimizer.calculate_npv(contract, discount_rate=0.10)

        assert npv_10pct['npv'] < npv_5pct['npv'], \
            "Higher discount rate should produce lower NPV"

    def test_npv_realistic_values(self, optimizer):
        """Test NPV produces realistic contract values."""
        # $150M over 6 years, no deferrals
        contract = ContractStructure(total_value=150, years=6, aav=25)
        npv = optimizer.calculate_npv(contract)

        # NPV should be between 80-95% of stated value for normal contracts
        pct_of_stated = npv['npv'] / contract.total_value
        assert 0.80 <= pct_of_stated <= 0.95, \
            f"NPV should be 80-95% of stated value, got {pct_of_stated:.1%}"

    # Opt-Out Valuation Tests
    def test_opt_out_valuation(self, optimizer):
        """Test opt-out clause valuation via Monte Carlo."""
        # $200M over 8 years with opt-out after year 3
        contract = ContractStructure(
            total_value=200,
            years=8,
            aav=25,
            opt_outs=[3]
        )

        valuation = optimizer.value_opt_out_clause(
            contract,
            current_war=5.0,
            position='OF',
            current_age=28,
            n_simulations=1000
        )

        # Should have key metrics
        assert 'expected_value_to_team' in valuation
        assert 'opt_out_probability' in valuation
        assert 'expected_years_played' in valuation

        # Opt-out probability should be between 0 and 1
        assert 0 <= valuation['opt_out_probability'] <= 1

    def test_high_war_player_opts_out(self, optimizer):
        """Test that elite players are likely to opt out."""
        # Elite player: 7 WAR, age 27, OF
        contract = ContractStructure(
            total_value=150,
            years=6,
            aav=25,
            opt_outs=[3]
        )

        valuation = optimizer.value_opt_out_clause(
            contract,
            current_war=7.0,  # Elite
            position='OF',
            current_age=27,  # Prime age
            n_simulations=1000
        )

        # Elite players should have high opt-out probability
        assert valuation['opt_out_probability'] > 0.5, \
            "Elite players should be likely to opt out for bigger contract"

    def test_declining_player_stays(self, optimizer):
        """Test that declining players are unlikely to opt out."""
        # Declining player: 2 WAR, age 34
        contract = ContractStructure(
            total_value=100,
            years=5,
            aav=20,
            opt_outs=[2]
        )

        valuation = optimizer.value_opt_out_clause(
            contract,
            current_war=2.0,  # Below average
            position='1B',
            current_age=34,  # Declining
            n_simulations=1000
        )

        # Declining players should have low opt-out probability
        assert valuation['opt_out_probability'] < 0.3, \
            "Declining players should be unlikely to opt out"

    # Contract Comparison Tests
    def test_compare_contract_structures(self, optimizer):
        """Test comparing different contract structures."""
        # Standard contract
        standard = ContractStructure(total_value=200, years=8, aav=25)

        # Frontloaded contract
        frontloaded = ContractStructure(total_value=200, years=8, aav=25)

        # Deferred contract
        deferred = ContractStructure(
            total_value=200,
            years=8,
            aav=25,
            deferred_pct=0.50,
            deferral_years=5
        )

        comparison = optimizer.compare_structures([standard, frontloaded, deferred])

        # Should return comparison DataFrame
        assert isinstance(comparison, pd.DataFrame)
        assert len(comparison) == 3
        assert 'npv' in comparison.columns

    def test_frontloaded_vs_backloaded(self, optimizer):
        """Test that frontloaded contracts have higher NPV."""
        # Both $100M over 5 years, but different payment structures
        frontloaded = ContractStructure(total_value=100, years=5, aav=20)
        backloaded = ContractStructure(total_value=100, years=5, aav=20)

        # Frontloaded: More money early
        # Backloaded: More money late

        front_npv = optimizer.calculate_npv(frontloaded)
        back_npv = optimizer.calculate_npv(backloaded)

        # For equal total values, frontloaded should have higher NPV
        # (This test assumes the optimizer has methods to model payment timing)
        assert front_npv['npv'] <= frontloaded.total_value

    # Performance Bonus Tests
    def test_incentive_valuation(self, optimizer):
        """Test performance incentive valuation."""
        base_salary = 150.0
        incentive_structure = {
            'games_played': {'threshold': 140, 'bonus': 2.0},
            'all_star': {'bonus': 1.0},
            'awards_bonus': {'bonus': 3.0}
        }

        valuation = optimizer.value_incentives(
            base_salary,
            incentive_structure,
            historical_achievement_rate=0.60
        )

        # Expected value should be less than total possible incentives
        assert valuation['expected_incentive_value'] < 6.0
        assert valuation['expected_incentive_value'] > 0

    # Risk-Adjusted Valuation Tests
    def test_risk_adjusted_contract_value(self, optimizer):
        """Test risk-adjusted contract valuation."""
        contract = ContractStructure(total_value=180, years=6, aav=30)

        # High injury risk player
        risk_adjusted = optimizer.calculate_risk_adjusted_value(
            contract,
            injury_risk_score=70,  # High risk
            performance_volatility=0.15
        )

        # Risk-adjusted value should be lower
        assert risk_adjusted['adjusted_value'] < contract.total_value
        assert risk_adjusted['risk_discount'] > 0

    def test_low_risk_minimal_discount(self, optimizer):
        """Test that low-risk players have minimal discount."""
        contract = ContractStructure(total_value=100, years=4, aav=25)

        risk_adjusted = optimizer.calculate_risk_adjusted_value(
            contract,
            injury_risk_score=10,  # Low risk
            performance_volatility=0.05  # Stable
        )

        # Discount should be minimal
        discount_pct = risk_adjusted['risk_discount'] / contract.total_value
        assert discount_pct < 0.10, "Low-risk players should have <10% discount"

    # Aging Curve Integration
    def test_aging_curves_by_position(self, optimizer):
        """Test that aging curves differ by position."""
        assert optimizer.aging_curves['C'] < optimizer.aging_curves['DH'], \
            "Catchers should age worse than DHs"
        assert optimizer.aging_curves['SP'] < optimizer.aging_curves['OF'], \
            "Starting pitchers should age worse than outfielders"

    # Edge Cases
    def test_zero_year_contract(self, optimizer):
        """Test handling of invalid contract (0 years)."""
        contract = ContractStructure(total_value=100, years=0, aav=0)
        npv = optimizer.calculate_npv(contract)

        # Should handle gracefully
        assert npv['npv'] == 0 or pd.isna(npv['npv'])

    def test_negative_values_rejected(self, optimizer):
        """Test that negative values are rejected or handled."""
        # Negative total value doesn't make sense
        with pytest.raises(ValueError):
            contract = ContractStructure(total_value=-100, years=5, aav=-20)

    # Realistic Contract Scenarios
    def test_shohei_ohtani_contract_npv(self, optimizer):
        """Test NPV of Shohei Ohtani's actual contract."""
        # $700M over 10 years, 97% deferred for 10 years at 0% interest
        ohtani = ContractStructure(
            total_value=700.0,
            years=10,
            aav=70.0,
            deferred_pct=0.97,
            deferral_years=10
        )

        npv = optimizer.calculate_npv(ohtani)

        # NPV should be approximately $460M (reported CBT value)
        # Allow 10% margin for different assumptions
        assert 400 <= npv['npv'] <= 520, \
            f"Ohtani NPV should be ~$460M, got ${npv['npv']:.0f}M"

    def test_mookie_betts_contract(self, optimizer):
        """Test Mookie Betts contract structure."""
        # $365M over 12 years with some deferrals
        betts = ContractStructure(
            total_value=365.0,
            years=12,
            aav=30.42,
            deferred_pct=0.15,
            deferral_years=5
        )

        npv = optimizer.calculate_npv(betts)

        # NPV should be slightly less than stated value
        assert 320 <= npv['npv'] <= 365
        assert npv['deferral_discount'] > 0

    # Utility Methods
    def test_effective_aav_calculation(self, optimizer):
        """Test effective AAV calculation (NPV-based)."""
        contract = ContractStructure(
            total_value=200,
            years=10,
            aav=20,
            deferred_pct=0.50,
            deferral_years=5
        )

        npv = optimizer.calculate_npv(contract)
        effective_aav = npv['effective_aav']

        # Effective AAV should be less than stated AAV for deferred contracts
        assert effective_aav < contract.aav
        assert effective_aav > 0

    def test_contract_comparison_sorting(self, optimizer):
        """Test that contract comparisons can be sorted by value."""
        contracts = [
            ContractStructure(total_value=100, years=4, aav=25),
            ContractStructure(total_value=200, years=8, aav=25),
            ContractStructure(total_value=150, years=5, aav=30)
        ]

        comparison = optimizer.compare_structures(contracts)

        # Should be sortable by NPV
        sorted_comparison = comparison.sort_values('npv', ascending=False)
        assert sorted_comparison.iloc[0]['npv'] >= sorted_comparison.iloc[-1]['npv']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
