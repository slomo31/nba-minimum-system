"""
Quick Test: V3.2 on Today's Games
==================================
See if loosened thresholds give us any picks for today
"""

import pandas as pd
import sys
import os

from monte_carlo_engine_v3_2 import MonteCarloEngineV32

def test_today():
    """Test V3.2 on today's games"""
    
    print("\n" + "=" * 80)
    print("🧪 V3.2 TEST: TODAY'S GAMES")
    print("=" * 80)
    
    # Load data
    team_stats = pd.read_csv('data/nba_team_stats_2025_2026.csv')
    completed_games = pd.read_csv('data/nba_completed_games_2025_2026.csv')
    
    # Initialize V3.2 engine
    engine = MonteCarloEngineV32(team_stats, completed_games)
    
    # Today's games (from your earlier output)
    todays_games = [
        ('Boston Celtics', 'Minnesota Timberwolves', 207.5),
        ('Toronto Raptors', 'Charlotte Hornets', 208.5),
        ('Chicago Bulls', 'Indiana Pacers', 221.5),
        ('Brooklyn Nets', 'Milwaukee Bucks', 201.5),
        ('Detroit Pistons', 'Miami Heat', 217.5),
        ('New Orleans Pelicans', 'Golden State Warriors', 203.5),
        ('Denver Nuggets', 'Phoenix Suns', 211.5),
        ('Dallas Mavericks', 'Los Angeles Clippers', 199.5),
    ]
    
    print("\n" + "-" * 80)
    print("ANALYZING GAMES WITH V3.2 (LOOSENED THRESHOLDS)")
    print("-" * 80)
    
    bettable = []
    skip = []
    
    for away, home, line in todays_games:
        result = engine.analyze_game(away, home, line)
        
        if result is None:
            print(f"  [SKIP] {away} @ {home} - Team not found")
            continue
        
        game_str = f"{away} @ {home}"
        mc_prob = result['mc_probability']
        flags = result['flag_count']
        flag_list = result['flags']
        decision = result['decision']
        
        if flags == 0 and mc_prob >= 88:
            bettable.append({
                'game': game_str,
                'line': line,
                'mc_prob': mc_prob,
                'flags': flags,
                'decision': decision
            })
            print(f"\n  ✅ {game_str}")
            print(f"     Line: {line} | MC: {mc_prob:.1f}% | Flags: {flags} | {decision}")
        else:
            skip.append({
                'game': game_str,
                'line': line,
                'mc_prob': mc_prob,
                'flags': flags,
                'flag_list': flag_list
            })
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 V3.2 RESULTS FOR TODAY")
    print("=" * 80)
    
    print(f"\n  ✅ BETTABLE (0 flags): {len(bettable)}")
    for b in bettable:
        print(f"     🟢 {b['game']} | Line: {b['line']} | MC: {b['mc_prob']:.1f}%")
    
    print(f"\n  ❌ SKIP (has flags): {len(skip)}")
    for s in skip:
        print(f"     ⚠️ {s['game']} | Flags: {s['flags']}")
        for f in s['flag_list'][:2]:  # Show first 2 flags
            print(f"        - {f}")
    
    # Compare to V3.1
    print("\n" + "=" * 80)
    print("📈 V3.1 vs V3.2 COMPARISON (TODAY)")
    print("=" * 80)
    print(f"""
    V3.1 (Strict):   0 bettable games
    V3.2 (Loosened): {len(bettable)} bettable games
    
    Improvement: +{len(bettable)} picks
    """)


if __name__ == "__main__":
    test_today()
