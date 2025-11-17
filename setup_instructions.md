# NBA MINIMUM SYSTEM - SETUP INSTRUCTIONS

## 📋 **REQUIREMENTS**

- Python 3.9 or higher
- Your Odds API key (paid plan)
- Internet connection

---

## 🚀 **SETUP STEPS**

### **1. Create Project Folder**

```bash
# Create and navigate to project folder
mkdir NBA_Minimum_System
cd NBA_Minimum_System
```

### **2. Set Up Virtual Environment**

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment

# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

You should see `(venv)` in your terminal prompt.

### **3. Install Dependencies**

```bash
# Install all required packages
pip install -r requirements.txt
```

This will install:
- pandas
- numpy
- requests
- beautifulsoup4
- scipy
- and other dependencies

### **4. Verify Installation**

```bash
# Check Python version
python --version

# Check packages
pip list
```

---

## ⚙️ **CONFIGURATION**

### **Update API Key** (if different)

Edit `config/api_config.py`:

```python
ODDS_API_KEY = "your_api_key_here"
```

---

## 🎯 **RUNNING THE SYSTEM**

### **Option 1: Daily Predictions (Live)**

```bash
# Run complete workflow for today's games
python master_workflow.py
```

This will:
1. ✅ Collect team stats
2. ✅ Fetch today's games
3. ✅ Get minimum alternates
4. ✅ Run predictions
5. ✅ Output YES/NO decisions
6. ✅ Save results to `output_archive/decisions/`

### **Option 2: Backtest (Validate System)**

```bash
# Test system against completed games
python run_backtest.py
```

This will:
1. ✅ Load all completed 2025-2026 games
2. ✅ Run predictions on each
3. ✅ Calculate accuracy
4. ✅ Validate 90%+ threshold
5. ✅ Save results to `output_archive/backtests/`

---

## 📁 **PROJECT STRUCTURE**

```
NBA_Minimum_System/
├── venv/                    # Virtual environment (created by you)
├── config/                  # Configuration files
├── data_collection/         # Data scrapers
├── analyzers/              # Factor analyzers
├── core/                   # Main prediction engine
├── decision/               # YES/NO decision maker
├── backtesting/            # Backtest system
├── output/                 # Output generators
├── data/                   # Input data (auto-created)
├── output_archive/         # All results (auto-created)
│   ├── decisions/         # Daily decisions
│   └── backtests/         # Backtest results
├── master_workflow.py      # Main command (daily)
├── run_backtest.py         # Backtest command
└── requirements.txt        # Dependencies
```

---

## 🐛 **TROUBLESHOOTING**

### **Issue: "Module not found"**

```bash
# Reinstall dependencies
pip install -r requirements.txt
```

### **Issue: "API Error"**

- Check your API key in `config/api_config.py`
- Verify API quota: https://the-odds-api.com/account/
- Ensure you have paid plan (free plan doesn't support alternates)

### **Issue: "No games found"**

- System only works on NBA game days
- Check if season is active
- Verify date/time settings

### **Issue: "Permission denied"**

```bash
# On macOS/Linux, if needed:
chmod +x master_workflow.py
chmod +x run_backtest.py
```

---

## 📊 **EXPECTED OUTPUT**

### **Daily Workflow:**

```
✅ WORKFLOW COMPLETE!

📊 Ready to bet: 6 YES decisions
📁 Results saved to: output_archive/decisions/2025-11-04_09-30_decisions.csv

YES BETS (90%+ confidence):
- HOU @ DAL: Over 212.5 at -450 (92% confidence)
- BOS @ CLE: Over 218.5 at -420 (95% confidence)
...
```

### **Backtest:**

```
✅ SYSTEM VALIDATED!

Win rate: 93.5% (exceeds 90% threshold)
System is ready for live betting!
```

---

## 🎓 **NEXT STEPS**

1. ✅ Run backtest first to validate system
2. ✅ If validated (90%+), proceed to live betting
3. ✅ Run master_workflow.py daily before games
4. ✅ Review YES decisions
5. ✅ Place bets on sportsbook
6. ✅ Track results

---

## 💡 **TIPS**

- Run backtest after every ~20 new games to revalidate
- Keep bankroll management strict (3% per bet max)
- Don't chase losses
- Trust the system's NO decisions
- Update team stats weekly (re-run master_workflow.py)

---

## 🆘 **SUPPORT**

If you encounter issues:

1. Check this file first
2. Review error messages carefully
3. Verify all files are present
4. Check Python version (3.9+)
5. Ensure virtual environment is activated

---

**Good luck! 🍀**
