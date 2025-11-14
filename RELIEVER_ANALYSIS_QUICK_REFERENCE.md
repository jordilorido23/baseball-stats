# Reliever Free Agent Analysis - Quick Reference

**Date:** November 13, 2025
**Status:** Phase 1 Complete (Critical Fixes Done)

---

## What We Built Today

### Phase 1: Critical Fixes (COMPLETE ✅)

1. **Fixed Missing Free Agents**
   - Before: 48/82 FAs (59%)
   - After: 76/82 FAs (93%)
   - Now includes: Edwin Díaz, Ryan Helsley, Shawn Armstrong, Danny Coulombe, Steven Matz, and 28+ others

2. **Fixed Broken Rankings**
   - Before: Chad Green (-0.9 WAR) ranked #1
   - After: Positive WAR filter → sensible rankings
   - New top 5: Brad Keller, Sean Newcomb, Robert Suarez, Phil Maton, Edwin Díaz

3. **Added Uncertainty Quantification**
   - Sample size warnings (Very Small / Small / Medium / Large)
   - Bust risk scores (0-100)
   - Confidence interval widths

4. **Built Historical Contract Model**
   - 38 reliever contracts (2020-2024)
   - AAV regression model (R² = 0.750)
   - Historical comps matching
   - Contract length recommendations

---

## Key Files

### Analysis Outputs
- `data/2025_reliever_fa_analysis_COMPLETE.csv` - 76 FAs, all metrics
- `data/2025_reliever_fa_analysis_COMPLETE_positive_war.csv` - 43 positive WAR FAs
- `RELIEVER_ANALYSIS_ASSESSMENT_AND_IMPROVEMENTS.md` - Full assessment

### Code
- `src/scripts/analyze_reliever_fa_COMPLETE.py` - Main analysis script
- `src/data/reliever_contract_database.py` - Historical contracts
- `src/analysis/contract_market_model.py` - Market value model

### Original Files (Still Valid)
- `RELIEVER_FA_EXECUTIVE_SUMMARY.md` - V1 executive summary
- `RELIEVER_FA_DEEP_DIVE_2025.md` - V2 deep dive with trends
- `src/analysis/elite_reliever_analyzer_v2.py` - V2 analyzer

---

## Top 10 Free Agents (Improved Rankings)

| Rank | Name | Age | WAR | K/9 | BB/9 | SV | Overall Score | Sample | Bust Risk |
|------|------|-----|-----|-----|------|-------|---------------|--------|-----------|
| 1 | Brad Keller | 29 | 1.3 | 9.69 | 2.84 | 3 | 65.3 | Large | Low |
| 2 | Sean Newcomb | 32 | 1.7 | 8.87 | 3.02 | 2 | 65.2 | Large | Low |
| 3 | **Robert Suarez** | 34 | 1.9 | 9.69 | 2.07 | 40 | 64.5 | Large | Low |
| 4 | **Phil Maton** | 32 | 1.5 | 11.89 | 3.38 | 5 | 62.8 | Large | Low |
| 5 | **Edwin Díaz** | 31 | 2.0 | 13.30 | 2.85 | 28 | 60.4 | Large | Low |
| 6 | Seranthony Domínguez | 30 | 0.9 | 11.35 | 5.17 | 2 | 57.9 | Large | Low |
| 7 | Emilio Pagán | 34 | 1.0 | 10.62 | 2.88 | 32 | 51.7 | Large | Low |
| 8 | Shelby Miller | 34 | 0.6 | 10.57 | 2.93 | 10 | 51.6 | Medium | Low |
| 9 | Justin Wilson | 37 | 1.0 | 10.61 | 3.72 | 0 | 50.3 | Medium | High |
| 10 | Shawn Armstrong | 34 | 1.4 | 9.00 | 2.43 | 9 | 47.7 | Large | Low |

---

## Contract Recommendations (Top 5)

### 1. Edwin Díaz (Age 31, 2.0 WAR, 28 SV, 13.3 K/9)
- **Predicted AAV:** $16.6M ($13.1M - $20.2M)
- **Recommended Contract:** 4 years, $66.5M total
- **Comps:** Josh Hader ($19M), Raisel Iglesias ($14.5M), Liam Hendriks ($13.5M)
- **Edge:** Elite closer, prime age, low bust risk

### 2. Robert Suarez (Age 34, 1.9 WAR, 40 SV, 9.69 K/9)
- **Predicted AAV:** $14-16M (closer premium)
- **Recommended Contract:** 2-3 years
- **Comps:** Kenley Jansen ($16M at age 35), Taylor Rogers ($11M at age 32)
- **Edge:** Proven closer, age 34 discount possible

### 3. Phil Maton (Age 32, 1.5 WAR, 5 SV, 11.89 K/9)
- **Predicted AAV:** $11.2M ($7.6M - $14.7M)
- **Recommended Contract:** 2 years, $22.4M total
- **Comps:** Robert Stephenson ($11M), Rafael Montero ($11.5M), Zack Britton ($13M)
- **Edge:** Elite strikeouts, setup role discount

### 4. Shelby Miller (Age 34, 0.6 WAR, 10 SV, 10.57 K/9)
- **Predicted AAV:** $6-8M
- **Recommended Contract:** 1-2 years
- **Comps:** Matt Moore ($7.5M), Andrew Chafin ($6.5M)
- **Edge:** Late-career renaissance, K% breakout (+7.2% over 3 years)

### 5. Justin Wilson (Age 37, 1.0 WAR, 0 SV, 10.61 K/9)
- **Predicted AAV:** $4-6M
- **Recommended Contract:** 1 year
- **Comps:** Brad Hand ($3M at age 33), Sergio Romo ($2.5M at age 38)
- **Edge:** Elite K rate, LOOGY specialist, age discount
- **Risk:** Age 37, high bust risk

---

## What's Still Needed (Next Phase)

### High Priority
1. **Integrate Baseball Savant Expected Stats**
   - xERA, xwOBA, xBA
   - Weight: 40% expected, 60% actual
   - Identify unlucky buy-low candidates

2. **Add Platoon Split Analysis**
   - L/R ERA splits
   - Identify platoon-neutral guys vs LOOGYs
   - Adjust value based on versatility

3. **Add Downside Scenarios**
   - Optimistic / Expected / Pessimistic WAR projections
   - Realistic expectations for volatile position

### Medium Priority
4. Monte Carlo simulations (1,000 season simulations)
5. Team-specific recommendations (closers vs setup vs bargains)
6. Leverage index analysis (gmLI)

---

## How to Use This Analysis

### For Identifying Targets
1. Start with `data/2025_reliever_fa_analysis_COMPLETE_positive_war.csv`
2. Sort by `Overall_Value_Score_V2` (high to low)
3. Filter by `Bust_Risk_Classification` = "Low Risk" or "Moderate Risk"
4. Check `Sample_Size_Classification` - prefer "Large Sample" or "Medium Sample"

### For Contract Negotiations
1. Run player through contract market model (`src/analysis/contract_market_model.py`)
2. Review historical comps (3-5 similar players)
3. Use predicted AAV range as negotiation bounds
4. Follow contract length recommendation

### For Risk Assessment
1. Check `Bust_Risk_Score` (0-100)
2. Check `Sample_Size_Classification`
3. Review velocity trends (`Velo_Trend_Classification`)
4. Review K% trends (`K_Pct_Trend_Classification`)

---

## Red Flags to Avoid

### High Bust Risk Signals
- **Very Small Sample (<20 IP)** - unreliable data
- **Declining velocity (-2+ mph over 3 years)** - injury/aging signal
- **K% collapse (-5+ percentage points)** - stuff degradation
- **Age 35+ with high workload** - injury cliff risk
- **High BB/9 (>4.5)** - control issues

### Examples from Current FA Class
- **Hunter Harvey:** Elite stuff BUT 10.2 IP only + declining velo (-2.1 mph) = Very High Bust Risk
- **Craig Kimbrel:** Adapted from sticky stuff BUT age 37 + high BB/9 (5.25) = High Risk
- **Jordan Romano:** 8.23 ERA, negative WAR, injury concerns = AVOID

---

## Market Inefficiencies Identified

### 1. Closer Premium (+79%)
- Closers avg $12.3M AAV
- Setup men avg $6.9M AAV
- **Edge:** Buy elite setup men (Phil Maton, Shelby Miller) at discount, install as closers

### 2. Sticky Stuff Adaptation Winners
- Gregory Soto: Overcame -4.7% K% drop, recovered +2.3%
- Craig Kimbrel: Overcame -14.9% K% drop, recovered +7.0%
- **Edge:** Buy adaptation winners - shows resilience

### 3. K% Breakouts (Late-Career Surges)
- Robert Suarez: +5.7% K% improvement
- Phil Maton: +5.7% K% improvement
- Shelby Miller: +7.2% K% improvement
- **Edge:** Buy breakouts, not just established stars

### 4. Small Sample + Elite Stuff = High Variance
- Hunter Harvey: 0.00 ERA, 9.28 K/9, 0.84 BB/9 BUT 10.2 IP
- Luke Weaver: High upside but low 2025 WAR
- **Edge:** Calculate true bust risk before paying for small-sample success

---

## Quick Contract Cheat Sheet

### Closer Market (30+ Saves)
- Elite (2+ WAR): $16-20M AAV, 3-5 years
- Good (1-2 WAR): $10-14M AAV, 2-3 years
- Average (<1 WAR): $6-10M AAV, 1-2 years

### Setup Market (0-10 Saves, High K)
- Elite (2+ WAR, 12+ K/9): $10-13M AAV, 2-3 years
- Good (1-2 WAR, 10+ K/9): $7-11M AAV, 2-3 years
- Average (<1 WAR): $3-6M AAV, 1-2 years

### LOOGY Market (Lefty Specialists)
- Elite (1+ WAR): $4-7M AAV, 1-2 years
- Average: $2-4M AAV, 1 year

---

## Bottom Line

**✅ Phase 1 Complete:**
- 76/82 FA coverage (93%)
- Fixed rankings (no more negative WAR at top)
- Uncertainty quantification added
- Historical contract model built

**📊 Current State:**
Solid research project with MLB-quality foundation

**🎯 Next Steps:**
Add xStats, platoon splits, downside scenarios → **MLB front office quality**

**🚀 How to Run:**
```bash
python src/scripts/analyze_reliever_fa_COMPLETE.py
```

---

**Questions?** See full assessment in `RELIEVER_ANALYSIS_ASSESSMENT_AND_IMPROVEMENTS.md`
