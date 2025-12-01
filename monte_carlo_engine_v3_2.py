"""
Monte Carlo Engine V3.2 - Adjusted Thresholds
==============================================
Changes from V3.1:
- Loosened flag thresholds to reduce false positives
- More picks while still filtering truly dangerous games

THRESHOLD CHANGES:
- High variance: StdDev > 12 → StdDev > 14
- Both below avg pace: Pace < 100 → Pace < 98
- Road good defense: DRtg < 113 → DRtg < 110
- Pace mismatch: Diff > 3.0 → Diff > 5.0
- Both good defense: DRtg < 114 → DRtg < 111
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')


class MonteCarloEngineV32:
    """
    Monte Carlo simulation engine V3.2 with LOOSENED flag thresholds
    
    Key improvements over V3.1:
    - Less restrictive variance threshold (14 vs 12)
    - Less restrictive pace thresholds
    - Less restrictive defense thresholds
    - Should produce more bettable games
    """
    
    # ==========================================
    # V3.2 LOOSENED THRESHOLDS
    # ==========================================
    
    # Defense thresholds (higher = more lenient)
    ELITE_DEFENSE_THRESHOLD = 108.0      # Same - truly elite
    GOOD_DEFENSE_THRESHOLD = 111.0       # Was 114 - now stricter definition of "good"
    ROAD_GOOD_DEFENSE_THRESHOLD = 110.0  # Was 113 - only flag really good road D
    
    # Offense thresholds
    MEDIOCRE_OFFENSE_THRESHOLD = 112.0   # Same
    WEAK_OFFENSE_THRESHOLD = 108.0       # Was 110 - only flag truly weak
    
    # Pace thresholds (lower = more lenient)  
    SLOW_PACE_THRESHOLD = 96.0           # Was 98 - only flag truly slow
    BOTH_BELOW_AVG_PACE_THRESHOLD = 98.0 # Was 100 - more lenient
    PACE_MISMATCH_THRESHOLD = 5.0        # Was 3.0 - allow more mismatch
    
    # Variance threshold (higher = more lenient)
    HIGH_VARIANCE_THRESHOLD = 14.0       # Was 12 - allow more variance
    
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
        
        print("  Initializing Monte Carlo Engine V3.2 (Loosened Thresholds)...")
        self._build_team_profiles()
        self._fetch_injuries()
        print("  ✓ Monte Carlo Engine V3.2 initialized")
    
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
        
        # Calculate game-by-game variance for each team if we have completed games
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
                    team_variances[team] = 12.0  # Default variance
        
        # Build profiles
        elite_d_count = 0
        slow_pace_count = 0
        bad_offense_count = 0
        mediocre_offense_count = 0
        
        for _, row in self.team_stats.iterrows():
            team = row['Team']
            
            ortg = row.get('ORtg', self.league_avg_ortg)
            drtg = row.get('DRtg', self.league_avg_drtg)
            pace = row.get('Pace', self.league_avg_pace)
            ppg = row.get('PPG', 110.0)
            
            # Get variance from game history or estimate
            if team in team_variances:
                variance = team_variances[team]
            else:
                variance = 12.0
            
            # Classify team
            is_elite_defense = drtg < self.ELITE_DEFENSE_THRESHOLD
            is_good_defense = drtg < self.GOOD_DEFENSE_THRESHOLD
            is_slow_pace = pace < self.SLOW_PACE_THRESHOLD
            is_bad_offense = ortg < self.WEAK_OFFENSE_THRESHOLD
            is_mediocre_offense = ortg < self.MEDIOCRE_OFFENSE_THRESHOLD
            is_high_variance = variance > self.HIGH_VARIANCE_THRESHOLD
            
            if is_elite_defense:
                elite_d_count += 1
            if is_slow_pace:
                slow_pace_count += 1
            if is_bad_offense:
                bad_offense_count += 1
            if is_mediocre_offense:
                mediocre_offense_count += 1
            
            self.team_profiles[team] = {
                'ortg': ortg,
                'drtg': drtg,
                'pace': pace,
                'ppg': ppg,
                'variance': variance,
                'is_elite_defense': is_elite_defense,
                'is_good_defense': is_good_defense,
                'is_slow_pace': is_slow_pace,
                'is_bad_offense': is_bad_offense,
                'is_mediocre_offense': is_mediocre_offense,
                'is_high_variance': is_high_variance
            }
        
        print(f"    Elite defenses (DRtg < {self.ELITE_DEFENSE_THRESHOLD}): {elite_d_count}")
        if elite_d_count > 0:
            for team, profile in self.team_profiles.items():
                if profile['is_elite_defense']:
                    print(f"      - {team} ({profile['drtg']:.1f})")
        print(f"    Slow pace teams (Pace < {self.SLOW_PACE_THRESHOLD}): {slow_pace_count}")
        print(f"    Bad offenses (ORtg < {self.WEAK_OFFENSE_THRESHOLD}): {bad_offense_count}")
        print(f"    Mediocre offenses (ORtg < {self.MEDIOCRE_OFFENSE_THRESHOLD}): {mediocre_offense_count}")
    
    def _fetch_injuries(self):
        """Fetch injury data (placeholder for now)"""
        print("  Fetching injury data...")
        self.injuries = {}
        print(f"    ✓ Loaded injuries for {len(self.injuries)} teams")
    
    def calculate_matchup_expected(self, away_team: str, home_team: str) -> Dict:
        """
        Calculate expected total using matchup-based scoring
        
        Formula: Expected Points = (Team ORtg × Opp DRtg) / League Avg × Pace Factor
        """
        away_profile = self.team_profiles.get(away_team, {})
        home_profile = self.team_profiles.get(home_team, {})
        
        if not away_profile or not home_profile:
            return None
        
        # Get ratings
        away_ortg = away_profile['ortg']
        away_drtg = away_profile['drtg']
        home_ortg = home_profile['ortg']
        home_drtg = home_profile['drtg']
        
        away_pace = away_profile['pace']
        home_pace = home_profile['pace']
        
        # Calculate game pace (average of both teams)
        game_pace = (away_pace + home_pace) / 2
        pace_factor = game_pace / 100.0
        
        # Matchup-based expected scoring
        # Away team scores: (Away ORtg × Home DRtg) / League Avg
        away_expected = (away_ortg * home_drtg) / self.league_avg_drtg * pace_factor
        
        # Home team scores: (Home ORtg × Away DRtg) / League Avg + home court
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
        """
        Run Monte Carlo simulation for a game
        """
        matchup = self.calculate_matchup_expected(away_team, home_team)
        
        if matchup is None:
            return None
        
        away_profile = self.team_profiles.get(away_team, {})
        home_profile = self.team_profiles.get(home_team, {})
        
        # Get variance for both teams
        away_var = away_profile.get('variance', 12.0)
        home_var = home_profile.get('variance', 12.0)
        
        # Combined game variance
        game_variance = np.sqrt(away_var**2 + home_var**2) / 1.5
        
        # Run simulations
        simulated_totals = np.random.normal(
            matchup['total_expected'], 
            game_variance, 
            n_simulations
        )
        
        # Apply floor (games rarely go below certain thresholds)
        floor = min(matchup['total_expected'] * 0.75, 180)
        simulated_totals = np.maximum(simulated_totals, floor)
        
        # Calculate results
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
        Count risk flags for a game - V3.2 LOOSENED THRESHOLDS
        """
        flags = []
        
        away_profile = self.team_profiles.get(away_team, {})
        home_profile = self.team_profiles.get(home_team, {})
        matchup = simulation_results.get('matchup', {})
        minimum_line = simulation_results.get('minimum_line', 0)
        
        # === DEFENSE FLAGS ===
        
        # Flag 1: Elite defense involved (keep strict - these are game changers)
        if away_profile.get('is_elite_defense'):
            flags.append(f"🛡️ {away_team} elite defense (DRtg: {away_profile['drtg']:.1f})")
        if home_profile.get('is_elite_defense'):
            flags.append(f"🛡️ {home_team} elite defense (DRtg: {home_profile['drtg']:.1f})")
        
        # Flag 2: BOTH teams good defense (V3.2: DRtg < 111 instead of 114)
        away_drtg = away_profile.get('drtg', 115)
        home_drtg = home_profile.get('drtg', 115)
        if away_drtg < self.GOOD_DEFENSE_THRESHOLD and home_drtg < self.GOOD_DEFENSE_THRESHOLD:
            flags.append(f"🛡️🛡️ BOTH teams good defense ({away_drtg:.1f} & {home_drtg:.1f} DRtg)")
        
        # Flag 3: Road team good defense (V3.2: DRtg < 110 instead of 113)
        if away_drtg < self.ROAD_GOOD_DEFENSE_THRESHOLD:
            flags.append(f"🚗🛡️ Road team good defense ({away_drtg:.1f} DRtg)")
        
        # === OFFENSE FLAGS ===
        
        # Flag 4: Both mediocre offenses
        away_ortg = away_profile.get('ortg', 115)
        home_ortg = home_profile.get('ortg', 115)
        if away_ortg < self.MEDIOCRE_OFFENSE_THRESHOLD and home_ortg < self.MEDIOCRE_OFFENSE_THRESHOLD:
            flags.append(f"⚠️ Both teams mediocre offense ({away_ortg:.1f} vs {home_ortg:.1f})")
        
        # Flag 5: Weak offense (V3.2: ORtg < 108 instead of 110)
        if away_ortg < self.WEAK_OFFENSE_THRESHOLD:
            flags.append(f"📉 {away_team} weak offense (ORtg: {away_ortg:.1f})")
        if home_ortg < self.WEAK_OFFENSE_THRESHOLD:
            flags.append(f"📉 {home_team} weak offense (ORtg: {home_ortg:.1f})")
        
        # === PACE FLAGS ===
        
        away_pace = away_profile.get('pace', 100)
        home_pace = home_profile.get('pace', 100)
        
        # Flag 6: Slow pace team (V3.2: Pace < 96 instead of 98)
        if away_pace < self.SLOW_PACE_THRESHOLD:
            flags.append(f"🐢 {away_team} slow pace ({away_pace:.1f})")
        if home_pace < self.SLOW_PACE_THRESHOLD:
            flags.append(f"🐢 {home_team} slow pace ({home_pace:.1f})")
        
        # Flag 7: Both teams below avg pace (V3.2: Pace < 98 instead of 100)
        if away_pace < self.BOTH_BELOW_AVG_PACE_THRESHOLD and home_pace < self.BOTH_BELOW_AVG_PACE_THRESHOLD:
            flags.append(f"🐢🐢 Both teams below avg pace ({away_pace:.1f} & {home_pace:.1f})")
        
        # Flag 8: Pace mismatch (V3.2: Diff > 5.0 instead of 3.0)
        pace_diff = abs(away_pace - home_pace)
        if pace_diff > self.PACE_MISMATCH_THRESHOLD:
            flags.append(f"🔄 Pace mismatch ({pace_diff:.1f} difference)")
        
        # === VARIANCE FLAGS ===
        
        # Flag 9: High variance team (V3.2: StdDev > 14 instead of 12)
        away_var = away_profile.get('variance', 10)
        home_var = home_profile.get('variance', 10)
        if away_var > self.HIGH_VARIANCE_THRESHOLD:
            flags.append(f"🎲 {away_team} high variance (±{away_var:.1f})")
        if home_var > self.HIGH_VARIANCE_THRESHOLD:
            flags.append(f"🎲 {home_team} high variance (±{home_var:.1f})")
        
        # === STATISTICAL FLAGS ===
        
        # Flag 10: Floor risk (10th percentile below line)
        percentile_10 = simulation_results.get('percentile_10', 0)
        if percentile_10 < minimum_line:
            flags.append(f"📉 Floor risk: 10th pctl ({percentile_10:.1f}) < line ({minimum_line})")
        
        return len(flags), flags
    
    def make_decision(self, mc_probability: float, flag_count: int, 
                      floor_safe: bool) -> Tuple[str, str]:
        """
        Make betting decision based on MC probability and flags
        
        V3.2 Rule: Still only bet 0-flag games, but with loosened flag definitions
        """
        # Floor not safe = automatic skip
        if not floor_safe:
            return ('SKIP', 'FLOOR_RISK')
        
        # ANY flags = skip
        if flag_count >= 1:
            return ('SKIP', f'{flag_count}_FLAGS')
        
        # 0 flags - check probability thresholds
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
        """
        Complete analysis of a single game
        """
        # Run simulation
        sim_results = self.run_simulation(away_team, home_team, minimum_line, n_simulations)
        
        if sim_results is None:
            return None
        
        # Count flags
        flag_count, flags = self.count_risk_flags(away_team, home_team, sim_results)
        
        # Check floor safety
        floor_safe = sim_results['percentile_10'] >= minimum_line
        
        # Make decision
        decision, reason = self.make_decision(
            sim_results['mc_probability'], 
            flag_count, 
            floor_safe
        )
        
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
    """Print V3.2 threshold comparison"""
    print("\n" + "=" * 70)
    print("V3.2 THRESHOLD CHANGES (vs V3.1)")
    print("=" * 70)
    print("""
    | Flag                  | V3.1      | V3.2      | Change        |
    |-----------------------|-----------|-----------|---------------|
    | High variance         | StdDev>12 | StdDev>14 | More lenient  |
    | Both below avg pace   | Pace<100  | Pace<98   | More lenient  |
    | Slow pace team        | Pace<98   | Pace<96   | More lenient  |
    | Road good defense     | DRtg<113  | DRtg<110  | More lenient  |
    | Both good defense     | DRtg<114  | DRtg<111  | More lenient  |
    | Pace mismatch         | Diff>3.0  | Diff>5.0  | More lenient  |
    | Weak offense          | ORtg<110  | ORtg<108  | More lenient  |
    """)


if __name__ == "__main__":
    print_thresholds()
