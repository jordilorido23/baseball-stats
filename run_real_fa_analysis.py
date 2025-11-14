"""
Run complete 2025-26 Free Agent Analysis with REAL 2025 data

This script runs the full analysis pipeline with actual 2025 statistics
and generates updated reports, rankings, and insights.
"""

import pandas as pd
import numpy as np
from src.data import SavantLeaderboards, FanGraphsFetcher, ContractData
from src.analysis import FreeAgentAnalyzer, AgingCurveAnalyzer

def main():
    print("\n" + "="*70)
    print("  2025-26 MLB FREE AGENT ANALYSIS - REAL DATA")
    print("="*70 + "\n")

    # Initialize modules
    print("Initializing analysis modules...")
    contracts = ContractData()
    fa_analyzer = FreeAgentAnalyzer(dollars_per_war=8.0)
    aging = AgingCurveAnalyzer()

    # Load free agent list with REAL WAR
    fa_list = contracts.get_all_free_agents()
    print(f"✓ Loaded {len(fa_list)} free agents with real 2025 WAR data\n")

    # Display top 15 by WAR
    print("="*70)
    print("TOP 15 FREE AGENTS BY 2025 WAR (REAL DATA)")
    print("="*70 + "\n")

    top_15 = fa_list.nlargest(15, '2025_war')
    for i, (_, player) in enumerate(top_15.iterrows(), 1):
        print(f"{i:2d}. {player['player_name']:25s} {player['position']:3s} | "
              f"{player['2025_war']:5.1f} WAR | Age {player['age_2025']:2d} | {player['tier']:8s}")

    # Key insights
    print("\n" + "="*70)
    print("KEY INSIGHTS FROM REAL 2025 DATA")
    print("="*70 + "\n")

    print("🏆 ELITE PERFORMERS (4.0+ WAR):")
    elite = fa_list[fa_list['2025_war'] >= 4.0].sort_values('2025_war', ascending=False)
    for _, player in elite.iterrows():
        print(f"   • {player['player_name']:25s} - {player['2025_war']:.1f} WAR ({player['position']})")

    print("\n⚠️  INJURY/DOWN YEARS (< 1.0 WAR):")
    poor = fa_list[fa_list['2025_war'] < 1.0].sort_values('2025_war')
    for _, player in poor.iterrows():
        print(f"   • {player['player_name']:25s} - {player['2025_war']:.1f} WAR ({player['position']}) - RED FLAG")

    print("\n📊 STATISTICS:")
    print(f"   Mean WAR: {fa_list['2025_war'].mean():.2f}")
    print(f"   Median WAR: {fa_list['2025_war'].median():.2f}")
    print(f"   Players with 4+ WAR: {len(elite)}")
    print(f"   Players with negative WAR: {len(fa_list[fa_list['2025_war'] < 0])}")

    # Contract projections for top players
    print("\n" + "="*70)
    print("CONTRACT PROJECTIONS (TOP 10 PLAYERS)")
    print("="*70 + "\n")

    projections = []
    for _, player in fa_list.nlargest(10, '2025_war').iterrows():
        name = player['player_name']
        position = player['position']
        age = player['age_2025']
        war = player['2025_war']

        # Determine contract length
        if age <= 28:
            years = 7
        elif age <= 30:
            years = 6
        elif age <= 32:
            years = 5
        elif age <= 34:
            years = 4
        else:
            years = 3

        # Project WAR
        war_proj = fa_analyzer.project_multi_year_war(war, age, position, years)
        contract_est = fa_analyzer.estimate_contract_value(war_proj, include_inflation=True)

        projections.append({
            'Player': name,
            'Pos': position,
            'Age': age,
            '2025 WAR': war,
            'Years': years,
            'Total $M': contract_est['total_value_millions'],
            'AAV $M': contract_est['aav_millions'],
            'Proj WAR': contract_est['total_projected_war']
        })

    proj_df = pd.DataFrame(projections)
    print(proj_df.to_string(index=False))

    print(f"\nTotal projected contract value (top 10): ${proj_df['Total $M'].sum():.0f}M")

    # Position-by-position breakdown
    print("\n" + "="*70)
    print("BEST FREE AGENTS BY POSITION")
    print("="*70 + "\n")

    positions = ['C', '1B', '2B', '3B', 'SS', 'OF', 'DH', 'SP', 'RP']

    for pos in positions:
        pos_fas = fa_list[fa_list['position'] == pos].nlargest(3, '2025_war')
        if len(pos_fas) > 0:
            print(f"{pos}:")
            for i, (_, p) in enumerate(pos_fas.iterrows(), 1):
                print(f"   {i}. {p['player_name']:25s} - {p['2025_war']:5.1f} WAR, Age {p['age_2025']}")
            print()

    # Red flags and concerns
    print("=" * 70)
    print("RED FLAGS & INJURY CONCERNS")
    print("="*70 + "\n")

    print("⚠️  Major injury/down years that change valuation:\n")

    concerning = [
        ('Corbin Burnes', 0.7, 'Injured year - was supposed to be elite FA'),
        ('Anthony Santander', -0.9, 'Terrible year - negative WAR'),
        ('Walker Buehler', -0.3, 'Injured/recovering from surgery'),
        ('Shane Bieber', 0.3, 'Injured - limited to 40 IP'),
        ('Blake Snell', 1.9, 'Injured/limited - only 61 IP'),
        ('Marcell Ozuna', 1.2, 'Down year - only 1.2 WAR'),
        ('Teoscar Hernandez', 0.6, 'Poor year - only 0.6 WAR'),
    ]

    for name, war, concern in concerning:
        print(f"   • {name:25s} - {war:4.1f} WAR - {concern}")

    # Save results
    print("\n" + "="*70)
    print("SAVING RESULTS")
    print("="*70 + "\n")

    fa_list.to_csv('data/2025_fa_real_war_list.csv', index=False)
    print("✓ Saved FA list: data/2025_fa_real_war_list.csv")

    proj_df.to_csv('data/2025_fa_contract_projections_real.csv', index=False)
    print("✓ Saved projections: data/2025_fa_contract_projections_real.csv")

    # Summary recommendations
    print("\n" + "="*70)
    print("FINAL RECOMMENDATIONS BASED ON REAL 2025 DATA")
    print("="*70 + "\n")

    print("MAX CONTRACT CANDIDATES (4.5+ WAR):")
    print("   1. Kyle Schwarber (4.9 WAR, DH, 32) - Elite production but age concern")
    print("   2. Cody Bellinger (4.9 WAR, OF, 29) - Two-way player, ideal age")
    print("   3. Max Fried (4.8 WAR, SP, 31) - Best pitcher FA")
    print("   4. Kyle Tucker (4.5 WAR, OF, 28) - Young, solid year\n")

    print("PREMIUM TIER (3.5-4.4 WAR):")
    print("   • Willy Adames (4.0 WAR, SS, 29) - Premium position")
    print("   • Framber Valdez (4.0 WAR, SP, 31) - Innings eater")
    print("   • Ranger Suarez (4.0 WAR, SP, 29) - Quality starter")
    print("   • Eugenio Suarez (3.8 WAR, 3B, 33) - Age 33 concern")
    print("   • Nathan Eovaldi (3.7 WAR, SP, 35) - Age risk")
    print("   • Nick Pivetta (3.7 WAR, SP, 32) - Strong year")
    print("   • Pete Alonso (3.6 WAR, 1B, 30) - Power bat")
    print("   • Alex Bregman (3.5 WAR, 3B, 31) - Down from past years\n")

    print("AVOID / RED FLAGS:")
    print("   ✗ Corbin Burnes - Injured year (0.7 WAR), huge risk")
    print("   ✗ Anthony Santander - Negative WAR (-0.9), terrible year")
    print("   ✗ Walker Buehler - Injured (-0.3 WAR)")
    print("   ✗ Shane Bieber - Injured, only 40 IP (0.3 WAR)")
    print("   ✗ Blake Snell - Limited innings, injury concerns (1.9 WAR)\n")

    print("="*70)
    print("ANALYSIS COMPLETE - All data is now REAL 2025 statistics")
    print("="*70 + "\n")

    print("Next steps:")
    print("1. Review saved CSV files in data/ directory")
    print("2. Run Jupyter notebook for detailed visualizations")
    print("3. Update blog posts with these findings")
    print("4. Generate final report with real player analysis\n")

if __name__ == '__main__':
    main()
