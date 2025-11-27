"""
CORRECTED FULL SEASON BACKTEST - Monte Carlo
==============================================
Tests MC predictions PROPERLY:
- MC predicts what it THINKS the total will be
- We compare that prediction to what ACTUALLY happened
- We simulate realistic minimum lines based on team averages

The key insight: We need to test if MC would have CORRECTLY predicted
games going OVER a line that was set BEFORE the game, not after.
"""

import pandas as pd
import numpy as np
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from core.monte_carlo_engine import MonteCarloEngineV3 as MonteCarloEngine
    print("Using Monte Carlo Engine v3.0")
except ImportError:
    from core.monte_carlo_engine import MonteCarloEngine
    print("Using Monte Carlo Engine v1.0")


def estimate_vegas_line(away_team, home_team, team_stats):
    """
    Estimate what Vegas total line would have been for a game
    Based on team averages (similar to how Vegas sets lines)
    """
    away_row = team_stats[team_stats['Team'] == away_team]
    home_row = team_stats[team_stats['Team'] == home_team]
    
    if len(away_row) == 0 or len(home_row) == 0:
        return 220  # Default
    
    away_ppg = away_row['PPG'].values[0]
    home_ppg = home_row['PPG'].values[0]
    
    # Vegas line is typically close to combined PPG with home boost
    estimated_total = away_ppg + home_ppg + 2  # Small home boost
    
    return round(estimated_total, 1)


def run_corrected_backtest():
    """
    Proper backtest:
    1. For each game, estimate what Vegas line would have been
    2. Set minimum alternate at line - 15 (typical)
    3. Run MC to see what it predicts
    4. Check if MC prediction was correct vs actual result
    """
    
    print("\n" + "=" * 80)
    print("CORRECTED FULL SEASON BACKTEST - MONTE CARLO")
    print("=" * 80)
    
    # Load data
    print("\nLoading data...")
    team_stats = pd.read_csv('data/nba_team_stats_2025_2026.csv')
    completed_games = pd.read_csv('data/nba_completed_games_2025_2026.csv')
    print(f"  ✓ {len(team_stats)} teams")
    print(f"  ✓ {len(completed_games)} completed games")
    
    print("\n" + "=" * 80)
    print("METHODOLOGY (CORRECTED)")
    print("=" * 80)
    print("""
  For each completed game:
  1. Estimate Vegas total line from team PPG averages
  2. Calculate minimum alternate = Vegas line - 15
  3. Run Monte Carlo to get predicted probability
  4. Compare MC's prediction to ACTUAL result
  
  This tests: Would MC have correctly predicted the outcome
  if we had bet BEFORE the game?
    """)
    
    # Initialize MC engine
    print("Initializing Monte Carlo Engine (1,000 sims for speed)...")
    mc_engine = MonteCarloEngine(team_stats, completed_games, n_simulations=1000)
    
    results = []
    total_games = len(completed_games)
    
    print("\n" + "=" * 80)
    print("RUNNING BACKTEST...")
    print("=" * 80)
    
    for idx, game in completed_games.iterrows():
        if idx % 50 == 0:
            print(f"  Processing game {idx+1}/{total_games}...")
        
        away = game['Visitor']
        home = game['Home']
        actual_total = game['Total_Points']
        
        # Step 1: Estimate what Vegas line would have been
        vegas_line = estimate_vegas_line(away, home, team_stats)
        
        # Step 2: Calculate minimum alternate (15 below Vegas)
        min_line = vegas_line - 15
        
        # Step 3: Run MC simulation
        try:
            result = mc_engine.simulate_game(
                away_team=away,
                home_team=home,
                minimum_line=min_line
            )
            
            mc_prob = result['mc_probability']
            mc_predicted_total = result['avg_simulated_total']
            
            # MC decision
            if mc_prob >= 92:
                mc_decision = 'STRONG_YES'
            elif mc_prob >= 85:
                mc_decision = 'YES'
            elif mc_prob >= 78:
                mc_decision = 'MAYBE'
            elif mc_prob >= 70:
                mc_decision = 'LEAN_NO'
            else:
                mc_decision = 'NO'
            
            # Step 4: Check actual result
            actual_over = actual_total > min_line
            
            # Was MC correct?
            if mc_decision in ['STRONG_YES', 'YES']:
                mc_bet = True
                mc_result = 'WIN' if actual_over else 'LOSS'
            else:
                mc_bet = False
                mc_result = 'SKIP'
            
            # Prediction accuracy (how close was MC's predicted total to actual?)
            prediction_error = mc_predicted_total - actual_total
            
            results.append({
                'date': game['Date'],
                'away': away,
                'home': home,
                'vegas_line': vegas_line,
                'min_line': min_line,
                'mc_prob': mc_prob,
                'mc_decision': mc_decision,
                'mc_predicted_total': mc_predicted_total,
                'actual_total': actual_total,
                'actual_over': actual_over,
                'mc_bet': mc_bet,
                'mc_result': mc_result,
                'prediction_error': prediction_error,
                'buffer': actual_total - min_line  # How much cushion was there
            })
            
        except Exception as e:
            print(f"  Error on {away} @ {home}: {str(e)[:50]}")
    
    df = pd.DataFrame(results)
    print(f"\n  ✓ Processed {len(df)} games")
    
    # ================================================================
    # ANALYSIS
    # ================================================================
    
    print("\n" + "=" * 80)
    print("OVERALL RESULTS")
    print("=" * 80)
    
    # How many games actually went over the minimum line?
    games_over = len(df[df['actual_over'] == True])
    games_under = len(df[df['actual_over'] == False])
    
    print(f"\n  Games where actual > min line (OVER): {games_over} ({games_over/len(df)*100:.1f}%)")
    print(f"  Games where actual < min line (UNDER): {games_under} ({games_under/len(df)*100:.1f}%)")
    
    # MC betting results
    print("\n" + "=" * 80)
    print("MC BETTING RESULTS (85%+ threshold)")
    print("=" * 80)
    
    bets = df[df['mc_bet'] == True]
    wins = bets[bets['mc_result'] == 'WIN']
    losses = bets[bets['mc_result'] == 'LOSS']
    
    print(f"\n  Total bets (MC said YES/STRONG_YES): {len(bets)}")
    print(f"  Wins: {len(wins)}")
    print(f"  Losses: {len(losses)}")
    
    if len(bets) > 0:
        win_rate = len(wins) / len(bets) * 100
        print(f"  WIN RATE: {win_rate:.1f}%")
        
        # ROI at -450 odds
        profit = len(wins) * 22.22 - len(losses) * 100
        roi = profit / len(bets)
        print(f"  Estimated ROI: {roi:+.1f}% (at -450 odds)")
    
    # By decision category
    print("\n" + "=" * 80)
    print("RESULTS BY MC DECISION CATEGORY")
    print("=" * 80)
    
    for decision in ['STRONG_YES', 'YES', 'MAYBE', 'LEAN_NO', 'NO']:
        dec_df = df[df['mc_decision'] == decision]
        if len(dec_df) == 0:
            continue
        
        over = len(dec_df[dec_df['actual_over'] == True])
        total = len(dec_df)
        rate = over / total * 100
        
        print(f"\n  {decision} ({len(dec_df)} games):")
        print(f"    Actual OVER: {over} ({rate:.1f}%)")
        print(f"    Actual UNDER: {total - over} ({100-rate:.1f}%)")
        
        if decision in ['STRONG_YES', 'YES']:
            print(f"    → These are BETS. Win rate: {rate:.1f}%")
    
    # Threshold analysis
    print("\n" + "=" * 80)
    print("WIN RATE BY MC PROBABILITY THRESHOLD")
    print("=" * 80)
    
    print(f"\n  {'Threshold':<12} {'Bets':<10} {'Wins':<10} {'Losses':<10} {'Win Rate':<12}")
    print("  " + "-" * 60)
    
    for thresh in [70, 75, 80, 85, 88, 90, 92, 95]:
        above = df[df['mc_prob'] >= thresh]
        if len(above) == 0:
            continue
        
        wins_t = len(above[above['actual_over'] == True])
        losses_t = len(above) - wins_t
        rate = wins_t / len(above) * 100
        
        print(f"  {thresh}%+{'':<8} {len(above):<10} {wins_t:<10} {losses_t:<10} {rate:.1f}%")
    
    # Analyze the losses
    print("\n" + "=" * 80)
    print("ANALYZING LOSSES (Games MC got wrong)")
    print("=" * 80)
    
    mc_losses = df[(df['mc_bet'] == True) & (df['mc_result'] == 'LOSS')]
    
    if len(mc_losses) > 0:
        print(f"\n  Total losses when MC bet: {len(mc_losses)}")
        print("\n  LOSS DETAILS:")
        print("  " + "-" * 75)
        
        for _, loss in mc_losses.head(15).iterrows():
            print(f"  {loss['away']} @ {loss['home']}")
            print(f"    Min Line: {loss['min_line']:.1f} | MC Prob: {loss['mc_prob']:.1f}% | Actual: {loss['actual_total']:.0f}")
            print(f"    Missed by: {loss['min_line'] - loss['actual_total']:.1f} points")
            print()
    else:
        print("\n  No losses! (This seems unlikely, check the data)")
    
    # Save results
    print("\n" + "=" * 80)
    print("SAVING RESULTS")
    print("=" * 80)
    
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M')
    filename = f'mc_corrected_backtest_{timestamp}.csv'
    df.to_csv(filename, index=False)
    print(f"  ✓ Saved to {filename}")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    bets = df[df['mc_bet'] == True]
    wins = bets[bets['mc_result'] == 'WIN']
    
    if len(bets) > 0:
        print(f"""
  MC v3.0 Backtest Results (526 games):
  
  Total bets (85%+ MC probability): {len(bets)}
  Wins: {len(wins)}
  Losses: {len(bets) - len(wins)}
  Win Rate: {len(wins)/len(bets)*100:.1f}%
  
  For comparison, your actual system has: 73-5 (93.6%)
        """)
    
    return df


if __name__ == "__main__":
    df = run_corrected_backtest()
    
    print("\n" + "=" * 80)
    print("BACKTEST COMPLETE")
    print("=" * 80)
