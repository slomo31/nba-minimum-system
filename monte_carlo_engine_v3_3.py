"""
Monte Carlo Engine V3.3 - Smart Variance Handling
===================================================
Changes from V3.2:
- HIGH VARIANCE threshold raised to 20 (was 14)
- Only flag variance when EXTREME (>22) or BOTH teams high variance
- Removed redundant pace flags that overlap

The issue: NBA game totals naturally have 15-20 point variance.
Flagging at 14 catches almost every game.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')


class MonteCarloEngineV33:
    """
    Monte Carlo simulation engine V3.3 with SMART variance handling
    """
    
    # ==========================================
    # V3.3 THRESHOLDS - SMART VARIANCE
    # ==========================================
    
    # Defense thresholds
    ELITE_DEFENSE_THRESHOLD = 108.0      # Truly elite
    GOOD_DEFENSE_THRESHOLD = 110.0       # Good defense
    ROAD_GOOD_DEFENSE_THRESHOLD = 109.0  # Only flag really good road D
    
    # Offense thresholds
    MEDIOCRE_OFFENSE_THRESHOLD = 111.0   # Slightly loosened
    WEAK_OFFENSE_THRESHOLD = 107.0       # Only truly weak
    
    # Pace thresholds
    SLOW_PACE_THRESHOLD = 95.0           # Only flag very slow
    PACE_MISMATCH_THRESHOLD = 6.0        # Allow more mismatch
    
    # Variance thresholds - THE KEY CHANGE
    HIGH_VARIANCE_THRESHOLD = 20.0       # Was 14 - now only extreme
    EXTREME_VARIANCE_THRESHOLD = 22.0    # New - for single team extreme
    BOTH_HIGH_VARIANCE_THRESHOLD = 18.0  # Flag if BOTH teams are this high
    
    # Decision thresholds
    STRONG_YES_THRESHOLD = 95.0
    YES_THRESHOLD = 92.0
    LEAN_YES_THRESHOLD = 88.0
    
    def __init__(self, team_stats_df: pd.DataFrame, completed_games_df: pd.DataFrame = None):
        """Initialize the engine with team stats"""
        self.team_stats = team_stats_df
        self.completed_games = completed_games_df
        self.team_profiles = {}
        self.league_avg_pace = 100.0
        self.league_avg_ortg = 115.0
        self.league_avg_drtg = 115.0
        
        print("  Initializing Monte Carlo Engine V3.3 (Smart Variance)...")
        self._build_team_profiles()
        self._fetch_injuries()
        print("  ✓ Monte Carlo Engine V3.3 initialized")
    
    def _build_team_profiles(self):
        """Build statistical profiles for each team"""
        print("  Building team profiles with efficiency ratings...")
        
        # Calculate league averages
        self.league_avg_pace = self.team_stats['Pace'].mean()
        self.league_avg_ortg = self.team_stats['ORtg'].mean()
        self.league_avg_drtg = self.team_stats['DRtg'].mean()
        
        print(f"    League Avg Pace: {self.league_avg_pace:.1f}")
        print(f"    League Avg ORtg: {self.league_avg_ortg:.1f}")
        print(f"    League Avg DRtg: {self.league_avg_drtg:.1f}")
        
        # Calculate game-by-game variance for each team
        team_variances = {}
        if self.completed_games is not None and len(self.completed_games) > 0:
            for team in self.team_stats['Team'].unique():
                team_games = self.completed_games[
                    (self.completed_games['Visitor'] == team) | 
                    (self.completed_games['Home'] == team)
                ]
                if len(team_games) >= 5:
                    totals = team_games['Total_Points'].values
                    team_variances[team] = np.std(totals)
                else:
                    team_variances[team] = 15.0  # Default variance
        
        # Calculate league average variance
        all_variances = list(team_variances.values()) if team_variances else [15.0]
        league_avg_variance = np.mean(all_variances)
        print(f"    League Avg Variance: ±{league_avg_variance:.1f}")
        
        # Build profiles
        elite_d_count = 0
        slow_pace_count = 0
        weak_offense_count = 0
        high_var_count = 0
        
        for _, row in self.team_stats.iterrows():
            team = row['Team']
            
            ortg = row.get('ORtg', self.league_avg_ortg)
            drtg = row.get('DRtg', self.league_avg_drtg)
            pace = row.get('Pace', self.league_avg_pace)
            ppg = row.get('PPG', 110.0)
            
            # Get variance
            variance = team_variances.get(team, 15.0)
            
            # Classify team
            is_elite_defense = drtg < self.ELITE_DEFENSE_THRESHOLD
            is_good_defense = drtg < self.GOOD_DEFENSE_THRESHOLD
            is_slow_pace = pace < self.SLOW_PACE_THRESHOLD
            is_weak_offense = ortg < self.WEAK_OFFENSE_THRESHOLD
            is_high_variance = variance > self.HIGH_VARIANCE_THRESHOLD
            is_extreme_variance = variance > self.EXTREME_VARIANCE_THRESHOLD
            
            if is_elite_defense:
                elite_d_count += 1
            if is_slow_pace:
                slow_pace_count += 1
            if is_weak_offense:
                weak_offense_count += 1
            if is_high_variance:
                high_var_count += 1
            
            self.team_profiles[team] = {
                'ortg': ortg,
                'drtg': drtg,
                'pace': pace,
                'ppg': ppg,
                'variance': variance,
                'is_elite_defense': is_elite_defense,
                'is_good_defense': is_good_defense,
                'is_slow_pace': is_slow_pace,
                'is_weak_offense': is_weak_offense,
                'is_high_variance': is_high_variance,
                'is_extreme_variance': is_extreme_variance
            }
        
        print(f"    Elite defenses (DRtg < {self.ELITE_DEFENSE_THRESHOLD}): {elite_d_count}")
        if elite_d_count > 0:
            for team, profile in self.team_profiles.items():
                if profile['is_elite_defense']:
                    print(f"      - {team} ({profile['drtg']:.1f})")
        print(f"    Slow pace teams (Pace < {self.SLOW_PACE_THRESHOLD}): {slow_pace_count}")
        print(f"    Weak offenses (ORtg < {self.WEAK_OFFENSE_THRESHOLD}): {weak_offense_count}")
        print(f"    High variance teams (StdDev > {self.HIGH_VARIANCE_THRESHOLD}): {high_var_count}")
    
    def _fetch_injuries(self):
        """Fetch injury data (placeholder)"""
        print("  Fetching injury data...")
        self.injuries = {}
        print(f"    ✓ Loaded injuries for {len(self.injuries)} teams")
    
    def calculate_matchup_expected(self, away_team: str, home_team: str) -> Dict:
        """Calculate expected total using matchup-based scoring"""
        away_profile = self.team_profiles.get(away_team, {})
        home_profile = self.team_profiles.get(home_team, {})
        
        if not away_profile or not home_profile:
            return None
        
        away_ortg = away_profile['ortg']
        away_drtg = away_profile['drtg']
        home_ortg = home_profile['ortg']
        home_drtg = home_profile['drtg']
        away_pace = away_profile['pace']
        home_pace = home_profile['pace']
        
        game_pace = (away_pace + home_pace) / 2
        pace_factor = game_pace / 100.0
        
        away_expected = (away_ortg * home_drtg) / self.league_avg_drtg * pace_factor
        home_expected = (home_ortg * away_drtg) / self.league_avg_drtg * pace_factor + 2.5
        
        total_expected = away_expected + home_expected
        
        return {
            'away_expected': away_expected,
            'home_expected': home_expected,
            'total_expected': total_expected,
            'game_pace': game_pace,
            'away_ortg': away_ortg,
            'away_drtg': away_drtg,
            'home_ortg': home_ortg,
            'home_drtg': home_drtg
        }
    
    def run_simulation(self, away_team: str, home_team: str, minimum_line: float, 
                       n_simulations: int = 10000) -> Dict:
        """Run Monte Carlo simulation"""
        matchup = self.calculate_matchup_expected(away_team, home_team)
        
        if matchup is None:
            return None
        
        away_profile = self.team_profiles.get(away_team, {})
        home_profile = self.team_profiles.get(home_team, {})
        
        away_var = away_profile.get('variance', 15.0)
        home_var = home_profile.get('variance', 15.0)
        game_variance = np.sqrt(away_var**2 + home_var**2) / 1.5
        
        simulated_totals = np.random.normal(
            matchup['total_expected'], 
            game_variance, 
            n_simulations
        )
        
        floor = min(matchup['total_expected'] * 0.75, 180)
        simulated_totals = np.maximum(simulated_totals, floor)
        
        hits = np.sum(simulated_totals > minimum_line)
        mc_probability = (hits / n_simulations) * 100
        
        return {
            'mc_probability': mc_probability,
            'avg_simulated': np.mean(simulated_totals),
            'std_simulated': np.std(simulated_totals),
            'percentile_5': np.percentile(simulated_totals, 5),
            'percentile_10': np.percentile(simulated_totals, 10),
            'percentile_25': np.percentile(simulated_totals, 25),
            'percentile_75': np.percentile(simulated_totals, 75),
            'percentile_90': np.percentile(simulated_totals, 90),
            'percentile_95': np.percentile(simulated_totals, 95),
            'matchup': matchup,
            'minimum_line': minimum_line
        }
    
    def count_risk_flags(self, away_team: str, home_team: str, 
                         simulation_results: Dict) -> Tuple[int, List[str]]:
        """
        Count risk flags - V3.3 SMART VARIANCE
        
        Key changes:
        - Only flag extreme variance (>22) for single team
        - Flag if BOTH teams have high variance (>18)
        - Removed redundant pace flags
        """
        flags = []
        
        away_profile = self.team_profiles.get(away_team, {})
        home_profile = self.team_profiles.get(home_team, {})
        matchup = simulation_results.get('matchup', {})
        minimum_line = simulation_results.get('minimum_line', 0)
        
        away_drtg = away_profile.get('drtg', 115)
        home_drtg = home_profile.get('drtg', 115)
        away_ortg = away_profile.get('ortg', 115)
        home_ortg = home_profile.get('ortg', 115)
        away_pace = away_profile.get('pace', 100)
        home_pace = home_profile.get('pace', 100)
        away_var = away_profile.get('variance', 15)
        home_var = home_profile.get('variance', 15)
        
        # === FLAG 1: Elite defense (keep - these matter) ===
        if away_drtg < self.ELITE_DEFENSE_THRESHOLD:
            flags.append(f"🛡️ {away_team} elite defense (DRtg: {away_drtg:.1f})")
        if home_drtg < self.ELITE_DEFENSE_THRESHOLD:
            flags.append(f"🛡️ {home_team} elite defense (DRtg: {home_drtg:.1f})")
        
        # === FLAG 2: Both teams good defense ===
        if away_drtg < self.GOOD_DEFENSE_THRESHOLD and home_drtg < self.GOOD_DEFENSE_THRESHOLD:
            flags.append(f"🛡️🛡️ BOTH teams good defense ({away_drtg:.1f} & {home_drtg:.1f} DRtg)")
        
        # === FLAG 3: Weak offense (only truly weak) ===
        if away_ortg < self.WEAK_OFFENSE_THRESHOLD:
            flags.append(f"📉 {away_team} weak offense (ORtg: {away_ortg:.1f})")
        if home_ortg < self.WEAK_OFFENSE_THRESHOLD:
            flags.append(f"📉 {home_team} weak offense (ORtg: {home_ortg:.1f})")
        
        # === FLAG 4: Very slow pace (only extreme) ===
        if away_pace < self.SLOW_PACE_THRESHOLD:
            flags.append(f"🐢 {away_team} very slow pace ({away_pace:.1f})")
        if home_pace < self.SLOW_PACE_THRESHOLD:
            flags.append(f"🐢 {home_team} very slow pace ({home_pace:.1f})")
        
        # === FLAG 5: Large pace mismatch ===
        pace_diff = abs(away_pace - home_pace)
        if pace_diff > self.PACE_MISMATCH_THRESHOLD:
            flags.append(f"🔄 Large pace mismatch ({pace_diff:.1f} difference)")
        
        # === FLAG 6: VARIANCE - SMART HANDLING ===
        # Only flag if:
        # a) Single team has EXTREME variance (>22), OR
        # b) BOTH teams have high variance (>18)
        
        if away_var > self.EXTREME_VARIANCE_THRESHOLD:
            flags.append(f"🎲 {away_team} extreme variance (±{away_var:.1f})")
        if home_var > self.EXTREME_VARIANCE_THRESHOLD:
            flags.append(f"🎲 {home_team} extreme variance (±{home_var:.1f})")
        
        # Both teams high variance (but not extreme individually)
        if (away_var > self.BOTH_HIGH_VARIANCE_THRESHOLD and 
            home_var > self.BOTH_HIGH_VARIANCE_THRESHOLD and
            away_var <= self.EXTREME_VARIANCE_THRESHOLD and
            home_var <= self.EXTREME_VARIANCE_THRESHOLD):
            flags.append(f"🎲🎲 BOTH teams high variance ({away_var:.1f} & {home_var:.1f})")
        
        # === FLAG 7: Floor risk ===
        percentile_10 = simulation_results.get('percentile_10', 0)
        if percentile_10 < minimum_line:
            flags.append(f"📉 Floor risk: 10th pctl ({percentile_10:.1f}) < line ({minimum_line})")
        
        return len(flags), flags
    
    def make_decision(self, mc_probability: float, flag_count: int, 
                      floor_safe: bool) -> Tuple[str, str]:
        """Make betting decision"""
        if not floor_safe:
            return ('SKIP', 'FLOOR_RISK')
        
        if flag_count >= 1:
            return ('SKIP', f'{flag_count}_FLAGS')
        
        if mc_probability >= self.STRONG_YES_THRESHOLD:
            return ('STRONG_YES', 'ELITE_CLEAN')
        elif mc_probability >= self.YES_THRESHOLD:
            return ('YES', 'HIGH_CLEAN')
        elif mc_probability >= self.LEAN_YES_THRESHOLD:
            return ('LEAN_YES', 'MEDIUM_CLEAN')
        else:
            return ('SKIP', 'LOW_PROBABILITY')
    
    def analyze_game(self, away_team: str, home_team: str, minimum_line: float,
                     n_simulations: int = 10000) -> Dict:
        """Complete analysis of a single game"""
        sim_results = self.run_simulation(away_team, home_team, minimum_line, n_simulations)
        
        if sim_results is None:
            return None
        
        flag_count, flags = self.count_risk_flags(away_team, home_team, sim_results)
        floor_safe = sim_results['percentile_10'] >= minimum_line
        decision, reason = self.make_decision(sim_results['mc_probability'], flag_count, floor_safe)
        
        return {
            'away_team': away_team,
            'home_team': home_team,
            'game': f"{away_team} @ {home_team}",
            'minimum_line': minimum_line,
            'mc_probability': sim_results['mc_probability'],
            'avg_simulated': sim_results['avg_simulated'],
            'std_simulated': sim_results['std_simulated'],
            'percentile_5': sim_results['percentile_5'],
            'percentile_10': sim_results['percentile_10'],
            'percentile_90': sim_results['percentile_90'],
            'percentile_95': sim_results['percentile_95'],
            'flag_count': flag_count,
            'flags': flags,
            'floor_safe': floor_safe,
            'decision': decision,
            'reason': reason,
            'matchup': sim_results['matchup']
        }


def print_thresholds():
    """Print V3.3 threshold changes"""
    print("\n" + "=" * 70)
    print("V3.3 SMART VARIANCE THRESHOLDS")
    print("=" * 70)
    print("""
    VARIANCE (THE BIG CHANGE):
    - Single team extreme: StdDev > 22 (was 12 in V3.1)
    - Both teams high: StdDev > 18 for BOTH
    - Normal variance (15-20) is NO LONGER FLAGGED
    
    OTHER THRESHOLDS:
    - Elite defense: DRtg < 108 (same)
    - Good defense: DRtg < 110 (was 114)
    - Weak offense: ORtg < 107 (was 110)
    - Slow pace: Pace < 95 (was 98)
    - Pace mismatch: Diff > 6 (was 3)
    """)


if __name__ == "__main__":
    print_thresholds()
