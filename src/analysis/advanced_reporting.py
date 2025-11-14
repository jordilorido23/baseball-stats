"""
Phase 5: Advanced Reporting & Pitcher-Specific Profiles

This module generates:
- Individual pitcher profiles with physics insights
- Executive summaries with market intelligence
- Visual comparisons and recommendations
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime


class AdvancedReporter:
    """Generates advanced reports and pitcher profiles."""

    def __init__(self):
        self.report_sections = []

    def generate_pitcher_profile(self, pitcher_data: Dict) -> str:
        """
        Generate detailed pitcher profile with physics insights.

        Format matches the Hunter Harvey example from the plan.

        Args:
            pitcher_data: Complete pitcher analysis data

        Returns:
            Formatted markdown profile
        """
        name = pitcher_data.get('player_name', 'Unknown')
        diamond_score = pitcher_data.get('Diamond_Score', 0)

        profile = f"""
# {name.upper()} - The Hidden Elite Closer

## Physics Edge:
- **VAA**: {pitcher_data.get('VAA_FB_avg', 0):.1f}° ({self._classify_vaa_percentile(pitcher_data.get('VAA_FB_avg', 0))}) → {self._vaa_interpretation(pitcher_data.get('VAA_FB_avg', 0))}
- **SSW Movement**: +{pitcher_data.get('SSW_Movement_FB', 0):.1f} inches ({self._ssw_interpretation(pitcher_data.get('SSW_Movement_FB', 0))})
- **Tunneling Score**: {pitcher_data.get('Tunneling_Score', 0):.0f}/100 ({self._tunneling_interpretation(pitcher_data.get('Tunneling_Score', 0))})

## Arsenal Synergy:
- **Has Gyro Slider**: {self._yes_no(pitcher_data.get('Has_Gyro', False))} | **Has Sweeper**: {self._yes_no(pitcher_data.get('Has_Sweeper', False))} → {self._arsenal_combo_interpretation(pitcher_data)}
- **Effective Velocity**: {pitcher_data.get('Effective_Velocity_Composite', 0):.1f} mph perceived ({pitcher_data.get('release_speed', 0):.1f} mph actual) → {self._ev_interpretation(pitcher_data)}
- **Nash Score**: {pitcher_data.get('Nash_Equilibrium_Score', 0):.0f}/100 → Pitch mix {self._nash_interpretation(pitcher_data.get('Nash_Equilibrium_Score', 0))}
- **Arsenal Synergy Score**: {pitcher_data.get('Arsenal_Synergy_Score', 0):.0f}/100

## Biomechanics:
- **Release Point SD**: {pitcher_data.get('Release_Point_SD', 0):.1f} inches ({pitcher_data.get('Release_Strategy_Classification', 'Unknown')} strategy) → {self._release_interpretation(pitcher_data)}
- **Fatigue Units**: {pitcher_data.get('Fatigue_Units_Total', 0):.0f} FU over 3yr ({self._fu_percentile(pitcher_data)}) → {self._durability_interpretation(pitcher_data)}
- **Extension**: {pitcher_data.get('Extension_ft', 0):.1f} ft ({self._extension_percentile(pitcher_data)}) → {self._extension_interpretation(pitcher_data)}

## Cognitive Load & Deception:
- **Swing Decision Disruption**: {pitcher_data.get('Swing_Decision_Disruption_Index', 0):.1f} → {self._disruption_interpretation(pitcher_data)}
- **Cognitive Load Score**: {pitcher_data.get('Cognitive_Load_Score', 0):.0f}/100

## The Opportunity:
- **Closer Talent Score**: {self._closer_talent_score(pitcher_data):.0f}/100 ({self._talent_tier(pitcher_data)})
- **2025 Saves**: {pitcher_data.get('Saves', 0)} (Role mismatch: {self._role_mismatch_level(pitcher_data)})
- **Projected AAV**: ${pitcher_data.get('Projected_AAV', 0):.1f}M (Market sees: {self._market_perception(pitcher_data)})
- **True Value**: ${self._true_value(pitcher_data):.1f}M ({self._value_interpretation(pitcher_data)})
- **Bust Risk**: {pitcher_data.get('Bust_Risk_Score', 0):.0f}/100 ({self._risk_interpretation(pitcher_data)})

## RECOMMENDATION:
{self._generate_recommendation(pitcher_data)}

---
"""
        return profile

    def _classify_vaa_percentile(self, vaa: float) -> str:
        """Classify VAA into percentile."""
        abs_vaa = abs(vaa)
        if abs_vaa < 4:
            return "Top 5% flat angle"
        elif abs_vaa < 5:
            return "Top 20% flat angle"
        elif abs_vaa < 6:
            return "Average"
        else:
            return "Steep angle"

    def _vaa_interpretation(self, vaa: float) -> str:
        """Interpret VAA for pitcher profile."""
        abs_vaa = abs(vaa)
        if abs_vaa < 4:
            return "ELITE fastball 'rise' potential"
        elif abs_vaa < 5:
            return "Good carry on fastball"
        elif abs_vaa < 6:
            return "Average plane"
        else:
            return "Downhill plane advantage"

    def _ssw_interpretation(self, ssw: float) -> str:
        """Interpret SSW movement."""
        if ssw > 4:
            return "Elite unexplained movement - natural cutter/sink action"
        elif ssw > 3:
            return "Significant SSW advantage"
        elif ssw > 2:
            return "Above average SSW effect"
        else:
            return "Typical spin-based movement"

    def _tunneling_interpretation(self, score: float) -> str:
        """Interpret tunneling score."""
        if score > 85:
            return "Elite deception at decision point"
        elif score > 70:
            return "Strong tunneling between pitches"
        elif score > 55:
            return "Adequate pitch pairing"
        else:
            return "Limited tunneling"

    def _arsenal_combo_interpretation(self, pitcher_data: Dict) -> str:
        """Interpret arsenal combination."""
        has_gyro = pitcher_data.get('Has_Gyro', False)
        has_sweeper = pitcher_data.get('Has_Sweeper', False)

        if has_gyro and has_sweeper:
            return "ELITE COMBO (Luke Jackson profile)"
        elif has_gyro:
            return "Has gyro, missing sweeper = INCOMPLETE arsenal"
        elif has_sweeper:
            return "Has sweeper, could add gyro"
        else:
            return "Traditional breaking ball profile"

    def _ev_interpretation(self, pitcher_data: Dict) -> str:
        """Interpret effective velocity."""
        ev = pitcher_data.get('Effective_Velocity_Composite', 0)
        actual_v = pitcher_data.get('release_speed', 0)
        diff = ev - actual_v

        if diff > 3:
            return "Inside targeting master"
        elif diff > 1:
            return "Good location optimization"
        else:
            return "Standard velocity perception"

    def _nash_interpretation(self, nash_score: float) -> str:
        """Interpret Nash equilibrium score."""
        if nash_score < 30:
            return "ALREADY OPTIMIZED"
        elif nash_score < 50:
            return "well balanced"
        elif nash_score < 70:
            return "has room for improvement"
        else:
            return "NEEDS REBALANCING (easy gains available)"

    def _release_interpretation(self, pitcher_data: Dict) -> str:
        """Interpret release point strategy."""
        strategy = pitcher_data.get('Release_Strategy_Classification', 'Unknown')

        if strategy == 'Consistency':
            return "Tunneling optimized"
        elif strategy == 'Variability':
            return "Deception through arm slot changes"
        else:
            return "Inconsistent mechanics (red flag)"

    def _fu_percentile(self, pitcher_data: Dict) -> str:
        """Calculate FU percentile."""
        fu_per_game = pitcher_data.get('FU_Per_Game_Avg', 30)

        if fu_per_game < 25:
            return "Bottom 25%"
        elif fu_per_game < 35:
            return "Below average"
        elif fu_per_game < 45:
            return "Average"
        else:
            return "Top 25% (high stress)"

    def _durability_interpretation(self, pitcher_data: Dict) -> str:
        """Interpret durability metrics."""
        durability = pitcher_data.get('Durability_Score', 50)

        if durability > 75:
            return "DURABLE arm"
        elif durability > 60:
            return "Good durability"
        elif durability > 45:
            return "Average durability"
        else:
            return "Injury risk concerns"

    def _extension_percentile(self, pitcher_data: Dict) -> str:
        """Calculate extension percentile."""
        extension = pitcher_data.get('Extension_ft', 6.0)

        if extension > 6.8:
            return "Top 5%"
        elif extension > 6.5:
            return "Top 20%"
        elif extension > 6.2:
            return "Average"
        else:
            return "Below average"

    def _extension_interpretation(self, pitcher_data: Dict) -> str:
        """Interpret extension metrics."""
        extension = pitcher_data.get('Extension_ft', 6.0)

        if extension > 6.8:
            return "Elite plate advantage"
        elif extension > 6.5:
            return "Significant plate advantage"
        else:
            return "Standard extension"

    def _disruption_interpretation(self, pitcher_data: Dict) -> str:
        """Interpret swing decision disruption."""
        disruption = pitcher_data.get('Swing_Decision_Disruption_Index', 0)

        if disruption > 15:
            return "Elite timing disruption"
        elif disruption > 10:
            return "Strong cognitive load"
        else:
            return "Standard sequencing"

    def _closer_talent_score(self, pitcher_data: Dict) -> float:
        """Calculate closer talent score."""
        k_rate = pitcher_data.get('K_pct', 25)
        whiff_rate = pitcher_data.get('Whiff_pct', 25)
        stuff_plus = pitcher_data.get('Stuff_plus', 100)
        diamond = pitcher_data.get('Diamond_Score', 50)

        # Weighted average
        score = (
            (k_rate / 40) * 25 +
            (whiff_rate / 40) * 25 +
            ((stuff_plus - 80) / 40) * 25 +
            (diamond / 100) * 25
        )

        return min(100, max(0, score))

    def _talent_tier(self, pitcher_data: Dict) -> str:
        """Classify talent tier."""
        talent = self._closer_talent_score(pitcher_data)

        if talent > 80:
            return "ELITE"
        elif talent > 70:
            return "Above Average"
        elif talent > 55:
            return "Average"
        else:
            return "Below Average"

    def _role_mismatch_level(self, pitcher_data: Dict) -> str:
        """Classify role mismatch."""
        mismatch = pitcher_data.get('Role_Mismatch_Score', 0)

        if mismatch > 70:
            return "VERY HIGH"
        elif mismatch > 50:
            return "HIGH"
        elif mismatch > 30:
            return "Moderate"
        else:
            return "Low"

    def _market_perception(self, pitcher_data: Dict) -> str:
        """Describe market perception."""
        saves = pitcher_data.get('Saves', 0)
        age = pitcher_data.get('Age', 30)
        injury_history = pitcher_data.get('IL_days_3yr', 0)

        if saves < 5:
            if injury_history > 60:
                return "setup guy with injury history"
            else:
                return "middle reliever/setup man"
        elif saves < 15:
            return "partial closer, inconsistent"
        else:
            return "proven closer"

    def _true_value(self, pitcher_data: Dict) -> float:
        """Calculate true value in millions."""
        diamond = pitcher_data.get('Diamond_Score', 50)
        bust_risk = pitcher_data.get('Bust_Risk_Score', 50)

        # Adjust for risk
        risk_adjusted = diamond * (1 - bust_risk / 150)

        if risk_adjusted > 80:
            return 12
        elif risk_adjusted > 70:
            return 9
        elif risk_adjusted > 60:
            return 6
        elif risk_adjusted > 50:
            return 4
        else:
            return 2.5

    def _value_interpretation(self, pitcher_data: Dict) -> str:
        """Interpret value proposition."""
        true_value = self._true_value(pitcher_data)
        projected = pitcher_data.get('Projected_AAV', 5)
        delta = true_value - projected

        if delta > 5:
            return "MASSIVE VALUE OPPORTUNITY"
        elif delta > 3:
            return "Strong value play"
        elif delta > 1:
            return "Modest upside"
        elif delta > -1:
            return "Fair value"
        else:
            return "Overpriced"

    def _risk_interpretation(self, pitcher_data: Dict) -> str:
        """Interpret bust risk."""
        risk = pitcher_data.get('Bust_Risk_Score', 50)

        if risk < 25:
            return "Low risk, durable profile"
        elif risk < 40:
            return "Manageable risk"
        elif risk < 60:
            return "Moderate injury concerns"
        else:
            return "HIGH RISK - injury red flags"

    def _generate_recommendation(self, pitcher_data: Dict) -> str:
        """Generate signing recommendation."""
        name = pitcher_data.get('player_name', 'Player')
        true_value = self._true_value(pitcher_data)
        diamond = pitcher_data.get('Diamond_Score', 50)
        bust_risk = pitcher_data.get('Bust_Risk_Score', 50)

        # Determine contract recommendation
        if true_value > 10:
            years = 3
            total = true_value * years * 0.95  # Slight discount for multi-year
        elif true_value > 7:
            years = 2
            total = true_value * years * 0.98
        else:
            years = 2
            total = true_value * years

        # Generate recommendation text
        rec = f"**Sign {years}yr/${total:.0f}M** (${true_value:.1f}M AAV). "

        # Add reasoning
        if diamond > 80 and bust_risk < 30:
            rec += f"Physics profile indicates elite closer talent stuck in setup role. "
            rec += f"Low injury risk with elite deception metrics makes this a premium value play."
        elif diamond > 75 and bust_risk < 40:
            rec += f"Strong physics edge with manageable risk profile. "
            rec += f"Role optimization could unlock significant value."
        elif diamond > 70:
            rec += f"Good underlying metrics with upside potential. "
            rec += f"Worth a buy-low opportunity."
        else:
            rec += f"Solid contributor with depth value."

        return rec

    def _yes_no(self, value: bool) -> str:
        """Convert boolean to YES/NO."""
        return "YES" if value else "NO"

    def generate_executive_summary(self, all_pitchers: pd.DataFrame,
                                   hidden_gems: pd.DataFrame,
                                   categories: Dict[str, pd.DataFrame]) -> str:
        """
        Generate executive summary report.

        Args:
            all_pitchers: All analyzed pitchers
            hidden_gems: Filtered hidden gems
            categories: Pitcher categories

        Returns:
            Formatted markdown executive summary
        """
        summary = f"""
# RELIEVER FREE AGENT MARKET INTELLIGENCE 2025
## Executive Summary - Advanced Physics & Biomechanics Analysis

**Analysis Date**: {datetime.now().strftime('%Y-%m-%d')}
**Total Relievers Analyzed**: {len(all_pitchers)}
**Hidden Gems Identified**: {len(hidden_gems)}

---

## Key Findings

### Market Inefficiencies Detected:

1. **Physics-Based Edges**: {len(all_pitchers[all_pitchers['Diamond_Score'] > 75])} relievers with elite physics metrics underutilized
2. **Gyro/Sweeper Combos**: {len(all_pitchers[all_pitchers['Has_Gyro_Sweeper_Combo'] == True])} pitchers with rare arsenal combinations
3. **Role Mismatches**: {len(all_pitchers[all_pitchers['Role_Mismatch_Score'] > 70])} elite talents stuck in setup roles

### Top Value Opportunities:

"""

        # Add top 5 hidden gems
        if not hidden_gems.empty:
            top_gems = hidden_gems.head(5)
            for idx, (_, pitcher) in enumerate(top_gems.iterrows(), 1):
                summary += f"{idx}. **{pitcher.get('player_name', 'Unknown')}** - "
                summary += f"Diamond Score: {pitcher.get('Diamond_Score', 0):.0f}/100, "
                summary += f"Value Score: {pitcher.get('Value_Score', 0):.0f}/100, "
                summary += f"Projected: ${pitcher.get('Projected_AAV', 0):.1f}M → "
                summary += f"True Value: ${self._true_value(pitcher):.1f}M\n"

        summary += f"""
---

## Category Breakdown:

"""

        # Add category counts
        for category, df in categories.items():
            if not df.empty:
                summary += f"- **{category.replace('_', ' ')}**: {len(df)} pitchers\n"

        summary += f"""
---

## Physics Insights:

### Vertical Approach Angle (VAA) Optimization:
- **Flat VAA Throwers** (<4°): {len(all_pitchers[all_pitchers['VAA_FB_avg'].abs() < 4])} pitchers
  - Optimal for high fastballs with "rise" effect
  - Market undervalues flat VAA + elite extension combinations

### Seam-Shifted Wake (SSW) Detection:
- **Elite SSW Movement** (>3 inches): {len(all_pitchers[all_pitchers['SSW_Movement_FB'] > 3])} pitchers
  - Unconscious stuff advantage market doesn't see in traditional metrics
  - Natural cutting/sinking action independent of spin rate

### Tunneling Excellence:
- **Elite Tunneling** (>85/100): {len(all_pitchers[all_pitchers['Tunneling_Score'] > 85])} pitchers
  - Superior deception at hitter decision point
  - Often paired with consistent release point strategy

---

## Arsenal Synergy Findings:

### Emerging Arsenal Profiles:
- **Gyro + Sweeper Combo**: {len(all_pitchers[all_pitchers['Has_Gyro_Sweeper_Combo'] == True])} pitchers (Luke Jackson profile)
- **High Cognitive Load** (>75): {len(all_pitchers[all_pitchers['Cognitive_Load_Score'] > 75])} pitchers with elite timing disruption

### Pitch Mix Optimization:
- **Already Optimized** (Nash <30): {len(all_pitchers[all_pitchers['Nash_Equilibrium_Score'] < 30])} pitchers
- **Easy Gains Available** (Nash >70): {len(all_pitchers[all_pitchers['Nash_Equilibrium_Score'] > 70])} pitchers with suboptimal mix

---

## Biomechanics & Durability:

### Release Point Strategy:
- **Consistency Strategy** (<3" SD): {len(all_pitchers[all_pitchers['Release_Strategy_Classification'] == 'Consistency'])} pitchers
- **Variability Strategy** (>6" SD): {len(all_pitchers[all_pitchers['Release_Strategy_Classification'] == 'Variability'])} pitchers
- **Middle Ground** (RED FLAG): {len(all_pitchers[all_pitchers['Release_Strategy_Classification'] == 'Middle'])} pitchers

### Durability Profile:
- **Low Risk** (Bust Risk <30): {len(all_pitchers[all_pitchers['Bust_Risk_Score'] < 30])} pitchers
- **Moderate Risk** (30-50): {len(all_pitchers[(all_pitchers['Bust_Risk_Score'] >= 30) & (all_pitchers['Bust_Risk_Score'] < 50)])} pitchers
- **High Risk** (>50): {len(all_pitchers[all_pitchers['Bust_Risk_Score'] >= 50])} pitchers

---

## Recommendations:

### Tier 1 - Immediate Targets (Elite Hidden Gems):
"""

        # Add Tier 1 recommendations
        tier1 = categories.get('Elite_Hidden_Gems', pd.DataFrame())
        if not tier1.empty:
            for _, pitcher in tier1.head(3).iterrows():
                summary += f"- **{pitcher.get('player_name', 'Unknown')}**: {self._generate_recommendation(pitcher)}\n"
        else:
            summary += "- No elite hidden gems identified in current dataset\n"

        summary += """
### Tier 2 - Value Plays:
"""

        # Add Tier 2 recommendations
        tier2 = categories.get('Value_Plays', pd.DataFrame())
        if not tier2.empty:
            for _, pitcher in tier2.head(3).iterrows():
                summary += f"- **{pitcher.get('player_name', 'Unknown')}**: {self._generate_recommendation(pitcher)}\n"

        summary += """
### Tier 3 - Avoid List:
"""

        # Add avoid list
        avoid = categories.get('Avoid', pd.DataFrame())
        if not avoid.empty:
            for _, pitcher in avoid.head(3).iterrows():
                summary += f"- **{pitcher.get('player_name', 'Unknown')}**: High bust risk ({pitcher.get('Bust_Risk_Score', 0):.0f}/100) or poor physics profile\n"

        summary += """
---

## Methodology Note:

This analysis combines:
- **Pitch Physics**: VAA, SSW effects, tunneling metrics from Statcast data
- **Arsenal Synergy**: Gyro/sweeper detection, effective velocity, cognitive load
- **Biomechanics**: Release point strategy, fatigue units, extension optimization
- **Game Theory**: Nash equilibrium modeling for pitch mix optimization

All metrics are physics-based and capture edges invisible to traditional stats.

---
"""

        return summary

    def export_detailed_rankings(self, all_pitchers: pd.DataFrame, filename: str):
        """
        Export detailed rankings to CSV.

        Args:
            all_pitchers: All analyzed pitchers
            filename: Output CSV filename
        """
        # Select key columns for export
        export_columns = [
            'player_name', 'Diamond_Score', 'Diamond_Rank', 'Value_Score', 'Value_Rank',
            'Bust_Risk_Score', 'Projected_AAV',
            'VAA_FB_avg', 'SSW_Movement_FB', 'Tunneling_Score',
            'Arsenal_Synergy_Score', 'Cognitive_Load_Score', 'Has_Gyro_Sweeper_Combo',
            'Durability_Score', 'Role_Mismatch_Score',
            'K_pct', 'Whiff_pct', 'Saves', 'Appearances'
        ]

        # Filter to available columns
        available_columns = [col for col in export_columns if col in all_pitchers.columns]

        export_df = all_pitchers[available_columns].copy()

        # Sort by Diamond Rank
        export_df = export_df.sort_values('Diamond_Rank')

        # Export to CSV
        export_df.to_csv(filename, index=False)
        print(f"Detailed rankings exported to {filename}")


if __name__ == "__main__":
    # Test with sample data
    sample_pitcher = {
        'player_name': 'Hunter Harvey',
        'player_id': 663961,
        'Diamond_Score': 85,
        'Value_Score': 88,
        'Bust_Risk_Score': 25,
        'Projected_AAV': 4.0,
        'VAA_FB_avg': -3.2,
        'SSW_Movement_FB': 4.1,
        'Tunneling_Score': 82,
        'Arsenal_Synergy_Score': 70,
        'Has_Gyro': True,
        'Has_Sweeper': False,
        'Effective_Velocity_Composite': 97.2,
        'release_speed': 95.8,
        'Nash_Equilibrium_Score': 42,
        'Release_Point_SD': 2.1,
        'Release_Strategy_Classification': 'Consistency',
        'Durability_Score': 75,
        'Extension_ft': 6.8,
        'Swing_Decision_Disruption_Index': 12.5,
        'Cognitive_Load_Score': 65,
        'K_pct': 32,
        'Whiff_pct': 35,
        'Stuff_plus': 115,
        'Saves': 0,
        'Role_Mismatch_Score': 75,
        'Age': 29,
        'IL_days_3yr': 45,
    }

    reporter = AdvancedReporter()

    print("Generating pitcher profile...")
    profile = reporter.generate_pitcher_profile(sample_pitcher)
    print(profile)
