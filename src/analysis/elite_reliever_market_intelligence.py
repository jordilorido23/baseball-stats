"""
Elite Reliever Market Intelligence System - 2025-26 Free Agency

This is the REAL market intelligence analysis for reliever free agents.

Focuses on ACTIONABLE insights for the 2025-26 FA class:

Level 3 Analysis (Competitive Edge):
    1. Pitch Arsenal Deep Dive
       - Arsenal diversity, stuff quality, FB reliance, velocity trends

    2. Multi-Year Trend Analysis (2023-2025)
       - Velocity, K%, BB%, GB% evolution

    3. Park & Defense Context
       - Park-adjusted ERA/FIP, defense impacts

    4. Workload Stress Forensics
       - 3-year cumulative IP, appearance clustering, high-leverage usage

    5. Pitch Sequencing & Predictability
       - Arsenal balance, wipeout pitch analysis, FB-SL dependency

    6. Platoon Optimization
       - L/R splits, platoon-neutral specialists, reverse platoon guys

    7. Biomechanical Red Flags
       - Velo decline, K% decline, workload stress, age risk

    8. Historical Contract Comps
       - 5-year RP FA market, premiums (closer, youth, high-K)

    9. Similar Reliever Breakouts
       - Historical clustering, late-bloomer comps

    10. Market Value Gap
        - True Value vs. Expected Contract = EDGE

Created: November 13, 2025
Author: Baseball Analytics Portfolio
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from scipy import stats
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import warnings
warnings.filterwarnings('ignore')

# Import existing analyzers
from .injury_risk_analyzer import InjuryRiskAnalyzer
from .aging_curves import AgingCurveAnalyzer
from .free_agent_analyzer import FreeAgentAnalyzer
from ..data.fangraphs_fetcher import FanGraphsFetcher
from ..data.savant_leaderboards import SavantLeaderboards


class EliteRelieverMarketIntelligence:
    """
    Comprehensive reliever free agent market intelligence system.

    Provides actionable insights for 2025-26 FA class:
    - Pitch arsenal analysis
    - Multi-year trends
    - Park/defense context
    - Workload forensics
    - Platoon optimization
    - Contract market efficiency
    - Historical breakout comps
    """

    def __init__(
        self,
        dollars_per_war: float = 8.0,
        cache_dir: str = "data/cache"
    ):
        """Initialize market intelligence system."""
        self.dollars_per_war = dollars_per_war

        # Data fetchers
        self.fg = FanGraphsFetcher(cache_dir=cache_dir)
        self.savant = SavantLeaderboards(cache_dir=cache_dir)

        # Analysis modules
        self.injury_analyzer = InjuryRiskAnalyzer()
        self.aging_analyzer = AgingCurveAnalyzer()
        self.fa_analyzer = FreeAgentAnalyzer(dollars_per_war=dollars_per_war)

        # Market intelligence thresholds
        self.thresholds = {
            # Arsenal metrics
            'elite_k_rate': 12.0,
            'elite_bb_rate': 2.5,
            'arsenal_diversity_elite': 4,
            'arsenal_diversity_good': 3,
            'fastball_reliance_high': 0.60,
            'fastball_slider_dependency': 0.80,

            # Trend signals
            'velo_decline_red_flag': -2.0,  # 2+ mph decline over 3 years
            'velo_decline_warning': -1.0,
            'k_pct_decline_red_flag': -5.0,  # 5 percentage points
            'k_pct_decline_warning': -2.5,

            # Workload thresholds
            'workload_3yr_extreme': 240,  # 240+ IP over 3 years
            'workload_3yr_high': 200,     # 200+ IP
            'workload_single_year_high': 80,  # 80+ IP in one year
            'appearance_frequency_high': 70,   # 70+ appearances

            # Platoon thresholds
            'platoon_neutral_era_diff': 0.5,  # <0.5 ERA difference
            'reverse_platoon_bonus': 0.75,    # LHP better vs RHB

            # Market comps
            'closer_premium_pct': 0.50,   # +50% AAV for closers
            'youth_premium_pct': 0.20,    # +20% AAV for age <30
            'high_k_premium_pct': 0.30,   # +30% AAV for K/9 >12
        }

        # Park factors (league-average = 100)
        # Source: FanGraphs park factors (sample data - would fetch real data)
        self.park_factors = {
            'COL': 115,  # Coors Field (hitter friendly)
            'NYY': 105,  # Yankee Stadium (HR friendly)
            'BOS': 105,  # Fenway Park
            'CIN': 102,  # Great American Ball Park
            'LAA': 98,   # Angel Stadium
            'OAK': 95,   # Oakland Coliseum (pitcher friendly)
            'SF': 92,    # Oracle Park (pitcher friendly)
            'SEA': 95,   # T-Mobile Park
            'MIA': 93,   # loanDepot park
            'SD': 92,    # Petco Park (pitcher friendly)
        }

    # =========================================================================
    # MODULE 0: BASEBALL SAVANT EXPECTED STATS INTEGRATION
    # =========================================================================

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

    # =========================================================================
    # MODULE 1: PITCH ARSENAL DEEP DIVE
    # =========================================================================

    def calculate_arsenal_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate comprehensive pitch arsenal metrics.

        Metrics:
        - Arsenal Diversity Score (count of pitches >10%)
        - Stuff Quality Index (weighted pitch values per 100 pitches)
        - Fastball Reliance Risk (FB% >60%)
        - Fastball-Slider Dependency (FB% + SL% >80%)
        - Wipeout Pitch (best pitch by value)

        Args:
            df: DataFrame with pitch usage and value data

        Returns:
            DataFrame with arsenal metrics added
        """
        print("\nCalculating pitch arsenal metrics...")

        result = df.copy()

        # Arsenal Diversity Score
        pitch_pcts = ['FB%', 'SL%', 'CB%', 'CH%', 'SF%', 'KN%']

        def count_pitches(row):
            count = 0
            for pitch in pitch_pcts:
                if pitch in row and pd.notna(row[pitch]) and row[pitch] >= 0.10:
                    count += 1
            return count

        result['Arsenal_Diversity_Count'] = result.apply(count_pitches, axis=1)

        # Classify arsenal diversity
        def classify_arsenal(count):
            if count >= self.thresholds['arsenal_diversity_elite']:
                return 'Elite (4+ Pitches)'
            elif count >= self.thresholds['arsenal_diversity_good']:
                return 'Good (3 Pitches)'
            elif count >= 2:
                return 'Average (2 Pitches)'
            else:
                return 'Limited (1 Pitch)'

        result['Arsenal_Diversity_Class'] = result['Arsenal_Diversity_Count'].apply(classify_arsenal)

        # Stuff Quality Index (weighted pitch values per 100 pitches)
        stuff_cols = ['wFB', 'wSL', 'wCH', 'wCB', 'wSF']

        def calc_stuff_index(row):
            total_stuff = 0
            for col in stuff_cols:
                if col in row and pd.notna(row[col]):
                    total_stuff += row[col] or 0
            return total_stuff

        result['Stuff_Quality_Index'] = result.apply(calc_stuff_index, axis=1)

        # Fastball Reliance Risk
        result['Fastball_Reliance_Pct'] = result.get('FB%', 0)

        def classify_fb_reliance(fb_pct):
            if pd.isna(fb_pct):
                return 'Unknown'
            elif fb_pct >= self.thresholds['fastball_reliance_high']:
                return 'High (>60% FB - Predictable)'
            elif fb_pct >= 0.50:
                return 'Moderate (50-60% FB)'
            else:
                return 'Low (<50% FB - Diverse)'

        result['Fastball_Reliance_Class'] = result['Fastball_Reliance_Pct'].apply(classify_fb_reliance)

        # Fastball-Slider Dependency
        fb_pct = result.get('FB%', 0).fillna(0)
        sl_pct = result.get('SL%', 0).fillna(0)
        result['FB_SL_Dependency_Pct'] = fb_pct + sl_pct

        def classify_fb_sl_dependency(fb_sl_pct):
            if fb_sl_pct >= self.thresholds['fastball_slider_dependency']:
                return 'High (>80% FB+SL - One-Dimensional)'
            elif fb_sl_pct >= 0.70:
                return 'Moderate (70-80% FB+SL)'
            else:
                return 'Low (<70% FB+SL - Diverse)'

        result['FB_SL_Dependency_Class'] = result['FB_SL_Dependency_Pct'].apply(classify_fb_sl_dependency)

        # Wipeout Pitch (highest value pitch)
        def find_wipeout_pitch(row):
            pitch_values = {}

            pitch_map = {
                'wFB': 'Fastball',
                'wSL': 'Slider',
                'wCH': 'Changeup',
                'wCB': 'Curveball',
                'wSF': 'Splitter'
            }

            for col, pitch_name in pitch_map.items():
                if col in row and pd.notna(row[col]):
                    pitch_values[pitch_name] = row[col] or 0

            if pitch_values:
                best_pitch = max(pitch_values, key=pitch_values.get)
                best_value = pitch_values[best_pitch]
                return f"{best_pitch} ({best_value:.1f})"
            return 'Unknown'

        result['Wipeout_Pitch'] = result.apply(find_wipeout_pitch, axis=1)

        # Secondary Stuff Quality (non-fastball pitches)
        def calc_secondary_stuff(row):
            secondary_total = 0
            secondary_cols = ['wSL', 'wCH', 'wCB', 'wSF']

            for col in secondary_cols:
                if col in row and pd.notna(row[col]):
                    secondary_total += row[col] or 0

            return secondary_total

        result['Secondary_Stuff_Quality'] = result.apply(calc_secondary_stuff, axis=1)

        # Elite Secondary (hidden gem indicator)
        def classify_secondary_stuff(secondary_value, fb_pct):
            if pd.isna(secondary_value) or pd.isna(fb_pct):
                return 'Unknown'

            # Elite secondaries buried in FB-heavy approach = EDGE
            if secondary_value >= 5.0 and fb_pct >= 0.60:
                return 'Elite Secondary (Hidden Gem)'
            elif secondary_value >= 5.0:
                return 'Elite Secondary'
            elif secondary_value >= 3.0:
                return 'Good Secondary'
            elif secondary_value >= 1.0:
                return 'Average Secondary'
            else:
                return 'Below Average Secondary'

        result['Secondary_Stuff_Class'] = result.apply(
            lambda row: classify_secondary_stuff(
                row.get('Secondary_Stuff_Quality', 0),
                row.get('Fastball_Reliance_Pct', 0)
            ),
            axis=1
        )

        print(f"  Arsenal metrics calculated for {len(result)} relievers")

        return result

    # =========================================================================
    # MODULE 2: MULTI-YEAR TREND ANALYSIS (2023-2025)
    # =========================================================================

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
            try:
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
            except Exception as e:
                print(f"    Error fetching {year}: {e}")
                continue

        return data_by_year

    def calculate_multi_year_trends(
        self,
        data_by_year: Dict[int, pd.DataFrame]
    ) -> pd.DataFrame:
        """
        Calculate 3-year trends for velocity, K%, BB%, GB%.

        Args:
            data_by_year: Dictionary of year → DataFrame

        Returns:
            DataFrame with trend metrics
        """
        print("\nCalculating multi-year trends (2023-2025)...")

        years = sorted(data_by_year.keys())

        if len(years) < 2:
            print("  Insufficient years for trend analysis")
            return pd.DataFrame()

        # Build trend dataset
        trend_metrics = []

        for metric, column in [
            ('FBv', 'FBv'),
            ('K_Pct', 'K%'),
            ('BB_Pct', 'BB%'),
            ('GB_Pct', 'GB%')
        ]:
            metric_data = []

            for year in years:
                df = data_by_year[year]
                if column in df.columns:
                    year_data = df[['Name', column]].copy()
                    year_data.columns = ['Name', f'{metric}_{year}']
                    metric_data.append(year_data)

            if metric_data:
                merged = metric_data[0]
                for df in metric_data[1:]:
                    merged = merged.merge(df, on='Name', how='outer')

                trend_metrics.append(merged)

        # Merge all metrics
        if not trend_metrics:
            return pd.DataFrame()

        result = trend_metrics[0]
        for df in trend_metrics[1:]:
            result = result.merge(df, on='Name', how='outer')

        # Calculate trends (most recent - oldest)
        if len(years) >= 3:
            recent_3_years = years[-3:]

            # Velocity trend
            result['Velo_Trend_3yr_mph'] = (
                result[f'FBv_{recent_3_years[-1]}'] - result[f'FBv_{recent_3_years[0]}']
            )

            # K% trend (convert to percentage points)
            result['K_Pct_Trend_3yr'] = (
                (result[f'K_Pct_{recent_3_years[-1]}'] - result[f'K_Pct_{recent_3_years[0]}']) * 100
            )

            # BB% trend
            result['BB_Pct_Trend_3yr'] = (
                (result[f'BB_Pct_{recent_3_years[-1]}'] - result[f'BB_Pct_{recent_3_years[0]}']) * 100
            )

            # GB% trend
            result['GB_Pct_Trend_3yr'] = (
                (result[f'GB_Pct_{recent_3_years[-1]}'] - result[f'GB_Pct_{recent_3_years[0]}']) * 100
            )

        # 1-year trend (year-over-year)
        if len(years) >= 2:
            result['Velo_Trend_1yr_mph'] = (
                result[f'FBv_{years[-1]}'] - result[f'FBv_{years[-2]}']
            )

            result['K_Pct_Trend_1yr'] = (
                (result[f'K_Pct_{years[-1]}'] - result[f'K_Pct_{years[-2]}']) * 100
            )

        # Current values
        result['Current_FBv'] = result[f'FBv_{years[-1]}']
        result['Current_K_Pct'] = result[f'K_Pct_{years[-1]}']
        result['Current_BB_Pct'] = result[f'BB_Pct_{years[-1]}']
        result['Current_GB_Pct'] = result[f'GB_Pct_{years[-1]}']

        # Classify trends
        def classify_velo_trend(velo_trend_3yr):
            if pd.isna(velo_trend_3yr):
                return 'Insufficient Data'
            elif velo_trend_3yr <= self.thresholds['velo_decline_red_flag']:
                return 'Declining (Red Flag)'
            elif velo_trend_3yr <= self.thresholds['velo_decline_warning']:
                return 'Declining (Warning)'
            elif velo_trend_3yr >= 1.0:
                return 'Improving'
            else:
                return 'Stable'

        result['Velo_Trend_Classification'] = result['Velo_Trend_3yr_mph'].apply(classify_velo_trend)

        def classify_k_trend(k_trend_3yr):
            if pd.isna(k_trend_3yr):
                return 'Insufficient Data'
            elif k_trend_3yr <= self.thresholds['k_pct_decline_red_flag']:
                return 'Declining (Stuff Loss)'
            elif k_trend_3yr <= self.thresholds['k_pct_decline_warning']:
                return 'Declining (Warning)'
            elif k_trend_3yr >= 3.0:
                return 'Improving (Breakout)'
            else:
                return 'Stable'

        result['K_Pct_Trend_Classification'] = result['K_Pct_Trend_3yr'].apply(classify_k_trend)

        print(f"  Calculated trends for {len(result)} relievers")

        return result

    # =========================================================================
    # MODULE 3: PARK & DEFENSE CONTEXT
    # =========================================================================

    def calculate_park_adjusted_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate park-adjusted ERA and FIP.

        Args:
            df: DataFrame with ERA, FIP, Team columns

        Returns:
            DataFrame with park-adjusted metrics
        """
        print("\nCalculating park-adjusted metrics...")

        result = df.copy()

        # Map team abbreviations to park factors
        def get_park_factor(team):
            if pd.isna(team):
                return 100  # League average

            # Handle multi-team players (e.g., "- - -" or "TEX, CHC")
            if team in ['- - -', 'FFA']:
                return 100

            # Get first team if multiple teams
            first_team = team.split(',')[0].strip()

            return self.park_factors.get(first_team, 100)

        result['Park_Factor'] = result['Team'].apply(get_park_factor)

        # Park-adjusted ERA = ERA × 100 / Park Factor
        result['ERA_Park_Adjusted'] = result['ERA'] * 100 / result['Park_Factor']

        # Park-adjusted FIP (less affected by park, but still some impact)
        # Use 70% weight for park adjustment on FIP
        result['FIP_Park_Adjusted'] = result['FIP'] * 100 / (result['Park_Factor'] * 0.7 + 30)

        # Calculate park advantage/disadvantage
        def classify_park_context(park_factor):
            if park_factor >= 110:
                return 'Hitter-Friendly (Coors-level)'
            elif park_factor >= 105:
                return 'Hitter-Friendly (Moderate)'
            elif park_factor >= 95:
                return 'Neutral'
            elif park_factor >= 90:
                return 'Pitcher-Friendly (Moderate)'
            else:
                return 'Pitcher-Friendly (SF/SD-level)'

        result['Park_Context'] = result['Park_Factor'].apply(classify_park_context)

        # Identify context-driven ERA inflation/deflation
        result['ERA_Park_Impact'] = result['ERA'] - result['ERA_Park_Adjusted']

        def classify_park_impact(era_impact):
            if abs(era_impact) < 0.20:
                return 'Minimal Park Impact'
            elif era_impact >= 0.50:
                return 'Park Inflated ERA (Hidden Gem)'
            elif era_impact <= -0.50:
                return 'Park Deflated ERA (Risk)'
            elif era_impact > 0:
                return 'Slight Park Inflation'
            else:
                return 'Slight Park Deflation'

        result['Park_Impact_Class'] = result['ERA_Park_Impact'].apply(classify_park_impact)

        print(f"  Park-adjusted metrics calculated for {len(result)} relievers")

        return result

    # =========================================================================
    # MODULE 4: WORKLOAD STRESS FORENSICS
    # =========================================================================

    def calculate_workload_forensics(
        self,
        data_by_year: Dict[int, pd.DataFrame],
        current_year_df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Calculate 3-year cumulative workload and stress indicators.

        Args:
            data_by_year: Dictionary of year → DataFrame
            current_year_df: Current year DataFrame with names

        Returns:
            DataFrame with workload forensics
        """
        print("\nCalculating workload stress forensics...")

        years = sorted(data_by_year.keys())
        recent_3_years = years[-3:] if len(years) >= 3 else years

        # Build cumulative workload dataset
        workload_data = []

        for year in recent_3_years:
            df = data_by_year[year]
            year_data = df[['Name', 'IP', 'G']].copy()
            year_data.columns = ['Name', f'IP_{year}', f'G_{year}']
            workload_data.append(year_data)

        if not workload_data:
            return pd.DataFrame()

        # Merge all years
        result = workload_data[0]
        for df in workload_data[1:]:
            result = result.merge(df, on='Name', how='outer')

        # Calculate cumulative totals
        ip_cols = [f'IP_{y}' for y in recent_3_years]
        g_cols = [f'G_{y}' for y in recent_3_years]

        result['Cumulative_IP_3yr'] = result[ip_cols].sum(axis=1, skipna=True)
        result['Cumulative_G_3yr'] = result[g_cols].sum(axis=1, skipna=True)

        # Average IP per appearance
        result['Avg_IP_Per_App_3yr'] = result['Cumulative_IP_3yr'] / result['Cumulative_G_3yr']

        # Workload trend (increasing or decreasing)
        if len(recent_3_years) >= 3:
            result['IP_Trend_3yr'] = (
                result[f'IP_{recent_3_years[-1]}'] - result[f'IP_{recent_3_years[0]}']
            )

            result['Appearance_Trend_3yr'] = (
                result[f'G_{recent_3_years[-1]}'] - result[f'G_{recent_3_years[0]}']
            )

        # Classify workload stress
        def classify_workload(row):
            cumulative_ip = row.get('Cumulative_IP_3yr', 0)
            cumulative_g = row.get('Cumulative_G_3yr', 0)

            if cumulative_ip >= self.thresholds['workload_3yr_extreme']:
                return 'Extreme Workload (Fatigue Risk)'
            elif cumulative_ip >= self.thresholds['workload_3yr_high']:
                return 'High Workload'
            elif cumulative_g >= 200:
                return 'High Appearance Frequency'
            else:
                return 'Normal Workload'

        result['Workload_Classification_3yr'] = result.apply(classify_workload, axis=1)

        # Identify workload risk (high IP + declining stuff)
        # This will be enriched later when we merge with trend data

        print(f"  Workload forensics calculated for {len(result)} relievers")

        return result

    # =========================================================================
    # MODULE 5: PITCH SEQUENCING & PREDICTABILITY
    # =========================================================================

    def calculate_pitch_sequencing_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate pitch sequencing and predictability metrics.

        Metrics:
        - Arsenal Balance Score (deviation from even usage)
        - Pitch Evolution (added/dropped pitches)
        - Wipeout Pitch Analysis

        Args:
            df: DataFrame with pitch usage data

        Returns:
            DataFrame with sequencing metrics
        """
        print("\nCalculating pitch sequencing metrics...")

        result = df.copy()

        # Arsenal Balance Score
        # Perfect balance = all pitches used equally
        # High deviation = predictable (over-reliant on 1-2 pitches)

        pitch_cols = ['FB%', 'SL%', 'CB%', 'CH%', 'SF%']

        def calc_arsenal_balance(row):
            pitches_used = []
            for col in pitch_cols:
                if col in row and pd.notna(row[col]):
                    pitches_used.append(row[col] or 0)

            if not pitches_used:
                return np.nan

            # Calculate standard deviation of pitch usage
            # Lower std = more balanced
            std_dev = np.std(pitches_used)

            # Convert to balance score (0-100, higher = more balanced)
            # Perfect balance (4 pitches at 25% each) has std ~0
            # Extreme imbalance (100% one pitch) has std ~0.45
            balance_score = max(0, 100 - (std_dev * 200))

            return balance_score

        result['Arsenal_Balance_Score'] = result.apply(calc_arsenal_balance, axis=1)

        def classify_balance(score):
            if pd.isna(score):
                return 'Unknown'
            elif score >= 80:
                return 'Highly Balanced (Unpredictable)'
            elif score >= 60:
                return 'Moderately Balanced'
            elif score >= 40:
                return 'Somewhat Imbalanced'
            else:
                return 'Highly Imbalanced (Predictable)'

        result['Arsenal_Balance_Class'] = result['Arsenal_Balance_Score'].apply(classify_balance)

        print(f"  Pitch sequencing metrics calculated for {len(result)} relievers")

        return result

    # =========================================================================
    # MODULE 6: PLATOON OPTIMIZATION (Placeholder - requires split data)
    # =========================================================================

    def calculate_platoon_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate platoon split metrics.

        NOTE: This is a placeholder. Real implementation would require
        fetching split data from Savant or FanGraphs (vs LHB/RHB).

        Args:
            df: DataFrame with reliever data

        Returns:
            DataFrame with platoon metrics (placeholder)
        """
        print("\nCalculating platoon metrics (placeholder)...")

        result = df.copy()

        # Placeholder columns
        result['Platoon_Split_ERA_Diff'] = np.nan
        result['Platoon_Neutral_Flag'] = False
        result['Reverse_Platoon_Flag'] = False

        # TODO: Implement real platoon split analysis when split data available
        # Would need to fetch:
        # - RHP vs LHB ERA, RHP vs RHB ERA
        # - LHP vs LHB ERA, LHP vs RHB ERA
        # Then calculate:
        # - ERA difference (neutral if <0.5)
        # - Reverse platoon (LHP better vs RHB)

        print("  Platoon metrics (placeholder) - requires split data")

        return result

    # =========================================================================
    # MODULE 7: HISTORICAL CONTRACT COMPS
    # =========================================================================

    def build_contract_comp_model(self) -> Dict:
        """
        Build historical contract comp database (placeholder).

        NOTE: Real implementation would scrape Spotrac/Cot's for last 5 years
        of RP free agent signings.

        Returns:
            Dictionary with contract market insights
        """
        print("\nBuilding contract comp model...")

        # Placeholder comp data (would be fetched from Spotrac in real implementation)
        comp_database = {
            'closer_premium': self.thresholds['closer_premium_pct'],
            'youth_premium': self.thresholds['youth_premium_pct'],
            'high_k_premium': self.thresholds['high_k_premium_pct'],
            'base_dollars_per_war': self.dollars_per_war,

            # Sample historical comps (placeholder)
            'sample_comps': [
                {'name': 'Josh Hader', 'year': 2023, 'age': 29, 'war': 2.5, 'saves': 33, 'k_9': 14.5, 'aav': 19.0},
                {'name': 'Edwin Diaz', 'year': 2022, 'age': 28, 'war': 3.0, 'saves': 32, 'k_9': 16.0, 'aav': 20.0},
                {'name': 'Kenley Jansen', 'year': 2022, 'age': 34, 'war': 1.5, 'saves': 38, 'k_9': 9.5, 'aav': 16.0},
            ]
        }

        print("  Contract comp model built (placeholder)")

        return comp_database

    def calculate_market_value_gap(self, df: pd.DataFrame, contract_comps: Dict) -> pd.DataFrame:
        """
        Calculate market value gap (true value vs expected contract).

        Args:
            df: DataFrame with reliever stats
            contract_comps: Contract comp database

        Returns:
            DataFrame with market value metrics
        """
        print("\nCalculating market value gap...")

        result = df.copy()

        # Calculate true value (WAR-based)
        war = result.get('WAR', 0)
        result['True_Value_WAR_Based'] = war * contract_comps['base_dollars_per_war']

        # Estimate expected contract based on profile
        def estimate_expected_contract(row):
            base_value = row.get('True_Value_WAR_Based', 0)

            if base_value <= 0:
                return 0

            multiplier = 1.0

            # Closer premium
            saves = row.get('SV', 0)
            if saves >= 30:
                multiplier += contract_comps['closer_premium']
            elif saves >= 20:
                multiplier += contract_comps['closer_premium'] * 0.5

            # Youth premium
            age = row.get('Age', 35)
            if age < 30:
                multiplier += contract_comps['youth_premium']

            # High-K premium
            k_9 = row.get('K/9', 0)
            if k_9 >= 12.0:
                multiplier += contract_comps['high_k_premium']
            elif k_9 >= 10.5:
                multiplier += contract_comps['high_k_premium'] * 0.5

            return base_value * multiplier

        result['Expected_Contract_AAV'] = result.apply(estimate_expected_contract, axis=1)

        # Calculate market value gap
        result['Market_Value_Gap'] = result['True_Value_WAR_Based'] - result['Expected_Contract_AAV']

        # Classify market efficiency
        def classify_market_value(gap):
            if pd.isna(gap):
                return 'Unknown'
            elif gap >= 5.0:
                return 'Major Undervalued (Hidden Gem)'
            elif gap >= 2.0:
                return 'Undervalued (Good Value)'
            elif gap >= -2.0:
                return 'Fairly Valued'
            elif gap >= -5.0:
                return 'Overvalued (Market Premium)'
            else:
                return 'Major Overvalued (Avoid)'

        result['Market_Value_Class'] = result['Market_Value_Gap'].apply(classify_market_value)

        print(f"  Market value gap calculated for {len(result)} relievers")

        return result

    # =========================================================================
    # MODULE 8: HISTORICAL BREAKOUT CLUSTERING
    # =========================================================================

    def find_similar_breakout_comps(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Find similar historical relievers using clustering.

        Cluster by: Age, FBv, K%, BB%, pitch mix
        Identify breakout patterns from historical data.

        Args:
            df: DataFrame with reliever data

        Returns:
            DataFrame with similarity clusters and breakout comps
        """
        print("\nFinding similar breakout comps via clustering...")

        result = df.copy()

        # Select features for clustering
        cluster_features = []
        feature_cols = ['Age', 'FBv', 'K/9', 'BB/9', 'FB%', 'SL%']

        # Build feature matrix
        feature_data = []
        valid_indices = []

        for idx, row in result.iterrows():
            features = []
            valid = True

            for col in feature_cols:
                val = row.get(col, np.nan)
                if pd.isna(val):
                    valid = False
                    break
                features.append(val)

            if valid:
                feature_data.append(features)
                valid_indices.append(idx)

        if len(feature_data) < 10:
            print("  Insufficient data for clustering")
            result['Cluster_ID'] = -1
            result['Similar_Comp_Archetype'] = 'Insufficient Data'
            return result

        # Standardize features
        scaler = StandardScaler()
        features_scaled = scaler.fit_transform(feature_data)

        # K-means clustering (5 clusters for archetypes)
        n_clusters = min(5, len(feature_data) // 10)
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        clusters = kmeans.fit_predict(features_scaled)

        # Assign cluster IDs
        result['Cluster_ID'] = -1
        for i, idx in enumerate(valid_indices):
            result.at[idx, 'Cluster_ID'] = clusters[i]

        # Label clusters with archetypes
        cluster_archetypes = {
            0: 'Power Arm (High Velo, High K)',
            1: 'Finesse (Low Velo, Good Control)',
            2: 'Slider Specialist',
            3: 'Balanced Arsenal',
            4: 'Groundball Artist'
        }

        result['Similar_Comp_Archetype'] = result['Cluster_ID'].apply(
            lambda x: cluster_archetypes.get(x, 'Unclustered')
        )

        print(f"  Clustered {len(feature_data)} relievers into {n_clusters} archetypes")

        return result

    # =========================================================================
    # MODULE 9: FINAL COMPOSITE SCORING
    # =========================================================================

    def calculate_composite_scores(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate final composite scores for market intelligence.

        Scores (0-100 each):
        - True Talent Score: Stuff + Results + Sustainability
        - Health Risk Score: Biomechanical signals + Workload + Age
        - Upside Score: Role optimization + Context + Arsenal evolution
        - Confidence Score: Sample size + Consistency + Alignment
        - Overall Value Score: Weighted combination

        Args:
            df: DataFrame with all analytics

        Returns:
            DataFrame with composite scores
        """
        print("\nCalculating composite scores...")

        result = df.copy()

        # TRUE TALENT SCORE (0-100)
        result = self._calculate_true_talent_score(result)

        # HEALTH RISK SCORE (0-100)
        result = self._calculate_health_risk_score(result)

        # UPSIDE SCORE (0-100)
        result = self._calculate_upside_score(result)

        # CONFIDENCE SCORE (0-100)
        result = self._calculate_confidence_score(result)

        # OVERALL VALUE SCORE (0-100)
        # Weighted combination: 40% Talent, 30% Upside, 20% Confidence, -10% Health Risk
        result['Overall_Value_Score'] = (
            result['True_Talent_Score'] * 0.40 +
            result['Upside_Score'] * 0.30 +
            result['Confidence_Score'] * 0.20 -
            result['Health_Risk_Score'] * 0.10
        ).clip(0, 100)

        print(f"  Composite scores calculated for {len(result)} relievers")

        return result

    def _calculate_true_talent_score(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate True Talent Score (0-100)."""

        def calc_talent(row):
            score = 0

            # Component 1: Stuff Quality (40 pts)
            k_9 = row.get('K/9', 0)
            if k_9 >= 13.0:
                score += 20
            elif k_9 >= 11.0:
                score += 15
            elif k_9 >= 9.0:
                score += 10
            elif k_9 >= 7.5:
                score += 5

            fb_velo = row.get('FBv', row.get('Current_FBv', 0))
            if pd.notna(fb_velo):
                if fb_velo >= 97.0:
                    score += 10
                elif fb_velo >= 95.0:
                    score += 7
                elif fb_velo >= 93.0:
                    score += 4

            stuff_index = row.get('Stuff_Quality_Index', 0) or 0
            if stuff_index >= 8.0:
                score += 10
            elif stuff_index >= 5.0:
                score += 7
            elif stuff_index >= 3.0:
                score += 4

            # Component 2: Results Quality (30 pts)
            # Use 40% xERA + 60% FIP for skill-based results
            # Prefer park-adjusted if available
            fip = row.get('FIP_Park_Adjusted', row.get('FIP', 6.0))
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

            # Component 3: Sustainability (30 pts)
            bb_9 = row.get('BB/9', 5.0)
            if bb_9 <= 2.0:
                score += 15
            elif bb_9 <= 2.5:
                score += 12
            elif bb_9 <= 3.0:
                score += 9
            elif bb_9 <= 3.5:
                score += 6

            arsenal_div = row.get('Arsenal_Diversity_Count', 1)
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

            # Trend adjustments
            velo_trend = row.get('Velo_Trend_Classification', '')
            if velo_trend == 'Declining (Red Flag)':
                score -= 10
            elif velo_trend == 'Declining (Warning)':
                score -= 5
            elif velo_trend == 'Improving':
                score += 5

            k_trend = row.get('K_Pct_Trend_Classification', '')
            if k_trend == 'Declining (Stuff Loss)':
                score -= 10
            elif k_trend == 'Declining (Warning)':
                score -= 5
            elif k_trend == 'Improving (Breakout)':
                score += 10

            return max(0, min(score, 100))

        df['True_Talent_Score'] = df.apply(calc_talent, axis=1)
        return df

    def _calculate_health_risk_score(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate Health Risk Score (0-100, higher = more risk)."""

        def calc_health_risk(row):
            risk = 0

            # Velocity decline
            velo_trend = row.get('Velo_Trend_3yr_mph', 0)
            if pd.notna(velo_trend):
                if velo_trend <= -2.0:
                    risk += 30
                elif velo_trend <= -1.0:
                    risk += 15

            # K% decline
            k_trend = row.get('K_Pct_Trend_3yr', 0)
            if pd.notna(k_trend):
                if k_trend <= -5.0:
                    risk += 25
                elif k_trend <= -2.5:
                    risk += 10

            # Workload stress
            workload_class = row.get('Workload_Classification_3yr', '')
            if workload_class == 'Extreme Workload (Fatigue Risk)':
                risk += 20
            elif workload_class == 'High Workload':
                risk += 10

            # Age risk
            age = row.get('Age', 30)
            if age >= 35:
                risk += 20
            elif age >= 33:
                risk += 10

            return max(0, min(risk, 100))

        df['Health_Risk_Score'] = df.apply(calc_health_risk, axis=1)
        return df

    def _calculate_upside_score(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate Upside Score (0-100)."""

        def calc_upside(row):
            score = 0

            # Role optimization (closer potential)
            saves = row.get('SV', 0)
            k_9 = row.get('K/9', 0)
            bb_9 = row.get('BB/9', 5.0)

            # Elite stuff but not closer = upside
            if k_9 >= 11.0 and bb_9 <= 2.5 and saves < 15:
                score += 40
            elif k_9 >= 10.0 and bb_9 <= 3.0 and saves < 20:
                score += 25

            # Age curve
            age = row.get('Age', 35)
            if age <= 27:
                score += 30
            elif age <= 29:
                score += 20
            elif age <= 31:
                score += 10

            # Park context (bad park = upside in new team)
            park_impact = row.get('ERA_Park_Impact', 0)
            if park_impact >= 0.50:
                score += 15
            elif park_impact >= 0.25:
                score += 10

            # Arsenal evolution
            secondary_class = row.get('Secondary_Stuff_Class', '')
            if 'Elite Secondary (Hidden Gem)' in secondary_class:
                score += 20
            elif 'Elite Secondary' in secondary_class:
                score += 10

            # Velocity improvement
            velo_trend = row.get('Velo_Trend_Classification', '')
            if velo_trend == 'Improving':
                score += 10

            # K% improvement
            k_trend = row.get('K_Pct_Trend_Classification', '')
            if k_trend == 'Improving (Breakout)':
                score += 15

            # xERA-ERA gap for luck-based upside (20 pts max)
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

            return max(0, min(score, 100))

        df['Upside_Score'] = df.apply(calc_upside, axis=1)
        return df

    def _calculate_confidence_score(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate Confidence Score (0-100)."""

        def calc_confidence(row):
            score = 0

            # Sample size
            ip = row.get('IP', 0)
            if ip >= 60:
                score += 40
            elif ip >= 50:
                score += 35
            elif ip >= 40:
                score += 30
            elif ip >= 30:
                score += 20

            # Multi-year consistency
            workload_class = row.get('Workload_Classification_3yr', '')
            if workload_class in ['High Workload', 'Normal Workload', 'High Appearance Frequency']:
                score += 25

            # Velocity stability
            velo_trend = row.get('Velo_Trend_Classification', '')
            if velo_trend == 'Stable':
                score += 10

            # xERA-ERA alignment (more important than ERA-FIP)
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
                era_park_adj = row.get('ERA_Park_Adjusted', row.get('ERA', 5.0))
                fip_park_adj = row.get('FIP_Park_Adjusted', row.get('FIP', 5.0))
                gap = abs(era_park_adj - fip_park_adj)

                if pd.notna(gap):
                    if gap <= 0.30:
                        score += 15
                    elif gap <= 0.50:
                        score += 10

            # Track record WAR
            war = row.get('WAR', 0)
            if war >= 1.0:
                score += 5

            return max(0, min(score, 100))

        df['Confidence_Score'] = df.apply(calc_confidence, axis=1)
        return df

    # =========================================================================
    # Helper methods for later modules
    # =========================================================================

    def merge_all_analyses(
        self,
        base_data: pd.DataFrame,
        arsenal_metrics: pd.DataFrame,
        trend_data: pd.DataFrame,
        workload_data: pd.DataFrame
    ) -> pd.DataFrame:
        """Merge all analyses into comprehensive dataset."""

        print("\nMerging all analyses...")

        result = base_data.copy()

        # Merge arsenal metrics (already calculated on base_data, but just in case)
        if not arsenal_metrics.empty and 'Name' in arsenal_metrics.columns:
            # Arsenal metrics should already be in base_data
            pass

        # Merge trend data
        if not trend_data.empty:
            result = result.merge(trend_data, on='Name', how='left')
            print(f"  Merged trend data: {len(trend_data)} players")

        # Merge workload data
        if not workload_data.empty:
            result = result.merge(workload_data, on='Name', how='left')
            print(f"  Merged workload data: {len(workload_data)} players")

        return result

    def run_comprehensive_analysis(
        self,
        fa_list: List[Tuple[str, int, float]],
        current_year: int = 2025,
        lookback_years: int = 3
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Run FULL market intelligence analysis.

        Args:
            fa_list: List of (name, age, projected_war) for FA relievers
            current_year: Current season
            lookback_years: Years of historical data to analyze

        Returns:
            (full_analysis, fa_only) DataFrames
        """
        print("\n" + "="*80)
        print("ELITE RELIEVER MARKET INTELLIGENCE SYSTEM - 2025-26 FA CLASS")
        print("="*80)

        # Step 1: Fetch multi-year data
        years_to_fetch = list(range(current_year - lookback_years + 1, current_year + 1))
        data_by_year = self.fetch_multi_year_data(years=years_to_fetch, min_ip=10)

        if not data_by_year or current_year not in data_by_year:
            raise ValueError(f"Could not fetch data for {current_year}")

        # Step 2: Get current year base data
        base_data = data_by_year[current_year].copy()

        # Step 2.5: Add Baseball Savant expected stats (xERA, xwOBA, xBA) for 2025 season
        print(f"\nAdding Baseball Savant expected stats for {current_year}...")
        base_data = self.add_expected_stats(base_data, season=current_year)

        # Step 3: Calculate arsenal metrics
        base_data = self.calculate_arsenal_metrics(base_data)

        # Step 4: Calculate multi-year trends
        trend_data = self.calculate_multi_year_trends(data_by_year)

        # Step 5: Calculate park-adjusted metrics
        base_data = self.calculate_park_adjusted_metrics(base_data)

        # Step 6: Calculate workload forensics
        workload_data = self.calculate_workload_forensics(data_by_year, base_data)

        # Step 7: Calculate pitch sequencing metrics
        base_data = self.calculate_pitch_sequencing_metrics(base_data)

        # Step 8: Calculate platoon metrics (placeholder)
        base_data = self.calculate_platoon_metrics(base_data)

        # Step 9: Merge all analyses
        full_data = self.merge_all_analyses(
            base_data=base_data,
            arsenal_metrics=base_data,  # Already merged
            trend_data=trend_data,
            workload_data=workload_data
        )

        # Step 10: Build contract comp model and calculate market value gap
        contract_comps = self.build_contract_comp_model()
        full_data = self.calculate_market_value_gap(full_data, contract_comps)

        # Step 11: Find similar breakout comps via clustering
        full_data = self.find_similar_breakout_comps(full_data)

        # Step 12: Calculate final composite scores
        full_data = self.calculate_composite_scores(full_data)

        # Step 13: Match with FA list
        print("\nMatching with free agent list...")
        fa_df = pd.DataFrame(fa_list, columns=['Name', 'Age_FA', 'Projected_WAR_FA'])
        fa_df['Is_FA'] = True

        result = full_data.merge(fa_df[['Name', 'Is_FA']], on='Name', how='left')
        result['Is_FA'] = result['Is_FA'].fillna(False)

        fa_only = result[result['Is_FA'] == True].copy()

        print(f"\nMatched {len(fa_only)} free agent relievers")
        print(f"Total relievers analyzed: {len(result)}")

        return result, fa_only


if __name__ == "__main__":
    # Example usage
    analyzer = EliteRelieverMarketIntelligence()

    # Sample FA list
    fa_list = [
        ('Tanner Scott', 30, 2.0),
        ('Carlos Estevez', 31, 1.5),
        ('Jeff Hoffman', 31, 1.5),
    ]

    full_analysis, fa_only = analyzer.run_comprehensive_analysis(fa_list, current_year=2025)

    print("\n" + "="*80)
    print("ANALYSIS COMPLETE")
    print("="*80)
    print(f"Total relievers analyzed: {len(full_analysis)}")
    print(f"Free agents in 2025-26 class: {len(fa_only)}")
