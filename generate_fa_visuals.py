"""
Generate visualizations for 2025-2026 Free Agent Analysis.

This script creates publication-ready charts for the free agent analysis report and blog posts.
Run this after the Jupyter notebook to export high-quality figures.

Usage:
    python generate_fa_visuals.py

Output:
    Saves PNG files to blog/figures/ directory
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Import custom modules
from src.data import ContractData
from src.analysis import FreeAgentAnalyzer

# Configuration
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette('husl')
OUTPUT_DIR = Path('blog/figures')
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def create_fa_tier_chart():
    """Create bar chart of free agents by tier and position."""
    contracts = ContractData()
    fa_list = contracts.get_all_free_agents()

    # Count by tier
    tier_counts = fa_list['tier'].value_counts().sort_index()

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    # Tier distribution
    colors = {'Elite': '#2E7D32', 'Premium': '#1976D2', 'Mid': '#F57C00', 'Value': '#C62828'}
    tier_colors = [colors.get(tier, 'gray') for tier in tier_counts.index]

    ax1.bar(tier_counts.index, tier_counts.values, color=tier_colors, alpha=0.8, edgecolor='black')
    ax1.set_xlabel('Market Tier', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Number of Free Agents', fontsize=12, fontweight='bold')
    ax1.set_title('2025-26 Free Agent Class\nDistribution by Market Tier',
                  fontsize=14, fontweight='bold', pad=15)
    ax1.grid(axis='y', alpha=0.3)

    # Add value labels
    for i, v in enumerate(tier_counts.values):
        ax1.text(i, v + 0.5, str(v), ha='center', fontweight='bold')

    # Position distribution
    pos_counts = fa_list['position'].value_counts().nlargest(10)
    ax2.barh(range(len(pos_counts)), pos_counts.values, alpha=0.8, edgecolor='black')
    ax2.set_yticks(range(len(pos_counts)))
    ax2.set_yticklabels(pos_counts.index)
    ax2.set_xlabel('Number of Free Agents', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Position', fontsize=12, fontweight='bold')
    ax2.set_title('2025-26 Free Agent Class\nTop 10 Positions',
                  fontsize=14, fontweight='bold', pad=15)
    ax2.grid(axis='x', alpha=0.3)

    # Add value labels
    for i, v in enumerate(pos_counts.values):
        ax2.text(v + 0.2, i, str(v), va='center', fontweight='bold')

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'fa_2025_tier_distribution.png', dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {OUTPUT_DIR / 'fa_2025_tier_distribution.png'}")
    plt.close()

def create_top_fas_chart():
    """Create horizontal bar chart of top 15 free agents by WAR."""
    contracts = ContractData()
    fa_list = contracts.get_all_free_agents()

    top_15 = fa_list.nlargest(15, '2025_war').sort_values('2025_war')

    fig, ax = plt.subplots(figsize=(12, 10))

    # Color by position type
    colors = {
        'SP': '#1976D2', 'RP': '#0288D1',
        'OF': '#2E7D32', 'DH': '#388E3C',
        '1B': '#F57C00', '2B': '#FB8C00', '3B': '#FF9800', 'SS': '#FFA726',
        'C': '#C62828'
    }
    bar_colors = [colors.get(pos, '#757575') for pos in top_15['position']]

    bars = ax.barh(range(len(top_15)), top_15['2025_war'], color=bar_colors,
                   alpha=0.8, edgecolor='black', linewidth=1.5)

    # Labels
    labels = [f"{row['player_name']} ({row['position']}, {row['age_2025']})"
              for _, row in top_15.iterrows()]
    ax.set_yticks(range(len(top_15)))
    ax.set_yticklabels(labels, fontsize=10)
    ax.set_xlabel('2025 WAR', fontsize=12, fontweight='bold')
    ax.set_title('Top 15 Free Agents by 2025 WAR\n(2025-26 Free Agent Class)',
                 fontsize=14, fontweight='bold', pad=20)
    ax.grid(axis='x', alpha=0.3)

    # Add WAR values
    for i, (_, row) in enumerate(top_15.iterrows()):
        ax.text(row['2025_war'] + 0.15, i, f"{row['2025_war']:.1f}",
                va='center', fontweight='bold', fontsize=9)

    # Legend
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='#1976D2', label='Pitchers'),
        Patch(facecolor='#2E7D32', label='Outfield'),
        Patch(facecolor='#F57C00', label='Infield'),
        Patch(facecolor='#C62828', label='Catcher')
    ]
    ax.legend(handles=legend_elements, loc='lower right', fontsize=10)

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'fa_2025_top_15_war.png', dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {OUTPUT_DIR / 'fa_2025_top_15_war.png'}")
    plt.close()

def create_age_distribution():
    """Create age distribution histogram with aging cliff zones."""
    contracts = ContractData()
    fa_list = contracts.get_all_free_agents()

    fig, ax = plt.subplots(figsize=(12, 7))

    # Histogram
    ax.hist(fa_list['age_2025'], bins=range(25, 45), alpha=0.7,
            edgecolor='black', linewidth=1.5, color='#1976D2')

    # Aging zones
    ax.axvspan(27, 30, alpha=0.2, color='green', label='Prime Years (27-30)')
    ax.axvspan(30, 33, alpha=0.2, color='yellow', label='Late Prime (30-33)')
    ax.axvspan(33, 37, alpha=0.2, color='orange', label='Aging Cliff Zone (33-37)')
    ax.axvspan(37, 44, alpha=0.2, color='red', label='High Risk (37+)')

    ax.set_xlabel('Age in 2025-26 Season', fontsize=12, fontweight='bold')
    ax.set_ylabel('Number of Free Agents', fontsize=12, fontweight='bold')
    ax.set_title('2025-26 Free Agent Class: Age Distribution\nwith Aging Cliff Risk Zones',
                 fontsize=14, fontweight='bold', pad=20)
    ax.legend(loc='upper right', fontsize=10)
    ax.grid(axis='y', alpha=0.3)

    # Add statistics
    mean_age = fa_list['age_2025'].mean()
    median_age = fa_list['age_2025'].median()

    ax.axvline(mean_age, color='red', linestyle='--', linewidth=2, alpha=0.7)
    ax.text(mean_age + 0.3, ax.get_ylim()[1] * 0.9,
            f'Mean: {mean_age:.1f}', fontsize=10, fontweight='bold')

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'fa_2025_age_distribution.png', dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {OUTPUT_DIR / 'fa_2025_age_distribution.png'}")
    plt.close()

def create_war_vs_age_scatter():
    """Create scatter plot of WAR vs Age with contract value bubbles."""
    contracts = ContractData()
    fa_list = contracts.get_all_free_agents()
    fa_analyzer = FreeAgentAnalyzer(dollars_per_war=8.0)

    # Calculate estimated contract values
    contract_values = []
    for _, player in fa_list.iterrows():
        age = player['age_2025']
        position = player['position']
        war = player['2025_war']

        # Determine contract length based on age
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
        contract_est = fa_analyzer.estimate_contract_value(war_proj)
        contract_values.append(contract_est['total_value_millions'])

    fa_list['contract_value'] = contract_values

    fig, ax = plt.subplots(figsize=(12, 8))

    # Color by tier
    tier_colors = {'Elite': '#2E7D32', 'Premium': '#1976D2', 'Mid': '#F57C00', 'Value': '#C62828'}
    colors = [tier_colors.get(tier, 'gray') for tier in fa_list['tier']]

    scatter = ax.scatter(fa_list['age_2025'], fa_list['2025_war'],
                        s=fa_list['contract_value'] * 2,
                        c=colors, alpha=0.6, edgecolors='black', linewidth=1.5)

    # Label top players
    top_players = fa_list.nlargest(10, '2025_war')
    for _, player in top_players.iterrows():
        ax.annotate(player['player_name'],
                   (player['age_2025'], player['2025_war']),
                   xytext=(5, 5), textcoords='offset points', fontsize=8)

    ax.set_xlabel('Age in 2025-26', fontsize=12, fontweight='bold')
    ax.set_ylabel('2025 WAR', fontsize=12, fontweight='bold')
    ax.set_title('Free Agent Value: WAR vs Age\n(bubble size = projected contract value)',
                 fontsize=14, fontweight='bold', pad=20)
    ax.grid(alpha=0.3)

    # Legend
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='#2E7D32', label='Elite Tier'),
        Patch(facecolor='#1976D2', label='Premium Tier'),
        Patch(facecolor='#F57C00', label='Mid Tier'),
        Patch(facecolor='#C62828', label='Value Tier')
    ]
    ax.legend(handles=legend_elements, loc='upper right', fontsize=10)

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'fa_2025_war_vs_age.png', dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {OUTPUT_DIR / 'fa_2025_war_vs_age.png'}")
    plt.close()

def create_contract_projection_table():
    """Create visual table of top contract projections."""
    contracts = ContractData()
    fa_list = contracts.get_all_free_agents()
    fa_analyzer = FreeAgentAnalyzer(dollars_per_war=8.0)

    # Top 10 by WAR
    top_10 = fa_list.nlargest(10, '2025_war')

    projections = []
    for _, player in top_10.iterrows():
        age = player['age_2025']
        position = player['position']
        war = player['2025_war']

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

        war_proj = fa_analyzer.project_multi_year_war(war, age, position, years)
        contract_est = fa_analyzer.estimate_contract_value(war_proj)

        projections.append({
            'Player': player['player_name'],
            'Pos': position,
            'Age': age,
            '2025 WAR': war,
            'Years': years,
            'Total $M': f"${contract_est['total_value_millions']:.0f}M",
            'AAV': f"${contract_est['aav_millions']:.0f}M"
        })

    proj_df = pd.DataFrame(projections)

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.axis('tight')
    ax.axis('off')

    table = ax.table(cellText=proj_df.values, colLabels=proj_df.columns,
                    cellLoc='center', loc='center',
                    colWidths=[0.25, 0.08, 0.08, 0.12, 0.08, 0.15, 0.12])

    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 2)

    # Style header
    for i in range(len(proj_df.columns)):
        cell = table[(0, i)]
        cell.set_facecolor('#1976D2')
        cell.set_text_props(weight='bold', color='white')

    # Alternate row colors
    for i in range(1, len(proj_df) + 1):
        for j in range(len(proj_df.columns)):
            cell = table[(i, j)]
            if i % 2 == 0:
                cell.set_facecolor('#E3F2FD')
            else:
                cell.set_facecolor('white')

    plt.title('Top 10 Free Agents: Projected Contract Values\n(2025-26 Free Agent Class)',
              fontsize=14, fontweight='bold', pad=20)

    plt.savefig(OUTPUT_DIR / 'fa_2025_contract_projections.png', dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {OUTPUT_DIR / 'fa_2025_contract_projections.png'}")
    plt.close()

def main():
    """Generate all visualizations."""
    print("\n=== Generating 2025-26 Free Agent Analysis Visualizations ===\n")

    print("Creating charts...")
    create_fa_tier_chart()
    create_top_fas_chart()
    create_age_distribution()
    create_war_vs_age_scatter()
    create_contract_projection_table()

    print(f"\n✅ All visualizations saved to {OUTPUT_DIR}/")
    print("\nGenerated files:")
    for file in OUTPUT_DIR.glob('fa_2025_*.png'):
        print(f"  - {file.name}")

    print("\nUse these visualizations in:")
    print("  - Blog posts (blog/posts/)")
    print("  - Reports (2025_FREE_AGENT_ANALYSIS_REPORT.md)")
    print("  - Presentations")
    print("  - Social media")

if __name__ == '__main__':
    main()
