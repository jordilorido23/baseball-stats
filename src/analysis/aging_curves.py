"""
Aging curves analysis for player projections and contract valuation.
Uses historical data to model position-specific performance decline.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats


class AgingCurveAnalyzer:
    """
    Analyze aging patterns and project future performance.

    Uses historical data to build position-specific aging curves
    for contract evaluation and multi-year projections.
    """

    def __init__(self):
        """Initialize aging curve analyzer."""
        # Default aging curves based on historical research
        # Values represent annual decline rate (multiplicative)
        self.default_aging_curves = {
            # Position players (based on wRC+ / WAR)
            'C': {
                'peak_age': 27,
                'decline_rate': 0.93,  # 7% annual decline post-peak
                'cliff_age': 33  # Accelerated decline starts
            },
            '1B': {
                'peak_age': 28,
                'decline_rate': 0.95,
                'cliff_age': 34
            },
            '2B': {
                'peak_age': 27,
                'decline_rate': 0.94,
                'cliff_age': 33
            },
            '3B': {
                'peak_age': 27,
                'decline_rate': 0.94,
                'cliff_age': 33
            },
            'SS': {
                'peak_age': 27,
                'decline_rate': 0.94,
                'cliff_age': 32
            },
            'OF': {
                'peak_age': 27,
                'decline_rate': 0.95,
                'cliff_age': 34
            },
            'DH': {
                'peak_age': 29,
                'decline_rate': 0.96,
                'cliff_age': 35
            },
            # Pitchers
            'SP': {
                'peak_age': 28,
                'decline_rate': 0.92,  # 8% annual decline
                'cliff_age': 33
            },
            'RP': {
                'peak_age': 27,
                'decline_rate': 0.90,  # 10% annual decline
                'cliff_age': 32
            }
        }

    def project_performance(
        self,
        current_performance: float,
        current_age: int,
        position: str,
        years_forward: int = 5,
        metric_type: str = 'WAR'
    ) -> List[Dict]:
        """
        Project future performance using aging curves.

        Args:
            current_performance: Current season performance level
            current_age: Player's current age
            position: Position
            years_forward: Number of years to project
            metric_type: Type of metric (WAR, wRC+, ERA+, etc.)

        Returns:
            List of dictionaries with yearly projections
        """
        curve = self.default_aging_curves.get(position, self.default_aging_curves['OF'])

        projections = []

        for year in range(years_forward):
            age = current_age + year
            years_from_peak = age - curve['peak_age']

            # Calculate decline factor
            if years_from_peak <= 0:
                # Pre-peak: slight improvement
                decline_factor = 1.0 + (years_from_peak * -0.02)  # 2% improvement per year
            elif age < curve['cliff_age']:
                # Normal decline
                decline_factor = curve['decline_rate'] ** years_from_peak
            else:
                # Post-cliff: accelerated decline
                normal_years = curve['cliff_age'] - curve['peak_age']
                cliff_years = age - curve['cliff_age']
                normal_decline = curve['decline_rate'] ** normal_years
                cliff_decline = 0.88 ** cliff_years  # 12% annual decline post-cliff
                decline_factor = normal_decline * cliff_decline

            # Calculate projected performance
            projected = current_performance * decline_factor

            # Floor for counting stats (can't be negative)
            if metric_type == 'WAR':
                projected = max(0, projected)
            elif metric_type in ['wRC+', 'ERA+', 'OPS+']:
                projected = max(70, projected)  # Floor at replacement level

            projections.append({
                'year': year + 1,
                'age': age,
                'projected_value': round(projected, 2),
                'decline_factor': round(decline_factor, 3),
                'years_from_peak': years_from_peak
            })

        return projections

    def calculate_contract_war(
        self,
        current_war: float,
        current_age: int,
        position: str,
        contract_years: int
    ) -> Dict:
        """
        Calculate total WAR over a contract period.

        Args:
            current_war: Current season WAR
            current_age: Player's age
            position: Position
            contract_years: Length of contract

        Returns:
            Dictionary with contract WAR analysis
        """
        projections = self.project_performance(
            current_war,
            current_age,
            position,
            contract_years,
            'WAR'
        )

        total_war = sum(p['projected_value'] for p in projections)
        peak_years = sum(1 for p in projections if p['projected_value'] >= current_war * 0.9)

        curve = self.default_aging_curves.get(position, self.default_aging_curves['OF'])

        return {
            'total_war': round(total_war, 1),
            'avg_war_per_year': round(total_war / contract_years, 1),
            'peak_years': peak_years,
            'decline_years': contract_years - peak_years,
            'years_to_cliff': max(0, curve['cliff_age'] - current_age),
            'cliff_during_contract': current_age + contract_years > curve['cliff_age'],
            'year_by_year': projections
        }

    def estimate_surplus_value(
        self,
        projected_war_by_year: List[float],
        contract_aav: float,
        dollars_per_war: float = 8.0,
        inflation_rate: float = 0.05
    ) -> Dict:
        """
        Calculate surplus value (projected value - contract cost).

        Args:
            projected_war_by_year: List of projected WAR values
            contract_aav: Average annual value of contract (millions)
            dollars_per_war: Current $/WAR on market
            inflation_rate: Annual inflation rate for $/WAR

        Returns:
            Dictionary with surplus value analysis
        """
        years = len(projected_war_by_year)
        total_value = 0
        total_cost = contract_aav * years

        yearly_analysis = []

        for year, war in enumerate(projected_war_by_year):
            # Inflate $/WAR
            year_dollars_per_war = dollars_per_war * ((1 + inflation_rate) ** year)

            # Market value
            market_value = war * year_dollars_per_war

            # Surplus
            surplus = market_value - contract_aav

            total_value += market_value

            yearly_analysis.append({
                'year': year + 1,
                'war': round(war, 1),
                'market_value_millions': round(market_value, 1),
                'contract_cost_millions': round(contract_aav, 1),
                'surplus_millions': round(surplus, 1)
            })

        total_surplus = total_value - total_cost

        return {
            'total_surplus_millions': round(total_surplus, 1),
            'total_market_value_millions': round(total_value, 1),
            'total_cost_millions': round(total_cost, 1),
            'surplus_per_year': round(total_surplus / years, 1),
            'value_ratio': round(total_value / total_cost, 2) if total_cost > 0 else 0,
            'yearly_breakdown': yearly_analysis
        }

    def compare_contract_scenarios(
        self,
        current_war: float,
        current_age: int,
        position: str,
        scenarios: List[Dict]
    ) -> pd.DataFrame:
        """
        Compare multiple contract scenarios (different years/AAV).

        Args:
            current_war: Current season WAR
            current_age: Player age
            position: Position
            scenarios: List of dicts with 'years' and 'aav' keys

        Returns:
            DataFrame comparing scenarios
        """
        results = []

        for i, scenario in enumerate(scenarios):
            years = scenario['years']
            aav = scenario['aav']

            # Get WAR projections
            contract_analysis = self.calculate_contract_war(
                current_war,
                current_age,
                position,
                years
            )

            war_by_year = [p['projected_value'] for p in contract_analysis['year_by_year']]

            # Get surplus value
            surplus_analysis = self.estimate_surplus_value(
                war_by_year,
                aav
            )

            results.append({
                'scenario': f"{years}yr/${aav}M",
                'years': years,
                'aav_millions': aav,
                'total_cost_millions': aav * years,
                'total_war': contract_analysis['total_war'],
                'avg_war_per_year': contract_analysis['avg_war_per_year'],
                'total_surplus_millions': surplus_analysis['total_surplus_millions'],
                'surplus_per_year': surplus_analysis['surplus_per_year'],
                'value_ratio': surplus_analysis['value_ratio'],
                'cliff_during_contract': contract_analysis['cliff_during_contract']
            })

        return pd.DataFrame(results)

    def plot_aging_curve(
        self,
        position: str,
        current_age: int,
        current_performance: float = 100,
        years_back: int = 5,
        years_forward: int = 10,
        metric_name: str = 'wRC+'
    ) -> plt.Figure:
        """
        Visualize aging curve for a position.

        Args:
            position: Position to plot
            current_age: Player's current age
            current_performance: Current performance level (indexed to 100)
            years_back: Years of history to show
            years_forward: Years of projection
            metric_name: Name of metric for labels

        Returns:
            Matplotlib figure
        """
        curve = self.default_aging_curves.get(position, self.default_aging_curves['OF'])

        # Generate age range
        ages = list(range(current_age - years_back, current_age + years_forward + 1))
        performance = []

        for age in ages:
            years_from_current = age - current_age
            if years_from_current <= 0:
                # Past/current
                years_from_peak = current_age - curve['peak_age']
                if years_from_peak > 0:
                    current_decline = curve['decline_rate'] ** years_from_peak
                else:
                    current_decline = 1.0

                age_decline = curve['decline_rate'] ** (age - curve['peak_age'])
                value = current_performance * (age_decline / current_decline)
            else:
                # Future projection
                projections = self.project_performance(
                    current_performance,
                    current_age,
                    position,
                    years_from_current,
                    metric_name
                )
                value = projections[-1]['projected_value']

            performance.append(max(70, value))  # Floor at replacement

        # Create plot
        fig, ax = plt.subplots(figsize=(12, 7))

        # Plot curve
        ax.plot(ages, performance, 'b-', linewidth=2.5, label=f'{position} Aging Curve')

        # Highlight current age
        current_idx = years_back
        ax.scatter(
            [current_age],
            [performance[current_idx]],
            s=200,
            c='red',
            zorder=5,
            label=f'Current Age ({current_age})'
        )

        # Shade peak years
        peak_age = curve['peak_age']
        peak_range = 2
        ax.axvspan(
            peak_age - peak_range,
            peak_age + peak_range,
            alpha=0.2,
            color='green',
            label=f'Peak Years (~{peak_age})'
        )

        # Shade cliff years
        cliff_age = curve['cliff_age']
        ax.axvspan(
            cliff_age,
            max(ages),
            alpha=0.2,
            color='red',
            label=f'Cliff Age ({cliff_age}+)'
        )

        # Add reference lines
        ax.axhline(100, linestyle='--', color='gray', alpha=0.5, label='Average (100)')
        ax.axvline(current_age, linestyle=':', color='red', alpha=0.3)

        ax.set_xlabel('Age', fontsize=12, fontweight='bold')
        ax.set_ylabel(f'{metric_name} (Indexed)', fontsize=12, fontweight='bold')
        ax.set_title(
            f'{position} Aging Curve: Performance Projection',
            fontsize=14,
            fontweight='bold',
            pad=20
        )
        ax.legend(loc='upper right', fontsize=10)
        ax.grid(alpha=0.3)

        plt.tight_layout()
        return fig

    def identify_risky_contracts(
        self,
        fa_df: pd.DataFrame,
        min_years: int = 5,
        cliff_threshold: int = 2
    ) -> pd.DataFrame:
        """
        Identify free agents likely to get risky long-term contracts.

        Args:
            fa_df: Free agent DataFrame with age and position
            min_years: Minimum contract length to flag
            cliff_threshold: Years from cliff to consider risky

        Returns:
            DataFrame of risky contract scenarios
        """
        risky_fas = []

        for _, player in fa_df.iterrows():
            age = player.get('age_2025', 30)
            position = player.get('position', 'OF')

            curve = self.default_aging_curves.get(position, self.default_aging_curves['OF'])

            years_to_cliff = curve['cliff_age'] - age

            # Flag if player would hit cliff during typical contract
            if years_to_cliff <= cliff_threshold + min_years:
                risky_fas.append({
                    'player_name': player.get('player_name', 'Unknown'),
                    'position': position,
                    'current_age': age,
                    'cliff_age': curve['cliff_age'],
                    'years_to_cliff': years_to_cliff,
                    'risk_level': 'High' if years_to_cliff <= 3 else 'Medium',
                    'recommended_max_years': min(years_to_cliff - 1, min_years)
                })

        return pd.DataFrame(risky_fas).sort_values('years_to_cliff', ascending=True)
