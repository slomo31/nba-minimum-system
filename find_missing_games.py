"""
Find missing games - compare all decision files to tracker results
"""
import pandas as pd
import glob

print("=" * 80)
print("FINDING MISSING GAMES")
print("=" * 80)
print()

# Load all decision files
decision_files = glob.glob('output_archive/decisions/*_decisions.csv')
all_decisions = []

for file in sorted(decision_files):
    df = pd.read_csv(file)
    df['source_file'] = file
    all_decisions.append(df)

combined = pd.concat(all_decisions, ignore_index=True)

print(f"Total predictions across all files: {len(combined)}")

# Create unique game key
combined['game_time_parsed'] = pd.to_datetime(combined['game_time'], utc=True)
combined['game_key'] = (
    combined['game_time_parsed'].dt.date.astype(str) + '_' + 
    combined['away_team'] + '_' + 
    combined['home_team']
)

# Get all YES bets before deduplication
all_yes = combined[combined['decision'] == 'YES'].copy()
print(f"Total YES bets (with duplicates): {len(all_yes)}")

# Deduplicate
all_yes_sorted = all_yes.sort_values('confidence', ascending=False)
unique_yes = all_yes_sorted.drop_duplicates(subset='game_key', keep='first')
print(f"Unique YES bets: {len(unique_yes)}")
print()

# Load tracker results
tracker = pd.read_csv('min_total_results_tracker.csv')
tracker_yes = tracker[tracker['decision'] == 'YES']

print(f"YES bets in tracker: {len(tracker_yes)}")
print()

if len(unique_yes) > len(tracker_yes):
    print(f"⚠️  MISSING {len(unique_yes) - len(tracker_yes)} GAMES!")
    print()
    
    # Create game keys for tracker
    tracker['game_time_parsed'] = pd.to_datetime(tracker['game_time'], utc=True)
    tracker['game_key'] = (
        tracker['game_time_parsed'].dt.date.astype(str) + '_' + 
        tracker['away_team'] + '_' + 
        tracker['home_team']
    )
    
    tracker_keys = set(tracker_yes['game_key'].tolist())
    unique_keys = set(unique_yes['game_key'].tolist())
    
    missing_keys = unique_keys - tracker_keys
    
    print("MISSING GAMES:")
    print("-" * 80)
    for key in sorted(missing_keys):
        game = unique_yes[unique_yes['game_key'] == key].iloc[0]
        print(f"  {game['game_time_parsed'].strftime('%Y-%m-%d')} | {game['game']} | Conf: {game['confidence']}%")
    
    print()
    print("REASON:")
    print("-" * 80)
    print("These games are in your decision files but not in the tracker.")
    print("This usually means:")
    print("  1. The games haven't been played yet (future games)")
    print("  2. The completed games file doesn't have these results yet")
    print("  3. Team names don't match between sources")
    print()
    print("Check if these games happened and run:")
    print("  python data_collection/game_results_collector.py")
    print("  python track_minimum_results.py")
else:
    print("✓ All YES bets are in the tracker")
