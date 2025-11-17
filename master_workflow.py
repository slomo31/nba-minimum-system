"""
MASTER WORKFLOW - NBA MINIMUM SYSTEM
=====================================
ONE COMMAND to run entire system for today's games

Usage:
    python master_workflow.py

This will:
1. Collect team stats (2025-2026)
2. Fetch today's games and minimum alternates
3. Run predictions
4. Make YES/NO decisions
5. Export results
"""

import sys
import os

# Import all modules
from data_collection.bball_ref_collector import BballRefCollector
from data_collection.odds_minimum_fetcher import MinimumAlternateFetcher
from data_collection.game_results_collector import GameResultsCollector
from core.minimum_total_predictor import MinimumTotalPredictor
from decision.yes_no_decider import YesNoDecider
from output.csv_exporter import CSVExporter

import pandas as pd


def main():
    """Run complete workflow"""
    
    print("\n" + "=" * 70)
    print("NBA MINIMUM ALTERNATE SYSTEM - MASTER WORKFLOW")
    print("=" * 70)
    print()
    
    # Step 1: Collect team stats (if not already collected)
    print("STEP 1: Team Stats")
    print("-" * 70)
    
    if not os.path.exists('data/nba_team_stats_2025_2026.csv'):
        print("Collecting team stats from Basketball Reference...")
        collector = BballRefCollector()
        if not collector.run():
            print("[ERROR] Failed to collect team stats")
            return False
    else:
        print("[OK] Team stats already collected")
    
    # Load team stats
    team_stats = pd.read_csv('data/nba_team_stats_2025_2026.csv')
    print(f"[OK] Loaded {len(team_stats)} teams")
    
    # Step 2: Collect completed games (for form/rest analysis)
    print("\n" + "=" * 70)
    print("STEP 2: Completed Games")
    print("-" * 70)
    
    if not os.path.exists('data/nba_completed_games_2025_2026.csv'):
        print("Collecting completed games...")
        results_collector = GameResultsCollector()
        if not results_collector.run():
            print("[WARN] No completed games - using empty dataframe")
            completed_games = pd.DataFrame(columns=['Date', 'Visitor', 'Home', 'Visitor_PTS', 'Home_PTS', 'Total_Points'])
        else:
            # Successfully collected - now load it
            completed_games = pd.read_csv('data/nba_completed_games_2025_2026.csv')
    else:
        print("[OK] Completed games already collected")
        completed_games = pd.read_csv('data/nba_completed_games_2025_2026.csv')
    
    print(f"[OK] Loaded {len(completed_games)} completed games")
    
    # Step 3: Fetch today's games and minimum alternates
    print("\n" + "=" * 70)
    print("STEP 3: Today's Games & Minimum Alternates")
    print("-" * 70)
    
    fetcher = MinimumAlternateFetcher()
    if not fetcher.run():
        print("[ERROR] Failed to fetch games/minimums")
        return False
    
    # Load upcoming games
    upcoming = pd.read_csv('data/upcoming_games.csv')
    print(f"\n[OK] Found {len(upcoming)} games today")
    
    # Step 4: Run predictions
    print("\n" + "=" * 70)
    print("STEP 4: Running Predictions")
    print("-" * 70)
    
    predictor = MinimumTotalPredictor(team_stats, completed_games)
    predictions = predictor.predict_all_games(upcoming)
    
    print(f"[OK] Generated {len(predictions)} predictions")
    
    # Step 5: Make YES/NO decisions
    print("\n" + "=" * 70)
    print("STEP 5: Making YES/NO Decisions")
    print("-" * 70)
    
    decider = YesNoDecider()
    decisions_df = decider.process_all_predictions(predictions)
    
    # Print summary
    decider.print_summary(decisions_df)
    
    # Step 6: Export results
    print("\n" + "=" * 70)
    print("STEP 6: Exporting Results")
    print("-" * 70)
    
    exporter = CSVExporter()
    exporter.save_decisions(decisions_df)
    
    # Final summary
    print("\n" + "=" * 70)
    print("[SUCCESS] WORKFLOW COMPLETE!")
    print("=" * 70)
    
    yes_count = len(decisions_df[decisions_df['decision'] == 'YES'])
    print(f"\nReady to bet: {yes_count} YES decisions")
    print(f"Results saved to: output_archive/decisions/")
    print()
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)