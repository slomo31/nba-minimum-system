"""
Monte Carlo Results Tracker V3.1
=================================
Tracks TWO separate records:
1. ACTUAL BETS (0 flags) - Real money on the line
2. TRACKED SKIPS (has flags) - For validation that flags work

This helps validate the flag system by showing:
- Would flagged games have won or lost?
- Are we correctly skipping dangerous games?
"""

import pandas as pd
import numpy as np
import os
import glob
from datetime import datetime


def load_completed_games():
    """Load completed games data"""
    if os.path.exists('data/nba_completed_games_2025_2026.csv'):
        return pd.read_csv('data/nba_completed_games_2025_2026.csv')
    return None


def find_game_result(game_str, completed_games):
    """Find actual total for a game"""
    if completed_games is None:
        return None, None
    
    # Parse game string "Away Team @ Home Team"
    if ' @ ' not in game_str:
        return None, None
    
    parts = game_str.split(' @ ')
    away_team = parts[0].strip()
    home_team = parts[1].strip()
    
    # Search for match
    for _, row in completed_games.iterrows():
        if away_team in str(row.get('Visitor', '')) and home_team in str(row.get('Home', '')):
            return row.get('Total_Points', None), row.get('Date', None)
        if away_team in str(row.get('Home', '')) and home_team in str(row.get('Visitor', '')):
            return row.get('Total_Points', None), row.get('Date', None)
    
    return None, None


def track_mc_results():
    """Main tracking function with separate records"""
    
    print("\n" + "=" * 80)
    print("🎲 MONTE CARLO V3.1 RESULTS TRACKER")
    print("=" * 80)
    
    # Load completed games
    completed_games = load_completed_games()
    if completed_games is not None:
        print(f"  ✓ Loaded {len(completed_games)} completed games")
    
    # Load or create tracker
    tracker_file = 'mc_results_tracker_v31.csv'
    
    if os.path.exists(tracker_file):
        tracker = pd.read_csv(tracker_file)
        print(f"  ✓ Loaded existing tracker: {len(tracker)} entries")
    else:
        tracker = pd.DataFrame(columns=[
            'date', 'game', 'minimum_line', 'mc_probability', 'flag_count',
            'risk_flags', 'bet_type', 'actual_total', 'result', 'buffer', 'version'
        ])
        print("  ✓ Created new tracker")
    
    # Load latest MC predictions
    mc_files = glob.glob('output_archive/decisions/*_mc_decisions.csv')
    
    if not mc_files:
        print("  [WARNING] No MC prediction files found")
        return
    
    print(f"  ✓ Found {len(mc_files)} prediction files")
    
    # Process each prediction file
    new_entries = 0
    updated_entries = 0
    
    for mc_file in mc_files:
        try:
            predictions = pd.read_csv(mc_file)
            file_date = os.path.basename(mc_file).split('_')[0]
            
            # Determine file version based on columns
            is_v31 = 'flag_count' in predictions.columns and 'minimum_line' in predictions.columns
            
            for _, pred in predictions.iterrows():
                game = pred.get('game', '')
                if not game:
                    continue
                
                mc_prob = pred.get('mc_probability', 0)
                
                # Handle different column names between V3.0 and V3.1
                if is_v31:
                    flag_count = pred.get('flag_count', 0)
                    min_line = pred.get('minimum_line', 0)
                    risk_flags = pred.get('risk_flags', '')
                else:
                    # V3.0 format - extract flag count from risk_factors
                    min_line = pred.get('minimum_total', 0)
                    risk_factors = str(pred.get('risk_factors', ''))
                    # Count flags by counting items in the list
                    if risk_factors and risk_factors != '[]' and risk_factors != 'nan':
                        # Count emoji flags or list items
                        flag_count = risk_factors.count('🎲') + risk_factors.count('🐢') + \
                                    risk_factors.count('🛡️') + risk_factors.count('⚠️') + \
                                    risk_factors.count('high variance') + risk_factors.count('slow pace')
                        if flag_count == 0 and '[' in risk_factors:
                            # Fallback: count commas + 1 if there's content
                            flag_count = risk_factors.count(',') + 1 if len(risk_factors) > 5 else 0
                    else:
                        flag_count = 0
                    risk_flags = risk_factors
                
                # Determine bet type based on flags
                if flag_count == 0 and mc_prob >= 88:
                    bet_type = 'BET'  # Actual bet (0 flags)
                else:
                    bet_type = 'SKIP'  # Tracked but not bet (has flags)
                
                # Check if already in tracker
                existing = tracker[tracker['game'] == game]
                
                if len(existing) > 0:
                    # Update existing entry with result if available
                    idx = existing.index[0]
                    
                    if tracker.loc[idx, 'result'] == 'PENDING':
                        actual_total, game_date = find_game_result(game, completed_games)
                        
                        if actual_total is not None:
                            stored_line = tracker.loc[idx, 'minimum_line']
                            result = 'WIN' if actual_total > stored_line else 'LOSS'
                            buffer = actual_total - stored_line
                            
                            tracker.loc[idx, 'actual_total'] = actual_total
                            tracker.loc[idx, 'result'] = result
                            tracker.loc[idx, 'buffer'] = buffer
                            updated_entries += 1
                else:
                    # Add new entry
                    actual_total, game_date = find_game_result(game, completed_games)
                    
                    if actual_total is not None:
                        result = 'WIN' if actual_total > min_line else 'LOSS'
                        buffer = actual_total - min_line
                    else:
                        result = 'PENDING'
                        buffer = None
                    
                    new_entry = {
                        'date': file_date,
                        'game': game,
                        'minimum_line': min_line,
                        'mc_probability': mc_prob,
                        'flag_count': flag_count,
                        'risk_flags': risk_flags,
                        'bet_type': bet_type,
                        'actual_total': actual_total,
                        'result': result,
                        'buffer': buffer,
                        'version': 'V3.1' if is_v31 else 'V3.0'
                    }
                    
                    tracker = pd.concat([tracker, pd.DataFrame([new_entry])], ignore_index=True)
                    new_entries += 1
                    
        except Exception as e:
            print(f"  [ERROR] Processing {mc_file}: {e}")
            import traceback
            traceback.print_exc()
    
    # Remove duplicates - keep most recent per game
    tracker = tracker.drop_duplicates(subset=['game'], keep='last')
    
    # Save tracker
    tracker.to_csv(tracker_file, index=False)
    print(f"\n  ✓ Added {new_entries} new entries")
    print(f"  ✓ Updated {updated_entries} entries")
    print(f"  ✓ Saved to {tracker_file}")
    
    # ==========================================
    # DISPLAY RESULTS - SEPARATED BY BET TYPE
    # ==========================================
    
    print("\n" + "=" * 80)
    print("📊 RESULTS BY CATEGORY")
    print("=" * 80)
    
    # ACTUAL BETS (0 flags)
    bets = tracker[tracker['bet_type'] == 'BET']
    bet_completed = bets[bets['result'].isin(['WIN', 'LOSS'])]
    bet_pending = bets[bets['result'] == 'PENDING']
    bet_wins = len(bet_completed[bet_completed['result'] == 'WIN'])
    bet_losses = len(bet_completed[bet_completed['result'] == 'LOSS'])
    bet_total = bet_wins + bet_losses
    bet_rate = (bet_wins / bet_total * 100) if bet_total > 0 else 0
    
    print(f"\n🎯 ACTUAL BETS (0 FLAGS) - Real Money")
    print("-" * 80)
    print(f"  Record: {bet_wins}-{bet_losses} ({bet_rate:.1f}%)")
    print(f"  Pending: {len(bet_pending)}")
    
    if len(bet_completed) > 0:
        print(f"\n  Completed:")
        for _, row in bet_completed.iterrows():
            icon = "✅" if row['result'] == 'WIN' else "❌"
            buffer = f"+{row['buffer']:.1f}" if row['buffer'] and row['buffer'] > 0 else f"{row['buffer']:.1f}" if row['buffer'] else "?"
            print(f"    {icon} {row['game']}")
            print(f"       Line: {row['minimum_line']} | Actual: {row['actual_total']} | Buffer: {buffer}")
            print(f"       MC: {row['mc_probability']:.1f}% | Flags: {row['flag_count']}")
    
    if len(bet_pending) > 0:
        print(f"\n  Pending:")
        for _, row in bet_pending.iterrows():
            print(f"    ⏳ {row['game']}")
            print(f"       Line: {row['minimum_line']} | MC: {row['mc_probability']:.1f}% | Flags: {row['flag_count']}")
    
    # TRACKED SKIPS (has flags)
    skips = tracker[tracker['bet_type'] == 'SKIP']
    skip_completed = skips[skips['result'].isin(['WIN', 'LOSS'])]
    skip_pending = skips[skips['result'] == 'PENDING']
    skip_wins = len(skip_completed[skip_completed['result'] == 'WIN'])
    skip_losses = len(skip_completed[skip_completed['result'] == 'LOSS'])
    skip_total = skip_wins + skip_losses
    skip_rate = (skip_wins / skip_total * 100) if skip_total > 0 else 0
    
    print(f"\n\n⚠️ TRACKED SKIPS (HAS FLAGS) - Not Bet")
    print("-" * 80)
    print(f"  Would-Be Record: {skip_wins}-{skip_losses} ({skip_rate:.1f}%)")
    print(f"  Pending: {len(skip_pending)}")
    
    if skip_losses > 0:
        print(f"\n  ✅ CORRECTLY SKIPPED (would have lost):")
        for _, row in skip_completed[skip_completed['result'] == 'LOSS'].iterrows():
            print(f"    🛡️ {row['game']}")
            print(f"       Line: {row['minimum_line']} | Actual: {row['actual_total']} | Missed by: {row['minimum_line'] - row['actual_total']:.1f}")
            print(f"       Flags ({row['flag_count']}): {row['risk_flags'][:60]}...")
    
    if skip_wins > 0:
        print(f"\n  ⚠️ SKIPPED BUT WOULD HAVE WON:")
        for _, row in skip_completed[skip_completed['result'] == 'WIN'].iterrows():
            print(f"    ⚠️ {row['game']}")
            print(f"       Line: {row['minimum_line']} | Actual: {row['actual_total']} | Buffer: +{row['buffer']:.1f}")
            print(f"       Flags ({row['flag_count']}): {row['risk_flags'][:60]}...")
    
    if len(skip_pending) > 0:
        print(f"\n  Pending Skips:")
        for _, row in skip_pending.head(5).iterrows():
            print(f"    ⏳ {row['game']} | Flags: {row['flag_count']}")
        if len(skip_pending) > 5:
            print(f"    ... and {len(skip_pending) - 5} more")
    
    # ==========================================
    # SUMMARY
    # ==========================================
    
    print("\n" + "=" * 80)
    print("📈 SUMMARY")
    print("=" * 80)
    
    print(f"""
  🎯 ACTUAL BETS (0 flags):     {bet_wins}-{bet_losses} ({bet_rate:.1f}%)
  ⚠️ TRACKED SKIPS (flagged):   {skip_wins}-{skip_losses} ({skip_rate:.1f}%)
  
  FLAG SYSTEM EFFECTIVENESS:
  - Correctly skipped {skip_losses} games that would have LOST
  - Missed {skip_wins} games that would have WON (acceptable trade-off)
  
  Net benefit: Avoided {skip_losses} losses by using flag system!
    """)


if __name__ == "__main__":
    track_mc_results()