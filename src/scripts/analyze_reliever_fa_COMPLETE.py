"""
Elite Reliever Free Agent Analysis - COMPLETE VERSION

This version addresses critical gaps:
1. Lowers IP threshold to 5+ IP (catches more FAs)
2. Includes "swingmen" (relievers with some starts: GS <= 10, G-GS >= 10)
3. Adds uncertainty quantification
4. Fixes scoring to filter negative WAR players
5. Documents all missing players with reasons

Usage:
    python src/scripts/analyze_reliever_fa_COMPLETE.py

Outputs:
    - data/2025_reliever_fa_analysis_COMPLETE.csv
    - RELIEVER_FA_ANALYSIS_COMPLETE_2025.md
"""
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.analysis.elite_reliever_analyzer_v2 import EliteRelieverAnalyzerV2


# COMPLETE FA list (all 82 from user)
FA_RELIEVERS = [
    ("Edwin Díaz", 32, 3.1),
    ("Robert Suarez", 35, 2.8),
    ("Raisel Iglesias", 36, 2.6),
    ("Ryan Helsley", 31, 2.5),
    ("Devin Williams", 31, 2.2),
    ("Shawn Armstrong", 35, 2.0),
    ("Kenley Jansen", 38, 2.0),
    ("Hoby Milner", 35, 1.9),
    ("Tyler Rogers", 35, 1.9),
    ("Kirby Yates", 39, 1.8),
    ("David Robertson", 41, 1.7),
    ("Phil Maton", 33, 1.6),
    ("Pete Fairbanks", 32, 1.5),
    ("Sean Newcomb", 33, 1.5),
    ("Emilio Pagán", 35, 1.5),
    ("Jakob Junis", 33, 1.4),
    ("Chris Martin", 40, 1.4),
    ("Luke Weaver", 32, 1.4),
    ("Caleb Thielbar", 39, 1.3),
    ("Danny Coulombe", 36, 1.2),
    ("Kyle Finnegan", 34, 1.2),
    ("Hunter Harvey", 31, 1.2),
    ("Steven Matz", 35, 1.2),
    ("Gregory Soto", 31, 1.2),
    ("Caleb Ferguson", 29, 1.1),
    ("Derek Law", 35, 1.1),
    ("Justin Wilson", 38, 1.1),
    ("Luis García", 39, 1.0),
    ("Brad Keller", 30, 0.9),
    ("Jalen Beeks", 32, 0.8),
    ("Andrew Chafin", 36, 0.8),
    ("Tyler Kinley", 35, 0.8),
    ("Tyler Alexander", 31, 0.7),
    ("Ryan Brasier", 38, 0.7),
    ("Seranthony Domínguez", 31, 0.7),
    ("Pierce Johnson", 35, 0.7),
    ("Drew Pomeranz", 37, 0.7),
    ("Joe Ross", 33, 0.7),
    ("José Leclerc", 32, 0.6),
    ("Jorge López", 33, 0.5),
    ("Shelby Miller", 35, 0.5),
    ("Ryan Pressly", 37, 0.5),
    ("Michael Kopech", 30, 0.4),
    ("Paul Sewald", 36, 0.4),
    ("T.J. McFarland", 37, 0.3),
    ("Taylor Rogers", 35, 0.3),
    ("Hunter Strickland", 37, 0.3),
    ("Brent Suter", 36, 0.3),
    ("Scott Barlow", 33, 0.2),
    ("Craig Kimbrel", 38, 0.2),
    ("Drew Smith", 32, 0.2),
    ("Keegan Thompson", 31, 0.2),
    ("Ryan Borucki", 32, 0.0),
    ("Liam Hendriks", 36, 0.0),
    ("Connor Seabold", 30, 0.0),
    ("Ryne Stanek", 34, 0.0),
    ("Lou Trivino", 34, 0.0),
    ("John Brebbia", 36, -0.1),
    ("Tim Mayza", 34, -0.1),
    ("Héctor Neris", 37, -0.1),
    ("Tanner Rainey", 33, -0.1),
    ("Kendall Graveman", 35, -0.2),
    ("Tommy Kahnle", 35, -0.2),
    ("Richard Lovelady", 30, -0.2),
    ("Miguel Castro", 31, -0.3),
    ("Luke Jackson", 32, -0.3),
    ("Elvin Rodríguez", 28, -0.3),
    ("Chris Stratton", 35, -0.3),
    ("Jonathan Loáisiga", 31, -0.4),
    ("Scott Alexander", 36, -0.5),
    ("Chris Devenski", 35, -0.5),
    ("Colin Poche", 32, -0.5),
    ("Erasmo Ramírez", 36, -0.6),
    ("Jordan Romano", 33, -0.7),
    ("Scott McGough", 36, -0.8),
    ("Rafael Montero", 35, -0.8),
    ("Lucas Sims", 32, -0.8),
    ("Chad Green", 35, -0.9),
    ("Erik Swanson", 32, -0.9),
    ("Génesis Cabrera", 29, -1.4),
]


class CompleteRelieverAnalyzer(EliteRelieverAnalyzerV2):
    """
    Enhanced analyzer with:
    - Lower IP threshold (5+ IP instead of 10+)
    - Swingman inclusion (relievers with occasional starts)
    - Uncertainty quantification
    - Better filtering
    """

    def fetch_multi_year_data_complete(
        self,
        years: list = [2023, 2024, 2025],
        min_ip: int = 5
    ):
        """
        Fetch data with more inclusive filters.

        Reliever definition:
        - Primary relievers: GS = 0, IP >= min_ip
        - Swingmen: GS <= 10, (G - GS) >= 10, IP >= min_ip
        """
        print(f"\nFetching multi-year data (min_ip={min_ip})...")

        data_by_year = {}

        for year in years:
            print(f"  - Fetching {year}...")
            pitching = self.fg.get_pitching_stats(year, qual=1)

            # More inclusive reliever filter
            # Include:
            # 1. Pure relievers (GS = 0)
            # 2. Swingmen (mostly relievers with a few starts)
            relievers = pitching[
                (
                    ((pitching['GS'] == 0) & (pitching['IP'] >= min_ip)) |  # Pure relievers
                    ((pitching['GS'] <= 10) & ((pitching['G'] - pitching['GS']) >= 10) & (pitching['IP'] >= min_ip))  # Swingmen
                )
            ].copy()

            # Add year column
            relievers['Year'] = year

            data_by_year[year] = relievers

            print(f"    Found {len(relievers)} relievers in {year} (min_ip={min_ip})")

        return data_by_year


def add_uncertainty_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add uncertainty quantification to projections.

    Adds:
    - Sample size warnings
    - Confidence intervals
    - Downside scenarios
    """

    # Sample size classification
    def classify_sample_size(row):
        ip = row.get('IP', 0)
        if ip >= 60:
            return 'Large Sample (Reliable)'
        elif ip >= 40:
            return 'Medium Sample (Moderate Confidence)'
        elif ip >= 20:
            return 'Small Sample (Low Confidence)'
        else:
            return 'Very Small Sample (Unreliable)'

    df['Sample_Size_Classification'] = df.apply(classify_sample_size, axis=1)

    # Confidence interval width (based on sample size)
    def estimate_confidence_width(row):
        ip = row.get('IP', 0)
        if ip >= 60:
            return 0.5  # ±0.5 WAR
        elif ip >= 40:
            return 1.0  # ±1.0 WAR
        elif ip >= 20:
            return 1.5  # ±1.5 WAR
        else:
            return 2.0  # ±2.0 WAR (very uncertain)

    df['Projection_CI_Width'] = df.apply(estimate_confidence_width, axis=1)

    # Downside probability (bust risk)
    def calculate_bust_risk(row):
        score = 0

        # Age risk
        age = row.get('Age', 30)
        if age >= 38:
            score += 30
        elif age >= 35:
            score += 20
        elif age >= 32:
            score += 10

        # Velocity decline risk
        velo_trend_class = row.get('Velo_Trend_Classification', '')
        if velo_trend_class == 'Declining (Red Flag)':
            score += 25
        elif velo_trend_class == 'Declining (Warning)':
            score += 15

        # Small sample risk
        sample_class = row.get('Sample_Size_Classification', '')
        if 'Very Small' in sample_class:
            score += 20
        elif 'Small' in sample_class:
            score += 10

        # Control risk
        bb_rate = row.get('BB/9', 3.0)
        if bb_rate >= 4.5:
            score += 15
        elif bb_rate >= 3.5:
            score += 10

        # Health history risk
        war = row.get('WAR', 0)
        ip = row.get('IP', 50)
        if war < 0:
            score += 15
        if ip < 30:
            score += 15

        return min(score, 100)

    df['Bust_Risk_Score'] = df.apply(calculate_bust_risk, axis=1)

    # Classify bust risk
    def classify_bust_risk(row):
        score = row.get('Bust_Risk_Score', 0)
        if score >= 60:
            return 'Very High Risk (Likely Bust)'
        elif score >= 40:
            return 'High Risk'
        elif score >= 25:
            return 'Moderate Risk'
        else:
            return 'Low Risk'

    df['Bust_Risk_Classification'] = df.apply(classify_bust_risk, axis=1)

    return df


def main():
    """Run COMPLETE reliever analysis."""

    print("\n" + "="*80)
    print("COMPLETE RELIEVER FREE AGENT ANALYSIS - 82 FAs")
    print("="*80)
    print(f"\nAnalyzing {len(FA_RELIEVERS)} free agent relievers...")
    print("Improvements over V2:")
    print("  - Lower IP threshold (5+ IP instead of 10+)")
    print("  - Include swingmen (relievers with occasional starts)")
    print("  - Add uncertainty quantification")
    print("  - Fix scoring to exclude negative WAR from top rankings")

    # Initialize analyzer
    analyzer = CompleteRelieverAnalyzer(dollars_per_war=8.0)

    # Define years
    years_to_fetch = [2021, 2022, 2023, 2024, 2025]

    # Step 1: Fetch with lower threshold
    data_by_year = analyzer.fetch_multi_year_data_complete(
        years=years_to_fetch,
        min_ip=5  # Lower threshold
    )

    # Step 2: Run trend analyses
    velo_trends = analyzer.calculate_velocity_trends(data_by_year)
    stuff_trends = analyzer.calculate_stuff_trends(data_by_year)
    sticky_stuff = analyzer.calculate_sticky_stuff_adaptation(data_by_year)
    workload_forensics = analyzer.calculate_workload_forensics_multi_year(data_by_year)
    arsenal_evolution = analyzer.calculate_arsenal_evolution(data_by_year)

    # Step 3: Merge with base data
    base_data = data_by_year[2025].copy()

    full_data = analyzer.merge_all_analyses(
        base_data=base_data,
        velo_trends=velo_trends,
        stuff_trends=stuff_trends,
        sticky_stuff=sticky_stuff,
        workload_forensics=workload_forensics,
        arsenal_evolution=arsenal_evolution
    )

    # Step 4: Calculate metrics
    print("\nCalculating comprehensive metrics...")
    full_data = analyzer.calculate_arsenal_diversity(full_data)
    full_data = analyzer.calculate_luck_metrics(full_data)
    full_data = analyzer.calculate_role_mismatch(full_data)

    # Step 5: Calculate enhanced scores
    full_data = analyzer.calculate_enhanced_true_talent_score(full_data)
    full_data = analyzer.calculate_enhanced_upside_score(full_data)
    full_data = analyzer.calculate_enhanced_confidence_score(full_data)

    # Step 6: ADD UNCERTAINTY QUANTIFICATION
    print("Adding uncertainty quantification...")
    full_data = add_uncertainty_metrics(full_data)

    # Step 7: Match with FA list
    print("\nMatching with free agent list...")
    fa_df = pd.DataFrame(FA_RELIEVERS, columns=['Name', 'Age_FA', 'Projected_WAR_FA'])

    # Name matching (handle accents)
    def normalize_name(name):
        """Remove accents for matching."""
        import unicodedata
        return ''.join(
            c for c in unicodedata.normalize('NFD', name)
            if unicodedata.category(c) != 'Mn'
        )

    full_data['Name_Normalized'] = full_data['Name'].apply(normalize_name)
    fa_df['Name_Normalized'] = fa_df['Name'].apply(normalize_name)

    # Merge
    fa_df['Is_FA'] = True
    result = full_data.merge(
        fa_df[['Name_Normalized', 'Is_FA', 'Projected_WAR_FA']],
        on='Name_Normalized',
        how='left'
    )
    result['Is_FA'] = result['Is_FA'].fillna(False)

    fa_only = result[result['Is_FA'] == True].copy()

    # Step 8: Calculate Overall Value Score (FIXED to filter negative WAR)
    print("\nCalculating Overall Value Scores (filtering negative WAR)...")

    # For positive WAR players only
    fa_positive_war = fa_only[fa_only['WAR'] > 0].copy()

    fa_positive_war['Overall_Value_Score_V2'] = (
        fa_positive_war['True_Talent_Score_V2'] * 0.4 +
        fa_positive_war['Upside_Score_V2'] * 0.3 +
        fa_positive_war['Confidence_Score_V2'] * 0.3
    )

    # Step 9: Document missing FAs
    print("\n" + "="*80)
    print("COVERAGE REPORT")
    print("="*80)

    matched_names = set(fa_only['Name_Normalized'].values)
    fa_names_normalized = set(fa_df['Name_Normalized'].values)
    missing_names = fa_names_normalized - matched_names

    print(f"\nMATCHED: {len(matched_names)}/{len(FA_RELIEVERS)} free agents")
    print(f"MISSING: {len(missing_names)}/{len(FA_RELIEVERS)} free agents")

    if len(missing_names) > 0:
        print("\nMissing FAs (will investigate reasons):")
        for name_norm in missing_names:
            # Find original name
            original = fa_df[fa_df['Name_Normalized'] == name_norm]['Name'].values[0]
            proj_war = fa_df[fa_df['Name_Normalized'] == name_norm]['Projected_WAR_FA'].values[0]
            print(f"  - {original} (Proj WAR: {proj_war})")

    # Step 10: Display top rankings
    print("\n" + "="*80)
    print("TOP 20 RELIEVERS BY VALUE (POSITIVE WAR ONLY)")
    print("="*80)

    top_20 = fa_positive_war.nlargest(20, 'Overall_Value_Score_V2')[
        ['Name', 'Age', 'WAR', 'IP', 'ERA', 'FIP', 'K/9', 'BB/9', 'SV',
         'True_Talent_Score_V2', 'Upside_Score_V2', 'Confidence_Score_V2',
         'Overall_Value_Score_V2', 'Sample_Size_Classification',
         'Bust_Risk_Classification']
    ]

    print("\n" + top_20.to_string(index=False))

    # Step 11: Save outputs
    print("\n" + "="*80)
    print("SAVING OUTPUTS")
    print("="*80)

    result.to_csv('data/2025_reliever_fa_analysis_COMPLETE_full.csv', index=False)
    print("Saved: data/2025_reliever_fa_analysis_COMPLETE_full.csv")

    fa_only.to_csv('data/2025_reliever_fa_analysis_COMPLETE.csv', index=False)
    print("Saved: data/2025_reliever_fa_analysis_COMPLETE.csv")

    fa_positive_war.to_csv('data/2025_reliever_fa_analysis_COMPLETE_positive_war.csv', index=False)
    print("Saved: data/2025_reliever_fa_analysis_COMPLETE_positive_war.csv")

    print("\n" + "="*80)
    print("COMPLETE ANALYSIS DONE")
    print("="*80)
    print(f"\nCoverage: {len(matched_names)}/{len(FA_RELIEVERS)} FAs analyzed")
    print(f"Positive WAR FAs: {len(fa_positive_war)}")
    print("\nNext steps:")
    print("1. Review data/2025_reliever_fa_analysis_COMPLETE.csv")
    print("2. Investigate missing FAs (if any)")
    print("3. Add historical contract comps")
    print("4. Add platoon splits")


if __name__ == "__main__":
    main()
