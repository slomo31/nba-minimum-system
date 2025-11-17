"""
Find all tracker CSV files
"""
import glob
import os
import pandas as pd

print("=" * 80)
print("SEARCHING FOR ALL TRACKER FILES")
print("=" * 80)
print()

# Search for tracker files
patterns = [
    '*tracker*.csv',
    '**/*tracker*.csv',
    '*results*.csv',
    '**/*results*.csv'
]

all_trackers = set()
for pattern in patterns:
    files = glob.glob(pattern, recursive=True)
    for f in files:
        if 'tracker' in f.lower() or 'results' in f.lower():
            all_trackers.add(os.path.abspath(f))

print(f"Found {len(all_trackers)} tracker-related files:")
print("-" * 80)
print()

for f in sorted(all_trackers):
    print(f"FILE: {f}")
    
    # Get modification time
    import datetime
    mtime = datetime.datetime.fromtimestamp(os.path.getmtime(f))
    print(f"  Modified: {mtime.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Try to read it
    try:
        df = pd.read_csv(f)
        yes_bets = df[df['decision'] == 'YES']
        wins = len(yes_bets[yes_bets['result'] == 'WIN'])
        losses = len(yes_bets[yes_bets['result'] == 'LOSS'])
        pending = len(yes_bets[yes_bets['result'] == 'PENDING'])
        
        print(f"  YES bets: {len(yes_bets)} ({wins}-{losses}, {pending} pending)")
    except Exception as e:
        print(f"  Error reading: {e}")
    
    print()

print("=" * 80)
print("WHICH FILE SHOULD BE USED?")
print("-" * 80)
print("The dashboard generator reads: min_total_results_tracker.csv")
print("Make sure this is the file with your complete data!")
