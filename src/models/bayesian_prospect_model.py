"""
Bayesian Hierarchical Model for Prospect Success Prediction.

This module implements a Bayesian hierarchical model using PyMC to predict MLB
arrival probability for minor league prospects. Unlike traditional ML models,
this provides full posterior distributions and uncertainty quantification.

Key Features:
- Hierarchical structure with partial pooling across positions
- Position-specific random effects with shrinkage
- Informative priors from historical prospect cohorts
- Full posterior distributions (not just point estimates)
- Credible intervals for predictions and parameters
- Proper uncertainty quantification for decision-making

Statistical Approach:
    For player i in position group j:

    MLB_Success_i ~ Bernoulli(p_i)
    logit(p_i) = α_j + β_1*Age_Adj_i + β_2*wRC+_i + β_3*K%_i + β_4*BB%_i + ...

    Hierarchical priors:
    α_j ~ Normal(μ_α, σ_α)  # Position-specific intercepts with pooling
    β_k ~ Normal(0, σ_β)    # Regularized slopes

This structure allows position-level patterns to inform individual predictions
while accounting for position-specific baseline success rates.

References:
- Gelman & Hill (2007): Data Analysis Using Regression and Multilevel/Hierarchical Models
- McElreath (2020): Statistical Rethinking
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Literal, Union
from pathlib import Path
import warnings

try:
    import pymc as pm
    import arviz as az
    PYMC_AVAILABLE = True
except ImportError:
    PYMC_AVAILABLE = False
    warnings.warn(
        "PyMC not available. Install with: pip install pymc arviz"
    )

try:
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


class BayesianProspectModel:
    """
    Bayesian hierarchical model for predicting MLB success probability.

    This model provides several advantages over traditional ML approaches:

    1. Uncertainty Quantification: Full posterior distributions for all parameters
    2. Hierarchical Structure: Borrows strength across positions (partial pooling)
    3. Interpretability: Clear probabilistic interpretation of coefficients
    4. Small Sample Handling: Shrinkage prevents overfitting with limited data
    5. Decision Support: Credible intervals inform risk assessment

    Example:
        >>> model = BayesianProspectModel()
        >>> model.prepare_data(milb_df, mlb_outcomes)
        >>> model.fit(chains=4, draws=2000)
        >>> predictions = model.predict(new_prospects)
        >>> # Get 95% credible intervals
        >>> print(predictions[['player', 'prob_mean', 'prob_5%', 'prob_95%']])
    """

    def __init__(
        self,
        model_dir: str = "data/models",
        random_seed: int = 42
    ):
        """
        Initialize Bayesian prospect predictor.

        Args:
            model_dir: Directory to save trained models and diagnostics
            random_seed: Random seed for reproducibility
        """
        if not PYMC_AVAILABLE:
            raise ImportError(
                "PyMC required for Bayesian modeling. "
                "Install with: pip install pymc arviz"
            )

        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)

        self.random_seed = random_seed
        self.model = None
        self.trace = None
        self.scaler = None
        self.feature_names = None
        self.position_mapping = None

    def prepare_data(
        self,
        milb_df: pd.DataFrame,
        success_col: str = 'mlb_success',
        position_col: str = 'Pos',
        feature_cols: Optional[List[str]] = None,
        test_size: float = 0.2
    ) -> Dict[str, np.ndarray]:
        """
        Prepare and engineer features for Bayesian modeling.

        Creates hierarchical structure by position and standardizes features
        for efficient MCMC sampling.

        Args:
            milb_df: DataFrame with minor league stats
            success_col: Binary outcome column (1=MLB success, 0=no)
            position_col: Position column for hierarchical grouping
            feature_cols: List of features to use (if None, uses defaults)
            test_size: Fraction for train/test split

        Returns:
            Dictionary with train/test data and metadata
        """
        df = milb_df.copy()

        # Default features if not specified
        if feature_cols is None:
            feature_cols = [
                'Age', 'wRC+', 'K%', 'BB%', 'ISO', 'BABIP',
                'age_differential', 'k_bb_ratio'
            ]

        # Filter to available features
        available_features = [f for f in feature_cols if f in df.columns]
        self.feature_names = available_features

        # Encode positions as integers for hierarchical indexing
        positions = df[position_col].fillna('Unknown')
        unique_positions = sorted(positions.unique())
        self.position_mapping = {pos: idx for idx, pos in enumerate(unique_positions)}
        position_idx = positions.map(self.position_mapping).values

        # Extract features and outcome
        X = df[available_features].fillna(df[available_features].median())
        y = df[success_col].values

        # Standardize features for better MCMC performance
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)

        # Train/test split
        X_train, X_test, y_train, y_test, pos_train, pos_test = train_test_split(
            X_scaled, y, position_idx,
            test_size=test_size,
            random_state=self.random_seed,
            stratify=y
        )

        return {
            'X_train': X_train,
            'y_train': y_train,
            'pos_train': pos_train,
            'X_test': X_test,
            'y_test': y_test,
            'pos_test': pos_test,
            'n_positions': len(unique_positions),
            'n_features': len(available_features),
            'positions': unique_positions
        }

    def build_hierarchical_model(
        self,
        X: np.ndarray,
        y: np.ndarray,
        position_idx: np.ndarray,
        n_positions: int
    ) -> pm.Model:
        """
        Build hierarchical Bayesian logistic regression model.

        Model Structure:
            Level 1 (Player-level):
                MLB_Success ~ Bernoulli(p_i)
                logit(p_i) = α_position[i] + X_i @ β

            Level 2 (Position-level):
                α_j ~ Normal(μ_α, σ_α)  # Partial pooling across positions

            Level 3 (Hyperpriors):
                μ_α ~ Normal(0, 2)      # Overall intercept prior
                σ_α ~ HalfNormal(1)     # Position variance
                β_k ~ Normal(0, 1)      # Feature coefficients

        This structure allows positions with sparse data to borrow information
        from the overall population while still capturing position-specific effects.

        Args:
            X: Standardized feature matrix (N x P)
            y: Binary outcomes (N,)
            position_idx: Position group indices (N,)
            n_positions: Number of unique positions

        Returns:
            PyMC model object
        """
        n_obs, n_features = X.shape

        with pm.Model() as hierarchical_model:
            # Hyperpriors for position-level intercepts
            mu_alpha = pm.Normal('mu_alpha', mu=0, sigma=2)
            sigma_alpha = pm.HalfNormal('sigma_alpha', sigma=1)

            # Position-specific random intercepts (partial pooling)
            alpha = pm.Normal(
                'alpha',
                mu=mu_alpha,
                sigma=sigma_alpha,
                shape=n_positions
            )

            # Feature coefficients with regularization
            beta = pm.Normal('beta', mu=0, sigma=1, shape=n_features)

            # Linear predictor
            # For each player i: logit(p_i) = alpha[position[i]] + X[i] @ beta
            logit_p = alpha[position_idx] + pm.math.dot(X, beta)

            # Likelihood
            y_obs = pm.Bernoulli(
                'y_obs',
                logit_p=logit_p,
                observed=y
            )

        return hierarchical_model

    def fit(
        self,
        data: Dict[str, np.ndarray],
        chains: int = 4,
        draws: int = 2000,
        tune: int = 1000,
        target_accept: float = 0.95,
        return_diagnostics: bool = True
    ) -> Union[az.InferenceData, Tuple[az.InferenceData, Dict]]:
        """
        Fit Bayesian model using NUTS sampler.

        Uses No-U-Turn Sampler (NUTS), a variant of Hamiltonian Monte Carlo
        that efficiently explores high-dimensional posterior distributions.

        Args:
            data: Dictionary from prepare_data()
            chains: Number of MCMC chains (4+ recommended)
            draws: Number of posterior samples per chain
            tune: Number of tuning steps for adaptation
            target_accept: Target acceptance rate (0.8-0.95)
            return_diagnostics: If True, return convergence diagnostics

        Returns:
            InferenceData object with posterior samples
            Optionally: tuple of (InferenceData, diagnostics_dict)
        """
        # Build model
        self.model = self.build_hierarchical_model(
            X=data['X_train'],
            y=data['y_train'],
            position_idx=data['pos_train'],
            n_positions=data['n_positions']
        )

        # Sample from posterior
        with self.model:
            self.trace = pm.sample(
                draws=draws,
                tune=tune,
                chains=chains,
                target_accept=target_accept,
                random_seed=self.random_seed,
                return_inferencedata=True
            )

        if return_diagnostics:
            diagnostics = self._compute_diagnostics(self.trace)
            return self.trace, diagnostics

        return self.trace

    def _compute_diagnostics(self, trace: az.InferenceData) -> Dict:
        """
        Compute MCMC diagnostics for model validation.

        Key diagnostics:
        - R-hat: Convergence metric (should be < 1.01)
        - ESS: Effective sample size (should be > 400 per chain)
        - Divergences: Sampling issues (should be 0)
        - BFMI: Bayesian Fraction of Missing Information (should be > 0.3)

        Args:
            trace: ArviZ InferenceData object

        Returns:
            Dictionary of diagnostic metrics
        """
        summary = az.summary(trace, var_names=['alpha', 'beta', 'mu_alpha', 'sigma_alpha'])

        # Check convergence
        max_rhat = summary['r_hat'].max()
        min_ess_bulk = summary['ess_bulk'].min()
        min_ess_tail = summary['ess_tail'].min()

        # Count divergences
        divergences = trace.sample_stats.diverging.sum().values

        diagnostics = {
            'converged': max_rhat < 1.01,
            'max_rhat': float(max_rhat),
            'min_ess_bulk': float(min_ess_bulk),
            'min_ess_tail': float(min_ess_tail),
            'n_divergences': int(divergences),
            'summary': summary
        }

        # Warnings
        if not diagnostics['converged']:
            warnings.warn(
                f"Model may not have converged. Max R-hat: {max_rhat:.4f}"
            )

        if diagnostics['n_divergences'] > 0:
            warnings.warn(
                f"Found {divergences} divergences. Consider increasing target_accept."
            )

        return diagnostics

    def predict(
        self,
        X_new: pd.DataFrame,
        position_new: np.ndarray,
        credible_interval: float = 0.95,
        n_samples: int = 1000
    ) -> pd.DataFrame:
        """
        Generate predictions with full posterior uncertainty.

        Returns not just point estimates but entire posterior predictive
        distributions, allowing for proper risk assessment.

        Args:
            X_new: New features to predict on
            position_new: Position indices for new observations
            credible_interval: Width of credible interval (default 95%)
            n_samples: Number of posterior samples to use

        Returns:
            DataFrame with columns:
                - prob_mean: Posterior mean probability
                - prob_median: Posterior median
                - prob_lower: Lower credible bound
                - prob_upper: Upper credible bound
                - prob_std: Posterior standard deviation
        """
        if self.trace is None:
            raise ValueError("Model not fitted. Call fit() first.")

        # Standardize features
        X_scaled = self.scaler.transform(X_new)

        # Extract posterior samples
        alpha_samples = self.trace.posterior['alpha'].values  # (chains, draws, n_positions)
        beta_samples = self.trace.posterior['beta'].values    # (chains, draws, n_features)

        # Reshape to (total_samples, n_positions) and (total_samples, n_features)
        alpha_flat = alpha_samples.reshape(-1, alpha_samples.shape[-1])
        beta_flat = beta_samples.reshape(-1, beta_samples.shape[-1])

        # Random sample if too many draws
        if len(alpha_flat) > n_samples:
            idx = np.random.choice(len(alpha_flat), n_samples, replace=False)
            alpha_flat = alpha_flat[idx]
            beta_flat = beta_flat[idx]

        # Compute predictions for each posterior sample
        predictions = []
        for i in range(len(alpha_flat)):
            logit_p = alpha_flat[i, position_new] + X_scaled @ beta_flat[i]
            p = 1 / (1 + np.exp(-logit_p))  # Inverse logit
            predictions.append(p)

        predictions = np.array(predictions)  # Shape: (n_samples, n_new_obs)

        # Compute posterior statistics
        alpha = (1 - credible_interval) / 2
        lower_q = alpha * 100
        upper_q = (1 - alpha) * 100

        results = pd.DataFrame({
            'prob_mean': predictions.mean(axis=0),
            'prob_median': np.median(predictions, axis=0),
            'prob_std': predictions.std(axis=0),
            'prob_lower': np.percentile(predictions, lower_q, axis=0),
            'prob_upper': np.percentile(predictions, upper_q, axis=0)
        })

        # Add prediction interval width for uncertainty assessment
        results['interval_width'] = results['prob_upper'] - results['prob_lower']

        return results

    def get_feature_effects(
        self,
        credible_interval: float = 0.95
    ) -> pd.DataFrame:
        """
        Extract feature effects (beta coefficients) with uncertainty.

        Provides interpretable effect sizes with credible intervals,
        allowing you to identify which features are most predictive.

        Args:
            credible_interval: Width of credible interval

        Returns:
            DataFrame with feature names, means, and credible intervals
        """
        if self.trace is None:
            raise ValueError("Model not fitted. Call fit() first.")

        beta_samples = self.trace.posterior['beta'].values.reshape(-1, len(self.feature_names))

        alpha = (1 - credible_interval) / 2
        lower_q = alpha * 100
        upper_q = (1 - alpha) * 100

        effects = pd.DataFrame({
            'feature': self.feature_names,
            'effect_mean': beta_samples.mean(axis=0),
            'effect_std': beta_samples.std(axis=0),
            'effect_lower': np.percentile(beta_samples, lower_q, axis=0),
            'effect_upper': np.percentile(beta_samples, upper_q, axis=0)
        })

        # Flag statistically significant effects (CI doesn't include 0)
        effects['significant'] = (
            (effects['effect_lower'] > 0) | (effects['effect_upper'] < 0)
        )

        # Sort by absolute effect size
        effects['abs_effect'] = effects['effect_mean'].abs()
        effects = effects.sort_values('abs_effect', ascending=False)

        return effects[['feature', 'effect_mean', 'effect_std',
                       'effect_lower', 'effect_upper', 'significant']]

    def get_position_effects(
        self,
        credible_interval: float = 0.95
    ) -> pd.DataFrame:
        """
        Extract position-specific baseline success rates.

        Shows how much partial pooling is occurring and which positions
        have higher/lower baseline MLB success rates.

        Args:
            credible_interval: Width of credible interval

        Returns:
            DataFrame with position names and intercepts
        """
        if self.trace is None:
            raise ValueError("Model not fitted. Call fit() first.")

        alpha_samples = self.trace.posterior['alpha'].values.reshape(
            -1, len(self.position_mapping)
        )

        alpha_value = (1 - credible_interval) / 2
        lower_q = alpha_value * 100
        upper_q = (1 - alpha_value) * 100

        # Get position names
        pos_names = sorted(self.position_mapping.keys(),
                          key=lambda x: self.position_mapping[x])

        position_effects = pd.DataFrame({
            'position': pos_names,
            'intercept_mean': alpha_samples.mean(axis=0),
            'intercept_std': alpha_samples.std(axis=0),
            'intercept_lower': np.percentile(alpha_samples, lower_q, axis=0),
            'intercept_upper': np.percentile(alpha_samples, upper_q, axis=0)
        })

        # Convert to probability scale for interpretation
        position_effects['baseline_prob'] = 1 / (
            1 + np.exp(-position_effects['intercept_mean'])
        )

        return position_effects.sort_values('baseline_prob', ascending=False)

    def plot_posterior_diagnostics(
        self,
        var_names: Optional[List[str]] = None,
        save_path: Optional[str] = None
    ):
        """
        Create diagnostic plots for MCMC convergence.

        Generates trace plots and posterior distributions to assess
        whether the sampler has converged to the true posterior.

        Args:
            var_names: Variables to plot (if None, plots main parameters)
            save_path: Optional path to save figure
        """
        if self.trace is None:
            raise ValueError("Model not fitted. Call fit() first.")

        if var_names is None:
            var_names = ['mu_alpha', 'sigma_alpha', 'beta']

        ax = az.plot_trace(
            self.trace,
            var_names=var_names,
            compact=True
        )

        if save_path:
            ax.figure.savefig(save_path, dpi=300, bbox_inches='tight')

        return ax

    def compare_to_pooled_model(
        self,
        data: Dict[str, np.ndarray]
    ) -> Dict[str, float]:
        """
        Compare hierarchical model to complete pooling baseline.

        Demonstrates the value of the hierarchical structure by comparing
        to a simpler model that ignores position information.

        Args:
            data: Dictionary from prepare_data()

        Returns:
            Dictionary with WAIC comparison metrics
        """
        # Build pooled (non-hierarchical) model
        with pm.Model() as pooled_model:
            alpha_pooled = pm.Normal('alpha_pooled', mu=0, sigma=2)
            beta_pooled = pm.Normal('beta_pooled', mu=0, sigma=1, shape=data['n_features'])

            logit_p = alpha_pooled + pm.math.dot(data['X_train'], beta_pooled)
            y_obs = pm.Bernoulli('y_obs', logit_p=logit_p, observed=data['y_train'])

            trace_pooled = pm.sample(
                1000, tune=1000, chains=2,
                random_seed=self.random_seed,
                return_inferencedata=True
            )

        # Compute WAIC for both models
        waic_hierarchical = az.waic(self.trace)
        waic_pooled = az.waic(trace_pooled)

        comparison = {
            'hierarchical_waic': float(waic_hierarchical.waic),
            'pooled_waic': float(waic_pooled.waic),
            'improvement': float(waic_pooled.waic - waic_hierarchical.waic)
        }

        return comparison

    def save(self, filename: str = 'bayesian_prospect_model'):
        """
        Save trained model and trace.

        Args:
            filename: Base filename (without extension)
        """
        if self.trace is None:
            raise ValueError("No model to save. Fit model first.")

        # Save trace
        trace_path = self.model_dir / f"{filename}_trace.nc"
        self.trace.to_netcdf(trace_path)

        # Save metadata
        import pickle
        metadata_path = self.model_dir / f"{filename}_metadata.pkl"
        metadata = {
            'feature_names': self.feature_names,
            'position_mapping': self.position_mapping,
            'scaler': self.scaler
        }
        with open(metadata_path, 'wb') as f:
            pickle.dump(metadata, f)

        print(f"Model saved to {self.model_dir}")

    def load(self, filename: str = 'bayesian_prospect_model'):
        """
        Load trained model and trace.

        Args:
            filename: Base filename (without extension)
        """
        import pickle

        trace_path = self.model_dir / f"{filename}_trace.nc"
        metadata_path = self.model_dir / f"{filename}_metadata.pkl"

        if not trace_path.exists():
            raise FileNotFoundError(f"Model file not found: {trace_path}")

        # Load trace
        self.trace = az.from_netcdf(trace_path)

        # Load metadata
        with open(metadata_path, 'rb') as f:
            metadata = pickle.load(f)

        self.feature_names = metadata['feature_names']
        self.position_mapping = metadata['position_mapping']
        self.scaler = metadata['scaler']

        print(f"Model loaded from {self.model_dir}")
