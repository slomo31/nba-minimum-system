"""
Check for recent predictions (Nov 15-16)
"""
import pandas as pd
import glob

print("=" * 80)
print("CHECKING FOR RECENT PREDICTIONS")
print("=" * 80)
print()

# Load all decision files
decision_files = glob.glob('output_archive/decisions/*_decisions.csv')

# Get the most recent file
latest_file = sorted(decision_files)[-1] if decision_files else None

if latest_file:
    print(f"Most recent decision file: {latest_file}")
    print()
    
    df = pd.read_csv(latest_file)
    df['game_date'] = pd.to_datetime(df['game_time'], utc=True).dt.date
    
    print(f"Total predictions: {len(df)}")
    print()
    
    # Show YES bets
    yes_bets = df[df['decision'] == 'YES']
    print(f"YES BETS: {len(yes_bets)}")
    print("-" * 80)
    if len(yes_bets) > 0:
        for _, game in yes_bets.iterrows():
            print(f"  {game['game_date']} | {game['game']} | Conf: {game['confidence']}%")
    else:
        print("  No YES bets in this file")
    
    print()
    
    # Show all dates
    print("All dates in this file:")
    print("-" * 80)
    for date in sorted(df['game_date'].unique()):
        yes_count = len(df[(df['game_date'] == date) & (df['decision'] == 'YES')])
        no_count = len(df[(df['game_date'] == date) & (df['decision'] == 'NO')])
        maybe_count = len(df[(df['game_date'] == date) & (df['decision'] == 'MAYBE')])
        print(f"  {date}: {yes_count} YES, {maybe_count} MAYBE, {no_count} NO")
else:
    print("No decision files found!")

print()
print("=" * 80)
print("CHECKING COMPLETED GAMES")
print("=" * 80)

# Check if Nov 15 games are in completed games
import os
if os.path.exists('data/nba_completed_games_2025_2026.csv'):
    games = pd.read_csv('data/nba_completed_games_2025_2026.csv')
    games['Date'] = pd.to_datetime(games['Date'])
    
    latest_game = games['Date'].max()
    print(f"Latest completed game: {latest_game.strftime('%Y-%m-%d')}")
    
    nov15 = len(games[games['Date'].dt.date == pd.to_datetime('2025-11-15').date()])
    print(f"Nov 15 games in file: {nov15}")
    
    if nov15 == 0:
        print()
        print("⚠️  Nov 15 games NOT in completed games file yet!")
        print("Run: python data_collection/game_results_collector.py")
else:
    print("Completed games file not found")
