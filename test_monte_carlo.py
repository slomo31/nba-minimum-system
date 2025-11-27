"""
Test Monte Carlo Engine
========================
Validates the MC engine works correctly with your data.
Also backtests against your known losses to confirm it would have caught them.
"""

import pandas as pd
import numpy as np
import sys
import os

# Add paths
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_monte_carlo():
    """Test the Monte Carlo engine with sample data"""
    
    print("=" * 70)
    print("MONTE CARLO ENGINE - VALIDATION TEST")
    print("=" * 70)
    
    # Load your actual data
    print("\n1. Loading data...")
    
    try:
        team_stats = pd.read_csv('data/nba_team_stats_2025_2026.csv')
        completed_games = pd.read_csv('data/nba_completed_games_2025_2026.csv')
        print(f"   ✓ Loaded {len(team_stats)} teams")
        print(f"   ✓ Loaded {len(completed_games)} completed games")
    except FileNotFoundError as e:
        print(f"   ✗ Error: {e}")
        print("   Make sure you're running from your nba_minimun_system directory")
        return False
    
    # Import and initialize MC engine
    print("\n2. Initializing Monte Carlo Engine...")
    
    from core.monte_carlo_engine import MonteCarloEngine, print_team_profiles
    
    mc_engine = MonteCarloEngine(team_stats, completed_games, n_simulations=10000)
    print(f"   ✓ Engine initialized with 10,000 simulations per game")
    
    # Print team profiles
    print("\n3. Team Variance Profiles:")
    print_team_profiles(mc_engine)
    
    # Test on your known losses
    print("\n" + "=" * 70)
    print("4. BACKTEST: Testing Against Your 5 Known Losses")
    print("=" * 70)
    
    losses = [
        # (away_team, home_team, minimum_line, actual_total, original_conf)
        ("Boston Celtics", "Philadelphia 76ers", 209.5, 202.0, 90),
        ("Memphis Grizzlies", "Cleveland Cavaliers", 216.5, 208.0, 77),
        ("Los Angeles Lakers", "Utah Jazz", 223.5, 214.0, 70),
        ("San Antonio Spurs", "Phoenix Suns", 213.5, 213.0, 78),
        ("Cleveland Cavaliers", "Toronto Raptors", 215.5, 209.0, 82),
    ]
    
    caught = 0
    
    for away, home, line, actual, orig_conf in losses:
        print(f"\n  {away} @ {home}")
        print(f"  Line: {line} | Actual: {actual} | Original Conf: {orig_conf}%")
        
        result = mc_engine.simulate_game(away, home, line)
        mc_prob = result['mc_probability']
        
        # Would MC have caught this?
        if mc_prob < 80:
            caught += 1
            status = "✓ CAUGHT"
        else:
            status = "✗ MISSED"
        
        print(f"  MC Probability: {mc_prob}%")
        print(f"  Status: {status}")
        
        if result['risk_factors']:
            print(f"  Risk factors: {', '.join(result['risk_factors'][:2])}")
    
    print(f"\n" + "=" * 70)
    print(f"BACKTEST RESULT: MC would have caught {caught}/5 losses ({caught/5*100:.0f}%)")
    print("=" * 70)
    
    # Test parlay calculation
    print("\n5. Testing Parlay Calculator...")
    
    test_probs = [92.5, 88.3, 85.1]
    combined = mc_engine.calculate_parlay_probability(test_probs)
    print(f"   Individual: {test_probs}")
    print(f"   Combined: {combined}%")
    print(f"   Expected: ~69.5%")
    
    # Test a few sample games
    print("\n" + "=" * 70)
    print("6. Sample Simulations")
    print("=" * 70)
    
    sample_games = [
        ("Denver Nuggets", "Sacramento Kings", 215.0),
        ("Memphis Grizzlies", "Atlanta Hawks", 218.0),
        ("Utah Jazz", "Cleveland Cavaliers", 210.0),  # Slow teams
    ]
    
    for away, home, line in sample_games:
        print(f"\n  {away} @ {home} (Line: {line})")
        result = mc_engine.simulate_game(away, home, line)
        
        decision, level = mc_engine.get_mc_decision(result['mc_probability'])[:2]
        
        print(f"  MC Probability: {result['mc_probability']}%")
        print(f"  Decision: {decision} ({level})")
        print(f"  Simulated range: {result['percentile_5']} - {result['percentile_95']}")
        if result['risk_factors']:
            print(f"  Risk factors: {', '.join(result['risk_factors'][:2])}")
    
    print("\n" + "=" * 70)
    print("✓ MONTE CARLO ENGINE VALIDATION COMPLETE")
    print("=" * 70)
    
    return True


if __name__ == "__main__":
    success = test_monte_carlo()
    sys.exit(0 if success else 1)
