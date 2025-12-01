"""
FINAL SANITY CHECK
==================
Let's manually verify a few games to make sure everything is correct
"""

import pandas as pd

def sanity_check():
    print("\n" + "=" * 80)
    print("🔍 FINAL SANITY CHECK")
    print("=" * 80)
    
    # Load the backtest results
    import glob
    result_files = glob.glob('valid_backtest_v33_*.csv')
    if not result_files:
        print("No results file found!")
        return
    
    results = pd.read_csv(sorted(result_files)[-1])
    completed = pd.read_csv('data/nba_completed_games_2025_2026.csv')
    
    print(f"\n  Backtest results: {len(results)} games")
    print(f"  0-flag games: {len(results[results['category'] == '0_flags'])}")
    
    # Check a few specific games manually
    print("\n" + "-" * 80)
    print("MANUAL VERIFICATION (Random Sample)")
    print("-" * 80)
    
    # Get 5 random 0-flag games
    zero_flag = results[results['category'] == '0_flags'].sample(min(5, len(results)))
    
    for _, row in zero_flag.iterrows():
        game = row['game']
        line = row['line']
        actual = row['actual']
        result = row['result']
        buffer = row['buffer']
        
        # Parse teams
        if ' @ ' in game:
            away, home = game.split(' @ ')
        else:
            continue
        
        # Find in completed games
        match = completed[
            (completed['Visitor'] == away) & 
            (completed['Home'] == home)
        ]
        
        print(f"\n  Game: {game}")
        print(f"  Line from prediction file: {line}")
        
        if len(match) > 0:
            real_total = match.iloc[0]['Total_Points']
            print(f"  Actual total from completed_games: {real_total}")
            print(f"  Backtest recorded actual: {actual}")
            
            if real_total == actual:
                print(f"  ✅ MATCH - Data is consistent")
            else:
                print(f"  ❌ MISMATCH - Something is wrong!")
            
            # Verify win/loss logic
            if real_total > line:
                expected_result = 'WIN'
            else:
                expected_result = 'LOSS'
            
            print(f"  Expected result: {expected_result}")
            print(f"  Recorded result: {result}")
            
            if expected_result == result:
                print(f"  ✅ WIN/LOSS logic correct")
            else:
                print(f"  ❌ WIN/LOSS logic ERROR!")
        else:
            print(f"  ⚠️ Game not found in completed_games")
    
    # Check for any close calls (buffer < 5)
    print("\n" + "-" * 80)
    print("CLOSEST CALLS (Buffer < 5 points)")
    print("-" * 80)
    
    close_calls = results[(results['category'] == '0_flags') & (results['buffer'] < 5)]
    
    if len(close_calls) == 0:
        print("\n  No games with buffer < 5 points")
    else:
        print(f"\n  Found {len(close_calls)} close calls:")
        for _, row in close_calls.iterrows():
            print(f"    {row['game']}")
            print(f"    Line: {row['line']} | Actual: {row['actual']} | Buffer: {row['buffer']}")
            print()
    
    # Check for ANY losses anywhere
    print("\n" + "-" * 80)
    print("LOSS CHECK")
    print("-" * 80)
    
    losses = results[results['result'] == 'LOSS']
    print(f"\n  Total losses in backtest: {len(losses)}")
    
    if len(losses) > 0:
        print("\n  LOSSES:")
        for _, row in losses.iterrows():
            print(f"    {row['game']} | Line: {row['line']} | Actual: {row['actual']}")
    else:
        print("  No losses recorded")
    
    # What about the legacy system losses?
    print("\n" + "-" * 80)
    print("COMPARISON: Legacy System Losses")
    print("-" * 80)
    print("""
    Your legacy system (non-MC) had these losses:
    
    1. Boston @ Philly: Line 209.5, Actual 202.0 (LOSS)
    2. Cleveland @ Toronto: Line 215.5, Actual 209.0 (LOSS)  
    3. San Antonio @ Portland: Line 218.5, Actual 217.0 (LOSS)
    4. Memphis @ Cleveland: Line 216.5, Actual 208.0 (LOSS)
    5. San Antonio @ Phoenix: Line 213.5, Actual 213.0 (LOSS)
    6. LA Lakers @ Utah: Line 223.5, Actual 214.0 (LOSS)
    7. Milwaukee @ Miami: Line 215.5, Actual 209.0 (LOSS)
    
    Let's check if V3.3 would have flagged these...
    """)
    
    # Check if these games are in our 0-flag results
    legacy_losses = [
        ('Boston Celtics', 'Philadelphia 76ers', 209.5, 202.0),
        ('Cleveland Cavaliers', 'Toronto Raptors', 215.5, 209.0),
        ('San Antonio Spurs', 'Portland Trail Blazers', 218.5, 217.0),
        ('Memphis Grizzlies', 'Cleveland Cavaliers', 216.5, 208.0),
        ('San Antonio Spurs', 'Phoenix Suns', 213.5, 213.0),
        ('Los Angeles Lakers', 'Utah Jazz', 223.5, 214.0),
        ('Milwaukee Bucks', 'Miami Heat', 215.5, 209.0),
    ]
    
    for away, home, line, actual in legacy_losses:
        game_str = f"{away} @ {home}"
        
        # Check if this game is in 0-flag results
        in_zero_flag = len(results[
            (results['game'] == game_str) & 
            (results['category'] == '0_flags')
        ]) > 0
        
        in_any_results = len(results[results['game'] == game_str]) > 0
        
        if in_zero_flag:
            print(f"  ⚠️ {game_str}")
            print(f"     Was 0-flag in backtest - would have lost!")
        elif in_any_results:
            row = results[results['game'] == game_str].iloc[0]
            print(f"  ✅ {game_str}")
            print(f"     Category: {row['category']} - would have been SKIPPED")
        else:
            print(f"  ❓ {game_str}")
            print(f"     Not in backtest data")
    
    print("\n" + "=" * 80)
    print("📋 SUMMARY")
    print("=" * 80)


if __name__ == "__main__":
    sanity_check()
