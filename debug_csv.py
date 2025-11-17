"""
Debug script to check what's in the results tracker CSV
"""
import pandas as pd

print("=" * 80)
print("CHECKING RESULTS TRACKER DATA")
print("=" * 80)
print()

try:
    df = pd.read_csv('min_total_results_tracker.csv')
    
    print(f"Total rows in CSV: {len(df)}")
    print()
    
    # Check decisions
    print("DECISIONS BREAKDOWN:")
    print("-" * 80)
    for decision in df['decision'].unique():
        count = len(df[df['decision'] == decision])
        print(f"  {decision}: {count} games")
    print()
    
    # Check results
    print("RESULTS BREAKDOWN:")
    print("-" * 80)
    for result in df['result'].unique():
        count = len(df[df['result'] == result])
        print(f"  {result}: {count} games")
    print()
    
    # YES bets detail
    yes_bets = df[df['decision'] == 'YES']
    print("YES BETS DETAIL:")
    print("-" * 80)
    print(f"  Total YES bets: {len(yes_bets)}")
    
    completed_yes = yes_bets[yes_bets['result'].isin(['WIN', 'LOSS'])]
    wins = len(yes_bets[yes_bets['result'] == 'WIN'])
    losses = len(yes_bets[yes_bets['result'] == 'LOSS'])
    pending = len(yes_bets[yes_bets['result'] == 'PENDING'])
    
    print(f"  Wins: {wins}")
    print(f"  Losses: {losses}")
    print(f"  Pending: {pending}")
    print(f"  Record: {wins}-{losses}")
    print()
    
    # Show all YES bets
    print("ALL YES BETS:")
    print("-" * 80)
    for idx, row in yes_bets.iterrows():
        print(f"  {row['game_date']} | {row['game']:<50} | {row['result']:<10} | Conf: {row['confidence']}%")
    
except FileNotFoundError:
    print("ERROR: min_total_results_tracker.csv not found")
    print("Run: python track_minimum_results.py first")
except Exception as e:
    print(f"ERROR: {e}")