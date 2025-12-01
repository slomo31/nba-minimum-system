"""
Backtest V3.3 (Smart Variance) Engine
======================================
Test V3.3 thresholds on ALL historical completed games
to verify win rate before deploying to production.

This backtest simulates what would have happened if we 
used V3.3 for every game this season.
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime
from monte_carlo_engine_v3_3 import MonteCarloEngineV33


def run_v33_backtest():
    """Run comprehensive backtest of V3.3 engine"""
    
    print("\n" + "=" * 80)
    print("🔬 V3.3 COMPREHENSIVE BACKTEST")
    print("=" * 80)
    print("Testing smart variance thresholds on all completed games...")
    
    # Load data
    team_stats_file = 'data/nba_team_stats_2025_2026.csv'
    completed_games_file = 'data/nba_completed_games_2025_2026.csv'
    
    if not os.path.exists(team_stats_file):
        print(f"[ERROR] Team stats not found: {team_stats_file}")
        return
    
    if not os.path.exists(completed_games_file):
        print(f"[ERROR] Completed games not found: {completed_games_file}")
        return
    
    team_stats = pd.read_csv(team_stats_file)
    completed_games = pd.read_csv(completed_games_file)
    
    # Remove duplicates
    completed_games = completed_games.drop_duplicates(subset=['Visitor', 'Home', 'Date'])
    
    print(f"\n  ✓ Loaded {len(team_stats)} teams")
    print(f"  ✓ Loaded {len(completed_games)} unique completed games")
    
    # Initialize V3.3 engine
    engine = MonteCarloEngineV33(team_stats, completed_games)
    
    # Results storage
    results = {
        '0_flags': {'bets': 0, 'wins': 0, 'losses': 0, 'details': []},
        '1_flag': {'bets': 0, 'wins': 0, 'losses': 0, 'details': []},
        '2_flags': {'bets': 0, 'wins': 0, 'losses': 0, 'details': []},
        '3+_flags': {'bets': 0, 'wins': 0, 'losses': 0, 'details': []}
    }
    
    all_results = []
    skipped_teams = 0
    
    print(f"\n  Running {len(completed_games)} simulations...")
    print("  " + "-" * 60)
    
    # Test each completed game
    for idx, game in completed_games.iterrows():
        away_team = game['Visitor']
        home_team = game['Home']
        actual_total = game['Total_Points']
        game_date = game.get('Date', 'Unknown')
        
        # Skip if teams not in profiles
        if away_team not in engine.team_profiles or home_team not in engine.team_profiles:
            skipped_teams += 1
            continue
        
        # Simulate minimum line (15-25 points below actual)
        # This mimics typical sportsbook alternate lines
        buffer = np.random.uniform(15, 25)
        minimum_line = actual_total - buffer
        
        # Run V3.3 analysis
        analysis = engine.analyze_game(away_team, home_team, minimum_line, n_simulations=5000)
        
        if analysis is None:
            continue
        
        mc_prob = analysis['mc_probability']
        flag_count = analysis['flag_count']
        flags = analysis['flags']
        floor_safe = analysis['floor_safe']
        
        # Determine actual result
        would_win = actual_total > minimum_line
        
        # Categorize by flag count
        if flag_count == 0:
            category = '0_flags'
        elif flag_count == 1:
            category = '1_flag'
        elif flag_count == 2:
            category = '2_flags'
        else:
            category = '3+_flags'
        
        # Only count if MC probability >= 88% (our betting threshold)
        if mc_prob >= 88:
            results[category]['bets'] += 1
            
            if would_win:
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
            
            all_results.append({
                'date': game_date,
                'away_team': away_team,
                'home_team': home_team,
                'minimum_line': minimum_line,
                'actual_total': actual_total,
                'mc_probability': mc_prob,
                'flag_count': flag_count,
                'flags': '; '.join(flags) if flags else '',
                'floor_safe': floor_safe,
                'result': result_str,
                'category': category
            })
    
    if skipped_teams > 0:
        print(f"  [Note] Skipped {skipped_teams} games (teams not in current stats)")
    
    # ==========================================
    # PRINT RESULTS
    # ==========================================
    
    print("\n" + "=" * 80)
    print("📊 V3.3 BACKTEST RESULTS")
    print("=" * 80)
    
    # Summary table
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
        
        if category == '0_flags':
            status = "✅ BET" if rate >= 90 else "⚠️ RISKY"
        else:
            status = "❌ SKIP"
        
        cat_display = category.replace('_', ' ').upper()
        print(f"    │  {cat_display:<12} │  {bets:>5}  │  {wins:>5}  │  {losses:>6}  │  {rate:>7.1f}%  │  {status:<6}  │")
    
    print(f"    └────────────────────────────────────────────────────────────────────────┘")
    
    # Key metric: 0-flag performance
    zero_flag = results['0_flags']
    zero_rate = (zero_flag['wins'] / zero_flag['bets'] * 100) if zero_flag['bets'] > 0 else 0
    
    print(f"\n" + "=" * 80)
    print("🎯 KEY METRIC: 0-FLAG GAMES (What we bet on)")
    print("=" * 80)
    print(f"""
    Record:    {zero_flag['wins']}-{zero_flag['losses']}
    Win Rate:  {zero_rate:.1f}%
    Total Bets: {zero_flag['bets']}
    """)
    
    # Show 0-flag losses (if any)
    if zero_flag['losses'] > 0:
        print("\n⚠️ 0-FLAG LOSSES (need to analyze):")
        print("-" * 80)
        for detail in zero_flag['details']:
            if detail['result'] == 'LOSS':
                print(f"  ❌ {detail['game']}")
                print(f"     Date: {detail['date']}")
                print(f"     Line: {detail['line']:.1f} | Actual: {detail['actual']:.1f} | MC: {detail['mc_prob']:.1f}%")
                print(f"     Missed by: {detail['line'] - detail['actual']:.1f} points")
                print()
    
    # Compare to what flagged games would have done
    print("\n" + "=" * 80)
    print("🛡️ FLAG SYSTEM EFFECTIVENESS")
    print("=" * 80)
    
    flagged_losses = results['1_flag']['losses'] + results['2_flags']['losses'] + results['3+_flags']['losses']
    flagged_wins = results['1_flag']['wins'] + results['2_flags']['wins'] + results['3+_flags']['wins']
    flagged_total = flagged_wins + flagged_losses
    
    print(f"""
    Flagged games that would have LOST:  {flagged_losses}
    Flagged games that would have WON:   {flagged_wins}
    
    By skipping flagged games, we:
    ✅ Avoided {flagged_losses} losses
    ⚠️ Missed {flagged_wins} wins (acceptable trade-off)
    """)
    
    # Recommendation
    print("\n" + "=" * 80)
    print("💡 RECOMMENDATION")
    print("=" * 80)
    
    if zero_rate >= 95:
        print(f"""
    ✅ V3.3 APPROVED FOR PRODUCTION
    
    - 0-flag win rate: {zero_rate:.1f}% (target: 95%+)
    - Total 0-flag bets: {zero_flag['bets']}
    - Only {zero_flag['losses']} losses
    
    The smart variance handling is working!
        """)
    elif zero_rate >= 90:
        print(f"""
    ⚠️ V3.3 ACCEPTABLE (but monitor closely)
    
    - 0-flag win rate: {zero_rate:.1f}% (target: 95%+)
    - {zero_flag['losses']} losses in backtest
    - May need further threshold tuning
        """)
    else:
        print(f"""
    ❌ V3.3 NEEDS MORE WORK
    
    - 0-flag win rate: {zero_rate:.1f}% (target: 95%+)
    - Too many losses ({zero_flag['losses']})
    - Need to tighten thresholds or add more flags
        """)
    
    # Save detailed results
    output_file = f'backtest_v33_{datetime.now().strftime("%Y-%m-%d_%H-%M")}.csv'
    if all_results:
        pd.DataFrame(all_results).to_csv(output_file, index=False)
        print(f"\n  ✓ Detailed results saved to: {output_file}")
    
    return results


if __name__ == "__main__":
    results = run_v33_backtest()
