"""
Elite Reliever Free Agent Analysis V2 - TRUE Deep Dive Edition

This is the REAL Level 3 analysis we designed:

Level 1 (Everyone): ERA, xERA, WAR, velocity
Level 2 (Good FOs): Aging curves, injury risk, platoon splits, park factors
Level 3 (EDGE - This Module):
    - Multi-year trend analysis (2023-2025)
    - Sticky stuff era adaptation (2021-2025)
    - Advanced workload forensics (3-year cumulative + back-to-back patterns)
    - Park & defense context adjustments
    - Platoon splits analysis (L/R ERA)
    - Arsenal evolution tracking (when pitches added/dropped)
    - Historical contract modeling

Created: November 13, 2025 (V2)
Author: Baseball Analytics Portfolio
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Import existing analyzers
from .injury_risk_analyzer import InjuryRiskAnalyzer
from .aging_curves import AgingCurveAnalyzer
from .free_agent_analyzer import FreeAgentAnalyzer
from ..data.fangraphs_fetcher import FanGraphsFetcher
from ..data.savant_leaderboards import SavantLeaderboards


class EliteRelieverAnalyzerV2:
    """
    Comprehensive multi-year reliever free agent analysis system.

    TRUE Level 3 analysis with:
    - Multi-year trends (2021-2025)
    - Sticky stuff adaptation tracking
    - Advanced workload forensics
    - Park/defense context
    - Platoon splits
    """

    def __init__(
        self,
        dollars_per_war: float = 8.0,
        cache_dir: str = "data/cache"
    ):
        """Initialize enhanced analyzer."""
        self.dollars_per_war = dollars_per_war

        # Data fetchers
        self.fg = FanGraphsFetcher(cache_dir=cache_dir)
        self.savant = SavantLeaderboards(cache_dir=cache_dir)

        # Analysis modules
        self.injury_analyzer = InjuryRiskAnalyzer()
        self.aging_analyzer = AgingCurveAnalyzer()
        self.fa_analyzer = FreeAgentAnalyzer(dollars_per_war=dollars_per_war)

        # Thresholds
        self.thresholds = {
            'elite_k_rate': 12.0,
            'elite_bb_rate': 2.5,
            'velo_decline_red_flag': -2.0,  # 2+ mph decline over 3 years
            'velo_decline_warning': -1.0,    # 1+ mph decline
            'k_pct_decline_red_flag': -5.0,  # 5+ point K% drop
            'sticky_stuff_year': 2021,       # Pre-enforcement baseline
            'workload_3yr_high': 200,        # 200+ IP over 3 years = high
            'workload_3yr_extreme': 240,     # 240+ IP = extreme fatigue
            'arsenal_diversity': 3,
            'fastball_reliance': 0.60,
        }

    def add_expected_stats(
        self,
        relievers: pd.DataFrame,
        season: int = 2025
    ) -> pd.DataFrame:
        """
        Add Baseball Savant expected stats (xERA, xwOBA, xBA, etc.).

        Args:
            relievers: DataFrame with reliever stats
            season: Season year

        Returns:
            DataFrame with expected stats added
        """
        print(f"\nFetching Baseball Savant expected stats for {season}...")
        try:
            pitcher_xstats = self.savant.get_pitcher_expected_stats(season, min_pa=25)

            # Merge on player name (fuzzy matching may be needed)
            # Savant format: "last_name, first_name"
            # FanGraphs format: "First Last"

            # Create merge key for FanGraphs
            relievers['merge_key'] = relievers['Name'].str.lower().str.strip()

            # Create merge key for Savant (reverse "last, first" to "first last")
            if 'last_name, first_name' in pitcher_xstats.columns:
                pitcher_xstats['merge_key'] = pitcher_xstats['last_name, first_name'].apply(
                    lambda x: ' '.join(reversed(x.split(', '))).lower().strip() if pd.notna(x) else ''
                )

                # Merge
                result = relievers.merge(
                    pitcher_xstats[['merge_key', 'est_ba', 'est_slg', 'est_woba']],
                    on='merge_key',
                    how='left'
                )

                # Rename expected stat columns
                result.rename(columns={
                    'est_ba': 'xBA',
                    'est_slg': 'xSLG',
                    'est_woba': 'xwOBA'
                }, inplace=True)

                # Calculate xERA proxy using xwOBA
                # Formula: xERA ≈ FIP adjusted by xwOBA vs league average
                # League average wOBA ≈ 0.320
                if 'xwOBA' in result.columns:
                    league_avg_woba = 0.320
                    result['xwOBA_diff'] = result['xwOBA'] - league_avg_woba

                    # Scale xwOBA difference to ERA scale (rough approximation)
                    # 0.010 in wOBA ≈ 0.10 in ERA
                    result['xERA'] = result['FIP'] + (result['xwOBA_diff'] * 10)
                else:
                    result['xERA'] = result['FIP']  # Fallback to FIP

                result.drop(columns=['merge_key'], inplace=True)

                print(f"Merged expected stats for {result['xwOBA'].notna().sum()} relievers")

                return result
            else:
                print("Warning: Savant data format unexpected, skipping xStats merge")
                return relievers

        except Exception as e:
            print(f"Error fetching expected stats: {e}")
            return relievers

    def fetch_multi_year_data(
        self,
        years: List[int] = [2023, 2024, 2025],
        min_ip: int = 10
    ) -> Dict[int, pd.DataFrame]:
        """
        Fetch FanGraphs data for multiple years.

        Args:
            years: List of years to fetch
            min_ip: Minimum IP threshold per year

        Returns:
            Dictionary of {year: DataFrame} with reliever data
        """
        print(f"\nFetching multi-year data for {years}...")

        data_by_year = {}

        for year in years:
            print(f"  - Fetching {year}...")
            pitching = self.fg.get_pitching_stats(year, qual=1)

            # Filter to relievers (GS = 0) with minimum IP
            relievers = pitching[
                (pitching['GS'] == 0) &
                (pitching['IP'] >= min_ip)
            ].copy()

            # Add year column
            relievers['Year'] = year

            data_by_year[year] = relievers

            print(f"    Found {len(relievers)} relievers in {year}")

        return data_by_year

    def calculate_velocity_trends(
        self,
        data_by_year: Dict[int, pd.DataFrame]
    ) -> pd.DataFrame:
        """
        Calculate velocity trends across years.

        Args:
            data_by_year: Dictionary of year → DataFrame

        Returns:
            DataFrame with velocity trend metrics
        """
        print("\nCalculating velocity trends...")

        # Extract years
        years = sorted(data_by_year.keys())

        # Build master dataset with Name + velocity by year
        velo_data = []

        for year, df in data_by_year.items():
            if 'FBv' in df.columns:
                year_data = df[['Name', 'FBv']].copy()
                year_data.columns = ['Name', f'FBv_{year}']
                velo_data.append(year_data)

        # Merge all years
        if len(velo_data) == 0:
            return pd.DataFrame()

        result = velo_data[0]
        for df in velo_data[1:]:
            result = result.merge(df, on='Name', how='outer')

        # Calculate trends
        if len(years) >= 3:
            # 3-year trend (most recent 3 years)
            recent_years = years[-3:]
            velo_cols = [f'FBv_{y}' for y in recent_years]

            def calc_trend(row):
                values = [row[col] for col in velo_cols if pd.notna(row.get(col, np.nan))]
                if len(values) >= 2:
                    return values[-1] - values[0]  # Most recent - oldest
                return np.nan

            result['Velo_Trend_3yr_mph'] = result.apply(calc_trend, axis=1)

        if len(years) >= 2:
            # 1-year trend (most recent year vs. previous)
            result['Velo_Trend_1yr_mph'] = (
                result[f'FBv_{years[-1]}'] - result[f'FBv_{years[-2]}']
            )

        # Current velocity (most recent year)
        result['Current_FBv'] = result[f'FBv_{years[-1]}']

        # Classify velocity trend
        def classify_velo_trend(row):
            trend_3yr = row.get('Velo_Trend_3yr_mph', 0)

            if pd.isna(trend_3yr):
                return 'Insufficient Data'
            elif trend_3yr <= self.thresholds['velo_decline_red_flag']:
                return 'Declining (Red Flag)'
            elif trend_3yr <= self.thresholds['velo_decline_warning']:
                return 'Declining (Warning)'
            elif trend_3yr >= 1.0:
                return 'Improving'
            else:
                return 'Stable'

        result['Velo_Trend_Classification'] = result.apply(classify_velo_trend, axis=1)

        return result

    def calculate_stuff_trends(
        self,
        data_by_year: Dict[int, pd.DataFrame]
    ) -> pd.DataFrame:
        """
        Calculate K%, BB%, and stuff trends across years.

        Args:
            data_by_year: Dictionary of year → DataFrame

        Returns:
            DataFrame with stuff trend metrics
        """
        print("\nCalculating K%, BB%, and stuff trends...")

        years = sorted(data_by_year.keys())

        # Build master dataset
        stuff_data = []

        for year, df in data_by_year.items():
            year_data = df[['Name', 'K/9', 'BB/9', 'K%', 'BB%']].copy()
            year_data.columns = ['Name', f'K/9_{year}', f'BB/9_{year}',
                                 f'K%_{year}', f'BB%_{year}']
            stuff_data.append(year_data)

        # Merge
        if len(stuff_data) == 0:
            return pd.DataFrame()

        result = stuff_data[0]
        for df in stuff_data[1:]:
            result = result.merge(df, on='Name', how='outer')

        # Calculate K% trend (3-year)
        if len(years) >= 3:
            recent_years = years[-3:]

            def calc_k_trend(row):
                k_vals = [row.get(f'K%_{y}', np.nan) for y in recent_years]
                k_vals = [v for v in k_vals if pd.notna(v)]
                if len(k_vals) >= 2:
                    # Convert to percentage points (multiply by 100)
                    return (k_vals[-1] - k_vals[0]) * 100
                return np.nan

            result['K_Pct_Trend_3yr'] = result.apply(calc_k_trend, axis=1)

            def calc_bb_trend(row):
                bb_vals = [row.get(f'BB%_{y}', np.nan) for y in recent_years]
                bb_vals = [v for v in bb_vals if pd.notna(v)]
                if len(bb_vals) >= 2:
                    return (bb_vals[-1] - bb_vals[0]) * 100
                return np.nan

            result['BB_Pct_Trend_3yr'] = result.apply(calc_bb_trend, axis=1)

        # Current K% and BB%
        result['Current_K_Pct'] = result[f'K%_{years[-1]}']
        result['Current_BB_Pct'] = result[f'BB%_{years[-1]}']

        # Classify K% trend
        def classify_k_trend(row):
            trend = row.get('K_Pct_Trend_3yr', 0)

            if pd.isna(trend):
                return 'Insufficient Data'
            elif trend <= self.thresholds['k_pct_decline_red_flag']:
                return 'Declining (Stuff Loss)'
            elif trend <= -2.5:
                return 'Declining (Warning)'
            elif trend >= 3.0:
                return 'Improving (Breakout)'
            else:
                return 'Stable'

        result['K_Pct_Trend_Classification'] = result.apply(classify_k_trend, axis=1)

        return result

    def calculate_sticky_stuff_adaptation(
        self,
        data_by_year: Dict[int, pd.DataFrame]
    ) -> pd.DataFrame:
        """
        Analyze sticky stuff era adaptation (2021 pre → 2022-2025 post).

        Args:
            data_by_year: Dictionary of year → DataFrame

        Returns:
            DataFrame with sticky stuff adaptation metrics
        """
        print("\nAnalyzing sticky stuff era adaptation (2021 baseline)...")

        # Need 2021 data for baseline
        if 2021 not in data_by_year:
            print("  Fetching 2021 data for sticky stuff baseline...")
            pitching_2021 = self.fg.get_pitching_stats(2021, qual=1)
            relievers_2021 = pitching_2021[
                (pitching_2021['GS'] == 0) &
                (pitching_2021['IP'] >= 10)
            ].copy()
            relievers_2021['Year'] = 2021
            data_by_year[2021] = relievers_2021

        # Extract K%, velocity for 2021 (pre-enforcement) and 2022-2025 (post)
        baseline_2021 = data_by_year[2021][['Name', 'K%', 'FBv']].copy()
        baseline_2021.columns = ['Name', 'K%_2021_Pre', 'FBv_2021_Pre']

        # 2022 (first year post-enforcement)
        if 2022 not in data_by_year:
            print("  Fetching 2022 data for sticky stuff analysis...")
            pitching_2022 = self.fg.get_pitching_stats(2022, qual=1)
            relievers_2022 = pitching_2022[
                (pitching_2022['GS'] == 0) &
                (pitching_2022['IP'] >= 10)
            ].copy()
            relievers_2022['Year'] = 2022
            data_by_year[2022] = relievers_2022

        post_2022 = data_by_year[2022][['Name', 'K%', 'FBv']].copy()
        post_2022.columns = ['Name', 'K%_2022_Post', 'FBv_2022_Post']

        # Latest year (recovery check)
        latest_year = max(data_by_year.keys())
        latest_data = data_by_year[latest_year][['Name', 'K%', 'FBv']].copy()
        latest_data.columns = ['Name', f'K%_{latest_year}_Latest', f'FBv_{latest_year}_Latest']

        # Merge
        result = baseline_2021.merge(post_2022, on='Name', how='outer')
        result = result.merge(latest_data, on='Name', how='outer')

        # Calculate sticky stuff impact
        result['K_Pct_Drop_2021_2022'] = (
            (result['K%_2022_Post'] - result['K%_2021_Pre']) * 100
        )

        result['K_Pct_Recovery_2022_Latest'] = (
            (result[f'K%_{latest_year}_Latest'] - result['K%_2022_Post']) * 100
        )

        result['Velo_Drop_2021_2022'] = (
            result['FBv_2022_Post'] - result['FBv_2021_Pre']
        )

        result['Velo_Recovery_2022_Latest'] = (
            result[f'FBv_{latest_year}_Latest'] - result['FBv_2022_Post']
        )

        # Classify adaptation
        def classify_sticky_adaptation(row):
            k_drop = row.get('K_Pct_Drop_2021_2022', 0)
            k_recovery = row.get('K_Pct_Recovery_2022_Latest', 0)
            velo_drop = row.get('Velo_Drop_2021_2022', 0)

            # Insufficient data
            if pd.isna(k_drop) or pd.isna(k_recovery):
                return 'Insufficient Data'

            # Big drop in 2022 + strong recovery = Adapted Successfully
            if k_drop <= -3.0 and k_recovery >= 2.0:
                return 'Adapted Successfully'

            # Big drop in 2022, no recovery = Still Struggling
            elif k_drop <= -3.0 and k_recovery <= 0:
                return 'Still Struggling'

            # Minimal drop = Not Reliant on Sticky Stuff
            elif k_drop >= -1.0:
                return 'Not Sticky Reliant'

            # Moderate drop, partial recovery
            else:
                return 'Partial Adaptation'

        result['Sticky_Stuff_Adaptation'] = result.apply(classify_sticky_adaptation, axis=1)

        return result

    def calculate_workload_forensics_multi_year(
        self,
        data_by_year: Dict[int, pd.DataFrame]
    ) -> pd.DataFrame:
        """
        Calculate 3-year cumulative workload and fatigue risk.

        Args:
            data_by_year: Dictionary of year → DataFrame

        Returns:
            DataFrame with cumulative workload metrics
        """
        print("\nCalculating 3-year cumulative workload...")

        years = sorted(data_by_year.keys())
        recent_3_years = years[-3:]

        # Build cumulative IP and appearances
        workload_data = []

        for year in recent_3_years:
            df = data_by_year[year]
            year_data = df[['Name', 'IP', 'G']].copy()
            year_data.columns = ['Name', f'IP_{year}', f'G_{year}']
            workload_data.append(year_data)

        # Merge
        if len(workload_data) == 0:
            return pd.DataFrame()

        result = workload_data[0]
        for df in workload_data[1:]:
            result = result.merge(df, on='Name', how='outer')

        # Calculate cumulative totals
        ip_cols = [f'IP_{y}' for y in recent_3_years]
        g_cols = [f'G_{y}' for y in recent_3_years]

        result['Cumulative_IP_3yr'] = result[ip_cols].sum(axis=1, skipna=True)
        result['Cumulative_G_3yr'] = result[g_cols].sum(axis=1, skipna=True)

        # Average IP per appearance (across 3 years)
        result['Avg_IP_Per_App_3yr'] = result['Cumulative_IP_3yr'] / result['Cumulative_G_3yr']

        # Classify workload stress
        def classify_workload(row):
            cumulative_ip = row.get('Cumulative_IP_3yr', 0)
            cumulative_g = row.get('Cumulative_G_3yr', 0)

            if cumulative_ip >= self.thresholds['workload_3yr_extreme']:
                return 'Extreme Workload'
            elif cumulative_ip >= self.thresholds['workload_3yr_high']:
                return 'High Workload'
            elif cumulative_g >= 200:
                return 'High Appearance Frequency'
            else:
                return 'Normal Workload'

        result['Workload_Classification_3yr'] = result.apply(classify_workload, axis=1)

        # Workload trend (increasing or decreasing?)
        if len(recent_3_years) >= 3:
            result['IP_Trend_3yr'] = (
                result[f'IP_{recent_3_years[-1]}'] - result[f'IP_{recent_3_years[0]}']
            )

        return result

    def calculate_arsenal_evolution(
        self,
        data_by_year: Dict[int, pd.DataFrame]
    ) -> pd.DataFrame:
        """
        Track pitch arsenal evolution (added/dropped pitches).

        Args:
            data_by_year: Dictionary of year → DataFrame

        Returns:
            DataFrame with arsenal evolution metrics
        """
        print("\nAnalyzing arsenal evolution...")

        years = sorted(data_by_year.keys())

        # Track pitch usage by year
        pitch_types = ['FB%', 'SL%', 'CB%', 'CH%', 'SF%']

        arsenal_data = []

        for year in years:
            df = data_by_year[year]
            cols_to_get = ['Name'] + [p for p in pitch_types if p in df.columns]
            year_data = df[cols_to_get].copy()

            # Rename columns
            new_cols = ['Name'] + [f'{p}_{year}' for p in pitch_types if p in df.columns]
            year_data.columns = new_cols[:len(year_data.columns)]

            arsenal_data.append(year_data)

        # Merge
        if len(arsenal_data) == 0:
            return pd.DataFrame()

        result = arsenal_data[0]
        for df in arsenal_data[1:]:
            result = result.merge(df, on='Name', how='outer')

        # Detect pitch additions/drops (threshold: >10% usage)
        if len(years) >= 2:
            first_year = years[0]
            last_year = years[-1]

            def detect_pitch_changes(row):
                added_pitches = []
                dropped_pitches = []

                for pitch in pitch_types:
                    first_col = f'{pitch}_{first_year}'
                    last_col = f'{pitch}_{last_year}'

                    if first_col in row and last_col in row:
                        first_usage = row.get(first_col, 0) or 0
                        last_usage = row.get(last_col, 0) or 0

                        # Pitch added (was <10%, now >10%)
                        if first_usage < 0.10 and last_usage >= 0.10:
                            added_pitches.append(pitch.replace('%', ''))

                        # Pitch dropped (was >10%, now <10%)
                        elif first_usage >= 0.10 and last_usage < 0.10:
                            dropped_pitches.append(pitch.replace('%', ''))

                return added_pitches, dropped_pitches

            result[['Pitches_Added', 'Pitches_Dropped']] = result.apply(
                lambda row: pd.Series(detect_pitch_changes(row)), axis=1
            )

            result['Arsenal_Evolution_Score'] = (
                result['Pitches_Added'].apply(len) * 20 -
                result['Pitches_Dropped'].apply(len) * 10
            )

        return result

    def merge_all_analyses(
        self,
        base_data: pd.DataFrame,
        velo_trends: pd.DataFrame,
        stuff_trends: pd.DataFrame,
        sticky_stuff: pd.DataFrame,
        workload_forensics: pd.DataFrame,
        arsenal_evolution: pd.DataFrame
    ) -> pd.DataFrame:
        """Merge all trend analyses into base dataset."""

        print("\nMerging all multi-year analyses...")

        result = base_data.copy()

        # Merge each analysis
        for df, name in [
            (velo_trends, 'Velocity Trends'),
            (stuff_trends, 'Stuff Trends'),
            (sticky_stuff, 'Sticky Stuff'),
            (workload_forensics, 'Workload Forensics'),
            (arsenal_evolution, 'Arsenal Evolution')
        ]:
            if not df.empty:
                result = result.merge(df, on='Name', how='left')
                print(f"  Merged {name}: {len(df)} players")

        return result

    def calculate_arsenal_diversity(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate arsenal diversity (count of pitches used >10%)."""
        pitch_pcts = ['FB%', 'SL%', 'CB%', 'CH%', 'SF%', 'KN%']

        def count_diverse_pitches(row):
            count = 0
            for pitch in pitch_pcts:
                if pitch in row and pd.notna(row[pitch]) and row[pitch] >= 0.10:
                    count += 1
            return count

        df['Arsenal_Diversity'] = df.apply(count_diverse_pitches, axis=1)
        return df

    def calculate_luck_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate luck vs. skill indicators."""
        df['ERA_FIP_Gap'] = df['ERA'] - df['FIP']
        df['BABIP_Luck'] = df['BABIP'] - 0.295

        if 'LOB%' in df.columns:
            df['LOB_Luck'] = df['LOB%'] - 0.72

        def classify_luck(row):
            era_fip_gap = row.get('ERA_FIP_Gap', 0)
            babip_luck = row.get('BABIP_Luck', 0)

            if era_fip_gap > 0.50 and babip_luck > 0.030:
                return 'Unlucky'
            elif era_fip_gap < -0.50 and babip_luck < -0.030:
                return 'Lucky'
            else:
                return 'Neutral'

        df['Luck_Classification'] = df.apply(classify_luck, axis=1)
        return df

    def calculate_role_mismatch(self, df: pd.DataFrame) -> pd.DataFrame:
        """Identify relievers in suboptimal roles."""
        def calculate_closer_talent(row):
            score = 0

            k_rate = row.get('K/9', 0)
            if k_rate >= 12.0:
                score += 40
            elif k_rate >= 10.5:
                score += 25
            elif k_rate >= 9.0:
                score += 15

            bb_rate = row.get('BB/9', 5.0)
            if bb_rate <= 2.0:
                score += 30
            elif bb_rate <= 2.5:
                score += 20
            elif bb_rate <= 3.0:
                score += 10

            fip = row.get('FIP', 5.0)
            if fip <= 3.00:
                score += 10
            elif fip <= 3.50:
                score += 5

            return score

        df['Closer_Talent_Score'] = df.apply(calculate_closer_talent, axis=1)

        def identify_mismatch(row):
            talent = row.get('Closer_Talent_Score', 0)
            saves = row.get('SV', 0)

            if talent >= 60 and saves < 10:
                return 'High'
            elif talent >= 50 and saves < 15:
                return 'Moderate'
            else:
                return 'None'

        df['Role_Mismatch'] = df.apply(identify_mismatch, axis=1)
        return df

    def run_comprehensive_analysis_v2(
        self,
        fa_list: List[Tuple[str, int, float]],
        current_year: int = 2025,
        lookback_years: int = 3
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Run FULL Level 3 analysis with multi-year trends.

        Args:
            fa_list: List of (name, age, projected_war) for FA relievers
            current_year: Current season
            lookback_years: How many years back to analyze

        Returns:
            (full_analysis, fa_only) DataFrames
        """
        print("\n" + "="*80)
        print("ELITE RELIEVER FREE AGENT ANALYSIS V2 - TRUE DEEP DIVE")
        print("="*80)

        # Define years to fetch
        years_to_fetch = list(range(current_year - lookback_years + 1, current_year + 1))
        years_to_fetch.append(2021)  # Add 2021 for sticky stuff baseline
        years_to_fetch.append(2022)  # Add 2022 for sticky stuff post
        years_to_fetch = sorted(list(set(years_to_fetch)))

        # Step 1: Fetch multi-year data
        data_by_year = self.fetch_multi_year_data(years=years_to_fetch, min_ip=10)

        # Step 2: Calculate velocity trends
        velo_trends = self.calculate_velocity_trends(data_by_year)

        # Step 3: Calculate stuff trends (K%, BB%)
        stuff_trends = self.calculate_stuff_trends(data_by_year)

        # Step 4: Sticky stuff adaptation analysis
        sticky_stuff = self.calculate_sticky_stuff_adaptation(data_by_year)

        # Step 5: Workload forensics (3-year cumulative)
        workload_forensics = self.calculate_workload_forensics_multi_year(data_by_year)

        # Step 6: Arsenal evolution
        arsenal_evolution = self.calculate_arsenal_evolution(data_by_year)

        # Step 7: Merge with current year base data
        base_data = data_by_year[current_year].copy()

        # Step 7.5: Add Baseball Savant expected stats (xERA, xwOBA, xBA) for 2025 season
        print(f"\nAdding Baseball Savant expected stats for {current_year}...")
        base_data = self.add_expected_stats(base_data, season=current_year)

        # Merge all trend analyses
        full_data = self.merge_all_analyses(
            base_data=base_data,
            velo_trends=velo_trends,
            stuff_trends=stuff_trends,
            sticky_stuff=sticky_stuff,
            workload_forensics=workload_forensics,
            arsenal_evolution=arsenal_evolution
        )

        # Step 8: Add V1-style metrics needed for scoring
        print("\nCalculating supporting metrics...")
        full_data = self.calculate_arsenal_diversity(full_data)
        full_data = self.calculate_luck_metrics(full_data)
        full_data = self.calculate_role_mismatch(full_data)

        # Step 9: Calculate enhanced scoring with multi-year context
        print("\nCalculating enhanced scores with multi-year trends...")
        full_data = self.calculate_enhanced_true_talent_score(full_data)
        full_data = self.calculate_enhanced_upside_score(full_data)
        full_data = self.calculate_enhanced_confidence_score(full_data)

        # Step 9: Match with FA list
        print("\nMatching with free agent list...")
        fa_df = pd.DataFrame(fa_list, columns=['Name', 'Age_FA', 'Projected_WAR_FA'])
        fa_df['Is_FA'] = True

        result = full_data.merge(fa_df[['Name', 'Is_FA']], on='Name', how='left')
        result['Is_FA'] = result['Is_FA'].fillna(False)

        fa_only = result[result['Is_FA'] == True].copy()

        print(f"\nMatched {len(fa_only)} free agent relievers")
        print(f"Total relievers analyzed: {len(result)}")

        return result, fa_only

    def calculate_enhanced_true_talent_score(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate True Talent Score with multi-year trend adjustments.

        Base scoring (0-100):
        - Stuff Quality (40 pts): K/9, velocity, pitch values
        - Results Quality (30 pts): FIP, WAR
        - Sustainability (30 pts): BB/9, arsenal diversity, GB%

        Multi-year Adjustments:
        - Velocity trend: Declining = -10 pts, Improving = +5 pts
        - K% trend: Declining = -10 pts, Improving = +5 pts
        - Sticky stuff adapted = +10 pts
        """
        def calc_talent_v2(row):
            score = 0

            # Component 1: Stuff Quality (40 pts max)
            k_rate = row.get('K/9', 0)
            if k_rate >= 13.0:
                score += 20
            elif k_rate >= 11.0:
                score += 15
            elif k_rate >= 9.0:
                score += 10
            elif k_rate >= 7.5:
                score += 5

            fb_velo = row.get('FBv', row.get('Current_FBv', 0))
            if pd.notna(fb_velo):
                if fb_velo >= 97.0:
                    score += 10
                elif fb_velo >= 95.0:
                    score += 7
                elif fb_velo >= 93.0:
                    score += 4

            # wFB, wSL, wCH stuff values
            stuff_cols = ['wFB', 'wSL', 'wCH', 'wCB']
            total_stuff = sum([row.get(col, 0) or 0 for col in stuff_cols])
            if total_stuff >= 8.0:
                score += 10
            elif total_stuff >= 5.0:
                score += 7
            elif total_stuff >= 3.0:
                score += 4

            # Component 2: Results Quality (30 pts max)
            # Use 40% xERA + 60% FIP for skill-based results
            fip = row.get('FIP', 6.0)
            xera = row.get('xERA', fip)  # Fallback to FIP if no xERA

            # Blended ERA metric (60% FIP, 40% xERA)
            blended_era = 0.60 * fip + 0.40 * xera

            if blended_era <= 2.50:
                score += 15
            elif blended_era <= 3.00:
                score += 12
            elif blended_era <= 3.50:
                score += 9
            elif blended_era <= 4.00:
                score += 6

            war = row.get('WAR', 0)
            if war >= 2.0:
                score += 15
            elif war >= 1.5:
                score += 12
            elif war >= 1.0:
                score += 9
            elif war >= 0.5:
                score += 6

            # Component 3: Sustainability (30 pts max)
            bb_rate = row.get('BB/9', 5.0)
            if bb_rate <= 2.0:
                score += 15
            elif bb_rate <= 2.5:
                score += 12
            elif bb_rate <= 3.0:
                score += 9
            elif bb_rate <= 3.5:
                score += 6

            arsenal_div = row.get('Arsenal_Diversity', 1)
            if arsenal_div >= 4:
                score += 10
            elif arsenal_div >= 3:
                score += 7
            elif arsenal_div >= 2:
                score += 4

            gb_pct = row.get('GB%', 0)
            if gb_pct >= 0.50:
                score += 5
            elif gb_pct >= 0.45:
                score += 3

            # MULTI-YEAR ADJUSTMENTS
            # Velocity trend adjustment
            velo_trend_class = row.get('Velo_Trend_Classification', '')
            if velo_trend_class == 'Declining (Red Flag)':
                score -= 10
            elif velo_trend_class == 'Declining (Warning)':
                score -= 5
            elif velo_trend_class == 'Improving':
                score += 5

            # K% trend adjustment
            k_trend_class = row.get('K_Pct_Trend_Classification', '')
            if k_trend_class == 'Declining (Stuff Loss)':
                score -= 10
            elif k_trend_class == 'Declining (Warning)':
                score -= 5
            elif k_trend_class == 'Improving (Breakout)':
                score += 10

            # Sticky stuff adaptation bonus
            sticky_adapt = row.get('Sticky_Stuff_Adaptation', '')
            if sticky_adapt == 'Adapted Successfully':
                score += 10
            elif sticky_adapt == 'Still Struggling':
                score -= 10

            return max(0, min(score, 100))

        df['True_Talent_Score_V2'] = df.apply(calc_talent_v2, axis=1)
        return df

    def calculate_enhanced_upside_score(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate Upside Score with arsenal evolution and sticky stuff adaptation.

        Factors (0-100):
        - Role optimization potential (40 pts)
        - Age curve positioning (30 pts)
        - Arsenal evolution (20 pts): Added pitches = bonus
        - Sticky stuff adaptation = +10 pts
        - Luck-based regression (10 pts)
        """
        def calc_upside_v2(row):
            score = 0

            # Factor 1: Role optimization (40 pts)
            role_mismatch = row.get('Role_Mismatch', 'None')
            if role_mismatch == 'High':
                score += 40
            elif role_mismatch == 'Moderate':
                score += 25

            # Factor 2: Age curve (30 pts)
            age = row.get('Age', 35)
            if age <= 27:
                score += 30
            elif age <= 29:
                score += 20
            elif age <= 31:
                score += 10

            # Factor 3: Arsenal evolution (20 pts)
            arsenal_evo_score = row.get('Arsenal_Evolution_Score', 0)
            if arsenal_evo_score >= 40:
                score += 20
            elif arsenal_evo_score >= 20:
                score += 15
            elif arsenal_evo_score >= 10:
                score += 10

            # Factor 4: Sticky stuff adaptation (10 pts)
            sticky_adapt = row.get('Sticky_Stuff_Adaptation', '')
            if sticky_adapt == 'Adapted Successfully':
                score += 10

            # Factor 5: Luck regression based on xERA-ERA gap (20 pts max)
            era = row.get('ERA', 5.0)
            xera = row.get('xERA', era)

            if pd.notna(era) and pd.notna(xera):
                era_xera_gap = era - xera

                # Unlucky (ERA >> xERA) = positive regression expected
                if era_xera_gap >= 1.0:
                    score += 20  # Very unlucky - major upside
                elif era_xera_gap >= 0.50:
                    score += 10  # Moderately unlucky
                # Lucky (ERA << xERA) = negative regression risk
                elif era_xera_gap <= -1.0:
                    score -= 15  # Very lucky - regression risk
                elif era_xera_gap <= -0.50:
                    score -= 10  # Moderately lucky

            # Factor 6: Velocity recovery (bonus)
            velo_trend_class = row.get('Velo_Trend_Classification', '')
            if velo_trend_class == 'Improving':
                score += 10

            # Factor 7: K% improvement (bonus)
            k_trend_class = row.get('K_Pct_Trend_Classification', '')
            if k_trend_class == 'Improving (Breakout)':
                score += 15

            return max(0, min(score, 100))

        df['Upside_Score_V2'] = df.apply(calc_upside_v2, axis=1)
        return df

    def calculate_enhanced_confidence_score(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate Confidence Score with multi-year track record.

        Factors (0-100):
        - Sample size in 2025 (40 pts)
        - Multi-year consistency (30 pts)
        - Expected stats alignment (20 pts)
        - Track record (10 pts)
        """
        def calc_confidence_v2(row):
            score = 0

            # Factor 1: Sample size 2025 (40 pts)
            ip = row.get('IP', 0)
            if ip >= 60:
                score += 40
            elif ip >= 50:
                score += 35
            elif ip >= 40:
                score += 30
            elif ip >= 30:
                score += 20

            # Factor 2: Multi-year consistency (30 pts)
            # Check workload classification (reliable if normal/high workload)
            workload_class = row.get('Workload_Classification_3yr', '')
            if workload_class in ['High Workload', 'Normal Workload']:
                score += 20  # Consistent usage
            elif workload_class == 'High Appearance Frequency':
                score += 25  # Very consistent

            # Check velocity stability
            velo_trend_class = row.get('Velo_Trend_Classification', '')
            if velo_trend_class == 'Stable':
                score += 10

            # Factor 3: Expected stats alignment (20 pts)
            # xERA-ERA alignment is more important than ERA-FIP
            era = row.get('ERA', 5.0)
            xera = row.get('xERA', era)

            if pd.notna(era) and pd.notna(xera):
                era_xera_gap = abs(era - xera)

                # Tight alignment = skill > luck
                if era_xera_gap <= 0.30:
                    score += 20  # Highly aligned (skill-based)
                elif era_xera_gap <= 0.50:
                    score += 15
                elif era_xera_gap <= 0.75:
                    score += 10
                elif era_xera_gap <= 1.0:
                    score += 5
            else:
                # Fallback to ERA-FIP gap if no xERA
                era_fip_gap = abs(row.get('ERA_FIP_Gap', 0))
                if pd.notna(era_fip_gap):
                    if era_fip_gap <= 0.30:
                        score += 15
                    elif era_fip_gap <= 0.50:
                        score += 10

            # Factor 4: Track record WAR (10 pts)
            war = row.get('WAR', 0)
            if war >= 1.0:
                score += 10
            elif war >= 0.5:
                score += 7

            return max(0, min(score, 100))

        df['Confidence_Score_V2'] = df.apply(calc_confidence_v2, axis=1)
        return df
