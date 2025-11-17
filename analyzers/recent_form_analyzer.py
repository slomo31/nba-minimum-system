"""
Recent Form Analyzer
====================
Analyzes last 6 games to detect hot/cold scoring trends

Hot team = scoring MORE than expected
Cold team = scoring LESS than expected
"""

import pandas as pd
import numpy as np


class RecentFormAnalyzer:
    """Analyze team scoring trends over last 6 games"""
    
    def __init__(self, completed_games_df, team_stats_df):
        """
        Args:
            completed_games_df: DataFrame with all completed games
            team_stats_df: DataFrame with team season stats (PPG)
        """
        self.games = completed_games_df
        self.team_stats = team_stats_df
        
    def get_team_last_n_games(self, team_name, n=6):
        """Get last N games for a team"""
        # Find games where team played
        team_games = self.games[
            (self.games['Visitor'] == team_name) | 
            (self.games['Home'] == team_name)
        ].copy()
        
        # Get their scores
        team_games['Team_Score'] = team_games.apply(
            lambda row: row['Visitor_PTS'] if row['Visitor'] == team_name else row['Home_PTS'],
            axis=1
        )
        
        # Get last N games
        last_n = team_games.tail(n)
        
        return last_n['Team_Score'].tolist()
    
    def analyze_team_form(self, team_name):
        """
        Analyze if team is hot or cold
        
        Returns:
            {
                'team': team_name,
                'last_6_scores': [115, 128, 119, ...],
                'avg_last_6': 121.3,
                'season_ppg': 118.5,
                'diff': +2.8,  (scoring 2.8 more than season avg)
                'is_hot': True,
                'trend': 'HOT',
                'form_score': 20  (0-20 points for scoring system)
            }
        """
        # Get last 6 game scores
        recent_scores = self.get_team_last_n_games(team_name, n=6)
        
        if len(recent_scores) < 3:
            # Not enough data
            return {
                'team': team_name,
                'last_6_scores': recent_scores,
                'avg_last_6': None,
                'season_ppg': None,
                'diff': 0,
                'is_hot': False,
                'trend': 'INSUFFICIENT_DATA',
                'form_score': 0
            }
        
        # Calculate recent average
        avg_recent = np.mean(recent_scores)
        
        # Get season PPG
        team_data = self.team_stats[self.team_stats['Team'] == team_name]
        if len(team_data) == 0:
            season_ppg = avg_recent
        else:
            season_ppg = team_data['PPG'].values[0]
        
        # Calculate difference
        diff = avg_recent - season_ppg
        
        # Determine if hot/cold
        if diff >= 5:
            trend = 'HOT'
            is_hot = True
            form_score = 20  # Max points
        elif diff >= 3:
            trend = 'WARM'
            is_hot = True
            form_score = 12
        elif diff <= -5:
            trend = 'COLD'
            is_hot = False
            form_score = 0  # Red flag
        elif diff <= -3:
            trend = 'COOL'
            is_hot = False
            form_score = 5
        else:
            trend = 'NEUTRAL'
            is_hot = False
            form_score = 8
        
        return {
            'team': team_name,
            'last_6_scores': recent_scores,
            'avg_last_6': round(avg_recent, 1),
            'season_ppg': round(season_ppg, 1),
            'diff': round(diff, 1),
            'is_hot': is_hot,
            'trend': trend,
            'form_score': form_score
        }
    
    def analyze_matchup_form(self, away_team, home_team):
        """
        Analyze form for both teams in a matchup
        
        Returns combined form score (0-20 points)
        """
        away_form = self.analyze_team_form(away_team)
        home_form = self.analyze_team_form(home_team)
        
        # Combined scoring
        if away_form['is_hot'] and home_form['is_hot']:
            combined_score = 20  # Both hot = easy minimum
            reason = f"Both teams hot ({away_form['trend']}/{home_form['trend']})"
        elif away_form['is_hot'] or home_form['is_hot']:
            combined_score = 12  # One hot
            if away_form['is_hot']:
                reason = f"{away_team} hot ({away_form['trend']})"
            else:
                reason = f"{home_team} hot ({home_form['trend']})"
        elif away_form['trend'] == 'COLD' or home_form['trend'] == 'COLD':
            combined_score = 0  # RED FLAG - one team cold
            if away_form['trend'] == 'COLD':
                reason = f"{away_team} cold (scoring slump)"
            else:
                reason = f"{home_team} cold (scoring slump)"
        else:
            combined_score = 8  # Neutral
            reason = "Both teams neutral form"
        
        return {
            'away_form': away_form,
            'home_form': home_form,
            'combined_score': combined_score,
            'reason': reason
        }


def main():
    """Test the analyzer"""
    # This is just a test - real usage is in the predictor
    print("Recent Form Analyzer - Ready")
    print("Use this in minimum_total_predictor.py")


if __name__ == "__main__":
    main()
