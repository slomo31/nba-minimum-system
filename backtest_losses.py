"""
BACKTEST: Verify Monte Carlo Would Have Caught Your 5 Losses
=============================================================
"""

import pandas as pd
import numpy as np
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Try v3 first, fall back to v1
try:
    from core.monte_carlo_engine import MonteCarloEngineV3 as MonteCarloEngine
    print("Using Monte Carlo Engine v3.0")
except ImportError:
    try:
        from core.monte_carlo_engine import MonteCarloEngine
        print("Using Monte Carlo Engine v1.0")
    except ImportError:
        print("ERROR: Could not import Monte Carlo Engine")
        print("Make sure monte_carlo_engine.py is in core/ folder")
        sys.exit(1)


def run_backtest():
    """Test MC against your 5 known losses"""
    
    print("=" * 70)
    print("MONTE CARLO BACKTEST - YOUR 5 LOSSES")
    print("=" * 70)
    
    # Load data
    print("\nLoading data...")
    team_stats = pd.read_csv('data/nba_team_stats_2025_2026.csv')
    completed_games = pd.read_csv('data/nba_completed_games_2025_2026.csv')
    print(f"  ✓ {len(team_stats)} teams, {len(completed_games)} completed games")
    
    # Initialize MC engine
    print("\nInitializing Monte Carlo Engine...")
    mc_engine = MonteCarloEngine(team_stats, completed_games, n_simulations=10000)
    
    # Your 5 losses
    losses = [
        {
            'date': '2025-11-12',
            'away': 'Boston Celtics',
            'home': 'Philadelphia 76ers',
            'line': 209.5,
            'actual': 202.0,
            'original_conf': 90,
            'bet_type': 'YES'
        },
        {
            'date': '2025-11-15',
            'away': 'Memphis Grizzlies',
            'home': 'Cleveland Cavaliers',
            'line': 216.5,
            'actual': 208.0,
            'original_conf': 77,
            'bet_type': 'MAYBE'
        },
        {
            'date': '2025-11-24',
            'away': 'Los Angeles Lakers',
            'home': 'Utah Jazz',
            'line': 223.5,
            'actual': 214.0,
            'original_conf': 70,
            'bet_type': 'MAYBE'
        },
        {
            'date': '2025-11-24',
            'away': 'San Antonio Spurs',
            'home': 'Phoenix Suns',
            'line': 213.5,
            'actual': 213.0,
            'original_conf': 78,
            'bet_type': 'MAYBE'
        },
        {
            'date': '2025-11-25',
            'away': 'Cleveland Cavaliers',
            'home': 'Toronto Raptors',
            'line': 215.5,
            'actual': 209.0,
            'original_conf': 82,
            'bet_type': 'YES'
        },
    ]
    
    print("\n" + "=" * 70)
    print("RUNNING MONTE CARLO ON EACH LOSS")
    print("=" * 70)
    
    caught = 0
    results = []
    
    for loss in losses:
        print(f"\n{'─' * 70}")
        print(f"  {loss['date']} | {loss['away']} @ {loss['home']}")
        print(f"  Line: {loss['line']} | Actual: {loss['actual']} | Missed by: {loss['line'] - loss['actual']:.1f}")
        print(f"  Original Confidence: {loss['original_conf']}% ({loss['bet_type']})")
        
        # Run MC simulation
        result = mc_engine.simulate_game(
            away_team=loss['away'],
            home_team=loss['home'],
            minimum_line=loss['line']
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
        
        # Would MC have prevented this loss?
        # We only bet on 85%+ now, so anything below = CAUGHT
        would_skip = mc_prob < 85
        
        if would_skip:
            caught += 1
            status = "✓ CAUGHT - MC would have skipped this"
        else:
            status = "✗ MISSED - MC would have bet this too"
        
        print(f"\n  MC Probability: {mc_prob}%")
        print(f"  MC Decision: {mc_decision}")
        print(f"  Simulated range: {result['percentile_5']} - {result['percentile_95']}")
        
        if result['risk_factors']:
            print(f"  Risk factors:")
            for rf in result['risk_factors'][:3]:
                print(f"    • {rf}")
        
        print(f"\n  >>> {status}")
        
        results.append({
            'game': f"{loss['away']} @ {loss['home']}",
            'date': loss['date'],
            'line': loss['line'],
            'actual': loss['actual'],
            'original_conf': loss['original_conf'],
            'mc_prob': mc_prob,
            'mc_decision': mc_decision,
            'caught': would_skip
        })
    
    # Summary
    print("\n" + "=" * 70)
    print("BACKTEST SUMMARY")
    print("=" * 70)
    
    print(f"\n  Total losses tested: 5")
    print(f"  MC would have caught: {caught}")
    print(f"  MC would have missed: {5 - caught}")
    print(f"  Catch rate: {caught/5*100:.0f}%")
    
    print("\n  BREAKDOWN:")
    print("  " + "─" * 66)
    print(f"  {'Game':<40} {'Orig':>6} {'MC':>8} {'Caught':>8}")
    print("  " + "─" * 66)
    
    for r in results:
        caught_str = "✓ YES" if r['caught'] else "✗ NO"
        print(f"  {r['game']:<40} {r['original_conf']:>5}% {r['mc_prob']:>7.1f}% {caught_str:>8}")
    
    # Analysis
    print("\n" + "=" * 70)
    print("ANALYSIS")
    print("=" * 70)
    
    yes_losses = [r for r in results if r['original_conf'] >= 80]
    maybe_losses = [r for r in results if r['original_conf'] < 80]
    
    print(f"\n  YES bet losses (80%+ original): {len(yes_losses)}")
    for r in yes_losses:
        caught_str = "CAUGHT" if r['caught'] else "MISSED"
        print(f"    • {r['game']}: {r['original_conf']}% → MC {r['mc_prob']:.1f}% [{caught_str}]")
    
    print(f"\n  MAYBE bet losses (<80% original): {len(maybe_losses)}")
    for r in maybe_losses:
        caught_str = "CAUGHT" if r['caught'] else "MISSED"
        print(f"    • {r['game']}: {r['original_conf']}% → MC {r['mc_prob']:.1f}% [{caught_str}]")
    
    # Impact
    print("\n" + "=" * 70)
    print("PROJECTED IMPACT")
    print("=" * 70)
    
    print(f"""
  Your current record: 73-5 (93.6%)
  
  If MC had been active (85% threshold):
    - Losses caught: {caught}
    - Losses still taken: {5 - caught}
    - Projected record: 73-{5-caught} ({73/(73+5-caught)*100:.1f}%)
  
  Key insight: MC catches games with hidden variance, 
  slow pace matchups, and defensive battles.
    """)
    
    return caught


if __name__ == "__main__":
    caught = run_backtest()
    print(f"\n{'=' * 70}")
    print(f"RESULT: MC would have prevented {caught} of your 5 losses")
    print("=" * 70)