"""
Unit Tests for Advanced Reliever Market Intelligence System

Tests each analyzer module with real data from Hunter Harvey (2024 season).

Run this BEFORE attempting the full 76-pitcher analysis to catch bugs early.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import pandas as pd
import numpy as np
import pybaseball as pyb
from analysis.pitch_physics_analyzer import PitchPhysicsAnalyzer
from analysis.arsenal_synergy_analyzer import ArsenalSynergyAnalyzer
from analysis.biomechanics_analyzer import BiomechanicsAnalyzer
from analysis.diamond_detector import analyze_reliever_complete

# Suppress warnings
import warnings
warnings.filterwarnings('ignore')


class TestResults:
    """Track test results."""
    def __init__(self):
        self.tests_run = 0
        self.tests_passed = 0
        self.tests_failed = 0
        self.failures = []

    def record_pass(self, test_name):
        self.tests_run += 1
        self.tests_passed += 1
        print(f"  ✅ {test_name}")

    def record_fail(self, test_name, error):
        self.tests_run += 1
        self.tests_failed += 1
        self.failures.append((test_name, error))
        print(f"  ❌ {test_name}: {error}")

    def summary(self):
        print(f"\n{'='*80}")
        print("TEST SUMMARY")
        print(f"{'='*80}")
        print(f"Total Tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed} ({self.tests_passed/self.tests_run*100:.1f}%)")
        print(f"Failed: {self.tests_failed} ({self.tests_failed/self.tests_run*100:.1f}%)")

        if self.failures:
            print(f"\n{'='*80}")
            print("FAILED TESTS - DETAILS")
            print(f"{'='*80}")
            for test_name, error in self.failures:
                print(f"\n{test_name}:")
                print(f"  Error: {error}")


def test_1_1_fetch_statcast_data(results: TestResults):
    """Test 1.1: Can we fetch Statcast data with required fields?"""
    print("\n" + "="*80)
    print("TEST 1.1: Fetch Statcast Data")
    print("="*80)

    try:
        # Clay Holmes: 605280 (2024 Yankees closer - known to have data)
        player_id = 605280
        start_date = '2024-03-01'
        end_date = '2024-10-01'

        print(f"\nFetching data for Clay Holmes (player {player_id}) ({start_date} to {end_date})...")
        data = pyb.statcast_pitcher(start_date, end_date, player_id)

        if data.empty:
            results.record_fail("Fetch Statcast Data", "No data returned (empty DataFrame)")
            return None

        print(f"  Loaded {len(data)} pitches")
        results.record_pass("Fetch Statcast Data - Got pitches")

        # Check for required fields
        required_fields = {
            'vx0': 'Velocity X component at release',
            'vy0': 'Velocity Y component at release',
            'vz0': 'Velocity Z component at release',
            'ax': 'Acceleration X component',
            'ay': 'Acceleration Y component',
            'az': 'Acceleration Z component',
            'pfx_x': 'Horizontal movement',
            'pfx_z': 'Vertical movement',
            'release_spin_rate': 'Spin rate',
            'spin_axis': 'Spin axis',
            'release_speed': 'Release velocity',
            'release_extension': 'Extension',
            'plate_x': 'Horizontal location',
            'plate_z': 'Vertical location',
            'pitch_type': 'Pitch type',
            'release_pos_x': 'Release position X',
            'release_pos_z': 'Release position Z',
        }

        missing_fields = []
        for field, description in required_fields.items():
            if field not in data.columns:
                missing_fields.append(f"{field} ({description})")
                results.record_fail(f"Required field: {field}", "Field missing from Statcast data")
            else:
                # Check if field has any non-null values
                non_null_count = data[field].notna().sum()
                if non_null_count > 0:
                    results.record_pass(f"Required field: {field} ({non_null_count} values)")
                else:
                    results.record_fail(f"Required field: {field}", "Field exists but all values are null")

        if missing_fields:
            print(f"\n  ⚠️  Missing fields: {', '.join(missing_fields)}")

        print(f"\n  Available columns ({len(data.columns)}):")
        print(f"    {', '.join(data.columns[:20])}...")

        return data

    except Exception as e:
        results.record_fail("Fetch Statcast Data", str(e))
        return None


def test_1_2_vaa_calculation(data: pd.DataFrame, results: TestResults):
    """Test 1.2: VAA Calculation"""
    print("\n" + "="*80)
    print("TEST 1.2: VAA Calculation")
    print("="*80)

    if data is None or data.empty:
        results.record_fail("VAA Calculation", "No data available")
        return

    try:
        analyzer = PitchPhysicsAnalyzer()

        # Test on first 10 pitches
        print(f"\nTesting VAA calculation on {min(10, len(data))} pitches...")

        vaa_values = []
        for idx in range(min(10, len(data))):
            test_pitch = data.iloc[idx]
            vaa = analyzer.calculate_vaa(test_pitch)
            vaa_values.append(vaa)

            if pd.notna(vaa):
                print(f"  Pitch {idx+1}: VAA = {vaa:.2f}° (pitch_type: {test_pitch.get('pitch_type', 'Unknown')})")
            else:
                print(f"  Pitch {idx+1}: VAA = NaN (missing data)")

        # Check results
        valid_vaa = [v for v in vaa_values if pd.notna(v)]

        if len(valid_vaa) == 0:
            results.record_fail("VAA Calculation", "All VAA values are NaN - calculation not working")
            return

        results.record_pass(f"VAA Calculation - {len(valid_vaa)}/{len(vaa_values)} valid values")

        # Check if VAA values are reasonable (-2° to -8° typical for fastballs)
        avg_vaa = np.mean(valid_vaa)
        print(f"\n  Average VAA: {avg_vaa:.2f}°")

        if -10 < avg_vaa < 0:
            results.record_pass(f"VAA values reasonable (avg: {avg_vaa:.2f}°)")
        else:
            results.record_fail("VAA values reasonable", f"Average VAA {avg_vaa:.2f}° outside expected range (-10 to 0)")

    except Exception as e:
        results.record_fail("VAA Calculation", str(e))


def test_1_3_ssw_detection(data: pd.DataFrame, results: TestResults):
    """Test 1.3: SSW Detection"""
    print("\n" + "="*80)
    print("TEST 1.3: SSW (Seam-Shifted Wake) Detection")
    print("="*80)

    if data is None or data.empty:
        results.record_fail("SSW Detection", "No data available")
        return

    try:
        analyzer = PitchPhysicsAnalyzer()

        print(f"\nTesting SSW calculation on {min(10, len(data))} pitches...")

        ssw_values = []
        for idx in range(min(10, len(data))):
            test_pitch = data.iloc[idx]
            ssw_x, ssw_z, ssw_total = analyzer.calculate_ssw_effect(test_pitch)
            ssw_values.append(ssw_total)

            if pd.notna(ssw_total):
                print(f"  Pitch {idx+1}: SSW = {ssw_total:.2f} inches (x: {ssw_x:.2f}, z: {ssw_z:.2f})")
            else:
                print(f"  Pitch {idx+1}: SSW = NaN (missing data)")

        # Check results
        valid_ssw = [v for v in ssw_values if pd.notna(v)]

        if len(valid_ssw) == 0:
            results.record_fail("SSW Detection", "All SSW values are NaN - calculation not working")
            return

        results.record_pass(f"SSW Detection - {len(valid_ssw)}/{len(ssw_values)} valid values")

        # Check if SSW values are reasonable (0-10 inches typical)
        avg_ssw = np.mean(valid_ssw)
        print(f"\n  Average SSW: {avg_ssw:.2f} inches")

        if 0 <= avg_ssw <= 15:
            results.record_pass(f"SSW values reasonable (avg: {avg_ssw:.2f} inches)")
        else:
            results.record_fail("SSW values reasonable", f"Average SSW {avg_ssw:.2f} inches outside expected range (0-15)")

    except Exception as e:
        results.record_fail("SSW Detection", str(e))


def test_1_4_full_physics_analysis(results: TestResults):
    """Test 1.4: Full Physics Analysis"""
    print("\n" + "="*80)
    print("TEST 1.4: Full Physics Analysis")
    print("="*80)

    try:
        analyzer = PitchPhysicsAnalyzer()

        player_id = 605280  # Clay Holmes
        start_date = '2024-03-01'
        end_date = '2024-10-01'

        print(f"\nRunning complete physics analysis for Clay Holmes (player {player_id})...")
        physics_results = analyzer.analyze_pitcher(player_id, start_date, end_date)

        if not physics_results:
            results.record_fail("Full Physics Analysis", "No results returned")
            return None

        results.record_pass("Full Physics Analysis - Completed without errors")

        # Check for expected keys
        expected_keys = ['VAA_FB_avg', 'SSW_Movement_FB', 'Tunneling_Score', 'VAA_Zone_Mismatch_Score']

        print(f"\n  Results:")
        for key in expected_keys:
            if key in physics_results:
                value = physics_results[key]
                print(f"    {key}: {value}")
                results.record_pass(f"Physics metric present: {key}")
            else:
                print(f"    {key}: MISSING")
                results.record_fail(f"Physics metric present: {key}", "Key not found in results")

        return physics_results

    except Exception as e:
        results.record_fail("Full Physics Analysis", str(e))
        return None


def test_1_5_arsenal_synergy(data: pd.DataFrame, results: TestResults):
    """Test 1.5: Arsenal Synergy Analysis"""
    print("\n" + "="*80)
    print("TEST 1.5: Arsenal Synergy Analysis")
    print("="*80)

    if data is None or data.empty:
        results.record_fail("Arsenal Synergy", "No data available")
        return None

    try:
        analyzer = ArsenalSynergyAnalyzer()

        print(f"\nAnalyzing arsenal for Clay Holmes...")
        arsenal_results = analyzer.analyze_pitcher_arsenal(data, 'Hunter Harvey')

        if not arsenal_results:
            results.record_fail("Arsenal Synergy", "No results returned")
            return None

        results.record_pass("Arsenal Synergy - Completed without errors")

        # Check for expected keys
        expected_keys = [
            'Has_Gyro_Sweeper_Combo',
            'Arsenal_Completeness',
            'Effective_Velocity_Composite',
            'Cognitive_Load_Score',
            'Nash_Equilibrium_Score'
        ]

        print(f"\n  Results:")
        for key in expected_keys:
            if key in arsenal_results:
                value = arsenal_results[key]
                print(f"    {key}: {value}")
                results.record_pass(f"Arsenal metric present: {key}")
            else:
                print(f"    {key}: MISSING")
                results.record_fail(f"Arsenal metric present: {key}", "Key not found in results")

        return arsenal_results

    except Exception as e:
        results.record_fail("Arsenal Synergy", str(e))
        return None


def test_1_6_biomechanics(data: pd.DataFrame, results: TestResults):
    """Test 1.6: Biomechanics Analysis"""
    print("\n" + "="*80)
    print("TEST 1.6: Biomechanics Analysis")
    print("="*80)

    if data is None or data.empty:
        results.record_fail("Biomechanics", "No data available")
        return None

    try:
        analyzer = BiomechanicsAnalyzer()

        print(f"\nAnalyzing biomechanics for Clay Holmes...")
        biomech_results = analyzer.analyze_pitcher_biomechanics(data, 'Hunter Harvey')

        if not biomech_results:
            results.record_fail("Biomechanics", "No results returned")
            return None

        results.record_pass("Biomechanics - Completed without errors")

        # Check for expected keys
        expected_keys = [
            'Release_Point_SD',
            'Release_Strategy_Classification',
            'Fatigue_Units_Total',
            'FU_Risk_Score',
            'Extension_ft',
            'Durability_Score'
        ]

        print(f"\n  Results:")
        for key in expected_keys:
            if key in biomech_results:
                value = biomech_results[key]
                print(f"    {key}: {value}")
                results.record_pass(f"Biomechanics metric present: {key}")
            else:
                print(f"    {key}: MISSING")
                results.record_fail(f"Biomechanics metric present: {key}", "Key not found in results")

        return biomech_results

    except Exception as e:
        results.record_fail("Biomechanics", str(e))
        return None


def test_1_7_diamond_score(physics_results, arsenal_results, biomech_results, results: TestResults):
    """Test 1.7: Diamond Score Calculation"""
    print("\n" + "="*80)
    print("TEST 1.7: Diamond Score Calculation")
    print("="*80)

    if not all([physics_results, arsenal_results, biomech_results]):
        results.record_fail("Diamond Score", "Missing required inputs")
        return None

    try:
        print(f"\nCalculating Diamond Score...")

        # Mock traditional stats
        traditional_stats = {
            'player_name': 'Clay Holmes',
            'player_id': 605280,
            'Saves': 0,
            'K_pct': 25.0,
            'Whiff_pct': 30.0,
            'Age': 29,
            'Projected_AAV': 4.0,
            'Appearances': 50,
            'Stuff_plus': 110,
            'Location_plus': 105,
            'gmLI': 1.1,
        }

        complete = analyze_reliever_complete(
            physics_data=physics_results,
            arsenal_data=arsenal_results,
            biomech_data=biomech_results,
            traditional_data=traditional_stats
        )

        if not complete:
            results.record_fail("Diamond Score", "No results returned")
            return None

        results.record_pass("Diamond Score - Completed without errors")

        # Check for expected keys
        expected_keys = ['Diamond_Score', 'Value_Score', 'Bust_Risk_Score', 'Role_Mismatch_Score']

        print(f"\n  Results:")
        for key in expected_keys:
            if key in complete:
                value = complete[key]
                print(f"    {key}: {value:.1f}/100")
                results.record_pass(f"Diamond metric present: {key}")

                # Check if values are reasonable (0-100 range)
                if 0 <= value <= 100:
                    results.record_pass(f"Diamond metric in range: {key}")
                else:
                    results.record_fail(f"Diamond metric in range: {key}", f"Value {value} outside 0-100 range")
            else:
                print(f"    {key}: MISSING")
                results.record_fail(f"Diamond metric present: {key}", "Key not found in results")

        return complete

    except Exception as e:
        results.record_fail("Diamond Score", str(e))
        return None


def main():
    """Run all unit tests."""
    print("\n" + "="*80)
    print("ADVANCED RELIEVER ANALYSIS - UNIT TESTS")
    print("Testing with Clay Holmes (2024 season - Yankees closer)")
    print("="*80)

    results = TestResults()

    # Test 1.1: Fetch Statcast data
    data = test_1_1_fetch_statcast_data(results)

    if data is None:
        print("\n❌ CRITICAL FAILURE: Cannot fetch Statcast data. Cannot proceed with further tests.")
        results.summary()
        return

    # Test 1.2: VAA calculation
    test_1_2_vaa_calculation(data, results)

    # Test 1.3: SSW detection
    test_1_3_ssw_detection(data, results)

    # Test 1.4: Full physics analysis
    physics_results = test_1_4_full_physics_analysis(results)

    # Test 1.5: Arsenal synergy
    arsenal_results = test_1_5_arsenal_synergy(data, results)

    # Test 1.6: Biomechanics
    biomech_results = test_1_6_biomechanics(data, results)

    # Test 1.7: Diamond score
    diamond_results = test_1_7_diamond_score(physics_results, arsenal_results, biomech_results, results)

    # Summary
    results.summary()

    # Recommendation
    print(f"\n{'='*80}")
    print("RECOMMENDATION")
    print(f"{'='*80}")

    if results.tests_passed / results.tests_run >= 0.8:
        print("✅ PROCEED TO PHASE 2 (Integration Tests)")
        print("   Most tests passed. Code is ready for multi-pitcher testing.")
    elif results.tests_passed / results.tests_run >= 0.5:
        print("⚠️  FIX BUGS BEFORE PHASE 2")
        print("   Some tests failed. Review failures and fix before proceeding.")
    else:
        print("❌ DO NOT PROCEED")
        print("   Too many failures. Code needs significant debugging.")


if __name__ == '__main__':
    main()
