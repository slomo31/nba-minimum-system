"""
MC Results Tracker - Manual Fix
================================
Fixes the Orlando @ Detroit entry and removes bad data
"""

import pandas as pd
import os

def fix_tracker():
    print("=" * 70)
    print("MC RESULTS TRACKER - MANUAL FIX")
    print("=" * 70)
    
    if not os.path.exists('mc_results_tracker.csv'):
        print("[ERROR] mc_results_tracker.csv not found")
        return
    
    # Load tracker
    df = pd.read_csv('mc_results_tracker.csv')
    print(f"\n  Loaded {len(df)} entries")
    
    print("\n  Before fix:")
    for _, row in df.iterrows():
        print(f"    {row.get('result', '?')} | {row.get('game', '?')} | MC: {row.get('mc_probability', 0)}% | Line: {row.get('minimum_line', '?')}")
    
    # Fix Orlando @ Detroit - the game went OVER, so it's a WIN
    # The actual total was 251 (Orlando 131, Detroit 120)
    orlando_mask = df['game'].str.contains('Orlando', na=False) & df['game'].str.contains('Detroit', na=False)
    
    if orlando_mask.any():
        print(f"\n  Found {orlando_mask.sum()} Orlando @ Detroit entries")
        
        # Get the line for this game
        orlando_rows = df[orlando_mask]
        for idx, row in orlando_rows.iterrows():
            line = row.get('minimum_line', 211.5)
            print(f"    Entry {idx}: Line {line}, Result: {row.get('result', '?')}")
        
        # The actual total was 251 - way over any line
        # Set all Orlando @ Detroit to WIN
        df.loc[orlando_mask, 'result'] = 'WIN'
        df.loc[orlando_mask, 'actual_total'] = 251.0
        
        # Keep only one entry (the V3.1 one with 99.81%)
        orlando_indices = df[orlando_mask].index.tolist()
        if len(orlando_indices) > 1:
            # Keep the first one, drop the rest
            df = df.drop(orlando_indices[1:])
            print(f"    Removed {len(orlando_indices) - 1} duplicate Orlando entries")
    
    print("\n  After fix:")
    for _, row in df.iterrows():
        result = row.get('result', 'PENDING')
        icon = "✓" if result == 'WIN' else ("✗" if result == 'LOSS' else "⏳")
        print(f"    {icon} {result} | {row.get('game', '?')} | MC: {row.get('mc_probability', 0)}%")
    
    # Save
    df.to_csv('mc_results_tracker.csv', index=False)
    print(f"\n  ✓ Saved fixed tracker")
    
    # Summary
    wins = len(df[df['result'] == 'WIN'])
    losses = len(df[df['result'] == 'LOSS'])
    pending = len(df[df['result'] == 'PENDING'])
    
    total = wins + losses
    win_rate = (wins / total * 100) if total > 0 else 0
    
    print(f"\n" + "=" * 70)
    print("CORRECTED SUMMARY")
    print("=" * 70)
    print(f"""
  Record: {wins}-{losses}
  Win Rate: {win_rate:.1f}%
  Pending: {pending}
  
  Note: Orlando @ Detroit actual total was 251
        Line was 211.5 → WIN by 39.5 points!
    """)

if __name__ == "__main__":
    fix_tracker()
