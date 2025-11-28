"""
V3.0 vs V3.1 Backtest Comparison
=================================
Tests both MC versions against completed games to compare:
1. Win rates at different thresholds
2. False positive rates
3. Flag system effectiveness
"""

import pandas as pd
import numpy as np
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def run_comparison_backtest():
    """Run backtest comparing V3.0 vs V3.1"""
    
    print("=" * 80)
    print("V3.0 vs V3.1 COMPARISON BACKTEST")
    print("=" * 80)
    
    # Load data
    print("\nLoading data...")
    
    if os.path.exists('data/nba_team_stats_2025_2026.csv'):
        team_stats = pd.read_csv('data/nba_team_stats_2025_2026.csv')
        completed_games = pd.read_csv('data/nba_completed_games_2025_2026.csv')
    else:
        print("ERROR: Data files not found!")
        print("Looking for: data/nba_team_stats_2025_2026.csv")
        return
    
    print(f"  ✓ {len(team_stats)} teams")
    print(f"  ✓ {len(completed_games)} completed games")
    
    # Import both engines
    print("\nInitializing engines...")
    
    try:
        from monte_carlo_engine_v3_1 import MonteCarloEngineV31
        engine_v31 = MonteCarloEngineV31(team_stats, completed_games, n_simulations=1000, check_injuries=False)
        print("  ✓ V3.1 engine loaded")
    except ImportError as e:
        print(f"  ✗ V3.1 engine failed: {e}")
        return
    
    try:
        from core.monte_carlo_engine import MonteCarloEngineV3
        engine_v30 = MonteCarloEngineV3(team_stats, completed_games, n_simulations=1000, check_injuries=False)
        print("  ✓ V3.0 engine loaded")
    except ImportError:
        print("  ⚠️ V3.0 engine not found - will only test V3.1")
        engine_v30 = None
    
    # Run backtest
    print("\n" + "=" * 80)
    print("RUNNING BACKTEST")
    print("=" * 80)
    
    results_v31 = []
    results_v30 = []
    
    for idx, game in completed_games.iterrows():
        if idx % 50 == 0:
            print(f"  Processing game {idx+1}/{len(completed_games)}...")
        
        away_team = game['Visitor']
        home_team = game['Home']
        actual_total = game['Total_Points']
        
        # Estimate Vegas line from team PPGs
        away_row = team_stats[team_stats['Team'] == away_team]
        home_row = team_stats[team_stats['Team'] == home_team]
        
        if len(away_row) == 0 or len(home_row) == 0:
            continue
        
        away_ppg = away_row['PPG'].values[0]
        home_ppg = home_row['PPG'].values[0]
        estimated_vegas = away_ppg + home_ppg
        
        # Minimum alternate = Vegas - 20
        minimum_line = estimated_vegas - 20
        
        # V3.1 simulation
        result_v31 = engine_v31.simulate_game(away_team, home_team, minimum_line)
        result_v31['actual_total'] = actual_total
        result_v31['hit'] = actual_total > minimum_line
        result_v31['estimated_vegas'] = estimated_vegas
        results_v31.append(result_v31)
        
        # V3.0 simulation (if available)
        if engine_v30:
            result_v30 = engine_v30.simulate_game(away_team, home_team, minimum_line)
            result_v30['actual_total'] = actual_total
            result_v30['hit'] = actual_total > minimum_line
            results_v30.append(result_v30)
    
    print(f"\n  ✓ Processed {len(results_v31)} games")
    
    # Analyze V3.1 Results
    print("\n" + "=" * 80)
    print("V3.1 RESULTS (MATCHUP-BASED + FLAG PENALTIES)")
    print("=" * 80)
    
    df_v31 = pd.DataFrame(results_v31)
    
    # Win rate by decision
    print("\n  BY DECISION CATEGORY:")
    for decision in ['STRONG_YES', 'YES', 'MAYBE', 'LEAN_NO', 'NO']:
        subset = df_v31[df_v31['mc_decision'] == decision]
        if len(subset) == 0:
            continue
        
        wins = len(subset[subset['hit'] == True])
        total = len(subset)
        rate = wins / total * 100 if total > 0 else 0
        
        marker = "✓" if decision in ['STRONG_YES', 'YES'] else " "
        print(f"    {marker} {decision}: {wins}/{total} ({rate:.1f}%)")
    
    # Win rate by probability threshold
    print("\n  BY PROBABILITY THRESHOLD:")
    print(f"    {'Threshold':<12} {'Games':<10} {'Wins':<10} {'Losses':<10} {'Win Rate':<12}")
    print("    " + "-" * 55)
    
    for thresh in [70, 75, 80, 85, 88, 90, 92, 95]:
        above = df_v31[df_v31['mc_probability'] >= thresh]
        if len(above) == 0:
            print(f"    {thresh}%+{'':<8} {'0':<10} {'-':<10} {'-':<10} {'N/A':<12}")
            continue
        
        wins = len(above[above['hit'] == True])
        losses = len(above) - wins
        rate = wins / len(above) * 100
        
        print(f"    {thresh}%+{'':<8} {len(above):<10} {wins:<10} {losses:<10} {rate:.1f}%")
    
    # Flag analysis
    print("\n  BY FLAG COUNT:")
    for flags in range(6):
        subset = df_v31[df_v31['flag_count'] == flags]
        if len(subset) == 0:
            continue
        
        wins = len(subset[subset['hit'] == True])
        total = len(subset)
        rate = wins / total * 100 if total > 0 else 0
        
        # Show yes decisions at this flag count
        yes_at_flags = subset[subset['mc_decision'].isin(['STRONG_YES', 'YES'])]
        yes_wins = len(yes_at_flags[yes_at_flags['hit'] == True])
        yes_total = len(yes_at_flags)
        yes_rate = yes_wins / yes_total * 100 if yes_total > 0 else 0
        
        print(f"    {flags} flags: {wins}/{total} overall ({rate:.1f}%) | YES bets: {yes_wins}/{yes_total} ({yes_rate:.1f}%)")
    
    # Floor safety analysis
    print("\n  FLOOR SAFETY CHECK:")
    floor_safe = df_v31[df_v31['floor_safe'] == True]
    floor_unsafe = df_v31[df_v31['floor_safe'] == False]
    
    safe_wins = len(floor_safe[floor_safe['hit'] == True])
    safe_total = len(floor_safe)
    safe_rate = safe_wins / safe_total * 100 if safe_total > 0 else 0
    
    unsafe_wins = len(floor_unsafe[floor_unsafe['hit'] == True])
    unsafe_total = len(floor_unsafe)
    unsafe_rate = unsafe_wins / unsafe_total * 100 if unsafe_total > 0 else 0
    
    print(f"    Floor Safe: {safe_wins}/{safe_total} ({safe_rate:.1f}%)")
    print(f"    Floor Unsafe: {unsafe_wins}/{unsafe_total} ({unsafe_rate:.1f}%)")
    
    # YES/STRONG_YES bets analysis
    print("\n" + "=" * 80)
    print("V3.1 BET ANALYSIS (STRONG_YES + YES ONLY)")
    print("=" * 80)
    
    bets = df_v31[df_v31['mc_decision'].isin(['STRONG_YES', 'YES'])]
    bet_wins = len(bets[bets['hit'] == True])
    bet_total = len(bets)
    bet_rate = bet_wins / bet_total * 100 if bet_total > 0 else 0
    
    print(f"\n  Total YES/STRONG_YES bets: {bet_total}")
    print(f"  Wins: {bet_wins}")
    print(f"  Losses: {bet_total - bet_wins}")
    print(f"  Win Rate: {bet_rate:.1f}%")
    
    # Show losses
    if bet_total - bet_wins > 0:
        print("\n  LOSSES (games where YES/STRONG_YES missed):")
        losses = bets[bets['hit'] == False]
        for _, row in losses.iterrows():
            print(f"    ✗ {row['game']}")
            print(f"      MC: {row['mc_probability']}% | Line: {row['minimum_line']:.0f} | Actual: {row['actual_total']:.0f}")
            print(f"      Flags: {row['flag_count']} | Floor Safe: {row['floor_safe']}")
            if row['risk_flags']:
                for flag in row['risk_flags'][:2]:
                    print(f"        - {flag}")
    
    # Compare with V3.0 if available
    if engine_v30 and len(results_v30) > 0:
        print("\n" + "=" * 80)
        print("V3.0 COMPARISON")
        print("=" * 80)
        
        df_v30 = pd.DataFrame(results_v30)
        
        # Get V3.0 YES bets (old thresholds)
        v30_yes = df_v30[df_v30['mc_probability'] >= 85]  # V3.0 used 85%
        v30_wins = len(v30_yes[v30_yes['hit'] == True])
        v30_total = len(v30_yes)
        v30_rate = v30_wins / v30_total * 100 if v30_total > 0 else 0
        
        print(f"\n  V3.0 (85%+ threshold):")
        print(f"    Bets: {v30_total}, Wins: {v30_wins}, Rate: {v30_rate:.1f}%")
        
        print(f"\n  V3.1 (88%+ with flags):")
        print(f"    Bets: {bet_total}, Wins: {bet_wins}, Rate: {bet_rate:.1f}%")
        
        print(f"\n  Improvement: {bet_rate - v30_rate:+.1f}% win rate")
        print(f"  Trade-off: {v30_total - bet_total} fewer bets")
    
    # Save results
    output_file = f"v31_backtest_{datetime.now().strftime('%Y-%m-%d_%H-%M')}.csv"
    df_v31.to_csv(output_file, index=False)
    print(f"\n  ✓ Results saved to {output_file}")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    print(f"""
  V3.1 KEY METRICS:
  
  YES/STRONG_YES Bets: {bet_total}
  Wins: {bet_wins}
  Losses: {bet_total - bet_wins}
  Win Rate: {bet_rate:.1f}%
  
  FLAG SYSTEM IMPACT:
  - Games with 3+ flags auto-downgraded to MAYBE
  - Floor unsafe games auto-downgraded
  
  MATCHUP-BASED SCORING:
  - Uses ORtg × OppDRtg formula
  - Accounts for opponent defense quality
    """)
    
    return df_v31


if __name__ == "__main__":
    run_comparison_backtest()
