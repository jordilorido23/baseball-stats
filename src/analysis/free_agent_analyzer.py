"""
Free agent analysis module for front office decision-making.
Combines performance metrics, expected stats, and contract valuations.
"""
import pandas as pd
import numpy as np
from typing import List, Optional, Dict, Tuple
import matplotlib.pyplot as plt
import seaborn as sns


class FreeAgentAnalyzer:
    """
    Analyze free agents for front office evaluation.

    Combines:
    - Expected stats analysis (luck vs skill)
    - Quality of contact metrics
    - Aging projections
    - Contract value estimates
    """

    def __init__(self, dollars_per_war: float = 8.0):
        """
        Initialize free agent analyzer.

        Args:
            dollars_per_war: Current $/WAR on FA market (in millions)
        """
        self.dollars_per_war = dollars_per_war

        # Position-specific aging curves (annual decline rates)
        self.aging_curves = {
            'SP': 0.92,   # Starting pitchers decline ~8% per year
            'RP': 0.90,   # Relievers decline ~10% per year
            'C': 0.93,    # Catchers decline ~7% per year
            '1B': 0.95,   # First basemen
            '2B': 0.94,   # Second basemen
            '3B': 0.94,   # Third basemen
            'SS': 0.94,   # Shortstops
            'OF': 0.95,   # Outfielders
            'DH': 0.96    # Designated hitters
        }

    def analyze_free_agent_class(
        self,
        performance_df: pd.DataFrame,
        fa_list_df: pd.DataFrame,
        player_name_col: str = 'Name'
    ) -> pd.DataFrame:
        """
        Comprehensive analysis of free agent class.

        Args:
            performance_df: Player performance data with expected stats
            fa_list_df: Free agent list with contract info
            player_name_col: Column name for player names

        Returns:
            DataFrame with FA analysis
        """
        # Merge FA list with performance data
        fa_performance = performance_df.merge(
            fa_list_df,
            left_on=player_name_col,
            right_on='player_name',
            how='inner'
        )

        # Calculate expected stats gaps
        fa_performance = self._calculate_xstat_gaps(fa_performance)

        # Calculate value score
        fa_performance = self._calculate_fa_value_score(fa_performance)

        # Add contract tier classification
        fa_performance['contract_recommendation'] = fa_performance.apply(
            self._classify_contract_tier,
            axis=1
        )

        return fa_performance

    def _calculate_xstat_gaps(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate gaps between expected and actual stats."""
        result = df.copy()

        # Batting gaps
        if 'xba' in result.columns and 'ba' in result.columns:
            result['ba_gap'] = result['xba'] - result['ba']

        if 'xslg' in result.columns and 'slg' in result.columns:
            result['slg_gap'] = result['xslg'] - result['slg']

        if 'xwoba' in result.columns and 'woba' in result.columns:
            result['woba_gap'] = result['xwoba'] - result['woba']

        # Pitching gaps (if applicable)
        if 'xera' in result.columns and 'era' in result.columns:
            result['era_gap'] = result['xera'] - result['era']

        if 'xfip' in result.columns and 'fip' in result.columns:
            result['fip_gap'] = result['xfip'] - result['fip']

        return result

    def _calculate_fa_value_score(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate composite value score for free agents.

        Factors:
        1. Current performance level (40%)
        2. Expected stats gap / luck factor (30%)
        3. Age / remaining prime years (20%)
        4. Quality of contact / stuff (10%)
        """
        result = df.copy()
        result['fa_value_score'] = 0.0

        # Factor 1: Current performance (use WAR or wRC+/ERA+)
        if 'WAR' in result.columns:
            war_pct = result['WAR'].rank(pct=True)
            result['fa_value_score'] += war_pct * 40
        elif 'wRC+' in result.columns:  # For batters
            wrc_pct = result['wRC+'].rank(pct=True)
            result['fa_value_score'] += wrc_pct * 40

        # Factor 2: Expected stats gap (unlucky = higher score)
        if 'woba_gap' in result.columns:
            # Normalize: 0.030 gap = 30 points, scaled
            woba_component = (result['woba_gap'] / 0.030) * 30
            woba_component = woba_component.clip(lower=-30, upper=30)
            result['fa_value_score'] += woba_component

        # Factor 3: Age (younger = better)
        if 'age_2025' in result.columns:
            # Peak age varies by position, but generally 27-29
            # Bonus for players in their prime
            age_bonus = np.where(
                result['age_2025'] <= 30,
                (30 - result['age_2025']) * 2,
                np.where(
                    result['age_2025'] <= 33,
                    10 - (result['age_2025'] - 30) * 3,
                    0
                )
            )
            result['fa_value_score'] += age_bonus

        # Factor 4: Quality metrics
        if 'barrel_batted_rate' in result.columns:
            barrel_pct = result['barrel_batted_rate'].rank(pct=True)
            result['fa_value_score'] += barrel_pct * 10
        elif 'whiff_percent' in result.columns:  # For pitchers
            whiff_pct = result['whiff_percent'].rank(pct=True)
            result['fa_value_score'] += whiff_pct * 10

        return result

    def _classify_contract_tier(self, row: pd.Series) -> str:
        """
        Classify contract recommendation tier.

        Returns:
            One of: 'Max Contract', 'Premium', 'Mid-Tier', 'Value', 'Avoid'
        """
        score = row.get('fa_value_score', 50)
        age = row.get('age_2025', 30)

        if score >= 80 and age <= 30:
            return 'Max Contract'
        elif score >= 70:
            return 'Premium'
        elif score >= 55:
            return 'Mid-Tier'
        elif score >= 40:
            return 'Value'
        else:
            return 'Avoid'

    def project_multi_year_war(
        self,
        current_war: float,
        age: int,
        position: str,
        years: int
    ) -> List[float]:
        """
        Project WAR over multi-year contract using aging curves.

        Args:
            current_war: Most recent WAR
            age: Current age
            position: Position
            years: Contract length

        Returns:
            List of projected WAR by year
        """
        decline_rate = self.aging_curves.get(position, 0.94)

        projections = []
        for year in range(years):
            projected_war = current_war * (decline_rate ** year)
            # Floor at 0 WAR (can't be negative)
            projections.append(max(0, projected_war))

        return projections

    def estimate_contract_value(
        self,
        war_projections: List[float],
        include_inflation: bool = True,
        inflation_rate: float = 0.05
    ) -> Dict:
        """
        Estimate fair contract value based on WAR projections.

        Args:
            war_projections: Projected WAR by year
            include_inflation: Account for $/WAR inflation
            inflation_rate: Annual $/WAR inflation rate

        Returns:
            Dictionary with contract estimates
        """
        years = len(war_projections)
        total_value = 0

        for year, war in enumerate(war_projections):
            if include_inflation:
                year_dollars_per_war = self.dollars_per_war * ((1 + inflation_rate) ** year)
            else:
                year_dollars_per_war = self.dollars_per_war

            total_value += war * year_dollars_per_war

        aav = total_value / years if years > 0 else 0

        return {
            'total_value_millions': round(total_value, 1),
            'aav_millions': round(aav, 1),
            'total_projected_war': round(sum(war_projections), 1),
            'avg_war_per_year': round(sum(war_projections) / years, 1) if years > 0 else 0,
            'years': years,
            'war_by_year': [round(w, 1) for w in war_projections]
        }

    def identify_buy_low_candidates(
        self,
        fa_df: pd.DataFrame,
        min_woba_gap: float = 0.020,
        max_age: int = 32,
        min_quality_threshold: float = 0.10
    ) -> pd.DataFrame:
        """
        Identify buy-low free agents with strong underlying metrics.

        Args:
            fa_df: Free agent analysis DataFrame
            min_woba_gap: Minimum xwOBA gap (unlucky threshold)
            max_age: Maximum age to consider
            min_quality_threshold: Minimum barrel rate or other quality metric

        Returns:
            DataFrame of buy-low candidates
        """
        candidates = fa_df.copy()

        # Filter criteria
        filters = []

        # Must be unlucky (xStats > actual)
        if 'woba_gap' in candidates.columns:
            filters.append(candidates['woba_gap'] >= min_woba_gap)

        # Age filter
        if 'age_2025' in candidates.columns:
            filters.append(candidates['age_2025'] <= max_age)

        # Quality filter (either batting or pitching)
        if 'barrel_batted_rate' in candidates.columns:
            filters.append(candidates['barrel_batted_rate'] >= min_quality_threshold)
        elif 'whiff_percent' in candidates.columns:
            filters.append(candidates['whiff_percent'] >= 0.25)  # 25%+ whiff rate

        # Apply all filters
        if filters:
            mask = filters[0]
            for f in filters[1:]:
                mask = mask & f

            candidates = candidates[mask]

        # Sort by value score
        if 'fa_value_score' in candidates.columns:
            candidates = candidates.sort_values('fa_value_score', ascending=False)

        return candidates

    def identify_regression_risks(
        self,
        fa_df: pd.DataFrame,
        min_woba_gap: float = -0.020,
        quality_threshold: float = 0.08
    ) -> pd.DataFrame:
        """
        Identify free agents at risk of negative regression.

        Args:
            fa_df: Free agent analysis DataFrame
            min_woba_gap: Maximum negative gap (lucky threshold)
            quality_threshold: Maximum barrel rate for "lucky" classification

        Returns:
            DataFrame of regression risk candidates
        """
        candidates = fa_df.copy()

        filters = []

        # Overperforming (actual > xStats)
        if 'woba_gap' in candidates.columns:
            filters.append(candidates['woba_gap'] <= min_woba_gap)

        # Weak underlying metrics
        if 'barrel_batted_rate' in candidates.columns:
            filters.append(candidates['barrel_batted_rate'] <= quality_threshold)

        if filters:
            mask = filters[0]
            for f in filters[1:]:
                mask = mask & f

            candidates = candidates[mask]

        # Sort by gap size (most overperforming first)
        if 'woba_gap' in candidates.columns:
            candidates = candidates.sort_values('woba_gap', ascending=True)

        return candidates

    def create_fa_comparison_chart(
        self,
        fa_df: pd.DataFrame,
        x_col: str = 'woba',
        y_col: str = 'xwoba',
        label_col: str = 'player_name',
        highlight_players: Optional[List[str]] = None,
        title: str = '2025 Free Agents: Expected vs Actual Performance'
    ) -> plt.Figure:
        """
        Create scatter plot comparing actual vs expected stats.

        Args:
            fa_df: Free agent data
            x_col: Column for x-axis (actual stat)
            y_col: Column for y-axis (expected stat)
            label_col: Column for player labels
            highlight_players: List of players to highlight
            title: Chart title

        Returns:
            Matplotlib figure
        """
        fig, ax = plt.subplots(figsize=(12, 8))

        # All players
        ax.scatter(
            fa_df[x_col],
            fa_df[y_col],
            alpha=0.6,
            s=100,
            c='#1f77b4',
            edgecolors='white',
            linewidth=1.5
        )

        # Highlight specific players
        if highlight_players:
            highlight_df = fa_df[fa_df[label_col].isin(highlight_players)]
            ax.scatter(
                highlight_df[x_col],
                highlight_df[y_col],
                alpha=0.9,
                s=200,
                c='#d62728',
                edgecolors='black',
                linewidth=2,
                zorder=5
            )

            # Label highlighted players
            for _, row in highlight_df.iterrows():
                ax.annotate(
                    row[label_col],
                    (row[x_col], row[y_col]),
                    xytext=(5, 5),
                    textcoords='offset points',
                    fontsize=9,
                    fontweight='bold'
                )

        # Reference line (actual = expected)
        min_val = min(fa_df[x_col].min(), fa_df[y_col].min())
        max_val = max(fa_df[x_col].max(), fa_df[y_col].max())
        ax.plot([min_val, max_val], [min_val, max_val], 'k--', alpha=0.3, label='Perfect Match')

        # Shaded regions
        ax.fill_between(
            [min_val, max_val],
            [min_val - 0.020, max_val - 0.020],
            [min_val, max_val],
            alpha=0.1,
            color='red',
            label='Overperforming (Regression Risk)'
        )

        ax.fill_between(
            [min_val, max_val],
            [min_val, max_val],
            [min_val + 0.020, max_val + 0.020],
            alpha=0.1,
            color='green',
            label='Underperforming (Buy-Low)'
        )

        ax.set_xlabel(f'Actual {x_col.upper()}', fontsize=12, fontweight='bold')
        ax.set_ylabel(f'Expected {y_col.upper()}', fontsize=12, fontweight='bold')
        ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
        ax.legend(loc='upper left')
        ax.grid(alpha=0.3)

        plt.tight_layout()
        return fig

    def generate_fa_report(
        self,
        player_name: str,
        fa_df: pd.DataFrame,
        current_war: float,
        contract_years: int = 5
    ) -> Dict:
        """
        Generate comprehensive report for a single free agent.

        Args:
            player_name: Player name
            fa_df: Free agent analysis data
            current_war: Most recent WAR
            contract_years: Projected contract length

        Returns:
            Dictionary with complete FA analysis
        """
        player_data = fa_df[fa_df['player_name'] == player_name]

        if len(player_data) == 0:
            return {'error': f'Player {player_name} not found'}

        player = player_data.iloc[0]

        report = {
            'player_name': player_name,
            'position': player.get('position', 'N/A'),
            'age': player.get('age_2025', 'N/A'),
            'tier': player.get('tier', 'N/A'),
            'value_score': round(player.get('fa_value_score', 0), 1),
            'contract_recommendation': player.get('contract_recommendation', 'N/A')
        }

        # Expected stats analysis
        report['expected_stats'] = {
            'ba': player.get('ba', 'N/A'),
            'xba': player.get('xba', 'N/A'),
            'ba_gap': player.get('ba_gap', 'N/A'),
            'woba': player.get('woba', 'N/A'),
            'xwoba': player.get('xwoba', 'N/A'),
            'woba_gap': player.get('woba_gap', 'N/A')
        }

        # Quality metrics
        report['quality'] = {
            'barrel_rate': player.get('barrel_batted_rate', 'N/A'),
            'avg_exit_velo': player.get('avg_hit_speed', 'N/A'),
            'hard_hit_rate': player.get('hard_hit_percent', 'N/A')
        }

        # Contract projection
        position = player.get('position', 'OF')
        age = player.get('age_2025', 30)
        war_projections = self.project_multi_year_war(current_war, age, position, contract_years)
        contract_estimate = self.estimate_contract_value(war_projections)

        report['contract_projection'] = contract_estimate

        return report
