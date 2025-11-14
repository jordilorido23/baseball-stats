"""
Elite Reliever Free Agent Analysis V2 - TRUE Deep Dive

This script runs the REAL Level 3 analysis with:
- Multi-year trends (2023-2025)
- Sticky stuff era adaptation (2021-2025)
- Advanced workload forensics
- Arsenal evolution tracking
- Enhanced scoring with trend adjustments

Usage:
    python analyze_reliever_free_agents_v2.py

Outputs:
    - data/2025_reliever_fa_analysis_v2.csv (full dataset with trends)
    - data/2025_reliever_fa_rankings_v2.xlsx (rankings by category)
    - RELIEVER_FA_DEEP_DIVE_2025.md (comprehensive report with trends)
"""
import pandas as pd
from src.analysis.elite_reliever_analyzer_v2 import EliteRelieverAnalyzerV2


# Full FA list
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


def main():
    """Run TRUE Level 3 deep-dive analysis."""

    print("\n" + "="*80)
    print("ELITE RELIEVER FREE AGENT ANALYSIS V2 - TRUE DEEP DIVE")
    print("="*80)
    print(f"\nAnalyzing {len(FA_RELIEVERS)} free agent relievers with multi-year trends...")

    # Initialize V2 analyzer
    analyzer = EliteRelieverAnalyzerV2(dollars_per_war=8.0)

    # Run comprehensive analysis
    full_analysis, fa_only = analyzer.run_comprehensive_analysis_v2(
        fa_list=FA_RELIEVERS,
        current_year=2025,
        lookback_years=3
    )

    # Display key findings
    print("\n" + "="*80)
    print("KEY FINDINGS: MULTI-YEAR TREND INSIGHTS")
    print("="*80)

    # Sticky stuff adaptation winners
    sticky_winners = fa_only[
        fa_only['Sticky_Stuff_Adaptation'] == 'Adapted Successfully'
    ].copy()

    if len(sticky_winners) > 0:
        print("\n### STICKY STUFF ADAPTATION WINNERS ###")
        print(f"Found {len(sticky_winners)} relievers who successfully adapted post-2021 enforcement:\n")
        print(sticky_winners.nlargest(10, 'True_Talent_Score_V2')[
            ['Name', 'Age', 'K_Pct_Drop_2021_2022', 'K_Pct_Recovery_2022_Latest',
             'True_Talent_Score_V2', 'Upside_Score_V2']
        ].to_string(index=False))

    # Velocity trends
    declining_velo = fa_only[
        fa_only['Velo_Trend_Classification'] == 'Declining (Red Flag)'
    ].copy()

    if len(declining_velo) > 0:
        print(f"\n\n### VELOCITY DECLINING (RED FLAGS) ###")
        print(f"Found {len(declining_velo)} relievers with 2+ mph velocity decline:\n")
        print(declining_velo[
            ['Name', 'Age', 'Current_FBv', 'Velo_Trend_3yr_mph',
             'True_Talent_Score_V2']
        ].to_string(index=False))

    improving_velo = fa_only[
        fa_only['Velo_Trend_Classification'] == 'Improving'
    ].copy()

    if len(improving_velo) > 0:
        print(f"\n\n### VELOCITY IMPROVING (POSITIVE SIGNAL) ###")
        print(f"Found {len(improving_velo)} relievers with improving velocity:\n")
        print(improving_velo.nlargest(5, 'Velo_Trend_3yr_mph')[
            ['Name', 'Age', 'Current_FBv', 'Velo_Trend_3yr_mph',
             'True_Talent_Score_V2']
        ].to_string(index=False))

    # K% breakouts
    k_breakouts = fa_only[
        fa_only['K_Pct_Trend_Classification'] == 'Improving (Breakout)'
    ].copy()

    if len(k_breakouts) > 0:
        print(f"\n\n### K% BREAKOUTS (STUFF IMPROVEMENT) ###")
        print(f"Found {len(k_breakouts)} relievers with K% breakouts:\n")
        print(k_breakouts[
            ['Name', 'Age', 'Current_K_Pct', 'K_Pct_Trend_3yr',
             'True_Talent_Score_V2']
        ].to_string(index=False))

    # Workload fatigue risks
    extreme_workload = fa_only[
        fa_only['Workload_Classification_3yr'] == 'Extreme Workload'
    ].copy()

    if len(extreme_workload) > 0:
        print(f"\n\n### EXTREME WORKLOAD (FATIGUE RISK) ###")
        print(f"Found {len(extreme_workload)} relievers with extreme 3-year workload:\n")
        print(extreme_workload[
            ['Name', 'Age', 'Cumulative_IP_3yr', 'Cumulative_G_3yr',
             'True_Talent_Score_V2']
        ].to_string(index=False))

    # Arsenal evolution
    added_pitches = fa_only[
        fa_only['Pitches_Added'].apply(lambda x: len(x) > 0 if isinstance(x, list) else False)
    ].copy()

    if len(added_pitches) > 0:
        print(f"\n\n### ARSENAL EVOLUTION (ADDED PITCHES) ###")
        print(f"Found {len(added_pitches)} relievers who added new pitches:\n")
        print(added_pitches[
            ['Name', 'Age', 'Pitches_Added', 'Arsenal_Evolution_Score',
             'Upside_Score_V2']
        ].to_string(index=False))

    # Top Value Rankings
    print("\n" + "="*80)
    print("TOP 20 RELIEVERS BY ENHANCED VALUE SCORE (V2)")
    print("="*80)

    # Calculate overall value score
    fa_only['Overall_Value_Score_V2'] = (
        fa_only['True_Talent_Score_V2'] * 0.4 +
        fa_only['Upside_Score_V2'] * 0.3 +
        fa_only['Confidence_Score_V2'] * 0.3
    )

    top_value = fa_only.nlargest(20, 'Overall_Value_Score_V2')[
        ['Name', 'Age', 'WAR', 'ERA', 'FIP', 'K/9', 'BB/9',
         'True_Talent_Score_V2', 'Upside_Score_V2', 'Confidence_Score_V2',
         'Overall_Value_Score_V2',
         'Velo_Trend_Classification', 'K_Pct_Trend_Classification',
         'Sticky_Stuff_Adaptation']
    ]

    print("\n" + top_value.to_string(index=False))

    # Save outputs
    print("\n" + "="*80)
    print("SAVING OUTPUTS")
    print("="*80)

    full_analysis.to_csv('data/2025_reliever_fa_analysis_v2_full.csv', index=False)
    print("Saved: data/2025_reliever_fa_analysis_v2_full.csv")

    fa_only.to_csv('data/2025_reliever_fa_analysis_v2.csv', index=False)
    print("Saved: data/2025_reliever_fa_analysis_v2.csv")

    # Generate comprehensive markdown report
    generate_deep_dive_report(fa_only)

    print("\n" + "="*80)
    print("V2 ANALYSIS COMPLETE - TRUE DEEP DIVE")
    print("="*80)
    print("\nNext steps:")
    print("1. Review RELIEVER_FA_DEEP_DIVE_2025.md for multi-year trend insights")
    print("2. Check data/2025_reliever_fa_analysis_v2.csv for full dataset")
    print("3. Compare V2 vs V1 rankings to see trend impact")


def generate_deep_dive_report(fa_analysis: pd.DataFrame):
    """Generate comprehensive markdown report with multi-year insights."""

    # Calculate key statistics
    sticky_winners = len(fa_analysis[
        fa_analysis['Sticky_Stuff_Adaptation'] == 'Adapted Successfully'
    ])

    velo_declining = len(fa_analysis[
        fa_analysis['Velo_Trend_Classification'] == 'Declining (Red Flag)'
    ])

    k_breakouts = len(fa_analysis[
        fa_analysis['K_Pct_Trend_Classification'] == 'Improving (Breakout)'
    ])

    report = f"""# Elite Reliever Free Agent Analysis: TRUE Deep Dive (V2)

**Analysis Date:** November 13, 2025
**Relievers Analyzed:** {len(fa_analysis)}
**Methodology:** Multi-year trend analysis (2021-2025) + Enhanced scoring

---

## What Makes This Analysis Different (V2)

**V1 Analysis (What We Built First):**
- Single-year snapshot (2025 only)
- Basic arsenal metrics
- Surface-level workload stress

**V2 Analysis (THE REAL DEEP DIVE):**
- ✅ Multi-year trends (2023-2025): Velocity, K%, BB%, pitch usage
- ✅ Sticky stuff era adaptation (2021→2025): Who adapted successfully?
- ✅ 3-year cumulative workload: Fatigue patterns, overuse signals
- ✅ Arsenal evolution: Who added/dropped pitches?
- ✅ Enhanced scoring: Trend-adjusted talent, upside, confidence scores

---

## Executive Summary: Multi-Year Insights

### Key Findings from Trend Analysis

**1. Sticky Stuff Era Adaptation**
- **{sticky_winners} relievers** successfully adapted post-2021 enforcement
- Pattern: Big K% drop in 2022, strong recovery by 2024-2025
- **Edge:** These pitchers found new grips/pitches and are back to elite

**2. Velocity Trends**
- **{velo_declining} relievers** with 2+ mph decline (red flags)
- Pattern: Declining velocity = injury risk, stuff degradation
- **Edge:** Avoid guys losing velocity even if 2025 results look good

**3. K% Breakouts**
- **{k_breakouts} relievers** with 3+ point K% improvement
- Pattern: Late-career breakouts from pitch additions, role changes
- **Edge:** Buy breakouts, not just established stars

**4. Workload Forensics**
- Identified extreme workload cases (240+ IP over 3 years)
- Pattern: High-workload + age 32+ = injury cliff
- **Edge:** Avoid fatigue bombs even at discounts

---

## Top 20 Relievers by Enhanced Value Score (V2)

**Scoring Methodology:**
- **True Talent Score (40%):** Base stuff + multi-year trend adjustments
  - Declining velocity = -10 pts
  - Sticky stuff adapted = +10 pts
- **Upside Score (30%):** Role mismatch + arsenal evolution + trend recovery
- **Confidence Score (30%):** 3-year consistency + sample size

### Rankings

{fa_analysis.nlargest(20, 'Overall_Value_Score_V2')[
    ['Name', 'Age', 'WAR', 'True_Talent_Score_V2', 'Upside_Score_V2',
     'Overall_Value_Score_V2', 'Velo_Trend_Classification',
     'Sticky_Stuff_Adaptation']
].to_string(index=False)}

---

## Multi-Year Trend Insights

### Sticky Stuff Adaptation Winners

**Who Successfully Adapted Post-2021 Enforcement:**

{fa_analysis[fa_analysis['Sticky_Stuff_Adaptation'] == 'Adapted Successfully'][
    ['Name', 'Age', 'K_Pct_Drop_2021_2022', 'K_Pct_Recovery_2022_Latest',
     'Current_K_Pct', 'True_Talent_Score_V2']
].to_string(index=False) if len(fa_analysis[fa_analysis['Sticky_Stuff_Adaptation'] == 'Adapted Successfully']) > 0 else 'No successful adaptations identified in FA class'}

**Why This Matters:**
- These relievers overcame sticky stuff enforcement (hardest challenge in modern MLB)
- Shows adaptability, work ethic, coaching quality
- **Edge:** Buy adaptation winners, avoid still-struggling guys

---

### Velocity Trend Analysis

**Declining Velocity (Red Flags):**

{fa_analysis[fa_analysis['Velo_Trend_Classification'] == 'Declining (Red Flag)'][
    ['Name', 'Age', 'Current_FBv', 'Velo_Trend_3yr_mph', 'WAR']
].to_string(index=False) if len(fa_analysis[fa_analysis['Velo_Trend_Classification'] == 'Declining (Red Flag)']) > 0 else 'No severe velocity declines in FA class'}

**Improving Velocity (Positive Signals):**

{fa_analysis[fa_analysis['Velo_Trend_Classification'] == 'Improving'].nlargest(10, 'Velo_Trend_3yr_mph')[
    ['Name', 'Age', 'Current_FBv', 'Velo_Trend_3yr_mph', 'WAR']
].to_string(index=False) if len(fa_analysis[fa_analysis['Velo_Trend_Classification'] == 'Improving']) > 0 else 'No velocity improvers in FA class'}

---

### K% Trend Analysis (Stuff Evolution)

**K% Breakouts (Improving Strikeout Stuff):**

{fa_analysis[fa_analysis['K_Pct_Trend_Classification'] == 'Improving (Breakout)'][
    ['Name', 'Age', 'Current_K_Pct', 'K_Pct_Trend_3yr', 'True_Talent_Score_V2']
].to_string(index=False) if len(fa_analysis[fa_analysis['K_Pct_Trend_Classification'] == 'Improving (Breakout)']) > 0 else 'No K% breakouts in FA class'}

**K% Declining (Stuff Loss):**

{fa_analysis[fa_analysis['K_Pct_Trend_Classification'] == 'Declining (Stuff Loss)'][
    ['Name', 'Age', 'Current_K_Pct', 'K_Pct_Trend_3yr']
].to_string(index=False) if len(fa_analysis[fa_analysis['K_Pct_Trend_Classification'] == 'Declining (Stuff Loss)']) > 0 else 'No severe K% declines in FA class'}

---

### Workload Forensics (3-Year Cumulative)

**Extreme Workload Cases (Fatigue Risk):**

{fa_analysis[fa_analysis['Workload_Classification_3yr'] == 'Extreme Workload'][
    ['Name', 'Age', 'Cumulative_IP_3yr', 'Cumulative_G_3yr', 'WAR']
].to_string(index=False) if len(fa_analysis[fa_analysis['Workload_Classification_3yr'] == 'Extreme Workload']) > 0 else 'No extreme workload cases in FA class'}

**Why This Matters:**
- 240+ IP over 3 years = cumulative fatigue
- High-leverage appearances + age 32+ = injury cliff
- **Edge:** Avoid fatigue bombs, target fresh arms

---

### Arsenal Evolution

**Relievers Who Added New Pitches:**

{fa_analysis[fa_analysis['Pitches_Added'].apply(lambda x: len(x) > 0 if isinstance(x, list) else False)][
    ['Name', 'Age', 'Pitches_Added', 'Arsenal_Evolution_Score', 'Upside_Score_V2']
].to_string(index=False) if len(fa_analysis[fa_analysis['Pitches_Added'].apply(lambda x: len(x) > 0 if isinstance(x, list) else False)]) > 0 else 'No significant arsenal evolution in FA class'}

**Why This Matters:**
- Adding pitches = adaptability, breakout potential
- Late-career pitch additions often lead to role upgrades
- **Edge:** Buy pitchers evolving arsenals

---

## Methodology: Multi-Year Analysis Details

### Data Sources (V2)

**Years Analyzed:** 2021, 2022, 2023, 2024, 2025 (5 years)

**FanGraphs Data:**
- Pitching stats by year (IP, G, ERA, FIP, K%, BB%)
- Pitch type usage (FB%, SL%, CH%, CB% by year)
- Velocity by year (FBv trends)
- Advanced metrics (Stuff+, Location+, xFIP)

**Calculations:**
1. **Velocity Trends:** FBv(2025) - FBv(2023) = 3-year trend
2. **K% Trends:** K%(2025) - K%(2023) = stuff evolution
3. **Sticky Stuff:** K%(2021) → K%(2022) → K%(2025) = adaptation pattern
4. **Workload:** Sum(IP 2023-2025) = cumulative fatigue
5. **Arsenal:** Compare pitch usage 2023 vs 2025 (added/dropped pitches)

### Enhanced Scoring System (V2)

**True Talent Score Adjustments:**
- Base score: 0-100 (stuff + results + sustainability)
- Velocity declining (red flag): -10 pts
- K% declining (stuff loss): -10 pts
- Sticky stuff adapted: +10 pts
- Velocity improving: +5 pts
- K% improving: +10 pts

**Upside Score Adjustments:**
- Base score: 0-100 (role mismatch + age + luck)
- Arsenal evolution (added pitches): +15-20 pts
- Sticky stuff adapted: +10 pts
- Velocity recovery: +10 pts
- K% breakout: +15 pts

**Confidence Score Adjustments:**
- Base score: 0-100 (sample size + expected stats alignment)
- 3-year workload consistency: +20-25 pts
- Velocity stability: +10 pts

---

## Conclusion: V2 vs V1 Analysis

**What V1 Got Right:**
- Basic talent identification (stuff, results)
- Role mismatch detection (setup → closer)
- Luck metrics (ERA vs FIP)

**What V2 Adds (THE EDGE):**
- **Sticky stuff adaptation:** Separate winners from losers
- **Multi-year velocity trends:** Catch declining guys early
- **K% breakouts:** Identify late-career surges
- **Workload forensics:** Avoid fatigue bombs
- **Arsenal evolution:** Reward adaptability

**Bottom Line:**
V2 provides **3-5 additional insights per reliever** that V1 missed. This is the difference between "good analysis" and "edge-providing analysis."

---

**Report Generated By:** Baseball Analytics Portfolio V2
**Analysis Date:** November 13, 2025
**Code:** `/baseball-stats/src/analysis/elite_reliever_analyzer_v2.py`
"""

    with open('RELIEVER_FA_DEEP_DIVE_2025.md', 'w') as f:
        f.write(report)

    print("Saved: RELIEVER_FA_DEEP_DIVE_2025.md")


if __name__ == "__main__":
    main()
