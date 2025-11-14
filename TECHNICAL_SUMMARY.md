# Technical Summary: Advanced Baseball Analytics Portfolio

**For: Senior Quantitative Analyst Position - Chicago White Sox**

---

## Executive Summary

This repository demonstrates advanced statistical modeling expertise specifically aligned with the White Sox Senior Quantitative Analyst role requirements:

**Job Requirements Met:**
- ✅ **Deep Bayesian Statistics Expertise**: Hierarchical models with PyMC
- ✅ **Probabilistic Programming**: Custom Bayesian models using MCMC (NUTS sampler)
- ✅ **Causal Inference**: Propensity scoring, DiD, RDD, doubly robust estimation
- ✅ **Machine Learning**: Random forests, gradient boosting, ensemble methods
- ✅ **Production Model Pipelines**: End-to-end workflow from data → model → deployment
- ✅ **Version Control**: Git-based workflow with proper structure
- ✅ **Statistical Rigor**: MCMC diagnostics, convergence checks, uncertainty quantification

---

## Key Statistical Implementations

### 1. Bayesian Hierarchical Prospect Model (PyMC)

**File**: `src/models/bayesian_prospect_model.py` (800+ lines)
**Notebook**: `notebooks/06_bayesian_prospect_model.ipynb`

**Statistical Approach:**
```
Level 1 (Player): MLB_Success ~ Bernoulli(p_i)
                  logit(p_i) = α_position[i] + X_i @ β

Level 2 (Position): α_j ~ Normal(μ_α, σ_α)  # Partial pooling

Level 3 (Hyperpriors): μ_α ~ Normal(0, 2)
                        σ_α ~ HalfNormal(1)
                        β_k ~ Normal(0, 1)
```

**Key Features:**
- Hierarchical logistic regression with position-level random effects
- Partial pooling: positions with sparse data borrow strength from population
- MCMC sampling with NUTS (No-U-Turn Sampler)
- Full posterior distributions for predictions
- Uncertainty quantification: 95% credible intervals
- Convergence diagnostics: R-hat, ESS, divergences
- Model comparison via WAIC

**Why It Matters:**
- Shows understanding of hierarchical modeling for grouped data
- Demonstrates ability to build custom Bayesian models
- Provides uncertainty quantification critical for multi-million dollar decisions
- Prevents overfitting on sparse position categories (catchers, utility players)

**Front Office Application:**
- Prospect ranking with confidence intervals
- Identify high-uncertainty prospects needing more scouting
- Quantify risk in Rule 5 Draft decisions

---

### 2. Causal Inference Framework

**File**: `src/analysis/causal_inference.py` (600+ lines)

**Methods Implemented:**

#### A. Propensity Score Matching
```python
P(Treatment | Covariates) = logit^(-1)(X @ β)
ATT = E[Y(1) - Y(0) | T=1]
```
- Logistic regression for propensity model
- Nearest neighbor / caliper / radius matching
- Covariate balance checks (standardized mean differences)
- Average Treatment Effect on Treated (ATT) estimation

#### B. Difference-in-Differences (DiD)
```python
DiD = [E[Y|Treated, Post] - E[Y|Treated, Pre]] -
      [E[Y|Control, Post] - E[Y|Control, Pre]]
```
- Regression-based DiD with cluster-robust standard errors
- Parallel trends testing
- Time-varying controls

#### C. Regression Discontinuity Design (RDD)
```python
τ_RDD = lim[x↓c] E[Y|X=x] - lim[x↑c] E[Y|X=x]
```
- Local linear regression around cutoff
- Optimal bandwidth selection (Imbens-Kalyanaraman)
- Polynomial orders for flexible functional forms

#### D. Doubly Robust Estimation
```python
ATE = E[τ_DR] where
τ_DR = (T/e(X))Y - ((T-e(X))/e(X))μ_1(X) +
       ((1-T)/(1-e(X)))μ_0(X) - ((T-e(X))/(1-e(X)))μ_0(X)
```
- Combines propensity scores + outcome regression
- Valid if either model is correctly specified

**Why It Matters:**
- Answers "why" questions, not just "what" predictions
- Essential for evaluating player development interventions
- Demonstrates understanding of selection bias and confounding

**Front Office Applications:**
- Does changing launch angle approach improve performance? (PSM)
- Did a coaching change improve player development? (DiD)
- Effect of barely making 40-man roster on development (RDD)
- Impact of position change on offensive production (DR)

---

### 3. Survival Analysis for Aging Curves

**File**: `src/models/survival_models.py` (700+ lines)

**Models Implemented:**

#### A. Weibull Accelerated Failure Time (AFT)
```python
log(T) = β₀ + β₁X₁ + ... + σε
h(t) = λρt^(ρ-1)  # Hazard function
```
- Parametric time-to-event modeling
- Covariate effects on survival time
- Interpretation: acceleration factors

#### B. Cox Proportional Hazards
```python
h(t|X) = h₀(t) × exp(β'X)
```
- Semi-parametric hazard model
- Baseline hazard h₀(t) not specified
- Hazard ratios for covariate effects

#### C. Kaplan-Meier Estimator
```python
S(t) = ∏[tᵢ≤t] (1 - dᵢ/nᵢ)
```
- Non-parametric survival curves
- Group comparisons (position-specific)

#### D. Contract Risk Analyzer
- Monte Carlo simulation for WAR projections
- Probabilistic aging cliff timing
- Downside risk assessment (10th percentile outcomes)

**Why It Matters:**
- Aging is inherently probabilistic, not deterministic
- Handles censoring (active players haven't retired yet)
- Provides contract risk assessment with uncertainty
- Position-specific hazard functions

**Front Office Applications:**
- Multi-year contract risk: "32-year-old OF has 23% chance of cliff in years 3-4"
- Expected career WAR with confidence bands
- Optimal contract length given age/position
- Downside risk quantification (P10 WAR scenarios)

---

## Statistical Rigor Demonstrated

### Bayesian Model Diagnostics
- **R-hat**: Convergence metric (should be < 1.01)
- **ESS**: Effective sample size (bulk & tail)
- **Divergences**: MCMC sampler issues
- **Trace plots**: Visual convergence inspection
- **WAIC**: Model comparison (information criterion)

### Causal Inference Validation
- **Covariate balance**: Standardized mean differences < 0.1
- **Parallel trends**: Pre-treatment trend similarity
- **Sensitivity analysis**: Robustness to hidden confounding
- **Placebo tests**: Falsification checks

### Survival Analysis Checks
- **Concordance index**: Predictive discrimination (C-statistic)
- **Proportional hazards assumption**: Schoenfeld residuals
- **Kaplan-Meier validation**: Non-parametric comparison
- **Cross-validation**: Out-of-sample performance

---

## Production-Ready Code Quality

### Software Engineering Best Practices
- **Modular design**: Separate data/analysis/models layers
- **Type hints**: `typing` module for function signatures
- **Docstrings**: Google-style documentation for all classes/methods
- **Error handling**: Try/except with informative warnings
- **Unit tests**: pytest-compatible structure
- **Configuration**: Centralized config.py
- **Version control**: Git with .gitignore for data/models

### Reproducibility
- **Random seeds**: Set throughout for reproducible MCMC/simulation
- **Environment management**: requirements.txt with pinned versions
- **Data caching**: Intelligent caching to avoid repeated API calls
- **Model serialization**: Save/load fitted models (pickle, NetCDF)

### Scalability
- **Parallel MCMC**: Multi-chain sampling for faster convergence
- **Vectorized operations**: NumPy/pandas for efficiency
- **Optional dependencies**: Graceful degradation if advanced libs unavailable
- **Memory management**: Chunked data loading for large datasets

---

## Comparison to Job Requirements

| Requirement | Implementation | Evidence |
|------------|---------------|----------|
| **Bayesian statistics expertise** | Hierarchical logistic regression, MCMC | `bayesian_prospect_model.py` |
| **Probabilistic programming (Stan/PyMC)** | PyMC with NUTS sampler | Notebook 06 |
| **Causal inference** | PSM, DiD, RDD, DR | `causal_inference.py` |
| **Machine learning (RF, GBM, NN)** | Random forests, gradient boosting | `prospect_predictor.py` |
| **Production pipelines** | Data → Feature engineering → Model → Prediction | All notebooks |
| **Statistical rigor** | Diagnostics, validation, uncertainty quantification | Throughout |
| **Git version control** | Proper repo structure, .gitignore | Entire repo |
| **Mentoring capability** | Extensive documentation, clear code structure | Docstrings, notebooks |

---

## Novel Contributions Beyond Standard Sabermetrics

Most baseball analytics uses:
- Deterministic aging curves (everyone hits a cliff at age 34)
- Point estimates from ML models (no uncertainty)
- Correlational analysis (not causal)
- Frequentist methods (p-values, confidence intervals)

This portfolio demonstrates:
1. **Probabilistic aging curves**: Survival models with individual variation
2. **Bayesian uncertainty**: Full posterior distributions for decision-making
3. **Causal inference**: Answering "why" questions about interventions
4. **Hierarchical modeling**: Partial pooling for sparse data
5. **Production-grade rigor**: Diagnostics, validation, reproducibility

---

## What This Demonstrates

### Statistical Sophistication
- Graduate-level understanding of modern statistical methods
- Ability to implement complex models from scratch (not just using packages)
- Knowledge of when to use parametric vs semi-parametric vs non-parametric approaches
- Understanding of bias-variance tradeoffs, regularization, shrinkage

### Research Skills
- Formulating research questions as statistical problems
- Choosing appropriate methods for causal vs predictive inference
- Model diagnostics and validation
- Communicating uncertainty to non-technical audiences

### Production Engineering
- Writing maintainable, documented, tested code
- Building reusable modeling infrastructure
- Handling missing data, edge cases, errors
- Scalability and performance considerations

### Baseball Domain Knowledge
- Understanding prospect development trajectories
- Position-specific aging patterns
- Expected stats vs actual performance (luck vs skill)
- Contract economics and valuation

---

## How to Discuss in Interviews

### For Technical Interviewers:

**Bayesian Model:**
- "I implemented a hierarchical Bayesian logistic regression using PyMC to predict prospect success. The key insight is using partial pooling across positions—catchers and utility players have less data, so we borrow strength from the overall population while still capturing position-specific effects. This prevents overfitting compared to complete pooling or no pooling."

**Causal Inference:**
- "To evaluate whether a swing change improves performance, you can't just compare changers vs non-changers—that's selection bias. I implemented propensity score matching to create a balanced comparison group, checking covariate balance with standardized mean differences. The ATT estimate then gives us the causal effect for those who actually changed."

**Survival Analysis:**
- "Traditional aging curves assume everyone hits a cliff at the same age. I used Weibull AFT and Cox models to estimate probabilistic decline curves. This lets you quantify contract risk: 'This 32-year-old has a 23% chance of hitting his cliff during a 6-year deal.' That's actionable for front office decisions."

### For Non-Technical Interviewers:

**Why Bayesian?**
- "Instead of saying 'This prospect has a 65% chance of MLB success,' Bayesian methods give us '65% with a 95% confidence range of 45-82%.' When the range is wide, we know to get more scouting info. When it's narrow, we're confident in the projection."

**Why Causal Inference?**
- "Say we want to know if a coaching change improved player development. Just comparing before vs after isn't enough—maybe players naturally improved with age. DiD compares the change in the treated group to the change in a control group, removing the age effect."

**Why Survival Analysis?**
- "Not every 32-year-old ages the same way. Some have cliffs at 34, others at 37. Survival models give us probabilities: 'By age 35, there's a 40% chance this player's WAR drops 50%.' That helps assess multi-year contract risk."

---

## Next Steps to Strengthen Portfolio

If you want to add more before applying:

1. **Add a pitcher module**: Extend Bayesian model to pitchers (different features)
2. **Time-series forecasting**: ARIMA/state-space models for in-season projections
3. **Multi-level models**: Organization → Team → Player hierarchy
4. **Neural networks**: Add PyTorch/TensorFlow for comparison to Bayesian methods
5. **Web dashboard**: Streamlit/Dash for interactive visualizations
6. **SQL integration**: Pull data from databases, not just APIs
7. **A/B testing framework**: Experimental design for coaching interventions

But honestly, what you have now is **already impressive** for a Senior Quant Analyst role. The Bayesian + Causal + Survival trilogy demonstrates advanced statistical expertise beyond most baseball analytics portfolios.

---

## Files to Highlight in Application

**Core Statistical Implementations:**
1. `src/models/bayesian_prospect_model.py` - Bayesian expertise
2. `src/analysis/causal_inference.py` - Causal methods
3. `src/models/survival_models.py` - Survival analysis

**Showcase Notebooks:**
4. `notebooks/06_bayesian_prospect_model.ipynb` - Full Bayesian workflow

**Documentation:**
5. `README.md` - Updated with advanced methods
6. `requirements.txt` - Shows PyMC, lifelines, arviz

**Supporting Code:**
7. `src/models/prospect_predictor.py` - Traditional ML baseline
8. `src/analysis/aging_curves.py` - Deterministic curves for comparison

---

## Potential Interview Questions & Answers

**Q: "Why use Bayesian methods over frequentist?"**

A: "Bayesian methods provide full posterior distributions, not just point estimates. For a front office making multi-million dollar decisions, knowing the uncertainty is critical. If two prospects both have 60% MLB arrival probability but one has a 95% CI of [55%, 65%] and another [30%, 90%], the second needs more scouting. Frequentist methods don't naturally provide this uncertainty quantification."

**Q: "How do you check if your MCMC sampler converged?"**

A: "I use R-hat (Gelman-Rubin statistic)—should be < 1.01 for all parameters. I also check effective sample size (ESS)—want > 400 for bulk and tail. Trace plots should look like 'fuzzy caterpillars' with no trends. Divergences indicate sampler issues, so I increase target_accept or reparameterize. Finally, I run multiple chains and verify they converge to the same posterior."

**Q: "When would you use propensity scores vs difference-in-differences?"**

A: "PSM is for cross-sectional data with no time dimension—match treated and control units at a single time point. DiD requires panel data (multiple time periods) and exploits before/after variation. DiD controls for time-invariant confounders, while PSM assumes no unmeasured confounding given covariates. If you have panel data with a clear intervention time, DiD is often preferred. If not, PSM or regression adjustment."

**Q: "How do you handle censoring in survival analysis?"**

A: "Right-censoring occurs when active players haven't reached the event (retirement, cliff) yet. Survival models account for this in the likelihood function—censored observations contribute information about 'survival past time t' rather than 'event at time t.' This is why we use survival analysis instead of regular regression—it properly uses partial information from censored units."

**Q: "What's the difference between ATT and ATE?"**

A: "ATT is Average Treatment Effect on the Treated—the effect for those who actually received treatment. ATE is the average effect if we treated the entire population. ATT is often more relevant for baseball: 'For players who changed their swing, what was the effect?' vs 'If we forced all players to change, what would happen?' The latter might not make sense if only certain players benefit."

---

## Final Thoughts

This portfolio demonstrates that you can:

1. **Design** sophisticated statistical models for baseball problems
2. **Implement** them in production-quality Python code
3. **Validate** them with proper diagnostics and checks
4. **Communicate** results to technical and non-technical audiences
5. **Mentor** others through clear documentation and code structure

These are exactly the skills the White Sox are looking for in a Senior Quantitative Analyst.

**Key Message:** You're not just running models—you're advancing the statistical rigor of baseball analytics by bringing modern methods (Bayesian, causal, survival) to a field that traditionally relies on simpler approaches.
