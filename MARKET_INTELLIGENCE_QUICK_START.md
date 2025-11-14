# Quick Start Guide - Advanced Reliever Market Intelligence

## Installation

```bash
# Install dependencies
pip install pandas numpy pybaseball scipy

# Verify installation
python -c "import pybaseball; print('✓ Ready to analyze!')"
```

## Running Your First Analysis

### Option 1: Quick Test (Sample Data)

```bash
# Run with built-in sample of 10 free agents
python analyze_reliever_market_intelligence.py
```

This will analyze a sample of notable 2024-25 free agents including:
- Hunter Harvey
- Tanner Scott
- Jeff Hoffman
- Carlos Estévez
- Clay Holmes
- And 5 more...

**Expected runtime**: ~10-15 minutes

### Option 2: Custom Free Agent List

1. Create a CSV file with your target free agents:

```csv
player_name,player_id,Projected_AAV,Age
Hunter Harvey,663961,4.0,29
Tanner Scott,605463,12.0,30
```

2. Run the analysis:

```bash
python analyze_reliever_market_intelligence.py
```

## Understanding the Output

After analysis completes, you'll see 4 output files:

### 1. Executive Summary (Markdown)
**File**: `RELIEVER_MARKET_INTELLIGENCE_EXECUTIVE_SUMMARY.md`

**Contains**:
- Market inefficiencies detected
- Top value opportunities (Top 5 hidden gems)
- Category breakdown (Elite Gems, Value Plays, Avoid)
- Physics insights (VAA, SSW, Tunneling distributions)
- Tier 1/2/3 recommendations with contract suggestions

**Read this first** for high-level insights and top targets.

### 2. Pitcher Profiles (Markdown)
**File**: `PITCHER_PROFILES_DEEP_DIVE.md`

**Contains**:
- Deep dive profiles for top 10 pitchers
- Physics edge breakdown (VAA, SSW, Tunneling)
- Arsenal synergy analysis (Gyro/Sweeper, Effective Velocity)
- Biomechanical assessment (Release Point, Fatigue Units, Extension)
- Specific signing recommendations

**Use this** for detailed scouting reports on top targets.

### 3. Complete Rankings (CSV)
**File**: `reliever_market_intelligence_rankings.csv`

**Columns include**:
- Diamond_Score, Diamond_Rank
- Value_Score, Value_Rank
- All physics metrics (VAA, SSW, Tunneling)
- All arsenal metrics (Arsenal_Synergy, Cognitive_Load)
- All biomechanics metrics (Durability, FU_Risk)

**Use this** for sorting, filtering, and custom analysis in Excel/Python.

### 4. Hidden Gems List (CSV)
**File**: `hidden_gems_targets.csv`

**Filtered for**:
- Diamond Score > 75 (elite talent)
- Saves < 15 (underutilized)
- Bust Risk < 40 (durable)
- Projected AAV < $6M (undervalued)

**Use this** as your priority acquisition list.

## Key Metrics Cheat Sheet

### Diamond Score (0-100)
**What it is**: Composite talent score combining physics, arsenal, biomechanics

- **90+**: Elite, franchise closer level
- **80-90**: Premium closer/elite setup
- **70-80**: Good closer/very good setup
- **60-70**: Solid setup/middle reliever
- **<60**: Depth piece

### Value Score (0-100)
**What it is**: Expected value vs. projected market price

- **80+**: Massive value opportunity (sign immediately!)
- **70-80**: Strong value play
- **60-70**: Modest upside
- **50-60**: Fair value
- **<50**: Overpriced, avoid

### Bust Risk Score (0-100)
**What it is**: Injury/durability concerns (LOWER is better)

- **<25**: Low risk, durable profile
- **25-40**: Manageable risk
- **40-60**: Moderate injury concerns
- **60+**: HIGH RISK - injury red flags

### Role Mismatch Score (0-100)
**What it is**: Underutilization level (higher = more wasted talent)

- **70+**: Elite closer stuck in setup role
- **50-70**: Closer talent, partial usage
- **30-50**: Role fairly appropriate
- **<30**: Properly utilized

## Next Steps

1. **Review Executive Summary** - Get high-level insights
2. **Read Top 5 Pitcher Profiles** - Deep dive on best targets
3. **Sort Hidden Gems CSV** - Filter by your team's budget/needs
4. **Cross-reference with video** - Confirm physics with scouting
5. **Make acquisition decisions** - Target undervalued gems!

---

**You're ready to find diamonds in the rough! 💎⚾**

For detailed methodology and technical docs, see `ADVANCED_MARKET_INTELLIGENCE_README.md`
