"""
Fixed Results Tracker - Legacy System
======================================
Reads your legacy decision CSVs and matches them to actual results
Outputs proper format for Render dashboard

This fixes the "nan%" issue by ensuring confidence values are numbers
"""

import pandas as pd
import glob
import os
from datetime import datetime


def load_all_legacy_decisions():
    """Load all legacy decision files (non-MC)"""
    
    decision_files = glob.glob('output_archive/decisions/*_decisions.csv')
    
    # Filter out MC files
    legacy_files = [f for f in decision_files if '_mc_' not in f]
    
    print(f"Found {len(legacy_files)} legacy decision files")
    
    all_decisions = []
    
    for file in sorted(legacy_files):
        try:
            df = pd.read_csv(file)
            
            # Extract date from filename
            filename = os.path.basename(file)
            date_str = filename.split('_')[0]  # 2025-12-02
            
            # Add date column
            df['prediction_date'] = date_str
            df['source_file'] = filename
            
            all_decisions.append(df)
        except Exception as e:
            print(f"Error loading {file}: {e}")
            continue
    
    if not all_decisions:
        return pd.DataFrame()
    
    combined = pd.concat(all_decisions, ignore_index=True)
    
    return combined


def load_completed_games():
    """Load completed games"""
    
    if os.path.exists('data/nba_completed_games_2025_2026.csv'):
        return pd.read_csv('data/nba_completed_games_2025_2026.csv')
    
    return pd.DataFrame()


def match_predictions_to_results(predictions_df, completed_games_df):
    """Match predictions to actual results"""
    
    results = []
    
    for _, pred in predictions_df.iterrows():
        
        # Parse game
        if 'game' in pred:
            game_str = pred['game']
        elif 'away_team' in pred and 'home_team' in pred:
            game_str = f"{pred['away_team']} @ {pred['home_team']}"
        else:
            continue
        
        if ' @ ' not in str(game_str):
            continue
        
        parts = game_str.split(' @ ')
        away_team = parts[0].strip()
        home_team = parts[1].strip()
        
        # Find matching completed game
        match = completed_games_df[
            (completed_games_df['Visitor'] == away_team) &
            (completed_games_df['Home'] == home_team)
        ]
        
        if len(match) == 0:
            # Game not played yet - mark as PENDING
            result_row = {
                'date': pred.get('prediction_date', 'Unknown'),
                'game': game_str,
                'away_team': away_team,
                'home_team': home_team,
                'minimum_line': pred.get('minimum_total', 0),
                'decision': pred.get('decision', 'UNKNOWN'),
                'confidence': float(pred.get('confidence', 0)),  # Ensure it's a number
                'actual_total': None,
                'result': 'PENDING',
                'buffer': None
            }
            results.append(result_row)
            continue
        
        # Game was played
        actual_total = match.iloc[0]['Total_Points']
        minimum_line = pred.get('minimum_total', 0)
        
        # Determine result
        if actual_total > minimum_line:
            result = 'WIN'
        else:
            result = 'LOSS'
        
        buffer = actual_total - minimum_line
        
        result_row = {
            'date': pred.get('prediction_date', 'Unknown'),
            'game': game_str,
            'away_team': away_team,
            'home_team': home_team,
            'minimum_line': minimum_line,
            'decision': pred.get('decision', 'UNKNOWN'),
            'confidence': float(pred.get('confidence', 0)),  # Ensure it's a number
            'actual_total': actual_total,
            'result': result,
            'buffer': buffer
        }
        
        results.append(result_row)
    
    return pd.DataFrame(results)


def main():
    """Generate tracker CSV for dashboard"""
    
    print("\n" + "=" * 80)
    print("📊 LEGACY RESULTS TRACKER")
    print("=" * 80)
    
    # Load decisions
    print("\nLoading legacy decision files...")
    predictions = load_all_legacy_decisions()
    
    if len(predictions) == 0:
        print("[ERROR] No decision files found")
        return
    
    print(f"[OK] Loaded {len(predictions)} predictions")
    
    # Load completed games
    print("\nLoading completed games...")
    completed = load_completed_games()
    
    if len(completed) == 0:
        print("[WARN] No completed games found")
        print("Run: python data_collection/odds_api_results_collector.py")
        return
    
    print(f"[OK] Loaded {len(completed)} completed games")
    
    # Match predictions to results
    print("\nMatching predictions to results...")
    results = match_predictions_to_results(predictions, completed)
    
    print(f"[OK] Matched {len(results)} predictions")
    
    # Calculate stats
    yes_decisions = results[results['decision'] == 'YES']
    yes_with_results = yes_decisions[yes_decisions['result'].isin(['WIN', 'LOSS'])]
    
    wins = len(yes_with_results[yes_with_results['result'] == 'WIN'])
    losses = len(yes_with_results[yes_with_results['result'] == 'LOSS'])
    pending = len(yes_decisions[yes_decisions['result'] == 'PENDING'])
    
    win_rate = (wins / len(yes_with_results) * 100) if len(yes_with_results) > 0 else 0
    
    print("\n" + "=" * 80)
    print("📈 LEGACY SYSTEM STATS")
    print("=" * 80)
    print(f"""
    YES Decisions: {len(yes_decisions)}
    
    Completed:
      Wins:   {wins}
      Losses: {losses}
      Win Rate: {win_rate:.1f}%
    
    Pending: {pending}
    """)
    
    # Save tracker
    output_file = 'min_total_results_tracker.csv'
    results.to_csv(output_file, index=False)
    print(f"[OK] Saved to {output_file}")
    
    # Show recent results
    recent = yes_with_results.tail(10)
    
    if len(recent) > 0:
        print("\n" + "=" * 80)
        print("🎯 RECENT YES BETS")
        print("=" * 80)
        
        for _, row in recent.iterrows():
            icon = "✅" if row['result'] == 'WIN' else "❌"
            print(f"{icon} {row['game']}")
            print(f"   Line: {row['minimum_line']:.1f} | Actual: {row['actual_total']:.1f} | Buffer: {row['buffer']:+.1f}")
            print()
    
    print("=" * 80)
    print("✅ TRACKER UPDATED - Deploy to Render")
    print("=" * 80)
    print("""
    Next steps:
    1. git add min_total_results_tracker.csv
    2. git commit -m "Update tracker"
    3. git push
    
    Dashboard will update automatically on Render
    """)


if __name__ == "__main__":
    main()
