"""
FULL SEASON BACKTEST - Monte Carlo vs All Games
=================================================
Tests MC predictions against every completed game this season
to see what it would have predicted and how accurate it was.
"""

import pandas as pd
import numpy as np
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import MC engine
try:
    from core.monte_carlo_engine import MonteCarloEngineV3 as MonteCarloEngine
    print("Using Monte Carlo Engine v3.0")
except ImportError:
    from core.monte_carlo_engine import MonteCarloEngine
    print("Using Monte Carlo Engine v1.0")


def run_full_backtest():
    """Backtest MC against all completed games"""
    
    print("\n" + "=" * 80)
    print("FULL SEASON BACKTEST - MONTE CARLO")
    print("=" * 80)
    
    # Load data
    print("\nLoading data...")
    team_stats = pd.read_csv('data/nba_team_stats_2025_2026.csv')
    completed_games = pd.read_csv('data/nba_completed_games_2025_2026.csv')
    print(f"  ✓ {len(team_stats)} teams")
    print(f"  ✓ {len(completed_games)} completed games to test")
    
    # We need minimum lines for each game
    # Since we don't have historical odds, we'll estimate minimum lines
    # Minimum alternate is typically 15-20 points below the game total
    # We'll test at different thresholds
    
    print("\n" + "=" * 80)
    print("METHODOLOGY")
    print("=" * 80)
    print("""
  Since we don't have historical betting lines, we'll simulate what the
  minimum alternate line would have been for each game.
  
  Typical minimum alternates are 15-20 points below Vegas total.
  We'll test: What if the minimum line was set at different levels?
  
  For each game, we'll test minimum lines at:
  - Actual total - 5 (very tight)
  - Actual total - 10 (tight)
  - Actual total - 15 (typical minimum alternate)
  - Actual total - 20 (loose minimum alternate)
  - Actual total - 25 (very loose)
  
  This tells us: At each buffer level, how accurate is MC?
    """)
    
    # Initialize MC engine (use fewer sims for speed)
    print("Initializing Monte Carlo Engine (1,000 sims for speed)...")
    mc_engine = MonteCarloEngine(team_stats, completed_games, n_simulations=1000)
    
    # Test different buffer levels
    buffers = [5, 10, 15, 20, 25]
    
    all_results = []
    
    print("\n" + "=" * 80)
    print("RUNNING BACKTEST...")
    print("=" * 80)
    
    total_games = len(completed_games)
    
    for idx, game in completed_games.iterrows():
        if idx % 50 == 0:
            print(f"  Processing game {idx+1}/{total_games}...")
        
        away = game['Visitor']
        home = game['Home']
        actual_total = game['Total_Points']
        
        # Test each buffer level
        for buffer in buffers:
            # Simulate what the minimum line would have been
            # If actual was 220, minimum at -15 buffer = 205
            simulated_min_line = actual_total - buffer
            
            # Run MC simulation
            try:
                result = mc_engine.simulate_game(
                    away_team=away,
                    home_team=home,
                    minimum_line=simulated_min_line
                )
                
                mc_prob = result['mc_probability']
                
                # Determine MC decision
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
                
                # Did the actual total beat the simulated minimum?
                actual_hit = actual_total > simulated_min_line
                
                # Would MC have been correct?
                if mc_decision in ['STRONG_YES', 'YES']:
                    mc_bet = True
                    mc_correct = actual_hit  # Bet over, was it over?
                elif mc_decision == 'NO':
                    mc_bet = False
                    mc_correct = not actual_hit  # Didn't bet, was it under?
                else:
                    mc_bet = False  # MAYBE/LEAN_NO = skip
                    mc_correct = None  # N/A - didn't bet
                
                all_results.append({
                    'date': game['Date'],
                    'away': away,
                    'home': home,
                    'actual_total': actual_total,
                    'buffer': buffer,
                    'min_line': simulated_min_line,
                    'mc_prob': mc_prob,
                    'mc_decision': mc_decision,
                    'actual_hit': actual_hit,
                    'mc_bet': mc_bet,
                    'mc_correct': mc_correct
                })
                
            except Exception as e:
                print(f"  Error on {away} @ {home}: {str(e)[:50]}")
                continue
    
    print(f"\n  ✓ Processed {len(all_results)} game/buffer combinations")
    
    # Analyze results
    df = pd.DataFrame(all_results)
    
    print("\n" + "=" * 80)
    print("RESULTS BY BUFFER LEVEL")
    print("=" * 80)
    print("""
  Buffer = how far below actual total the minimum line was
  Example: Buffer 15 means minimum line was 15 points below actual total
           If game ended 220, min line was 205
    """)
    
    for buffer in buffers:
        buffer_df = df[df['buffer'] == buffer]
        
        # Games where MC said YES (bet)
        yes_bets = buffer_df[buffer_df['mc_bet'] == True]
        yes_wins = yes_bets[yes_bets['mc_correct'] == True]
        yes_losses = yes_bets[yes_bets['mc_correct'] == False]
        
        # Games where MC said NO (skip)
        no_bets = buffer_df[buffer_df['mc_decision'] == 'NO']
        no_correct = no_bets[no_bets['actual_hit'] == False]  # Correctly skipped
        
        # Calculate win rate
        if len(yes_bets) > 0:
            win_rate = len(yes_wins) / len(yes_bets) * 100
        else:
            win_rate = 0
        
        print(f"\n  BUFFER: {buffer} points below actual")
        print(f"  " + "-" * 60)
        print(f"  Total games tested: {len(buffer_df)}")
        print(f"  MC said YES (bet): {len(yes_bets)}")
        print(f"    Wins: {len(yes_wins)}")
        print(f"    Losses: {len(yes_losses)}")
        print(f"    WIN RATE: {win_rate:.1f}%")
        print(f"  MC said NO (skip): {len(no_bets)}")
        print(f"    Correctly skipped (would have lost): {len(no_correct)}")
    
    # Detailed analysis at buffer 15 (typical minimum alternate)
    print("\n" + "=" * 80)
    print("DETAILED ANALYSIS - BUFFER 15 (TYPICAL MINIMUM ALTERNATE)")
    print("=" * 80)
    
    buffer_15 = df[df['buffer'] == 15]
    
    # By decision category
    for decision in ['STRONG_YES', 'YES', 'MAYBE', 'LEAN_NO', 'NO']:
        dec_df = buffer_15[buffer_15['mc_decision'] == decision]
        if len(dec_df) == 0:
            continue
        
        wins = len(dec_df[dec_df['actual_hit'] == True])
        total = len(dec_df)
        rate = wins / total * 100
        
        print(f"\n  {decision}:")
        print(f"    Games: {total}")
        print(f"    Over hit: {wins} ({rate:.1f}%)")
        print(f"    Under hit: {total - wins} ({100-rate:.1f}%)")
    
    # Save detailed results
    print("\n" + "=" * 80)
    print("SAVING RESULTS")
    print("=" * 80)
    
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M')
    filename = f'mc_full_backtest_{timestamp}.csv'
    df.to_csv(filename, index=False)
    print(f"  ✓ Saved to {filename}")
    
    # Summary stats
    print("\n" + "=" * 80)
    print("KEY FINDINGS")
    print("=" * 80)
    
    # At buffer 15 (typical)
    b15 = df[df['buffer'] == 15]
    yes_bets_15 = b15[b15['mc_bet'] == True]
    yes_wins_15 = yes_bets_15[yes_bets_15['mc_correct'] == True]
    
    strong_yes_15 = b15[b15['mc_decision'] == 'STRONG_YES']
    strong_yes_wins = strong_yes_15[strong_yes_15['actual_hit'] == True]
    
    print(f"""
  At typical minimum alternate buffer (15 points):
  
  STRONG YES (92%+ MC):
    Games: {len(strong_yes_15)}
    Win rate: {len(strong_yes_wins)/len(strong_yes_15)*100:.1f}% (if we bet all)
    
  YES + STRONG YES (85%+ MC):
    Games: {len(yes_bets_15)}
    Win rate: {len(yes_wins_15)/len(yes_bets_15)*100:.1f}%
    
  This is what your win rate would be if you:
  - Only bet games where MC says 85%+
  - At minimum alternates ~15 points below Vegas line
    """)
    
    return df


def analyze_mc_thresholds(df):
    """Analyze different MC probability thresholds"""
    
    print("\n" + "=" * 80)
    print("MC THRESHOLD ANALYSIS (Buffer 15)")
    print("=" * 80)
    print("\n  What win rate do we get at different MC probability thresholds?")
    
    b15 = df[df['buffer'] == 15]
    
    thresholds = [70, 75, 80, 85, 90, 92, 95]
    
    print(f"\n  {'Threshold':<12} {'Games':<10} {'Wins':<10} {'Win Rate':<12} {'ROI (est)':<10}")
    print("  " + "-" * 60)
    
    for thresh in thresholds:
        above = b15[b15['mc_prob'] >= thresh]
        if len(above) == 0:
            continue
        
        wins = len(above[above['actual_hit'] == True])
        total = len(above)
        win_rate = wins / total * 100
        
        # Estimate ROI at -450 odds (typical minimum alternate)
        # Win = +$22.22 per $100, Loss = -$100
        roi = (wins * 22.22 - (total - wins) * 100) / total
        
        print(f"  {thresh}%+{'':<8} {total:<10} {wins:<10} {win_rate:<11.1f}% {roi:>+.1f}%")
    
    print("""
  
  ROI calculation assumes -450 average odds on minimum alternates
  Positive ROI = profitable, Negative ROI = losing money
    """)


if __name__ == "__main__":
    df = run_full_backtest()
    analyze_mc_thresholds(df)
    
    print("\n" + "=" * 80)
    print("BACKTEST COMPLETE")
    print("=" * 80)
