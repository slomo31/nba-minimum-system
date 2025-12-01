"""
V3.3 VALID BACKTEST
====================
Uses REAL historical prediction files with actual DraftKings minimum lines
to test what V3.3 flags would have caught.

This is a proper backtest because:
1. Lines come from DraftKings (set BEFORE games)
2. Results come from actual games
3. We retroactively apply V3.3 flag logic to see what would have happened
"""

import pandas as pd
import numpy as np
import os
import glob
from datetime import datetime
from monte_carlo_engine_v3_3 import MonteCarloEngineV33


def run_valid_backtest():
    """Run backtest using real historical predictions and results"""
    
    print("\n" + "=" * 80)
    print("🔬 V3.3 VALID BACKTEST (Real Lines)")
    print("=" * 80)
    print("Using actual DraftKings lines from historical prediction files...")
    
    # Load current data
    team_stats = pd.read_csv('data/nba_team_stats_2025_2026.csv')
    completed_games = pd.read_csv('data/nba_completed_games_2025_2026.csv')
    completed_games = completed_games.drop_duplicates(subset=['Visitor', 'Home', 'Date'])
    
    print(f"\n  ✓ Loaded {len(team_stats)} teams")
    print(f"  ✓ Loaded {len(completed_games)} completed games")
    
    # Initialize V3.3 engine
    engine = MonteCarloEngineV33(team_stats, completed_games)
    
    # Load all historical prediction files
    pred_files = glob.glob('output_archive/decisions/*.csv')
    print(f"\n  ✓ Found {len(pred_files)} prediction files")
    
    # Collect all predictions with real lines
    all_predictions = []
    
    for pred_file in pred_files:
        try:
            df = pd.read_csv(pred_file)
            file_date = os.path.basename(pred_file).split('_')[0]
            
            # Look for line column (different formats)
            line_col = None
            for col in ['minimum_line', 'minimum_total', 'line']:
                if col in df.columns:
                    line_col = col
                    break
            
            if line_col is None:
                continue
            
            # Get game column
            game_col = None
            for col in ['game', 'matchup']:
                if col in df.columns:
                    game_col = col
                    break
            
            if game_col is None and 'away_team' in df.columns and 'home_team' in df.columns:
                df['game'] = df['away_team'] + ' @ ' + df['home_team']
                game_col = 'game'
            
            if game_col is None:
                continue
            
            for _, row in df.iterrows():
                game = row[game_col]
                line = row[line_col]
                
                if pd.isna(line) or line == 0:
                    continue
                
                # Parse teams from game string
                if ' @ ' in str(game):
                    parts = game.split(' @ ')
                    away_team = parts[0].strip()
                    home_team = parts[1].strip()
                else:
                    continue
                
                all_predictions.append({
                    'file_date': file_date,
                    'game': game,
                    'away_team': away_team,
                    'home_team': home_team,
                    'minimum_line': float(line),
                    'source_file': os.path.basename(pred_file)
                })
                
        except Exception as e:
            print(f"  [WARN] Error reading {pred_file}: {e}")
            continue
    
    print(f"  ✓ Extracted {len(all_predictions)} predictions with lines")
    
    # Remove duplicate predictions (same game, keep first)
    preds_df = pd.DataFrame(all_predictions)
    preds_df = preds_df.drop_duplicates(subset=['away_team', 'home_team'], keep='first')
    print(f"  ✓ After dedup: {len(preds_df)} unique game predictions")
    
    # Match predictions to actual results
    results = {
        '0_flags': {'bets': 0, 'wins': 0, 'losses': 0, 'details': []},
        '1_flag': {'bets': 0, 'wins': 0, 'losses': 0, 'details': []},
        '2_flags': {'bets': 0, 'wins': 0, 'losses': 0, 'details': []},
        '3+_flags': {'bets': 0, 'wins': 0, 'losses': 0, 'details': []}
    }
    
    matched = 0
    unmatched = 0
    
    print(f"\n  Matching predictions to results...")
    print("  " + "-" * 60)
    
    for _, pred in preds_df.iterrows():
        away_team = pred['away_team']
        home_team = pred['home_team']
        minimum_line = pred['minimum_line']
        
        # Find matching completed game
        match = completed_games[
            (completed_games['Visitor'] == away_team) & 
            (completed_games['Home'] == home_team)
        ]
        
        if len(match) == 0:
            unmatched += 1
            continue
        
        matched += 1
        actual_total = match.iloc[0]['Total_Points']
        game_date = match.iloc[0]['Date']
        
        # Skip if teams not in engine
        if away_team not in engine.team_profiles or home_team not in engine.team_profiles:
            continue
        
        # Run V3.3 analysis with REAL line
        analysis = engine.analyze_game(away_team, home_team, minimum_line, n_simulations=5000)
        
        if analysis is None:
            continue
        
        mc_prob = analysis['mc_probability']
        flag_count = analysis['flag_count']
        flags = analysis['flags']
        
        # Determine actual result
        won = actual_total > minimum_line
        
        # Categorize by flag count
        if flag_count == 0:
            category = '0_flags'
        elif flag_count == 1:
            category = '1_flag'
        elif flag_count == 2:
            category = '2_flags'
        else:
            category = '3+_flags'
        
        # Only count if MC probability >= 88%
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
                'game': f"{away_team} @ {home_team}",
                'line': minimum_line,
                'actual': actual_total,
                'mc_prob': mc_prob,
                'flags': flag_count,
                'flag_list': flags,
                'result': result_str,
                'buffer': actual_total - minimum_line
            })
    
    print(f"\n  ✓ Matched: {matched} games")
    print(f"  ✗ Unmatched: {unmatched} games (not yet played or team name mismatch)")
    
    # ==========================================
    # PRINT RESULTS
    # ==========================================
    
    print("\n" + "=" * 80)
    print("📊 V3.3 VALID BACKTEST RESULTS")
    print("=" * 80)
    
    print(f"""
    ┌────────────────────────────────────────────────────────────────────────┐
    │  FLAG COUNT    │  BETS   │  WINS   │  LOSSES  │  WIN RATE  │  STATUS  │
    ├────────────────┼─────────┼─────────┼──────────┼────────────┼──────────┤""")
    
    total_bets = 0
    total_wins = 0
    total_losses = 0
    
    for category in ['0_flags', '1_flag', '2_flags', '3+_flags']:
        data = results[category]
        bets = data['bets']
        wins = data['wins']
        losses = data['losses']
        rate = (wins / bets * 100) if bets > 0 else 0
        
        total_bets += bets
        total_wins += wins
        total_losses += losses
        
        if category == '0_flags':
            status = "✅ BET" if rate >= 90 else "⚠️ CHECK"
        else:
            status = "❌ SKIP"
        
        cat_display = category.replace('_', ' ').upper()
        print(f"    │  {cat_display:<12} │  {bets:>5}  │  {wins:>5}  │  {losses:>6}  │  {rate:>7.1f}%  │  {status:<6}  │")
    
    print(f"    └────────────────────────────────────────────────────────────────────────┘")
    
    # Overall
    overall_rate = (total_wins / total_bets * 100) if total_bets > 0 else 0
    print(f"\n    OVERALL: {total_wins}-{total_losses} ({overall_rate:.1f}%)")
    
    # Key metric
    zero_flag = results['0_flags']
    zero_rate = (zero_flag['wins'] / zero_flag['bets'] * 100) if zero_flag['bets'] > 0 else 0
    
    print(f"\n" + "=" * 80)
    print("🎯 KEY METRIC: 0-FLAG GAMES")
    print("=" * 80)
    print(f"""
    Record:     {zero_flag['wins']}-{zero_flag['losses']}
    Win Rate:   {zero_rate:.1f}%
    Total Bets: {zero_flag['bets']}
    """)
    
    # Show ALL 0-flag results
    if zero_flag['details']:
        print("\n  0-FLAG GAME DETAILS:")
        print("  " + "-" * 70)
        for detail in zero_flag['details']:
            icon = "✅" if detail['result'] == 'WIN' else "❌"
            buffer = detail['buffer']
            buffer_str = f"+{buffer:.1f}" if buffer > 0 else f"{buffer:.1f}"
            print(f"  {icon} {detail['game']}")
            print(f"     Line: {detail['line']:.1f} | Actual: {detail['actual']:.1f} | Buffer: {buffer_str}")
            print(f"     MC: {detail['mc_prob']:.1f}% | Flags: {detail['flags']}")
            print()
    
    # Show losses in flagged games (correctly avoided)
    flagged_losses = []
    for cat in ['1_flag', '2_flags', '3+_flags']:
        for detail in results[cat]['details']:
            if detail['result'] == 'LOSS':
                flagged_losses.append(detail)
    
    if flagged_losses:
        print("\n" + "=" * 80)
        print("🛡️ LOSSES WE AVOIDED (Flagged games that lost)")
        print("=" * 80)
        for detail in flagged_losses:
            print(f"  🛡️ {detail['game']}")
            print(f"     Line: {detail['line']:.1f} | Actual: {detail['actual']:.1f} | Missed by: {detail['line'] - detail['actual']:.1f}")
            print(f"     Flags ({detail['flags']}): {detail['flag_list'][:2] if detail['flag_list'] else 'N/A'}")
            print()
    
    # Recommendation
    print("\n" + "=" * 80)
    print("💡 VERDICT")
    print("=" * 80)
    
    if zero_flag['bets'] == 0:
        print("""
    ⚠️ NOT ENOUGH DATA
    
    No 0-flag games found in historical predictions.
    Need more prediction history to validate V3.3.
        """)
    elif zero_rate >= 95:
        print(f"""
    ✅ V3.3 VALIDATED
    
    - 0-flag win rate: {zero_rate:.1f}%
    - Record: {zero_flag['wins']}-{zero_flag['losses']}
    - Safe to use in production
        """)
    elif zero_rate >= 85:
        print(f"""
    ⚠️ V3.3 ACCEPTABLE (but needs monitoring)
    
    - 0-flag win rate: {zero_rate:.1f}%
    - Record: {zero_flag['wins']}-{zero_flag['losses']}
    - Consider tightening some thresholds
        """)
    else:
        print(f"""
    ❌ V3.3 NEEDS WORK
    
    - 0-flag win rate: {zero_rate:.1f}%
    - Too many losses
    - Need to add more flags or tighten thresholds
        """)
    
    # Save results
    output_file = f'valid_backtest_v33_{datetime.now().strftime("%Y-%m-%d_%H-%M")}.csv'
    all_details = []
    for cat, data in results.items():
        for d in data['details']:
            d['category'] = cat
            all_details.append(d)
    
    if all_details:
        pd.DataFrame(all_details).to_csv(output_file, index=False)
        print(f"\n  ✓ Results saved to: {output_file}")


if __name__ == "__main__":
    run_valid_backtest()
