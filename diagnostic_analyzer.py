"""
SCORING DIAGNOSTIC TOOL
=======================
Analyzes why games are scoring low and suggests adjustments

Usage:
    python diagnostic_analyzer.py
"""

import pandas as pd
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_collection.bball_ref_collector import BballRefCollector
from data_collection.game_results_collector import GameResultsCollector
from core.minimum_total_predictor import MinimumTotalPredictor
from decision.yes_no_decider import YesNoDecider


def analyze_factor_scores(predictions):
    """Analyze score distribution by factor"""
    
    # Collect scores by factor
    offensive_scores = []
    pace_scores = []
    form_scores = []
    buffer_scores = []
    defense_scores = []
    rest_scores = []
    total_scores = []
    
    for pred in predictions:
        factors = pred['factors']
        offensive_scores.append(factors['offensive_power']['score'])
        pace_scores.append(factors['pace']['pace_score'])
        form_scores.append(factors['form']['combined_score'])
        buffer_scores.append(factors['buffer']['score'])
        defense_scores.append(factors['defense']['score'])
        rest_scores.append(factors['rest']['combined_score'])
        total_scores.append(pred['total_score'])
    
    print("\n" + "=" * 70)
    print("FACTOR SCORE DISTRIBUTION")
    print("=" * 70)
    print()
    
    factors_data = {
        'Offensive Power (max 30)': offensive_scores,
        'Pace (max 25)': pace_scores,
        'Form (max 20)': form_scores,
        'Buffer (max 15)': buffer_scores,
        'Defense (max 10)': defense_scores,
        'Rest (max 10)': rest_scores
    }
    
    for factor_name, scores in factors_data.items():
        avg = sum(scores) / len(scores)
        max_score = max(scores)
        min_score = min(scores)
        zeros = scores.count(0)
        
        print(f"{factor_name}")
        print(f"  Average: {avg:.1f}")
        print(f"  Range: {min_score:.1f} to {max_score:.1f}")
        print(f"  Zero scores: {zeros}/{len(scores)} ({zeros/len(scores)*100:.1f}%)")
        print()
    
    print(f"TOTAL SCORES (max 110)")
    print(f"  Average: {sum(total_scores)/len(total_scores):.1f}")
    print(f"  Highest: {max(total_scores):.1f}")
    print(f"  Lowest: {min(total_scores):.1f}")
    print()
    
    return {
        'offensive': offensive_scores,
        'pace': pace_scores,
        'form': form_scores,
        'buffer': buffer_scores,
        'defense': defense_scores,
        'rest': rest_scores,
        'total': total_scores
    }


def identify_bottlenecks(score_data):
    """Identify which factors are holding back scores"""
    
    print("\n" + "=" * 70)
    print("BOTTLENECK ANALYSIS")
    print("=" * 70)
    print()
    
    # Calculate utilization rate (average / max possible)
    utilization = {
        'Offensive Power': (sum(score_data['offensive']) / len(score_data['offensive'])) / 30 * 100,
        'Pace': (sum(score_data['pace']) / len(score_data['pace'])) / 25 * 100,
        'Form': (sum(score_data['form']) / len(score_data['form'])) / 20 * 100,
        'Buffer': (sum(score_data['buffer']) / len(score_data['buffer'])) / 15 * 100,
        'Defense': (sum(score_data['defense']) / len(score_data['defense'])) / 10 * 100,
        'Rest': (sum(score_data['rest']) / len(score_data['rest'])) / 10 * 100
    }
    
    print("UTILIZATION RATES (what % of max points are being awarded):")
    print()
    
    sorted_util = sorted(utilization.items(), key=lambda x: x[1])
    
    for factor, rate in sorted_util:
        status = "TOO STRICT" if rate < 40 else "OK" if rate < 70 else "GOOD"
        print(f"  {factor}: {rate:.1f}% [{status}]")
    
    print()
    print("RECOMMENDATIONS:")
    print()
    
    for factor, rate in sorted_util:
        if rate < 40:
            print(f"⚠️  {factor} is TOO STRICT (only {rate:.1f}% utilization)")
            if factor == "Offensive Power":
                print(f"    → Lower ORtg thresholds (currently 116+ for elite)")
            elif factor == "Pace":
                print(f"    → Lower pace thresholds (currently 102+ for fast)")
            elif factor == "Form":
                print(f"    → Lower hot streak threshold (currently +5 PPG)")
            elif factor == "Buffer":
                print(f"    → Lower buffer requirements (currently 30+ for max)")
            elif factor == "Defense":
                print(f"    → Lower DRtg threshold (currently 115+ for weak)")
            elif factor == "Rest":
                print(f"    → This is fine, based on actual rest days")
            print()


def suggest_threshold_adjustments(predictions, actual_results):
    """Compare predicted vs actual to suggest adjustments"""
    
    print("\n" + "=" * 70)
    print("THRESHOLD TUNING SUGGESTIONS")
    print("=" * 70)
    print()
    
    # Find games that went over but scored low
    went_over = []
    for i, pred in enumerate(predictions):
        if i < len(actual_results):
            actual = actual_results.iloc[i]
            if actual['Total_Points'] > pred['minimum_total']:
                went_over.append({
                    'game': f"{pred['away_team']} @ {pred['home_team']}",
                    'score': pred['total_score'],
                    'confidence': pred['confidence'],
                    'factors': pred['factors']
                })
    
    if went_over:
        print(f"Found {len(went_over)} games that went OVER but scored low:")
        print()
        
        # Analyze these games
        low_scoring_overs = [g for g in went_over if g['score'] < 80]
        
        if low_scoring_overs:
            print(f"{len(low_scoring_overs)} games went OVER despite scoring < 80 points")
            print()
            print("Sample games we SHOULD have bet:")
            for game in low_scoring_overs[:5]:
                print(f"\n  {game['game']} - Score: {game['score']}/110 ({game['confidence']}%)")
                print(f"    Offense: {game['factors']['offensive_power']['score']}")
                print(f"    Pace: {game['factors']['pace']['pace_score']}")
                print(f"    Form: {game['factors']['form']['combined_score']}")
                print(f"    Buffer: {game['factors']['buffer']['score']}")
                print(f"    Defense: {game['factors']['defense']['score']}")
                print(f"    Rest: {game['factors']['rest']['combined_score']}")


def main():
    """Run diagnostic analysis"""
    
    print("\n" + "=" * 70)
    print("SCORING DIAGNOSTIC TOOL")
    print("=" * 70)
    print()
    
    # Load data
    print("Loading data...")
    
    if not os.path.exists('data/nba_team_stats_2025_2026.csv'):
        print("Error: Team stats not found. Run master_workflow.py first")
        return
    
    if not os.path.exists('data/nba_completed_games_2025_2026.csv'):
        print("Error: Completed games not found. Run master_workflow.py first")
        return
    
    team_stats = pd.read_csv('data/nba_team_stats_2025_2026.csv')
    completed_games = pd.read_csv('data/nba_completed_games_2025_2026.csv')
    
    print(f"Loaded {len(team_stats)} teams")
    print(f"Loaded {len(completed_games)} completed games")
    
    # Create predictor
    print("\nRunning predictions on all completed games...")
    predictor = MinimumTotalPredictor(team_stats, completed_games)
    
    # Analyze all completed games
    predictions = []
    for _, game in completed_games.iterrows():
        # Estimate minimum (actual - 15)
        estimated_min = game['Total_Points'] - 15
        
        try:
            prediction = predictor.predict_game(
                away_team=game['Visitor'],
                home_team=game['Home'],
                minimum_total=estimated_min,
                game_date=pd.to_datetime(game['Date'])
            )
            predictions.append(prediction)
        except:
            continue
    
    print(f"Analyzed {len(predictions)} games")
    
    # Run diagnostics
    score_data = analyze_factor_scores(predictions)
    identify_bottlenecks(score_data)
    suggest_threshold_adjustments(predictions, completed_games)
    
    print("\n" + "=" * 70)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 70)
    print()
    print("Next steps:")
    print("1. Review the bottleneck analysis above")
    print("2. Adjust thresholds in core/minimum_total_predictor.py")
    print("3. Run: python run_backtest.py")
    print("4. Repeat until you get acceptable win rate")
    print()


if __name__ == "__main__":
    main()
