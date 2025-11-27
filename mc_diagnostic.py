"""
DIAGNOSTIC BACKTEST - Understanding MC Predictions
===================================================
Let's see what MC is actually predicting for games
and why it's so conservative.
"""

import pandas as pd
import numpy as np
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from core.monte_carlo_engine import MonteCarloEngineV3 as MonteCarloEngine
    print("Using Monte Carlo Engine v3.0")
except ImportError:
    from core.monte_carlo_engine import MonteCarloEngine
    print("Using Monte Carlo Engine v1.0")


def run_diagnostic():
    """Diagnose why MC is so conservative"""
    
    print("\n" + "=" * 80)
    print("MC DIAGNOSTIC - UNDERSTANDING PREDICTIONS")
    print("=" * 80)
    
    # Load data
    team_stats = pd.read_csv('data/nba_team_stats_2025_2026.csv')
    completed_games = pd.read_csv('data/nba_completed_games_2025_2026.csv')
    
    print(f"\n  Teams: {len(team_stats)}")
    print(f"  Completed games: {len(completed_games)}")
    
    # Show team stats summary
    print("\n" + "=" * 80)
    print("TEAM PPG SUMMARY")
    print("=" * 80)
    
    avg_ppg = team_stats['PPG'].mean()
    min_ppg = team_stats['PPG'].min()
    max_ppg = team_stats['PPG'].max()
    
    print(f"\n  Average team PPG: {avg_ppg:.1f}")
    print(f"  Min team PPG: {min_ppg:.1f}")
    print(f"  Max team PPG: {max_ppg:.1f}")
    print(f"  Expected game total (2 avg teams): {avg_ppg * 2:.1f}")
    
    # Show completed game totals
    print("\n" + "=" * 80)
    print("COMPLETED GAME TOTALS")
    print("=" * 80)
    
    avg_total = completed_games['Total_Points'].mean()
    min_total = completed_games['Total_Points'].min()
    max_total = completed_games['Total_Points'].max()
    std_total = completed_games['Total_Points'].std()
    
    print(f"\n  Average game total: {avg_total:.1f}")
    print(f"  Std dev: {std_total:.1f}")
    print(f"  Min total: {min_total:.0f}")
    print(f"  Max total: {max_total:.0f}")
    
    # Distribution of game totals
    print("\n  Game total distribution:")
    brackets = [(170, 190), (190, 210), (210, 220), (220, 230), (230, 250), (250, 280)]
    for low, high in brackets:
        count = len(completed_games[(completed_games['Total_Points'] >= low) & (completed_games['Total_Points'] < high)])
        pct = count / len(completed_games) * 100
        print(f"    {low}-{high}: {count} games ({pct:.1f}%)")
    
    # Initialize MC
    print("\n" + "=" * 80)
    print("TESTING MC ON SAMPLE GAMES")
    print("=" * 80)
    
    mc_engine = MonteCarloEngine(team_stats, completed_games, n_simulations=1000)
    
    # Test a few games at different minimum line levels
    sample_games = completed_games.sample(10)
    
    print("\n  Testing 10 random games at different minimum lines:")
    print("  " + "-" * 75)
    
    all_probs = []
    
    for _, game in sample_games.iterrows():
        away = game['Visitor']
        home = game['Home']
        actual = game['Total_Points']
        
        # Get team PPGs
        away_ppg = team_stats[team_stats['Team'] == away]['PPG'].values[0]
        home_ppg = team_stats[team_stats['Team'] == home]['PPG'].values[0]
        expected = away_ppg + home_ppg
        
        print(f"\n  {away} @ {home}")
        print(f"  Team PPGs: {away_ppg:.1f} + {home_ppg:.1f} = {expected:.1f} expected")
        print(f"  Actual total: {actual:.0f}")
        
        # Test at different minimum lines
        for min_line in [expected - 25, expected - 20, expected - 15, expected - 10]:
            result = mc_engine.simulate_game(away, home, min_line)
            mc_prob = result['mc_probability']
            mc_pred = result['avg_simulated_total']
            
            hit = "✓" if actual > min_line else "✗"
            
            all_probs.append({
                'min_line': min_line,
                'buffer': expected - min_line,
                'mc_prob': mc_prob,
                'actual': actual,
                'hit': actual > min_line
            })
            
            print(f"    Min {min_line:.0f} (buffer {expected-min_line:.0f}): MC {mc_prob:.1f}% | Actual {hit}")
    
    # Analyze all probabilities
    prob_df = pd.DataFrame(all_probs)
    
    print("\n" + "=" * 80)
    print("MC PROBABILITY ANALYSIS")
    print("=" * 80)
    
    print("\n  By buffer level (how far min line is below expected):")
    for buffer in [10, 15, 20, 25]:
        buf_df = prob_df[prob_df['buffer'] == buffer]
        if len(buf_df) > 0:
            avg_prob = buf_df['mc_prob'].mean()
            hit_rate = buf_df['hit'].mean() * 100
            print(f"    Buffer {buffer}: Avg MC prob {avg_prob:.1f}%, Actual hit rate {hit_rate:.1f}%")
    
    # Now test with ACTUAL minimum lines (like your real bets)
    print("\n" + "=" * 80)
    print("TESTING WITH REALISTIC MINIMUM LINES")
    print("=" * 80)
    print("""
  Your actual minimum lines are typically 15-25 points below the Vegas total.
  Vegas total is usually close to combined team PPG.
  
  Let's test: If min line = team PPG average - 20, what does MC predict?
    """)
    
    results = []
    
    for idx, game in completed_games.iterrows():
        away = game['Visitor']
        home = game['Home']
        actual = game['Total_Points']
        
        away_row = team_stats[team_stats['Team'] == away]
        home_row = team_stats[team_stats['Team'] == home]
        
        if len(away_row) == 0 or len(home_row) == 0:
            continue
        
        away_ppg = away_row['PPG'].values[0]
        home_ppg = home_row['PPG'].values[0]
        expected = away_ppg + home_ppg
        
        # Minimum line at expected - 20 (realistic minimum alternate)
        min_line = expected - 20
        
        result = mc_engine.simulate_game(away, home, min_line)
        mc_prob = result['mc_probability']
        
        results.append({
            'game': f"{away} @ {home}",
            'expected': expected,
            'min_line': min_line,
            'mc_prob': mc_prob,
            'actual': actual,
            'hit': actual > min_line
        })
    
    df = pd.DataFrame(results)
    
    print(f"\n  Tested {len(df)} games with min_line = expected - 20")
    
    # MC probability distribution
    print("\n  MC Probability Distribution:")
    for low, high in [(0, 50), (50, 70), (70, 78), (78, 85), (85, 92), (92, 100)]:
        count = len(df[(df['mc_prob'] >= low) & (df['mc_prob'] < high)])
        pct = count / len(df) * 100
        wins = len(df[(df['mc_prob'] >= low) & (df['mc_prob'] < high) & (df['hit'] == True)])
        if count > 0:
            win_rate = wins / count * 100
            print(f"    {low}-{high}%: {count} games ({pct:.1f}%) | Actual win rate: {win_rate:.1f}%")
    
    # Win rate at different thresholds
    print("\n" + "=" * 80)
    print("WIN RATE BY MC THRESHOLD (min_line = expected - 20)")
    print("=" * 80)
    
    print(f"\n  {'Threshold':<12} {'Games':<10} {'Wins':<10} {'Losses':<10} {'Win Rate':<12}")
    print("  " + "-" * 60)
    
    for thresh in [50, 60, 70, 75, 78, 80, 85, 90, 92, 95]:
        above = df[df['mc_prob'] >= thresh]
        if len(above) == 0:
            print(f"  {thresh}%+{'':<8} {'0':<10} {'-':<10} {'-':<10} {'N/A':<12}")
            continue
        
        wins = len(above[above['hit'] == True])
        losses = len(above) - wins
        rate = wins / len(above) * 100
        
        print(f"  {thresh}%+{'':<8} {len(above):<10} {wins:<10} {losses:<10} {rate:.1f}%")
    
    # Show some examples
    print("\n" + "=" * 80)
    print("SAMPLE PREDICTIONS")
    print("=" * 80)
    
    # High confidence correct
    high_conf_wins = df[(df['mc_prob'] >= 85) & (df['hit'] == True)].head(5)
    print("\n  HIGH CONFIDENCE WINS (85%+ MC, actual over):")
    for _, row in high_conf_wins.iterrows():
        print(f"    {row['game']}: MC {row['mc_prob']:.1f}% | Line {row['min_line']:.0f} | Actual {row['actual']:.0f}")
    
    # High confidence wrong
    high_conf_losses = df[(df['mc_prob'] >= 80) & (df['hit'] == False)].head(5)
    print("\n  HIGH CONFIDENCE LOSSES (80%+ MC, actual under):")
    for _, row in high_conf_losses.iterrows():
        print(f"    {row['game']}: MC {row['mc_prob']:.1f}% | Line {row['min_line']:.0f} | Actual {row['actual']:.0f}")
    
    # Summary
    print("\n" + "=" * 80)
    print("KEY FINDINGS")
    print("=" * 80)
    
    bets_85 = df[df['mc_prob'] >= 85]
    wins_85 = bets_85[bets_85['hit'] == True]
    
    bets_80 = df[df['mc_prob'] >= 80]
    wins_80 = bets_80[bets_80['hit'] == True]
    
    print(f"""
  At minimum line = (combined PPG - 20):
  
  Threshold 85%+:
    Games: {len(bets_85)}
    Wins: {len(wins_85)}
    Losses: {len(bets_85) - len(wins_85)}
    Win Rate: {len(wins_85)/max(len(bets_85),1)*100:.1f}%
    
  Threshold 80%+:
    Games: {len(bets_80)}
    Wins: {len(wins_80)}
    Losses: {len(bets_80) - len(wins_80)}
    Win Rate: {len(wins_80)/max(len(bets_80),1)*100:.1f}%
    """)
    
    return df


if __name__ == "__main__":
    run_diagnostic()
