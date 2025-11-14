"""
Test multi-year reliever analysis.

This script tests the V2 analyzer with multi-year trend capabilities.
"""
from src.analysis.elite_reliever_analyzer_v2 import EliteRelieverAnalyzerV2

# Sample FA list (just a few for testing)
FA_RELIEVERS_SAMPLE = [
    ("Edwin Díaz", 32, 3.1),
    ("Robert Suarez", 35, 2.8),
    ("Raisel Iglesias", 36, 2.6),
    ("Ryan Helsley", 31, 2.5),
    ("Devin Williams", 31, 2.2),
    ("Hunter Harvey", 31, 1.2),
    ("Gregory Soto", 31, 1.2),
]

def main():
    """Test V2 analyzer."""

    print("="*80)
    print("TESTING MULTI-YEAR RELIEVER ANALYSIS")
    print("="*80)

    # Initialize V2 analyzer
    analyzer = EliteRelieverAnalyzerV2(dollars_per_war=8.0)

    # Test multi-year data fetching
    print("\n### TEST 1: Fetch Multi-Year Data ###")
    data_by_year = analyzer.fetch_multi_year_data(
        years=[2023, 2024, 2025],
        min_ip=10
    )

    for year, df in data_by_year.items():
        print(f"\n{year}: {len(df)} relievers")
        print(f"  Sample: {df['Name'].head(5).tolist()}")

    # Test velocity trends
    print("\n### TEST 2: Calculate Velocity Trends ###")
    velo_trends = analyzer.calculate_velocity_trends(data_by_year)
    print(f"\nVelocity trends calculated for {len(velo_trends)} pitchers")

    # Show examples
    declining = velo_trends[
        velo_trends['Velo_Trend_Classification'] == 'Declining (Red Flag)'
    ].head(5)

    if len(declining) > 0:
        print("\nExample: Declining Velocity (Red Flag)")
        print(declining[['Name', 'Current_FBv', 'Velo_Trend_3yr_mph',
                        'Velo_Trend_Classification']].to_string(index=False))

    improving = velo_trends[
        velo_trends['Velo_Trend_Classification'] == 'Improving'
    ].head(5)

    if len(improving) > 0:
        print("\nExample: Improving Velocity")
        print(improving[['Name', 'Current_FBv', 'Velo_Trend_3yr_mph',
                        'Velo_Trend_Classification']].to_string(index=False))

    # Test stuff trends
    print("\n### TEST 3: Calculate K% and BB% Trends ###")
    stuff_trends = analyzer.calculate_stuff_trends(data_by_year)
    print(f"\nStuff trends calculated for {len(stuff_trends)} pitchers")

    # Show examples
    k_declining = stuff_trends[
        stuff_trends['K_Pct_Trend_Classification'] == 'Declining (Stuff Loss)'
    ].head(5)

    if len(k_declining) > 0:
        print("\nExample: K% Declining (Stuff Loss)")
        print(k_declining[['Name', 'Current_K_Pct', 'K_Pct_Trend_3yr',
                          'K_Pct_Trend_Classification']].to_string(index=False))

    # Test sticky stuff adaptation
    print("\n### TEST 4: Sticky Stuff Adaptation ###")
    sticky_stuff = analyzer.calculate_sticky_stuff_adaptation(data_by_year)
    print(f"\nSticky stuff analysis for {len(sticky_stuff)} pitchers")

    adapted = sticky_stuff[
        sticky_stuff['Sticky_Stuff_Adaptation'] == 'Adapted Successfully'
    ].head(5)

    if len(adapted) > 0:
        print("\nExample: Adapted Successfully")
        print(adapted[['Name', 'K_Pct_Drop_2021_2022', 'K_Pct_Recovery_2022_Latest',
                      'Sticky_Stuff_Adaptation']].to_string(index=False))

    # Test workload forensics
    print("\n### TEST 5: Workload Forensics (3-year) ###")
    workload = analyzer.calculate_workload_forensics_multi_year(data_by_year)
    print(f"\nWorkload analysis for {len(workload)} pitchers")

    extreme_workload = workload[
        workload['Workload_Classification_3yr'] == 'Extreme Workload'
    ].head(5)

    if len(extreme_workload) > 0:
        print("\nExample: Extreme Workload (Fatigue Risk)")
        print(extreme_workload[['Name', 'Cumulative_IP_3yr', 'Cumulative_G_3yr',
                               'Workload_Classification_3yr']].to_string(index=False))

    # Test arsenal evolution
    print("\n### TEST 6: Arsenal Evolution ###")
    arsenal = analyzer.calculate_arsenal_evolution(data_by_year)
    print(f"\nArsenal evolution for {len(arsenal)} pitchers")

    added_pitches = arsenal[arsenal['Pitches_Added'].apply(len) > 0].head(5)

    if len(added_pitches) > 0:
        print("\nExample: Added New Pitches")
        print(added_pitches[['Name', 'Pitches_Added', 'Arsenal_Evolution_Score']].to_string(index=False))

    print("\n" + "="*80)
    print("MULTI-YEAR ANALYSIS TEST COMPLETE")
    print("="*80)


if __name__ == "__main__":
    main()
