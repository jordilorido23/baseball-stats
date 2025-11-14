# Notebook Guide: Creating Your Free Agent Analysis Notebook

This guide helps you create `05_free_agent_analysis_2025.ipynb` to analyze the 2025 free agent class.

---

## Notebook Structure

### Cell 1: Setup and Imports

```python
# Setup
import sys
sys.path.append('..')

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

from src.data import SavantLeaderboards, FanGraphsFetcher, ContractData
from src.analysis import FreeAgentAnalyzer, AgingCurveAnalyzer, BreakoutDetector
import config

pd.set_option('display.max_columns', 50)
pd.set_option('display.max_rows', 100)
sns.set_style('darkgrid')

print("Setup complete!")
print(f"Analyzing {config.CURRENT_SEASON} season")
```

### Cell 2: Fetch 2025 Season Data

```python
# Initialize data fetchers
savant = SavantLeaderboards()
fangraphs = FanGraphsFetcher()
contracts = ContractData()

# Fetch 2025 season data
print(f"Fetching {config.CURRENT_SEASON} season data...")

# Expected stats from Baseball Savant
batter_xstats = savant.get_batter_expected_stats(
    config.CURRENT_SEASON,
    min_pa=200
)

# Traditional stats from FanGraphs (optional - for additional context)
batting_stats = fangraphs.get_batting_stats(
    config.CURRENT_SEASON,
    qual=200  # Minimum 200 PA
)

# Free agent list
fa_list = contracts.get_all_free_agents()

print(f"Fetched data for {len(batter_xstats)} batters")
print(f"Tracking {len(fa_list)} free agents")

# Preview
print("\nSample xStats data:")
batter_xstats.head()
```

### Cell 3: Initialize Analyzers

```python
# Initialize analysis tools
fa_analyzer = FreeAgentAnalyzer(dollars_per_war=8.0)  # Current market rate
aging_analyzer = AgingCurveAnalyzer()
breakout_detector = BreakoutDetector()  # For additional insights

print("Analyzers initialized!")
```

### Cell 4: Comprehensive Free Agent Analysis

```python
# Merge FA list with performance data
fa_analysis = fa_analyzer.analyze_free_agent_class(
    performance_df=batter_xstats,
    fa_list_df=fa_list,
    player_name_col='Name'  # Adjust based on your data's column name
)

print(f"Analyzed {len(fa_analysis)} free agents")
print("\nValue Score Distribution:")
fa_analysis['fa_value_score'].describe()

# Preview top candidates
fa_analysis.nlargest(10, 'fa_value_score')[
    ['player_name', 'age_2025', 'position', 'fa_value_score',
     'contract_recommendation', 'woba', 'xwoba', 'woba_gap']
]
```

### Cell 5: Identify Buy-Low Candidates

```python
# Find buy-low opportunities
buy_low = fa_analyzer.identify_buy_low_candidates(
    fa_analysis,
    min_woba_gap=0.020,      # 20+ point gap
    max_age=32,              # Pre-cliff
    min_quality_threshold=0.10  # 10%+ barrel rate
)

print(f"Found {len(buy_low)} buy-low candidates")

# Display
buy_low_display = buy_low[[
    'player_name', 'position', 'age_2025',
    'woba', 'xwoba', 'woba_gap',
    'barrel_batted_rate', 'avg_hit_speed',
    'fa_value_score', 'contract_recommendation'
]].head(15)

print("\nTop 15 Buy-Low Free Agents:")
print(buy_low_display.to_string(index=False))
```

### Cell 6: Identify Regression Risks

```python
# Find overperformers (regression risk)
regression_risks = fa_analyzer.identify_regression_risks(
    fa_analysis,
    min_woba_gap=-0.020,     # 20+ point negative gap
    quality_threshold=0.08    # Below average barrel rate
)

print(f"Found {len(regression_risks)} regression risk candidates")

# Display
if len(regression_risks) > 0:
    regression_display = regression_risks[[
        'player_name', 'position', 'age_2025',
        'woba', 'xwoba', 'woba_gap',
        'barrel_batted_rate',
        'fa_value_score'
    ]].head(15)

    print("\nTop 15 Regression Risks (Sell High):")
    print(regression_display.to_string(index=False))
```

### Cell 7: Visualization - Expected vs Actual Performance

```python
# Create scatter plot comparing actual vs expected stats
fig = fa_analyzer.create_fa_comparison_chart(
    fa_df=fa_analysis,
    x_col='woba',
    y_col='xwoba',
    label_col='player_name',
    highlight_players=['Juan Soto', 'Pete Alonso', 'Willy Adames'],  # Adjust names
    title='2025 Free Agents: Expected vs Actual wOBA'
)

# Save for blog
plt.savefig('../blog/figures/fa_xwoba_vs_woba_2025.png', dpi=300, bbox_inches='tight')
plt.show()

print("Saved to: blog/figures/fa_xwoba_vs_woba_2025.png")
```

### Cell 8: Quality of Contact Analysis

```python
# Barrel rate leaders among free agents
if 'barrel_batted_rate' in fa_analysis.columns:
    barrel_leaders = fa_analysis.nlargest(20, 'barrel_batted_rate')

    # Visualization
    fig, ax = plt.subplots(figsize=(12, 8))

    # Horizontal bar chart
    ax.barh(
        barrel_leaders['player_name'],
        barrel_leaders['barrel_batted_rate'],
        color='steelblue',
        edgecolor='black'
    )

    # Overlay wOBA gap with color
    for idx, row in barrel_leaders.iterrows():
        gap = row.get('woba_gap', 0)
        if gap >= 0.020:
            ax.scatter(row['barrel_batted_rate'], row['player_name'],
                      s=200, c='green', marker='o', zorder=3,
                      label='Buy-Low' if idx == barrel_leaders.index[0] else '')
        elif gap <= -0.020:
            ax.scatter(row['barrel_batted_rate'], row['player_name'],
                      s=200, c='red', marker='x', zorder=3,
                      label='Regression Risk' if idx == barrel_leaders.index[0] else '')

    ax.set_xlabel('Barrel Rate (%)', fontsize=12, fontweight='bold')
    ax.set_title('2025 Free Agents: Barrel Rate Leaders', fontsize=14, fontweight='bold')
    ax.legend()
    plt.tight_layout()

    # Save
    plt.savefig('../blog/figures/fa_barrel_rate_leaders_2025.png', dpi=300, bbox_inches='tight')
    plt.show()
```

### Cell 9: Aging Curve Projections for Top FAs

```python
# Project contracts for top free agents
top_fas = fa_analysis.nlargest(10, 'fa_value_score')

projections = []

for _, player in top_fas.iterrows():
    player_name = player['player_name']
    age = player['age_2025']
    position = player['position']

    # Estimate current WAR (you may have this in your data)
    # For now, use value score as proxy
    estimated_war = player['fa_value_score'] / 20  # Rough conversion

    # Project 6-year contract
    contract_analysis = aging_analyzer.calculate_contract_war(
        current_war=estimated_war,
        current_age=age,
        position=position,
        contract_years=6
    )

    projections.append({
        'player': player_name,
        'age': age,
        'position': position,
        'total_war_6yr': contract_analysis['total_war'],
        'avg_war_per_year': contract_analysis['avg_war_per_year'],
        'cliff_during_contract': contract_analysis['cliff_during_contract'],
        'years_to_cliff': contract_analysis['years_to_cliff']
    })

proj_df = pd.DataFrame(projections)
print("6-Year Contract Projections for Top Free Agents:")
print(proj_df.to_string(index=False))
```

### Cell 10: Individual Player Deep Dive

```python
# Generate detailed report for a specific player
target_player = "Juan Soto"  # Change to any FA

player_report = fa_analyzer.generate_fa_report(
    player_name=target_player,
    fa_df=fa_analysis,
    current_war=6.5,  # Update with actual WAR
    contract_years=12
)

print(f"=== {target_player} Free Agent Report ===\n")

for section, data in player_report.items():
    if section != 'player_name':
        print(f"{section.upper().replace('_', ' ')}:")
        if isinstance(data, dict):
            for key, value in data.items():
                print(f"  {key}: {value}")
        else:
            print(f"  {data}")
        print()
```

### Cell 11: Aging Curve Visualization

```python
# Visualize aging curve for a top FA
target_player_data = fa_analysis[fa_analysis['player_name'] == target_player].iloc[0]

age = target_player_data['age_2025']
position = target_player_data['position']
current_performance = 135  # Indexed wRC+ or similar

fig = aging_analyzer.plot_aging_curve(
    position=position,
    current_age=age,
    current_performance=current_performance,
    years_back=5,
    years_forward=10,
    metric_name='wRC+'
)

plt.savefig(f'../blog/figures/aging_curve_{position}_{target_player}.png',
            dpi=300, bbox_inches='tight')
plt.show()

print(f"Saved aging curve for {target_player}")
```

### Cell 12: Contract Scenario Comparison

```python
# Compare different contract scenarios for a player
scenarios = [
    {'years': 10, 'aav': 50},  # 10yr/$500M
    {'years': 12, 'aav': 45},  # 12yr/$540M
    {'years': 14, 'aav': 42},  # 14yr/$588M
]

comparison = aging_analyzer.compare_contract_scenarios(
    current_war=6.5,
    current_age=age,
    position=position,
    scenarios=scenarios
)

print(f"\nContract Scenario Comparison for {target_player}:")
print(comparison.to_string(index=False))

# Visualize
fig, ax = plt.subplots(figsize=(10, 6))

ax.bar(comparison['scenario'], comparison['total_surplus_millions'],
       color=['green' if x > 0 else 'red' for x in comparison['total_surplus_millions']],
       edgecolor='black')

ax.axhline(0, color='black', linewidth=0.8)
ax.set_xlabel('Contract Scenario', fontsize=12, fontweight='bold')
ax.set_ylabel('Surplus Value ($M)', fontsize=12, fontweight='bold')
ax.set_title(f'{target_player}: Contract Scenario Surplus Value',
             fontsize=14, fontweight='bold')
ax.grid(alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig(f'../blog/figures/contract_scenarios_{target_player}.png',
            dpi=300, bbox_inches='tight')
plt.show()
```

### Cell 13: Export Results for Blog

```python
# Export key findings to CSV for blog reference
buy_low.to_csv('../blog/figures/buy_low_candidates_2025.csv', index=False)
regression_risks.to_csv('../blog/figures/regression_risks_2025.csv', index=False)
proj_df.to_csv('../blog/figures/aging_projections_2025.csv', index=False)

print("Exported CSVs for blog reference")
```

### Cell 14: Summary Statistics

```python
# Overall summary
print("=== 2025 Free Agent Class Summary ===\n")

print(f"Total Free Agents Analyzed: {len(fa_analysis)}")
print(f"Buy-Low Candidates: {len(buy_low)}")
print(f"Regression Risks: {len(regression_risks)}")
print()

print("Value Score Tiers:")
for tier in ['Max Contract', 'Premium', 'Mid-Tier', 'Value', 'Avoid']:
    count = (fa_analysis['contract_recommendation'] == tier).sum()
    print(f"  {tier}: {count} players")

print("\nPosition Breakdown:")
print(fa_analysis['position'].value_counts())

print("\nAge Distribution:")
print(fa_analysis['age_2025'].describe())
```

---

## Tips for Analysis

### 1. Data Quality Checks
Always verify:
- Column names match between datasets (use `df.columns` to check)
- Player name matching works (fuzzy match if needed)
- No missing data in key columns (xwOBA, barrel_rate, etc.)

### 2. Customization
Adjust thresholds based on your findings:
- `min_woba_gap`: Try 0.015, 0.020, 0.025 to see sensitivity
- `min_quality_threshold`: Adjust based on position
- `max_age`: Consider position-specific cutoffs

### 3. Visualization Best Practices
- Always save figures to `blog/figures/` with descriptive names
- Use 300 DPI for publication quality
- Include player names on key charts
- Color code by category (buy-low = green, regression = red)

### 4. Blog Integration
After running analysis:
1. Update blog posts with actual numbers from output
2. Add generated figures using markdown: `![Description](../figures/filename.png)`
3. Link to CSV exports for readers to explore
4. Include code snippets showing reproducibility

---

## Next Steps After Running Notebook

1. **Update Blog Post 1**
   - Replace placeholder numbers with actual 2025 data
   - Add specific player examples from results
   - Insert generated visualizations

2. **Update Blog Post 2**
   - Add real buy-low candidate names and stats
   - Include barrel rate leaders from analysis
   - Add contract recommendations

3. **Write Blog Post 3**
   - Use aging curve analysis from notebook
   - Focus on contract length decisions
   - Include scenario comparison charts

4. **Share Findings**
   - Publish to Substack/Medium
   - Share visualizations on Twitter/X
   - Post to r/baseball and r/Sabermetrics

---

## Troubleshooting

### Issue: Player names don't match between datasets
```python
# Use fuzzy matching
from fuzzywuzzy import fuzz

def match_players(name1, name2):
    return fuzz.ratio(name1, name2) > 85
```

### Issue: Missing xStats columns
Check Baseball Savant data structure:
```python
print(batter_xstats.columns.tolist())
```

May need to use different column names like:
- `estimated_woba_using_speedangle` instead of `xwoba`
- `launch_speed` instead of `exit_velocity`

### Issue: Free agents not in performance data
Filter FA list to only include players with 2025 MLB data:
```python
fa_with_data = fa_list[fa_list['player_name'].isin(batter_xstats['Name'])]
```

---

Happy analyzing! Use this guide as a template and customize based on your specific data and interests.
