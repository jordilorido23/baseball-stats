"""
Analyze Contract Structures for 2025-26 Free Agent Class.

This script demonstrates how different contract structures affect real value:
- NPV of deferred money (Ohtani-style contracts)
- Opt-out clause valuations (Monte Carlo simulation)
- Performance bonus optimization
- Side-by-side comparisons

Created: November 13, 2025
Author: Baseball Analytics Portfolio
"""
import pandas as pd
import numpy as np
from src.analysis import ContractStructureOptimizer, ContractStructure
from src.data import ContractData

# Silence warnings
import warnings
warnings.filterwarnings('ignore')


def main():
    print("\n" + "=" * 100)
    print("2025-26 MLB FREE AGENT CONTRACT STRUCTURE OPTIMIZATION")
    print("Going Beyond $/WAR: NPV, Opt-Outs, and Deferred Money Analysis")
    print("=" * 100)

    # Initialize
    optimizer = ContractStructureOptimizer(discount_rate=0.05)  # 5% discount rate
    contracts = ContractData()
    fa_list = contracts.get_all_free_agents()

    # ====================================================================
    # PART 1: OHTANI-STYLE DEFERRED CONTRACT ANALYSIS
    # ====================================================================
    print("\n" + "=" * 100)
    print("PART 1: THE OHTANI EFFECT - Deferred Money NPV Analysis")
    print("=" * 100)

    print("\n📊 Shohei Ohtani's Actual Contract:")
    print("   Stated Value: $700M over 10 years")
    print("   Structure: $2M/year salary, $68M/year deferred (97% deferred)")
    print("   Deferrals: Paid 2034-2043 (after contract ends)")

    ohtani_contract, ohtani_npv = optimizer.generate_ohtani_style_contract(
        total_value=700,
        years=10,
        deferred_pct=0.97,
        deferral_years=10
    )

    print(f"\n   NPV Analysis (5% discount rate):")
    print(f"   - Real Cost to Dodgers: ${ohtani_npv['npv']:.1f}M")
    print(f"   - Discount from Stated: ${ohtani_npv['discount_from_stated']:.1f}M ({ohtani_npv['discount_pct']:.1f}%)")
    print(f"   - CBT (Luxury Tax) AAV: ${ohtani_npv['cbt_aav']:.1f}M")
    print(f"   - CBT Savings vs Stated: ${ohtani_npv['cbt_savings_per_year']:.1f}M per year")

    print(f"\n💡 INSIGHT: Dodgers save ~${ohtani_npv['discount_from_stated']:.0f}M in present value")
    print(f"   This allows them to spend that money NOW on other players!")

    # ====================================================================
    # PART 2: TOP FREE AGENT CONTRACT STRUCTURE COMPARISONS
    # ====================================================================
    print("\n" + "=" * 100)
    print("PART 2: CONTRACT STRUCTURE OPTIMIZATION FOR TOP 2025-26 FAs")
    print("=" * 100)

    # Define top free agents to analyze
    top_fas = [
        {'name': 'Kyle Tucker', 'war': 8.7, 'age': 29, 'position': 'RF'},
        {'name': 'Kyle Schwarber', 'war': 8.3, 'age': 33, 'position': 'DH'},
        {'name': 'Dylan Cease', 'war': 8.1, 'age': 30, 'position': 'SP'},
        {'name': 'Alex Bregman', 'war': 7.7, 'age': 32, 'position': '3B'},
        {'name': 'Cody Bellinger', 'war': 7.0, 'age': 30, 'position': 'CF'},
        {'name': 'Pete Alonso', 'war': 5.6, 'age': 31, 'position': '1B'},
    ]

    all_comparisons = []

    for fa in top_fas:
        print(f"\n{'=' * 100}")
        print(f"📋 {fa['name']}: {fa['age']} years old, {fa['position']}, {fa['war']:.1f} WAR")
        print(f"{'=' * 100}")

        # Determine reasonable contract range based on WAR and age
        if fa['war'] >= 8.0 and fa['age'] <= 30:
            base_years = 8
            base_aav = 38.0
        elif fa['war'] >= 7.0 and fa['age'] <= 31:
            base_years = 7
            base_aav = 32.0
        elif fa['war'] >= 7.0:
            base_years = 6
            base_aav = 30.0
        else:
            base_years = 5
            base_aav = 24.0

        base_value = base_aav * base_years

        # Define 4 contract structures
        structures = [
            # Structure A: Traditional straight deal
            (
                "Traditional",
                ContractStructure(
                    total_value=base_value,
                    years=base_years,
                    aav=base_aav,
                    deferred_pct=0.0
                )
            ),

            # Structure B: Opt-outs (player-friendly)
            (
                "With Opt-Outs",
                ContractStructure(
                    total_value=base_value * 1.1,  # 10% premium for opt-outs
                    years=base_years + 2,  # Extend years
                    aav=base_aav * 1.05,
                    deferred_pct=0.0,
                    opt_outs=[3, 5] if base_years >= 6 else [3]  # Opt out after year 3, 5
                )
            ),

            # Structure C: Heavy deferrals (team-friendly)
            (
                "50% Deferred",
                ContractStructure(
                    total_value=base_value * 1.15,  # 15% premium to accept deferrals
                    years=base_years,
                    aav=base_aav * 1.15,
                    deferred_pct=0.50,
                    deferral_years=base_years  # Pay over same period after contract
                )
            ),

            # Structure D: Incentive-heavy (risk-sharing)
            (
                "Incentive-Loaded",
                ContractStructure(
                    total_value=base_value * 0.85,  # Lower guarantee
                    years=base_years,
                    aav=base_aav * 0.85,
                    deferred_pct=0.0,
                    incentives_total=base_value * 0.30  # 30% in performance bonuses
                )
            )
        ]

        # Compare structures
        comparison = optimizer.compare_contract_structures(
            player_name=fa['name'],
            structures=structures,
            current_war=fa['war'],
            age=fa['age'],
            position=fa['position']
        )

        print(f"\n{'Structure':<20} {'Years':<6} {'Stated $M':<12} {'NPV $M':<10} "
              f"{'CBT AAV $M':<12} {'Opt-Out %':<10} {'Team Risk':<10}")
        print("-" * 100)

        for _, row in comparison.iterrows():
            print(f"{row['structure_name']:<20} "
                  f"{row['years']:<6} "
                  f"{row['stated_value']:<12.1f} "
                  f"{row['npv']:<10.1f} "
                  f"{row['cbt_aav']:<12.1f} "
                  f"{row['opt_out_probability']*100:<10.1f} "
                  f"{row['team_risk_score']:<10.1f}")

        all_comparisons.append(comparison)

        # Add analysis
        best_for_team = comparison.nlargest(1, 'cbt_savings')['structure_name'].values[0]
        best_for_player = comparison.nsmallest(1, 'team_risk_score')['structure_name'].values[0]

        print(f"\n💡 RECOMMENDATION:")
        print(f"   - Best for TEAM: {best_for_team} (max CBT savings)")
        print(f"   - Best for PLAYER: {best_for_player} (lowest team control risk)")

    # ====================================================================
    # PART 3: PERFORMANCE BONUS OPTIMIZATION
    # ====================================================================
    print("\n" + "=" * 100)
    print("PART 3: PERFORMANCE BONUS OPTIMIZATION")
    print("=" * 100)

    print("\n🎯 Optimizing PA/IP Thresholds for Bonus Structures\n")

    # Example: Kyle Tucker (batter)
    print("KYLE TUCKER (Batter - Expected 650 PA)")
    print("-" * 60)
    tucker_bonuses = optimizer.optimize_performance_bonuses(
        position='RF',
        expected_pa_or_ip=650,
        pa_or_ip_std=80,
        bonus_pool=20.0,  # $20M in bonuses
        is_pitcher=False
    )

    print(f"Total Bonus Pool: ${tucker_bonuses['total_bonus_pool']:.1f}M")
    print(f"Expected Payout: ${tucker_bonuses['expected_payout']:.1f}M")
    print(f"Team Savings (Expected): ${tucker_bonuses['team_savings_expected']:.1f}M\n")

    print(f"{'Tier':<6} {'PA Threshold':<15} {'Bonus $M':<12} {'Probability':<12} {'Expected Value $M'}")
    print("-" * 60)
    for tier in tucker_bonuses['bonus_structure']:
        print(f"{tier['tier']:<6} "
              f"{tier['PA_threshold']:<15} "
              f"{tier['bonus_earned']:<12.2f} "
              f"{tier['probability']:<12.1%} "
              f"{tier['expected_value']:<12.2f}")

    # Example: Dylan Cease (pitcher)
    print("\n\nDYLAN CEASE (Pitcher - Expected 180 IP)")
    print("-" * 60)
    cease_bonuses = optimizer.optimize_performance_bonuses(
        position='SP',
        expected_pa_or_ip=180,
        pa_or_ip_std=25,
        bonus_pool=15.0,  # $15M in bonuses
        is_pitcher=True
    )

    print(f"Total Bonus Pool: ${cease_bonuses['total_bonus_pool']:.1f}M")
    print(f"Expected Payout: ${cease_bonuses['expected_payout']:.1f}M")
    print(f"Team Savings (Expected): ${cease_bonuses['team_savings_expected']:.1f}M\n")

    print(f"{'Tier':<6} {'IP Threshold':<15} {'Bonus $M':<12} {'Probability':<12} {'Expected Value $M'}")
    print("-" * 60)
    for tier in cease_bonuses['bonus_structure']:
        print(f"{tier['tier']:<6} "
              f"{tier['IP_threshold']:<15} "
              f"{tier['bonus_earned']:<12.2f} "
              f"{tier['probability']:<12.1%} "
              f"{tier['expected_value']:<12.2f}")

    # ====================================================================
    # PART 4: REAL-WORLD EXAMPLES
    # ====================================================================
    print("\n" + "=" * 100)
    print("PART 4: REAL-WORLD CONTRACT STRUCTURE EXAMPLES")
    print("=" * 100)

    examples = [
        {
            'player': 'Shohei Ohtani',
            'stated': 700,
            'years': 10,
            'deferred_pct': 0.97,
            'deferral_years': 10
        },
        {
            'player': 'Mookie Betts (hypothetical)',
            'stated': 365,
            'years': 12,
            'deferred_pct': 0.30,
            'deferral_years': 10
        },
        {
            'player': 'Standard Max Contract',
            'stated': 300,
            'years': 10,
            'deferred_pct': 0.0,
            'deferral_years': 0
        }
    ]

    print(f"\n{'Player':<30} {'Stated Value':<15} {'NPV (5%)':<15} {'Savings':<15} {'CBT AAV':<15}")
    print("-" * 100)

    for ex in examples:
        contract, npv = optimizer.generate_ohtani_style_contract(
            total_value=ex['stated'],
            years=ex['years'],
            deferred_pct=ex['deferred_pct'],
            deferral_years=ex['deferral_years']
        )
        print(f"{ex['player']:<30} "
              f"${npv['stated_value']:.0f}M{'':<10} "
              f"${npv['npv']:.0f}M{'':<10} "
              f"${npv['discount_from_stated']:.0f}M{'':<10} "
              f"${npv['cbt_aav']:.1f}M")

    # ====================================================================
    # SUMMARY
    # ====================================================================
    print("\n" + "=" * 100)
    print("💡 KEY TAKEAWAYS")
    print("=" * 100)

    print("""
1. DEFERRED MONEY SAVES REAL DOLLARS
   - Ohtani's $700M costs Dodgers ~$460M in present value
   - Teams can reinvest ~$240M savings into other players NOW
   - CBT savings of ~$24M/year creates roster flexibility

2. OPT-OUTS CREATE UNCERTAINTY
   - 30-50% probability elite players opt out after Year 3-5
   - Teams lose 2-4 expected years of control
   - Must pay premium (~10-15%) to include opt-outs

3. PERFORMANCE BONUSES ALIGN INCENTIVES
   - Optimal thresholds: Achievable but not guaranteed
   - Teams save 20-40% of bonus pool in expectation
   - Players get upside for elite performance

4. STRUCTURE MATTERS AS MUCH AS TOTAL VALUE
   - Same player, 4 different structures = $30-80M NPV difference
   - CBT optimization can create $50M+ in roster flexibility
   - Risk allocation (opt-outs, deferrals) changes true value

BOTTOM LINE: Don't just look at $/WAR. Model the structure.
""")

    # Save results
    print("\n" + "=" * 100)
    print("SAVING RESULTS")
    print("=" * 100)

    combined = pd.concat(all_comparisons, ignore_index=True)
    combined.to_csv('data/2025_fa_contract_structure_comparisons.csv', index=False)
    print(f"✓ Saved contract comparisons to data/2025_fa_contract_structure_comparisons.csv")

    print("\n✅ Analysis complete!")
    print("\nNext steps:")
    print("1. Review saved CSV for detailed comparisons")
    print("2. Open notebooks/07_contract_structure_optimization.ipynb for visualizations")
    print("3. Read CONTRACT_STRUCTURE_ANALYSIS_2025.md for full report")


if __name__ == '__main__':
    main()
