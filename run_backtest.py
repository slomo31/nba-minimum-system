"""
BACKTEST RUNNER
===============
ONE COMMAND to validate system against completed 2025-2026 games

Usage:
    python run_backtest.py

This will:
1. Load completed games
2. Run predictions on each game (as if betting that day)
3. Compare to actual results
4. Calculate accuracy
5. Validate against configured threshold
"""

import sys
import os
import pandas as pd

from config.season_config import CONFIDENCE_THRESHOLD_YES

from backtesting.season_backtester import SeasonBacktester
from backtesting.backtest_validator import BacktestValidator
from output.csv_exporter import CSVExporter


def main():
    """Run backtest workflow"""
    
    print("\n" + "=" * 70)
    print("ðŸ€ NBA MINIMUM SYSTEM - BACKTEST VALIDATOR")
    print("=" * 70)
    print()
    
    # Load data
    print("Loading data...")
    
    if not os.path.exists('data/nba_team_stats_2025_2026.csv'):
        print("âŒ Team stats not found. Run master_workflow.py first")
        return False
    
    if not os.path.exists('data/nba_completed_games_2025_2026.csv'):
        print("âŒ Completed games not found. Run master_workflow.py first")
        return False
    
    team_stats = pd.read_csv('data/nba_team_stats_2025_2026.csv')
    completed_games = pd.read_csv('data/nba_completed_games_2025_2026.csv')
    
    print(f"âœ“ Loaded {len(team_stats)} teams")
    print(f"âœ“ Loaded {len(completed_games)} completed games")
    
    # Run backtest
    print("\n" + "=" * 70)
    print("RUNNING BACKTEST...")
    print("=" * 70)
    
    backtester = SeasonBacktester(team_stats, completed_games)
    results = backtester.run_backtest()
    
    # Validate results
    print("\n" + "=" * 70)
    print("VALIDATING RESULTS...")
    print("=" * 70)
    
    validator = BacktestValidator(results)
    metrics = validator.print_report()
    
    # Save results
    print("\n" + "=" * 70)
    print("SAVING RESULTS...")
    print("=" * 70)
    
    exporter = CSVExporter()
    exporter.save_backtest(results)
    
    # Final summary
    print("\n" + "=" * 70)
    
    if metrics.get('validated', False):
        print("âœ… SYSTEM VALIDATED!")
        print("=" * 70)
        print(f"\nWin rate: {metrics['win_rate']}% (exceeds {CONFIDENCE_THRESHOLD_YES}% threshold)")
        print("System is ready for live betting!")
    else:
        print("âš ï¸ SYSTEM NEEDS ADJUSTMENT")
        print("=" * 70)
        print(f"\nWin rate: {metrics['win_rate']}% (below {CONFIDENCE_THRESHOLD_YES}% target)")
        print("Review failures and adjust scoring factors")
    
    print()
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)