"""
Update 2025-26 Free Agent Analysis with REAL 2025 Data

This script fetches actual 2025 season data from FanGraphs and Baseball Savant,
matches it with the free agent list, and updates the contract_data.py module.

Run this to replace simulated data with real statistics.
"""

import pandas as pd
import sys
from src.data import FanGraphsFetcher, ContractData

def fetch_real_2025_data():
    """Fetch real 2025 batting and pitching data."""
    print("Fetching real 2025 data from FanGraphs...")
    fg = FanGraphsFetcher()

    batting = fg.get_batting_stats(2025, qual=10)
    pitching = fg.get_pitching_stats(2025, qual=10)

    print(f"✓ Retrieved {len(batting)} batters and {len(pitching)} pitchers")
    return batting, pitching

def match_fa_with_real_data(fa_list, batting_df, pitching_df):
    """Match free agents with their actual 2025 stats."""
    matched_data = []

    for _, fa in fa_list.iterrows():
        name = fa['player_name']
        position = fa['position']

        # Split name for matching
        parts = name.split()
        last_name = parts[-1]
        first_name = parts[0] if len(parts) > 1 else ""

        matched = False
        war_value = None
        fg_name = None

        # Match based on position type
        if position in ['SP', 'RP']:
            # Search pitchers
            for _, pitcher in pitching_df.iterrows():
                if last_name.lower() in pitcher['Name'].lower():
                    # Additional check with first name if available
                    if not first_name or first_name[0].lower() == pitcher['Name'][0].lower():
                        war_value = pitcher['WAR']
                        fg_name = pitcher['Name']
                        matched = True
                        break
        else:
            # Search batters
            for _, batter in batting_df.iterrows():
                if last_name.lower() in batter['Name'].lower():
                    if not first_name or first_name[0].lower() == batter['Name'][0].lower():
                        war_value = batter['WAR']
                        fg_name = batter['Name']
                        matched = True
                        break

        matched_data.append({
            'fa_name': name,
            'position': position,
            'age': fa['age_2025'],
            'matched': matched,
            'fg_name': fg_name,
            'real_war': war_value if matched else fa['2025_war'],  # Keep original if no match
            'original_war': fa['2025_war']
        })

    return pd.DataFrame(matched_data)

def main():
    print("\n=== Updating 2025-26 Free Agent Analysis with REAL Data ===\n")

    # Load current FA list
    contracts = ContractData()
    fa_list = contracts.get_all_free_agents()
    print(f"Free agents in database: {len(fa_list)}")

    # Fetch real data
    batting, pitching = fetch_real_2025_data()

    # Match FAs with real data
    print("\nMatching free agents with 2025 statistics...")
    matched = match_fa_with_real_data(fa_list, batting, pitching)

    # Display results
    print("\n=== MATCHED FREE AGENTS (sorted by real WAR) ===\n")
    matched_sorted = matched.sort_values('real_war', ascending=False)

    for _, row in matched_sorted.iterrows():
        status = "✓" if row['matched'] else "✗"
        fg_info = f"({row['fg_name']})" if row['matched'] else "(NO MATCH)"
        war_change = row['real_war'] - row['original_war']
        war_indicator = f"({war_change:+.1f})" if row['matched'] else ""

        print(f"{status} {row['fa_name']:25s} {row['position']:3s} | "
              f"Real: {row['real_war']:5.1f} WAR {war_indicator:8s} | "
              f"Orig: {row['original_war']:5.1f} | {fg_info}")

    # Summary statistics
    print(f"\n=== SUMMARY ===")
    print(f"Total FAs: {len(matched)}")
    print(f"Matched: {matched['matched'].sum()} ({matched['matched'].sum()/len(matched)*100:.1f}%)")
    print(f"Not matched: {(~matched['matched']).sum()}")

    print(f"\nWAR Statistics (matched players only):")
    matched_only = matched[matched['matched']]
    print(f"  Mean WAR: {matched_only['real_war'].mean():.2f}")
    print(f"  Median WAR: {matched_only['real_war'].median():.2f}")
    print(f"  Top player: {matched_only.nlargest(1, 'real_war').iloc[0]['fa_name']} "
          f"({matched_only['real_war'].max():.1f} WAR)")

    # Save results
    matched.to_csv('data/fa_real_war_matched.csv', index=False)
    print(f"\n✓ Saved match results to data/fa_real_war_matched.csv")

    # Print code to update contract_data.py
    print("\n=== UPDATE contract_data.py ===")
    print("\nReplace the '2025_war' list in src/data/contract_data.py with these REAL values:\n")
    print("'2025_war': [")

    # Print in same order as current FA list
    for _, fa in fa_list.iterrows():
        match_row = matched[matched['fa_name'] == fa['player_name']].iloc[0]
        war = match_row['real_war']
        print(f"    {war:.1f},  # {fa['player_name']}")

    print("]\n")

    print("Then re-run the Jupyter notebook to regenerate analysis with real data!")

if __name__ == '__main__':
    main()
