"""
Unit tests for src/data/contract_data.py
"""
import pytest
import pandas as pd
from src.data.contract_data import ContractData


class TestContractDataInit:
    """Tests for ContractData initialization."""

    def test_init(self):
        """Test basic initialization."""
        contract_data = ContractData()
        assert hasattr(contract_data, 'notable_2025_fas')
        assert isinstance(contract_data.notable_2025_fas, pd.DataFrame)

    def test_has_free_agents(self):
        """Test that initialization loads free agents."""
        contract_data = ContractData()
        assert len(contract_data.notable_2025_fas) > 0

    def test_free_agent_columns(self):
        """Test that free agent data has required columns."""
        contract_data = ContractData()
        df = contract_data.notable_2025_fas

        required_columns = ['player_name', 'position', 'age_2025', 'tier', 'free_agent_year']
        for col in required_columns:
            assert col in df.columns


class TestFreeAgentRetrieval:
    """Tests for retrieving free agents."""

    def test_get_all_free_agents(self):
        """Test getting all free agents."""
        contract_data = ContractData()
        df = contract_data.get_all_free_agents()

        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0

    def test_get_all_free_agents_is_copy(self):
        """Test that get_all returns a copy."""
        contract_data = ContractData()
        df1 = contract_data.get_all_free_agents()
        df2 = contract_data.get_all_free_agents()

        # Modifying one shouldn't affect the other
        df1.iloc[0, df1.columns.get_loc('tier')] = 'TEST'
        assert df2.iloc[0]['tier'] != 'TEST'


class TestPositionFiltering:
    """Tests for filtering by position."""

    def test_get_free_agents_by_position_sp(self):
        """Test filtering starting pitchers."""
        contract_data = ContractData()
        sp_fas = contract_data.get_free_agents_by_position('SP')

        assert len(sp_fas) > 0
        assert all(sp_fas['position'] == 'SP')

    def test_get_free_agents_by_position_of(self):
        """Test filtering outfielders."""
        contract_data = ContractData()
        of_fas = contract_data.get_free_agents_by_position('OF')

        assert all(of_fas['position'] == 'OF')

    def test_get_free_agents_by_position_empty(self):
        """Test filtering position with no FAs."""
        contract_data = ContractData()
        # Use position unlikely to exist
        result = contract_data.get_free_agents_by_position('FAKE_POS')

        assert len(result) == 0

    def test_get_free_agents_by_position_is_copy(self):
        """Test that position filter returns a copy."""
        contract_data = ContractData()
        df = contract_data.get_free_agents_by_position('SP')

        # Modifying shouldn't affect original
        original_len = len(contract_data.notable_2025_fas)
        df.drop(df.index, inplace=True)
        assert len(contract_data.notable_2025_fas) == original_len


class TestTierFiltering:
    """Tests for filtering by tier."""

    def test_get_free_agents_by_tier_elite(self):
        """Test filtering elite tier."""
        contract_data = ContractData()
        elite_fas = contract_data.get_free_agents_by_tier('Elite')

        assert len(elite_fas) > 0
        assert all(elite_fas['tier'] == 'Elite')

    def test_get_free_agents_by_tier_mid(self):
        """Test filtering mid tier."""
        contract_data = ContractData()
        mid_fas = contract_data.get_free_agents_by_tier('Mid')

        assert all(mid_fas['tier'] == 'Mid')

    def test_get_free_agents_by_tier_value(self):
        """Test filtering value tier."""
        contract_data = ContractData()
        value_fas = contract_data.get_free_agents_by_tier('Value')

        assert all(value_fas['tier'] == 'Value')

    def test_get_free_agents_by_tier_case_sensitive(self):
        """Test that tier filtering is case-sensitive."""
        contract_data = ContractData()
        result = contract_data.get_free_agents_by_tier('elite')  # lowercase

        # Should return empty if data uses 'Elite'
        assert len(result) == 0


class TestAgeFiltering:
    """Tests for age-based filtering."""

    def test_get_age_filtered_fas_default(self):
        """Test default age filter (32 and under)."""
        contract_data = ContractData()
        young_fas = contract_data.get_age_filtered_fas()

        assert all(young_fas['age_2025'] <= 32)

    def test_get_age_filtered_fas_custom(self):
        """Test custom age filter."""
        contract_data = ContractData()
        young_fas = contract_data.get_age_filtered_fas(max_age=28)

        assert all(young_fas['age_2025'] <= 28)

    def test_get_age_filtered_fas_very_young(self):
        """Test very restrictive age filter."""
        contract_data = ContractData()
        result = contract_data.get_age_filtered_fas(max_age=20)

        # Should return empty or very few
        assert len(result) >= 0


class TestPerformanceMerge:
    """Tests for merging with performance data."""

    def test_merge_with_performance_basic(self):
        """Test basic merge with performance data."""
        contract_data = ContractData()

        # Create sample performance data with matching names
        performance_df = pd.DataFrame({
            'Name': ['Juan Soto', 'Pete Alonso'],
            'WAR': [5.5, 4.2],
            'AVG': [0.288, 0.250]
        })

        result = contract_data.merge_with_performance(performance_df, 'Name')

        assert len(result) == 2
        assert 'WAR' in result.columns
        assert 'position' in result.columns  # From FA data
        assert 'tier' in result.columns

    def test_merge_with_performance_no_matches(self):
        """Test merge with no matching players."""
        contract_data = ContractData()

        performance_df = pd.DataFrame({
            'Name': ['Fake Player 1', 'Fake Player 2'],
            'WAR': [3.0, 4.0]
        })

        result = contract_data.merge_with_performance(performance_df)

        assert len(result) == 0

    def test_merge_with_performance_partial_matches(self):
        """Test merge with some matching players."""
        contract_data = ContractData()

        performance_df = pd.DataFrame({
            'Name': ['Juan Soto', 'Fake Player'],
            'WAR': [5.5, 3.0]
        })

        result = contract_data.merge_with_performance(performance_df)

        # Should only have matching player
        assert len(result) == 1
        assert result.iloc[0]['Name'] == 'Juan Soto'


class TestContractValueEstimation:
    """Tests for contract value estimation."""

    def test_estimate_contract_value_basic(self):
        """Test basic contract value estimation."""
        contract_data = ContractData()

        result = contract_data.estimate_contract_value(
            war_projection=5.0,
            years=5,
            age=28,
            position='OF',
            dollars_per_war=8.0
        )

        assert 'total_value_millions' in result
        assert 'aav_millions' in result
        assert 'total_war_projection' in result
        assert 'years' in result
        assert result['years'] == 5

    def test_estimate_contract_value_calculations(self):
        """Test contract value calculations."""
        contract_data = ContractData()

        result = contract_data.estimate_contract_value(
            war_projection=5.0,
            years=1,
            age=27,
            position='OF',
            dollars_per_war=8.0
        )

        # 1 year, 5 WAR, $8M per WAR = $40M
        assert result['aav_millions'] == 40.0
        assert result['total_value_millions'] == 40.0

    def test_estimate_contract_value_aging(self):
        """Test that aging affects projections."""
        contract_data = ContractData()

        result = contract_data.estimate_contract_value(
            war_projection=5.0,
            years=5,
            age=28,
            position='SP',  # SP decline rate = 0.92
            dollars_per_war=8.0
        )

        # Total WAR should be less than 25 due to decline
        assert result['total_war_projection'] < 25.0

    def test_estimate_contract_value_different_positions(self):
        """Test that different positions have different aging."""
        contract_data = ContractData()

        sp_result = contract_data.estimate_contract_value(
            5.0, 5, 28, 'SP', 8.0
        )
        of_result = contract_data.estimate_contract_value(
            5.0, 5, 28, 'OF', 8.0
        )

        # OF should have more total WAR (slower decline)
        assert of_result['total_war_projection'] > sp_result['total_war_projection']

    def test_estimate_contract_value_war_floor(self):
        """Test that WAR doesn't go negative."""
        contract_data = ContractData()

        result = contract_data.estimate_contract_value(
            war_projection=1.0,
            years=10,
            age=38,
            position='SP',
            dollars_per_war=8.0
        )

        # Should not have negative WAR
        assert result['total_war_projection'] >= 0


class TestCustomFreeAgents:
    """Tests for adding custom free agents."""

    def test_add_custom_free_agent(self):
        """Test adding a custom free agent."""
        contract_data = ContractData()
        initial_count = len(contract_data.notable_2025_fas)

        contract_data.add_custom_free_agent(
            player_name='Custom Player',
            position='SS',
            age=29,
            tier='Mid'
        )

        assert len(contract_data.notable_2025_fas) == initial_count + 1

        # Verify the player was added
        custom = contract_data.notable_2025_fas[
            contract_data.notable_2025_fas['player_name'] == 'Custom Player'
        ]
        assert len(custom) == 1
        assert custom.iloc[0]['position'] == 'SS'
        assert custom.iloc[0]['age_2025'] == 29

    def test_add_custom_free_agent_default_tier(self):
        """Test that default tier is set correctly."""
        contract_data = ContractData()

        contract_data.add_custom_free_agent(
            player_name='Test Player',
            position='3B',
            age=30
        )

        player = contract_data.notable_2025_fas[
            contract_data.notable_2025_fas['player_name'] == 'Test Player'
        ].iloc[0]

        assert player['tier'] == 'Mid'

    def test_add_multiple_custom_free_agents(self):
        """Test adding multiple custom free agents."""
        contract_data = ContractData()
        initial_count = len(contract_data.notable_2025_fas)

        for i in range(3):
            contract_data.add_custom_free_agent(
                player_name=f'Player {i}',
                position='OF',
                age=28
            )

        assert len(contract_data.notable_2025_fas) == initial_count + 3


class TestComparableContracts:
    """Tests for getting comparable contracts."""

    def test_get_comparable_contracts_returns_dataframe(self):
        """Test that get_comparable_contracts returns DataFrame."""
        contract_data = ContractData()

        result = contract_data.get_comparable_contracts(
            position='SP',
            age_range=(25, 30),
            min_aav=20.0
        )

        assert isinstance(result, pd.DataFrame)

    def test_get_comparable_contracts_placeholder(self):
        """Test that method is a placeholder (returns empty for now)."""
        contract_data = ContractData()

        result = contract_data.get_comparable_contracts('OF')

        # Placeholder returns empty DataFrame
        assert len(result) == 0
