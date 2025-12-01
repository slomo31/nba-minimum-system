"""
Quick Test: V3.3 on Today's Games
==================================
Test smart variance handling
"""

import pandas as pd
from monte_carlo_engine_v3_3 import MonteCarloEngineV33

def test_v33_today():
    """Test V3.3 on today's games"""
    
    print("\n" + "=" * 80)
    print("🧪 V3.3 TEST: TODAY'S GAMES (SMART VARIANCE)")
    print("=" * 80)
    
    # Load data
    team_stats = pd.read_csv('data/nba_team_stats_2025_2026.csv')
    completed_games = pd.read_csv('data/nba_completed_games_2025_2026.csv')
    
    # Initialize V3.3 engine
    engine = MonteCarloEngineV33(team_stats, completed_games)
    
    # Today's games
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
    print("ANALYZING GAMES WITH V3.3 (SMART VARIANCE)")
    print("-" * 80)
    
    bettable = []
    skip = []
    
    for away, home, line in todays_games:
        result = engine.analyze_game(away, home, line)
        
        if result is None:
            continue
        
        game_str = f"{away} @ {home}"
        mc_prob = result['mc_probability']
        flags = result['flag_count']
        flag_list = result['flags']
        decision = result['decision']
        
        # Get variance info
        away_var = engine.team_profiles.get(away, {}).get('variance', 0)
        home_var = engine.team_profiles.get(home, {}).get('variance', 0)
        
        if flags == 0 and mc_prob >= 88:
            bettable.append({
                'game': game_str,
                'line': line,
                'mc_prob': mc_prob,
                'flags': flags,
                'decision': decision,
                'away_var': away_var,
                'home_var': home_var
            })
            print(f"\n  ✅ BET: {game_str}")
            print(f"     Line: {line} | MC: {mc_prob:.1f}% | Flags: {flags}")
            print(f"     Variance: {away_var:.1f} / {home_var:.1f} (not flagged)")
        else:
            skip.append({
                'game': game_str,
                'line': line,
                'mc_prob': mc_prob,
                'flags': flags,
                'flag_list': flag_list,
                'away_var': away_var,
                'home_var': home_var
            })
            print(f"\n  ❌ SKIP: {game_str}")
            print(f"     Line: {line} | MC: {mc_prob:.1f}% | Flags: {flags}")
            print(f"     Variance: {away_var:.1f} / {home_var:.1f}")
            for f in flag_list:
                print(f"     - {f}")
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 V3.3 RESULTS FOR TODAY")
    print("=" * 80)
    
    print(f"\n  ✅ BETTABLE (0 flags): {len(bettable)}")
    for b in bettable:
        print(f"     🟢 {b['game']}")
        print(f"        Line: {b['line']} | MC: {b['mc_prob']:.1f}% | {b['decision']}")
    
    print(f"\n  ❌ SKIP (has flags): {len(skip)}")
    
    # Compare versions
    print("\n" + "=" * 80)
    print("📈 VERSION COMPARISON (TODAY)")
    print("=" * 80)
    print(f"""
    V3.1 (Strict):        0 bettable games
    V3.2 (Loosened):      0 bettable games  
    V3.3 (Smart Var):     {len(bettable)} bettable games
    
    Improvement: +{len(bettable)} picks!
    """)
    
    return bettable


if __name__ == "__main__":
    bettable = test_v33_today()
