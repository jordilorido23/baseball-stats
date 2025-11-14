"""
Survival Analysis for Player Career Trajectories and Aging Curves.

This module implements survival analysis methods to model probabilistic
career outcomes: performance decline, aging cliffs, and retirement timing.

Unlike deterministic aging curves, survival models provide:
1. Probabilistic estimates of when decline occurs
2. Individual variation in aging patterns
3. Covariate effects (position, usage, injury history)
4. Censoring handling (active players haven't retired yet)

Key Models:
- Weibull AFT: Parametric accelerated failure time model
- Cox Proportional Hazards: Semi-parametric hazard model
- Kaplan-Meier: Non-parametric survival curves

Applications:
- Multi-year contract risk assessment
- Expected remaining career WAR
- Optimal retirement timing
- Position-specific aging patterns

References:
- Kleinbaum & Klein (2012): Survival Analysis: A Self-Learning Text
- Cox (1972): Regression models and life-tables
- Wei (1992): The accelerated failure time model
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Literal, Union
import warnings

try:
    from lifelines import WeibullAFTFitter, CoxPHFitter, KaplanMeierFitter
    from lifelines.utils import concordance_index
    LIFELINES_AVAILABLE = True
except ImportError:
    LIFELINES_AVAILABLE = False
    warnings.warn(
        "lifelines required for survival analysis. "
        "Install with: pip install lifelines"
    )

try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    PLOTTING_AVAILABLE = True
except ImportError:
    PLOTTING_AVAILABLE = False


class CareerSurvivalAnalyzer:
    """
    Analyze player career length and performance cliff timing.

    Uses survival analysis to model time-to-event outcomes:
    - Time until performance decline (WAR drops 50%+)
    - Time until retirement
    - Time until aging cliff (sharp performance drop)

    Handles censoring: active players are right-censored (event hasn't occurred yet).
    """

    def __init__(self, random_state: int = 42):
        """
        Initialize survival analyzer.

        Args:
            random_state: Random seed for reproducibility
        """
        if not LIFELINES_AVAILABLE:
            raise ImportError(
                "lifelines required for survival analysis. "
                "Install with: pip install lifelines"
            )

        self.random_state = random_state
        self.weibull_model = None
        self.cox_model = None
        self.km_fitter = KaplanMeierFitter()

    def prepare_survival_data(
        self,
        df: pd.DataFrame,
        player_id_col: str = 'playerid',
        age_col: str = 'Age',
        war_col: str = 'WAR',
        event_definition: Literal['decline', 'retirement', 'cliff'] = 'decline',
        decline_threshold: float = 0.5
    ) -> pd.DataFrame:
        """
        Prepare survival data with time-to-event and censoring.

        Args:
            df: Panel data with multiple seasons per player
            player_id_col: Player identifier
            age_col: Age column
            war_col: WAR or performance metric
            event_definition: Type of event to model
                - 'decline': WAR drops by threshold from peak
                - 'retirement': Last observed season
                - 'cliff': Single-season WAR drop exceeds threshold
            decline_threshold: Threshold for decline/cliff definition

        Returns:
            DataFrame with columns:
                - player_id
                - duration: Time from debut to event (years)
                - event: 1 if event occurred, 0 if censored
                - covariates (position, peak_war, etc.)
        """
        survival_data = []

        for player_id, player_df in df.groupby(player_id_col):
            player_df = player_df.sort_values(age_col)

            # Career metrics
            debut_age = player_df[age_col].min()
            last_age = player_df[age_col].max()
            career_length = last_age - debut_age + 1

            # Peak performance
            peak_war = player_df[war_col].max()
            peak_age = player_df.loc[player_df[war_col].idxmax(), age_col]

            # Event determination
            event_occurred = 0
            event_age = last_age

            if event_definition == 'decline':
                # Find first age where WAR < (1 - threshold) * peak_WAR
                decline_threshold_war = (1 - decline_threshold) * peak_war
                post_peak = player_df[player_df[age_col] > peak_age]

                if len(post_peak) > 0:
                    declined = post_peak[post_peak[war_col] < decline_threshold_war]
                    if len(declined) > 0:
                        event_occurred = 1
                        event_age = declined[age_col].min()

            elif event_definition == 'retirement':
                # Assume retirement if this is last observed season
                # In production: check if player appears in more recent seasons
                # For now: mark as censored (we don't observe retirement)
                event_occurred = 0
                event_age = last_age

            elif event_definition == 'cliff':
                # Single-season drop
                player_df['war_lag'] = player_df[war_col].shift(1)
                player_df['war_drop'] = (
                    player_df['war_lag'] - player_df[war_col]
                ) / player_df['war_lag']

                cliff_season = player_df[player_df['war_drop'] > decline_threshold]
                if len(cliff_season) > 0:
                    event_occurred = 1
                    event_age = cliff_season[age_col].min()

            # Duration: years from debut to event
            duration = event_age - debut_age

            # Get additional covariates (if available)
            position = player_df['Pos'].mode()[0] if 'Pos' in player_df.columns else None

            survival_data.append({
                'player_id': player_id,
                'duration': duration,
                'event': event_occurred,
                'debut_age': debut_age,
                'peak_age': peak_age,
                'peak_war': peak_war,
                'position': position,
                'career_length': career_length
            })

        return pd.DataFrame(survival_data)

    def fit_weibull_aft(
        self,
        df: pd.DataFrame,
        duration_col: str = 'duration',
        event_col: str = 'event',
        covariate_cols: Optional[List[str]] = None
    ) -> Dict:
        """
        Fit Weibull Accelerated Failure Time (AFT) model.

        AFT models: log(T) = β0 + β1*X1 + ... + σ*ε

        Interpretation: Covariates multiplicatively accelerate/decelerate time-to-event.
        - β > 0: covariate increases survival time (protective)
        - β < 0: covariate decreases survival time (harmful)

        Weibull distribution has closed-form hazard function:
        h(t) = λ * ρ * t^(ρ-1)
        - ρ > 1: increasing hazard (aging)
        - ρ < 1: decreasing hazard (burn-in)
        - ρ = 1: constant hazard (exponential)

        Args:
            df: Survival data from prepare_survival_data()
            duration_col: Duration column
            event_col: Event indicator (1=event, 0=censored)
            covariate_cols: Covariates to include

        Returns:
            Dictionary with model results and diagnostics
        """
        if covariate_cols is None:
            covariate_cols = ['peak_war', 'debut_age']

        # Prepare data
        available_covars = [c for c in covariate_cols if c in df.columns]
        model_df = df[[duration_col, event_col] + available_covars].dropna()

        # Fit Weibull AFT
        self.weibull_model = WeibullAFTFitter()
        self.weibull_model.fit(
            model_df,
            duration_col=duration_col,
            event_col=event_col
        )

        # Extract results
        summary = self.weibull_model.summary

        return {
            'model': self.weibull_model,
            'summary': summary,
            'aic': self.weibull_model.AIC_,
            'concordance_index': self.weibull_model.concordance_index_,
            'log_likelihood': self.weibull_model.log_likelihood_,
            'n_obs': len(model_df),
            'n_events': model_df[event_col].sum()
        }

    def fit_cox_model(
        self,
        df: pd.DataFrame,
        duration_col: str = 'duration',
        event_col: str = 'event',
        covariate_cols: Optional[List[str]] = None
    ) -> Dict:
        """
        Fit Cox Proportional Hazards model.

        Cox model: h(t|X) = h0(t) * exp(β1*X1 + ... + βp*Xp)

        Semi-parametric: baseline hazard h0(t) is not specified.
        Interpretation: Hazard ratios
        - exp(β) = 2: covariate doubles the hazard (bad for survival)
        - exp(β) = 0.5: covariate halves the hazard (good for survival)

        Args:
            df: Survival data
            duration_col: Duration column
            event_col: Event indicator
            covariate_cols: Covariates to include

        Returns:
            Dictionary with Cox model results
        """
        if covariate_cols is None:
            covariate_cols = ['peak_war', 'debut_age']

        # Prepare data
        available_covars = [c for c in covariate_cols if c in df.columns]
        model_df = df[[duration_col, event_col] + available_covars].dropna()

        # Fit Cox PH model
        self.cox_model = CoxPHFitter()
        self.cox_model.fit(
            model_df,
            duration_col=duration_col,
            event_col=event_col
        )

        # Extract results
        summary = self.cox_model.summary

        return {
            'model': self.cox_model,
            'summary': summary,
            'concordance_index': self.cox_model.concordance_index_,
            'log_likelihood': self.cox_model.log_likelihood_,
            'hazard_ratios': np.exp(self.cox_model.params_),
            'n_obs': len(model_df),
            'n_events': model_df[event_col].sum()
        }

    def predict_survival_curve(
        self,
        player_covariates: pd.DataFrame,
        model_type: Literal['weibull', 'cox'] = 'weibull',
        times: Optional[np.ndarray] = None
    ) -> pd.DataFrame:
        """
        Predict survival curves for specific players.

        Survival function S(t) = P(T > t) = probability of surviving past time t

        Args:
            player_covariates: DataFrame with player characteristics
            model_type: Which fitted model to use
            times: Time points for prediction (if None, uses default grid)

        Returns:
            DataFrame with survival probabilities at each time point
        """
        if model_type == 'weibull':
            if self.weibull_model is None:
                raise ValueError("Weibull model not fitted. Call fit_weibull_aft() first.")
            model = self.weibull_model
        elif model_type == 'cox':
            if self.cox_model is None:
                raise ValueError("Cox model not fitted. Call fit_cox_model() first.")
            model = self.cox_model
        else:
            raise ValueError(f"Unknown model_type: {model_type}")

        # Predict survival function
        if times is None:
            times = np.linspace(0, 20, 100)  # 0-20 years

        survival_curves = model.predict_survival_function(
            player_covariates, times=times
        )

        return survival_curves

    def estimate_median_survival(
        self,
        player_covariates: pd.DataFrame,
        model_type: Literal['weibull', 'cox'] = 'weibull'
    ) -> pd.Series:
        """
        Estimate median survival time (50th percentile).

        Median survival = time when S(t) = 0.5

        Args:
            player_covariates: Player characteristics
            model_type: Model to use

        Returns:
            Series with median survival times
        """
        if model_type == 'weibull':
            model = self.weibull_model
        elif model_type == 'cox':
            model = self.cox_model
        else:
            raise ValueError(f"Unknown model_type: {model_type}")

        median_survival = model.predict_median(player_covariates)

        return median_survival

    def plot_survival_curves(
        self,
        player_covariates: pd.DataFrame,
        labels: List[str],
        model_type: Literal['weibull', 'cox'] = 'weibull',
        save_path: Optional[str] = None
    ):
        """
        Plot survival curves for multiple player profiles.

        Args:
            player_covariates: DataFrame with player characteristics (each row = player)
            labels: Labels for each player/profile
            model_type: Model to use
            save_path: Path to save figure
        """
        if not PLOTTING_AVAILABLE:
            raise ImportError("matplotlib required for plotting")

        # Get survival curves
        survival_curves = self.predict_survival_curve(
            player_covariates, model_type=model_type
        )

        # Plot
        fig, ax = plt.subplots(figsize=(10, 6))

        for i, label in enumerate(labels):
            ax.plot(
                survival_curves.index,
                survival_curves.iloc[:, i],
                label=label,
                linewidth=2
            )

        ax.set_xlabel('Years Since Debut', fontsize=12)
        ax.set_ylabel('Survival Probability', fontsize=12)
        ax.set_title(f'Predicted Career Survival Curves ({model_type.title()} Model)',
                    fontsize=14, fontweight='bold')
        ax.legend()
        ax.grid(alpha=0.3)
        ax.set_ylim(0, 1)

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')

        plt.tight_layout()
        return fig, ax

    def kaplan_meier_by_group(
        self,
        df: pd.DataFrame,
        duration_col: str = 'duration',
        event_col: str = 'event',
        group_col: str = 'position'
    ) -> Dict[str, KaplanMeierFitter]:
        """
        Estimate Kaplan-Meier curves by group (e.g., position).

        Non-parametric survival curves without covariate adjustment.
        Good for exploratory analysis and visualizing group differences.

        Args:
            df: Survival data
            duration_col: Duration column
            event_col: Event indicator
            group_col: Grouping variable

        Returns:
            Dictionary of KM fitters by group
        """
        km_models = {}

        for group_name, group_df in df.groupby(group_col):
            km = KaplanMeierFitter()
            km.fit(
                durations=group_df[duration_col],
                event_observed=group_df[event_col],
                label=str(group_name)
            )
            km_models[group_name] = km

        return km_models

    def plot_kaplan_meier(
        self,
        km_models: Dict[str, KaplanMeierFitter],
        save_path: Optional[str] = None
    ):
        """
        Plot Kaplan-Meier curves by group.

        Args:
            km_models: Dictionary from kaplan_meier_by_group()
            save_path: Path to save figure
        """
        if not PLOTTING_AVAILABLE:
            raise ImportError("matplotlib required for plotting")

        fig, ax = plt.subplots(figsize=(10, 6))

        for group_name, km in km_models.items():
            km.plot_survival_function(ax=ax, label=group_name)

        ax.set_xlabel('Years Since Debut', fontsize=12)
        ax.set_ylabel('Survival Probability', fontsize=12)
        ax.set_title('Kaplan-Meier Survival Curves by Position',
                    fontsize=14, fontweight='bold')
        ax.legend(loc='best')
        ax.grid(alpha=0.3)

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')

        plt.tight_layout()
        return fig, ax


class ContractRiskAnalyzer:
    """
    Assess multi-year contract risk using survival analysis.

    Combines survival models with WAR projections to estimate:
    - Probability of performance cliff during contract
    - Expected WAR over contract period
    - Downside risk (e.g., 10th percentile outcome)
    - Contract value at risk
    """

    def __init__(self, survival_analyzer: CareerSurvivalAnalyzer):
        """
        Initialize contract risk analyzer.

        Args:
            survival_analyzer: Fitted CareerSurvivalAnalyzer
        """
        self.survival_analyzer = survival_analyzer

    def project_contract_war(
        self,
        player_covariates: pd.DataFrame,
        current_war: float,
        current_age: int,
        contract_years: int,
        model_type: Literal['weibull', 'cox'] = 'weibull',
        n_simulations: int = 1000
    ) -> Dict:
        """
        Project WAR over contract period with survival-based decline.

        Uses survival curves to model probabilistic performance decline,
        then simulates WAR trajectories.

        Args:
            player_covariates: Player characteristics
            current_war: Current season WAR
            current_age: Current age
            contract_years: Contract length (years)
            model_type: Survival model to use
            n_simulations: Number of Monte Carlo simulations

        Returns:
            Dictionary with projected WAR distribution and risk metrics
        """
        # Get survival probabilities
        contract_ages = np.arange(current_age, current_age + contract_years)
        years_from_now = contract_ages - current_age

        survival_curve = self.survival_analyzer.predict_survival_curve(
            player_covariates,
            model_type=model_type,
            times=years_from_now
        )

        # Extract survival probabilities
        survival_probs = survival_curve.iloc[:, 0].values

        # Simulate WAR trajectories
        np.random.seed(42)
        war_trajectories = []

        for _ in range(n_simulations):
            trajectory = []
            war = current_war

            for year_idx, age in enumerate(contract_ages):
                # Survival probability at this age
                surv_prob = survival_probs[year_idx]

                # Performance decline factor
                # If survived: gradual decline (2-5% per year)
                # If event occurred: sharp decline (30-50%)
                if np.random.random() > surv_prob:
                    # Event occurred (cliff)
                    decline_factor = np.random.uniform(0.5, 0.7)
                else:
                    # Normal aging
                    decline_factor = np.random.uniform(0.95, 0.98)

                war = max(0, war * decline_factor)
                trajectory.append(war)

            war_trajectories.append(trajectory)

        war_trajectories = np.array(war_trajectories)

        # Aggregate metrics
        mean_war_by_year = war_trajectories.mean(axis=0)
        total_war_distribution = war_trajectories.sum(axis=1)

        return {
            'mean_total_war': float(total_war_distribution.mean()),
            'median_total_war': float(np.median(total_war_distribution)),
            'war_10th_percentile': float(np.percentile(total_war_distribution, 10)),
            'war_90th_percentile': float(np.percentile(total_war_distribution, 90)),
            'mean_war_by_year': mean_war_by_year.tolist(),
            'cliff_probability': float(1 - survival_probs[-1]),
            'expected_value_millions': float(total_war_distribution.mean() * 8),  # $8M/WAR
            'downside_risk_millions': float(np.percentile(total_war_distribution, 10) * 8)
        }

    def compare_contract_scenarios(
        self,
        player_covariates: pd.DataFrame,
        current_war: float,
        current_age: int,
        contract_lengths: List[int],
        dollars_per_war: float = 8.0
    ) -> pd.DataFrame:
        """
        Compare risk/reward for different contract lengths.

        Args:
            player_covariates: Player characteristics
            current_war: Current WAR
            current_age: Current age
            contract_lengths: List of contract durations to compare
            dollars_per_war: Market rate ($/WAR)

        Returns:
            DataFrame comparing contract scenarios
        """
        scenarios = []

        for years in contract_lengths:
            projection = self.project_contract_war(
                player_covariates,
                current_war,
                current_age,
                years
            )

            scenarios.append({
                'contract_years': years,
                'expected_total_war': projection['mean_total_war'],
                'median_total_war': projection['median_total_war'],
                '10th_percentile_war': projection['war_10th_percentile'],
                '90th_percentile_war': projection['war_90th_percentile'],
                'cliff_probability': projection['cliff_probability'],
                'expected_value_$M': projection['mean_total_war'] * dollars_per_war,
                'downside_value_$M': projection['war_10th_percentile'] * dollars_per_war
            })

        return pd.DataFrame(scenarios)
