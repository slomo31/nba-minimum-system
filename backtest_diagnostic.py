"""
V3.3 BACKTEST DIAGNOSTIC
=========================
Let's verify everything is correct:
1. What games are we actually testing?
2. Are the lines realistic?
3. Are team names matching correctly?
4. Is the win/loss logic correct?
5. Is there data leakage?
"""

import pandas as pd
import numpy as np
import os
from monte_carlo_engine_v3_3 import MonteCarloEngineV33


def run_diagnostic():
    """Deep dive into backtest data and logic"""
    
    print("\n" + "=" * 80)
    print("🔍 V3.3 BACKTEST DIAGNOSTIC")
    print("=" * 80)
    
    # ==========================================
    # 1. CHECK THE DATA
    # ==========================================
    
    print("\n" + "-" * 80)
    print("1️⃣ DATA CHECK")
    print("-" * 80)
    
    # Load completed games
    completed_games = pd.read_csv('data/nba_completed_games_2025_2026.csv')
    team_stats = pd.read_csv('data/nba_team_stats_2025_2026.csv')
    
    print(f"\n  Completed Games File:")
    print(f"    Total rows: {len(completed_games)}")
    print(f"    Columns: {list(completed_games.columns)}")
    
    # Check for duplicates
    dupes = completed_games.duplicated(subset=['Visitor', 'Home', 'Date']).sum()
    print(f"    Duplicates: {dupes}")
    
    # Remove duplicates for analysis
    completed_games = completed_games.drop_duplicates(subset=['Visitor', 'Home', 'Date'])
    print(f"    After dedup: {len(completed_games)} unique games")
    
    # Date range
    print(f"\n  Date Range:")
    print(f"    First game: {completed_games['Date'].iloc[0]}")
    print(f"    Last game: {completed_games['Date'].iloc[-1]}")
    
    # Sample games
    print(f"\n  Sample Games (first 5):")
    for _, row in completed_games.head(5).iterrows():
        print(f"    {row['Date']}: {row['Visitor']} @ {row['Home']} = {row['Total_Points']}")
    
    print(f"\n  Sample Games (last 5):")
    for _, row in completed_games.tail(5).iterrows():
        print(f"    {row['Date']}: {row['Visitor']} @ {row['Home']} = {row['Total_Points']}")
    
    # ==========================================
    # 2. CHECK TEAM NAME MAPPING
    # ==========================================
    
    print("\n" + "-" * 80)
    print("2️⃣ TEAM NAME MAPPING CHECK")
    print("-" * 80)
    
    # Get unique teams from both sources
    teams_in_stats = set(team_stats['Team'].unique())
    teams_in_games_visitor = set(completed_games['Visitor'].unique())
    teams_in_games_home = set(completed_games['Home'].unique())
    teams_in_games = teams_in_games_visitor | teams_in_games_home
    
    print(f"\n  Teams in stats file: {len(teams_in_stats)}")
    print(f"  Teams in games file: {len(teams_in_games)}")
    
    # Find mismatches
    in_stats_not_games = teams_in_stats - teams_in_games
    in_games_not_stats = teams_in_games - teams_in_stats
    
    if in_stats_not_games:
        print(f"\n  ⚠️ In stats but NOT in games:")
        for t in in_stats_not_games:
            print(f"    - {t}")
    
    if in_games_not_stats:
        print(f"\n  ⚠️ In games but NOT in stats:")
        for t in in_games_not_stats:
            print(f"    - {t}")
    
    if not in_stats_not_games and not in_games_not_stats:
        print(f"\n  ✅ All team names match perfectly!")
    
    # ==========================================
    # 3. CHECK LINE GENERATION
    # ==========================================
    
    print("\n" + "-" * 80)
    print("3️⃣ LINE GENERATION CHECK")
    print("-" * 80)
    
    print("""
  ⚠️ POTENTIAL ISSUE IDENTIFIED:
  
  In the backtest, we generate minimum lines like this:
    buffer = random(15, 25)
    minimum_line = actual_total - buffer
  
  This means EVERY game's line is 15-25 points BELOW the actual total.
  
  By definition, this guarantees:
    actual_total > minimum_line (ALWAYS TRUE!)
  
  This is DATA LEAKAGE - we're using the actual result to set the line!
  
  In real betting:
    - The line is set BEFORE the game
    - We don't know the actual total
    - Sometimes actual < line (we lose)
    """)
    
    # Show examples
    print(f"\n  Example of the problem:")
    sample = completed_games.head(3)
    for _, row in sample.iterrows():
        actual = row['Total_Points']
        fake_line = actual - 20  # Simulated
        print(f"    Game: {row['Visitor']} @ {row['Home']}")
        print(f"    Actual: {actual}")
        print(f"    Fake line: {fake_line:.1f} (actual - 20)")
        print(f"    Result: WIN (guaranteed because line < actual)")
        print()
    
    # ==========================================
    # 4. WHAT A REAL BACKTEST NEEDS
    # ==========================================
    
    print("\n" + "-" * 80)
    print("4️⃣ WHAT WE ACTUALLY NEED")
    print("-" * 80)
    
    print("""
  For a VALID backtest, we need:
  
  1. HISTORICAL BETTING LINES
     - What were the actual minimum alternate lines on DraftKings?
     - These are set BEFORE the game, not derived from results
  
  2. HISTORICAL TEAM STATS (at time of game)
     - Team stats BEFORE that game was played
     - Not current season-end stats
  
  3. PROPER COMPARISON
     - Line (from sportsbook) vs Actual Total
     - Some games WILL go under the line (losses)
  
  Our current backtest is INVALID because:
     - We generate lines FROM the actual results
     - This guarantees 100% win rate
     - It doesn't reflect real betting conditions
    """)
    
    # ==========================================
    # 5. CHECK ACTUAL WIN/LOSS DISTRIBUTION
    # ==========================================
    
    print("\n" + "-" * 80)
    print("5️⃣ ACTUAL TOTAL DISTRIBUTION")
    print("-" * 80)
    
    totals = completed_games['Total_Points']
    print(f"\n  Total Points Statistics:")
    print(f"    Mean: {totals.mean():.1f}")
    print(f"    Std Dev: {totals.std():.1f}")
    print(f"    Min: {totals.min():.1f}")
    print(f"    Max: {totals.max():.1f}")
    print(f"    Median: {totals.median():.1f}")
    
    print(f"\n  Distribution:")
    print(f"    < 200: {len(totals[totals < 200])} games")
    print(f"    200-210: {len(totals[(totals >= 200) & (totals < 210)])} games")
    print(f"    210-220: {len(totals[(totals >= 210) & (totals < 220)])} games")
    print(f"    220-230: {len(totals[(totals >= 220) & (totals < 230)])} games")
    print(f"    230-240: {len(totals[(totals >= 230) & (totals < 240)])} games")
    print(f"    240-250: {len(totals[(totals >= 240) & (totals < 250)])} games")
    print(f"    > 250: {len(totals[totals >= 250])} games")
    
    # ==========================================
    # 6. WHAT WE CAN DO
    # ==========================================
    
    print("\n" + "-" * 80)
    print("6️⃣ OPTIONS FOR VALID BACKTEST")
    print("-" * 80)
    
    print("""
  OPTION A: Use your historical prediction files
     - You have files in output_archive/decisions/
     - These contain REAL lines from when predictions were made
     - Match these to actual results
  
  OPTION B: Simulate realistic lines
     - Set lines based on pre-game expected totals
     - Add random variance like sportsbooks do
     - Accept that some games WILL be losses
  
  OPTION C: Use a fixed buffer approach
     - Set minimum line = expected_total - 15
     - See how often actual exceeds that
     - More realistic than using actual results
  
  RECOMMENDATION: Option A is best - use your real historical data!
    """)
    
    # ==========================================
    # 7. CHECK HISTORICAL PREDICTION FILES
    # ==========================================
    
    print("\n" + "-" * 80)
    print("7️⃣ HISTORICAL PREDICTION FILES")
    print("-" * 80)
    
    import glob
    
    # Check for prediction files
    pred_files = glob.glob('output_archive/decisions/*.csv')
    print(f"\n  Found {len(pred_files)} prediction files:")
    
    for f in sorted(pred_files)[-10:]:  # Show last 10
        print(f"    - {os.path.basename(f)}")
    
    # Try to load one and show structure
    if pred_files:
        sample_file = sorted(pred_files)[-1]
        sample_preds = pd.read_csv(sample_file)
        print(f"\n  Sample prediction file: {os.path.basename(sample_file)}")
        print(f"    Columns: {list(sample_preds.columns)}")
        print(f"    Rows: {len(sample_preds)}")
        
        # Check for line column
        line_cols = [c for c in sample_preds.columns if 'line' in c.lower() or 'total' in c.lower() or 'minimum' in c.lower()]
        print(f"    Line-related columns: {line_cols}")
    
    print("\n" + "=" * 80)
    print("📋 SUMMARY")
    print("=" * 80)
    print("""
  🚨 THE 118-0 RESULT IS INVALID
  
  Reason: We used actual game results to generate the betting lines.
  This guarantees wins and doesn't reflect real betting conditions.
  
  To get a VALID backtest, we need to:
  1. Use historical betting lines (from your prediction files)
  2. Or simulate pre-game lines without knowing results
  
  The V3.3 engine itself may still be good - we just can't prove it
  with this backtest methodology.
    """)


if __name__ == "__main__":
    run_diagnostic()
