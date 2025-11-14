# Interview Talking Points: Advanced Statistical Methods

**Quick Reference for Discussing Technical Implementations**

---

## 1. Opening Statement (30 seconds)

*"I built a baseball analytics platform that goes beyond traditional sabermetrics by implementing three advanced statistical frameworks: Bayesian hierarchical modeling for prospect evaluation with uncertainty quantification, causal inference methods to evaluate player development interventions, and survival analysis for probabilistic aging curves. All implemented in production-quality Python with PyMC, statsmodels, and lifelines."*

---

## 2. Bayesian Hierarchical Model (2 minutes)

### The Problem
"Traditional ML models give point estimates: 'This prospect has a 65% chance of MLB success.' But they don't tell you how confident that estimate is. A 65% with tons of data is very different from 65% with sparse data."

### The Solution
"I implemented a hierarchical Bayesian logistic regression in PyMC. The key innovation is **partial pooling across positions**. Catchers and utility players have less data, so we borrow strength from the overall population while still capturing position-specific effects. It's a bias-variance tradeoff—we accept a bit of bias toward the population mean to reduce variance in sparse groups."

### Technical Details
- MCMC sampling with NUTS (No-U-Turn Sampler)
- 4 parallel chains, 2000 draws each
- Convergence diagnostics: R-hat < 1.01, ESS > 400
- Full posterior distributions for predictions
- 95% credible intervals for uncertainty

### The Punchline
"Now we can say: 'This prospect has a 65% chance (95% CI: 45-82%). The wide interval means we need more scouting info.' That's actionable intelligence for front office decisions."

---

## 3. Causal Inference Framework (2 minutes)

### The Problem
"Suppose we want to know: 'Does changing a player's launch angle approach improve performance?' You can't just compare changers vs non-changers—that's selection bias. Players who change might be different in unmeasured ways (motivation, coaching access, talent)."

### The Solution
"I implemented **propensity score matching** to create a balanced comparison. We estimate the probability of treatment given covariates (age, prior performance, position), then match treated and control players with similar propensity scores. This balances measured confounders."

### Technical Details
- Logistic regression for propensity model
- Caliper matching (max distance 0.05)
- Covariate balance checks: standardized mean differences < 0.1
- ATT estimation with robust standard errors
- Also implemented: DiD, RDD, doubly robust

### The Punchline
"This gives us the **causal effect**: 'Players who changed launch angle gained 15 wRC+ points (95% CI: 8-22, p=0.001).' That's evidence for a coaching intervention, not just correlation."

---

## 4. Survival Analysis for Aging (2 minutes)

### The Problem
"Traditional aging curves assume everyone hits a cliff at the same age. But some 32-year-olds decline at 34, others at 37. And we need to account for **censoring**—active players haven't retired yet, so we have partial information."

### The Solution
"I used **Weibull AFT and Cox proportional hazards models** to estimate probabilistic decline curves. These handle censoring properly and provide position-specific hazard functions."

### Technical Details
- Weibull AFT: parametric survival model
  - h(t) = λρt^(ρ-1)
  - Covariates: peak WAR, debut age, position
- Cox PH: semi-parametric hazard model
  - h(t|X) = h₀(t) × exp(β'X)
  - Hazard ratios interpretable
- Monte Carlo simulation for contract risk

### The Punchline
"For a 6-year contract on a 29-year-old outfielder, we can say: 'Expected total WAR: 18 (95% CI: 12-24). Probability of aging cliff during contract: 23%. Downside risk (10th percentile): 10 WAR worth $80M.' That quantifies contract risk."

---

## 5. Key Differentiators from Traditional Sabermetrics

| Traditional Approach | This Portfolio |
|---------------------|----------------|
| Point estimates | Full posterior distributions |
| Deterministic aging curves | Probabilistic survival curves |
| Correlation (xStats) | Causation (PSM, DiD, RDD) |
| Single models | Hierarchical/ensemble |
| No uncertainty | Credible intervals |
| Frequentist p-values | Bayesian posteriors |

---

## 6. Statistical Sophistication Signals

**To demonstrate expertise without being asked:**

1. **"I checked R-hat and ESS..."** (Bayesian convergence diagnostics)
2. **"The standardized mean difference was < 0.1..."** (Covariate balance)
3. **"I used WAIC for model comparison..."** (Bayesian model selection)
4. **"The concordance index was 0.73..."** (Survival model discrimination)
5. **"I implemented doubly robust estimation..."** (Advanced causal method)
6. **"Partial pooling prevents overfitting..."** (Hierarchical modeling intuition)

---

## 7. Handling Technical Challenges

### "How did you choose priors for the Bayesian model?"
"I used weakly informative priors: Normal(0, 1) for feature coefficients—regularizes without being too dogmatic. For the position-level variance, HalfNormal(1) allows flexibility while preventing degeneracy. In production, I'd elicit informative priors from domain experts or use empirical Bayes from historical data."

### "What if the parallel trends assumption fails in DiD?"
"Great question. I implemented a parallel trends test—regress outcome on treatment × time in the pre-period. If p > 0.05, we're safe. If not, I'd try: (1) event studies to see when trends diverge, (2) synthetic control methods, (3) difference-in-difference-in-differences with a comparison group, or (4) switch to a regression discontinuity design if there's a threshold."

### "How do you handle correlated errors in survival analysis?"
"I'd use a **frailty model** (random effects in survival)—adds a gamma-distributed frailty term to account for unobserved heterogeneity. Or cluster-robust standard errors if we have grouped data (e.g., players on the same team). For repeated events, I'd use Andersen-Gill or Prentice-Williams-Peterson models."

---

## 8. Connecting to Front Office Impact

### Prospect Evaluation
"Traditional scouting gives subjective grades (55/60/65). ML models give probabilities (70% MLB arrival). **Bayesian hierarchical models give probabilities with uncertainty** (70% ± 15%). When intervals are wide, allocate more scouting resources. When narrow, confidently draft/protect."

### Player Development
"Instead of guessing if a swing change worked, **causal inference gives evidence-based recommendations**. If PSM shows +15 wRC+ effect (p<0.01), implement organization-wide. If not significant, don't waste coaching time."

### Contract Negotiations
"Survival models turn aging curves into **contract risk assessments**. Instead of saying 'He'll decline 5% per year,' we say '23% chance of cliff in years 3-4.' That changes negotiation leverage—push for shorter deals or add performance clauses."

---

## 9. Mentoring & Communication Examples

### For Junior Analysts
"I documented every function with Google-style docstrings explaining parameters, returns, and examples. The Bayesian notebook walks through: (1) why Bayesian, (2) model structure, (3) MCMC diagnostics, (4) interpretation. Someone with basic Python can follow along."

### For Non-Technical Staff
"I create visualizations like survival curves ('This player has an 80% chance of maintaining performance for 3 more years') and uncertainty bands ('Our prediction could be off by ±10 wRC+ points'). Numbers with context, not just p-values."

### For Executives
"I translate statistical findings to business impact: 'Bayesian model says 65% MLB arrival (CI: 45-82%). That's borderline—recommend protected list spot but don't block a blockbuster trade.' Decision support, not just analysis."

---

## 10. "What's Your Best Work in This Portfolio?"

**Answer:**

"The Bayesian hierarchical prospect model. Here's why:

1. **Statistical sophistication**: Hierarchical modeling with partial pooling is graduate-level stats
2. **Production implementation**: 800 lines of well-documented Python, not just a notebook
3. **Practical impact**: Uncertainty quantification changes how you allocate scouting resources
4. **Demonstrates mentoring**: Extensive docstrings and tutorial notebook
5. **Shows rigor**: MCMC diagnostics, model comparison, validation

Most baseball analytics uses Random Forests or XGBoost—solid models, but they don't quantify uncertainty. Bayesian methods do. That's the edge for a Senior Quant Analyst role: bringing modern statistical methods to a field that needs them."

---

## 11. Why White Sox Specifically?

*"I'm excited about the White Sox because [research their analytics department]. I noticed [specific recent move/trade/signing], and I think [how your methods apply]. For example, my survival analysis framework could assess aging risk for multi-year FA contracts. My causal inference methods could evaluate player development program changes. And my Bayesian prospect model could improve draft/IFA allocation by quantifying uncertainty."*

---

## 12. One-Liner Zingers (Use Sparingly)

**On Bayesian vs Frequentist:**
*"P-values answer 'How likely is this data given no effect?' Bayesian posteriors answer 'How likely is this effect given the data?' The latter is what decision-makers actually care about."*

**On Causal Inference:**
*"Correlation tells you what happened. Causation tells you what will happen if you intervene. Front offices need the latter."*

**On Survival Analysis:**
*"Not all 32-year-olds are created equal. Some are Ichiro, some are Jamie Moyer, most are somewhere in between. Survival models quantify that variation."*

**On Hierarchical Models:**
*"When you have 8 catchers and 40 outfielders in your data, complete pooling ignores position differences, no pooling overfits on catchers, partial pooling gets the best of both worlds."*

---

## 13. Red Flags to Avoid

**Don't say:**
- "I just used the default settings" ❌
- "I didn't check convergence" ❌
- "P-value is < 0.05 so it's significant" ❌
- "I'm not sure why this worked" ❌
- "I assumed the data was clean" ❌

**Do say:**
- "I tuned hyperparameters via cross-validation" ✅
- "R-hat was < 1.01 across all parameters" ✅
- "Effect size is 15 wRC+ (95% CI: 8-22)" ✅
- "This works because of partial pooling shrinkage" ✅
- "I handled missing data with multiple imputation" ✅

---

## 14. Closing Statement (30 seconds)

*"This portfolio demonstrates three things: (1) I can implement advanced statistical methods from scratch, not just use packages blindly. (2) I understand when to use Bayesian vs frequentist, causal vs predictive, parametric vs non-parametric. (3) I write production-quality code with proper validation, documentation, and reproducibility. I'm ready to design and deploy sophisticated models that inform multi-million dollar decisions for the White Sox."*

---

## 15. Quick Stats to Memorize

- **Lines of code**: 2,000+ across 3 advanced modules
- **Statistical methods**: 10+ (Bayesian hierarchical, PSM, DiD, RDD, DR, Weibull, Cox, KM, etc.)
- **Notebooks**: 6 analysis notebooks including 1 advanced Bayesian tutorial
- **Dependencies mastered**: PyMC, ArviZ, lifelines, statsmodels, scikit-learn
- **MCMC diagnostics**: R-hat, ESS, divergences, trace plots, WAIC
- **GitHub commits**: Regular commits showing iterative development
- **Documentation**: 100% of functions have docstrings

---

## 16. Follow-Up Questions to Ask Them

**Technical:**
- "What probabilistic programming languages does your team use, if any?"
- "How do you currently handle uncertainty quantification in player projections?"
- "Are there opportunities to implement causal inference for development programs?"

**Strategic:**
- "What's the balance between research-focused and production-deployment work?"
- "How does the analytics team collaborate with scouting and player development?"
- "What statistical methods have you wanted to implement but haven't yet?"

**Cultural:**
- "How do you foster continuous learning in advanced statistical methods?"
- "What's the process for moving a research project to production?"
- "How do you communicate complex statistical findings to baseball ops?"

---

**Remember**: Be confident but not arrogant. Show enthusiasm for learning. Acknowledge limitations ("I haven't implemented neural networks yet, but I'm familiar with the theory"). Most importantly, tie everything back to **front office impact**—not just fancy math, but better decisions.

Good luck! 🚀
