# Results Tracker - Setup Instructions

## What This Does

The `track_minimum_results.py` script reads all your past prediction files and matches them against completed games to show:

1. **YES BETS**: Your W-L record with each game shown
2. **NO BETS**: Games you skipped, with warnings for missed opportunities
3. **Summary Stats**: Win rate, ROI estimate

## How to Use

### Step 1: Save the Script

Save `track_minimum_results.py` to your NBA project root directory (same folder as `master_workflow.py`)

### Step 2: Make Sure You Have These Files

The script needs:
- `output_archive/decisions/` folder with your past decision CSVs
- `data/nba_completed_games_2025_2026.csv` with game results

### Step 3: Run It

```bash
cd /path/to/your/NBA_project
python track_minimum_results.py
```

## Expected Output

```
================================================================================
MINIMUM TOTAL SYSTEM - 2025-2026 SEASON RESULTS
================================================================================

YES BETS: 42-12 (77.8%) - 5 pending
--------------------------------------------------------------------------------

✓ WIN | 2024-11-09 | Houston Rockets @ Milwaukee Bucks
     Line: 210.5 | Actual: 220.0 | Conf: 92%

✓ WIN | 2024-11-09 | Detroit Pistons @ Philadelphia 76ers
     Line: 210.5 | Actual: 240.7 | Conf: 87%

✗ LOSS | 2024-11-10 | Brooklyn Nets @ New York Knicks
     Line: 206.5 | Actual: 253.0 | Conf: 82%

... (more games)

NO BETS: 100 games skipped
--------------------------------------------------------------------------------

✓ CORRECT | 2024-11-09 | Indiana Pacers @ Golden State Warriors
        Line: 207.5 | Actual: 226.4 | Conf: 52%

⚠️  MISSED | 2024-11-10 | Boston Celtics @ Orlando Magic
        Line: 206.5 | Actual: 197.0 | Conf: 72%

... (more games)

⚠️  MISSED 8 OPPORTUNITIES (would have won if we bet)
✓ 92 CORRECT SKIPS (game went under minimum)

================================================================================

SUMMARY
--------------------------------------------------------------------------------
Completed YES bets: 54
Win rate: 77.8%
Estimated ROI: +12.3% (assuming -450 avg odds)
```

## Troubleshooting

**"No decision files found"**
- Make sure you're in the right directory
- Check that `output_archive/decisions/` exists
- Verify you have CSV files in that folder

**"No completed games file found"**
- Run `python data_collection/game_results_collector.py` first
- This creates/updates the completed games CSV

**Matches not working**
- Team names must match exactly between files
- Dates must match
- Script will show "Matched X predictions" - if 0, check data format

## What Gets Saved

The script also saves a full CSV file:
- `min_total_results_tracker.csv` - All your predictions with results

You can open this in Excel to sort, filter, and analyze however you want.
