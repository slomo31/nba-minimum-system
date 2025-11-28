"""
Monte Carlo Simulation Engine v3.1 - MATCHUP-BASED
====================================================
Upgraded based on CBB V3.1 learnings that achieved 100% win rate (14-0)

KEY UPGRADES FROM V3.0:
1. MATCHUP-BASED SCORING - Uses ORtg × OppDRtg formula
2. CUMULATIVE FLAG PENALTY - 3+ flags = auto-downgrade
3. FLOOR SAFETY CHECK - 10th percentile must clear minimum
4. CONTINUOUS DEFENSE ADJUSTMENT - Not just elite/not elite
5. BOTH BAD OFFENSES FLAG - When both teams have low ORtg

FORMULA FOR EXPECTED SCORING:
    game_tempo = (home_pace * 0.4) + (away_pace * 0.4) + (league_avg * 0.2)
    home_expected = (home_ortg * away_drtg / 100) * game_tempo / 100
    away_expected = (away_ortg * home_drtg / 100) * game_tempo / 100
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, List, Optional
import requests
import warnings
warnings.filterwarnings('ignore')


# ============================================================================
# CONFIGURATION - NBA SPECIFIC THRESHOLDS
# ============================================================================

# Efficiency thresholds (NBA scale - per 100 possessions)
ELITE_DEFENSE_THRESHOLD = 108.0      # DRtg below this = elite defense
GOOD_DEFENSE_THRESHOLD = 112.0       # DRtg below this = good defense
BAD_OFFENSE_THRESHOLD = 108.0        # ORtg below this = bad offense
MEDIOCRE_OFFENSE_THRESHOLD = 112.0   # ORtg below this = mediocre offense

# Pace thresholds
SLOW_PACE_THRESHOLD = 98.0           # Pace below this = slow team
FAST_PACE_THRESHOLD = 103.0          # Pace above this = fast team

# Variance thresholds
HIGH_VARIANCE_THRESHOLD = 12.0       # StdDev above this = high variance
MIN_STD_FLOOR = 8.0                  # Minimum standard deviation (raised from 6.0)

# Decision thresholds
YES_THRESHOLD = 88.0                 # Base threshold for YES
FLAG_1_THRESHOLD = 96.0              # Need this with 1 flag
FLAG_2_THRESHOLD = 97.0              # Need this with 2 flags
# 3+ flags = auto-downgrade to MAYBE

# Home court advantage (NBA is smaller than CBB)
HOME_COURT_ADVANTAGE = 2.5           # Points

# League averages (will be calculated from data)
LEAGUE_AVG_PACE = 100.0
LEAGUE_AVG_ORTG = 114.0
LEAGUE_AVG_DRTG = 114.0

# Star players for injury tracking
STAR_PLAYERS = {
    'Boston Celtics': ['Jayson Tatum', 'Jaylen Brown'],
    'Milwaukee Bucks': ['Giannis Antetokounmpo', 'Damian Lillard'],
    'Denver Nuggets': ['Nikola Jokic', 'Jamal Murray'],
    'Phoenix Suns': ['Kevin Durant', 'Devin Booker'],
    'Dallas Mavericks': ['Luka Doncic', 'Kyrie Irving'],
    'Philadelphia 76ers': ['Joel Embiid', 'Tyrese Maxey'],
    'Los Angeles Lakers': ['LeBron James', 'Anthony Davis'],
    'Golden State Warriors': ['Stephen Curry', 'Draymond Green'],
    'Cleveland Cavaliers': ['Donovan Mitchell', 'Darius Garland'],
    'Oklahoma City Thunder': ['Shai Gilgeous-Alexander', 'Chet Holmgren'],
    'New York Knicks': ['Jalen Brunson', 'Karl-Anthony Towns'],
    'Miami Heat': ['Jimmy Butler', 'Bam Adebayo'],
    'Minnesota Timberwolves': ['Anthony Edwards', 'Rudy Gobert'],
    'Memphis Grizzlies': ['Ja Morant', 'Desmond Bane'],
    'Sacramento Kings': ['De\'Aaron Fox', 'Domantas Sabonis'],
    'Los Angeles Clippers': ['Kawhi Leonard', 'Paul George'],
    'Indiana Pacers': ['Tyrese Haliburton', 'Pascal Siakam'],
    'New Orleans Pelicans': ['Zion Williamson', 'Brandon Ingram'],
    'Orlando Magic': ['Paolo Banchero', 'Franz Wagner'],
    'Houston Rockets': ['Jalen Green', 'Alperen Sengun'],
    'Atlanta Hawks': ['Trae Young', 'Dejounte Murray'],
    'Chicago Bulls': ['Zach LaVine', 'DeMar DeRozan'],
    'Toronto Raptors': ['Scottie Barnes', 'RJ Barrett'],
    'Brooklyn Nets': ['Mikal Bridges', 'Cameron Johnson'],
    'San Antonio Spurs': ['Victor Wembanyama', 'Devin Vassell'],
    'Portland Trail Blazers': ['Anfernee Simons', 'Jerami Grant'],
    'Charlotte Hornets': ['LaMelo Ball', 'Brandon Miller'],
    'Utah Jazz': ['Lauri Markkanen', 'Collin Sexton'],
    'Detroit Pistons': ['Cade Cunningham', 'Jaden Ivey'],
    'Washington Wizards': ['Jordan Poole', 'Kyle Kuzma'],
}


class MonteCarloEngineV31:
    """
    Monte Carlo V3.1 - Matchup-Based Simulation Engine
    
    Key improvements over V3.0:
    1. Uses ORtg × OppDRtg for expected scoring (not raw PPG)
    2. Cumulative flag penalty system
    3. Floor safety check (10th percentile)
    4. Continuous defense adjustment
    """
    
    def __init__(self, team_stats_df: pd.DataFrame, completed_games_df: pd.DataFrame, 
                 n_simulations: int = 10000, check_injuries: bool = True):
        """
        Initialize the V3.1 Monte Carlo Engine
        
        Args:
            team_stats_df: DataFrame with Team, PPG, ORtg, DRtg, Pace columns
            completed_games_df: DataFrame with completed game results
            n_simulations: Number of Monte Carlo simulations per game
            check_injuries: Whether to fetch injury data
        """
        self.team_stats = team_stats_df.copy()
        self.completed_games = completed_games_df.copy()
        self.n_simulations = n_simulations
        
        print(f"  Initializing Monte Carlo Engine V3.1...")
        print(f"  Building team profiles with efficiency ratings...")
        
        # Calculate league averages
        self.league_avg_pace = self.team_stats['Pace'].mean()
        self.league_avg_ortg = self.team_stats['ORtg'].mean() if 'ORtg' in self.team_stats.columns else 114.0
        self.league_avg_drtg = self.team_stats['DRtg'].mean() if 'DRtg' in self.team_stats.columns else 114.0
        self.league_avg_ppg = self.team_stats['PPG'].mean()
        
        print(f"    League Avg Pace: {self.league_avg_pace:.1f}")
        print(f"    League Avg ORtg: {self.league_avg_ortg:.1f}")
        print(f"    League Avg DRtg: {self.league_avg_drtg:.1f}")
        
        # Build team profiles
        self.team_profiles = self._build_team_profiles()
        
        # Identify special teams
        self._identify_elite_defenses()
        self._identify_slow_pace_teams()
        self._identify_bad_offenses()
        
        # Injury data
        self.injuries = {}
        if check_injuries:
            print("  Fetching injury data...")
            self._fetch_injuries()
        
        print(f"  ✓ Monte Carlo Engine V3.1 initialized")
    
    def _build_team_profiles(self) -> Dict:
        """Build comprehensive profiles for each team using efficiency data"""
        profiles = {}
        
        for _, row in self.team_stats.iterrows():
            team = row['Team']
            
            # Get efficiency ratings
            ortg = row['ORtg'] if 'ORtg' in row and pd.notna(row['ORtg']) else self.league_avg_ortg
            drtg = row['DRtg'] if 'DRtg' in row and pd.notna(row['DRtg']) else self.league_avg_drtg
            pace = row['Pace'] if 'Pace' in row and pd.notna(row['Pace']) else self.league_avg_pace
            ppg = row['PPG'] if 'PPG' in row and pd.notna(row['PPG']) else self.league_avg_ppg
            
            # Get game history for this team
            team_games = self.completed_games[
                (self.completed_games['Visitor'] == team) | 
                (self.completed_games['Home'] == team)
            ]
            
            # Calculate scoring variance from actual games
            if len(team_games) > 0:
                scores = []
                game_totals = []
                
                for _, game in team_games.iterrows():
                    if game['Visitor'] == team:
                        scores.append(game['Visitor_PTS'])
                    else:
                        scores.append(game['Home_PTS'])
                    game_totals.append(game['Total_Points'])
                
                scores = np.array(scores)
                game_totals = np.array(game_totals)
                
                std_ppg = np.std(scores) if len(scores) > 1 else 10.0
                std_ppg = max(std_ppg, MIN_STD_FLOOR)  # Apply floor
                
                game_total_std = np.std(game_totals) if len(game_totals) > 1 else 15.0
                avg_game_total = np.mean(game_totals)
                
                games_played = len(scores)
                variance_reliable = games_played >= 5
            else:
                std_ppg = 10.0
                game_total_std = 15.0
                avg_game_total = 220.0
                games_played = 0
                variance_reliable = False
            
            profiles[team] = {
                # Efficiency ratings (KEY FOR V3.1)
                'ortg': ortg,
                'drtg': drtg,
                'pace': pace,
                
                # Scoring stats
                'ppg': ppg,
                'std_ppg': std_ppg,
                'games_played': games_played,
                'variance_reliable': variance_reliable,
                
                # Game total history
                'avg_game_total': avg_game_total,
                'game_total_std': game_total_std,
                
                # Flags (will be set later)
                'is_elite_defense': False,
                'is_good_defense': False,
                'is_slow_pace': False,
                'is_bad_offense': False,
                'is_mediocre_offense': False,
                'is_high_variance': std_ppg > HIGH_VARIANCE_THRESHOLD
            }
        
        return profiles
    
    def _identify_elite_defenses(self):
        """Identify teams with elite and good defenses"""
        elite = []
        good = []
        
        for team, profile in self.team_profiles.items():
            if profile['drtg'] < ELITE_DEFENSE_THRESHOLD:
                profile['is_elite_defense'] = True
                elite.append(f"{team} ({profile['drtg']:.1f})")
            elif profile['drtg'] < GOOD_DEFENSE_THRESHOLD:
                profile['is_good_defense'] = True
                good.append(f"{team} ({profile['drtg']:.1f})")
        
        print(f"    Elite defenses (DRtg < {ELITE_DEFENSE_THRESHOLD}): {len(elite)}")
        for t in elite[:5]:
            print(f"      - {t}")
    
    def _identify_slow_pace_teams(self):
        """Identify slow pace teams"""
        slow = []
        
        for team, profile in self.team_profiles.items():
            if profile['pace'] < SLOW_PACE_THRESHOLD:
                profile['is_slow_pace'] = True
                slow.append(f"{team} ({profile['pace']:.1f})")
        
        print(f"    Slow pace teams (Pace < {SLOW_PACE_THRESHOLD}): {len(slow)}")
    
    def _identify_bad_offenses(self):
        """Identify teams with bad and mediocre offenses"""
        bad = []
        mediocre = []
        
        for team, profile in self.team_profiles.items():
            if profile['ortg'] < BAD_OFFENSE_THRESHOLD:
                profile['is_bad_offense'] = True
                bad.append(f"{team} ({profile['ortg']:.1f})")
            elif profile['ortg'] < MEDIOCRE_OFFENSE_THRESHOLD:
                profile['is_mediocre_offense'] = True
                mediocre.append(f"{team} ({profile['ortg']:.1f})")
        
        print(f"    Bad offenses (ORtg < {BAD_OFFENSE_THRESHOLD}): {len(bad)}")
        print(f"    Mediocre offenses (ORtg < {MEDIOCRE_OFFENSE_THRESHOLD}): {len(mediocre)}")
    
    def _fetch_injuries(self):
        """Fetch current injuries from ESPN API"""
        try:
            url = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/injuries"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                for team_data in data.get('teams', []):
                    team_name = team_data.get('team', {}).get('displayName', '')
                    injuries = []
                    
                    for athlete in team_data.get('injuries', []):
                        player_name = athlete.get('athlete', {}).get('displayName', '')
                        status = athlete.get('status', '')
                        injuries.append({
                            'player': player_name,
                            'status': status
                        })
                    
                    if team_name and injuries:
                        self.injuries[team_name] = injuries
                
                print(f"    ✓ Loaded injuries for {len(self.injuries)} teams")
            else:
                print(f"    ⚠️ Could not fetch injuries (status {response.status_code})")
                
        except Exception as e:
            print(f"    ⚠️ Injury fetch failed: {str(e)[:50]}")
            self.injuries = {}
    
    def is_star_player_out(self, team_name: str) -> Tuple[bool, List[str]]:
        """Check if any star players are out for a team"""
        team_injuries = self.injuries.get(team_name, [])
        stars = STAR_PLAYERS.get(team_name, [])
        
        out_stars = []
        for injury in team_injuries:
            player = injury.get('player', '')
            status = injury.get('status', '').lower()
            
            if any(star.lower() in player.lower() for star in stars):
                if 'out' in status or 'doubtful' in status:
                    out_stars.append(player)
        
        return len(out_stars) > 0, out_stars
    
    def get_team_profile(self, team_name: str) -> Dict:
        """Get profile for a team, with defaults if not found"""
        if team_name in self.team_profiles:
            return self.team_profiles[team_name]
        
        # Default profile for unknown teams
        return {
            'ortg': self.league_avg_ortg,
            'drtg': self.league_avg_drtg,
            'pace': self.league_avg_pace,
            'ppg': self.league_avg_ppg,
            'std_ppg': 10.0,
            'games_played': 0,
            'variance_reliable': False,
            'avg_game_total': 220.0,
            'game_total_std': 15.0,
            'is_elite_defense': False,
            'is_good_defense': False,
            'is_slow_pace': False,
            'is_bad_offense': False,
            'is_mediocre_offense': False,
            'is_high_variance': False
        }
    
    def calculate_matchup_expected(self, away_profile: Dict, home_profile: Dict) -> Tuple[float, float, float]:
        """
        Calculate matchup-specific expected scoring using efficiency formula
        
        This is THE KEY DIFFERENCE from V3.0!
        Instead of using raw PPG, we use:
            expected = (team_ortg × opp_drtg / 100) × game_tempo / 100
        
        Returns:
            (away_expected, home_expected, game_tempo)
        """
        # Calculate game tempo (weighted average)
        game_tempo = (
            home_profile['pace'] * 0.4 + 
            away_profile['pace'] * 0.4 + 
            self.league_avg_pace * 0.2
        )
        
        # Away team expected (scores against home defense)
        away_expected = (
            away_profile['ortg'] * home_profile['drtg'] / 100
        ) * game_tempo / 100
        
        # Home team expected (scores against away defense)
        home_expected = (
            home_profile['ortg'] * away_profile['drtg'] / 100
        ) * game_tempo / 100
        
        # Apply home court advantage
        home_expected += HOME_COURT_ADVANTAGE * 0.6
        away_expected -= HOME_COURT_ADVANTAGE * 0.4
        
        return away_expected, home_expected, game_tempo
    
    def count_risk_flags(self, away_profile: Dict, home_profile: Dict,
                         percentile_10: float, minimum_line: float,
                         away_team: str, home_team: str) -> Tuple[int, List[str]]:
        """
        Count risk flags for cumulative penalty system
        
        V3.1 STRICT - Updated with NEW FLAGS from loss analysis:
        - BOTH_GOOD_DEFENSE: Both teams DRtg < 114 (caught Toronto@Atlanta, SA@Phoenix)
        - PACE_MISMATCH: Pace diff > 3.0 (caught Denver@Portland, Chicago@Orlando)
        - WEAK_OFFENSE: Any team ORtg < 110 (caught Indiana@GSW)
        - BOTH_BELOW_AVG_PACE: Both teams Pace < 100 (caught SA@Phoenix)
        
        Returns:
            (flag_count, list of flag descriptions)
        """
        flags = []
        
        # ==========================================
        # ORIGINAL FLAGS
        # ==========================================
        
        # Flag 1: Elite defense involved (DRtg < 108)
        if away_profile['is_elite_defense']:
            flags.append(f"🛡️ {away_team} elite defense (DRtg: {away_profile['drtg']:.1f})")
        if home_profile['is_elite_defense']:
            flags.append(f"🛡️ {home_team} elite defense (DRtg: {home_profile['drtg']:.1f})")
        
        # Flag 2: Both teams have bad/mediocre offense (ORtg < 112)
        if (away_profile['is_bad_offense'] or away_profile['is_mediocre_offense']) and \
           (home_profile['is_bad_offense'] or home_profile['is_mediocre_offense']):
            flags.append(f"⚠️ Both teams mediocre offense ({away_profile['ortg']:.1f} vs {home_profile['ortg']:.1f})")
        
        # Flag 3: Slow pace involved (Pace < 98)
        if away_profile['is_slow_pace'] and home_profile['is_slow_pace']:
            flags.append(f"🐢 BOTH teams slow pace ({away_profile['pace']:.1f} & {home_profile['pace']:.1f})")
        elif away_profile['is_slow_pace']:
            flags.append(f"🐢 {away_team} slow pace ({away_profile['pace']:.1f})")
        elif home_profile['is_slow_pace']:
            flags.append(f"🐢 {home_team} slow pace ({home_profile['pace']:.1f})")
        
        # Flag 4: Floor risk - 10th percentile below minimum
        if percentile_10 < minimum_line:
            flags.append(f"📉 Floor risk: 10th pctl ({percentile_10:.1f}) < min ({minimum_line})")
        
        # Flag 5: High variance teams (StdDev > 12)
        if away_profile['is_high_variance']:
            flags.append(f"🎲 {away_team} high variance (±{away_profile['std_ppg']:.1f})")
        if home_profile['is_high_variance']:
            flags.append(f"🎲 {home_team} high variance (±{home_profile['std_ppg']:.1f})")
        
        # Flag 6: Road elite defense vs mediocre home offense
        if away_profile['is_elite_defense'] and (home_profile['is_bad_offense'] or home_profile['is_mediocre_offense']):
            flags.append(f"⚡ Road elite D vs mediocre home O - under risk")
        
        # Flag 7: Good defense + bad offense matchup
        if (away_profile['is_good_defense'] or away_profile['is_elite_defense']) and \
           (home_profile['is_bad_offense']):
            if f"Road elite D" not in str(flags):  # Avoid duplicate
                flags.append(f"⚡ Good D vs bad O matchup")
        
        # ==========================================
        # NEW FLAGS FROM LOSS ANALYSIS
        # ==========================================
        
        # Flag 8: BOTH_GOOD_DEFENSE - Both teams have DRtg < 114
        # Caught: Toronto @ Atlanta (112.5 & 113.3), SA @ Phoenix (112.3 & 113.7)
        if away_profile['drtg'] < 114 and home_profile['drtg'] < 114:
            flags.append(f"🛡️🛡️ BOTH teams good defense ({away_profile['drtg']:.1f} & {home_profile['drtg']:.1f} DRtg)")
        
        # Flag 9: PACE_MISMATCH - Pace difference > 3.0
        # Caught: Denver @ Portland (3.1 diff), Chicago @ Orlando (3.6 diff)
        pace_diff = abs(away_profile['pace'] - home_profile['pace'])
        if pace_diff > 3.0:
            flags.append(f"🔄 Pace mismatch ({pace_diff:.1f} difference)")
        
        # Flag 10: WEAK_OFFENSE - Any team with ORtg < 110
        # Caught: Indiana @ GSW (Pacers 107.5 ORtg)
        if away_profile['ortg'] < 110:
            flags.append(f"📉 {away_team} weak offense (ORtg: {away_profile['ortg']:.1f})")
        if home_profile['ortg'] < 110:
            flags.append(f"📉 {home_team} weak offense (ORtg: {home_profile['ortg']:.1f})")
        
        # Flag 11: BOTH_BELOW_AVG_PACE - Both teams below league average pace (100)
        # Caught: SA @ Phoenix (99.2 & 99.1)
        if away_profile['pace'] < 100 and home_profile['pace'] < 100:
            flags.append(f"🐢🐢 Both teams below avg pace ({away_profile['pace']:.1f} & {home_profile['pace']:.1f})")
        
        # Flag 12: ROAD_GOOD_DEFENSE - Road team has good defense (DRtg < 113)
        # This suppresses home scoring
        if away_profile['drtg'] < 113 and not away_profile['is_elite_defense']:
            flags.append(f"🚗🛡️ Road team good defense ({away_profile['drtg']:.1f} DRtg)")
        
        return len(flags), flags
    
    def simulate_game(self, away_team: str, home_team: str, minimum_line: float,
                      away_rest_days: int = 3, home_rest_days: int = 3,
                      spread: float = 0.0) -> Dict:
        """
        Run Monte Carlo simulation using matchup-based expected scoring
        
        This is the core V3.1 simulation that uses:
        1. ORtg × OppDRtg formula for expected scoring
        2. Variance from actual game history
        3. Cumulative flag penalty system
        4. Floor safety check
        """
        away_profile = self.get_team_profile(away_team)
        home_profile = self.get_team_profile(home_team)
        
        # ==========================================
        # MATCHUP-BASED EXPECTED SCORING (V3.1 KEY)
        # ==========================================
        
        away_expected, home_expected, game_tempo = self.calculate_matchup_expected(
            away_profile, home_profile
        )
        total_expected = away_expected + home_expected
        
        # ==========================================
        # CALCULATE ADJUSTMENT FACTORS
        # ==========================================
        
        # Fatigue (back-to-back)
        away_fatigue = 0.97 if away_rest_days <= 1 else 1.0
        home_fatigue = 0.97 if home_rest_days <= 1 else 1.0
        
        # Blowout probability
        abs_spread = abs(spread) if spread else 0
        blowout_prob = min(0.25, abs_spread * 0.02)
        
        # Injury impact
        away_star_out, away_out_players = self.is_star_player_out(away_team)
        home_star_out, home_out_players = self.is_star_player_out(home_team)
        
        away_injury_variance = 1.3 if away_star_out else 1.0
        home_injury_variance = 1.3 if home_star_out else 1.0
        
        # ==========================================
        # RUN SIMULATIONS
        # ==========================================
        
        simulated_totals = []
        hits = 0
        
        for _ in range(self.n_simulations):
            # Random pace variation (±3%)
            pace_variation = np.random.normal(1.0, 0.03)
            
            # Apply all adjustments to expected scoring
            away_adj_expected = away_expected * pace_variation * away_fatigue
            home_adj_expected = home_expected * pace_variation * home_fatigue
            
            # Get variance (boosted if star is out)
            away_std = away_profile['std_ppg'] * away_injury_variance
            home_std = home_profile['std_ppg'] * home_injury_variance
            
            # Simulate scores from normal distribution
            away_score = np.random.normal(away_adj_expected, away_std)
            home_score = np.random.normal(home_adj_expected, home_std)
            
            # Bad night scenario (5% chance per team)
            if np.random.random() < 0.05:
                away_score = away_adj_expected * np.random.uniform(0.75, 0.88)
            if np.random.random() < 0.05:
                home_score = home_adj_expected * np.random.uniform(0.75, 0.88)
            
            # Blowout adjustment (starters rest)
            if np.random.random() < blowout_prob:
                away_score -= 4
                home_score -= 4
            
            # Rare defensive slugfest (2%)
            if np.random.random() < 0.02:
                slug_reduction = np.random.uniform(8, 15)
                away_score -= slug_reduction / 2
                home_score -= slug_reduction / 2
            
            # Floor at realistic minimums
            away_score = max(75, min(155, away_score))
            home_score = max(75, min(155, home_score))
            
            total = away_score + home_score
            simulated_totals.append(total)
            
            if total > minimum_line:
                hits += 1
        
        simulated_totals = np.array(simulated_totals)
        
        # ==========================================
        # CALCULATE RESULTS
        # ==========================================
        
        mc_probability = round((hits / self.n_simulations) * 100, 2)
        avg_sim = round(np.mean(simulated_totals), 1)
        std_sim = round(np.std(simulated_totals), 1)
        
        percentile_5 = round(np.percentile(simulated_totals, 5), 1)
        percentile_10 = round(np.percentile(simulated_totals, 10), 1)
        percentile_25 = round(np.percentile(simulated_totals, 25), 1)
        percentile_75 = round(np.percentile(simulated_totals, 75), 1)
        percentile_90 = round(np.percentile(simulated_totals, 90), 1)
        percentile_95 = round(np.percentile(simulated_totals, 95), 1)
        
        # ==========================================
        # COUNT FLAGS FOR PENALTY SYSTEM
        # ==========================================
        
        flag_count, risk_flags = self.count_risk_flags(
            away_profile, home_profile,
            percentile_10, minimum_line,
            away_team, home_team
        )
        
        # Floor safety check
        floor_safe = percentile_10 >= minimum_line
        
        # ==========================================
        # MAKE DECISION WITH CUMULATIVE PENALTIES
        # ==========================================
        
        decision, confidence_level = self.make_decision(
            mc_probability, flag_count, floor_safe
        )
        
        # ==========================================
        # BUILD RESULT
        # ==========================================
        
        return {
            'away_team': away_team,
            'home_team': home_team,
            'game': f"{away_team} @ {home_team}",
            'minimum_line': minimum_line,
            
            # Expected scoring (V3.1 feature)
            'away_expected': round(away_expected, 1),
            'home_expected': round(home_expected, 1),
            'total_expected': round(total_expected, 1),
            'game_tempo': round(game_tempo, 1),
            
            # Simulation results
            'simulations': self.n_simulations,
            'hits': hits,
            'mc_probability': mc_probability,
            'avg_simulated_total': avg_sim,
            'std_simulated_total': std_sim,
            
            # Percentiles
            'percentile_5': percentile_5,
            'percentile_10': percentile_10,
            'percentile_25': percentile_25,
            'percentile_75': percentile_75,
            'percentile_90': percentile_90,
            'percentile_95': percentile_95,
            
            # Decision (V3.1 with flag penalties)
            'mc_decision': decision,
            'confidence_level': confidence_level,
            'flag_count': flag_count,
            'floor_safe': floor_safe,
            'risk_flags': risk_flags,
            
            # Team efficiency data
            'away_ortg': away_profile['ortg'],
            'away_drtg': away_profile['drtg'],
            'home_ortg': home_profile['ortg'],
            'home_drtg': home_profile['drtg'],
            
            # Flags
            'flags': {
                'slow_pace_game': away_profile['is_slow_pace'] or home_profile['is_slow_pace'],
                'both_slow_pace': away_profile['is_slow_pace'] and home_profile['is_slow_pace'],
                'elite_defense_involved': away_profile['is_elite_defense'] or home_profile['is_elite_defense'],
                'both_bad_offense': (away_profile['is_bad_offense'] or away_profile['is_mediocre_offense']) and \
                                   (home_profile['is_bad_offense'] or home_profile['is_mediocre_offense']),
                'high_variance': away_profile['is_high_variance'] or home_profile['is_high_variance'],
                'injury_concern': away_star_out or home_star_out
            },
            
            # Injury info
            'away_injuries': away_out_players,
            'home_injuries': home_out_players
        }
    
    def make_decision(self, mc_probability: float, flag_count: int, floor_safe: bool) -> Tuple[str, str]:
        """
        Make betting decision using STRICT cumulative flag penalty system
        
        V3.1 STRICT (updated based on backtest showing losses with flags):
        - 0 flags: 92%+ = YES (stricter base)
        - 1 flag: AUTO-DOWNGRADE to MAYBE (no exceptions)
        - 2+ flags: AUTO-DOWNGRADE to MAYBE (no exceptions)
        - Floor not safe: AUTO-DOWNGRADE
        
        The key learning: Games with ANY flags are dangerous, even at 99%+ MC.
        Utah Jazz, Cleveland, Boston Celtics all lost repeatedly WITH flags.
        """
        
        # Auto-downgrade if floor is not safe
        if not floor_safe:
            if mc_probability >= 80:
                return ('MAYBE', 'FLOOR_RISK')
            else:
                return ('NO', 'FLOOR_UNSAFE')
        
        # STRICT: ANY flags = MAYBE (this is the key change)
        # Backtest showed games with 1-2 flags at 97-100% MC still lost
        if flag_count >= 2:
            if mc_probability >= 95:
                return ('MAYBE', 'MULTI_FLAG_HIGH')
            elif mc_probability >= 85:
                return ('MAYBE', 'MULTI_FLAG')
            else:
                return ('NO', 'MULTI_FLAG_LOW')
        
        # 1 flag: Also MAYBE (too many losses in backtest)
        if flag_count == 1:
            if mc_probability >= 95:
                return ('MAYBE', 'FLAG_CAUTION')
            elif mc_probability >= 85:
                return ('MAYBE', 'FLAG_PENALTY')
            else:
                return ('NO', 'LOW_WITH_FLAG')
        
        # 0 flags ONLY: These are our safe bets
        if mc_probability >= 95:
            return ('STRONG_YES', 'ELITE_CLEAN')
        elif mc_probability >= 92:
            return ('YES', 'HIGH_CLEAN')
        elif mc_probability >= 88:
            return ('LEAN_YES', 'MEDIUM_CLEAN')
        elif mc_probability >= 80:
            return ('MAYBE', 'MEDIUM')
        else:
            return ('NO', 'LOW')
    
    def calculate_parlay_probability(self, probs: List[float]) -> float:
        """Calculate combined parlay probability"""
        combined = 1.0
        for p in probs:
            combined *= (p / 100)
        return round(combined * 100, 2)
    
    def get_summary_stats(self) -> Dict:
        """Get summary statistics about the engine"""
        elite_d = [t for t, p in self.team_profiles.items() if p['is_elite_defense']]
        slow = [t for t, p in self.team_profiles.items() if p['is_slow_pace']]
        bad_o = [t for t, p in self.team_profiles.items() if p['is_bad_offense']]
        high_var = [t for t, p in self.team_profiles.items() if p['is_high_variance']]
        
        return {
            'version': '3.1',
            'teams': len(self.team_profiles),
            'simulations_per_game': self.n_simulations,
            'league_avg_pace': round(self.league_avg_pace, 1),
            'league_avg_ortg': round(self.league_avg_ortg, 1),
            'league_avg_drtg': round(self.league_avg_drtg, 1),
            'elite_defenses': elite_d,
            'slow_pace_teams': slow,
            'bad_offenses': bad_o,
            'high_variance_teams': high_var
        }


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("MONTE CARLO ENGINE V3.1 - TEST")
    print("=" * 70)
    
    # Load test data
    import os
    
    if os.path.exists('data/nba_team_stats_2025_2026.csv'):
        team_stats = pd.read_csv('data/nba_team_stats_2025_2026.csv')
        completed = pd.read_csv('data/nba_completed_games_2025_2026.csv')
        
        engine = MonteCarloEngineV31(team_stats, completed, n_simulations=1000)
        
        # Test a game
        result = engine.simulate_game(
            away_team='San Antonio Spurs',
            home_team='Denver Nuggets',
            minimum_line=214.5
        )
        
        print(f"\nTest Game: {result['game']}")
        print(f"  Expected: {result['away_expected']:.1f} + {result['home_expected']:.1f} = {result['total_expected']:.1f}")
        print(f"  Simulated Avg: {result['avg_simulated_total']}")
        print(f"  MC Probability: {result['mc_probability']}%")
        print(f"  Flags: {result['flag_count']}")
        print(f"  Decision: {result['mc_decision']}")
        print(f"  Floor Safe: {result['floor_safe']}")
        
        if result['risk_flags']:
            print(f"  Risk Flags:")
            for flag in result['risk_flags']:
                print(f"    - {flag}")
    else:
        print("No test data available")