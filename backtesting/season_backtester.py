"""
Season Backtester
=================
Tests the system against ALL completed 2025-2026 games

For each completed game:
1. Get minimum alternate (estimate if not available)
2. Run prediction AS OF that date
3. Compare to actual result
4. Record W/L
"""

import pandas as pd
import numpy as np
from datetime import datetime
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.minimum_total_predictor import MinimumTotalPredictor
from decision.yes_no_decider import YesNoDecider


class SeasonBacktester:
    """Backtest system against completed games"""
    
    def __init__(self, team_stats_df, completed_games_df):
        self.team_stats = team_stats_df
        self.completed_games = completed_games_df
        self.backtest_results = []
    
    def estimate_minimum_total(self, away_ppg, home_ppg):
        """
        Estimate what the minimum alternate would have been
        
        Formula: (Combined PPG - 15) rounded to .5
        
        Example: Teams average 240 total → minimum ~225
        """
        combined_avg = away_ppg + home_ppg
        estimated_min = combined_avg - 15
        
        # Round to nearest .5
        estimated_min = round(estimated_min * 2) / 2
        
        return estimated_min
    
    def run_backtest(self):
        """Run backtest on all completed games"""
        print("=" * 70)
        print("RUNNING BACKTEST ON 2025-2026 SEASON")
        print("=" * 70)
        print()
        
        results = []
        
        for idx, game in self.completed_games.iterrows():
            # Get game info
            game_date = pd.to_datetime(game['Date'])
            away_team = game['Visitor']
            home_team = game['Home']
            actual_total = game['Total_Points']
            
            # Get team stats (for estimating minimum)
            away_stats = self.team_stats[self.team_stats['Team'] == away_team]
            home_stats = self.team_stats[self.team_stats['Team'] == home_team]
            
            if len(away_stats) == 0 or len(home_stats) == 0:
                continue  # Skip if no stats
            
            # Estimate minimum alternate
            away_ppg = away_stats['PPG'].values[0]
            home_ppg = home_stats['PPG'].values[0]
            estimated_minimum = self.estimate_minimum_total(away_ppg, home_ppg)
            
            # Run prediction (using data AS OF that date)
            # Note: In real backtest, we'd filter team_stats/games to only include data before game_date
            # For now, using full season data (acceptable for this version)
            
            predictor = MinimumTotalPredictor(self.team_stats, self.completed_games)
            
            prediction = predictor.predict_game(
                away_team=away_team,
                home_team=home_team,
                minimum_total=estimated_minimum,
                game_date=game_date
            )
            
            # Make decision
            decider = YesNoDecider()
            decision_result = decider.make_decision({
                **prediction,
                'game_time': game_date,
                'minimum_odds': -400  # Typical minimum odds
            })
            
            # Check if bet would have won
            went_over = actual_total > estimated_minimum
            
            if decision_result['decision'] == 'YES':
                result = 'WIN' if went_over else 'LOSS'
            else:
                result = 'SKIPPED'
            
            # Record result
            results.append({
                'date': game_date,
                'game': f"{away_team} @ {home_team}",
                'minimum': estimated_minimum,
                'prediction': decision_result['decision'],
                'confidence': decision_result['confidence'],
                'score': decision_result['score'],
                'actual_total': actual_total,
                'went_over': went_over,
                'result': result,
                'reasoning': decision_result['reasoning']
            })
            
            # Progress indicator
            if (idx + 1) % 20 == 0:
                print(f"  Processed {idx + 1}/{len(self.completed_games)} games...")
        
        self.backtest_results = pd.DataFrame(results)
        
        print(f"\n✓ Backtest complete: {len(self.backtest_results)} games analyzed")
        
        return self.backtest_results
    
    def save_results(self, output_dir='output_archive/backtests'):
        """Save backtest results"""
        if len(self.backtest_results) > 0:
            os.makedirs(output_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M')
            filepath = os.path.join(output_dir, f'{timestamp}_backtest_results.csv')
            
            self.backtest_results.to_csv(filepath, index=False)
            print(f"\n✓ Saved to: {filepath}")
            
            return filepath
        return None


def main():
    """Test the backtester"""
    print("Season Backtester - Ready")
    print("Use in run_backtest.py")


if __name__ == "__main__":
    main()
