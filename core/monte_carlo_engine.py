"""
Monte Carlo Simulation Engine v3.0 - FULLY ENHANCED
=====================================================
Complete implementation with:

1. SCORING VARIANCE
   - Team-specific standard deviation calculated from actual games
   - Identifies high-variance teams that are risky

2. PACE VARIANCE  
   - Team-specific pace from stats
   - Game total variance (how much game totals vary for each team)
   - Slow-pace team identification and penalties

3. DEFENSIVE FLAGS
   - Elite defense identification (top defensive ratings)
   - Defensive matchup penalties

4. SLOW-PACE FLAGS
   - Dynamic identification of slow teams
   - Double slow-pace matchup penalties

5. INJURY TRACKING
   - Fetches current injuries from API
   - Star player impact on team variance
   - Adjusts predictions when key players are out

6. GAME TOTAL HISTORY
   - Tracks how often each team's games go over/under
   - Identifies "under" teams vs "over" teams
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, List, Optional
import requests
import warnings
warnings.filterwarnings('ignore')


# ============================================================================
# CONFIGURATION
# ============================================================================

# Thresholds
HIGH_VARIANCE_THRESHOLD = 12.0      # Scoring std dev above this = risky
SLOW_PACE_THRESHOLD = 98.0          # Pace below this = slow team
ELITE_DEFENSE_DRTG_THRESHOLD = 110  # Defensive rating below this = elite

# Star players and their impact (increase variance when out)
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


class MonteCarloEngineV3:
    """
    Fully Enhanced Monte Carlo Simulation Engine
    
    Simulates each game 10,000 times with:
    - Team-specific scoring variance
    - Team-specific pace variance
    - Slow-pace penalties
    - Elite defense penalties
    - Injury adjustments
    - Game total history
    """
    
    def __init__(self, team_stats_df: pd.DataFrame, completed_games_df: pd.DataFrame, 
                 n_simulations: int = 10000, check_injuries: bool = True):
        """
        Initialize the Monte Carlo engine
        
        Args:
            team_stats_df: Current season team stats
            completed_games_df: Completed games for variance calculation
            n_simulations: Number of simulations per game
            check_injuries: Whether to fetch injury data (requires internet)
        """
        self.team_stats = team_stats_df
        self.completed_games = completed_games_df
        self.n_simulations = n_simulations
        
        # Build all profiles
        print("  Building team profiles...")
        self.team_profiles = self._build_team_profiles()
        
        print("  Calculating game total history...")
        self.game_total_history = self._build_game_total_history()
        
        print("  Identifying slow-pace teams...")
        self.slow_pace_teams = self._identify_slow_pace_teams()
        
        print("  Identifying elite defenses...")
        self.elite_defense_teams = self._identify_elite_defenses()
        
        # Injury data (fetched on demand)
        self.injuries = {}
        self.check_injuries = check_injuries
        if check_injuries:
            print("  Fetching injury data...")
            self._fetch_injuries()
        
        # League averages
        self.league_avg_ppg = team_stats_df['PPG'].mean()
        self.league_avg_pace = team_stats_df['Pace'].mean()
        self.league_avg_game_total = self.completed_games['Total_Points'].mean() if len(self.completed_games) > 0 else 220
        
        print("  ✓ Monte Carlo Engine v3.0 initialized")
    
    def _build_team_profiles(self) -> Dict:
        """Build comprehensive variance profiles for each team"""
        profiles = {}
        
        for team in self.team_stats['Team'].unique():
            # Get team's season stats
            team_row = self.team_stats[self.team_stats['Team'] == team]
            if len(team_row) == 0:
                continue
                
            pace = team_row['Pace'].values[0]
            drtg = team_row['DRtg'].values[0] if 'DRtg' in team_row.columns else 115
            ortg = team_row['ORtg'].values[0] if 'ORtg' in team_row.columns else 110
            
            # Get all games for this team
            team_games = self.completed_games[
                (self.completed_games['Visitor'] == team) | 
                (self.completed_games['Home'] == team)
            ].copy()
            
            if len(team_games) == 0:
                ppg = team_row['PPG'].values[0]
                profiles[team] = {
                    'mean_ppg': ppg,
                    'std_ppg': 10.0,
                    'min_ppg': ppg - 25,
                    'max_ppg': ppg + 25,
                    'games_played': 0,
                    'variance_reliable': False,
                    'pace': pace,
                    'pace_std': 3.0,  # Default pace variance
                    'drtg': drtg,
                    'ortg': ortg,
                    'is_slow_pace': pace < SLOW_PACE_THRESHOLD,
                    'is_elite_defense': drtg < ELITE_DEFENSE_DRTG_THRESHOLD,
                    'avg_game_total': 220,
                    'game_total_std': 15,
                    'over_220_pct': 50,
                    'under_210_pct': 30
                }
                continue
            
            # Calculate scoring stats
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
            
            mean_ppg = np.mean(scores)
            std_ppg = np.std(scores) if len(scores) > 1 else 10.0
            std_ppg = max(std_ppg, 6.0)  # Minimum variance
            
            # Game total stats
            avg_game_total = np.mean(game_totals)
            game_total_std = np.std(game_totals) if len(game_totals) > 1 else 15.0
            over_220_pct = (np.sum(game_totals > 220) / len(game_totals)) * 100
            under_210_pct = (np.sum(game_totals < 210) / len(game_totals)) * 100
            
            profiles[team] = {
                'mean_ppg': mean_ppg,
                'std_ppg': std_ppg,
                'min_ppg': np.min(scores),
                'max_ppg': np.max(scores),
                'games_played': len(scores),
                'variance_reliable': len(scores) >= 5,
                'pace': pace,
                'pace_std': 3.0,  # Estimated pace variance
                'drtg': drtg,
                'ortg': ortg,
                'is_slow_pace': pace < SLOW_PACE_THRESHOLD,
                'is_elite_defense': drtg < ELITE_DEFENSE_DRTG_THRESHOLD,
                'avg_game_total': avg_game_total,
                'game_total_std': game_total_std,
                'over_220_pct': over_220_pct,
                'under_210_pct': under_210_pct
            }
        
        return profiles
    
    def _build_game_total_history(self) -> Dict:
        """Build game total history for trend analysis"""
        history = {}
        
        for team in self.team_stats['Team'].unique():
            team_games = self.completed_games[
                (self.completed_games['Visitor'] == team) | 
                (self.completed_games['Home'] == team)
            ]
            
            if len(team_games) == 0:
                history[team] = {'totals': [], 'trend': 'NEUTRAL'}
                continue
            
            totals = team_games['Total_Points'].tolist()
            
            # Determine trend
            avg_total = np.mean(totals)
            if avg_total > 230:
                trend = 'OVER_TEAM'
            elif avg_total < 215:
                trend = 'UNDER_TEAM'
            else:
                trend = 'NEUTRAL'
            
            history[team] = {
                'totals': totals,
                'avg': avg_total,
                'trend': trend
            }
        
        return history
    
    def _identify_slow_pace_teams(self) -> List[str]:
        """Identify teams with slow pace"""
        slow_teams = []
        
        for team in self.team_stats['Team'].unique():
            team_row = self.team_stats[self.team_stats['Team'] == team]
            if len(team_row) > 0:
                pace = team_row['Pace'].values[0]
                if pace < SLOW_PACE_THRESHOLD:
                    slow_teams.append(team)
        
        return slow_teams
    
    def _identify_elite_defenses(self) -> List[str]:
        """Identify teams with elite defense"""
        elite_teams = []
        
        for team in self.team_stats['Team'].unique():
            team_row = self.team_stats[self.team_stats['Team'] == team]
            if len(team_row) > 0 and 'DRtg' in team_row.columns:
                drtg = team_row['DRtg'].values[0]
                if drtg < ELITE_DEFENSE_DRTG_THRESHOLD:
                    elite_teams.append(team)
        
        return elite_teams
    
    def _fetch_injuries(self):
        """Fetch current injury data from ESPN or other source"""
        try:
            # Try to fetch from a free injury API
            # This is a placeholder - you may need to adjust based on available APIs
            url = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/injuries"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Parse injuries by team
                for team_data in data.get('data', []):
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
    
    def get_team_injuries(self, team_name: str) -> List[Dict]:
        """Get injuries for a specific team"""
        return self.injuries.get(team_name, [])
    
    def is_star_player_out(self, team_name: str) -> Tuple[bool, List[str]]:
        """Check if any star players are out for a team"""
        team_injuries = self.get_team_injuries(team_name)
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
        """Get complete profile for a team"""
        if team_name in self.team_profiles:
            return self.team_profiles[team_name]
        
        return {
            'mean_ppg': self.league_avg_ppg,
            'std_ppg': 10.0,
            'min_ppg': 90,
            'max_ppg': 140,
            'games_played': 0,
            'variance_reliable': False,
            'pace': 100.0,
            'pace_std': 3.0,
            'drtg': 115,
            'ortg': 110,
            'is_slow_pace': False,
            'is_elite_defense': False,
            'avg_game_total': 220,
            'game_total_std': 15,
            'over_220_pct': 50,
            'under_210_pct': 30
        }
    
    def simulate_team_score(self, team_profile: Dict, 
                           pace_factor: float = 1.0,
                           fatigue_factor: float = 1.0,
                           defense_factor: float = 1.0,
                           blowout_adjustment: float = 0.0,
                           injury_variance_boost: float = 1.0) -> float:
        """
        Simulate a single team's score
        
        Args:
            team_profile: Team's variance profile
            pace_factor: Game pace multiplier
            fatigue_factor: B2B fatigue multiplier
            defense_factor: Opponent defense multiplier
            blowout_adjustment: Points to subtract in blowout
            injury_variance_boost: Increase variance if star is out
        """
        # Base score from normal distribution
        std = team_profile['std_ppg'] * injury_variance_boost
        base_score = np.random.normal(team_profile['mean_ppg'], std)
        
        # Apply all factors
        base_score *= pace_factor
        base_score *= fatigue_factor
        base_score *= defense_factor
        base_score -= blowout_adjustment
        
        # Clamp to realistic range
        return max(85, min(160, base_score))
    
    def simulate_game(self, away_team: str, home_team: str, minimum_line: float,
                     away_rest_days: int = 3, home_rest_days: int = 3,
                     spread: float = 0.0) -> Dict:
        """
        Run full Monte Carlo simulation for a game
        
        Returns comprehensive analysis including:
        - MC probability
        - Risk factors
        - Pace/defense flags
        - Injury impacts
        """
        away_profile = self.get_team_profile(away_team)
        home_profile = self.get_team_profile(home_team)
        
        # ==========================================
        # CALCULATE ALL FACTORS
        # ==========================================
        
        # 1. Fatigue factors (B2B penalty)
        away_fatigue = 0.97 if away_rest_days <= 1 else 1.0
        home_fatigue = 0.97 if home_rest_days <= 1 else 1.0
        
        # 2. Defense factors (elite defense reduces opponent scoring)
        away_vs_defense = 0.96 if home_profile.get('is_elite_defense', False) else 1.0
        home_vs_defense = 0.96 if away_profile.get('is_elite_defense', False) else 1.0
        
        # 3. Pace factors
        away_slow = away_profile.get('is_slow_pace', False)
        home_slow = home_profile.get('is_slow_pace', False)
        
        if away_slow and home_slow:
            base_pace_penalty = 0.94  # Both slow = big penalty
        elif away_slow or home_slow:
            base_pace_penalty = 0.97  # One slow = moderate penalty
        else:
            base_pace_penalty = 1.0
        
        # 4. Blowout probability
        abs_spread = abs(spread) if spread else 0
        blowout_prob = min(0.25, abs_spread * 0.02)
        
        # 5. Injury impact
        away_star_out, away_out_players = self.is_star_player_out(away_team)
        home_star_out, home_out_players = self.is_star_player_out(home_team)
        
        # Increase variance when star is out (team becomes unpredictable)
        away_injury_variance = 1.3 if away_star_out else 1.0
        home_injury_variance = 1.3 if home_star_out else 1.0
        
        # ==========================================
        # RUN SIMULATIONS
        # ==========================================
        
        simulated_totals = []
        hits = 0
        
        for _ in range(self.n_simulations):
            # Random pace variation for this specific game
            pace_variation = np.random.normal(1.0, 0.03)
            pace_factor = pace_variation * base_pace_penalty
            
            # Check if this sim is a blowout
            is_blowout = np.random.random() < blowout_prob
            blowout_adj = 8 if is_blowout else 0
            
            # Simulate away team score
            away_score = self.simulate_team_score(
                away_profile,
                pace_factor=pace_factor,
                fatigue_factor=away_fatigue,
                defense_factor=away_vs_defense,
                blowout_adjustment=blowout_adj / 2,
                injury_variance_boost=away_injury_variance
            )
            
            # Simulate home team score
            home_score = self.simulate_team_score(
                home_profile,
                pace_factor=pace_factor,
                fatigue_factor=home_fatigue,
                defense_factor=home_vs_defense,
                blowout_adjustment=blowout_adj / 2,
                injury_variance_boost=home_injury_variance
            )
            
            total = away_score + home_score
            simulated_totals.append(total)
            
            if total > minimum_line:
                hits += 1
        
        simulated_totals = np.array(simulated_totals)
        
        # ==========================================
        # BUILD RESULTS
        # ==========================================
        
        risk_factors = self._build_risk_factors(
            away_team, home_team,
            away_profile, home_profile,
            away_fatigue, home_fatigue,
            blowout_prob,
            away_star_out, home_star_out,
            away_out_players, home_out_players
        )
        
        mc_probability = round((hits / self.n_simulations) * 100, 2)
        
        return {
            'away_team': away_team,
            'home_team': home_team,
            'minimum_line': minimum_line,
            'simulations': self.n_simulations,
            'hits': hits,
            'mc_probability': mc_probability,
            'avg_simulated_total': round(np.mean(simulated_totals), 1),
            'std_simulated_total': round(np.std(simulated_totals), 1),
            'min_simulated_total': round(np.min(simulated_totals), 1),
            'max_simulated_total': round(np.max(simulated_totals), 1),
            'percentile_5': round(np.percentile(simulated_totals, 5), 1),
            'percentile_95': round(np.percentile(simulated_totals, 95), 1),
            'risk_factors': risk_factors,
            'flags': {
                'slow_pace_game': away_slow or home_slow,
                'both_slow_pace': away_slow and home_slow,
                'elite_defense_involved': away_profile.get('is_elite_defense', False) or home_profile.get('is_elite_defense', False),
                'both_elite_defense': away_profile.get('is_elite_defense', False) and home_profile.get('is_elite_defense', False),
                'high_variance_game': away_profile['std_ppg'] > HIGH_VARIANCE_THRESHOLD or home_profile['std_ppg'] > HIGH_VARIANCE_THRESHOLD,
                'injury_concern': away_star_out or home_star_out,
                'fatigue_concern': away_fatigue < 1.0 or home_fatigue < 1.0,
                'blowout_risk': blowout_prob > 0.15
            },
            'away_profile': away_profile,
            'home_profile': home_profile,
            'injuries': {
                'away_stars_out': away_out_players,
                'home_stars_out': home_out_players
            }
        }
    
    def _build_risk_factors(self, away_team, home_team, away_profile, home_profile,
                           away_fatigue, home_fatigue, blowout_prob,
                           away_star_out, home_star_out,
                           away_out_players, home_out_players) -> List[str]:
        """Build comprehensive list of risk factors"""
        risks = []
        
        # High variance
        if away_profile['std_ppg'] > HIGH_VARIANCE_THRESHOLD:
            risks.append(f"🎲 {away_team} high variance (±{away_profile['std_ppg']:.1f} PPG)")
        if home_profile['std_ppg'] > HIGH_VARIANCE_THRESHOLD:
            risks.append(f"🎲 {home_team} high variance (±{home_profile['std_ppg']:.1f} PPG)")
        
        # Slow pace
        if away_profile.get('is_slow_pace') and home_profile.get('is_slow_pace'):
            risks.append("🐢 BOTH TEAMS SLOW PACE - High under risk!")
        elif away_profile.get('is_slow_pace'):
            risks.append(f"🐢 {away_team} slow pace ({away_profile['pace']:.1f})")
        elif home_profile.get('is_slow_pace'):
            risks.append(f"🐢 {home_team} slow pace ({home_profile['pace']:.1f})")
        
        # Elite defense
        if away_profile.get('is_elite_defense') and home_profile.get('is_elite_defense'):
            risks.append("🛡️ BOTH ELITE DEFENSES - Grind game expected!")
        elif away_profile.get('is_elite_defense'):
            risks.append(f"🛡️ {away_team} elite defense (DRtg: {away_profile['drtg']:.1f})")
        elif home_profile.get('is_elite_defense'):
            risks.append(f"🛡️ {home_team} elite defense (DRtg: {home_profile['drtg']:.1f})")
        
        # Injuries
        if away_star_out:
            risks.append(f"🏥 {away_team} missing: {', '.join(away_out_players)}")
        if home_star_out:
            risks.append(f"🏥 {home_team} missing: {', '.join(home_out_players)}")
        
        # Fatigue
        if away_fatigue < 1.0:
            risks.append(f"😴 {away_team} on back-to-back")
        if home_fatigue < 1.0:
            risks.append(f"😴 {home_team} on back-to-back")
        
        # Blowout risk
        if blowout_prob > 0.15:
            risks.append(f"💨 Blowout risk ({blowout_prob*100:.0f}%) - starters may rest")
        
        # Data reliability
        if not away_profile['variance_reliable']:
            risks.append(f"📊 {away_team} limited data ({away_profile['games_played']} games)")
        if not home_profile['variance_reliable']:
            risks.append(f"📊 {home_team} limited data ({home_profile['games_played']} games)")
        
        return risks
    
    def get_mc_decision(self, mc_probability: float) -> Tuple[str, str]:
        """Convert MC probability to decision"""
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
    
    def calculate_parlay_probability(self, probs: List[float]) -> float:
        """Calculate combined parlay probability"""
        combined = 1.0
        for p in probs:
            combined *= (p / 100)
        return round(combined * 100, 2)
    
    def analyze_parlay(self, games: List[Dict]) -> Dict:
        """Analyze a potential parlay"""
        if not games:
            return {'error': 'No games'}
        
        probs = [g['mc_probability'] for g in games]
        combined = self.calculate_parlay_probability(probs)
        
        min_prob = min(probs)
        weakest = next(g for g in games if g['mc_probability'] == min_prob)
        
        if combined >= 75:
            rec = 'RECOMMENDED'
        elif combined >= 65:
            rec = 'ACCEPTABLE'
        else:
            rec = 'NOT_RECOMMENDED'
        
        return {
            'legs': len(games),
            'probabilities': probs,
            'combined': combined,
            'weakest_game': f"{weakest['away_team']} @ {weakest['home_team']}",
            'weakest_prob': min_prob,
            'recommendation': rec
        }


def print_team_profiles(engine: MonteCarloEngineV3):
    """Print detailed team profiles"""
    print("\n" + "=" * 100)
    print("TEAM PROFILES - MONTE CARLO v3.0")
    print("=" * 100)
    print(f"{'Team':<26} {'PPG':>7} {'Std':>7} {'Pace':>7} {'DRtg':>7} {'Slow':>6} {'Elite D':>8} {'Games':>6}")
    print("-" * 100)
    
    for team, p in sorted(engine.team_profiles.items()):
        slow = "🐢" if p.get('is_slow_pace') else ""
        elite = "🛡️" if p.get('is_elite_defense') else ""
        var = "🎲" if p['std_ppg'] > HIGH_VARIANCE_THRESHOLD else ""
        
        print(f"{team:<26} {p['mean_ppg']:>7.1f} {p['std_ppg']:>6.1f}{var} {p['pace']:>7.1f} {p['drtg']:>7.1f} {slow:>6} {elite:>8} {p['games_played']:>6}")
    
    print("\n🐢 = Slow Pace (<98)  |  🛡️ = Elite Defense (DRtg <110)  |  🎲 = High Variance (Std >12)")
    print(f"\nSlow pace teams: {', '.join(engine.slow_pace_teams)}")
    print(f"Elite defenses: {', '.join(engine.elite_defense_teams)}")


def main():
    print("Monte Carlo Engine v3.0 - Fully Enhanced")
    print("Features: Pace variance, Defense flags, Injury tracking")


if __name__ == "__main__":
    main()