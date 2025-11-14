"""
Elite Reliever Free Agent Analysis - Deep Dive Edition

This module goes 3 LEVELS DEEPER than standard reliever evaluation:

Level 1 (Everyone): ERA, xERA, WAR, velocity
Level 2 (Good FOs): Aging curves, injury risk, platoon splits
Level 3 (EDGE - Us): Arsenal evolution, workload forensics, role mismatch,
                      contract modeling, breakout clustering

Philosophy: Find market inefficiencies in reliever valuation by identifying:
- Sticky stuff adaptation winners (post-2021 enforcement)
- Unlucky high-ERA guys with elite xStats (park/defense victims)
- Setup talent buried in bad bullpens (future closers)
- Injury bounce-back candidates (late-season returns)
- Role mismatches (elite stuff in low-leverage)

Created: November 13, 2025
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


class EliteRelieverAnalyzer:
    """
    Comprehensive reliever free agent analysis system.

    Identifies undervalued relievers using multi-dimensional scoring:
    1. True Talent (stuff quality + context-adjusted results)
    2. Health Risk (biomechanical signals + workload stress)
    3. Upside (role optimization + arsenal evolution)
    4. Market Value Gap (true value vs. expected contract)
    5. Confidence (sample size + track record)
    """

    def __init__(
        self,
        dollars_per_war: float = 8.0,
        cache_dir: str = "data/cache"
    ):
        """
        Initialize elite reliever analyzer.

        Args:
            dollars_per_war: Market rate for WAR (default $8M for relievers)
            cache_dir: Directory for cached data
        """
        self.dollars_per_war = dollars_per_war

        # Initialize data fetchers
        self.fg = FanGraphsFetcher(cache_dir=cache_dir)
        self.savant = SavantLeaderboards(cache_dir=cache_dir)

        # Initialize analysis modules
        self.injury_analyzer = InjuryRiskAnalyzer()
        self.aging_analyzer = AgingCurveAnalyzer()
        self.fa_analyzer = FreeAgentAnalyzer(dollars_per_war=dollars_per_war)

        # Risk thresholds
        self.thresholds = {
            'elite_k_rate': 12.0,        # K/9 >= 12.0 = elite strikeout stuff
            'elite_bb_rate': 2.5,         # BB/9 <= 2.5 = elite control
            'high_leverage_pct': 0.50,    # >50% high-leverage = closer/setup
            'velo_decline_mph': -2.0,     # 2+ mph drop = red flag
            'workload_risk_ip': 80,       # 80+ IP for reliever = fatigue risk
            'unlucky_era_gap': 0.50,      # ERA - xERA > 0.50 = unlucky
            'lucky_era_gap': -0.50,       # ERA - xERA < -0.50 = lucky
            'arsenal_diversity': 3,       # 3+ pitches >10% usage = diverse
            'fastball_reliance': 0.60,    # >60% FB = predictable
        }

    def load_free_agent_list(
        self,
        fa_list: List[Tuple[str, int, float]]
    ) -> pd.DataFrame:
        """
        Load free agent reliever list and basic info.

        Args:
            fa_list: List of (name, age, projected_war) tuples

        Returns:
            DataFrame with FA relievers
        """
        df = pd.DataFrame(fa_list, columns=['Name', 'Age', 'Projected_WAR'])
        df['Is_FA'] = True
        return df

    def fetch_reliever_data(
        self,
        season: int = 2025,
        min_ip: int = 10
    ) -> pd.DataFrame:
        """
        Fetch all reliever data from FanGraphs (GS = 0).

        Args:
            season: Season year
            min_ip: Minimum innings pitched

        Returns:
            DataFrame with reliever statistics
        """
        print(f"\nFetching FanGraphs pitching data for {season}...")
        pitching = self.fg.get_pitching_stats(season, qual=1)

        # Filter to relievers only (GS = 0)
        relievers = pitching[pitching['GS'] == 0].copy()

        # Filter by minimum IP
        relievers = relievers[relievers['IP'] >= min_ip]

        print(f"Found {len(relievers)} relievers with {min_ip}+ IP in {season}")

        return relievers

    def add_expected_stats(
        self,
        relievers: pd.DataFrame,
        season: int = 2025
    ) -> pd.DataFrame:
        """
        Add Baseball Savant expected stats (xERA, xwOBA, etc.).

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

                # Calculate xERA proxy (using xwOBA)
                # xERA ≈ FIP-like formula using xwOBA
                result['xERA_proxy'] = result['FIP']  # Use FIP as proxy for now

                result.drop(columns=['merge_key'], inplace=True)

                print(f"Merged expected stats for {result['xwOBA'].notna().sum()} relievers")

                return result
            else:
                print("Warning: Savant data format unexpected, skipping xStats merge")
                return relievers

        except Exception as e:
            print(f"Error fetching expected stats: {e}")
            return relievers

    def calculate_arsenal_metrics(
        self,
        relievers: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Calculate pitch arsenal quality and diversity metrics.

        Metrics:
        - Arsenal diversity (number of pitches >10% usage)
        - Stuff quality index (weighted pitch values)
        - Fastball reliance risk (FB% >60%)
        - Velocity trends (if multi-year data available)

        Args:
            relievers: DataFrame with pitch type data

        Returns:
            DataFrame with arsenal metrics added
        """
        result = relievers.copy()

        # Calculate arsenal diversity (count pitches used >10%)
        pitch_pcts = ['FB%', 'SL%', 'CB%', 'CH%', 'SF%', 'KN%']

        def count_diverse_pitches(row):
            count = 0
            for pitch in pitch_pcts:
                if pitch in row and pd.notna(row[pitch]) and row[pitch] >= 0.10:
                    count += 1
            return count

        result['Arsenal_Diversity'] = result.apply(count_diverse_pitches, axis=1)

        # Calculate stuff quality index (weighted pitch values per 100 pitches)
        # wFB, wSL, wCH, wCB = run values per 100 pitches
        stuff_cols = ['wFB', 'wSL', 'wCB', 'wCH', 'wSF']

        def calculate_stuff_index(row):
            total_value = 0
            for col in stuff_cols:
                if col in row and pd.notna(row[col]):
                    total_value += row[col]
            return total_value

        result['Stuff_Quality_Index'] = result.apply(calculate_stuff_index, axis=1)

        # Fastball reliance risk (FB% from 'FB% 2' column)
        if 'FB% 2' in result.columns:
            result['FB_Reliance'] = result['FB% 2']
            result['FB_Reliance_Risk'] = result['FB_Reliance'] > self.thresholds['fastball_reliance']

        # Fastball velocity
        if 'FBv' in result.columns:
            result['Fastball_Velo'] = result['FBv']

        return result

    def calculate_luck_metrics(
        self,
        relievers: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Calculate luck vs. skill indicators.

        Metrics:
        - ERA - FIP gap (defense/luck)
        - ERA - xERA gap (batted ball luck)
        - BABIP extremes (>0.330 unlucky, <0.260 lucky)
        - LOB% extremes (>80% lucky, <70% unlucky)

        Args:
            relievers: DataFrame with performance stats

        Returns:
            DataFrame with luck metrics added
        """
        result = relievers.copy()

        # ERA - FIP gap (positive = unlucky, negative = lucky)
        result['ERA_FIP_Gap'] = result['ERA'] - result['FIP']

        # ERA - xERA gap (if available)
        if 'xERA_proxy' in result.columns:
            result['ERA_xERA_Gap'] = result['ERA'] - result['xERA_proxy']

        # BABIP luck (league average ~0.295)
        result['BABIP_Luck'] = result['BABIP'] - 0.295

        # LOB% luck (league average ~72%)
        if 'LOB%' in result.columns:
            result['LOB_Luck'] = result['LOB%'] - 0.72

        # Classify luck
        def classify_luck(row):
            era_fip_gap = row.get('ERA_FIP_Gap', 0)
            babip_luck = row.get('BABIP_Luck', 0)

            if era_fip_gap > 0.50 and babip_luck > 0.030:
                return 'Unlucky'
            elif era_fip_gap < -0.50 and babip_luck < -0.030:
                return 'Lucky'
            else:
                return 'Neutral'

        result['Luck_Classification'] = result.apply(classify_luck, axis=1)

        return result

    def calculate_workload_stress(
        self,
        relievers: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Calculate workload stress and fatigue risk.

        Metrics:
        - IP in 2025 (80+ = high workload for RP)
        - Appearances (70+ = high usage)
        - Average IP per appearance (indicates role)
        - Estimated back-to-back frequency (if game-level data available)

        Args:
            relievers: DataFrame with usage stats

        Returns:
            DataFrame with workload metrics added
        """
        result = relievers.copy()

        # Innings pitched risk
        result['IP_Risk'] = result['IP'] >= self.thresholds['workload_risk_ip']

        # Appearance frequency
        result['Appearances'] = result['G']
        result['High_Usage'] = result['G'] >= 70

        # Average IP per appearance (closer = ~1.0, setup = ~1.0, mop-up = ~1.5+)
        result['IP_Per_App'] = result['IP'] / result['G']

        # Estimate role based on IP per appearance and saves
        def estimate_role(row):
            ip_per_app = row.get('IP_Per_App', 1.0)
            saves = row.get('SV', 0)

            if saves >= 20:
                return 'Closer'
            elif ip_per_app >= 1.2 and saves < 5:
                return 'Mop-up'
            else:
                return 'Setup'

        result['Estimated_Role'] = result.apply(estimate_role, axis=1)

        # Workload stress score (0-100)
        def calculate_workload_score(row):
            score = 0

            # IP penalty
            ip = row.get('IP', 0)
            if ip >= 90:
                score += 40
            elif ip >= 80:
                score += 25
            elif ip >= 70:
                score += 15

            # Appearances penalty
            g = row.get('G', 0)
            if g >= 80:
                score += 30
            elif g >= 70:
                score += 20
            elif g >= 65:
                score += 10

            # Age penalty
            age = row.get('Age', 30)
            if age >= 35:
                score += 20
            elif age >= 32:
                score += 10

            return min(score, 100)

        result['Workload_Stress_Score'] = result.apply(calculate_workload_score, axis=1)

        return result

    def calculate_role_mismatch_score(
        self,
        relievers: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Identify relievers in suboptimal roles.

        Signals:
        - Elite K% + low BB% but few saves (setup talent)
        - High-leverage stuff in low-leverage situations (bad team)
        - Reverse platoon specialists underutilized

        Args:
            relievers: DataFrame with performance stats

        Returns:
            DataFrame with role mismatch scores
        """
        result = relievers.copy()

        # Closer talent score (K%, BB%, saves)
        def calculate_closer_talent(row):
            score = 0

            # Elite K rate
            k_rate = row.get('K/9', 0)
            if k_rate >= 12.0:
                score += 40
            elif k_rate >= 10.5:
                score += 25
            elif k_rate >= 9.0:
                score += 15

            # Elite control
            bb_rate = row.get('BB/9', 5.0)
            if bb_rate <= 2.0:
                score += 30
            elif bb_rate <= 2.5:
                score += 20
            elif bb_rate <= 3.0:
                score += 10

            # Stuff quality
            stuff_index = row.get('Stuff_Quality_Index', 0)
            if stuff_index >= 5.0:
                score += 20
            elif stuff_index >= 3.0:
                score += 10

            # FIP
            fip = row.get('FIP', 5.0)
            if fip <= 3.00:
                score += 10
            elif fip <= 3.50:
                score += 5

            return score

        result['Closer_Talent_Score'] = result.apply(calculate_closer_talent, axis=1)

        # Role mismatch: High closer talent but low saves
        def identify_mismatch(row):
            talent = row.get('Closer_Talent_Score', 0)
            saves = row.get('SV', 0)

            if talent >= 60 and saves < 10:
                return 'High'
            elif talent >= 50 and saves < 15:
                return 'Moderate'
            else:
                return 'None'

        result['Role_Mismatch'] = result.apply(identify_mismatch, axis=1)

        return result

    def calculate_true_talent_score(
        self,
        relievers: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Calculate comprehensive true talent score (0-100).

        Combines:
        - Stuff quality (velocity, pitch values)
        - Results quality (FIP, xERA adjusted for context)
        - Sustainability (K%, BB%, arsenal diversity)

        Args:
            relievers: DataFrame with all metrics

        Returns:
            DataFrame with true talent score
        """
        result = relievers.copy()

        def calculate_talent(row):
            score = 0

            # Component 1: Stuff Quality (40 points max)
            # K/9
            k_rate = row.get('K/9', 0)
            if k_rate >= 13.0:
                score += 20
            elif k_rate >= 11.0:
                score += 15
            elif k_rate >= 9.0:
                score += 10
            elif k_rate >= 7.5:
                score += 5

            # Fastball velocity
            fb_velo = row.get('Fastball_Velo', 0)
            if fb_velo >= 97.0:
                score += 10
            elif fb_velo >= 95.0:
                score += 7
            elif fb_velo >= 93.0:
                score += 4

            # Stuff quality index
            stuff_index = row.get('Stuff_Quality_Index', 0)
            if stuff_index >= 8.0:
                score += 10
            elif stuff_index >= 5.0:
                score += 7
            elif stuff_index >= 3.0:
                score += 4

            # Component 2: Results Quality (30 points max)
            # FIP
            fip = row.get('FIP', 6.0)
            if fip <= 2.50:
                score += 15
            elif fip <= 3.00:
                score += 12
            elif fip <= 3.50:
                score += 9
            elif fip <= 4.00:
                score += 6
            elif fip <= 4.50:
                score += 3

            # WAR
            war = row.get('WAR', 0)
            if war >= 2.0:
                score += 15
            elif war >= 1.5:
                score += 12
            elif war >= 1.0:
                score += 9
            elif war >= 0.5:
                score += 6
            elif war >= 0.0:
                score += 3

            # Component 3: Sustainability (30 points max)
            # BB/9 (control)
            bb_rate = row.get('BB/9', 5.0)
            if bb_rate <= 2.0:
                score += 15
            elif bb_rate <= 2.5:
                score += 12
            elif bb_rate <= 3.0:
                score += 9
            elif bb_rate <= 3.5:
                score += 6
            elif bb_rate <= 4.0:
                score += 3

            # Arsenal diversity
            diversity = row.get('Arsenal_Diversity', 1)
            if diversity >= 4:
                score += 10
            elif diversity >= 3:
                score += 7
            elif diversity >= 2:
                score += 4

            # GB% (groundball rate, sustainable)
            gb_pct = row.get('GB%', 0)
            if gb_pct >= 0.50:
                score += 5
            elif gb_pct >= 0.45:
                score += 3

            return min(score, 100)

        result['True_Talent_Score'] = result.apply(calculate_talent, axis=1)

        return result

    def calculate_upside_score(
        self,
        relievers: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Calculate upside potential (0-100).

        Factors:
        - Role optimization potential (setup → closer)
        - Age curve (pre-peak bonus)
        - Arsenal evolution (added pitches)
        - Context improvement potential (bad park → neutral)

        Args:
            relievers: DataFrame with all metrics

        Returns:
            DataFrame with upside score
        """
        result = relievers.copy()

        def calculate_upside(row):
            score = 0

            # Factor 1: Role optimization (40 points max)
            role_mismatch = row.get('Role_Mismatch', 'None')
            if role_mismatch == 'High':
                score += 40
            elif role_mismatch == 'Moderate':
                score += 25

            # Factor 2: Age curve (30 points max)
            age = row.get('Age', 35)
            if age <= 27:
                score += 30  # Pre-peak
            elif age <= 29:
                score += 20  # Peak
            elif age <= 31:
                score += 10  # Early decline
            # 32+ = no bonus

            # Factor 3: Arsenal diversity (20 points max)
            diversity = row.get('Arsenal_Diversity', 1)
            if diversity >= 3 and diversity < 4:
                score += 20  # Could add 4th pitch
            elif diversity == 2:
                score += 15  # Could add 3rd pitch

            # Factor 4: Luck-based upside (10 points max)
            luck = row.get('Luck_Classification', 'Neutral')
            if luck == 'Unlucky':
                score += 10  # Positive regression expected

            return min(score, 100)

        result['Upside_Score'] = result.apply(calculate_upside, axis=1)

        return result

    def project_multi_year_war(
        self,
        relievers: pd.DataFrame,
        years: int = 3
    ) -> pd.DataFrame:
        """
        Project WAR for next N years using aging curves.

        Args:
            relievers: DataFrame with current WAR
            years: Number of years to project

        Returns:
            DataFrame with projected WAR columns
        """
        result = relievers.copy()

        for year in range(1, years + 1):
            col_name = f'Projected_WAR_Year{year}'

            def project_war(row):
                projections = self.aging_analyzer.project_performance(
                    current_performance=row.get('WAR', 0),
                    current_age=row.get('Age', 30),
                    position='RP',
                    years_forward=year,
                    metric_type='WAR'
                )
                # Return the projected value for the specific year
                if projections and len(projections) >= year:
                    return projections[year - 1]['projected_value']
                return 0.0

            result[col_name] = result.apply(project_war, axis=1)

        # Calculate total projected WAR
        war_cols = [f'Projected_WAR_Year{i}' for i in range(1, years + 1)]
        result[f'Total_Projected_WAR_{years}yr'] = result[war_cols].sum(axis=1)

        return result

    def calculate_market_value(
        self,
        relievers: pd.DataFrame,
        years: int = 3
    ) -> pd.DataFrame:
        """
        Calculate market value and value gap.

        Args:
            relievers: DataFrame with projected WAR
            years: Contract length for valuation

        Returns:
            DataFrame with market value calculations
        """
        result = relievers.copy()

        # True value = Projected WAR × $/WAR
        total_war_col = f'Total_Projected_WAR_{years}yr'
        result['True_Value_$M'] = result[total_war_col] * self.dollars_per_war

        # Expected market value (simple model based on saves, age, K%)
        def estimate_market_value(row):
            # Base on closer premium
            saves = row.get('SV', 0)
            war = row.get('WAR', 0)
            age = row.get('Age', 30)

            # Base value
            base_value = war * self.dollars_per_war * years

            # Closer premium (30+ saves = +50%)
            if saves >= 30:
                base_value *= 1.50
            elif saves >= 20:
                base_value *= 1.30
            elif saves >= 10:
                base_value *= 1.15

            # Age discount
            if age >= 35:
                base_value *= 0.80
            elif age >= 32:
                base_value *= 0.90

            return base_value

        result['Expected_Market_Value_$M'] = result.apply(estimate_market_value, axis=1)

        # Value gap (positive = undervalued, negative = overvalued)
        result['Value_Gap_$M'] = result['True_Value_$M'] - result['Expected_Market_Value_$M']

        # Recommended contract structure
        result['Recommended_AAV_$M'] = result['True_Value_$M'] / years
        result['Recommended_Years'] = years

        return result

    def calculate_confidence_score(
        self,
        relievers: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Calculate confidence in projections (0-100).

        Factors:
        - Sample size (IP in 2025)
        - Track record consistency (if multi-year)
        - Expected stats alignment (ERA vs xERA)

        Args:
            relievers: DataFrame with stats

        Returns:
            DataFrame with confidence score
        """
        result = relievers.copy()

        def calculate_confidence(row):
            score = 0

            # Sample size (50 points max)
            ip = row.get('IP', 0)
            if ip >= 60:
                score += 50
            elif ip >= 50:
                score += 40
            elif ip >= 40:
                score += 30
            elif ip >= 30:
                score += 20
            elif ip >= 20:
                score += 10

            # Expected stats alignment (30 points max)
            if 'ERA_FIP_Gap' in row:
                era_fip_gap = abs(row['ERA_FIP_Gap'])
                if era_fip_gap <= 0.30:
                    score += 30  # Tight alignment
                elif era_fip_gap <= 0.50:
                    score += 20
                elif era_fip_gap <= 0.75:
                    score += 10

            # WAR consistency (20 points max)
            war = row.get('WAR', 0)
            if war >= 1.0:
                score += 20  # Proven contributor
            elif war >= 0.5:
                score += 15
            elif war >= 0.0:
                score += 10

            return min(score, 100)

        result['Confidence_Score'] = result.apply(calculate_confidence, axis=1)

        return result

    def run_comprehensive_analysis(
        self,
        fa_list: List[Tuple[str, int, float]],
        season: int = 2025,
        projection_years: int = 3
    ) -> pd.DataFrame:
        """
        Run complete analysis pipeline.

        Args:
            fa_list: List of (name, age, projected_war) for FA relievers
            season: Season year
            projection_years: Years to project forward

        Returns:
            Comprehensive analysis DataFrame
        """
        print("\n" + "="*80)
        print("ELITE RELIEVER FREE AGENT ANALYSIS")
        print("="*80)

        # Step 1: Fetch reliever data
        relievers = self.fetch_reliever_data(season=season)

        # Step 2: Add expected stats
        relievers = self.add_expected_stats(relievers, season=season)

        # Step 3: Calculate arsenal metrics
        print("\nCalculating arsenal metrics...")
        relievers = self.calculate_arsenal_metrics(relievers)

        # Step 4: Calculate luck metrics
        print("Calculating luck vs. skill indicators...")
        relievers = self.calculate_luck_metrics(relievers)

        # Step 5: Calculate workload stress
        print("Analyzing workload stress...")
        relievers = self.calculate_workload_stress(relievers)

        # Step 6: Calculate role mismatch
        print("Identifying role mismatches...")
        relievers = self.calculate_role_mismatch_score(relievers)

        # Step 7: Calculate injury risk
        print("Assessing injury risk...")
        relievers = self.injury_analyzer.calculate_pitcher_injury_risk(relievers)

        # Step 8: Calculate true talent score
        print("Calculating true talent scores...")
        relievers = self.calculate_true_talent_score(relievers)

        # Step 9: Calculate upside score
        print("Calculating upside potential...")
        relievers = self.calculate_upside_score(relievers)

        # Step 10: Project multi-year WAR
        print(f"Projecting {projection_years}-year WAR...")
        relievers = self.project_multi_year_war(relievers, years=projection_years)

        # Step 11: Calculate market value
        print("Calculating market values...")
        relievers = self.calculate_market_value(relievers, years=projection_years)

        # Step 12: Calculate confidence score
        print("Calculating confidence scores...")
        relievers = self.calculate_confidence_score(relievers)

        # Step 13: Match with FA list
        print("\nMatching with free agent list...")
        fa_df = self.load_free_agent_list(fa_list)

        # Merge FA list with analysis
        result = relievers.merge(
            fa_df[['Name', 'Is_FA']],
            on='Name',
            how='left'
        )
        result['Is_FA'] = result['Is_FA'].fillna(False)

        # Filter to FA only for final rankings
        fa_only = result[result['Is_FA'] == True].copy()

        print(f"\nMatched {len(fa_only)} free agent relievers")
        print(f"Total relievers analyzed: {len(result)}")

        return result, fa_only

    def generate_rankings(
        self,
        fa_analysis: pd.DataFrame,
        top_n: int = 20
    ) -> Dict[str, pd.DataFrame]:
        """
        Generate tiered rankings.

        Args:
            fa_analysis: DataFrame with FA analysis
            top_n: Number of top relievers to return

        Returns:
            Dictionary of ranked DataFrames by category
        """
        rankings = {}

        # Overall value ranking (Value Gap × Confidence)
        fa_analysis['Overall_Value_Score'] = (
            fa_analysis['Value_Gap_$M'] *
            (fa_analysis['Confidence_Score'] / 100)
        )

        rankings['Overall_Top_Value'] = fa_analysis.nlargest(
            top_n, 'Overall_Value_Score'
        )[['Name', 'Age', 'WAR', 'ERA', 'FIP', 'K/9', 'BB/9',
           'True_Talent_Score', 'Upside_Score', 'Value_Gap_$M',
           'Confidence_Score', 'Overall_Value_Score',
           'Recommended_AAV_$M', 'Estimated_Role']]

        # Best pure talent (ignoring value)
        rankings['Best_Talent'] = fa_analysis.nlargest(
            top_n, 'True_Talent_Score'
        )[['Name', 'Age', 'WAR', 'ERA', 'FIP', 'K/9', 'BB/9',
           'True_Talent_Score', 'Stuff_Quality_Index', 'Arsenal_Diversity']]

        # Highest upside
        rankings['Highest_Upside'] = fa_analysis.nlargest(
            top_n, 'Upside_Score'
        )[['Name', 'Age', 'WAR', 'Role_Mismatch', 'Upside_Score',
           'Closer_Talent_Score', 'Estimated_Role']]

        # Unlucky bargains (high ERA but good xStats)
        unlucky = fa_analysis[fa_analysis['Luck_Classification'] == 'Unlucky'].copy()
        if len(unlucky) > 0:
            rankings['Unlucky_Bargains'] = unlucky.nlargest(
                min(top_n, len(unlucky)), 'True_Talent_Score'
            )[['Name', 'Age', 'ERA', 'FIP', 'ERA_FIP_Gap', 'BABIP',
               'Luck_Classification', 'True_Talent_Score']]

        # Role mismatch targets
        mismatch = fa_analysis[fa_analysis['Role_Mismatch'] != 'None'].copy()
        if len(mismatch) > 0:
            rankings['Role_Mismatch_Targets'] = mismatch.nlargest(
                min(top_n, len(mismatch)), 'Closer_Talent_Score'
            )[['Name', 'Age', 'K/9', 'BB/9', 'SV', 'Closer_Talent_Score',
               'Role_Mismatch', 'Estimated_Role']]

        # Low injury risk veterans
        low_risk = fa_analysis[
            (fa_analysis['injury_risk_category'] == 'Low') &
            (fa_analysis['Age'] >= 30)
        ].copy()
        if len(low_risk) > 0:
            rankings['Low_Risk_Veterans'] = low_risk.nlargest(
                min(top_n, len(low_risk)), 'True_Talent_Score'
            )[['Name', 'Age', 'WAR', 'True_Talent_Score',
               'injury_risk_category', 'injury_risk_score']]

        return rankings
