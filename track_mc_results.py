"""
Monte Carlo Results Tracker
============================
Tracks MC predictions and their results
Similar to the legacy tracker but for MC-based picks
"""

import pandas as pd
import os
from datetime import datetime
import glob


def load_mc_predictions():
    """Load MC predictions from output archive"""
    mc_files = glob.glob('output_archive/decisions/*_mc_decisions.csv')
    if not mc_files:
        return None
    
    all_predictions = []
    for f in mc_files:
        df = pd.read_csv(f)
        # Extract date from filename
        filename = os.path.basename(f)
        date_str = filename.split('_')[0]
        df['prediction_date'] = date_str
        all_predictions.append(df)
    
    if all_predictions:
        return pd.concat(all_predictions, ignore_index=True)
    return None


def load_completed_games():
    """Load completed games for result matching"""
    if os.path.exists('data/nba_completed_games_2025_2026.csv'):
        return pd.read_csv('data/nba_completed_games_2025_2026.csv')
    return None


def track_mc_results():
    """Match MC predictions with actual results"""
    
    print("=" * 70)
    print("MONTE CARLO RESULTS TRACKER")
    print("=" * 70)
    
    # Load tracker if exists
    tracker_file = 'mc_results_tracker.csv'
    if os.path.exists(tracker_file):
        tracker = pd.read_csv(tracker_file)
        print(f"\n  ✓ Loaded existing tracker: {len(tracker)} entries")
    else:
        tracker = pd.DataFrame(columns=[
            'prediction_date', 'game', 'away_team', 'home_team',
            'minimum_total', 'mc_probability', 'mc_decision',
            'actual_total', 'result', 'buffer'
        ])
        print("\n  Creating new tracker...")
    
    # Load MC predictions
    predictions = load_mc_predictions()
    if predictions is None:
        print("  No MC predictions found in output_archive/decisions/")
        return
    
    # Load completed games
    completed = load_completed_games()
    if completed is None:
        print("  No completed games found")
        return
    
    print(f"  ✓ Found {len(predictions)} predictions")
    print(f"  ✓ Found {len(completed)} completed games")
    
    # Only track YES and STRONG_YES bets
    bettable = predictions[predictions['mc_decision'].isin(['STRONG_YES', 'YES'])]
    print(f"  ✓ {len(bettable)} bettable predictions (YES/STRONG_YES)")
    
    # Match predictions with results
    new_entries = 0
    updated_entries = 0
    
    for _, pred in bettable.iterrows():
        away = pred.get('away_team', '')
        home = pred.get('home_team', '')
        game = pred.get('game', f"{away} @ {home}")
        min_total = pred.get('minimum_total', 0)
        mc_prob = pred.get('mc_probability', 0)
        mc_decision = pred.get('mc_decision', '')
        pred_date = pred.get('prediction_date', '')
        
        # Check if already in tracker
        existing = tracker[
            (tracker['game'] == game) & 
            (tracker['minimum_total'] == min_total)
        ]
        
        if len(existing) > 0 and existing.iloc[0]['result'] != 'PENDING':
            continue  # Already tracked with result
        
        # Find matching completed game
        match = completed[
            (completed['Visitor'] == away) & 
            (completed['Home'] == home)
        ]
        
        if len(match) > 0:
            actual_total = match.iloc[0]['Total_Points']
            result = 'WIN' if actual_total > min_total else 'LOSS'
            buffer = actual_total - min_total
        else:
            actual_total = None
            result = 'PENDING'
            buffer = None
        
        # Add or update entry
        new_entry = {
            'prediction_date': pred_date,
            'game': game,
            'away_team': away,
            'home_team': home,
            'minimum_total': min_total,
            'mc_probability': mc_prob,
            'mc_decision': mc_decision,
            'actual_total': actual_total,
            'result': result,
            'buffer': buffer
        }
        
        if len(existing) > 0:
            # Update existing
            idx = existing.index[0]
            for col, val in new_entry.items():
                tracker.loc[idx, col] = val
            updated_entries += 1
        else:
            # Add new
            tracker = pd.concat([tracker, pd.DataFrame([new_entry])], ignore_index=True)
            new_entries += 1
    
    # Save tracker
    tracker.to_csv(tracker_file, index=False)
    
    # Calculate stats
    completed_bets = tracker[tracker['result'].isin(['WIN', 'LOSS'])]
    wins = len(completed_bets[completed_bets['result'] == 'WIN'])
    losses = len(completed_bets[completed_bets['result'] == 'LOSS'])
    pending = len(tracker[tracker['result'] == 'PENDING'])
    
    print(f"\n  ✓ Added {new_entries} new entries")
    print(f"  ✓ Updated {updated_entries} entries")
    print(f"  ✓ Saved to {tracker_file}")
    
    print("\n" + "=" * 70)
    print("MC RESULTS SUMMARY")
    print("=" * 70)
    
    print(f"\n  Record: {wins}-{losses}")
    if wins + losses > 0:
        print(f"  Win Rate: {wins/(wins+losses)*100:.1f}%")
    print(f"  Pending: {pending}")
    
    # Show by decision type
    print("\n  BY DECISION TYPE:")
    for decision in ['STRONG_YES', 'YES']:
        dec_bets = completed_bets[completed_bets['mc_decision'] == decision]
        dec_wins = len(dec_bets[dec_bets['result'] == 'WIN'])
        dec_total = len(dec_bets)
        if dec_total > 0:
            print(f"    {decision}: {dec_wins}-{dec_total - dec_wins} ({dec_wins/dec_total*100:.1f}%)")
    
    # Show recent results
    print("\n  RECENT RESULTS:")
    recent = completed_bets.tail(10)
    for _, row in recent.iterrows():
        emoji = "✓" if row['result'] == 'WIN' else "✗"
        print(f"    {emoji} {row['game']}: {row['mc_probability']:.1f}% → {row['result']} (buffer: {row['buffer']:.1f})")
    
    return tracker


if __name__ == "__main__":
    track_mc_results()
