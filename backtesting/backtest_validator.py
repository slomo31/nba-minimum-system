"""
Backtest Validator
==================
Analyzes backtest results and validates against configured threshold
"""

import pandas as pd
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.season_config import CONFIDENCE_THRESHOLD_YES


class BacktestValidator:
    """Validate backtest performance"""
    
    def __init__(self, backtest_results_df):
        self.results = backtest_results_df
        self.threshold = CONFIDENCE_THRESHOLD_YES
    
    def calculate_metrics(self):
        """Calculate key performance metrics"""
        # Filter to YES predictions only
        yes_bets = self.results[self.results['prediction'] == 'YES']
        
        if len(yes_bets) == 0:
            return {
                'total_games': len(self.results),
                'yes_predictions': 0,
                'no_predictions': len(self.results),
                'wins': 0,
                'losses': 0,
                'win_rate': 0,
                'status': 'NO BETS MADE'
            }
        
        # Calculate W/L
        wins = len(yes_bets[yes_bets['result'] == 'WIN'])
        losses = len(yes_bets[yes_bets['result'] == 'LOSS'])
        win_rate = (wins / len(yes_bets) * 100) if len(yes_bets) > 0 else 0
        
        # Validate against configured threshold
        validated = win_rate >= self.threshold
        
        metrics = {
            'total_games': len(self.results),
            'yes_predictions': len(yes_bets),
            'no_predictions': len(self.results) - len(yes_bets),
            'wins': wins,
            'losses': losses,
            'win_rate': round(win_rate, 1),
            'status': 'âœ… VALIDATED' if validated else 'âŒ BELOW TARGET',
            'validated': validated
        }
        
        return metrics
    
    def analyze_by_confidence(self):
        """Break down performance by confidence tier"""
        yes_bets = self.results[self.results['prediction'] == 'YES']
        
        tiers = []
        
        # 90-100%
        tier_90 = yes_bets[yes_bets['confidence'] >= 90]
        if len(tier_90) > 0:
            wins = len(tier_90[tier_90['result'] == 'WIN'])
            tiers.append({
                'tier': '90-100%',
                'games': len(tier_90),
                'wins': wins,
                'losses': len(tier_90) - wins,
                'win_rate': round(wins / len(tier_90) * 100, 1)
            })
        
        # 80-89%
        tier_80 = yes_bets[(yes_bets['confidence'] >= 80) & (yes_bets['confidence'] < 90)]
        if len(tier_80) > 0:
            wins = len(tier_80[tier_80['result'] == 'WIN'])
            tiers.append({
                'tier': '80-89%',
                'games': len(tier_80),
                'wins': wins,
                'losses': len(tier_80) - wins,
                'win_rate': round(wins / len(tier_80) * 100, 1)
            })
        
        # 75-79%
        tier_75 = yes_bets[(yes_bets['confidence'] >= 75) & (yes_bets['confidence'] < 80)]
        if len(tier_75) > 0:
            wins = len(tier_75[tier_75['result'] == 'WIN'])
            tiers.append({
                'tier': '75-79%',
                'games': len(tier_75),
                'wins': wins,
                'losses': len(tier_75) - wins,
                'win_rate': round(wins / len(tier_75) * 100, 1)
            })
        
        return pd.DataFrame(tiers)
    
    def identify_failures(self):
        """Analyze losing bets to find patterns"""
        yes_bets = self.results[self.results['prediction'] == 'YES']
        losses = yes_bets[yes_bets['result'] == 'LOSS']
        
        return losses[['date', 'game', 'minimum', 'confidence', 'actual_total', 'reasoning']]
    
    def print_report(self):
        """Print comprehensive validation report"""
        metrics = self.calculate_metrics()
        
        print("\n" + "=" * 70)
        print("BACKTEST VALIDATION REPORT")
        print("=" * 70)
        
        print(f"\nTotal games analyzed: {metrics['total_games']}")
        print(f"  YES predictions: {metrics['yes_predictions']}")
        print(f"  NO predictions: {metrics['no_predictions']}")
        
        if metrics['yes_predictions'] > 0:
            print(f"\nYES PREDICTIONS PERFORMANCE:")
            print(f"  Wins: {metrics['wins']} âœ…")
            print(f"  Losses: {metrics['losses']} âŒ")
            print(f"  Win rate: {metrics['win_rate']}%")
            print(f"\n  Status: {metrics['status']}")
            
            if metrics['validated']:
                print(f"\n  🎉 SYSTEM VALIDATED - Exceeds {self.threshold}% threshold!")
            else:
                print(f"\n  ⚠️ System needs adjustment - below {self.threshold}% target")
            
            # Confidence tiers
            print(f"\n" + "-" * 70)
            print("PERFORMANCE BY CONFIDENCE LEVEL:")
            print("-" * 70)
            
            tiers_df = self.analyze_by_confidence()
            print(tiers_df.to_string(index=False))
            
            # Failures
            failures = self.identify_failures()
            if len(failures) > 0:
                print(f"\n" + "-" * 70)
                print(f"DETAILED FAILURES ({len(failures)} losses):")
                print("-" * 70)
                for _, loss in failures.iterrows():
                    print(f"\n{loss['date'].strftime('%Y-%m-%d')}: {loss['game']}")
                    print(f"  Minimum: {loss['minimum']} | Actual: {loss['actual_total']}")
                    print(f"  Confidence: {loss['confidence']}%")
                    print(f"  Reasoning: {loss['reasoning']}")
        
        print("\n" + "=" * 70)
        
        return metrics


def main():
    """Test the validator"""
    print("Backtest Validator - Ready")


if __name__ == "__main__":
    main()