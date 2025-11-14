"""
Causal Inference Methods for Player Development Analysis.

This module implements causal inference techniques to answer "why" questions
about player performance, not just "what" predictions. Critical for evaluating
the impact of interventions (coaching changes, swing adjustments, position changes).

Key Methods:
1. Propensity Score Matching: Match treated/control units with similar covariates
2. Difference-in-Differences (DiD): Before/after analysis controlling for trends
3. Regression Discontinuity: Exploit threshold-based assignment
4. Instrumental Variables: Address endogeneity and selection bias
5. Doubly Robust Estimation: Combine outcome and treatment models

References:
- Imbens & Rubin (2015): Causal Inference for Statistics, Social, and Biomedical Sciences
- Angrist & Pischke (2008): Mostly Harmless Econometrics
- Pearl (2009): Causality: Models, Reasoning, and Inference
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Literal, Union
import warnings

try:
    from sklearn.linear_model import LogisticRegression, LinearRegression
    from sklearn.neighbors import NearestNeighbors
    from sklearn.preprocessing import StandardScaler
    import statsmodels.api as sm
    import statsmodels.formula.api as smf
    STATSMODELS_AVAILABLE = True
except ImportError:
    STATSMODELS_AVAILABLE = False
    warnings.warn(
        "statsmodels required for causal inference. "
        "Install with: pip install statsmodels"
    )


class PropensityScoreAnalyzer:
    """
    Propensity score matching and weighting for causal inference.

    Estimates treatment effects by matching treated and control units
    with similar probability of receiving treatment.

    Example Use Cases:
    - Effect of position change on offensive production
    - Impact of swing adjustment on batted ball quality
    - Effect of promotion timing on development trajectory
    """

    def __init__(self, random_state: int = 42):
        """
        Initialize propensity score analyzer.

        Args:
            random_state: Random seed for reproducibility
        """
        self.random_state = random_state
        self.propensity_model = None
        self.scaler = None

    def estimate_propensity_scores(
        self,
        df: pd.DataFrame,
        treatment_col: str,
        covariate_cols: List[str],
        model_type: Literal['logistic', 'probit'] = 'logistic'
    ) -> pd.Series:
        """
        Estimate propensity scores P(Treatment=1 | Covariates).

        Propensity score = probability of receiving treatment given observed
        characteristics. Allows matching on a single dimension instead of
        multiple covariates (curse of dimensionality).

        Args:
            df: DataFrame with treatment and covariates
            treatment_col: Binary treatment indicator (0/1)
            covariate_cols: Covariates to include in propensity model
            model_type: 'logistic' or 'probit'

        Returns:
            Series of propensity scores (0 to 1)
        """
        # Prepare data
        X = df[covariate_cols].fillna(df[covariate_cols].median())
        y = df[treatment_col]

        # Standardize covariates
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)

        # Fit propensity score model
        if model_type == 'logistic':
            self.propensity_model = LogisticRegression(
                random_state=self.random_state,
                max_iter=1000
            )
            self.propensity_model.fit(X_scaled, y)
            propensity_scores = self.propensity_model.predict_proba(X_scaled)[:, 1]

        elif model_type == 'probit':
            # Use statsmodels for probit
            if not STATSMODELS_AVAILABLE:
                raise ImportError("statsmodels required for probit model")

            X_sm = sm.add_constant(X_scaled)
            probit_model = sm.Probit(y, X_sm)
            probit_result = probit_model.fit(disp=False)
            propensity_scores = probit_result.predict(X_sm)

        else:
            raise ValueError(f"Unknown model_type: {model_type}")

        return pd.Series(propensity_scores, index=df.index, name='propensity_score')

    def match_on_propensity(
        self,
        df: pd.DataFrame,
        treatment_col: str,
        propensity_scores: pd.Series,
        matching_method: Literal['nearest', 'caliper', 'radius'] = 'nearest',
        caliper: float = 0.05,
        n_neighbors: int = 1,
        replace: bool = False
    ) -> pd.DataFrame:
        """
        Match treated and control units using propensity scores.

        Creates matched pairs/sets of treated and control units with
        similar propensity scores. Ensures covariate balance.

        Args:
            df: DataFrame with all units
            treatment_col: Treatment indicator column
            propensity_scores: Propensity scores from estimate_propensity_scores()
            matching_method: 'nearest', 'caliper', or 'radius'
            caliper: Maximum allowable propensity score distance
            n_neighbors: Number of controls to match per treated unit
            replace: Allow reusing control units (matching with replacement)

        Returns:
            DataFrame with matched units (treated + controls)
        """
        df_match = df.copy()
        df_match['propensity_score'] = propensity_scores

        treated = df_match[df_match[treatment_col] == 1].copy()
        control = df_match[df_match[treatment_col] == 0].copy()

        if len(treated) == 0 or len(control) == 0:
            raise ValueError("Need both treated and control units for matching")

        # Find matches
        matched_indices = []

        if matching_method in ['nearest', 'caliper']:
            # Nearest neighbor matching
            nn = NearestNeighbors(n_neighbors=n_neighbors, metric='euclidean')
            nn.fit(control[['propensity_score']])

            for idx, row in treated.iterrows():
                distances, indices = nn.kneighbors(
                    [[row['propensity_score']]]
                )

                # Apply caliper if specified
                if matching_method == 'caliper':
                    valid = distances[0] <= caliper
                    indices = indices[0][valid]
                else:
                    indices = indices[0]

                # Get matched control units
                matched_control_idx = control.iloc[indices].index.tolist()
                matched_indices.extend(matched_control_idx)

        elif matching_method == 'radius':
            # Radius matching (all controls within caliper)
            for idx, row in treated.iterrows():
                distances = np.abs(
                    control['propensity_score'] - row['propensity_score']
                )
                within_radius = control[distances <= caliper]
                matched_indices.extend(within_radius.index.tolist())

        # Create matched dataset
        if not replace:
            matched_indices = list(set(matched_indices))  # Remove duplicates

        matched_controls = df_match.loc[matched_indices]
        matched_data = pd.concat([treated, matched_controls], ignore_index=False)

        return matched_data.sort_index()

    def estimate_att(
        self,
        matched_df: pd.DataFrame,
        treatment_col: str,
        outcome_col: str
    ) -> Dict[str, float]:
        """
        Estimate Average Treatment Effect on the Treated (ATT).

        ATT = E[Y(1) - Y(0) | T=1]
        = Average effect of treatment for those who actually received it

        Args:
            matched_df: Matched dataset from match_on_propensity()
            treatment_col: Treatment indicator
            outcome_col: Outcome variable

        Returns:
            Dictionary with ATT estimate, standard error, and p-value
        """
        treated = matched_df[matched_df[treatment_col] == 1]
        control = matched_df[matched_df[treatment_col] == 0]

        # Mean outcomes
        y1_mean = treated[outcome_col].mean()
        y0_mean = control[outcome_col].mean()

        # ATT estimate
        att = y1_mean - y0_mean

        # Standard error (conservative: assumes independence)
        se_treated = treated[outcome_col].std() / np.sqrt(len(treated))
        se_control = control[outcome_col].std() / np.sqrt(len(control))
        se_att = np.sqrt(se_treated**2 + se_control**2)

        # T-statistic and p-value
        t_stat = att / se_att if se_att > 0 else 0
        from scipy import stats
        p_value = 2 * (1 - stats.t.cdf(abs(t_stat), len(matched_df) - 2))

        return {
            'att': float(att),
            'se': float(se_att),
            't_statistic': float(t_stat),
            'p_value': float(p_value),
            'ci_lower': float(att - 1.96 * se_att),
            'ci_upper': float(att + 1.96 * se_att),
            'n_treated': len(treated),
            'n_control': len(control)
        }

    def check_balance(
        self,
        df_original: pd.DataFrame,
        df_matched: pd.DataFrame,
        treatment_col: str,
        covariate_cols: List[str]
    ) -> pd.DataFrame:
        """
        Check covariate balance before and after matching.

        Good matching should achieve balance: treated and control groups
        have similar covariate distributions. Standardized mean difference
        (SMD) < 0.1 is considered well-balanced.

        Args:
            df_original: Original unmatched data
            df_matched: Matched data
            treatment_col: Treatment indicator
            covariate_cols: Covariates to check

        Returns:
            DataFrame with balance statistics
        """
        balance_results = []

        for dataset_name, dataset in [('Original', df_original), ('Matched', df_matched)]:
            treated = dataset[dataset[treatment_col] == 1]
            control = dataset[dataset[treatment_col] == 0]

            for covar in covariate_cols:
                # Means
                mean_treated = treated[covar].mean()
                mean_control = control[covar].mean()

                # Pooled standard deviation
                var_treated = treated[covar].var()
                var_control = control[covar].var()
                pooled_std = np.sqrt((var_treated + var_control) / 2)

                # Standardized mean difference
                smd = (mean_treated - mean_control) / pooled_std if pooled_std > 0 else 0

                balance_results.append({
                    'dataset': dataset_name,
                    'covariate': covar,
                    'mean_treated': mean_treated,
                    'mean_control': mean_control,
                    'std_mean_diff': abs(smd),
                    'balanced': abs(smd) < 0.1
                })

        return pd.DataFrame(balance_results)


class DifferenceInDifferences:
    """
    Difference-in-Differences (DiD) causal estimator.

    Estimates treatment effects by comparing changes over time between
    treated and control groups. Controls for time-invariant confounding
    and common trends.

    Model: Y_it = β0 + β1*Treated_i + β2*Post_t + β3*Treated_i*Post_t + ε_it

    β3 = DiD estimate (treatment effect)

    Example: Did a coaching change improve player performance?
    - Compare players who got new coach (treated) vs didn't (control)
    - Before vs after the change
    - DiD = (After_Treated - Before_Treated) - (After_Control - Before_Control)
    """

    def __init__(self):
        """Initialize DiD estimator."""
        self.model = None
        self.results = None

    def estimate_did(
        self,
        df: pd.DataFrame,
        outcome_col: str,
        treatment_col: str,
        post_col: str,
        covariate_cols: Optional[List[str]] = None,
        cluster_col: Optional[str] = None
    ) -> Dict:
        """
        Estimate DiD treatment effect with regression.

        Args:
            df: Panel data (must have multiple time periods)
            outcome_col: Outcome variable
            treatment_col: Treatment group indicator (0/1)
            post_col: Post-treatment period indicator (0/1)
            covariate_cols: Additional controls
            cluster_col: Column for clustered standard errors (e.g., player ID)

        Returns:
            Dictionary with DiD estimate, SE, p-value, and full results
        """
        if not STATSMODELS_AVAILABLE:
            raise ImportError("statsmodels required for DiD estimation")

        # Create interaction term
        df_reg = df.copy()
        df_reg['treated_x_post'] = df_reg[treatment_col] * df_reg[post_col]

        # Build formula
        formula = f"{outcome_col} ~ {treatment_col} + {post_col} + treated_x_post"

        if covariate_cols:
            formula += " + " + " + ".join(covariate_cols)

        # Estimate model
        if cluster_col:
            # Clustered standard errors
            model = smf.ols(formula, data=df_reg).fit(
                cov_type='cluster',
                cov_kwds={'groups': df_reg[cluster_col]}
            )
        else:
            model = smf.ols(formula, data=df_reg).fit()

        self.model = model

        # Extract DiD coefficient
        did_coef = model.params['treated_x_post']
        did_se = model.bse['treated_x_post']
        did_pval = model.pvalues['treated_x_post']

        return {
            'did_estimate': float(did_coef),
            'se': float(did_se),
            'p_value': float(did_pval),
            'ci_lower': float(model.conf_int().loc['treated_x_post', 0]),
            'ci_upper': float(model.conf_int().loc['treated_x_post', 1]),
            'r_squared': float(model.rsquared),
            'n_obs': int(model.nobs),
            'full_results': model.summary()
        }

    def parallel_trends_test(
        self,
        df: pd.DataFrame,
        outcome_col: str,
        treatment_col: str,
        time_col: str,
        pre_period_end: int
    ) -> Dict:
        """
        Test parallel trends assumption (pre-treatment).

        DiD requires that treated and control groups would have followed
        parallel trends in the absence of treatment. Test by checking
        pre-treatment trend differences.

        Args:
            df: Panel data
            outcome_col: Outcome variable
            treatment_col: Treatment indicator
            time_col: Time period column
            pre_period_end: Last pre-treatment period

        Returns:
            Dictionary with test results
        """
        # Filter to pre-period
        pre_df = df[df[time_col] <= pre_period_end].copy()

        # Interaction between treatment and time
        pre_df['treated_x_time'] = pre_df[treatment_col] * pre_df[time_col]

        # Regression: Y ~ Treated + Time + Treated*Time
        formula = f"{outcome_col} ~ {treatment_col} + {time_col} + treated_x_time"
        model = smf.ols(formula, data=pre_df).fit()

        # Test coefficient on interaction term
        interaction_coef = model.params['treated_x_time']
        interaction_pval = model.pvalues['treated_x_time']

        # Parallel trends hold if interaction is not significant
        parallel_trends = interaction_pval > 0.05

        return {
            'parallel_trends': parallel_trends,
            'trend_difference': float(interaction_coef),
            'p_value': float(interaction_pval),
            'interpretation': (
                'Parallel trends assumption satisfied' if parallel_trends
                else 'WARNING: Pre-treatment trends differ - DiD may be biased'
            )
        }


class RegressionDiscontinuity:
    """
    Regression Discontinuity Design (RDD) for causal inference.

    Exploits sharp cutoffs in treatment assignment to estimate causal effects.
    Near the cutoff, treatment assignment is "as good as random."

    Example: Effect of making 40-man roster on development
    - Players just above cutoff (added to roster) vs just below (not added)
    - Assignment based on ranking/performance score
    - Compare outcomes just above vs just below threshold
    """

    def __init__(self, bandwidth_method: Literal['ik', 'ccft'] = 'ik'):
        """
        Initialize RDD estimator.

        Args:
            bandwidth_method: Method for choosing optimal bandwidth
                - 'ik': Imbens-Kalyanaraman (2012)
                - 'ccft': Calonico-Cattaneo-Farrell-Titiunik (2014)
        """
        self.bandwidth_method = bandwidth_method
        self.model = None

    def estimate_rdd(
        self,
        df: pd.DataFrame,
        outcome_col: str,
        running_var: str,
        cutoff: float,
        bandwidth: Optional[float] = None,
        polynomial_order: int = 1
    ) -> Dict:
        """
        Estimate local treatment effect at discontinuity.

        Args:
            df: Data with outcome and running variable
            outcome_col: Outcome of interest
            running_var: Assignment variable (continuous)
            cutoff: Threshold for treatment assignment
            bandwidth: Bandwidth around cutoff (if None, uses optimal selection)
            polynomial_order: Polynomial order for local regression (1=linear)

        Returns:
            Dictionary with RDD estimate and diagnostics
        """
        if not STATSMODELS_AVAILABLE:
            raise ImportError("statsmodels required for RDD")

        df_rdd = df.copy()

        # Center running variable at cutoff
        df_rdd['running_centered'] = df_rdd[running_var] - cutoff

        # Treatment indicator
        df_rdd['treated'] = (df_rdd['running_centered'] >= 0).astype(int)

        # Select bandwidth if not provided
        if bandwidth is None:
            bandwidth = self._optimal_bandwidth(
                df_rdd, outcome_col, 'running_centered'
            )

        # Local sample within bandwidth
        local_df = df_rdd[
            df_rdd['running_centered'].abs() <= bandwidth
        ].copy()

        # Build polynomial terms
        formula = f"{outcome_col} ~ treated"
        for p in range(1, polynomial_order + 1):
            local_df[f'running_p{p}'] = local_df['running_centered'] ** p
            local_df[f'treated_x_running_p{p}'] = (
                local_df['treated'] * local_df[f'running_p{p}']
            )
            formula += f" + running_p{p} + treated_x_running_p{p}"

        # Estimate local linear regression
        model = smf.ols(formula, data=local_df).fit()
        self.model = model

        # Extract treatment effect at cutoff
        rdd_estimate = model.params['treated']
        rdd_se = model.bse['treated']
        rdd_pval = model.pvalues['treated']

        return {
            'rdd_estimate': float(rdd_estimate),
            'se': float(rdd_se),
            'p_value': float(rdd_pval),
            'ci_lower': float(model.conf_int().loc['treated', 0]),
            'ci_upper': float(model.conf_int().loc['treated', 1]),
            'bandwidth': float(bandwidth),
            'n_below_cutoff': int((local_df['treated'] == 0).sum()),
            'n_above_cutoff': int((local_df['treated'] == 1).sum()),
            'polynomial_order': polynomial_order
        }

    def _optimal_bandwidth(
        self,
        df: pd.DataFrame,
        outcome_col: str,
        running_var: str
    ) -> float:
        """
        Calculate optimal bandwidth using Imbens-Kalyanaraman method.

        Args:
            df: Data
            outcome_col: Outcome variable
            running_var: Centered running variable

        Returns:
            Optimal bandwidth
        """
        # Simplified IK bandwidth calculation
        # Full implementation would use rdrobust package

        # Use rule of thumb: 1.84 * sd(running_var) * n^(-1/5)
        n = len(df)
        sd_running = df[running_var].std()
        bandwidth = 1.84 * sd_running * (n ** (-0.2))

        return bandwidth


class DoublyRobustEstimator:
    """
    Doubly Robust (DR) estimation for causal effects.

    Combines propensity score weighting and outcome regression.
    Provides valid estimates if EITHER the propensity model OR the outcome
    model is correctly specified (doesn't require both to be correct).

    More robust than using propensity scores or regression alone.
    """

    def __init__(self, random_state: int = 42):
        """Initialize DR estimator."""
        self.random_state = random_state
        self.propensity_model = None
        self.outcome_model_treated = None
        self.outcome_model_control = None

    def estimate_ate(
        self,
        df: pd.DataFrame,
        treatment_col: str,
        outcome_col: str,
        covariate_cols: List[str]
    ) -> Dict:
        """
        Estimate Average Treatment Effect (ATE) using doubly robust method.

        ATE = E[Y(1) - Y(0)]
        = Average causal effect in the population

        Args:
            df: Data with treatment, outcome, and covariates
            treatment_col: Treatment indicator (0/1)
            outcome_col: Outcome variable
            covariate_cols: Covariates

        Returns:
            Dictionary with ATE estimate and diagnostics
        """
        X = df[covariate_cols].fillna(df[covariate_cols].median())
        T = df[treatment_col]
        Y = df[outcome_col]

        # Step 1: Estimate propensity scores
        propensity_model = LogisticRegression(
            random_state=self.random_state, max_iter=1000
        )
        propensity_model.fit(X, T)
        ps = propensity_model.predict_proba(X)[:, 1]
        ps = np.clip(ps, 0.01, 0.99)  # Avoid extreme weights

        # Step 2: Estimate outcome models for each treatment arm
        # E[Y | X, T=1]
        X_treated = X[T == 1]
        Y_treated = Y[T == 1]
        outcome_model_1 = LinearRegression()
        outcome_model_1.fit(X_treated, Y_treated)
        mu1 = outcome_model_1.predict(X)

        # E[Y | X, T=0]
        X_control = X[T == 0]
        Y_control = Y[T == 0]
        outcome_model_0 = LinearRegression()
        outcome_model_0.fit(X_control, Y_control)
        mu0 = outcome_model_0.predict(X)

        # Step 3: Doubly robust estimator
        # ATE = E[DR_1] - E[DR_0]
        # where DR_t = (T/ps) * Y - ((T-ps)/ps) * mu1  (for treated)
        #         DR_c = ((1-T)/(1-ps)) * Y + ((T-ps)/(1-ps)) * mu0  (for control)

        dr_treated = (T / ps) * Y - ((T - ps) / ps) * mu1
        dr_control = ((1 - T) / (1 - ps)) * Y + ((T - ps) / (1 - ps)) * mu0

        ate = dr_treated.mean() - dr_control.mean()

        # Standard error (bootstrap or asymptotic)
        # Simplified: use sample variance
        dr_effects = dr_treated - dr_control
        se = dr_effects.std() / np.sqrt(len(df))

        # Confidence interval
        ci_lower = ate - 1.96 * se
        ci_upper = ate + 1.96 * se

        return {
            'ate': float(ate),
            'se': float(se),
            'ci_lower': float(ci_lower),
            'ci_upper': float(ci_upper),
            'p_value': float(2 * (1 - stats.norm.cdf(abs(ate / se)))),
            'n': len(df)
        }
