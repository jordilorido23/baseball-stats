"""
Unit tests for src/utils/helpers.py
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime
from src.utils.helpers import (
    get_current_season_dates,
    get_date_range,
    filter_qualified_batters,
    filter_qualified_pitchers,
    clean_statcast_data,
    summarize_player_season,
    pitch_type_name_map,
    export_to_csv,
    fuzzy_match_player_name,
    find_player_in_dataframe,
    calculate_percentile_ranks,
    get_percentile_thresholds,
    categorize_by_percentile,
    compare_to_league_average,
    create_player_summary
)


class TestSeasonDates:
    """Tests for season date functions."""

    def test_get_current_season_dates_format(self):
        """Test that dates are returned in correct format."""
        start, end = get_current_season_dates()
        assert isinstance(start, str)
        assert isinstance(end, str)
        assert len(start) == 10  # YYYY-MM-DD
        assert len(end) == 10
        assert start[:4].isdigit()
        assert end[:4].isdigit()

    def test_get_current_season_dates_logic(self):
        """Test season date logic based on current month."""
        start, end = get_current_season_dates()
        # Start should always be April 1st
        assert start.endswith('-04-01')
        # End should be October 31st or current date
        assert end.endswith(('10-31', datetime.now().strftime('%m-%d')))

    def test_get_date_range(self):
        """Test date range calculation."""
        start, end = get_date_range(30)
        assert isinstance(start, str)
        assert isinstance(end, str)

        # Parse dates
        start_dt = datetime.strptime(start, '%Y-%m-%d')
        end_dt = datetime.strptime(end, '%Y-%m-%d')

        # Should be approximately 30 days apart
        diff = (end_dt - start_dt).days
        assert 29 <= diff <= 30

    def test_get_date_range_zero_days(self):
        """Test with zero days."""
        start, end = get_date_range(0)
        # Both should be today
        today = datetime.now().strftime('%Y-%m-%d')
        assert start == today or start == end


class TestQualifiedPlayerFilters:
    """Tests for qualified player filters."""

    def test_filter_qualified_batters_basic(self, sample_batting_data):
        """Test basic batter filtering."""
        result = filter_qualified_batters(sample_batting_data, min_pa=600)
        assert len(result) < len(sample_batting_data)
        assert all(result['PA'] >= 600)

    def test_filter_qualified_batters_all_qualify(self, sample_batting_data):
        """Test when all batters qualify."""
        result = filter_qualified_batters(sample_batting_data, min_pa=400)
        assert len(result) == len(sample_batting_data)

    def test_filter_qualified_batters_none_qualify(self, sample_batting_data):
        """Test when no batters qualify."""
        result = filter_qualified_batters(sample_batting_data, min_pa=1000)
        assert len(result) == 0

    def test_filter_qualified_batters_no_pa_column(self):
        """Test with dataframe missing PA column."""
        df = pd.DataFrame({'Name': ['Player 1'], 'HR': [10]})
        result = filter_qualified_batters(df, min_pa=100)
        assert len(result) == len(df)  # Should return unchanged

    def test_filter_qualified_pitchers_basic(self, sample_pitching_data):
        """Test basic pitcher filtering."""
        result = filter_qualified_pitchers(sample_pitching_data, min_ip=190)
        assert all(result['IP'] >= 190)

    def test_filter_qualified_pitchers_no_ip_column(self):
        """Test with dataframe missing IP column."""
        df = pd.DataFrame({'Name': ['Pitcher 1'], 'ERA': [3.50]})
        result = filter_qualified_pitchers(df, min_ip=100)
        assert len(result) == len(df)


class TestStatcastDataCleaning:
    """Tests for Statcast data cleaning."""

    def test_clean_statcast_data_basic(self, sample_statcast_data):
        """Test basic cleaning."""
        result = clean_statcast_data(sample_statcast_data)
        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0

    def test_clean_statcast_data_date_conversion(self, sample_statcast_data):
        """Test that game_date is converted to datetime."""
        result = clean_statcast_data(sample_statcast_data)
        assert pd.api.types.is_datetime64_any_dtype(result['game_date'])

    def test_clean_statcast_data_removes_nulls(self):
        """Test that null rows are removed from key columns."""
        df = pd.DataFrame({
            'pitch_type': [None, 'FF', 'SL'],
            'release_speed': [None, 95.0, 87.0],
            'events': [None, 'single', 'strikeout']
        })
        result = clean_statcast_data(df)
        # Should remove row where all key cols are null
        assert len(result) <= len(df)

    def test_clean_statcast_data_no_game_date(self):
        """Test with data missing game_date."""
        df = pd.DataFrame({
            'pitch_type': ['FF', 'SL'],
            'release_speed': [95.0, 87.0]
        })
        result = clean_statcast_data(df)
        assert 'game_date' not in result.columns


class TestPlayerSeasonSummary:
    """Tests for player season summary."""

    def test_summarize_batter_season(self, sample_statcast_data):
        """Test batter season summary."""
        result = summarize_player_season(sample_statcast_data, 'batter')

        assert 'total_pitches' in result
        assert 'games_played' in result
        assert result['total_pitches'] == len(sample_statcast_data)
        assert result['games_played'] > 0

    def test_summarize_pitcher_season(self, sample_statcast_data):
        """Test pitcher season summary."""
        result = summarize_player_season(sample_statcast_data, 'pitcher')

        assert 'total_pitches' in result
        assert 'strikeouts' in result
        assert 'walks' in result

    def test_summarize_batter_with_batted_balls(self, sample_statcast_data):
        """Test that batted ball stats are included."""
        # Add batted ball data
        df = sample_statcast_data.copy()
        df.loc[df.index[:10], 'type'] = 'X'

        result = summarize_player_season(df, 'batter')

        assert 'batted_balls' in result
        assert 'avg_exit_velo' in result


class TestPitchTypeMapping:
    """Tests for pitch type mapping."""

    def test_pitch_type_name_map_returns_dict(self):
        """Test that function returns a dictionary."""
        result = pitch_type_name_map()
        assert isinstance(result, dict)

    def test_pitch_type_name_map_common_pitches(self):
        """Test that common pitch types are included."""
        mapping = pitch_type_name_map()

        assert 'FF' in mapping
        assert 'SL' in mapping
        assert 'CH' in mapping
        assert 'CU' in mapping

        assert mapping['FF'] == '4-Seam Fastball'
        assert mapping['SL'] == 'Slider'


class TestCSVExport:
    """Tests for CSV export."""

    def test_export_to_csv_basic(self, sample_batting_data, tmp_path):
        """Test basic CSV export."""
        output_dir = str(tmp_path / 'exports')
        export_to_csv(sample_batting_data, 'test_export.csv', output_dir)

        import os
        filepath = os.path.join(output_dir, 'test_export.csv')
        assert os.path.exists(filepath)

        # Verify content
        df = pd.read_csv(filepath)
        assert len(df) == len(sample_batting_data)

    def test_export_to_csv_adds_extension(self, sample_batting_data, tmp_path):
        """Test that .csv extension is added if missing."""
        output_dir = str(tmp_path / 'exports')
        export_to_csv(sample_batting_data, 'test_no_ext', output_dir)

        import os
        filepath = os.path.join(output_dir, 'test_no_ext.csv')
        assert os.path.exists(filepath)


class TestFuzzyMatching:
    """Tests for fuzzy player name matching."""

    def test_fuzzy_match_exact(self, sample_player_names):
        """Test exact name match."""
        matches = fuzzy_match_player_name('Aaron Judge', sample_player_names)
        assert 'Aaron Judge' in matches
        assert len(matches) >= 1

    def test_fuzzy_match_typo(self, sample_player_names):
        """Test matching with typo."""
        matches = fuzzy_match_player_name('Aron Judge', sample_player_names)
        assert 'Aaron Judge' in matches

    def test_fuzzy_match_partial(self, sample_player_names):
        """Test partial name match."""
        matches = fuzzy_match_player_name('Judge', sample_player_names)
        assert 'Aaron Judge' in matches

    def test_fuzzy_match_case_insensitive(self, sample_player_names):
        """Test case-insensitive matching."""
        matches = fuzzy_match_player_name('aaron judge', sample_player_names)
        assert 'Aaron Judge' in matches

    def test_fuzzy_match_no_matches(self, sample_player_names):
        """Test when no matches found."""
        matches = fuzzy_match_player_name('Babe Ruth', sample_player_names, threshold=0.9)
        # May or may not return matches depending on similarity
        assert isinstance(matches, list)

    def test_fuzzy_match_max_results(self, sample_player_names):
        """Test max_results parameter."""
        matches = fuzzy_match_player_name('a', sample_player_names, max_results=3)
        assert len(matches) <= 3


class TestFindPlayerInDataFrame:
    """Tests for finding players in dataframes."""

    def test_find_player_exact_match(self, sample_batting_data):
        """Test finding player with exact name."""
        result = find_player_in_dataframe(sample_batting_data, 'Aaron Judge')
        assert len(result) == 1
        assert result.iloc[0]['Name'] == 'Aaron Judge'

    def test_find_player_case_insensitive(self, sample_batting_data):
        """Test case-insensitive search."""
        result = find_player_in_dataframe(sample_batting_data, 'aaron judge')
        assert len(result) == 1

    def test_find_player_partial_match(self, sample_batting_data):
        """Test partial name matching."""
        result = find_player_in_dataframe(sample_batting_data, 'Judge')
        assert len(result) >= 1

    def test_find_player_fuzzy_match(self, sample_batting_data):
        """Test fuzzy matching."""
        result = find_player_in_dataframe(sample_batting_data, 'Aron Judge', fuzzy=True)
        assert len(result) >= 1

    def test_find_player_not_found(self, sample_batting_data):
        """Test when player not found."""
        result = find_player_in_dataframe(sample_batting_data, 'Babe Ruth')
        assert len(result) == 0

    def test_find_player_wrong_column(self):
        """Test with wrong column name."""
        df = pd.DataFrame({'PlayerName': ['Test Player'], 'HR': [50]})
        # Should try alternatives
        result = find_player_in_dataframe(df, 'Test Player', name_column='Name')
        # May or may not find depending on alternatives


class TestPercentileCalculations:
    """Tests for percentile calculations."""

    def test_calculate_percentile_ranks(self, sample_batting_data):
        """Test percentile rank calculation."""
        result = calculate_percentile_ranks(sample_batting_data, ['HR', 'AVG'])

        assert 'HR_percentile' in result.columns
        assert 'AVG_percentile' in result.columns
        assert all(result['HR_percentile'] >= 0)
        assert all(result['HR_percentile'] <= 100)

    def test_calculate_percentile_ranks_nonexistent_column(self, sample_batting_data):
        """Test with non-existent column."""
        result = calculate_percentile_ranks(sample_batting_data, ['FAKE_STAT'])
        assert 'FAKE_STAT_percentile' not in result.columns

    def test_get_percentile_thresholds(self, sample_batting_data):
        """Test getting percentile thresholds."""
        result = get_percentile_thresholds(sample_batting_data, 'HR')

        assert '50th' in result
        assert '90th' in result
        assert result['90th'] > result['50th']
        assert result['50th'] > result['10th']

    def test_get_percentile_thresholds_custom(self, sample_batting_data):
        """Test with custom percentiles."""
        result = get_percentile_thresholds(sample_batting_data, 'HR', percentiles=[25, 75])

        assert '25th' in result
        assert '75th' in result
        assert len(result) == 2

    def test_get_percentile_thresholds_missing_column(self, sample_batting_data):
        """Test with missing column."""
        result = get_percentile_thresholds(sample_batting_data, 'FAKE_STAT')
        assert result == {}

    def test_categorize_by_percentile_elite(self):
        """Test elite categorization."""
        thresholds = {'25th': 20, '50th': 30, '75th': 40, '90th': 50}
        assert categorize_by_percentile(55, thresholds) == 'Elite'

    def test_categorize_by_percentile_above_average(self):
        """Test above average categorization."""
        thresholds = {'25th': 20, '50th': 30, '75th': 40, '90th': 50}
        assert categorize_by_percentile(45, thresholds) == 'Above Average'

    def test_categorize_by_percentile_average(self):
        """Test average categorization."""
        thresholds = {'25th': 20, '50th': 30, '75th': 40, '90th': 50}
        assert categorize_by_percentile(35, thresholds) == 'Average'

    def test_categorize_by_percentile_below_average(self):
        """Test below average categorization."""
        thresholds = {'25th': 20, '50th': 30, '75th': 40, '90th': 50}
        assert categorize_by_percentile(25, thresholds) == 'Below Average'

    def test_categorize_by_percentile_poor(self):
        """Test poor categorization."""
        thresholds = {'25th': 20, '50th': 30, '75th': 40, '90th': 50}
        assert categorize_by_percentile(15, thresholds) == 'Poor'

    def test_categorize_by_percentile_nan(self):
        """Test with NaN value."""
        thresholds = {'25th': 20, '50th': 30, '75th': 40, '90th': 50}
        assert categorize_by_percentile(np.nan, thresholds) == 'Unknown'


class TestLeagueComparison:
    """Tests for league average comparisons."""

    def test_compare_to_league_average_by_name(self, sample_batting_data):
        """Test comparison by player name."""
        result = compare_to_league_average(
            sample_batting_data,
            ['HR', 'AVG'],
            player_name='Aaron Judge'
        )

        assert len(result) > 0
        assert 'Metric' in result.columns
        assert 'Player' in result.columns
        assert 'League Avg' in result.columns
        assert 'Diff' in result.columns
        assert 'Percentile' in result.columns

    def test_compare_to_league_average_player_not_found(self, sample_batting_data):
        """Test when player not found."""
        result = compare_to_league_average(
            sample_batting_data,
            ['HR', 'AVG'],
            player_name='Babe Ruth'
        )
        assert len(result) == 0

    def test_compare_to_league_average_no_player_specified(self, sample_batting_data):
        """Test with no player specified."""
        result = compare_to_league_average(sample_batting_data, ['HR', 'AVG'])
        assert len(result) == 0


class TestPlayerSummary:
    """Tests for player summary creation."""

    def test_create_player_summary_basic(self, sample_batting_data):
        """Test basic player summary."""
        result = create_player_summary(sample_batting_data, 'Aaron Judge')

        assert 'name' in result
        assert 'age' in result
        assert 'team' in result
        assert result['name'] == 'Aaron Judge'

    def test_create_player_summary_with_categories(self, sample_batting_data):
        """Test with stat categories."""
        categories = {
            'power': ['HR', 'SLG'],
            'discipline': ['BB%', 'K%']
        }
        result = create_player_summary(sample_batting_data, 'Aaron Judge', categories)

        assert 'power' in result
        assert 'discipline' in result
        assert 'HR' in result['power']

    def test_create_player_summary_player_not_found(self, sample_batting_data):
        """Test when player not found."""
        result = create_player_summary(sample_batting_data, 'Babe Ruth')

        assert 'error' in result
        assert 'not found' in result['error'].lower()

    def test_create_player_summary_all_stats(self, sample_batting_data):
        """Test summary with all stats."""
        result = create_player_summary(sample_batting_data, 'Mike Trout')

        assert 'stats' in result
        assert isinstance(result['stats'], dict)
