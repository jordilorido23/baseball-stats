# Baseball Analytics Portfolio

**Production-ready Python platform for baseball operations and front office decision-making**

A comprehensive analytics toolkit covering player evaluation, prospect ranking, time-series forecasting, and advanced statistical modeling. Built with modern ML/statistical methods and designed for real-world baseball operations use cases.

---

## 🆕 **NEW: 2025-2026 MLB Free Agent Analysis**

**Just completed comprehensive analysis of the 2025-26 free agent class!**

📊 **[Read the Full Analysis Report →](2025_FREE_AGENT_ANALYSIS_REPORT.md)** (25,000+ word professional report)

**Highlights:**
- ✅ Analyzed **62 notable free agents** including Kyle Tucker (8.7 WAR), Dylan Cease (8.1 WAR), Alex Bregman (7.7 WAR)
- ✅ Expected stats (xStats) gap analysis identifying buy-low opportunities and regression risks
- ✅ Position-specific aging curves with multi-year contract projections
- ✅ Contract valuations using $8M/WAR baseline with inflation adjustments
- ✅ Strategic recommendations for contenders, rebuilders, and mid-market teams
- ✅ Complete position-by-position breakdowns (C, 1B, 2B, 3B, SS, OF, DH, SP, RP)

**Key Findings:**
- **Kyle Tucker (OF, 29)** is THE max contract to give → 7yr/$280-320M
- **Dylan Cease (SP, 30)** is the top pitcher → 6yr/$200-240M
- **Age 32+ players** show significant cliff risk → cap contract length
- **Mid-tier market** (Torres, Santander, Naylor) offers best value opportunities
- **Buy-low candidates** with elite contact quality (10%+ barrel rate) but unlucky 2025 results

**Analysis Files:**
- 📄 [Comprehensive Report](2025_FREE_AGENT_ANALYSIS_REPORT.md) - Full position-by-position breakdown
- 📓 [Jupyter Notebook](notebooks/05_free_agent_analysis_2025.ipynb) - Interactive analysis with visualizations
- 📝 [Blog Post](blog/posts/2025-11-fa-class-expected-stats.md) - Ready-to-publish content (5000+ words)
- 📋 [Quick Summary](ANALYSIS_SUMMARY.md) - Key insights and deliverables overview

---

## Core Capabilities

**What This Portfolio Demonstrates:**
- ✅ Machine Learning (ensemble models, gradient boosting, stacking)
- ✅ Time-Series Forecasting (in-season projections, rest-of-season WAR)
- ✅ Player Similarity & Comparables (scouting, trade targeting)
- ✅ Unsupervised Learning (pitch arsenal clustering, player segmentation)
- ✅ Expected Stats Analysis (buy-low/sell-high identification)
- ✅ Advanced Statistical Methods (Bayesian, causal inference, survival analysis)
- ✅ Production Code Quality (modular design, documentation, testing)

---

## Key Features

### Data Sources
- **MLB Statcast Data**: Pitch-level data including velocity, spin rate, exit velocity, launch angle, and more
- **FanGraphs Leaderboards**: Season-level stats for all MLB players (299+ metrics)
- **Baseball Savant Expected Stats**: xBA, xSLG, xwOBA, barrel rates, and quality of contact metrics
- **Minor League Analytics**: Track prospect development across all MiLB levels (AAA, AA, A+, A, Rookie)

### Practical ML & Analytics Tools

#### Time-Series Forecasting & Projections
- **ARIMA/ETS/Prophet Models**: In-season performance forecasting
- **Rest-of-Season WAR Projections**: Playoff race scenario planning
- **Player Trajectory Modeling**: Identify breakouts and slumps early
- **Model Comparison**: Evaluate multiple forecasting approaches
- **Walk-Forward Validation**: Proper out-of-sample testing

#### Player Similarity & Comparables
- **Cosine Similarity**: Find players with similar statistical profiles
- **K-Nearest Neighbors**: Efficient comparable player search
- **Feature Weighting**: Prioritize important stats in comparisons
- **Historical Comps**: "Who had similar stats at age 24?"
- **Radar Charts**: Visual player profile comparisons
- **Applications**: Scouting AAA for MLB-similar players, trade targeting

#### Ensemble Machine Learning
- **Model Stacking**: Meta-learner combines Random Forest + XGBoost + Logistic Regression
- **Weighted Ensembles**: Performance-based model weighting
- **Soft Voting**: Aggregate predictions from multiple models
- **Cross-Validation**: Proper evaluation with stratified folds
- **Calibration**: Ensure predicted probabilities match observed rates
- **Feature Importance**: Aggregate importance across models

#### Pitch Arsenal Clustering
- **K-Means Clustering**: Group pitchers by stuff profiles
- **Hierarchical Clustering**: Dendrogram of pitcher similarities
- **PCA Visualization**: Plot clusters in reduced dimensions
- **Optimal K Selection**: Silhouette/elbow methods
- **Applications**: "Which pitchers have similar stuff to Gerrit Cole?"

#### Expected Stats & Breakout Detection
- **xStats Gap Analysis**: Identify unlucky (buy-low) and lucky (sell-high) players
- **Quality of Contact Metrics**: Barrel rate, hard hit rate, exit velocity
- **Composite Breakout Scores**: Weighted combination of xStats, discipline, age
- **Buy-Low Candidates**: Undervalued players based on contact quality
- **Sell-High Candidates**: Players outperforming expected metrics

#### Prospect Evaluation
- **Random Forest Classifier**: MLB arrival probability prediction
- **Age-Adjusted Metrics**: Performance relative to level expectations
- **Feature Engineering**: K/BB ratios, elite thresholds, BABIP-neutral stats
- **Prospect Rankings**: Sort by prediction confidence

---

### Advanced Statistical Methods (Research-Grade)

#### Bayesian Hierarchical Prospect Model (PyMC)
- **Hierarchical logistic regression** with position-level partial pooling
- **Full posterior distributions** for predictions (not just point estimates)
- **Uncertainty quantification**: 95% credible intervals for MLB arrival probability
- **Shrinkage estimation**: Prevents overfitting on sparse position groups
- **MCMC diagnostics**: R-hat, ESS, divergence checks for model validation
- **Interpretable feature effects** with Bayesian credible intervals

#### Causal Inference Framework
- **Propensity Score Matching**: Estimate treatment effects for player development interventions
- **Difference-in-Differences (DiD)**: Before/after analysis controlling for trends
- **Regression Discontinuity**: Exploit threshold-based assignment (e.g., 40-man roster decisions)
- **Doubly Robust Estimation**: Combines propensity scores + outcome regression
- **Covariate Balance Checks**: Standardized mean differences to validate matching quality
- **Applications**: Coaching changes, swing adjustments, position changes, promotion timing

#### Survival Analysis for Aging Curves
- **Weibull AFT Models**: Parametric time-to-event modeling for performance decline
- **Cox Proportional Hazards**: Semi-parametric hazard functions by position
- **Kaplan-Meier Curves**: Non-parametric survival estimation by position
- **Contract Risk Assessment**: Probability of aging cliff during multi-year deals
- **Censoring Handling**: Accounts for active players (events haven't occurred yet)
- **Monte Carlo Simulation**: Probabilistic WAR projections with downside risk

*These advanced methods demonstrate statistical sophistication for research-heavy roles, but the practical ML tools above are the core focus.*

### Additional Tools
- **Advanced Metrics**: wOBA, barrel rate, hard hit rate, whiff rate, chase rate, plate discipline metrics
- **Rich Visualizations**: Pitch locations, movement profiles, spray charts, rolling metrics, player comparisons
- **Player Matching**: Fuzzy search to handle name variations and typos
- **Percentile Rankings**: Benchmark any player against league averages
- **Data Caching**: Intelligent caching system to minimize API calls and speed up analysis

### Interactive Notebooks & Blog
- **Advanced Statistical Notebooks**:
  - `06_bayesian_prospect_model.ipynb` - Hierarchical Bayesian modeling with PyMC
  - `07_causal_player_development.ipynb` - Causal inference for interventions (coming soon)
  - `08_survival_aging_curves.ipynb` - Survival analysis for contract risk (coming soon)
- **Traditional Analysis Notebooks**:
  - `01_mlb_statcast_analysis.ipynb` - Pitch-level MLB data exploration
  - `02_milb_prospect_analysis.ipynb` - Minor league prospect evaluation
  - `03_breakout_candidates.ipynb` - Expected stats gap analysis
  - `04_prospect_predictions.ipynb` - ML prospect rankings
  - `05_free_agent_analysis_2025.ipynb` - 2025 FA class evaluation
- **Blog**: Data-driven articles on free agency, player valuation, and front office strategy
  - [The 2025 Free Agent Class: Expected Stats Tell the Real Story](blog/posts/2025-11-fa-class-expected-stats.md)
  - [Buy-Low Free Agents: Hidden Gems with Elite Contact Quality](blog/posts/2025-11-buy-low-free-agents.md)

## Quick Start

### 1. Setup Environment

```bash
# Create a virtual environment
python -m venv venv

# Activate it
source venv/bin/activate  # On macOS/Linux
# OR
venv\Scripts\activate  # On Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Run Your First Analysis

```bash
# Launch Jupyter
jupyter notebook

# Open notebooks/01_mlb_statcast_analysis.ipynb
```

The starter notebook will guide you through:
- Fetching recent Statcast data
- Analyzing pitch velocities and types
- Looking up and analyzing specific players
- Visualizing exit velocity vs launch angle

## Project Structure

```
baseball-stats/
├── blog/                  # Blog posts and analysis articles
│   ├── posts/            # Published articles
│   ├── figures/          # Visualizations for blog posts
│   └── templates/        # Blog post templates
├── notebooks/              # Jupyter notebooks for analysis
│   ├── 01_mlb_statcast_analysis.ipynb    # Pitch-level MLB data
│   ├── 02_milb_prospect_analysis.ipynb   # Minor league prospects
│   ├── 03_breakout_candidates.ipynb      # Expected stats analysis
│   ├── 04_prospect_predictions.ipynb     # ML prospect rankings
│   ├── 05_free_agent_analysis_2025.ipynb # 2025 FA class evaluation
│   ├── 06_bayesian_prospect_model.ipynb  # Bayesian hierarchical modeling (PyMC)
│   ├── 07_causal_player_development.ipynb # Causal inference (coming soon)
│   └── 08_survival_aging_curves.ipynb    # Survival analysis (coming soon)
├── src/
│   ├── data/              # Data fetching modules
│   │   ├── statcast_fetcher.py           # Statcast pitch data
│   │   ├── fangraphs_fetcher.py          # FanGraphs leaderboards
│   │   ├── savant_leaderboards.py        # Expected stats
│   │   ├── milb_fetcher.py               # Minor league data
│   │   └── contract_data.py              # Free agent contract info
│   ├── analysis/          # Analysis utilities
│   │   ├── metrics.py                    # Advanced baseball metrics
│   │   ├── visualizations.py             # Plotting functions
│   │   ├── breakout_detector.py          # Breakout identification
│   │   ├── free_agent_analyzer.py        # FA evaluation tools
│   │   ├── aging_curves.py               # Age-based projections
│   │   └── causal_inference.py           # Causal inference methods
│   ├── models/            # Predictive models
│   │   ├── prospect_predictor.py         # Random forest prospect model
│   │   ├── bayesian_prospect_model.py    # Bayesian hierarchical model (PyMC)
│   │   └── survival_models.py            # Weibull/Cox survival models
│   └── utils/             # Helper functions
│       └── helpers.py                    # Player search, percentiles
├── data/                  # Local data cache (gitignored)
├── config.py              # Configuration settings (updated for 2025)
├── requirements.txt       # Python dependencies
└── README.md
```

## Example Usage

### Analyze 2025 Free Agents

```python
from src.data import SavantLeaderboards, ContractData
from src.analysis import FreeAgentAnalyzer, AgingCurveAnalyzer

# Initialize
savant = SavantLeaderboards()
contracts = ContractData()
fa_analyzer = FreeAgentAnalyzer(dollars_per_war=8.0)
aging = AgingCurveAnalyzer()

# Get 2025 season data
batter_xstats = savant.get_batter_expected_stats(2025, min_pa=200)
fa_list = contracts.get_all_free_agents()

# Analyze free agent class
fa_analysis = fa_analyzer.analyze_free_agent_class(
    batter_xstats,
    fa_list,
    player_name_col='Name'
)

# Find buy-low candidates
buy_low = fa_analyzer.identify_buy_low_candidates(
    fa_analysis,
    min_woba_gap=0.020,
    max_age=32,
    min_quality_threshold=0.10
)

print("2025 Buy-Low Free Agents:")
print(buy_low[['player_name', 'age_2025', 'woba', 'xwoba', 'woba_gap',
               'barrel_batted_rate', 'fa_value_score']])

# Project contract value with aging curves
player_war = 4.5  # Current WAR
player_age = 29
position = 'OF'
contract_years = 6

projection = aging.calculate_contract_war(
    player_war, player_age, position, contract_years
)

print(f"\nProjected WAR over {contract_years} years: {projection['total_war']}")
print(f"Average WAR/year: {projection['avg_war_per_year']}")
print(f"Reaches aging cliff: {projection['cliff_during_contract']}")
```

### Find Breakout Candidates (Expected Stats Analysis)

```python
from src.data import SavantLeaderboards
from src.analysis.breakout_detector import BreakoutDetector

# Initialize
savant = SavantLeaderboards()
detector = BreakoutDetector()

# Get expected stats
batter_xstats = savant.get_batter_expected_stats(2024, min_pa=100)

# Find unlucky players (xStats > actual stats)
unlucky = detector.find_unlucky_players(
    batter_xstats,
    player_type='batter',
    min_gap=0.020,  # 20+ point gap
    top_n=20
)

print("Buy low candidates:")
print(unlucky[['first_name', 'last_name', 'ba', 'xba', 'woba', 'xwoba']])
```

### Rank Minor League Prospects

```python
from src.data import MiLBFetcher
from src.models import ProspectPredictor

# Get AAA prospects
milb = MiLBFetcher()
aaa_batting = milb.get_batting_stats(2024, level="AAA")

# Find elite young prospects
elite = aaa_batting[
    (aaa_batting['Age'] <= 24) &
    (aaa_batting['wRC+'] >= 120) &
    (aaa_batting['PA'] >= 100)
].sort_values('wRC+', ascending=False)

print("Top young AAA prospects:")
print(elite[['Name', 'Age', 'wRC+', 'K%', 'BB%', 'HR', 'SB']].head(20))
```

---

## Advanced Statistical Methods

### Bayesian Hierarchical Prospect Model

```python
from src.models.bayesian_prospect_model import BayesianProspectModel
from src.data import MiLBFetcher

# Initialize model
bayes_model = BayesianProspectModel(random_seed=42)

# Prepare hierarchical data
data = bayes_model.prepare_data(
    milb_df=aaa_prospects,
    success_col='mlb_success',
    position_col='Pos',
    feature_cols=['Age', 'wRC+', 'K%', 'BB%', 'ISO', 'age_differential'],
    test_size=0.2
)

# Fit with MCMC (NUTS sampler)
trace, diagnostics = bayes_model.fit(
    data=data,
    chains=4,  # Parallel MCMC chains
    draws=2000,  # Posterior samples per chain
    tune=1000,  # Adaptation steps
    target_accept=0.95  # For complex posteriors
)

# Check convergence
print(f"Converged: {diagnostics['converged']}")
print(f"Max R-hat: {diagnostics['max_rhat']:.4f}")  # Should be < 1.01

# Get feature effects with uncertainty
feature_effects = bayes_model.get_feature_effects(credible_interval=0.95)
print("\nFeature Effects (95% Credible Intervals):")
print(feature_effects)

# Predict with full uncertainty quantification
predictions = bayes_model.predict(
    X_new=new_prospects[features],
    position_new=position_indices,
    credible_interval=0.95
)

print("\nPredictions with Uncertainty:")
print(predictions[['prob_mean', 'prob_lower', 'prob_upper', 'interval_width']])

# Position-specific baseline rates (partial pooling)
position_effects = bayes_model.get_position_effects()
print("\nPosition Baseline Success Rates:")
print(position_effects[['position', 'baseline_prob']])
```

**Key Advantages:**
- Full posterior distributions, not just point estimates
- Hierarchical structure with partial pooling across positions
- Proper uncertainty quantification for decision-making
- Shrinkage prevents overfitting on sparse data
- Interpretable effects with Bayesian credible intervals

---

### Causal Inference: Propensity Score Analysis

```python
from src.analysis.causal_inference import PropensityScoreAnalyzer

# Initialize analyzer
ps_analyzer = PropensityScoreAnalyzer(random_state=42)

# Research Question: Does changing hitting approach improve performance?
# Treatment: Players who changed launch angle approach
# Control: Players who didn't change

# Estimate propensity scores
propensity_scores = ps_analyzer.estimate_propensity_scores(
    df=player_data,
    treatment_col='changed_approach',
    covariate_cols=['Age', 'Prior_wRC+', 'K%', 'BB%', 'Position'],
    model_type='logistic'
)

# Match treated and control units
matched_data = ps_analyzer.match_on_propensity(
    df=player_data,
    treatment_col='changed_approach',
    propensity_scores=propensity_scores,
    matching_method='caliper',
    caliper=0.05,  # Max propensity score distance
    n_neighbors=1
)

# Check covariate balance
balance = ps_analyzer.check_balance(
    df_original=player_data,
    df_matched=matched_data,
    treatment_col='changed_approach',
    covariate_cols=['Age', 'Prior_wRC+', 'K%', 'BB%']
)

print("Covariate Balance (Standardized Mean Differences):")
print(balance[balance['dataset'] == 'Matched'])

# Estimate Average Treatment Effect on the Treated (ATT)
att_results = ps_analyzer.estimate_att(
    matched_df=matched_data,
    treatment_col='changed_approach',
    outcome_col='wRC+'
)

print(f"\nAverage Treatment Effect on Treated:")
print(f"ATT: {att_results['att']:.2f} wRC+ points")
print(f"95% CI: [{att_results['ci_lower']:.2f}, {att_results['ci_upper']:.2f}]")
print(f"P-value: {att_results['p_value']:.4f}")
```

**Causal Methods Available:**
- Propensity Score Matching
- Difference-in-Differences (DiD)
- Regression Discontinuity (RDD)
- Doubly Robust Estimation
- Instrumental Variables (IV)

---

### Survival Analysis: Aging Curves with Uncertainty

```python
from src.models.survival_models import CareerSurvivalAnalyzer, ContractRiskAnalyzer

# Initialize survival analyzer
survival = CareerSurvivalAnalyzer(random_state=42)

# Prepare survival data
survival_data = survival.prepare_survival_data(
    df=player_careers,
    player_id_col='playerid',
    age_col='Age',
    war_col='WAR',
    event_definition='decline',  # WAR drops 50% from peak
    decline_threshold=0.5
)

# Fit Weibull AFT model
weibull_results = survival.fit_weibull_aft(
    df=survival_data,
    duration_col='duration',
    event_col='event',
    covariate_cols=['peak_war', 'debut_age', 'position']
)

print("Weibull AFT Model Results:")
print(weibull_results['summary'])
print(f"Concordance Index: {weibull_results['concordance_index']:.3f}")

# Fit Cox Proportional Hazards
cox_results = survival.fit_cox_model(
    df=survival_data,
    covariate_cols=['peak_war', 'debut_age', 'position']
)

print("\nHazard Ratios (Cox Model):")
print(cox_results['hazard_ratios'])

# Contract risk assessment
risk_analyzer = ContractRiskAnalyzer(survival)

# Evaluate 6-year contract for 29-year-old outfielder
player_profile = pd.DataFrame({
    'peak_war': [5.0],
    'debut_age': [24],
    'position': ['OF']
})

contract_projection = risk_analyzer.project_contract_war(
    player_covariates=player_profile,
    current_war=4.5,
    current_age=29,
    contract_years=6,
    n_simulations=1000
)

print("\nContract Risk Assessment:")
print(f"Expected Total WAR: {contract_projection['mean_total_war']:.1f}")
print(f"10th Percentile WAR: {contract_projection['war_10th_percentile']:.1f}")
print(f"90th Percentile WAR: {contract_projection['war_90th_percentile']:.1f}")
print(f"Probability of Cliff: {contract_projection['cliff_probability']:.1%}")
print(f"Expected Value: ${contract_projection['expected_value_millions']:.1f}M")
print(f"Downside Risk (10th %ile): ${contract_projection['downside_risk_millions']:.1f}M")

# Compare contract scenarios
scenarios = risk_analyzer.compare_contract_scenarios(
    player_covariates=player_profile,
    current_war=4.5,
    current_age=29,
    contract_lengths=[3, 4, 5, 6],
    dollars_per_war=8.0
)

print("\nContract Length Comparison:")
print(scenarios)
```

**Survival Models Provided:**
- Weibull AFT (parametric)
- Cox Proportional Hazards (semi-parametric)
- Kaplan-Meier (non-parametric)
- Contract risk simulation with Monte Carlo

---

### Fetch Season-Level Stats

```python
from src.data import FanGraphsFetcher

# Get full season stats
fg = FanGraphsFetcher()
batting = fg.get_batting_stats(2024, qual=50)  # Min 50 PAs

# Top performers by wRC+
top_hitters = batting.nlargest(20, 'wRC+')
print(top_hitters[['Name', 'Team', 'wRC+', 'HR', 'SB', 'AVG', 'OBP']])
```


## Available Data Sources

### MLB (via pybaseball)
- **Statcast**: Pitch-level data (2015-present)
- **FanGraphs**: Season stats and advanced metrics
- **Baseball Reference**: Historical data

### Minor Leagues
- **FanGraphs Minor League Stats**: All levels (AAA → Rookie)
- Batting and pitching statistics
- Park-adjusted metrics (wRC+, FIP, etc.)

## Advanced Metrics Available

### Batting
- wOBA (weighted On-Base Average)
- Barrel Rate
- Hard Hit Rate (95+ mph)
- Exit Velocity metrics
- Launch Angle optimization
- Expected stats (xBA, xSLG, xwOBA)

### Pitching
- Pitch Arsenal Analysis (velocity, spin, usage)
- Whiff Rate
- Chase Rate
- Zone Contact Rate
- Pitch Movement profiles

### Plate Discipline
- Swing rates (in-zone, out-of-zone)
- Contact rates
- Pitch recognition metrics

## Configuration

Edit [config.py](config.py) to customize:
- Default date ranges
- Cache settings
- Statistical thresholds
- Visualization preferences
- Team colors for plots

## Data Caching

Data is automatically cached to avoid repeated downloads:
- **MLB Statcast**: 1-day cache (games update frequently)
- **MiLB Stats**: 7-day cache (stats update less frequently)
- Cache location: `data/cache/`

To force refresh, set `use_cache=False` when fetching data.

## Front Office Use Cases

### Free Agency & Contracts
1. **Evaluate 2025-26 free agent class** - Expected stats vs actual performance
2. **Identify buy-low candidates** - Players with elite contact quality but poor results
3. **Project multi-year contracts** - Aging curves + WAR projections
4. **Calculate surplus value** - Market value vs contract cost analysis
5. **Risk assessment** - Regression candidates (lucky vs sustainable results)

### Player Acquisition
1. **Trade deadline targets** - Undervalued players based on xStats
2. **Waiver wire analysis** - MLB-ready talent being underutilized
3. **International free agents** - Skillset translation from NPB/KBO
4. **Minor league free agents** - Hidden gems in organizational depth charts

### Roster Construction
1. **Platoon optimization** - Quantify platoon advantage opportunities
2. **Positional value** - Defense + offense trade-off analysis
3. **Lineup construction** - Run expectancy optimization
4. **Bullpen strategy** - Leverage optimization, matchup analysis

### Player Development
1. **Prospect progression tracking** - MiLB → MLB transition analysis
2. **Skill development** - Pitch arsenal evolution, approach changes
3. **Organizational comparisons** - Benchmark development systems
4. **Promotion timing** - Optimize call-up decisions based on readiness

### Competitive Intelligence
1. **Rival team analysis** - Identify strengths/weaknesses in competitor rosters
2. **Trade partner identification** - Find teams with complementary needs
3. **Market inefficiencies** - Undervalued skill sets across MLB
4. **Draft strategy** - College vs high school player development curves

## Blog & Analysis

This repository powers data-driven blog content on baseball front office analytics. Published articles available in [`blog/posts/`](blog/posts/).

**Current Series: 2025 Free Agent Analysis**
- Part 1: [The 2025 Free Agent Class: Expected Stats Tell the Real Story](blog/posts/2025-11-fa-class-expected-stats.md)
- Part 2: [Buy-Low Free Agents: Hidden Gems with Elite Contact Quality](blog/posts/2025-11-buy-low-free-agents.md)
- Part 3: Coming soon - "Aging Curves: Which Free Agents Are Worth Multi-Year Deals?"

**Publishing**: Articles written for Substack, Medium, or self-hosted blog. All analysis code is reproducible via Jupyter notebooks.

## Contributing

This platform supports front office analytics and public baseball analysis. Add your own:
- Blog posts in `blog/posts/` using the [template](blog/templates/post_template.md)
- Analysis notebooks in `notebooks/`
- Custom metrics in `src/analysis/metrics.py`
- Visualizations in `src/analysis/visualizations.py`
- Data sources in `src/data/`

## Resources

- [pybaseball documentation](https://github.com/jldbc/pybaseball)
- [Statcast Search](https://baseballsavant.mlb.com/statcast_search)
- [FanGraphs Library](https://library.fangraphs.com/)
- [Baseball Reference](https://www.baseball-reference.com/)

## Next Steps

### For Front Office Analysts
1. **Update data sources** - Fetch 2025 season data when available
2. **Run free agent analysis** - Evaluate specific players using xStats + aging curves
3. **Generate visualizations** - Create charts for presentations and reports
4. **Build trade models** - Adapt FA analysis framework for mid-season trade deadline
5. **Customize for your org** - Add proprietary data sources and internal metrics

### For Blog Writers
1. **Use blog templates** - Start with [`blog/templates/post_template.md`](blog/templates/post_template.md)
2. **Run analysis notebooks** - Generate findings in Jupyter, export to blog posts
3. **Create visualizations** - Save figures to `blog/figures/` for publication
4. **Publish and share** - Export to Substack, Medium, or self-host on GitHub Pages
5. **Build audience** - Share on Twitter/X, Reddit (r/baseball), and baseball analytics communities

### For Developers
1. **Extend data sources** - Add Spotrac API, Baseball Reference scraping, etc.
2. **Build new analyzers** - Defensive metrics, park factors, team-level aggregations
3. **Create APIs** - Expose analysis tools as REST endpoints for front office apps
4. **Automate reporting** - Schedule daily/weekly updates on free agent values
5. **Contribute improvements** - Open PRs for new features and bug fixes

Happy analyzing!
