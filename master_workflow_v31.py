"""
Master Workflow - Monte Carlo V3.1
===================================
Daily workflow using the upgraded V3.1 engine with:
1. Matchup-based expected scoring (ORtg × OppDRtg)
2. Cumulative flag penalty system
3. Floor safety checks
"""

import pandas as pd
import os
import sys
from datetime import datetime

# Ensure imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def run_workflow():
    """Run the complete V3.1 workflow"""
    
    print("\n" + "=" * 85)
    print("NBA MINIMUM ALTERNATE SYSTEM - MONTE CARLO V3.1")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 85)
    
    # ==========================================
    # STEP 1: Load Team Stats
    # ==========================================
    print("\nSTEP 1: Team Stats")
    print("-" * 85)
    
    if os.path.exists('data/nba_team_stats_2025_2026.csv'):
        team_stats = pd.read_csv('data/nba_team_stats_2025_2026.csv')
        print(f"[OK] Loaded {len(team_stats)} teams")
    else:
        print("[ERROR] Team stats not found!")
        print("Run: python data_collection/bball_ref_collector.py")
        return
    
    # ==========================================
    # STEP 2: Load Completed Games
    # ==========================================
    print("\nSTEP 2: Completed Games")
    print("-" * 85)
    
    if os.path.exists('data/nba_completed_games_2025_2026.csv'):
        completed_games = pd.read_csv('data/nba_completed_games_2025_2026.csv')
        print(f"[OK] Loaded {len(completed_games)} completed games")
    else:
        print("[WARNING] No completed games found - using empty DataFrame")
        completed_games = pd.DataFrame()
    
    # ==========================================
    # STEP 3: Fetch Today's Games
    # ==========================================
    print("\nSTEP 3: Today's Games & Minimum Alternates")
    print("-" * 85)
    
    try:
        from odds_minimum_fetcher import fetch_minimum_alternates
        upcoming = fetch_minimum_alternates()
        
        if upcoming is None or len(upcoming) == 0:
            print("[WARNING] No games found for today")
            return
        
        print(f"[OK] Found {len(upcoming)} games today")
    except Exception as e:
        print(f"[ERROR] Failed to fetch odds: {e}")
        return
    
    # ==========================================
    # STEP 4: Initialize V3.1 Engine
    # ==========================================
    print("\nSTEP 4: Initializing Monte Carlo V3.1 Engine")
    print("-" * 85)
    
    try:
        from monte_carlo_engine_v3_1 import MonteCarloEngineV31
        mc_engine = MonteCarloEngineV31(
            team_stats, 
            completed_games, 
            n_simulations=10000,
            check_injuries=True
        )
    except ImportError:
        print("[ERROR] V3.1 engine not found!")
        print("Make sure monte_carlo_engine_v3_1.py is in the project directory")
        return
    
    # ==========================================
    # STEP 5: Run Simulations
    # ==========================================
    print("\nSTEP 5: Running Monte Carlo V3.1 Simulations (10,000 per game)")
    print("-" * 85)
    
    results = []
    
    for _, game in upcoming.iterrows():
        away_team = game['away_team']
        home_team = game['home_team']
        minimum_total = game['minimum_total']
        
        print(f"  Simulating {away_team} @ {home_team}...", end=" ")
        
        result = mc_engine.simulate_game(
            away_team=away_team,
            home_team=home_team,
            minimum_line=minimum_total
        )
        
        # Add odds data
        result['odds'] = game.get('odds', -450)
        result['vegas_total'] = game.get('vegas_total', minimum_total + 15)
        
        print(f"MC: {result['mc_probability']}% | Flags: {result['flag_count']} | {result['mc_decision']}")
        
        results.append(result)
    
    # ==========================================
    # STEP 6: Print Results
    # ==========================================
    
    print_v31_results(results, mc_engine)
    
    # ==========================================
    # STEP 7: Save Results
    # ==========================================
    print("\nSTEP 7: Saving Results")
    print("-" * 85)
    
    # Create output directory
    os.makedirs('output_archive/decisions', exist_ok=True)
    
    # Save to CSV
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M')
    output_file = f"output_archive/decisions/{timestamp}_mc_v31_decisions.csv"
    
    df = pd.DataFrame(results)
    df.to_csv(output_file, index=False)
    print(f"[OK] Saved to {output_file}")
    
    print("\n" + "=" * 85)
    print("[SUCCESS] V3.1 WORKFLOW COMPLETE!")
    print("=" * 85)
    
    return results


def print_v31_results(results: list, mc_engine):
    """Print V3.1 results with flag analysis"""
    
    # Categorize by decision
    strong_yes = [r for r in results if r['mc_decision'] == 'STRONG_YES']
    yes_bets = [r for r in results if r['mc_decision'] == 'YES']
    maybe_bets = [r for r in results if r['mc_decision'] == 'MAYBE']
    skip = [r for r in results if r['mc_decision'] in ['LEAN_NO', 'NO']]
    
    print("\n" + "=" * 85)
    print("MONTE CARLO V3.1 PREDICTIONS")
    print("Features: Matchup-Based Scoring | Cumulative Flag Penalties | Floor Safety")
    print("=" * 85)
    
    # STRONG YES
    if strong_yes:
        print("\n🟢 STRONG YES (92%+ MC, 0 flags, floor safe)")
        print("-" * 85)
        for r in strong_yes:
            print(f"\n  {r['game']}")
            print(f"    Line: {r['minimum_line']} | Expected: {r['total_expected']:.1f}")
            print(f"    Matchup: {r['away_team']} ({r['away_ortg']:.1f} ORtg) vs {r['home_team']} ({r['home_drtg']:.1f} DRtg)")
            print(f"    MC: {r['mc_probability']}% | Avg Sim: {r['avg_simulated_total']} | Range: {r['percentile_10']}-{r['percentile_90']}")
            print(f"    Flags: {r['flag_count']} | Floor Safe: {'✓' if r['floor_safe'] else '✗'}")
    
    # YES
    if yes_bets:
        print("\n🟡 YES (88%+ MC or 96%+ with 1 flag)")
        print("-" * 85)
        for r in yes_bets:
            print(f"\n  {r['game']}")
            print(f"    Line: {r['minimum_line']} | Expected: {r['total_expected']:.1f}")
            print(f"    MC: {r['mc_probability']}% | Flags: {r['flag_count']} | Floor Safe: {'✓' if r['floor_safe'] else '✗'}")
            if r['risk_flags']:
                for flag in r['risk_flags'][:2]:
                    print(f"    ⚠️ {flag}")
    
    # MAYBE (downgraded due to flags)
    if maybe_bets:
        print("\n⚠️ MAYBE (High probability but flagged)")
        print("-" * 85)
        for r in maybe_bets:
            print(f"\n  {r['game']} | MC: {r['mc_probability']}%")
            print(f"    Reason: {r['confidence_level']}")
            print(f"    Flags ({r['flag_count']}):")
            for flag in r['risk_flags'][:3]:
                print(f"      - {flag}")
    
    # SKIP
    if skip:
        print("\n🔴 SKIP")
        print("-" * 85)
        for r in skip[:5]:
            print(f"  {r['game']} | MC: {r['mc_probability']}% | {r['confidence_level']}")
        if len(skip) > 5:
            print(f"  ... and {len(skip) - 5} more")
    
    # Parlay recommendations
    bettable = strong_yes + yes_bets
    
    if len(bettable) >= 2:
        print("\n" + "=" * 85)
        print("🎯 PARLAY RECOMMENDATIONS")
        print("=" * 85)
        
        bettable.sort(key=lambda x: x['mc_probability'], reverse=True)
        
        # 2-leg parlay
        if len(bettable) >= 2:
            legs = bettable[:2]
            probs = [g['mc_probability'] for g in legs]
            combined = mc_engine.calculate_parlay_probability(probs)
            
            print(f"\n✅ 2-LEG PARLAY (Combined: {combined}%)")
            for g in legs:
                flag_icon = "🚩" if g['flag_count'] > 0 else "✓"
                print(f"   {flag_icon} {g['game']} ({g['mc_probability']}%) - {g['flag_count']} flags")
        
        # 3-leg only if all are clean (0 flags)
        clean = [g for g in bettable if g['flag_count'] == 0]
        if len(clean) >= 3:
            legs = clean[:3]
            probs = [g['mc_probability'] for g in legs]
            combined = mc_engine.calculate_parlay_probability(probs)
            
            print(f"\n📊 3-LEG CLEAN PARLAY (Combined: {combined}%)")
            for g in legs:
                print(f"   ✓ {g['game']} ({g['mc_probability']}%) - 0 flags")
    elif len(bettable) == 1:
        print("\n" + "=" * 85)
        print("🎯 SINGLE BET RECOMMENDED")
        print("=" * 85)
        g = bettable[0]
        print(f"   {g['game']} ({g['mc_probability']}%)")
    else:
        print("\n" + "=" * 85)
        print("⚠️ NO SAFE BETS TODAY")
        print("=" * 85)
        print("   V3.1 flag system found too many risks in today's games.")
        print("   Consider sitting this one out.")
    
    # Summary
    print("\n" + "=" * 85)
    print("📊 SUMMARY")
    print("=" * 85)
    print(f"""
   🟢 STRONG YES: {len(strong_yes)} games
   🟡 YES: {len(yes_bets)} games
   ⚠️ MAYBE (flagged): {len(maybe_bets)} games
   🔴 SKIP: {len(skip)} games
   
   Total bettable: {len(bettable)} games
   
   V3.1 Features Active:
   ✓ Matchup-based scoring (ORtg × OppDRtg)
   ✓ Cumulative flag penalties
   ✓ Floor safety check (10th percentile)
    """)


if __name__ == "__main__":
    run_workflow()
