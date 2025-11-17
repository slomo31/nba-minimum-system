"""
TONIGHT'S PICKS - 80% vs 75% THRESHOLD COMPARISON
==================================================
Shows what picks you'd get tonight at different thresholds

Usage:
    python compare_tonight_thresholds.py
"""

import pandas as pd
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.minimum_total_predictor import MinimumTotalPredictor


def analyze_tonight_at_threshold(upcoming_games, team_stats, completed_games, threshold):
    """Run predictions and filter by threshold"""
    
    # Run predictions
    predictor = MinimumTotalPredictor(team_stats, completed_games)
    predictions = predictor.predict_all_games(upcoming_games)
    
    # Apply threshold
    picks = []
    for pred in predictions:
        confidence = pred['confidence']
        
        if confidence >= threshold:
            decision = 'YES'
            stake = '3% bankroll'
        elif confidence >= (threshold - 10):  # MAYBE range
            decision = 'MAYBE'
            stake = '2% bankroll (optional)'
        else:
            decision = 'NO'
            stake = '0%'
        
        picks.append({
            'game': f"{pred['away_team']} @ {pred['home_team']}",
            'away_team': pred['away_team'],
            'home_team': pred['home_team'],
            'game_time': pred['game_time'],
            'minimum_total': pred['minimum_total'],
            'minimum_odds': pred['minimum_odds'],
            'confidence': confidence,
            'score': pred['total_score'],
            'decision': decision,
            'stake': stake,
            'reasoning': ' | '.join(pred['reasoning'][:3])
        })
    
    return pd.DataFrame(picks)


def main():
    """Compare tonight's picks at different thresholds"""
    
    print("\n" + "=" * 70)
    print("🏀 TONIGHT'S PICKS - THRESHOLD COMPARISON")
    print("=" * 70)
    print()
    
    # Load data
    print("Loading data...")
    
    if not os.path.exists('data/upcoming_games.csv'):
        print("❌ No upcoming games found!")
        print("   Run: python master_workflow.py first")
        return False
    
    if not os.path.exists('data/nba_team_stats_2025_2026.csv'):
        print("❌ Team stats not found!")
        return False
    
    if not os.path.exists('data/nba_completed_games_2025_2026.csv'):
        print("❌ Completed games not found!")
        return False
    
    upcoming = pd.read_csv('data/upcoming_games.csv')
    team_stats = pd.read_csv('data/nba_team_stats_2025_2026.csv')
    completed_games = pd.read_csv('data/nba_completed_games_2025_2026.csv')
    
    print(f"✓ Found {len(upcoming)} games tonight")
    print()
    
    # Analyze at 80% threshold
    print("=" * 70)
    print("AT 80% THRESHOLD (YOUR CURRENT SYSTEM)")
    print("=" * 70)
    
    picks_80 = analyze_tonight_at_threshold(upcoming, team_stats, completed_games, 80)
    
    yes_80 = picks_80[picks_80['decision'] == 'YES']
    maybe_80 = picks_80[picks_80['decision'] == 'MAYBE']
    no_80 = picks_80[picks_80['decision'] == 'NO']
    
    print(f"\nTotal games: {len(picks_80)}")
    print(f"  YES: {len(yes_80)}")
    print(f"  MAYBE: {len(maybe_80)}")
    print(f"  NO: {len(no_80)}")
    
    if len(yes_80) > 0:
        print(f"\n✅ YES BETS at 80%:")
        for _, game in yes_80.iterrows():
            print(f"  • {game['game']}")
            print(f"    Over {game['minimum_total']} at {game['minimum_odds']:+d}")
            print(f"    Confidence: {game['confidence']}% | Score: {game['score']}/110")
            print(f"    {game['reasoning']}")
    
    # Analyze at 75% threshold
    print("\n" + "=" * 70)
    print("AT 75% THRESHOLD (TEST)")
    print("=" * 70)
    
    picks_75 = analyze_tonight_at_threshold(upcoming, team_stats, completed_games, 75)
    
    yes_75 = picks_75[picks_75['decision'] == 'YES']
    maybe_75 = picks_75[picks_75['decision'] == 'MAYBE']
    no_75 = picks_75[picks_75['decision'] == 'NO']
    
    print(f"\nTotal games: {len(picks_75)}")
    print(f"  YES: {len(yes_75)}")
    print(f"  MAYBE: {len(maybe_75)}")
    print(f"  NO: {len(no_75)}")
    
    if len(yes_75) > 0:
        print(f"\n✅ YES BETS at 75%:")
        for _, game in yes_75.iterrows():
            print(f"  • {game['game']}")
            print(f"    Over {game['minimum_total']} at {game['minimum_odds']:+d}")
            print(f"    Confidence: {game['confidence']}% | Score: {game['score']}/110")
            print(f"    {game['reasoning']}")
    
    # Show the difference
    print("\n" + "=" * 70)
    print("COMPARISON: WHAT'S DIFFERENT?")
    print("=" * 70)
    
    # Find new picks at 75%
    yes_80_games = set(yes_80['game'].tolist())
    yes_75_games = set(yes_75['game'].tolist())
    
    new_at_75 = yes_75_games - yes_80_games
    
    print(f"\nPicks at 80%: {len(yes_80)} games")
    print(f"Picks at 75%: {len(yes_75)} games")
    print(f"Additional at 75%: {len(new_at_75)} games")
    
    if len(new_at_75) > 0:
        print(f"\n🆕 NEW PICKS at 75% threshold:")
        for game_name in new_at_75:
            game = picks_75[picks_75['game'] == game_name].iloc[0]
            print(f"\n  {game['game']}")
            print(f"    Over {game['minimum_total']} at {game['minimum_odds']:+d}")
            print(f"    Confidence: {game['confidence']}% | Score: {game['score']}/110")
            print(f"    Why it wasn't YES at 80%: {game['confidence']}% is below 80%")
            print(f"    {game['reasoning']}")
    else:
        print("\n  No additional picks - same games qualify at both thresholds")
    
    # Parlay strategy recommendation
    print("\n" + "=" * 70)
    print("PARLAY STRATEGY RECOMMENDATION")
    print("=" * 70)
    
    num_picks_80 = len(yes_80)
    num_picks_75 = len(yes_75)
    
    print(f"\nAt 80% threshold: {num_picks_80} picks")
    if num_picks_80 == 1:
        print("  → Single bet (not a parlay)")
        print("  → Bet 3% bankroll")
    elif num_picks_80 == 2:
        print("  → 2-game parlay night")
        print("  → Your 2-game parlay win rate: 80% (at 80% threshold)")
        print("  → RECOMMENDED: Parlay both at +260-280 odds")
    elif num_picks_80 == 3:
        print("  → 3-game parlay night")
        print("  → Your 3-game parlay win rate: 50% (at 80% threshold)")
        print("  → CAUTION: High variance, consider betting individually")
    else:
        print(f"  → {num_picks_80}-game parlay night")
        print("  → AVOID: Correlation risk too high")
        print("  → RECOMMENDED: Bet individually or skip")
    
    print(f"\nAt 75% threshold: {num_picks_75} picks")
    if num_picks_75 == 1:
        print("  → Single bet")
        print("  → Bet 3% bankroll")
    elif num_picks_75 == 2:
        print("  → 2-game parlay night")
        print("  → Your 2-game parlay win rate: 100% (at 75% threshold)")
        print("  → HIGHLY RECOMMENDED: Parlay both!")
    elif num_picks_75 == 3:
        print("  → 3-game parlay night")
        print("  → Your 3-game parlay win rate: 50% (at 75% threshold)")
        print("  → RECOMMENDED: Bet individually (87.5% each)")
    else:
        print(f"  → {num_picks_75}-game parlay night")
        print("  → AVOID parlaying all")
        print("  → RECOMMENDED: Cherry-pick best 2-3 or bet individually")
    
    # Final recommendation
    print("\n" + "=" * 70)
    print("TONIGHT'S ACTION PLAN")
    print("=" * 70)
    
    if num_picks_80 == 2:
        print(f"\n✅ RECOMMENDED ACTION (80% threshold):")
        print(f"   Parlay both picks at +260-280 odds")
        print(f"   Stake: 5% bankroll")
        print(f"   Your 2-game win rate: 80%")
        print(f"   Expected value: High positive")
    elif num_picks_80 >= 3:
        print(f"\n⚠️ RECOMMENDED ACTION (80% threshold):")
        print(f"   Consider betting individually instead of parlaying")
        print(f"   OR parlay only the top 2 by confidence")
    
    if len(new_at_75) > 0:
        print(f"\n💡 IF YOU LOWER TO 75%:")
        print(f"   You'd get {len(new_at_75)} additional pick(s)")
        if num_picks_75 == 2:
            print(f"   2-game parlay win rate: 100% at 75%")
            print(f"   These picks look strong!")
        elif num_picks_75 == 3:
            print(f"   But creates 3-game night (50% parlay win rate)")
            print(f"   Better to bet individually")
    
    print("\n" + "=" * 70)
    
    return True


if __name__ == "__main__":
    success = main()
    if not success:
        exit(1)
