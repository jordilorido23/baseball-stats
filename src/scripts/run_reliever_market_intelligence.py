"""
Run Elite Reliever Market Intelligence Analysis for 2025-26 FA Class

This script runs the comprehensive market intelligence analysis on the
2025-26 free agent reliever class and generates:
1. Full analysis CSV with 400+ columns
2. Top 20 FA rankings by Market Value Gap
3. Summary report

Usage:
    python -m src.scripts.run_reliever_market_intelligence
"""
import pandas as pd
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.analysis.elite_reliever_market_intelligence import EliteRelieverMarketIntelligence


def load_fa_reliever_list():
    """Load the free agent reliever list."""

    # Read existing FA data
    fa_data_path = project_root / "data" / "2025_reliever_fa_analysis_v2.csv"

    if not fa_data_path.exists():
        print(f"Error: FA data not found at {fa_data_path}")
        print("Please ensure the FA reliever dataset exists.")
        return []

    fa_df = pd.read_csv(fa_data_path)

    # Extract FA list
    fa_list = []

    for _, row in fa_df.iterrows():
        name = row.get('Name', '')
        age = row.get('Age', 30)
        war = row.get('WAR', 0)

        if name:
            fa_list.append((name, age, war))

    print(f"\nLoaded {len(fa_list)} free agent relievers from existing dataset")

    return fa_list


def main():
    """Run the full market intelligence analysis."""

    print("\n" + "="*80)
    print("ELITE RELIEVER MARKET INTELLIGENCE - 2025-26 FA CLASS")
    print("="*80)

    # Step 1: Load FA list
    fa_list = load_fa_reliever_list()

    if not fa_list:
        print("No free agents to analyze. Exiting.")
        return

    # Step 2: Initialize analyzer
    analyzer = EliteRelieverMarketIntelligence(
        dollars_per_war=8.0,
        cache_dir=str(project_root / "data" / "cache")
    )

    # Step 3: Run comprehensive analysis
    try:
        full_analysis, fa_only = analyzer.run_comprehensive_analysis(
            fa_list=fa_list,
            current_year=2025,
            lookback_years=3
        )
    except Exception as e:
        print(f"\nError running analysis: {e}")
        import traceback
        traceback.print_exc()
        return

    # Step 4: Save full analysis
    output_dir = project_root / "data"
    output_dir.mkdir(exist_ok=True)

    full_output_path = output_dir / "2025_reliever_market_intelligence_full.csv"
    full_analysis.to_csv(full_output_path, index=False)
    print(f"\nFull analysis saved to: {full_output_path}")
    print(f"Total columns: {len(full_analysis.columns)}")

    # Step 5: Save FA-only analysis
    fa_output_path = output_dir / "2025_reliever_market_intelligence_fa_only.csv"
    fa_only.to_csv(fa_output_path, index=False)
    print(f"FA-only analysis saved to: {fa_output_path}")

    # Step 6: Generate Top 20 FA Rankings
    print("\n" + "="*80)
    print("TOP 20 FREE AGENT RELIEVERS - BY MARKET VALUE GAP")
    print("="*80)

    # Select columns for rankings
    ranking_cols = [
        'Name', 'Age', 'Team',
        'WAR', 'ERA', 'FIP', 'K/9', 'BB/9', 'SV',
        'FBv', 'Arsenal_Diversity_Count', 'Secondary_Stuff_Class',
        'Velo_Trend_Classification', 'K_Pct_Trend_Classification',
        'Park_Context', 'Workload_Classification_3yr',
        'True_Talent_Score', 'Health_Risk_Score', 'Upside_Score',
        'Confidence_Score', 'Overall_Value_Score',
        'Market_Value_Gap', 'Market_Value_Class',
        'Similar_Comp_Archetype'
    ]

    # Filter to available columns
    available_cols = [col for col in ranking_cols if col in fa_only.columns]

    # Sort by Market Value Gap (descending = best value first)
    top_20 = fa_only.sort_values('Market_Value_Gap', ascending=False).head(20)
    top_20_display = top_20[available_cols].copy()

    # Save top 20
    top_20_path = output_dir / "2025_reliever_fa_top20_value.csv"
    top_20_display.to_csv(top_20_path, index=False)
    print(f"\nTop 20 rankings saved to: {top_20_path}")

    # Print top 10 to console
    print("\nTOP 10 HIDDEN GEMS (Best Market Value Gap):")
    print("-" * 80)

    display_cols_short = ['Name', 'Age', 'WAR', 'K/9', 'BB/9', 'SV',
                          'Overall_Value_Score', 'Market_Value_Gap', 'Market_Value_Class']

    available_short_cols = [col for col in display_cols_short if col in fa_only.columns]

    print(top_20.head(10)[available_short_cols].to_string(index=False))

    # Step 7: Generate summary statistics
    print("\n" + "="*80)
    print("SUMMARY STATISTICS")
    print("="*80)

    if 'Overall_Value_Score' in fa_only.columns:
        print(f"\nOverall Value Score Distribution:")
        print(f"  Mean: {fa_only['Overall_Value_Score'].mean():.1f}")
        print(f"  Median: {fa_only['Overall_Value_Score'].median():.1f}")
        print(f"  Std Dev: {fa_only['Overall_Value_Score'].std():.1f}")

    if 'True_Talent_Score' in fa_only.columns:
        print(f"\nTrue Talent Score Distribution:")
        print(f"  Mean: {fa_only['True_Talent_Score'].mean():.1f}")
        print(f"  Top 25th percentile: {fa_only['True_Talent_Score'].quantile(0.75):.1f}")

    if 'Health_Risk_Score' in fa_only.columns:
        print(f"\nHealth Risk Score Distribution:")
        print(f"  Mean: {fa_only['Health_Risk_Score'].mean():.1f}")
        print(f"  High Risk (>60): {len(fa_only[fa_only['Health_Risk_Score'] > 60])} players")

    if 'Market_Value_Class' in fa_only.columns:
        print(f"\nMarket Value Classification:")
        print(fa_only['Market_Value_Class'].value_counts().to_string())

    if 'Arsenal_Diversity_Class' in fa_only.columns:
        print(f"\nArsenal Diversity:")
        print(fa_only['Arsenal_Diversity_Class'].value_counts().to_string())

    if 'Velo_Trend_Classification' in fa_only.columns:
        print(f"\nVelocity Trends:")
        print(fa_only['Velo_Trend_Classification'].value_counts().to_string())

    print("\n" + "="*80)
    print("ANALYSIS COMPLETE!")
    print("="*80)
    print(f"\nOutput files:")
    print(f"  1. Full Analysis: {full_output_path}")
    print(f"  2. FA Only: {fa_output_path}")
    print(f"  3. Top 20 Rankings: {top_20_path}")
    print("\nNext steps:")
    print("  - Review top 20 hidden gems (best Market Value Gap)")
    print("  - Identify high upside / low health risk targets")
    print("  - Analyze park context and trend patterns")
    print("  - Compare similar comp archetypes")


if __name__ == "__main__":
    main()
