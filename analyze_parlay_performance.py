"""
PARLAY PERFORMANCE ANALYZER
============================
Analyzes backtest results from a PARLAY perspective

This script:
1. Groups YES predictions by DATE
2. Shows parlay success rate by night
3. Identifies false negatives (NO predictions that went over)
4. Does NOT modify any existing system files

Usage:
    python analyze_parlay_performance.py
"""

import pandas as pd
import os
from datetime import datetime


def analyze_parlay_by_date(backtest_results_df):
    """
    Group YES predictions by date and see if ALL won on each night
    
    This simulates a parlay strategy where you parlay all YES bets per night
    """
    print("\n" + "=" * 70)
    print("PARLAY PERFORMANCE BY DATE")
    print("=" * 70)
    
    # Filter to YES predictions only
    yes_bets = backtest_results_df[backtest_results_df['prediction'] == 'YES'].copy()
    
    if len(yes_bets) == 0:
        print("No YES predictions to analyze")
        return None
    
    # Convert date column
    yes_bets['date'] = pd.to_datetime(yes_bets['date'])
    yes_bets['date_only'] = yes_bets['date'].dt.date
    
    # Group by date
    by_date = yes_bets.groupby('date_only')
    
    parlay_nights = []
    
    for date, games in by_date:
        total_games = len(games)
        wins = len(games[games['result'] == 'WIN'])
        losses = len(games[games['result'] == 'LOSS'])
        
        # Parlay wins only if ALL games won
        parlay_result = 'WIN' if losses == 0 else 'LOSS'
        
        # Get game details
        game_list = games['game'].tolist()
        
        parlay_nights.append({
            'date': date,
            'games_bet': total_games,
            'individual_wins': wins,
            'individual_losses': losses,
            'parlay_result': parlay_result,
            'games': game_list
        })
    
    parlay_df = pd.DataFrame(parlay_nights)
    
    # Calculate stats
    total_nights = len(parlay_df)
    parlay_wins = len(parlay_df[parlay_df['parlay_result'] == 'WIN'])
    parlay_losses = len(parlay_df[parlay_df['parlay_result'] == 'LOSS'])
    parlay_win_rate = (parlay_wins / total_nights * 100) if total_nights > 0 else 0
    
    print(f"\nTotal betting nights: {total_nights}")
    print(f"Perfect parlay nights (ALL games won): {parlay_wins} ✅")
    print(f"Losing parlay nights (at least 1 loss): {parlay_losses} ❌")
    print(f"\nPARLAY WIN RATE: {parlay_win_rate:.1f}%")
    
    # Show details by number of games parlayed
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
    
    # Show losing nights in detail
    print("\n" + "=" * 70)
    print("LOSING PARLAY NIGHTS (DETAILED)")
    print("=" * 70)
    
    losing_nights = parlay_df[parlay_df['parlay_result'] == 'LOSS']
    
    for _, night in losing_nights.iterrows():
        print(f"\n📅 {night['date']}")
        print(f"   Games parlayed: {night['games_bet']}")
        print(f"   Individual results: {night['individual_wins']}W - {night['individual_losses']}L")
        print(f"   Games:")
        
        # Get detailed game info for this night
        night_games = yes_bets[yes_bets['date_only'] == night['date']]
        for _, game in night_games.iterrows():
            result_emoji = "✅" if game['result'] == 'WIN' else "❌"
            print(f"      {result_emoji} {game['game']}")
            print(f"         Minimum: {game['minimum']} | Actual: {game['actual_total']} | Conf: {game['confidence']}%")
    
    # Show winning nights too
    print("\n" + "=" * 70)
    print("WINNING PARLAY NIGHTS (PERFECT NIGHTS)")
    print("=" * 70)
    
    winning_nights = parlay_df[parlay_df['parlay_result'] == 'WIN']
    
    print(f"\nTotal perfect nights: {len(winning_nights)}")
    
    # Show a few examples
    print("\nSample winning nights:")
    for _, night in winning_nights.head(5).iterrows():
        print(f"\n📅 {night['date']}")
        print(f"   Games parlayed: {night['games_bet']} - ALL WON ✅")
        print(f"   Games: {', '.join(night['games'][:3])}{'...' if len(night['games']) > 3 else ''}")
    
    if len(winning_nights) > 5:
        print(f"\n   ... and {len(winning_nights) - 5} more perfect nights!")
    
    return parlay_df


def analyze_false_negatives(backtest_results_df):
    """
    Find NO predictions that still went over (system too conservative)
    """
    print("\n" + "=" * 70)
    print("FALSE NEGATIVES (NO PREDICTIONS THAT WENT OVER)")
    print("=" * 70)
    
    # Filter to NO predictions
    no_bets = backtest_results_df[backtest_results_df['prediction'] == 'NO'].copy()
    
    if len(no_bets) == 0:
        print("No NO predictions to analyze")
        return None
    
    # Find ones that went over anyway
    false_negatives = no_bets[no_bets['went_over'] == True].copy()
    
    print(f"\nTotal NO predictions: {len(no_bets)}")
    print(f"NO predictions that went over: {len(false_negatives)}")
    print(f"False negative rate: {len(false_negatives) / len(no_bets) * 100:.1f}%")
    
    if len(false_negatives) > 0:
        print("\nSystem was TOO CONSERVATIVE on these games:")
        print("(These would have won if we bet them)")
        print("-" * 70)
        
        # Convert date
        false_negatives['date'] = pd.to_datetime(false_negatives['date'])
        
        for _, game in false_negatives.iterrows():
            print(f"\n{game['date'].strftime('%Y-%m-%d')}: {game['game']}")
            print(f"  Minimum: {game['minimum']} | Actual: {game['actual_total']} ✅")
            print(f"  Confidence: {game['confidence']}% (below 80% threshold)")
            print(f"  Reasoning: {game['reasoning']}")
    
    return false_negatives


def calculate_parlay_profitability(parlay_df):
    """Calculate expected value for different parlay strategies"""
    print("\n" + "=" * 70)
    print("PARLAY PROFITABILITY ANALYSIS")
    print("=" * 70)
    
    # Overall stats
    total_nights = len(parlay_df)
    wins = len(parlay_df[parlay_df['parlay_result'] == 'WIN'])
    win_rate = (wins / total_nights) * 100 if total_nights > 0 else 0
    
    print(f"\nYour parlay win rate: {win_rate:.1f}%")
    print("\nExpected value at different parlay odds:")
    print("-" * 70)
    
    # Typical parlay odds
    scenarios = [
        (2, 2.6, "+260"),  # 2-leg parlay ~+260
        (2, 2.8, "+280"),
        (3, 6.0, "+600"),  # 3-leg parlay ~+600
        (3, 6.5, "+650"),
    ]
    
    for legs, decimal_odds, american_odds in scenarios:
        # Only analyze if we have data for this parlay size
        subset = parlay_df[parlay_df['games_bet'] == legs]
        if len(subset) == 0:
            continue
        
        subset_wins = len(subset[subset['parlay_result'] == 'WIN'])
        subset_win_rate = (subset_wins / len(subset)) if len(subset) > 0 else 0
        
        # Calculate EV per $100 bet
        win_amount = (decimal_odds - 1) * 100
        ev = (subset_win_rate * win_amount) - ((1 - subset_win_rate) * 100)
        
        status = "✅ PROFITABLE" if ev > 0 else "❌ NOT PROFITABLE"
        
        print(f"\n{legs}-Leg Parlay at {american_odds} odds:")
        print(f"  Your win rate: {subset_win_rate * 100:.1f}% ({subset_wins}/{len(subset)} nights)")
        print(f"  Expected value: ${ev:+.2f} per $100 bet")
        print(f"  Status: {status}")
        
        # Break-even
        breakeven = 100 / (win_amount + 100) * 100
        edge = (subset_win_rate * 100) - breakeven
        print(f"  Break-even: {breakeven:.1f}%")
        print(f"  Your edge: {edge:+.1f}%")


def main():
    """Run complete parlay analysis"""
    print("\n" + "=" * 70)
    print("🏀 NBA PARLAY PERFORMANCE ANALYZER")
    print("=" * 70)
    print("\nThis analyzes your backtest from a PARLAY perspective")
    print("(Grouping YES bets by night, not individual games)")
    print()
    
    # Check for backtest results
    backtest_files = []
    if os.path.exists('output_archive/backtests'):
        backtest_files = [f for f in os.listdir('output_archive/backtests') if f.endswith('.csv')]
    
    if not backtest_files:
        print("❌ No backtest results found!")
        print("   Run: python run_backtest.py first")
        return False
    
    # Use most recent backtest
    latest_file = sorted(backtest_files)[-1]
    filepath = os.path.join('output_archive/backtests', latest_file)
    
    print(f"📂 Loading backtest results from:")
    print(f"   {filepath}")
    print()
    
    # Load data
    results = pd.read_csv(filepath)
    
    print(f"✓ Loaded {len(results)} games")
    print(f"   YES predictions: {len(results[results['prediction'] == 'YES'])}")
    print(f"   NO predictions: {len(results[results['prediction'] == 'NO'])}")
    
    # Analyze parlay performance by date
    parlay_df = analyze_parlay_by_date(results)
    
    # Calculate profitability
    if parlay_df is not None:
        calculate_parlay_profitability(parlay_df)
    
    # Analyze false negatives
    false_negatives = analyze_false_negatives(results)
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    if parlay_df is not None:
        total_nights = len(parlay_df)
        wins = len(parlay_df[parlay_df['parlay_result'] == 'WIN'])
        losses = total_nights - wins
        win_rate = (wins / total_nights * 100) if total_nights > 0 else 0
        
        print(f"\n📊 PARLAY RECORD BY NIGHT:")
        print(f"   Betting nights: {total_nights}")
        print(f"   Perfect nights: {wins} ✅")
        print(f"   Losing nights: {losses} ❌")
        print(f"   Win rate: {win_rate:.1f}%")
        
        # Your statement check
        print(f"\n💡 YOUR STATEMENT CHECK:")
        if losses <= 3:
            print(f"   ✅ Confirmed: Only {losses} losing nights!")
            print(f"   Even with max 3-game parlays, you win {wins} nights")
        else:
            print(f"   ⚠️ Actually {losses} losing nights (more than 3)")
    
    print("\n" + "=" * 70)
    
    return True


if __name__ == "__main__":
    success = main()
    if not success:
        exit(1)
