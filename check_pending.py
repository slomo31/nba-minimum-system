"""
Check pending games and see if results exist
"""
import pandas as pd

print("=" * 80)
print("CHECKING PENDING GAMES")
print("=" * 80)
print()

# Load tracker results
df = pd.read_csv('min_total_results_tracker.csv')

# Get pending YES bets
pending = df[(df['decision'] == 'YES') & (df['result'] == 'PENDING')]

print(f"Total pending YES bets: {len(pending)}")
print()

if len(pending) > 0:
    print("PENDING GAMES:")
    print("-" * 80)
    for _, game in pending.iterrows():
        print(f"  {game['game_date']} | {game['game']}")
    print()
    
    # Check date range
    pending['game_date'] = pd.to_datetime(pending['game_date'])
    earliest = pending['game_date'].min()
    latest = pending['game_date'].max()
    
    print(f"Date range: {earliest.strftime('%Y-%m-%d')} to {latest.strftime('%Y-%m-%d')}")
    print()

# Check completed games file
try:
    completed = pd.read_csv('data/nba_completed_games_2025_2026.csv')
    completed['Date'] = pd.to_datetime(completed['Date'])
    
    latest_completed = completed['Date'].max()
    print(f"Latest completed game in data: {latest_completed.strftime('%Y-%m-%d')}")
    print()
    
    print("SOLUTION:")
    print("-" * 80)
    print("Run this to update completed games:")
    print("  python data_collection/game_results_collector.py")
    print()
    print("Then run:")
    print("  python track_minimum_results.py")
    print("  python generate_dashboard.py")
    
except FileNotFoundError:
    print("Completed games file not found")