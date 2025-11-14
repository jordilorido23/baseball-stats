# Advanced Reliever Market Intelligence System

## Overview

This system implements **physics-based, biomechanical, and cognitive science analysis** to identify undervalued relievers in the free agent market. It goes far beyond traditional stats to detect hidden gems through:

- **Pitch trajectory physics** (VAA, SSW, Tunneling)
- **Arsenal synergies** (Gyro/Sweeper combos, Effective Velocity)
- **Biomechanical precision** (Release point strategy, Fatigue Units)
- **Game theory optimization** (Nash Equilibrium pitch mix)
- **Market inefficiency detection** (Role mismatches, value vs. price)

---

## System Architecture

### Phase 1: Pitch Physics Analysis (`pitch_physics_analyzer.py`)

**What it does:**
- Calculates **Vertical Approach Angle (VAA)** - measures pitch trajectory angle at plate
- Detects **Seam-Shifted Wake (SSW)** - unexplained movement from seam effects
- Measures **Pitch Tunneling** - deception through trajectory similarity

**Key Metrics:**
- `VAA_FB_avg`: Fastball approach angle (flat <4° vs steep >6°)
- `VAA_Zone_Mismatch_Score`: How well pitcher uses their VAA profile
- `SSW_Movement_FB`: Inches of movement not explained by spin (>3" = elite)
- `Tunneling_Score`: Deception at decision point (0-100)
- `SSW_Trend_3yr`: Multi-year SSW trend (declining = injury risk)

**Why it matters:**
- Flat VAA pitchers throwing high = elite "rising" fastball
- SSW movement = unconscious stuff advantage market doesn't see
- Elite tunneling = superior deception invisible in traditional stats

---

### Phase 2: Arsenal Synergy Analysis (`arsenal_synergy_analyzer.py`)

**What it does:**
- Detects **Gyro Slider + Sweeper** combinations (rare, elite arsenal)
- Calculates **Effective Velocity** by location (inside = faster perceived)
- Measures **Swing Decision Disruption** (timing confusion via sequencing)
- Models **Nash Equilibrium** for optimal pitch mix

**Key Metrics:**
- `Has_Gyro_Sweeper_Combo`: Rare arsenal (Luke Jackson profile)
- `Arsenal_Completeness`: Coverage of swing plane matrix (0-100)
- `Effective_Velocity_Composite`: Location-adjusted perceived velocity
- `Swing_Decision_Disruption_Index`: Cognitive load via sequencing
- `Nash_Equilibrium_Score`: Suboptimal mix (high = easy gains available)
- `Cognitive_Load_Score`: Overall timing disruption (0-100)

**Why it matters:**
- Gyro + Sweeper combo = multiple break shapes at similar velocity
- High effective velocity = "plays up" via location optimization
- Low Nash score = already optimized, high Nash = coaching can unlock value

---

### Phase 3: Biomechanics Analysis (`biomechanics_analyzer.py`)

**What it does:**
- Analyzes **Release Point Strategy** (consistency vs variability)
- Calculates **Fatigue Units (FU)** with decay modeling
- Measures **Extension & Release Height** optimization

**Key Metrics:**
- `Release_Point_SD`: Standard deviation in inches
- `Release_Strategy_Classification`: Consistency (<3"), Variability (>6"), or Middle (red flag)
- `Release_Drift_Game_to_Game`: Mechanical stability (>6" = unstable)
- `Fatigue_Units_Total`: Cumulative biomechanical stress over 3 years
- `FU_Per_Game_Avg`: Average stress per game
- `FU_Risk_Score`: Injury risk from workload (0-100)
- `Extension_ft`: Release extension (>6.5 ft = elite)
- `Plate_Distance_Advantage`: Combined extension + release height score
- `Durability_Score`: Overall durability assessment (0-100)

**Why it matters:**
- Extreme consistency OR variability = optimal (middle = worst)
- Low FU load = durable arm, high FU = injury risk
- Elite extension = biomechanical advantage (closer to plate)

---

### Phase 4: Diamond Detector (`diamond_detector.py`)

**What it does:**
- Combines all signals into **Diamond Score** (composite talent metric)
- Detects **Role Mismatches** (elite talent in setup roles)
- Calculates **Value Score** (talent vs. market price)
- Filters for **Hidden Gems** (high talent, low price, low risk)

**Key Metrics:**
- `Diamond_Score`: Composite talent score (0-100)
  - Weights: 50% physics, 30% arsenal, 20% market inefficiency
- `Role_Mismatch_Score`: Underutilized talent (0-100)
- `Value_Score`: Expected value vs. projected AAV (0-100)
- `Bust_Risk_Score`: Injury/durability concerns (0-100)

**Diamond Score Formula:**
```
Diamond_Score =
    0.20 × VAA_Zone_Mismatch_Score +      # Physics edge
    0.15 × SSW_Movement_Differential +
    0.15 × Tunneling_Coherence_Score +
    0.10 × Arsenal_Synergy_Score +         # Arsenal edge
    0.10 × Effective_Velocity_Composite +
    0.10 × Cognitive_Load_Score +
    0.10 × Role_Mismatch_Score +           # Market inefficiency
    0.05 × Nash_Equilibrium_Score +
    0.05 × Release_Strategy_Score
```

**Hidden Gems Criteria:**
- Diamond Score > 75 (elite potential)
- Saves < 15 (limited closer opportunities)
- Bust Risk < 40 (durable)
- Projected AAV < $6M (undervalued)

---

### Phase 5: Advanced Reporting (`advanced_reporting.py`)

**What it does:**
- Generates **pitcher-specific profiles** with physics insights
- Creates **executive summaries** with market intelligence
- Produces **category breakdowns** (Hidden Gems, Value Plays, Avoid List)
- Exports **detailed rankings** to CSV

**Outputs:**
1. `RELIEVER_MARKET_INTELLIGENCE_EXECUTIVE_SUMMARY.md`
   - Market inefficiencies detected
   - Top value opportunities
   - Physics insights summary
   - Tier 1/2/3 recommendations

2. `PITCHER_PROFILES_DEEP_DIVE.md`
   - Individual profiles for top 10 pitchers
   - Physics edge breakdown
   - Arsenal synergy analysis
   - Biomechanical assessment
   - Signing recommendations

3. `reliever_market_intelligence_rankings.csv`
   - Complete rankings with all metrics
   - Sortable by Diamond Score, Value Score, etc.

4. `hidden_gems_targets.csv`
   - Filtered list of undervalued targets
   - High Diamond Score, low projected AAV

---

## Usage

### Running the Analysis

```bash
# Basic usage (analyzes sample free agents)
python analyze_reliever_market_intelligence.py

# With custom free agent list
# (Create CSV with columns: player_name, player_id, Projected_AAV, Age)
python analyze_reliever_market_intelligence.py --free-agents my_fa_list.csv
```

### Analysis Flow

1. **Load Free Agent List** - Sample or custom CSV
2. **Phase 1-3: Data Collection** - Fetch Statcast data, calculate all metrics
3. **Phase 4: Diamond Detection** - Composite scoring, value assessment
4. **Phase 5: Report Generation** - Profiles, summaries, rankings

### Expected Runtime

- **Per Pitcher**: ~30-60 seconds (Statcast API fetches)
- **10 Pitchers**: ~10-15 minutes
- **76 Pitchers** (full FA class): ~60-90 minutes

**Note:** Uses pybaseball caching to speed up repeated runs.

---

## Key Innovations vs. Traditional Analysis

| Traditional Stats | Advanced Market Intelligence |
|------------------|------------------------------|
| ERA, WHIP, Saves | Diamond Score (physics-based composite) |
| K/9, BB/9 | Cognitive Load Score (timing disruption) |
| Velocity, Spin Rate | VAA, SSW (trajectory physics, unexplained movement) |
| Pitch mix % | Nash Equilibrium (optimal game theory mix) |
| Pitch types | Gyro/Sweeper detection (rare arsenal combos) |
| Generic workload | Fatigue Units (biomechanical stress modeling) |
| Injury history | Durability Score (FU + mechanics stability) |
| Contract value | Value Score (physics-based true value vs. market) |

---

## Understanding the Metrics

### What Makes a Hidden Gem?

**Elite Hidden Gem Profile:**
- Diamond Score 80+ = Elite talent
- Role Mismatch 70+ = Closer talent in setup role
- Bust Risk <30 = Durable, low injury risk
- Value Score 70+ = Significantly undervalued

**Example: Hunter Harvey**
- VAA: 3.2° (Top 5% flat) → Elite fastball rise
- SSW: +4.1" unexplained movement → Natural cutter action
- Tunneling: 82/100 → Strong deception
- Gyro Slider: YES → Modern arsenal
- Release SD: 2.1" → Consistency strategy (tunneling optimized)
- FU: Bottom 25% → Durable arm
- Extension: 6.8 ft → Elite plate advantage
- **Verdict**: Elite closer stuck in setup role, $3-5M → True value $8-12M

---

## Interpreting Reports

### Pitcher Profile Structure

1. **Physics Edge** - Trajectory advantages (VAA, SSW, Tunneling)
2. **Arsenal Synergy** - Pitch combinations and cognitive load
3. **Biomechanics** - Durability and mechanical precision
4. **The Opportunity** - Market inefficiency and recommendation

### Executive Summary Sections

1. **Key Findings** - Market inefficiencies, top opportunities
2. **Category Breakdown** - Tiers (Hidden Gems, Value Plays, Avoid)
3. **Physics Insights** - VAA/SSW/Tunneling distributions
4. **Arsenal Synergy Findings** - Gyro/Sweeper combos, Nash optimization
5. **Biomechanics & Durability** - Release strategies, risk profiles
6. **Recommendations** - Tier 1/2/3 targets with contract suggestions

---

## Dependencies

```bash
pip install pandas numpy pybaseball scipy
```

### Data Sources

- **Statcast** (via pybaseball): Pitch-level data
  - Release point, velocity, spin, movement
  - Pitch outcomes, locations
- **FanGraphs/Baseball Reference**: Traditional stats (optional)

---

## Module Descriptions

### Core Analysis Modules

1. **`pitch_physics_analyzer.py`** (Phase 1)
   - `PitchPhysicsAnalyzer` class
   - Methods: `calculate_vaa()`, `calculate_ssw_effect()`, `calculate_tunneling_score()`

2. **`arsenal_synergy_analyzer.py`** (Phase 2)
   - `ArsenalSynergyAnalyzer` class
   - Methods: `detect_gyro_sweeper_combo()`, `calculate_effective_velocity()`, `calculate_nash_equilibrium_score()`

3. **`biomechanics_analyzer.py`** (Phase 3)
   - `BiomechanicsAnalyzer` class
   - Methods: `calculate_release_point_consistency()`, `calculate_fu_load()`, `calculate_extension_metrics()`

4. **`diamond_detector.py`** (Phase 4)
   - `DiamondDetector` class
   - Methods: `calculate_diamond_score()`, `identify_hidden_gems()`, `categorize_pitchers()`

5. **`advanced_reporting.py`** (Phase 5)
   - `AdvancedReporter` class
   - Methods: `generate_pitcher_profile()`, `generate_executive_summary()`, `export_detailed_rankings()`

### Main Orchestrator

- **`analyze_reliever_market_intelligence.py`**
  - `RelieverMarketIntelligence` class
  - Coordinates all phases, manages data flow

---

## Customization

### Adjusting Diamond Score Weights

Edit `diamond_detector.py`:

```python
self.weights = {
    'vaa_zone_mismatch': 0.20,     # Adjust these
    'ssw_movement': 0.15,          # to emphasize
    'tunneling': 0.15,             # different signals
    # ... etc
}
```

### Hidden Gem Thresholds

Edit `diamond_detector.identify_hidden_gems()`:

```python
hidden_gems = all_pitchers[
    (all_pitchers['Diamond_Score'] > 75) &      # Lower = more inclusive
    (all_pitchers['Saves'] < 15) &              # Raise = include partial closers
    (all_pitchers['Bust_Risk_Score'] < 40) &    # Raise = accept more risk
    (all_pitchers['Projected_AAV'] < 6)         # Raise = higher budget
]
```

### Adding Custom Metrics

1. Add calculation to appropriate analyzer class
2. Include in `analyze_reliever_complete()` merge
3. Add to Diamond Score weighting if desired
4. Update reporting template

---

## Troubleshooting

### Common Issues

**"No Statcast data available"**
- Player didn't pitch in 2024 season
- Player ID incorrect (verify at baseball-reference.com)
- Statcast API timeout (retry with longer timeout)

**"API rate limit"**
- Add longer `time.sleep()` between players
- Use pybaseball cache (enabled by default)
- Run in smaller batches

**Missing metrics (NaN values)**
- Insufficient pitch data (<50 pitches)
- Missing Statcast fields (older seasons)
- System handles gracefully with default scores

---

## Future Enhancements

### Potential Additions

1. **Platoon Splits Analysis** - VAA/Tunneling vs LHH/RHH
2. **Park Factors** - Home park effects on physics metrics
3. **Multi-Year Trends** - Trajectory of all metrics over time
4. **Peer Comparisons** - Percentile rankings vs league
5. **Contract Recommendations** - Years + AAV optimization
6. **Trade Value Model** - Extend to trade market
7. **Stuff+ Integration** - Incorporate if available
8. **Video Analysis** - Link to video clips for scouting

### Advanced Features

- **Machine Learning Models** - Predict future performance from physics
- **Injury Risk Modeling** - More sophisticated biomechanics
- **Real-Time Updates** - Daily recalculation during season
- **Interactive Dashboards** - Web UI for exploration

---

## Credits

**System Design**: Advanced physics-based market intelligence framework
**Methodology**: Combines Statcast physics, biomechanics, cognitive science, game theory
**Inspiration**: Next-generation scouting beyond traditional stats

---

## License

MIT License - Feel free to adapt and extend for your own analysis.

---

## Contact

For questions, issues, or enhancements, please open a GitHub issue.

**Happy scouting! May you find many diamonds in the rough. 💎⚾**
