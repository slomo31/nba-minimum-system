"""
HISTORICAL PARLAY ANALYZER - 2024-2025 SEASON
===============================================
Analyzes historical backtest results grouped by NIGHT for parlay performance

IMPORTANT: Run run_historical_backtest.py FIRST

Usage:
    python analyze_historical_parlays.py

This will:
1. Load historical backtest results
2. Group YES bets by date (night)
3. Treat each night as one parlay
4. Show performance by parlay size
5. Calculate win rates and profitability
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime
from collections import defaultdict


class HistoricalParlayAnalyzer:
    """Analyze historical bets grouped by night (parlay style)"""
    
    def __init__(self):
        self.backtest_df = None
        self.parlay_nights = []
    
    def load_latest_backtest(self):
        """Load most recent historical backtest"""
        backtest_dir = 'output_archive/historical_backtests'
        
        if not os.path.exists(backtest_dir):
            print("❌ No historical backtests found!")
            print("   Run: python run_historical_backtest.py first")
            return False
        
        # Get all backtest files
        files = [f for f in os.listdir(backtest_dir) if f.endswith('.csv')]
        
        if not files:
            print("❌ No backtest CSV files found!")
            return False
        
        # Get most recent
        latest_file = max(files)
        filepath = os.path.join(backtest_dir, latest_file)
        
        print(f"\n📂 Loading: {latest_file}")
        self.backtest_df = pd.read_csv(filepath)
        
        print(f"✅ Loaded {len(self.backtest_df)} games")
        
        return True
    
    def analyze_parlay_performance(self):
        """Group YES bets by night and analyze as parlays"""
        print("\n" + "="*70)
        print("GROUPING BETS BY NIGHT (PARLAY ANALYSIS)")
        print("="*70)
        
        # Filter to YES predictions only
        yes_bets = self.backtest_df[self.backtest_df['prediction'] == 'YES'].copy()
        
        if len(yes_bets) == 0:
            print("\n❌ No YES bets found in backtest!")
            return False
        
        print(f"\nTotal YES bets: {len(yes_bets)}")
        
        # Convert date to date-only
        yes_bets['date'] = pd.to_datetime(yes_bets['date'])
        yes_bets['date_only'] = yes_bets['date'].dt.date
        
        # Group by date
        by_date = yes_bets.groupby('date_only')
        
        print(f"Total betting nights: {len(by_date)}")
        
        # Analyze each night
        for date, games in by_date:
            total_games = len(games)
            wins = len(games[games['result'] == 'WIN'])
            losses = len(games[games['result'] == 'LOSS'])
            
            # Parlay wins only if ALL games win
            parlay_result = 'WIN' if losses == 0 else 'LOSS'
            
            # Calculate average confidence
            avg_confidence = games['confidence'].mean()
            
            # Get game details
            games_list = []
            for _, game in games.iterrows():
                games_list.append({
                    'game': game['game'],
                    'minimum': game['minimum'],
                    'actual': game['actual_total'],
                    'confidence': game['confidence'],
                    'result': game['result']
                })
            
            self.parlay_nights.append({
                'date': date,
                'num_games': total_games,
                'wins': wins,
                'losses': losses,
                'parlay_result': parlay_result,
                'avg_confidence': round(avg_confidence, 1),
                'games': games_list
            })
        
        return True
    
    def print_detailed_report(self):
        """Print comprehensive parlay analysis"""
        print("\n" + "="*70)
        print("HISTORICAL PARLAY PERFORMANCE - 2024-2025 SEASON")
        print("="*70)
        
        parlay_df = pd.DataFrame(self.parlay_nights)
        
        # Overall stats
        total_nights = len(parlay_df)
        parlay_wins = len(parlay_df[parlay_df['parlay_result'] == 'WIN'])
        parlay_losses = total_nights - parlay_wins
        parlay_win_rate = (parlay_wins / total_nights * 100) if total_nights > 0 else 0
        
        print(f"\n📊 OVERALL PARLAY STATISTICS:")
        print(f"   Total betting nights: {total_nights}")
        print(f"   Perfect nights (all won): {parlay_wins} ✅")
        print(f"   Losing nights (≥1 loss): {parlay_losses} ❌")
        print(f"   PARLAY WIN RATE: {parlay_win_rate:.1f}%")
        
        # Breakdown by parlay size
        print(f"\n" + "="*70)
        print("PERFORMANCE BY PARLAY SIZE")
        print("="*70)
        
        size_stats = {}
        for num_games in sorted(parlay_df['num_games'].unique()):
            subset = parlay_df[parlay_df['num_games'] == num_games]
            subset_wins = len(subset[subset['parlay_result'] == 'WIN'])
            subset_total = len(subset)
            subset_win_rate = (subset_wins / subset_total * 100) if subset_total > 0 else 0
            
            size_stats[num_games] = {
                'nights': subset_total,
                'wins': subset_wins,
                'losses': subset_total - subset_wins,
                'win_rate': subset_win_rate
            }
            
            print(f"\n{num_games}-Game Parlays:")
            print(f"   Nights: {subset_total}")
            print(f"   Wins: {subset_wins}")
            print(f"   Losses: {subset_total - subset_wins}")
            print(f"   Win Rate: {subset_win_rate:.1f}%")
        
        # Show worst losing nights
        print(f"\n" + "="*70)
        print("WORST LOSING NIGHTS")
        print("="*70)
        
        losing_nights = parlay_df[parlay_df['parlay_result'] == 'LOSS'].copy()
        losing_nights = losing_nights.sort_values('losses', ascending=False).head(5)
        
        for _, night in losing_nights.iterrows():
            print(f"\n{night['date']}: {night['num_games']}-game parlay")
            print(f"   Result: {night['wins']}W-{night['losses']}L (LOST)")
            for game in night['games']:
                result_icon = "✅" if game['result'] == 'WIN' else "❌"
                print(f"   {result_icon} {game['game']} - {game['minimum']} → {game['actual']}")
        
        # Best winning streaks
        print(f"\n" + "="*70)
        print("LONGEST WIN STREAK")
        print("="*70)
        
        current_streak = 0
        max_streak = 0
        
        for _, night in parlay_df.iterrows():
            if night['parlay_result'] == 'WIN':
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:
                current_streak = 0
        
        print(f"\nLongest winning streak: {max_streak} nights")
        
        # Profitability analysis
        print(f"\n" + "="*70)
        print("PROFITABILITY ANALYSIS")
        print("="*70)
        
        # Calculate expected value for each parlay size
        typical_odds = {
            1: 0,  # No parlay, just individual bet
            2: 260,  # +260
            3: 600,  # +600
            4: 1200  # +1200
        }
        
        print("\nAssuming typical parlay odds:")
        
        for size, stats in size_stats.items():
            if size in typical_odds:
                win_rate = stats['win_rate'] / 100
                odds = typical_odds[size]
                
                if size == 1:
                    # Individual bets at -450
                    ev = (win_rate * 22.22) - ((1 - win_rate) * 100)
                    print(f"\n{size}-Game (Individual at -450):")
                else:
                    # Parlay
                    payout = odds
                    ev = (win_rate * payout) - ((1 - win_rate) * 100)
                    print(f"\n{size}-Game Parlay (+{odds}):")
                
                print(f"   Win Rate: {stats['win_rate']:.1f}%")
                print(f"   Expected Value: ${ev:+.2f} per $100")
                
                if ev > 0:
                    print(f"   Status: ✅ PROFITABLE")
                else:
                    print(f"   Status: ❌ NOT PROFITABLE")
        
        return size_stats
    
    def save_results(self):
        """Save parlay analysis results"""
        output_dir = 'output_archive/historical_parlays'
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M')
        filepath = os.path.join(output_dir, f'parlay_analysis_{timestamp}.csv')
        
        parlay_df = pd.DataFrame(self.parlay_nights)
        
        # Flatten games list for CSV
        rows = []
        for _, night in parlay_df.iterrows():
            for game in night['games']:
                rows.append({
                    'date': night['date'],
                    'parlay_size': night['num_games'],
                    'parlay_result': night['parlay_result'],
                    'game': game['game'],
                    'minimum': game['minimum'],
                    'actual': game['actual'],
                    'confidence': game['confidence'],
                    'game_result': game['result']
                })
        
        flat_df = pd.DataFrame(rows)
        flat_df.to_csv(filepath, index=False)
        
        print(f"\n💾 Saved to: {filepath}")
        
        return filepath


def main():
    """Run historical parlay analysis"""
    
    print("\n" + "="*70)
    print("🎲 HISTORICAL PARLAY ANALYZER - 2024-2025 SEASON")
    print("="*70)
    print("\nThis analyzes historical bets grouped by NIGHT")
    print("Each night's YES bets are treated as ONE PARLAY")
    
    # Initialize analyzer
    analyzer = HistoricalParlayAnalyzer()
    
    # Load backtest
    if not analyzer.load_latest_backtest():
        return False
    
    # Analyze parlays
    if not analyzer.analyze_parlay_performance():
        return False
    
    # Print detailed report
    analyzer.print_detailed_report()
    
    # Save results
    analyzer.save_results()
    
    print("\n" + "="*70)
    print("✅ PARLAY ANALYSIS COMPLETE!")
    print("="*70)
    print("\nNext steps:")
    print("1. Run: python generate_historical_pdf.py")
    print("   (This will create a PDF report of the results)")
    print()
    
    return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)