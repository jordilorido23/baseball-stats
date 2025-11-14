"""
Phase 2: Integration Tests - Advanced Reliever Market Intelligence

Tests the complete system on 5 diverse pitcher profiles to validate:
1. System handles different pitcher types (sinker, cutter, changeup, power)
2. Metrics differentiate between pitchers (not all the same scores)
3. Edge cases handled gracefully (aging veterans, low sample sizes)

Run time: ~10-15 minutes (5 pitchers × ~2-3 min each)
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import pandas as pd
import time
from analyze_reliever_market_intelligence import RelieverMarketIntelligence

# Suppress warnings
import warnings
warnings.filterwarnings('ignore')


# 5 diverse pitcher profiles for testing
TEST_PITCHERS = [
    {
        'player_name': 'Clay Holmes',
        'player_id': 605280,  # Sinker/Slider, Yankees closer
        'Projected_AAV': 9.0,
        'Age': 31,
        'Expected_Profile': 'Sinker specialist, high groundball rate'
    },
    {
        'player_name': 'Kenley Jansen',
        'player_id': 445276,  # Cutter specialist, aging vet
        'Projected_AAV': 10.0,
        'Age': 37,
        'Expected_Profile': 'Aging cutter specialist, velocity decline'
    },
    {
        'player_name': 'Devin Williams',
        'player_id': 642207,  # Changeup specialist ("Airbender")
        'Projected_AAV': 12.0,
        'Age': 30,
        'Expected_Profile': 'Elite changeup ("Airbender"), unique arsenal'
    },
    {
        'player_name': 'Emmanuel Clase',
        'player_id': 661403,  # Elite cutter, high velocity
        'Projected_AAV': 15.0,
        'Age': 27,
        'Expected_Profile': 'Elite cutter, 100+ mph, top closer'
    },
    {
        'player_name': 'Robert Suarez',
        'player_id': 663158,  # Power pitcher, high K%
        'Projected_AAV': 8.0,
        'Age': 34,
        'Expected_Profile': 'Power arm, high strikeout rate'
    },
]


def print_section_header(text):
    """Print formatted section header."""
    print(f"\n{'='*80}")
    print(text)
    print(f"{'='*80}")


def main():
    """Run Phase 2 integration tests."""
    print_section_header("PHASE 2: INTEGRATION TESTS - ADVANCED RELIEVER ANALYSIS")
    print(f"\nTesting {len(TEST_PITCHERS)} diverse pitcher profiles...")
    print(f"Expected runtime: ~10-15 minutes\n")

    # Initialize analyzer
    print("Initializing analyzer (season=2024)...")
    analyzer = RelieverMarketIntelligence(season=2024)
    print("✓ Analyzer initialized\n")

    # Convert to DataFrame
    test_df = pd.DataFrame(TEST_PITCHERS)

    # Track results
    start_time = time.time()
    successful = 0
    failed = 0
    failed_pitchers = []

    # Analyze each pitcher
    results = []

    for idx, pitcher in test_df.iterrows():
        print_section_header(f"PITCHER {idx+1}/5: {pitcher['player_name']}")
        print(f"Expected Profile: {pitcher['Expected_Profile']}")
        print(f"Age: {pitcher['Age']}, Projected AAV: ${pitcher['Projected_AAV']}M\n")

        pitcher_start = time.time()

        try:
            result = analyzer.analyze_pitcher(
                pitcher['player_id'],
                pitcher['player_name'],
                pitcher['Projected_AAV'],
                pitcher['Age']
            )

            if result:
                results.append(result)
                successful += 1
                elapsed = time.time() - pitcher_start
                print(f"\n✅ SUCCESS - Completed in {elapsed:.1f}s")
            else:
                failed += 1
                failed_pitchers.append(pitcher['player_name'])
                print(f"\n❌ FAILED - No results returned")

        except Exception as e:
            failed += 1
            failed_pitchers.append(pitcher['player_name'])
            print(f"\n❌ FAILED - Error: {e}")

        # Rate limiting
        time.sleep(2)

    # Convert results to DataFrame
    if results:
        results_df = pd.DataFrame(results)

        # Display summary
        print_section_header("INTEGRATION TEST RESULTS")

        print(f"\n📊 Success Rate: {successful}/{len(TEST_PITCHERS)} ({successful/len(TEST_PITCHERS)*100:.1f}%)")

        if failed_pitchers:
            print(f"❌ Failed Pitchers: {', '.join(failed_pitchers)}")

        elapsed_total = time.time() - start_time
        print(f"⏱️  Total Time: {elapsed_total/60:.1f} minutes ({elapsed_total/len(TEST_PITCHERS):.1f}s per pitcher)")

        # Key Metrics Comparison
        print_section_header("KEY METRICS COMPARISON")

        key_columns = [
            'player_name',
            'Diamond_Score',
            'Value_Score',
            'Arsenal_Completeness',
            'Cognitive_Load_Score',
            'Release_Strategy_Classification',
            'Durability_Score',
            'Bust_Risk_Score'
        ]

        # Filter to available columns
        available_cols = [col for col in key_columns if col in results_df.columns]

        if available_cols:
            comparison = results_df[available_cols].copy()

            # Round numeric columns
            numeric_cols = comparison.select_dtypes(include='number').columns
            comparison[numeric_cols] = comparison[numeric_cols].round(1)

            print("\n" + comparison.to_string(index=False))
        else:
            print("⚠️  No key metrics available for comparison")

        # Physics Metrics
        print_section_header("PHYSICS METRICS")

        physics_cols = [
            'player_name',
            'VAA_FB_avg',
            'SSW_Movement_FB',
            'Tunneling_Score',
            'VAA_Zone_Mismatch_Score'
        ]

        available_physics = [col for col in physics_cols if col in results_df.columns]

        if available_physics:
            physics_comparison = results_df[available_physics].copy()
            numeric_cols = physics_comparison.select_dtypes(include='number').columns
            physics_comparison[numeric_cols] = physics_comparison[numeric_cols].round(2)
            print("\n" + physics_comparison.to_string(index=False))
        else:
            print("⚠️  No physics metrics available")

        # Arsenal Insights
        print_section_header("ARSENAL INSIGHTS")

        arsenal_cols = [
            'player_name',
            'Has_Gyro_Sweeper_Combo',
            'Arsenal_Completeness',
            'Effective_Velocity_Composite',
            'Nash_Equilibrium_Score'
        ]

        available_arsenal = [col for col in arsenal_cols if col in results_df.columns]

        if available_arsenal:
            arsenal_comparison = results_df[available_arsenal].copy()
            numeric_cols = arsenal_comparison.select_dtypes(include='number').columns
            arsenal_comparison[numeric_cols] = arsenal_comparison[numeric_cols].round(1)
            print("\n" + arsenal_comparison.to_string(index=False))
        else:
            print("⚠️  No arsenal metrics available")

        # Biomechanics Insights
        print_section_header("BIOMECHANICS INSIGHTS")

        biomech_cols = [
            'player_name',
            'Release_Point_SD',
            'Release_Strategy_Classification',
            'Fatigue_Units_Total',
            'FU_Risk_Score',
            'Extension_ft'
        ]

        available_biomech = [col for col in biomech_cols if col in results_df.columns]

        if available_biomech:
            biomech_comparison = results_df[available_biomech].copy()
            numeric_cols = biomech_comparison.select_dtypes(include='number').columns
            biomech_comparison[numeric_cols] = biomech_comparison[numeric_cols].round(2)
            print("\n" + biomech_comparison.to_string(index=False))
        else:
            print("⚠️  No biomechanics metrics available")

        # Validation Checks
        print_section_header("VALIDATION CHECKS")

        print("\n1. Diamond Scores Differentiate?")
        if 'Diamond_Score' in results_df.columns:
            scores = results_df['Diamond_Score'].dropna()
            if len(scores) > 0:
                score_range = scores.max() - scores.min()
                print(f"   Range: {score_range:.1f} points (min: {scores.min():.1f}, max: {scores.max():.1f})")
                if score_range > 10:
                    print(f"   ✅ GOOD - Scores vary enough to differentiate pitchers")
                else:
                    print(f"   ⚠️  WARNING - Scores too similar (all within {score_range:.1f} points)")
            else:
                print(f"   ❌ No Diamond Scores calculated")
        else:
            print(f"   ❌ Diamond_Score column missing")

        print("\n2. Arsenal Completeness Varies?")
        if 'Arsenal_Completeness' in results_df.columns:
            completeness = results_df['Arsenal_Completeness'].dropna()
            if len(completeness) > 0:
                comp_range = completeness.max() - completeness.min()
                print(f"   Range: {comp_range:.1f} points (min: {completeness.min():.1f}, max: {completeness.max():.1f})")
                if comp_range > 15:
                    print(f"   ✅ GOOD - Arsenal diversity varies significantly")
                else:
                    print(f"   ⚠️  WARNING - Arsenal scores too similar")
            else:
                print(f"   ❌ No Arsenal Completeness calculated")
        else:
            print(f"   ❌ Arsenal_Completeness column missing")

        print("\n3. Release Strategies Differ?")
        if 'Release_Strategy_Classification' in results_df.columns:
            strategies = results_df['Release_Strategy_Classification'].value_counts()
            print(f"   Strategies detected: {len(strategies)}")
            for strategy, count in strategies.items():
                print(f"     - {strategy}: {count} pitchers")
            if len(strategies) > 1:
                print(f"   ✅ GOOD - Multiple strategies detected")
            else:
                print(f"   ⚠️  WARNING - All pitchers classified the same")
        else:
            print(f"   ❌ Release_Strategy_Classification column missing")

        print("\n4. Elite Reliever Ranked Highly?")
        # Emmanuel Clase should rank highly (elite closer)
        if 'Diamond_Score' in results_df.columns and 'player_name' in results_df.columns:
            clase_score = results_df[results_df['player_name'] == 'Emmanuel Clase']['Diamond_Score'].values
            if len(clase_score) > 0:
                clase_percentile = (results_df['Diamond_Score'] < clase_score[0]).sum() / len(results_df) * 100
                print(f"   Emmanuel Clase Diamond Score: {clase_score[0]:.1f}/100 ({clase_percentile:.0f}th percentile)")
                if clase_percentile >= 60:
                    print(f"   ✅ GOOD - Elite reliever scores highly")
                else:
                    print(f"   ⚠️  WARNING - Elite reliever not scoring as expected")
            else:
                print(f"   ⚠️  Emmanuel Clase not in results")
        else:
            print(f"   ❌ Cannot validate elite reliever ranking")

        # Save results
        output_file = 'data/phase2_integration_test_results.csv'
        results_df.to_csv(output_file, index=False)
        print_section_header("OUTPUT FILES")
        print(f"\n✓ Saved results to: {output_file}")
        print(f"  Columns: {len(results_df.columns)}")
        print(f"  Pitchers: {len(results_df)}")

        # Final Recommendation
        print_section_header("PHASE 2 RECOMMENDATION")

        if successful >= 4:
            print("\n✅ PROCEED TO PHASE 3 (Validation & Bug Fixes)")
            print("   System handles diverse pitcher profiles successfully.")
            print("   Ready for validation checks and targeted bug fixes.")
        elif successful >= 3:
            print("\n⚠️  PROCEED WITH CAUTION TO PHASE 3")
            print("   Some issues detected. Review failures before full run.")
        else:
            print("\n❌ DO NOT PROCEED")
            print("   Too many failures. System needs significant debugging.")

    else:
        print_section_header("CRITICAL FAILURE")
        print("\n❌ No successful analyses. Cannot proceed to Phase 3.")
        print("   Review error logs and debug before continuing.")


if __name__ == '__main__':
    main()
