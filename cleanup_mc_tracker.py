"""
MC Results Tracker Cleanup
===========================
Removes duplicate entries and corrupted data from mc_results_tracker.csv
"""

import pandas as pd
import os

def cleanup_tracker():
    print("=" * 70)
    print("MC RESULTS TRACKER CLEANUP")
    print("=" * 70)
    
    if not os.path.exists('mc_results_tracker.csv'):
        print("[ERROR] mc_results_tracker.csv not found")
        return
    
    # Load tracker
    df = pd.read_csv('mc_results_tracker.csv')
    print(f"\n  Loaded {len(df)} entries")
    
    # Show current state
    print(f"\n  Current entries:")
    for _, row in df.iterrows():
        result = row.get('result', 'PENDING')
        game = row.get('game', 'Unknown')
        mc_prob = row.get('mc_probability', 0)
        print(f"    {result} | {game} | MC: {mc_prob}%")
    
    # Remove entries with NaN buffer (corrupted)
    before_nan = len(df)
    df = df.dropna(subset=['mc_probability'])
    after_nan = len(df)
    if before_nan > after_nan:
        print(f"\n  Removed {before_nan - after_nan} entries with NaN values")
    
    # Remove duplicates - keep only ONE entry per game (highest MC probability)
    before_dup = len(df)
    
    # Group by game and date, keep the one with highest mc_probability
    if 'game' in df.columns and 'date' in df.columns:
        df = df.sort_values('mc_probability', ascending=False)
        df = df.drop_duplicates(subset=['game', 'date'], keep='first')
    elif 'game' in df.columns:
        df = df.sort_values('mc_probability', ascending=False)
        df = df.drop_duplicates(subset=['game'], keep='first')
    
    after_dup = len(df)
    if before_dup > after_dup:
        print(f"  Removed {before_dup - after_dup} duplicate entries")
    
    # Show cleaned state
    print(f"\n  Cleaned entries ({len(df)} total):")
    wins = 0
    losses = 0
    pending = 0
    
    for _, row in df.iterrows():
        result = row.get('result', 'PENDING')
        game = row.get('game', 'Unknown')
        mc_prob = row.get('mc_probability', 0)
        
        if result == 'WIN':
            wins += 1
            icon = "✓"
        elif result == 'LOSS':
            losses += 1
            icon = "✗"
        else:
            pending += 1
            icon = "⏳"
        
        print(f"    {icon} {result} | {game} | MC: {mc_prob}%")
    
    # Save cleaned tracker
    df.to_csv('mc_results_tracker.csv', index=False)
    print(f"\n  ✓ Saved cleaned tracker")
    
    # Summary
    print(f"\n" + "=" * 70)
    print("CLEANED SUMMARY")
    print("=" * 70)
    
    total_completed = wins + losses
    win_rate = (wins / total_completed * 100) if total_completed > 0 else 0
    
    print(f"""
  Record: {wins}-{losses}
  Win Rate: {win_rate:.1f}%
  Pending: {pending}
    """)

if __name__ == "__main__":
    cleanup_tracker()
