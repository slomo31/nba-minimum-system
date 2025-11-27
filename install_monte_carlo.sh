#!/bin/bash
# Monte Carlo Installation Script
# Run this from your nba_minimun_system folder

echo "Installing Monte Carlo Engine..."

# Create core directory
mkdir -p core

# Create monte_carlo_engine.py
cat > core/monte_carlo_engine.py << 'MCEOF'
"""
Monte Carlo Simulation Engine
==============================
Simulates games 10,000 times to get TRUE probability of hitting minimum total.
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple
import warnings
warnings.filterwarnings('ignore')


class MonteCarloEngine:
    """Monte Carlo simulation for NBA game totals"""
    
    def __init__(self, team_stats_df: pd.DataFrame, completed_games_df: pd.DataFrame, n_simulations: int = 10000):
        self.team_stats = team_stats_df
        self.completed_games = completed_games_df
        self.n_simulations = n_simulations
        self.team_profiles = self._build_team_profiles()
        self.league_avg_ppg = team_stats_df['PPG'].mean()
        self.league_avg_pace = team_stats_df['Pace'].mean()
        
    def _build_team_profiles(self) -> Dict:
        """Build variance profiles for each team"""
        profiles = {}
        
        for team in self.team_stats['Team'].unique():
            team_games = self.completed_games[
                (self.completed_games['Visitor'] == team) | 
                (self.completed_games['Home'] == team)
            ].copy()
            
            if len(team_games) == 0:
                team_row = self.team_stats[self.team_stats['Team'] == team]
                if len(team_row) > 0:
                    ppg = team_row['PPG'].values[0]
                    profiles[team] = {
                        'mean_ppg': ppg, 'std_ppg': 10.0,
                        'min_ppg': ppg - 25, 'max_ppg': ppg + 25,
                        'games_played': 0, 'variance_reliable': False
                    }
                continue
            
            scores = []
            for _, game in team_games.iterrows():
                if game['Visitor'] == team:
                    scores.append(game['Visitor_PTS'])
                else:
                    scores.append(game['Home_PTS'])
            
            scores = np.array(scores)
            mean_ppg = np.mean(scores)
            std_ppg = np.std(scores) if len(scores) > 1 else 10.0
            std_ppg = max(std_ppg, 6.0)
            
            profiles[team] = {
                'mean_ppg': mean_ppg, 'std_ppg': std_ppg,
                'min_ppg': np.min(scores), 'max_ppg': np.max(scores),
                'games_played': len(scores),
                'variance_reliable': len(scores) >= 5
            }
        
        return profiles
    
    def get_team_profile(self, team_name: str) -> Dict:
        if team_name in self.team_profiles:
            return self.team_profiles[team_name]
        return {
            'mean_ppg': self.league_avg_ppg, 'std_ppg': 10.0,
            'min_ppg': 90, 'max_ppg': 140,
            'games_played': 0, 'variance_reliable': False
        }
    
    def simulate_team_score(self, team_profile: Dict, pace_factor: float = 1.0, 
                           fatigue_factor: float = 1.0, blowout_adjustment: float = 0.0) -> float:
        base_score = np.random.normal(team_profile['mean_ppg'], team_profile['std_ppg'])
        base_score *= pace_factor * fatigue_factor
        base_score -= blowout_adjustment
        return max(85, min(160, base_score))
    
    def simulate_game(self, away_team: str, home_team: str, minimum_line: float,
                     away_rest_days: int = 3, home_rest_days: int = 3,
                     spread: float = 0.0) -> Dict:
        """Run full Monte Carlo simulation for a single game"""
        away_profile = self.get_team_profile(away_team)
        home_profile = self.get_team_profile(home_team)
        
        away_fatigue = 0.97 if away_rest_days <= 1 else 1.0
        home_fatigue = 0.97 if home_rest_days <= 1 else 1.0
        
        abs_spread = abs(spread) if spread else 0
        blowout_prob = min(0.25, abs_spread * 0.02)
        
        simulated_totals = []
        hits = 0
        
        for _ in range(self.n_simulations):
            pace_factor = np.random.normal(1.0, 0.03)
            is_blowout = np.random.random() < blowout_prob
            blowout_adj = 8 if is_blowout else 0
            
            away_score = self.simulate_team_score(
                away_profile, pace_factor, away_fatigue, blowout_adj / 2
            )
            home_score = self.simulate_team_score(
                home_profile, pace_factor, home_fatigue, blowout_adj / 2
            )
            
            total = away_score + home_score
            simulated_totals.append(total)
            if total > minimum_line:
                hits += 1
        
        simulated_totals = np.array(simulated_totals)
        
        risk_factors = []
        if away_profile['std_ppg'] > 12:
            risk_factors.append(f"{away_team} high variance (±{away_profile['std_ppg']:.1f})")
        if home_profile['std_ppg'] > 12:
            risk_factors.append(f"{home_team} high variance (±{home_profile['std_ppg']:.1f})")
        if away_fatigue < 1.0:
            risk_factors.append(f"{away_team} on back-to-back")
        if home_fatigue < 1.0:
            risk_factors.append(f"{home_team} on back-to-back")
        if blowout_prob > 0.15:
            risk_factors.append(f"High blowout risk ({blowout_prob*100:.0f}%)")
        if not away_profile['variance_reliable']:
            risk_factors.append(f"{away_team} limited data ({away_profile['games_played']} games)")
        if not home_profile['variance_reliable']:
            risk_factors.append(f"{home_team} limited data ({home_profile['games_played']} games)")
        
        return {
            'away_team': away_team, 'home_team': home_team,
            'minimum_line': minimum_line, 'simulations': self.n_simulations,
            'hits': hits, 'mc_probability': round((hits / self.n_simulations) * 100, 2),
            'avg_simulated_total': round(np.mean(simulated_totals), 1),
            'std_simulated_total': round(np.std(simulated_totals), 1),
            'min_simulated_total': round(np.min(simulated_totals), 1),
            'max_simulated_total': round(np.max(simulated_totals), 1),
            'percentile_5': round(np.percentile(simulated_totals, 5), 1),
            'percentile_95': round(np.percentile(simulated_totals, 95), 1),
            'risk_factors': risk_factors,
            'away_profile': away_profile, 'home_profile': home_profile
        }
    
    def get_mc_decision(self, mc_probability: float) -> Tuple[str, str]:
        if mc_probability >= 92:
            return ('STRONG_YES', 'VERY HIGH')
        elif mc_probability >= 85:
            return ('YES', 'HIGH')
        elif mc_probability >= 78:
            return ('MAYBE', 'MEDIUM')
        elif mc_probability >= 70:
            return ('LEAN_NO', 'LOW')
        else:
            return ('NO', 'VERY LOW')
    
    def calculate_parlay_probability(self, individual_probs: list) -> float:
        combined = 1.0
        for prob in individual_probs:
            combined *= (prob / 100)
        return round(combined * 100, 2)


def print_team_profiles(engine: MonteCarloEngine):
    """Print all team variance profiles"""
    print("\n" + "=" * 70)
    print("TEAM VARIANCE PROFILES")
    print("=" * 70)
    print(f"{'Team':<30} {'Mean PPG':>10} {'Std Dev':>10} {'Games':>8}")
    print("-" * 70)
    
    for team, profile in sorted(engine.team_profiles.items()):
        print(f"{team:<30} {profile['mean_ppg']:>10.1f} {profile['std_ppg']:>10.1f} {profile['games_played']:>8}")
MCEOF

echo "✓ Created core/monte_carlo_engine.py"

# Create master_workflow_mc.py
cat > master_workflow_mc.py << 'WFEOF'
"""
MASTER WORKFLOW - MONTE CARLO ENHANCED
"""

import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data_collection.bball_ref_collector import BballRefCollector
from data_collection.odds_minimum_fetcher import MinimumAlternateFetcher
from data_collection.game_results_collector import GameResultsCollector
from core.minimum_total_predictor import MinimumTotalPredictor
from core.monte_carlo_engine import MonteCarloEngine
from analyzers.rest_days_calculator import RestDaysCalculator

import pandas as pd


def get_mc_decision(mc_prob: float, original_conf: float) -> tuple:
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
    
    flag = None
    if original_conf >= 80 and mc_prob < 78:
        flag = "⚠️ DOWNGRADED: MC found hidden risk"
    elif original_conf < 75 and mc_prob >= 85:
        flag = "📈 UPGRADED: Safer than original thought"
    
    return decision, level, flag


def print_mc_results(results: list):
    strong_yes = [r for r in results if r['mc_decision'] == 'STRONG_YES']
    yes_bets = [r for r in results if r['mc_decision'] == 'YES']
    maybe_bets = [r for r in results if r['mc_decision'] == 'MAYBE']
    lean_no = [r for r in results if r['mc_decision'] == 'LEAN_NO']
    no_bets = [r for r in results if r['mc_decision'] == 'NO']
    
    print("\n" + "=" * 80)
    print("MONTE CARLO ENHANCED PREDICTIONS (10,000 simulations per game)")
    print("=" * 80)
    
    if strong_yes:
        print("\n🟢 STRONG YES (92%+ MC) - CORE PARLAY MATERIAL")
        print("-" * 80)
        for r in strong_yes:
            print(f"\n  {r['game']}")
            print(f"    Line: {r['minimum_total']} | Avg Sim: {r['avg_simulated_total']}")
            print(f"    Original: {r['original_confidence']}% | MC: {r['mc_probability']}%")
            if r['risk_factors']:
                print(f"    Risks: {', '.join(r['risk_factors'][:2])}")
    
    if yes_bets:
        print("\n🟡 YES (85-92% MC) - SAFE FOR PARLAYS")
        print("-" * 80)
        for r in yes_bets:
            print(f"\n  {r['game']}")
            print(f"    Line: {r['minimum_total']} | MC: {r['mc_probability']}%")
            if r.get('flag'):
                print(f"    {r['flag']}")
    
    if maybe_bets:
        print("\n⚠️ MAYBE (78-85% MC) - CAUTION")
        print("-" * 80)
        for r in maybe_bets:
            print(f"  {r['game']} | MC: {r['mc_probability']}%")
    
    if lean_no:
        print("\n🔸 LEAN NO (70-78% MC)")
        print("-" * 80)
        for r in lean_no:
            print(f"  {r['game']} | MC: {r['mc_probability']}%")
    
    if no_bets:
        print("\n🔴 NO BET (<70% MC)")
        print("-" * 80)
        for r in no_bets:
            print(f"  {r['game']} | MC: {r['mc_probability']}%")


def generate_parlay_recommendations(results: list, mc_engine):
    bettable = [r for r in results if r['mc_decision'] in ['STRONG_YES', 'YES']]
    
    if len(bettable) == 0:
        print("\n⚠️ NO SAFE PARLAY OPTIONS TONIGHT")
        return None
    
    print("\n" + "=" * 80)
    print("PARLAY RECOMMENDATIONS")
    print("=" * 80)
    
    bettable.sort(key=lambda x: x['mc_probability'], reverse=True)
    
    if len(bettable) >= 2:
        two_leg = bettable[:2]
        two_leg_prob = mc_engine.calculate_parlay_probability([g['mc_probability'] for g in two_leg])
        
        print(f"\n✅ SAFEST (2-leg): Combined {two_leg_prob}%")
        for g in two_leg:
            print(f"   • {g['game']} ({g['mc_probability']}%)")
        print(f"   {'✓ RECOMMENDED' if two_leg_prob >= 75 else '⚠️ BORDERLINE'}")
    
    if len(bettable) >= 3:
        three_leg = bettable[:3]
        three_leg_prob = mc_engine.calculate_parlay_probability([g['mc_probability'] for g in three_leg])
        
        print(f"\n📊 STANDARD (3-leg): Combined {three_leg_prob}%")
        for g in three_leg:
            print(f"   • {g['game']} ({g['mc_probability']}%)")
    
    print(f"\n🎯 SINGLE BEST: {bettable[0]['game']} ({bettable[0]['mc_probability']}%)")
    
    return bettable


def main():
    print("\n" + "=" * 80)
    print("NBA MINIMUM SYSTEM - MONTE CARLO ENHANCED")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 80)
    
    # Step 1: Team Stats
    print("\nSTEP 1: Team Stats")
    if not os.path.exists('data/nba_team_stats_2025_2026.csv'):
        print("Collecting team stats...")
        BballRefCollector().run()
    team_stats = pd.read_csv('data/nba_team_stats_2025_2026.csv')
    print(f"[OK] {len(team_stats)} teams")
    
    # Step 2: Completed Games
    print("\nSTEP 2: Completed Games")
    if not os.path.exists('data/nba_completed_games_2025_2026.csv'):
        GameResultsCollector().run()
    completed_games = pd.read_csv('data/nba_completed_games_2025_2026.csv')
    print(f"[OK] {len(completed_games)} games")
    
    # Step 3: Today's Games
    print("\nSTEP 3: Today's Games")
    MinimumAlternateFetcher().run()
    upcoming = pd.read_csv('data/upcoming_games.csv')
    print(f"[OK] {len(upcoming)} games today")
    
    if len(upcoming) == 0:
        print("\n⚠️ NO GAMES TODAY")
        return True
    
    # Step 4: Original Predictions
    print("\nSTEP 4: Original Predictions")
    predictor = MinimumTotalPredictor(team_stats, completed_games)
    predictions = predictor.predict_all_games(upcoming)
    
    # Step 5: Monte Carlo
    print("\nSTEP 5: Monte Carlo Simulations (10,000 per game)")
    mc_engine = MonteCarloEngine(team_stats, completed_games, n_simulations=10000)
    rest_calc = RestDaysCalculator(completed_games)
    
    mc_results = []
    
    for pred in predictions:
        game = f"{pred['away_team']} @ {pred['home_team']}"
        print(f"  Simulating {game}...", end=" ")
        
        away_rest = rest_calc.calculate_rest_days(pred['away_team'], pred['game_time'])
        home_rest = rest_calc.calculate_rest_days(pred['home_team'], pred['game_time'])
        
        mc_result = mc_engine.simulate_game(
            pred['away_team'], pred['home_team'], pred['minimum_total'],
            away_rest['rest_days'], home_rest['rest_days']
        )
        
        mc_decision, mc_level, flag = get_mc_decision(mc_result['mc_probability'], pred['confidence'])
        
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
            'percentile_5': mc_result['percentile_5'],
            'percentile_95': mc_result['percentile_95'],
            'risk_factors': mc_result['risk_factors'],
            'flag': flag
        }
        
        mc_results.append(combined)
        print(f"MC: {mc_result['mc_probability']}%")
    
    # Print Results
    print_mc_results(mc_results)
    generate_parlay_recommendations(mc_results, mc_engine)
    
    # Export
    print("\n" + "=" * 80)
    print("EXPORTING RESULTS")
    
    export_df = pd.DataFrame(mc_results)
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M')
    os.makedirs('output_archive/decisions', exist_ok=True)
    filename = f"output_archive/decisions/{timestamp}_mc_decisions.csv"
    export_df.to_csv(filename, index=False)
    print(f"[OK] Saved to {filename}")
    
    # Summary
    strong_yes = len([r for r in mc_results if r['mc_decision'] == 'STRONG_YES'])
    yes_count = len([r for r in mc_results if r['mc_decision'] == 'YES'])
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print(f"🟢 STRONG YES: {strong_yes}")
    print(f"🟡 YES: {yes_count}")
    print(f"Total bettable: {strong_yes + yes_count}")
    print("=" * 80)
    
    return True


if __name__ == "__main__":
    main()
WFEOF

echo "✓ Created master_workflow_mc.py"

echo ""
echo "======================================"
echo "INSTALLATION COMPLETE!"
echo "======================================"
echo ""
echo "Test the installation:"
echo "  python master_workflow_mc.py"
echo ""
echo "Your new workflow:"
echo "  python master_workflow_mc.py  (instead of master_workflow.py)"
echo ""
