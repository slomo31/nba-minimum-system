"""
V3.3 CORRECTED BACKTEST
========================
Fixes the date matching issue - matches predictions to games BY DATE

The bug was: matching only by team names, which grabbed wrong games
when teams played multiple times.
"""

import pandas as pd
import numpy as np
import os
import glob
from datetime import datetime
import re
from monte_carlo_engine_v3_3 import MonteCarloEngineV33


def parse_date_from_filename(filename):
    """Extract date from prediction filename like 2025-11-11_08-57_decisions.csv"""
    match = re.search(r'(\d{4}-\d{2}-\d{2})', filename)
    if match:
        return match.group(1)
    return None


def normalize_date(date_str):
    """Convert various date formats to YYYY-MM-DD for comparison"""
    if pd.isna(date_str):
        return None
    
    date_str = str(date_str).strip()
    
    # Format: "Fri, Nov 11, 2025" 
    try:
        dt = datetime.strptime(date_str, "%a, %b %d, %Y")
        return dt.strftime("%Y-%m-%d")
    except:
        pass
    
    # Format: "2025-11-11"
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return dt.strftime("%Y-%m-%d")
    except:
        pass
    
    return None


def run_corrected_backtest():
    """Run backtest with PROPER date matching"""
    
    print("\n" + "=" * 80)
    print("🔬 V3.3 CORRECTED BACKTEST (With Date Matching)")
    print("=" * 80)
    
    # Load data
    team_stats = pd.read_csv('data/nba_team_stats_2025_2026.csv')
    completed_games = pd.read_csv('data/nba_completed_games_2025_2026.csv')
    completed_games = completed_games.drop_duplicates(subset=['Visitor', 'Home', 'Date'])
    
    # Add normalized date column
    completed_games['norm_date'] = completed_games['Date'].apply(normalize_date)
    
    print(f"\n  ✓ Loaded {len(team_stats)} teams")
    print(f"  ✓ Loaded {len(completed_games)} completed games")
    
    # Initialize V3.3 engine
    engine = MonteCarloEngineV33(team_stats, completed_games)
    
    # Load all prediction files
    pred_files = glob.glob('output_archive/decisions/*.csv')
    print(f"\n  ✓ Found {len(pred_files)} prediction files")
    
    # Collect predictions WITH dates
    all_predictions = []
    
    for pred_file in pred_files:
        try:
            df = pd.read_csv(pred_file)
            file_date = parse_date_from_filename(os.path.basename(pred_file))
            
            if not file_date:
                continue
            
            # Get line column
            line_col = None
            for col in ['minimum_line', 'minimum_total', 'line']:
                if col in df.columns:
                    line_col = col
                    break
            
            if line_col is None:
                continue
            
            # Get game info
            for _, row in df.iterrows():
                # Get game string
                if 'game' in df.columns:
                    game = row['game']
                elif 'away_team' in df.columns and 'home_team' in df.columns:
                    game = f"{row['away_team']} @ {row['home_team']}"
                else:
                    continue
                
                line = row[line_col]
                
                if pd.isna(line) or line == 0:
                    continue
                
                if ' @ ' not in str(game):
                    continue
                
                parts = game.split(' @ ')
                away_team = parts[0].strip()
                home_team = parts[1].strip()
                
                all_predictions.append({
                    'pred_date': file_date,
                    'game': game,
                    'away_team': away_team,
                    'home_team': home_team,
                    'minimum_line': float(line),
                    'source_file': os.path.basename(pred_file)
                })
                
        except Exception as e:
            continue
    
    print(f"  ✓ Extracted {len(all_predictions)} predictions")
    
    # Remove duplicates (same game + same date)
    preds_df = pd.DataFrame(all_predictions)
    preds_df = preds_df.drop_duplicates(subset=['away_team', 'home_team', 'pred_date'], keep='first')
    print(f"  ✓ After dedup: {len(preds_df)} unique predictions")
    
    # Results storage
    results = {
        '0_flags': {'bets': 0, 'wins': 0, 'losses': 0, 'details': []},
        '1_flag': {'bets': 0, 'wins': 0, 'losses': 0, 'details': []},
        '2_flags': {'bets': 0, 'wins': 0, 'losses': 0, 'details': []},
        '3+_flags': {'bets': 0, 'wins': 0, 'losses': 0, 'details': []}
    }
    
    matched = 0
    unmatched = 0
    wrong_date_skipped = 0
    
    print(f"\n  Matching predictions to results BY DATE...")
    print("  " + "-" * 60)
    
    for _, pred in preds_df.iterrows():
        away_team = pred['away_team']
        home_team = pred['home_team']
        minimum_line = pred['minimum_line']
        pred_date = pred['pred_date']
        
        # Find matching game BY DATE
        # Prediction date should be the day BEFORE the game (or same day for evening games)
        # So we look for games on pred_date or pred_date + 1 day
        
        from datetime import timedelta
        pred_dt = datetime.strptime(pred_date, "%Y-%m-%d")
        next_day = (pred_dt + timedelta(days=1)).strftime("%Y-%m-%d")
        
        # Match by teams AND date (same day or next day)
        match = completed_games[
            (completed_games['Visitor'] == away_team) & 
            (completed_games['Home'] == home_team) &
            ((completed_games['norm_date'] == pred_date) | (completed_games['norm_date'] == next_day))
        ]
        
        if len(match) == 0:
            # Try without date restriction to see if game exists at all
            any_match = completed_games[
                (completed_games['Visitor'] == away_team) & 
                (completed_games['Home'] == home_team)
            ]
            if len(any_match) > 0:
                wrong_date_skipped += 1
            else:
                unmatched += 1
            continue
        
        matched += 1
        actual_total = match.iloc[0]['Total_Points']
        game_date = match.iloc[0]['Date']
        
        # Skip if teams not in engine
        if away_team not in engine.team_profiles or home_team not in engine.team_profiles:
            continue
        
        # Run V3.3 analysis
        analysis = engine.analyze_game(away_team, home_team, minimum_line, n_simulations=5000)
        
        if analysis is None:
            continue
        
        mc_prob = analysis['mc_probability']
        flag_count = analysis['flag_count']
        flags = analysis['flags']
        
        # Determine result
        won = actual_total > minimum_line
        
        # Categorize
        if flag_count == 0:
            category = '0_flags'
        elif flag_count == 1:
            category = '1_flag'
        elif flag_count == 2:
            category = '2_flags'
        else:
            category = '3+_flags'
        
        # Only count if MC >= 88%
        if mc_prob >= 88:
            results[category]['bets'] += 1
            
            if won:
                results[category]['wins'] += 1
                result_str = 'WIN'
            else:
                results[category]['losses'] += 1
                result_str = 'LOSS'
            
            results[category]['details'].append({
                'date': game_date,
                'pred_date': pred_date,
                'game': f"{away_team} @ {home_team}",
                'line': minimum_line,
                'actual': actual_total,
                'mc_prob': mc_prob,
                'flags': flag_count,
                'flag_list': flags,
                'result': result_str,
                'buffer': actual_total - minimum_line
            })
    
    print(f"\n  ✓ Matched (with date): {matched}")
    print(f"  ✗ Unmatched: {unmatched}")
    print(f"  ⚠️ Wrong date skipped: {wrong_date_skipped}")
    
    # ==========================================
    # RESULTS
    # ==========================================
    
    print("\n" + "=" * 80)
    print("📊 V3.3 CORRECTED BACKTEST RESULTS")
    print("=" * 80)
    
    print(f"""
    ┌────────────────────────────────────────────────────────────────────────┐
    │  FLAG COUNT    │  BETS   │  WINS   │  LOSSES  │  WIN RATE  │  STATUS  │
    ├────────────────┼─────────┼─────────┼──────────┼────────────┼──────────┤""")
    
    for category in ['0_flags', '1_flag', '2_flags', '3+_flags']:
        data = results[category]
        bets = data['bets']
        wins = data['wins']
        losses = data['losses']
        rate = (wins / bets * 100) if bets > 0 else 0
        
        status = "✅ BET" if (category == '0_flags' and rate >= 90) else ("⚠️ CHECK" if category == '0_flags' else "❌ SKIP")
        cat_display = category.replace('_', ' ').upper()
        print(f"    │  {cat_display:<12} │  {bets:>5}  │  {wins:>5}  │  {losses:>6}  │  {rate:>7.1f}%  │  {status:<6}  │")
    
    print(f"    └────────────────────────────────────────────────────────────────────────┘")
    
    # Key metric
    zero_flag = results['0_flags']
    zero_rate = (zero_flag['wins'] / zero_flag['bets'] * 100) if zero_flag['bets'] > 0 else 0
    
    print(f"\n" + "=" * 80)
    print("🎯 KEY METRIC: 0-FLAG GAMES (CORRECTED)")
    print("=" * 80)
    print(f"""
    Record:     {zero_flag['wins']}-{zero_flag['losses']}
    Win Rate:   {zero_rate:.1f}%
    Total Bets: {zero_flag['bets']}
    """)
    
    # Show losses
    if zero_flag['losses'] > 0:
        print("\n❌ 0-FLAG LOSSES:")
        print("-" * 60)
        for detail in zero_flag['details']:
            if detail['result'] == 'LOSS':
                print(f"  {detail['game']}")
                print(f"  Date: {detail['date']} (Pred: {detail['pred_date']})")
                print(f"  Line: {detail['line']} | Actual: {detail['actual']}")
                print(f"  Missed by: {detail['line'] - detail['actual']:.1f}")
                print(f"  MC: {detail['mc_prob']:.1f}% | Flags: {detail['flags']}")
                print()
    
    # Show close calls
    close_calls = [d for d in zero_flag['details'] if d['buffer'] < 5 and d['result'] == 'WIN']
    if close_calls:
        print("\n⚠️ CLOSE CALLS (Buffer < 5):")
        print("-" * 60)
        for detail in close_calls:
            print(f"  {detail['game']}")
            print(f"  Line: {detail['line']} | Actual: {detail['actual']} | Buffer: {detail['buffer']:.1f}")
            print()
    
    # Verdict
    print("\n" + "=" * 80)
    print("💡 CORRECTED VERDICT")
    print("=" * 80)
    
    if zero_flag['bets'] == 0:
        print("  ⚠️ No 0-flag games matched with dates")
    elif zero_rate >= 95:
        print(f"  ✅ V3.3 VALIDATED: {zero_rate:.1f}% win rate")
    elif zero_rate >= 85:
        print(f"  ⚠️ V3.3 ACCEPTABLE: {zero_rate:.1f}% win rate (needs monitoring)")
    else:
        print(f"  ❌ V3.3 NEEDS WORK: {zero_rate:.1f}% win rate")
    
    # Save
    output_file = f'corrected_backtest_v33_{datetime.now().strftime("%Y-%m-%d_%H-%M")}.csv'
    all_details = []
    for cat, data in results.items():
        for d in data['details']:
            d['category'] = cat
            all_details.append(d)
    
    if all_details:
        pd.DataFrame(all_details).to_csv(output_file, index=False)
        print(f"\n  ✓ Results saved to: {output_file}")


if __name__ == "__main__":
    run_corrected_backtest()
