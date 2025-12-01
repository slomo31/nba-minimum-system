"""
Backtest V3.1 vs V3.2 Thresholds
=================================
Compare the performance of strict V3.1 thresholds vs loosened V3.2 thresholds
on historical data to find the optimal balance.
"""

import pandas as pd
import numpy as np
import os
import sys
from datetime import datetime

# Import both engines
from monte_carlo_engine_v3_2 import MonteCarloEngineV32

# V3.1 thresholds (for comparison)
V31_THRESHOLDS = {
    'HIGH_VARIANCE': 12.0,
    'BOTH_BELOW_AVG_PACE': 100.0,
    'SLOW_PACE': 98.0,
    'ROAD_GOOD_DEFENSE': 113.0,
    'BOTH_GOOD_DEFENSE': 114.0,
    'PACE_MISMATCH': 3.0,
    'WEAK_OFFENSE': 110.0,
    'ELITE_DEFENSE': 108.0,
    'MEDIOCRE_OFFENSE': 112.0,
    'GOOD_DEFENSE': 114.0
}

# V3.2 thresholds (loosened)
V32_THRESHOLDS = {
    'HIGH_VARIANCE': 14.0,
    'BOTH_BELOW_AVG_PACE': 98.0,
    'SLOW_PACE': 96.0,
    'ROAD_GOOD_DEFENSE': 110.0,
    'BOTH_GOOD_DEFENSE': 111.0,
    'PACE_MISMATCH': 5.0,
    'WEAK_OFFENSE': 108.0,
    'ELITE_DEFENSE': 108.0,
    'MEDIOCRE_OFFENSE': 112.0,
    'GOOD_DEFENSE': 111.0
}


def count_flags_with_thresholds(away_profile, home_profile, thresholds, percentile_10, minimum_line):
    """Count flags using specific thresholds"""
    flags = []
    
    away_drtg = away_profile.get('drtg', 115)
    home_drtg = home_profile.get('drtg', 115)
    away_ortg = away_profile.get('ortg', 115)
    home_ortg = home_profile.get('ortg', 115)
    away_pace = away_profile.get('pace', 100)
    home_pace = home_profile.get('pace', 100)
    away_var = away_profile.get('variance', 10)
    home_var = home_profile.get('variance', 10)
    
    # Elite defense
    if away_drtg < thresholds['ELITE_DEFENSE']:
        flags.append('elite_d_away')
    if home_drtg < thresholds['ELITE_DEFENSE']:
        flags.append('elite_d_home')
    
    # Both good defense
    if away_drtg < thresholds['BOTH_GOOD_DEFENSE'] and home_drtg < thresholds['BOTH_GOOD_DEFENSE']:
        flags.append('both_good_d')
    
    # Road good defense
    if away_drtg < thresholds['ROAD_GOOD_DEFENSE']:
        flags.append('road_good_d')
    
    # Both mediocre offense
    if away_ortg < thresholds['MEDIOCRE_OFFENSE'] and home_ortg < thresholds['MEDIOCRE_OFFENSE']:
        flags.append('both_med_o')
    
    # Weak offense
    if away_ortg < thresholds['WEAK_OFFENSE']:
        flags.append('weak_o_away')
    if home_ortg < thresholds['WEAK_OFFENSE']:
        flags.append('weak_o_home')
    
    # Slow pace
    if away_pace < thresholds['SLOW_PACE']:
        flags.append('slow_away')
    if home_pace < thresholds['SLOW_PACE']:
        flags.append('slow_home')
    
    # Both below avg pace
    if away_pace < thresholds['BOTH_BELOW_AVG_PACE'] and home_pace < thresholds['BOTH_BELOW_AVG_PACE']:
        flags.append('both_slow')
    
    # Pace mismatch
    if abs(away_pace - home_pace) > thresholds['PACE_MISMATCH']:
        flags.append('pace_mismatch')
    
    # High variance
    if away_var > thresholds['HIGH_VARIANCE']:
        flags.append('var_away')
    if home_var > thresholds['HIGH_VARIANCE']:
        flags.append('var_home')
    
    # Floor risk
    if percentile_10 < minimum_line:
        flags.append('floor_risk')
    
    return len(flags), flags


def run_backtest():
    """Run backtest comparing V3.1 vs V3.2 thresholds"""
    
    print("\n" + "=" * 80)
    print("🔬 BACKTEST: V3.1 vs V3.2 THRESHOLDS")
    print("=" * 80)
    
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
    
    print(f"\n  ✓ Loaded {len(team_stats)} teams")
    print(f"  ✓ Loaded {len(completed_games)} completed games")
    
    # Remove duplicates from completed games
    completed_games = completed_games.drop_duplicates(subset=['Visitor', 'Home', 'Date'])
    print(f"  ✓ After dedup: {len(completed_games)} unique games")
    
    # Initialize V3.2 engine (we'll manually apply V3.1 thresholds for comparison)
    engine = MonteCarloEngineV32(team_stats, completed_games)
    
    # Results storage
    v31_results = {'bets': 0, 'wins': 0, 'losses': 0}
    v32_results = {'bets': 0, 'wins': 0, 'losses': 0}
    
    v31_details = []
    v32_details = []
    
    print(f"\n  Running simulations on {len(completed_games)} games...")
    print("  (This may take a minute...)")
    
    # Test each completed game
    for idx, game in completed_games.iterrows():
        away_team = game['Visitor']
        home_team = game['Home']
        actual_total = game['Total_Points']
        
        # Skip if team not in profiles
        if away_team not in engine.team_profiles or home_team not in engine.team_profiles:
            continue
        
        away_profile = engine.team_profiles[away_team]
        home_profile = engine.team_profiles[home_team]
        
        # Simulate minimum line (actual - random buffer between 15-30)
        # This mimics what sportsbooks would set
        buffer = np.random.uniform(15, 30)
        minimum_line = actual_total - buffer
        
        # Run simulation
        sim_results = engine.run_simulation(away_team, home_team, minimum_line, n_simulations=5000)
        
        if sim_results is None:
            continue
        
        mc_prob = sim_results['mc_probability']
        percentile_10 = sim_results['percentile_10']
        
        # Count flags with V3.1 thresholds
        v31_flags, v31_flag_list = count_flags_with_thresholds(
            away_profile, home_profile, V31_THRESHOLDS, percentile_10, minimum_line
        )
        
        # Count flags with V3.2 thresholds
        v32_flags, v32_flag_list = count_flags_with_thresholds(
            away_profile, home_profile, V32_THRESHOLDS, percentile_10, minimum_line
        )
        
        # Determine results
        would_win = actual_total > minimum_line
        
        # V3.1 decision
        if v31_flags == 0 and mc_prob >= 88:
            v31_results['bets'] += 1
            if would_win:
                v31_results['wins'] += 1
                v31_details.append(('WIN', away_team, home_team, minimum_line, actual_total, mc_prob, v31_flags))
            else:
                v31_results['losses'] += 1
                v31_details.append(('LOSS', away_team, home_team, minimum_line, actual_total, mc_prob, v31_flags))
        
        # V3.2 decision
        if v32_flags == 0 and mc_prob >= 88:
            v32_results['bets'] += 1
            if would_win:
                v32_results['wins'] += 1
                v32_details.append(('WIN', away_team, home_team, minimum_line, actual_total, mc_prob, v32_flags))
            else:
                v32_results['losses'] += 1
                v32_details.append(('LOSS', away_team, home_team, minimum_line, actual_total, mc_prob, v32_flags))
    
    # Calculate win rates
    v31_rate = (v31_results['wins'] / v31_results['bets'] * 100) if v31_results['bets'] > 0 else 0
    v32_rate = (v32_results['wins'] / v32_results['bets'] * 100) if v32_results['bets'] > 0 else 0
    
    # Print results
    print("\n" + "=" * 80)
    print("📊 BACKTEST RESULTS")
    print("=" * 80)
    
    print(f"""
    ┌─────────────────────────────────────────────────────────────────┐
    │                    V3.1 (STRICT)  vs  V3.2 (LOOSENED)           │
    ├─────────────────────────────────────────────────────────────────┤
    │  Total Bets:         {v31_results['bets']:>4}                  {v32_results['bets']:>4}              │
    │  Wins:               {v31_results['wins']:>4}                  {v32_results['wins']:>4}              │
    │  Losses:             {v31_results['losses']:>4}                  {v32_results['losses']:>4}              │
    │  Win Rate:           {v31_rate:>5.1f}%               {v32_rate:>5.1f}%            │
    └─────────────────────────────────────────────────────────────────┘
    """)
    
    # Show V3.2 losses (if any)
    if v32_results['losses'] > 0:
        print("\n⚠️ V3.2 LOSSES (games to analyze):")
        print("-" * 80)
        for detail in v32_details:
            if detail[0] == 'LOSS':
                print(f"  ❌ {detail[1]} @ {detail[2]}")
                print(f"     Line: {detail[3]:.1f} | Actual: {detail[4]:.1f} | MC: {detail[5]:.1f}%")
    
    # Recommendation
    print("\n" + "=" * 80)
    print("💡 RECOMMENDATION")
    print("=" * 80)
    
    if v32_rate >= 95 and v32_results['bets'] > v31_results['bets']:
        print(f"""
    ✅ V3.2 RECOMMENDED
    
    - More bets: {v32_results['bets']} vs {v31_results['bets']} (+{v32_results['bets'] - v31_results['bets']})
    - Win rate still excellent: {v32_rate:.1f}%
    - Only {v32_results['losses']} losses
        """)
    elif v31_rate > v32_rate:
        print(f"""
    ⚠️ STAY WITH V3.1
    
    - V3.1 has better win rate: {v31_rate:.1f}% vs {v32_rate:.1f}%
    - Fewer bets but safer
        """)
    else:
        print(f"""
    🤔 MIXED RESULTS - Consider middle ground
    
    - V3.1: {v31_results['bets']} bets, {v31_rate:.1f}% win rate
    - V3.2: {v32_results['bets']} bets, {v32_rate:.1f}% win rate
        """)
    
    # Save detailed results
    output_file = f'backtest_v31_vs_v32_{datetime.now().strftime("%Y-%m-%d_%H-%M")}.csv'
    
    all_details = []
    for d in v31_details:
        all_details.append({
            'version': 'V3.1',
            'result': d[0],
            'away': d[1],
            'home': d[2],
            'line': d[3],
            'actual': d[4],
            'mc_prob': d[5],
            'flags': d[6]
        })
    for d in v32_details:
        all_details.append({
            'version': 'V3.2',
            'result': d[0],
            'away': d[1],
            'home': d[2],
            'line': d[3],
            'actual': d[4],
            'mc_prob': d[5],
            'flags': d[6]
        })
    
    if all_details:
        pd.DataFrame(all_details).to_csv(output_file, index=False)
        print(f"\n  ✓ Detailed results saved to: {output_file}")


if __name__ == "__main__":
    run_backtest()
