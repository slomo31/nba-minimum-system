"""
MASTER WORKFLOW - MONTE CARLO v3.0 ENHANCED
=============================================
Fully enhanced with:
- Team-specific pace variance
- Slow-pace team flags
- Elite defense flags  
- Injury tracking
- Comprehensive risk analysis

Usage:
    python master_workflow_mc.py
"""

import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data_collection.bball_ref_collector import BballRefCollector
from data_collection.odds_minimum_fetcher import MinimumAlternateFetcher
from data_collection.game_results_collector import GameResultsCollector
from core.minimum_total_predictor import MinimumTotalPredictor
from core.monte_carlo_engine import MonteCarloEngineV3
from analyzers.rest_days_calculator import RestDaysCalculator

import pandas as pd


def get_mc_decision(mc_prob: float, original_conf: float) -> tuple:
    """Make final decision based on MC probability"""
    if mc_prob >= 92:
        decision, level = "STRONG_YES", "VERY HIGH"
    elif mc_prob >= 85:
        decision, level = "YES", "HIGH"
    elif mc_prob >= 78:
        decision, level = "MAYBE", "MEDIUM"
    elif mc_prob >= 70:
        decision, level = "LEAN_NO", "LOW"
    else:
        decision, level = "NO", "VERY LOW"
    
    # Flag disagreements
    flag = None
    if original_conf >= 80 and mc_prob < 78:
        flag = "⚠️ DOWNGRADED: MC found hidden risk (variance/pace/defense)"
    elif original_conf < 75 and mc_prob >= 85:
        flag = "📈 UPGRADED: MC shows safer than original estimate"
    
    return decision, level, flag


def print_mc_results(results: list):
    """Print comprehensive MC results"""
    
    strong_yes = [r for r in results if r['mc_decision'] == 'STRONG_YES']
    yes_bets = [r for r in results if r['mc_decision'] == 'YES']
    maybe_bets = [r for r in results if r['mc_decision'] == 'MAYBE']
    lean_no = [r for r in results if r['mc_decision'] == 'LEAN_NO']
    no_bets = [r for r in results if r['mc_decision'] == 'NO']
    
    print("\n" + "=" * 85)
    print("MONTE CARLO v3.0 ENHANCED PREDICTIONS")
    print("Simulations: 10,000 per game | Includes: Pace, Defense, Injury Analysis")
    print("=" * 85)
    
    # STRONG YES
    if strong_yes:
        print("\n🟢 STRONG YES (92%+ MC) - CORE PARLAY LEGS")
        print("-" * 85)
        for r in strong_yes:
            print(f"\n  {r['game']}")
            print(f"    Line: {r['minimum_total']} | Avg Sim: {r['avg_simulated_total']} | Range: {r['percentile_5']}-{r['percentile_95']}")
            print(f"    Original: {r['original_confidence']}% → MC: {r['mc_probability']}%")
            
            # Show flags
            flags = r.get('flags', {})
            if flags.get('slow_pace_game'):
                print(f"    🐢 Slow pace game")
            if flags.get('elite_defense_involved'):
                print(f"    🛡️ Elite defense involved")
            if flags.get('injury_concern'):
                print(f"    🏥 Injury concern")
            
            if r['risk_factors']:
                print(f"    Risks: {r['risk_factors'][0]}" if len(r['risk_factors']) > 0 else "")
    
    # YES
    if yes_bets:
        print("\n🟡 YES (85-92% MC) - SAFE FOR PARLAYS")
        print("-" * 85)
        for r in yes_bets:
            print(f"\n  {r['game']}")
            print(f"    Line: {r['minimum_total']} | MC: {r['mc_probability']}% | Original: {r['original_confidence']}%")
            if r.get('flag'):
                print(f"    {r['flag']}")
            if r['risk_factors']:
                print(f"    ⚠️ {r['risk_factors'][0]}" if len(r['risk_factors']) > 0 else "")
    
    # MAYBE
    if maybe_bets:
        print("\n⚠️ MAYBE (78-85% MC) - USE WITH CAUTION")
        print("-" * 85)
        for r in maybe_bets:
            print(f"\n  {r['game']} | MC: {r['mc_probability']}%")
            if r.get('flag'):
                print(f"    {r['flag']}")
            for risk in r['risk_factors'][:2]:
                print(f"    ⚠️ {risk}")
    
    # LEAN NO
    if lean_no:
        print("\n🔸 LEAN NO (70-78% MC) - HIGH RISK")
        print("-" * 85)
        for r in lean_no:
            print(f"  {r['game']} | MC: {r['mc_probability']}% | Original: {r['original_confidence']}%")
            if r.get('flag'):
                print(f"    {r['flag']}")
    
    # NO
    if no_bets:
        print("\n🔴 NO BET (<70% MC) - DO NOT BET")
        print("-" * 85)
        for r in no_bets:
            print(f"  {r['game']} | MC: {r['mc_probability']}%")
            if r['risk_factors']:
                print(f"    Why: {r['risk_factors'][0]}")


def generate_parlay_recommendations(results: list, mc_engine):
    """Generate parlay recommendations"""
    
    bettable = [r for r in results if r['mc_decision'] in ['STRONG_YES', 'YES']]
    
    if len(bettable) == 0:
        print("\n" + "=" * 85)
        print("⚠️ NO SAFE PARLAY OPTIONS TONIGHT")
        print("=" * 85)
        return None
    
    print("\n" + "=" * 85)
    print("🎯 PARLAY RECOMMENDATIONS")
    print("=" * 85)
    
    bettable.sort(key=lambda x: x['mc_probability'], reverse=True)
    
    # 2-leg (safest)
    if len(bettable) >= 2:
        legs = bettable[:2]
        probs = [g['mc_probability'] for g in legs]
        combined = mc_engine.calculate_parlay_probability(probs)
        
        print(f"\n✅ SAFEST PARLAY (2-leg) - Combined: {combined}%")
        for g in legs:
            flags = ""
            if g.get('flags', {}).get('slow_pace_game'):
                flags += " 🐢"
            if g.get('flags', {}).get('elite_defense_involved'):
                flags += " 🛡️"
            print(f"   • {g['game']} ({g['mc_probability']}%){flags}")
        
        status = "✓ RECOMMENDED" if combined >= 75 else "⚠️ BORDERLINE"
        print(f"   Status: {status}")
    
    # 3-leg
    if len(bettable) >= 3:
        legs = bettable[:3]
        probs = [g['mc_probability'] for g in legs]
        combined = mc_engine.calculate_parlay_probability(probs)
        
        print(f"\n📊 STANDARD PARLAY (3-leg) - Combined: {combined}%")
        for g in legs:
            print(f"   • {g['game']} ({g['mc_probability']}%)")
        
        status = "✓ ACCEPTABLE" if combined >= 70 else "⚠️ RISKY"
        print(f"   Status: {status}")
    
    # 4-leg (aggressive)
    if len(bettable) >= 4:
        legs = bettable[:4]
        probs = [g['mc_probability'] for g in legs]
        combined = mc_engine.calculate_parlay_probability(probs)
        
        print(f"\n⚠️ AGGRESSIVE PARLAY (4-leg) - Combined: {combined}%")
        for g in legs:
            print(f"   • {g['game']} ({g['mc_probability']}%)")
        
        status = "⚠️ HIGH RISK" if combined >= 60 else "✗ NOT RECOMMENDED"
        print(f"   Status: {status}")
    
    # Single best
    print(f"\n🎯 SINGLE SAFEST BET:")
    print(f"   {bettable[0]['game']}")
    print(f"   MC: {bettable[0]['mc_probability']}%")
    
    return bettable


def main():
    """Run complete MC v3.0 workflow"""
    
    print("\n" + "=" * 85)
    print("🏀 NBA MINIMUM SYSTEM - MONTE CARLO v3.0 ENHANCED")
    print(f"   Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("   Features: Pace Variance | Defense Flags | Injury Tracking")
    print("=" * 85)
    
    # Step 1: Team Stats
    print("\n📊 STEP 1: Loading Team Stats")
    print("-" * 85)
    
    if not os.path.exists('data/nba_team_stats_2025_2026.csv'):
        print("  Collecting team stats...")
        BballRefCollector().run()
    
    team_stats = pd.read_csv('data/nba_team_stats_2025_2026.csv')
    print(f"  ✓ Loaded {len(team_stats)} teams")
    
    # Step 2: Completed Games
    print("\n📊 STEP 2: Loading Completed Games")
    print("-" * 85)
    
    if not os.path.exists('data/nba_completed_games_2025_2026.csv'):
        GameResultsCollector().run()
    
    completed_games = pd.read_csv('data/nba_completed_games_2025_2026.csv')
    print(f"  ✓ Loaded {len(completed_games)} completed games")
    
    # Step 3: Today's Games
    print("\n📊 STEP 3: Fetching Today's Games")
    print("-" * 85)
    
    MinimumAlternateFetcher().run()
    upcoming = pd.read_csv('data/upcoming_games.csv')
    print(f"  ✓ Found {len(upcoming)} games today")
    
    if len(upcoming) == 0:
        print("\n⚠️ NO GAMES TODAY")
        return True
    
    # Step 4: Original Predictions
    print("\n📊 STEP 4: Running Original Predictions")
    print("-" * 85)
    
    predictor = MinimumTotalPredictor(team_stats, completed_games)
    predictions = predictor.predict_all_games(upcoming)
    print(f"  ✓ Generated {len(predictions)} predictions")
    
    # Step 5: Monte Carlo v3.0
    print("\n📊 STEP 5: Initializing Monte Carlo v3.0 Engine")
    print("-" * 85)
    
    mc_engine = MonteCarloEngineV3(
        team_stats, 
        completed_games, 
        n_simulations=10000,
        check_injuries=True  # Enable injury tracking
    )
    
    rest_calc = RestDaysCalculator(completed_games)
    
    # Step 6: Run Simulations
    print("\n📊 STEP 6: Running Monte Carlo Simulations (10,000 per game)")
    print("-" * 85)
    
    mc_results = []
    
    for pred in predictions:
        game = f"{pred['away_team']} @ {pred['home_team']}"
        print(f"  Simulating {game}...", end=" ", flush=True)
        
        # Get rest days
        away_rest = rest_calc.calculate_rest_days(pred['away_team'], pred['game_time'])
        home_rest = rest_calc.calculate_rest_days(pred['home_team'], pred['game_time'])
        
        # Run simulation
        mc_result = mc_engine.simulate_game(
            pred['away_team'],
            pred['home_team'],
            pred['minimum_total'],
            away_rest['rest_days'],
            home_rest['rest_days']
        )
        
        # Get decision
        mc_decision, mc_level, flag = get_mc_decision(
            mc_result['mc_probability'],
            pred['confidence']
        )
        
        # Combine results
        combined = {
            'game_time': pred['game_time'],
            'away_team': pred['away_team'],
            'home_team': pred['home_team'],
            'game': game,
            'minimum_total': pred['minimum_total'],
            'minimum_odds': pred['minimum_odds'],
            'original_confidence': pred['confidence'],
            'mc_probability': mc_result['mc_probability'],
            'mc_decision': mc_decision,
            'mc_level': mc_level,
            'avg_simulated_total': mc_result['avg_simulated_total'],
            'std_simulated_total': mc_result['std_simulated_total'],
            'percentile_5': mc_result['percentile_5'],
            'percentile_95': mc_result['percentile_95'],
            'risk_factors': mc_result['risk_factors'],
            'flags': mc_result['flags'],
            'injuries': mc_result.get('injuries', {}),
            'flag': flag
        }
        
        mc_results.append(combined)
        
        # Show flags inline
        flags_str = ""
        if mc_result['flags'].get('slow_pace_game'):
            flags_str += "🐢"
        if mc_result['flags'].get('elite_defense_involved'):
            flags_str += "🛡️"
        if mc_result['flags'].get('injury_concern'):
            flags_str += "🏥"
        if mc_result['flags'].get('high_variance_game'):
            flags_str += "🎲"
        
        print(f"MC: {mc_result['mc_probability']}% {flags_str}")
    
    # Print results
    print_mc_results(mc_results)
    
    # Parlay recommendations
    generate_parlay_recommendations(mc_results, mc_engine)
    
    # Export
    print("\n" + "=" * 85)
    print("📊 EXPORTING RESULTS")
    print("-" * 85)
    
    export_df = pd.DataFrame(mc_results)
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M')
    os.makedirs('output_archive/decisions', exist_ok=True)
    filename = f"output_archive/decisions/{timestamp}_mc_decisions.csv"
    export_df.to_csv(filename, index=False)
    print(f"  ✓ Saved to {filename}")
    
    # Summary
    strong_yes = len([r for r in mc_results if r['mc_decision'] == 'STRONG_YES'])
    yes_count = len([r for r in mc_results if r['mc_decision'] == 'YES'])
    maybe_count = len([r for r in mc_results if r['mc_decision'] == 'MAYBE'])
    
    print("\n" + "=" * 85)
    print("✅ WORKFLOW COMPLETE")
    print("=" * 85)
    print(f"\n  🟢 STRONG YES: {strong_yes} games")
    print(f"  🟡 YES: {yes_count} games")
    print(f"  ⚠️ MAYBE: {maybe_count} games")
    print(f"\n  Total bettable: {strong_yes + yes_count} games")
    print("=" * 85)
    
    return True


if __name__ == "__main__":
    main()