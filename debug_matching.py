"""
Enhanced debug - check exact matching logic
"""
import pandas as pd
import glob

print("=" * 80)
print("DETAILED MATCHING DEBUG")
print("=" * 80)
print()

# Load one decision file
decision_files = glob.glob('output_archive/decisions/*_decisions.csv')
decisions = pd.read_csv(decision_files[0])

# Load completed games
games = pd.read_csv('data/nba_completed_games_2025_2026.csv')

# Parse dates exactly as tracker does
decisions['game_date'] = pd.to_datetime(decisions['game_time'], utc=True).dt.date
games['Date'] = pd.to_datetime(games['Date']).dt.date

# Try first prediction
pred = decisions.iloc[0]
print("PREDICTION #1:")
print(f"  Date: {pred['game_date']} (type: {type(pred['game_date'])})")
print(f"  Away: '{pred['away_team']}'")
print(f"  Home: '{pred['home_team']}'")
print()

# Look for games on same date
same_date = games[games['Date'] == pred['game_date']]
print(f"Games in completed_games on {pred['game_date']}: {len(same_date)}")
if len(same_date) > 0:
    print()
    print("Sample of games that day:")
    for idx, game in same_date.head(5).iterrows():
        print(f"  {game['Date']} | '{game['Visitor']}' @ '{game['Home']}'")
    print()
    
    # Try exact match
    print("Trying exact match (away @ home):")
    match1 = same_date[
        (same_date['Visitor'] == pred['away_team']) & 
        (same_date['Home'] == pred['home_team'])
    ]
    print(f"  Found {len(match1)} matches")
    
    print()
    print("Trying reversed match (home @ away):")
    match2 = same_date[
        (same_date['Visitor'] == pred['home_team']) & 
        (same_date['Home'] == pred['away_team'])
    ]
    print(f"  Found {len(match2)} matches")
    if len(match2) > 0:
        print()
        print("MATCH FOUND:")
        print(match2[['Date', 'Visitor', 'Home', 'Total_Points']])

print()
print("=" * 80)
print("CHECKING ALL PREDICTIONS:")
print("-" * 80)

for i in range(min(5, len(decisions))):
    pred = decisions.iloc[i]
    match = games[
        (games['Date'] == pred['game_date']) &
        (
            ((games['Visitor'] == pred['away_team']) & (games['Home'] == pred['home_team'])) |
            ((games['Visitor'] == pred['home_team']) & (games['Home'] == pred['away_team']))
        )
    ]
    status = "✓" if len(match) > 0 else "✗"
    print(f"{status} {pred['game_date']} | {pred['away_team']} @ {pred['home_team']}")