"""
Investigate Boston @ Philly Discrepancy
========================================
The legacy system shows this as a LOSS, but backtest shows WIN
Let's find out what's happening
"""

import pandas as pd
import glob

def investigate():
    print("\n" + "=" * 80)
    print("🔍 INVESTIGATING: Boston Celtics @ Philadelphia 76ers")
    print("=" * 80)
    
    # Load completed games
    completed = pd.read_csv('data/nba_completed_games_2025_2026.csv')
    
    # Find ALL Boston @ Philly games
    print("\n1️⃣ ALL Boston @ Philly games in completed_games.csv:")
    print("-" * 60)
    
    matches = completed[
        (completed['Visitor'] == 'Boston Celtics') & 
        (completed['Home'] == 'Philadelphia 76ers')
    ]
    
    for _, row in matches.iterrows():
        print(f"  Date: {row['Date']}")
        print(f"  Boston: {row['Visitor_PTS']}, Philly: {row['Home_PTS']}")
        print(f"  Total: {row['Total_Points']}")
        print()
    
    # Check prediction files for this game
    print("\n2️⃣ Boston @ Philly in prediction files:")
    print("-" * 60)
    
    pred_files = glob.glob('output_archive/decisions/*.csv')
    
    for pred_file in sorted(pred_files):
        try:
            df = pd.read_csv(pred_file)
            
            # Look for Boston @ Philly
            for col in ['game', 'matchup']:
                if col in df.columns:
                    match = df[df[col].str.contains('Boston', na=False) & 
                              df[col].str.contains('Philadelphia', na=False)]
                    if len(match) > 0:
                        print(f"\n  File: {pred_file.split('/')[-1]}")
                        for _, row in match.iterrows():
                            line_col = 'minimum_line' if 'minimum_line' in df.columns else 'minimum_total'
                            line = row.get(line_col, 'N/A')
                            print(f"  Line: {line}")
        except Exception as e:
            continue
    
    # Check backtest results
    print("\n3️⃣ Boston @ Philly in backtest results:")
    print("-" * 60)
    
    result_files = glob.glob('valid_backtest_v33_*.csv')
    if result_files:
        results = pd.read_csv(sorted(result_files)[-1])
        match = results[results['game'].str.contains('Boston', na=False) & 
                       results['game'].str.contains('Philadelphia', na=False)]
        
        for _, row in match.iterrows():
            print(f"  Game: {row['game']}")
            print(f"  Line: {row['line']}")
            print(f"  Actual: {row['actual']}")
            print(f"  Result: {row['result']}")
            print(f"  Category: {row['category']}")
            print()
    
    # The issue
    print("\n4️⃣ THE ISSUE:")
    print("-" * 60)
    print("""
    There might be TWO Boston @ Philly games:
    
    1. Earlier game: Total = 217 (WIN if line was 209.5)
    2. Later game: Total = 202 (LOSS if line was 209.5)
    
    The backtest matched to the WRONG game!
    
    This is because our matching logic uses:
      (away_team == 'Boston') AND (home_team == 'Philly')
    
    But doesn't check the DATE!
    
    We need to match predictions to games BY DATE, not just teams.
    """)


if __name__ == "__main__":
    investigate()
