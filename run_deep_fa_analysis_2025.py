"""
Master script to run complete 2025-26 Free Agent Deep Analysis.

This script orchestrates all three deep analyses:
1. Injury Risk Analysis (biomechanical signals)
2. Plate Discipline Sustainability (sustainable skills vs luck)
3. Organizational Context Effects (causal org lift)

Created: November 13, 2025
Author: Baseball Analytics Portfolio
"""
import sys
import pandas as pd
import numpy as np
from pathlib import Path

# Add src to path
sys.path.append('.')

# Import data fetchers
from src.data import FreeAgent2025DataFetcher

# Import deep analysis modules
from src.analysis import (
    InjuryRiskAnalyzer,
    DisciplineSustainabilityAnalyzer,
    OrganizationalEffectsAnalyzer
)

import warnings
warnings.filterwarnings('ignore')

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', 100)
pd.set_option('display.width', 200)


def main():
    """Run complete 2025-26 FA deep analysis."""
    print("\n" + "=" * 100)
    print("2025-26 MLB FREE AGENT DEEP ANALYSIS")
    print("REAL DATA - NO SIMULATIONS")
    print("=" * 100)

    # ==========================================================================
    # STEP 1: FETCH ALL DATA
    # ==========================================================================
    print("\n" + "=" * 100)
    print("STEP 1: FETCHING REAL 2025 DATA")
    print("=" * 100)

    fetcher = FreeAgent2025DataFetcher()

    # Fetch 2025 data
    fa_data_2025 = fetcher.fetch_all_2025_data()

    # Fetch historical data for trends
    batting_hist, pitching_hist = fetcher.fetch_historical_data_for_trends([2023, 2024])

    # Add trends to FA data
    fa_data_complete = fetcher.get_fa_with_trends(fa_data_2025, batting_hist, pitching_hist)

    # Export complete dataset
    fetcher.export_complete_dataset(fa_data_complete, 'data/2025_fa_complete_real_data.csv')

    print(f"\n✓ Complete FA dataset ready: {len(fa_data_complete)} players")

    # ==========================================================================
    # STEP 2: INJURY RISK ANALYSIS
    # ==========================================================================
    print("\n" + "=" * 100)
    print("STEP 2: INJURY RISK ANALYSIS")
    print("=" * 100)

    injury_analyzer = InjuryRiskAnalyzer()

    # Separate batters and pitchers
    batters = fa_data_complete[~fa_data_complete['position'].isin(['SP', 'RP'])].copy()
    pitchers = fa_data_complete[fa_data_complete['position'].isin(['SP', 'RP'])].copy()

    print(f"\nAnalyzing injury risk for {len(batters)} batters and {len(pitchers)} pitchers...")

    # Calculate injury risk for batters
    if len(batters) > 0:
        batters_with_risk = injury_analyzer.calculate_batter_injury_risk(batters)
        batters_with_risk = injury_analyzer.calculate_injury_adjusted_war(batters_with_risk)

        print("\n=== Top 10 Batters by Injury Risk (Highest Risk) ===")
        high_risk_batters = batters_with_risk.nlargest(10, 'injury_risk_score')[[
            'player_name', 'position', 'age_2025', '2025_war',
            'injury_risk_score', 'injury_risk_category', 'injury_risk_factors'
        ]]
        print(high_risk_batters.to_string(index=False))

    # Calculate injury risk for pitchers
    if len(pitchers) > 0:
        pitchers_with_risk = injury_analyzer.calculate_pitcher_injury_risk(pitchers)
        pitchers_with_risk = injury_analyzer.calculate_injury_adjusted_war(pitchers_with_risk)

        print("\n=== Top 10 Pitchers by Injury Risk (Highest Risk) ===")
        high_risk_pitchers = pitchers_with_risk.nlargest(10, 'injury_risk_score')[[
            'player_name', 'position', 'age_2025', '2025_war',
            'injury_risk_score', 'injury_risk_category', 'injury_risk_factors'
        ]]
        print(high_risk_pitchers.to_string(index=False))

    # Combine
    fa_with_injury_risk = pd.concat([batters_with_risk, pitchers_with_risk], ignore_index=True)

    # Identify hidden injury risks
    hidden_risks = injury_analyzer.identify_hidden_injury_risks(fa_with_injury_risk, min_war=3.0)
    print(f"\n=== Hidden Injury Risks (Good 2025 WAR but High Risk Signals) ===")
    print(f"Found {len(hidden_risks)} players with concerning injury signals:")
    if len(hidden_risks) > 0:
        print(hidden_risks.to_string(index=False))

    # Export
    fa_with_injury_risk.to_csv('data/2025_fa_with_injury_risk.csv', index=False)
    print("\n✓ Injury risk analysis complete")

    # ==========================================================================
    # STEP 3: PLATE DISCIPLINE SUSTAINABILITY ANALYSIS
    # ==========================================================================
    print("\n" + "=" * 100)
    print("STEP 3: PLATE DISCIPLINE SUSTAINABILITY ANALYSIS")
    print("=" * 100)

    discipline_analyzer = DisciplineSustainabilityAnalyzer()

    # Analyze batters only
    if len(batters_with_risk) > 0:
        print(f"\nAnalyzing plate discipline for {len(batters_with_risk)} batters...")

        batters_with_disc = discipline_analyzer.calculate_discipline_scores(batters_with_risk)
        batters_with_disc = discipline_analyzer.compare_discipline_vs_power(batters_with_disc)
        batters_with_disc = discipline_analyzer.identify_discipline_trends(
            batters_with_disc,
            batting_hist
        )

        print("\n=== Player Archetypes (Discipline vs Power) ===")
        print(batters_with_disc['player_archetype'].value_counts())

        # Safe bets
        safe_bets = discipline_analyzer.identify_safe_bets(batters_with_disc, min_discipline_score=70)
        print(f"\n=== Safe Bets (Elite Discipline + Stable/Improving Trends) ===")
        print(f"Found {len(safe_bets)} safe bet candidates:")
        if len(safe_bets) > 0:
            print(safe_bets.head(10).to_string(index=False))

        # Risky bets
        risky_bets = discipline_analyzer.identify_risky_bets(batters_with_disc, max_discipline_score=50)
        print(f"\n=== Risky Bets (Poor Discipline Despite Good Results) ===")
        print(f"Found {len(risky_bets)} risky bet candidates:")
        if len(risky_bets) > 0:
            print(risky_bets.head(10).to_string(index=False))

        # Merge batters with discipline back
        batters_final = batters_with_disc
    else:
        batters_final = batters_with_risk

    # Combine batters and pitchers
    fa_with_all_analysis = pd.concat([batters_final, pitchers_with_risk], ignore_index=True)

    # Export
    fa_with_all_analysis.to_csv('data/2025_fa_with_discipline_analysis.csv', index=False)
    print("\n✓ Discipline sustainability analysis complete")

    # ==========================================================================
    # STEP 4: ORGANIZATIONAL CONTEXT EFFECTS ANALYSIS
    # ==========================================================================
    print("\n" + "=" * 100)
    print("STEP 4: ORGANIZATIONAL CONTEXT EFFECTS ANALYSIS")
    print("=" * 100)

    org_analyzer = OrganizationalEffectsAnalyzer()

    # Classify by organization
    fa_with_org = org_analyzer.classify_fa_organizations(fa_with_all_analysis)

    # Calculate org adjustments
    fa_with_org = org_analyzer.calculate_org_adjustment_factors(fa_with_org)

    print("\n=== Free Agents by Organization Tier ===")
    print(fa_with_org['org_tier'].value_counts())

    print("\n=== Organization Tier Summary ===")
    org_summary = org_analyzer.generate_org_tier_summary(fa_with_org)
    print(org_summary)

    # Org-boosted players (may regress)
    org_boosted = org_analyzer.identify_org_boosted_players(fa_with_org, min_war=3.0)
    print(f"\n=== Org-Boosted Players (May Regress) ===")
    print(f"Found {len(org_boosted)} elite org players with regression risk:")
    if len(org_boosted) > 0:
        print(org_boosted.to_string(index=False))

    # Hidden talent (may improve)
    hidden_talent = org_analyzer.identify_hidden_talent(fa_with_org, min_war=1.5)
    print(f"\n=== Hidden Talent (May Improve with Better Org) ===")
    print(f"Found {len(hidden_talent)} poor org players with upside:")
    if len(hidden_talent) > 0:
        print(hidden_talent.to_string(index=False))

    # Market inefficiencies
    overvalued, undervalued = org_analyzer.identify_market_inefficiencies(fa_with_org)
    print(f"\n=== Market Inefficiencies ===")
    print(f"Overvalued (org-boosted): {len(overvalued)} players")
    if len(overvalued) > 0:
        print(overvalued.head(10).to_string(index=False))

    print(f"\nUndervalued (org-suppressed): {len(undervalued)} players")
    if len(undervalued) > 0:
        print(undervalued.head(10).to_string(index=False))

    # Export
    fa_with_org.to_csv('data/2025_fa_with_org_analysis.csv', index=False)
    print("\n✓ Organizational context analysis complete")

    # ==========================================================================
    # STEP 5: INTEGRATED RANKING
    # ==========================================================================
    print("\n" + "=" * 100)
    print("STEP 5: INTEGRATED RANKING (ALL ANALYSES COMBINED)")
    print("=" * 100)

    # Calculate integrated value score
    # Combines: 2025 WAR + injury risk + discipline + org context
    fa_final = fa_with_org.copy()

    # Integrated score formula:
    # Base = 2025 WAR
    # Injury adjustment = multiply by (1 - injury_risk_discount)
    # Discipline bonus = add discipline_sustainability_score / 20 (max +5 WAR)
    # Org adjustment = apply org_adjustment_factor

    fa_final['injury_adjusted_war'] = fa_final['injury_adjusted_war'].fillna(fa_final['2025_war'])
    fa_final['org_adjusted_war'] = fa_final['org_adjusted_war'].fillna(fa_final['2025_war'])

    # For batters: add discipline component
    fa_final['discipline_bonus'] = 0.0
    batters_mask = ~fa_final['position'].isin(['SP', 'RP'])
    fa_final.loc[batters_mask, 'discipline_bonus'] = (
        fa_final.loc[batters_mask, 'discipline_sustainability_score'].fillna(50) / 20
    )

    # Integrated WAR = injury_adjusted * (1 + org_adjustment) + discipline_bonus
    fa_final['integrated_war_projection'] = (
        fa_final['injury_adjusted_war'] *
        (1 + fa_final['org_adjustment_factor'].fillna(0)) +
        fa_final['discipline_bonus']
    )

    # Rank by integrated projection
    fa_final_ranked = fa_final.sort_values('integrated_war_projection', ascending=False)

    print("\n=== Top 25 Free Agents by Integrated Projection ===")
    print("(Accounting for injury risk + discipline + org context)")

    top_25_cols = [
        'player_name', 'position', 'age_2025',
        '2025_war', 'integrated_war_projection',
        'injury_risk_category', 'org_tier',
        'player_archetype'
    ]

    top_25 = fa_final_ranked.head(25)[top_25_cols]
    print(top_25.to_string(index=False))

    # Export final rankings
    fa_final_ranked.to_csv('data/2025_fa_final_integrated_rankings.csv', index=False)
    print("\n✓ Final integrated rankings exported")

    # ==========================================================================
    # STEP 6: SUMMARY INSIGHTS
    # ==========================================================================
    print("\n" + "=" * 100)
    print("SUMMARY: KEY INSIGHTS FROM DEEP ANALYSIS")
    print("=" * 100)

    print("\n### INJURY RISK INSIGHTS ###")
    print(f"- High/Very High injury risk: {len(fa_final[fa_final['injury_risk_category'].isin(['High', 'Very High'])])} players")
    print(f"- Low injury risk: {len(fa_final[fa_final['injury_risk_category'] == 'Low'])} players")
    print(f"- Players with hidden injury risks (good WAR but concerning signals): {len(hidden_risks)}")

    print("\n### DISCIPLINE SUSTAINABILITY INSIGHTS ###")
    if 'player_archetype' in fa_final.columns:
        print(f"- Unicorns (elite disc + power): {len(fa_final[fa_final['player_archetype'].str.contains('Unicorn', na=False)])}")
        print(f"- Risky Sluggers (poor disc + power): {len(fa_final[fa_final['player_archetype'].str.contains('Risky', na=False)])}")
        print(f"- Safe bets (elite discipline): {len(safe_bets)}")
        print(f"- Risky bets (poor discipline): {len(risky_bets)}")

    print("\n### ORGANIZATIONAL CONTEXT INSIGHTS ###")
    print(f"- From Elite orgs (regression risk): {len(fa_final[fa_final['org_tier'] == 'Elite'])}")
    print(f"- From Poor orgs (hidden talent): {len(fa_final[fa_final['org_tier'] == 'Poor'])}")
    print(f"- Market overvalued (org-boosted): {len(overvalued)}")
    print(f"- Market undervalued (org-suppressed): {len(undervalued)}")

    print("\n### BIGGEST MOVERS ###")
    print("\nPlayers whose value changed MOST from surface stats to integrated projection:")
    fa_final['value_change'] = fa_final['integrated_war_projection'] - fa_final['2025_war']
    biggest_gainers = fa_final.nlargest(5, 'value_change')[['player_name', '2025_war', 'integrated_war_projection', 'value_change']]
    biggest_losers = fa_final.nsmallest(5, 'value_change')[['player_name', '2025_war', 'integrated_war_projection', 'value_change']]

    print("\nBiggest Gainers (Hidden Value):")
    print(biggest_gainers.to_string(index=False))

    print("\nBiggest Losers (Overvalued):")
    print(biggest_losers.to_string(index=False))

    print("\n" + "=" * 100)
    print("ANALYSIS COMPLETE!")
    print("=" * 100)
    print("\nOutputs saved to:")
    print("  - data/2025_fa_complete_real_data.csv")
    print("  - data/2025_fa_with_injury_risk.csv")
    print("  - data/2025_fa_with_discipline_analysis.csv")
    print("  - data/2025_fa_with_org_analysis.csv")
    print("  - data/2025_fa_final_integrated_rankings.csv")
    print("\nNext steps:")
    print("  1. Run notebooks/05_free_agent_analysis_2025.ipynb for visualizations")
    print("  2. Update 2025_FREE_AGENT_ANALYSIS_REPORT.md with insights")
    print("  3. Create blog post highlighting differentiated findings")


if __name__ == '__main__':
    main()
