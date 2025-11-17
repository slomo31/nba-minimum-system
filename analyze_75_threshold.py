"""
75% THRESHOLD ANALYZER
======================
Tests what your system would do at 75% threshold instead of 80%

IMPORTANT: This does NOT modify your working system!
It just re-analyzes the backtest data with a lower threshold.

Usage:
    python analyze_75_threshold.py
"""

import pandas as pd
import os
from datetime import datetime


def analyze_at_75_threshold(backtest_results_df):
    """
    Re-classify predictions using 75% threshold instead of 80%
    
    Current system: 80+ = YES, 70-79 = MAYBE, <70 = NO
    This test: 75+ = YES, 65-74 = MAYBE, <65 = NO
    """
    print("\n" + "=" * 70)
    print("RE-ANALYZING AT 75% THRESHOLD")
    print("=" * 70)
    print("\nCurrent system uses 80% threshold")
    print("This analysis shows what happens at 75% threshold")
    print()
    
    # Make a copy to avoid modifying original
    df = backtest_results_df.copy()
    
    # Re-classify based on 75% threshold
    df['prediction_75'] = df['confidence'].apply(
        lambda x: 'YES' if x >= 75 else ('MAYBE' if x >= 65 else 'NO')
    )
    
    # Compare to original predictions
    original_yes = len(df[df['prediction'] == 'YES'])
    new_yes = len(df[df['prediction_75'] == 'YES'])
    additional_yes = new_yes - original_yes
    
    print(f"PREDICTION COMPARISON:")
    print(f"  At 80% threshold: {original_yes} YES bets")
    print(f"  At 75% threshold: {new_yes} YES bets")
    print(f"  Additional bets: +{additional_yes} games")
    print(f"  Increase: {(additional_yes / original_yes * 100):.1f}%")
    
    # Show the new YES bets (those that are 75-79% confidence)
    new_bets = df[(df['confidence'] >= 75) & (df['confidence'] < 80)]
    
    print(f"\n" + "-" * 70)
    print(f"NEW YES BETS (75-79% confidence range):")
    print("-" * 70)
    print(f"\nTotal: {len(new_bets)} games")
    
    if len(new_bets) > 0:
        wins = len(new_bets[new_bets['went_over'] == True])
        losses = len(new_bets[new_bets['went_over'] == False])
        win_rate = (wins / len(new_bets) * 100) if len(new_bets) > 0 else 0
        
        print(f"  Wins: {wins}")
        print(f"  Losses: {losses}")
        print(f"  Win rate: {win_rate:.1f}%")
        
        # Show sample of new bets
        print(f"\n  Sample games (75-79% confidence):")
        for _, game in new_bets.head(10).iterrows():
            result = "✅ WIN" if game['went_over'] else "❌ LOSS"
            print(f"    {result} - {game['game']}")
            print(f"       Confidence: {game['confidence']}% | Min: {game['minimum']} | Actual: {game['actual_total']}")
    
    # Calculate overall performance at 75% threshold
    yes_75 = df[df['prediction_75'] == 'YES']
    
    if len(yes_75) > 0:
        wins = len(yes_75[yes_75['went_over'] == True])
        losses = len(yes_75[yes_75['went_over'] == False])
        win_rate = (wins / len(yes_75) * 100) if len(yes_75) > 0 else 0
        
        print(f"\n" + "=" * 70)
        print("OVERALL PERFORMANCE AT 75% THRESHOLD")
        print("=" * 70)
        print(f"\nTotal YES predictions: {len(yes_75)}")
        print(f"  Wins: {wins} ✅")
        print(f"  Losses: {losses} ❌")
        print(f"  Win rate: {win_rate:.1f}%")
        
        # Compare to 80% threshold
        original_yes_bets = df[df['prediction'] == 'YES']
        original_wins = len(original_yes_bets[original_yes_bets['went_over'] == True])
        original_win_rate = (original_wins / len(original_yes_bets) * 100) if len(original_yes_bets) > 0 else 0
        
        print(f"\n" + "-" * 70)
        print("COMPARISON:")
        print("-" * 70)
        print(f"  80% threshold: {original_win_rate:.1f}% win rate on {len(original_yes_bets)} bets")
        print(f"  75% threshold: {win_rate:.1f}% win rate on {len(yes_75)} bets")
        print(f"  Win rate change: {win_rate - original_win_rate:+.1f}%")
        
        # Recommendation
        print(f"\n" + "-" * 70)
        print("RECOMMENDATION:")
        print("-" * 70)
        
        if win_rate >= 85:
            print("  ✅ LOWER THRESHOLD - Win rate still excellent!")
            print(f"     You'd get {additional_yes} more bets with {win_rate:.1f}% accuracy")
        elif win_rate >= 80:
            print("  ⚠️ CONSIDER LOWERING - Win rate still good but slightly lower")
            print(f"     Trade-off: {additional_yes} more bets but {original_win_rate - win_rate:.1f}% lower accuracy")
        else:
            print("  ❌ KEEP 80% - Win rate drops too much at 75%")
            print(f"     Not worth the {original_win_rate - win_rate:.1f}% accuracy decrease")
    
    return df


def analyze_parlay_at_75(df):
    """Analyze parlay performance at 75% threshold"""
    print("\n" + "=" * 70)
    print("PARLAY PERFORMANCE AT 75% THRESHOLD")
    print("=" * 70)
    
    # Filter to YES at 75% threshold
    yes_bets = df[df['prediction_75'] == 'YES'].copy()
    
    if len(yes_bets) == 0:
        print("No YES predictions at 75% threshold")
        return None
    
    # Convert date
    yes_bets['date'] = pd.to_datetime(yes_bets['date'])
    yes_bets['date_only'] = yes_bets['date'].dt.date
    
    # Group by date
    by_date = yes_bets.groupby('date_only')
    
    parlay_nights = []
    
    for date, games in by_date:
        total_games = len(games)
        wins = len(games[games['went_over'] == True])
        losses = len(games[games['went_over'] == False])
        
        # Parlay wins only if ALL games won
        parlay_result = 'WIN' if losses == 0 else 'LOSS'
        
        parlay_nights.append({
            'date': date,
            'games_bet': total_games,
            'parlay_result': parlay_result
        })
    
    parlay_df = pd.DataFrame(parlay_nights)
    
    # Calculate stats
    total_nights = len(parlay_df)
    parlay_wins = len(parlay_df[parlay_df['parlay_result'] == 'WIN'])
    parlay_losses = len(parlay_df[parlay_df['parlay_result'] == 'LOSS'])
    parlay_win_rate = (parlay_wins / total_nights * 100) if total_nights > 0 else 0
    
    print(f"\nTotal betting nights: {total_nights}")
    print(f"Perfect parlay nights: {parlay_wins} ✅")
    print(f"Losing parlay nights: {parlay_losses} ❌")
    print(f"PARLAY WIN RATE: {parlay_win_rate:.1f}%")
    
    # Breakdown by size
    print("\n" + "-" * 70)
    print("BREAKDOWN BY PARLAY SIZE:")
    print("-" * 70)
    
    for num_games in sorted(parlay_df['games_bet'].unique()):
        subset = parlay_df[parlay_df['games_bet'] == num_games]
        subset_wins = len(subset[subset['parlay_result'] == 'WIN'])
        subset_total = len(subset)
        subset_win_rate = (subset_wins / subset_total * 100) if subset_total > 0 else 0
        
        print(f"\n{num_games}-Game Parlays:")
        print(f"  Nights: {subset_total}")
        print(f"  Wins: {subset_wins}")
        print(f"  Win Rate: {subset_win_rate:.1f}%")
    
    return parlay_df


def main():
    """Run 75% threshold analysis"""
    print("\n" + "=" * 70)
    print("🎲 75% THRESHOLD ANALYZER")
    print("=" * 70)
    print("\nThis shows what would happen if you lowered threshold to 75%")
    print("(Your current system at 80% is NOT modified)")
    print()
    
    # Load backtest results
    backtest_files = []
    if os.path.exists('output_archive/backtests'):
        backtest_files = [f for f in os.listdir('output_archive/backtests') if f.endswith('.csv')]
    
    if not backtest_files:
        print("❌ No backtest results found!")
        print("   Run: python run_backtest.py first")
        return False
    
    # Use most recent
    latest_file = sorted(backtest_files)[-1]
    filepath = os.path.join('output_archive/backtests', latest_file)
    
    print(f"📂 Loading: {filepath}\n")
    
    results = pd.read_csv(filepath)
    
    print(f"✓ Loaded {len(results)} games")
    
    # Analyze at 75% threshold
    df_75 = analyze_at_75_threshold(results)
    
    # Analyze parlay performance at 75%
    parlay_75 = analyze_parlay_at_75(df_75)
    
    # Final comparison
    print("\n" + "=" * 70)
    print("FINAL COMPARISON: 80% vs 75% THRESHOLD")
    print("=" * 70)
    
    # Load parlay results at 80% for comparison
    yes_80 = results[results['prediction'] == 'YES']
    yes_75 = df_75[df_75['prediction_75'] == 'YES']
    
    wins_80 = len(yes_80[yes_80['went_over'] == True])
    wins_75 = len(yes_75[yes_75['went_over'] == True])
    
    print(f"\nINDIVIDUAL GAME PERFORMANCE:")
    print(f"  80% threshold: {len(yes_80)} bets, {wins_80} wins ({wins_80/len(yes_80)*100:.1f}%)")
    print(f"  75% threshold: {len(yes_75)} bets, {wins_75} wins ({wins_75/len(yes_75)*100:.1f}%)")
    
    if parlay_75 is not None:
        # Calculate parlay stats at 80% from original analysis
        yes_80_dated = yes_80.copy()
        yes_80_dated['date'] = pd.to_datetime(yes_80_dated['date'])
        yes_80_dated['date_only'] = yes_80_dated['date'].dt.date
        
        nights_80 = len(yes_80_dated.groupby('date_only'))
        
        # Get nights_75
        nights_75 = len(parlay_75)
        
        print(f"\nPARLAY NIGHTS:")
        print(f"  80% threshold: {nights_80} nights")
        print(f"  75% threshold: {nights_75} nights")
        print(f"  Additional nights: +{nights_75 - nights_80}")
    
    print("\n" + "=" * 70)
    
    return True


if __name__ == "__main__":
    success = main()
    if not success:
        exit(1)
