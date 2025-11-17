# 📅 NBA MINIMUM SYSTEM - DAILY WORKFLOW

**Your complete guide to running the system every day**

---

## ⏰ **WHEN TO RUN**

**Best time:** 2-4 hours before first game of the day

Example: If games start at 7pm ET, run between 3pm-5pm ET

---

## 🔄 **DAILY ROUTINE (5 MINUTES)**

### **Step 1: Update Team Stats (Weekly - Every Monday)**

```bash
# Navigate to project
cd NBA_Minimum_System

# Activate environment
source venv/bin/activate  # Mac/Linux
# OR
venv\Scripts\activate  # Windows

# Update team stats
python data_collection/bball_ref_collector.py

# Collect yesterday's results
python data_collection/game_results_collector.py

# Run backtest to revalidate system
python run_backtest.py
```

**What this does:**
- Scrapes latest team stats from Basketball Reference
- Updates offensive ratings, pace, PPG
- Saves to `data/nba_team_stats_2025_2026.csv`

**When to run:** Monday mornings (once per week)

---

### **Step 2: Get Today's Picks**

```bash
# Run master workflow
python master_workflow.py

# Step 1: Get predictions at 80% threshold
python master_workflow.py

# Step 2: Should I lower to 75% for more action?
python compare_tonight_thresholds.py

# Step 3: What's the best parlay combo?
python parlay_optimizer.py

python compare_tonight_thresholds.py

python track_minimum_results.py

python generate_dashboard.py

open min_total_dashboard.html
```

**What this does:**
1. ✅ Loads current team stats
2. ✅ Collects completed games (for form/rest analysis)
3. ✅ Fetches today's games from Odds API
4. ✅ Gets minimum alternate totals
5. ✅ Runs predictions for each game
6. ✅ Makes YES/NO decisions
7. ✅ Saves results to `output_archive/decisions/`

**Output:** You'll see a summary like this:

```
✅ WORKFLOW COMPLETE!

📊 Ready to bet: 4 YES decisions
📁 Results saved to: output_archive/decisions/2025-11-05_15-30_decisions.csv

✅ YES BETS (90%+ confidence):

MIL @ TOR
  Minimum: Over 215.5 at -1160
  Confidence: 94%
  Reasoning: Elite offense | Fast pace | Both rested
  Action: BET IT (3% bankroll)

PHI @ CHI
  Minimum: Over 218.5 at -810
  Confidence: 92%
  Reasoning: Elite offense | PHI hot | Huge buffer
  Action: BET IT (3% bankroll)
```

---

### **Step 3: Review Your Picks**

Open the CSV file:

```bash
# Location
open output_archive/decisions/[TODAY'S DATE]_decisions.csv
```
open output_archive/decisions/2025-11-04_17-30_decisions.csv
**CSV Columns:**
- `game` - Teams playing
- `minimum_total` - The line you're betting
- `decision` - YES/NO/MAYBE
- `confidence` - System confidence %
- `action` - BET IT or SKIP
- `stake` - Recommended % of bankroll
- `reasoning` - Why this decision

**What to look for:**
- ✅ YES decisions with 90%+ confidence
- ⚠️ MAYBE decisions (75-89%) - your choice
- ❌ NO decisions - never bet these

---

### **Step 4: Place Your Bets**

1. Open DraftKings
2. Navigate to NBA
3. Find "Alternate Totals"
4. Place bets on YES decisions only
5. Stake 3% of bankroll per bet

**Example:**
- Bankroll: $1,000
- Per bet: $30
- If 4 YES bets: total risk = $120

---

### **Step 5: Track Results (Next Day)**

After games finish, update your tracking:

```bash
# Collect yesterday's results
python data_collection/game_results_collector.py
```

**What this does:**
- Scrapes completed game scores
- Updates `data/nba_completed_games_2025_2026.csv`
- Used for form/rest analysis in future predictions

**Manual tracking:**
Create a simple spreadsheet:

| Date | Game | Minimum | Prediction | Actual | Result | Profit/Loss |
|------|------|---------|------------|--------|--------|-------------|
| 11/05 | MIL@TOR | 215.5 | OVER | 243 | WIN | +$25.86 |
| 11/05 | PHI@CHI | 218.5 | OVER | 227 | WIN | +$37.04 |

---

## 📊 **WEEKLY VALIDATION (Every Monday)**

```bash
# Run backtest to revalidate system
python run_backtest.py
```

**What this does:**
- Tests system against all completed games
- Calculates current win rate
- Validates 90%+ threshold still holds

**Expected output:**

```
✅ SYSTEM VALIDATED!

Win rate: 93.2% (exceeds 90% threshold)
System is ready for live betting!
```

**If below 90%:**
- Review recent failures
- Consider adjusting factor weights
- May need to pause betting until corrected

---

## 🗓️ **COMPLETE WEEKLY SCHEDULE**

### **Monday Morning (10 minutes)**
```bash
# Update all data
python data_collection/bball_ref_collector.py
python data_collection/game_results_collector.py
python run_backtest.py
```

### **Every Game Day (5 minutes)**
```bash
# 2-4 hours before first game
python master_workflow.py

# Review picks
# Place bets
```

### **Next Morning (2 minutes)**
```bash
# Update results
python data_collection/game_results_collector.py

# Update tracking spreadsheet
```

---

## 🔍 **CHECKING DATA FRESHNESS**

### **Team Stats Age**

```bash
# Check when team stats were last updated
ls -lh data/nba_team_stats_2025_2026.csv
```

**If older than 7 days:** Run team stats collector

### **Completed Games Count**

```bash
# Check how many games you have
wc -l data/nba_completed_games_2025_2026.csv
```

**Expected:** ~180 games as of early November

---

## 📁 **FILE STRUCTURE & WHAT EACH FILE DOES**

```
data/
├── nba_team_stats_2025_2026.csv      # Current season stats (update weekly)
├── nba_completed_games_2025_2026.csv # All finished games (update daily)
└── upcoming_games.csv                 # Today's games (auto-generated)

output_archive/
├── decisions/
│   └── 2025-11-05_15-30_decisions.csv # Today's picks
└── backtests/
    └── 2025-11-05_10-00_backtest.csv  # Validation results
```

---

## 🚨 **TROUBLESHOOTING**

### **"No games found"**

**Causes:**
- No games today (off day)
- Running too early (lines not posted)
- API issue

**Solution:** Wait 2-3 hours, try again

---

### **"API Error 401"**

**Cause:** API key issue

**Solution:**
1. Check `config/api_config.py`
2. Verify key at https://the-odds-api.com/account/
3. Ensure paid plan active

---

### **"Module not found"**

**Cause:** Virtual environment not activated

**Solution:**
```bash
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate     # Windows
```

---

### **Stats seem outdated**

**Solution:**
```bash
# Force refresh team stats
rm data/nba_team_stats_2025_2026.csv
python data_collection/bball_ref_collector.py
```

---

## 💡 **TIPS FOR SUCCESS**

### **Data Freshness**
- ✅ Update team stats every Monday
- ✅ Collect game results daily
- ✅ Run backtest weekly

### **Betting Discipline**
- ✅ Only bet YES decisions (90%+)
- ✅ Never exceed 3% per bet
- ✅ Skip MAYBE decisions unless confident
- ✅ Never chase losses

### **System Monitoring**
- ✅ Track every bet in spreadsheet
- ✅ Calculate running win rate
- ✅ If win rate drops below 85%, pause and investigate

---

## 📈 **SAMPLE DAILY FLOW**

**Monday 10:00 AM**
```bash
python data_collection/bball_ref_collector.py
python data_collection/game_results_collector.py
python run_backtest.py
```
Result: System validated at 93.2%

**Monday 4:00 PM** (7 games tonight)
```bash
python master_workflow.py
```
Result: 5 YES bets identified

**Monday 4:15 PM**
- Review picks
- Open DraftKings
- Place 5 bets × $30 each = $150 total risk

**Tuesday 9:00 AM**
```bash
python data_collection/game_results_collector.py
```
- Update tracking: 5-0 ✅
- Profit: $136.80

**Repeat daily!**

---

## ⚡ **QUICK REFERENCE**

| Task | Command | Frequency |
|------|---------|-----------|
| Update team stats | `python data_collection/bball_ref_collector.py` | Weekly |
| Get today's picks | `python master_workflow.py` | Daily (game days) |
| Update results | `python data_collection/game_results_collector.py` | Daily |
| Validate system | `python run_backtest.py` | Weekly |

---

## 🎯 **SUCCESS METRICS**

Track these weekly:

- **Win Rate:** Should stay above 90%
- **ROI:** Profit / Total Risked
- **Bet Volume:** How many YES bets per week
- **Longest Win Streak:** Track confidence
- **Longest Lose Streak:** Watch for system degradation

**Example tracking:**

Week 1: 24-2 (92.3%) - $720 risked, $186 profit = +25.8% ROI ✅  
Week 2: 18-3 (85.7%) - $630 risked, $98 profit = +15.6% ROI ⚠️  
Week 3: 21-1 (95.5%) - $660 risked, $231 profit = +35.0% ROI ✅

---

## 🏁 **THAT'S IT!**

Your daily routine is:
1. Run master_workflow.py (5 min)
2. Review picks
3. Bet YES decisions
4. Update results next day
5. Revalidate weekly

**Simple, systematic, profitable!**

---

**Questions? Issues? Check troubleshooting section above!**
