"""
Rest Days Calculator
====================
Calculates rest days and detects back-to-back games

Back-to-back games = teams tired = lower scoring
Rested teams = better offense
"""

import pandas as pd
from datetime import datetime, timedelta


class RestDaysCalculator:
    """Calculate team rest and fatigue"""
    
    def __init__(self, completed_games_df):
        """
        Args:
            completed_games_df: DataFrame with all completed games
        """
        self.games = completed_games_df
        
        # Convert date column
        if 'Date' in self.games.columns:
            self.games['Date'] = pd.to_datetime(self.games['Date'])
    
    def get_last_game_date(self, team_name, before_date):
        """Get the date of team's last game before given date"""
        # If no completed games, return None
        if len(self.games) == 0:
            return None
        
        # Find games where team played before this date
        team_games = self.games[
            ((self.games['Visitor'] == team_name) | 
             (self.games['Home'] == team_name)) &
            (self.games['Date'] < before_date)
        ].sort_values('Date')
        
        if len(team_games) == 0:
            return None
        
        return team_games.iloc[-1]['Date']
    
    def calculate_rest_days(self, team_name, game_date):
        """
        Calculate days of rest before this game
        
        Returns:
            {
                'team': team_name,
                'game_date': game_date,
                'last_game_date': last_date,
                'rest_days': 2,
                'is_b2b': False,
                'fatigue_level': 'RESTED'
            }
        """
        game_date = pd.to_datetime(game_date)
        
        # Remove timezone info for comparison with completed games (which have no TZ)
        if game_date.tz is not None:
            game_date = game_date.tz_localize(None)
        
        last_game = self.get_last_game_date(team_name, game_date)
        
        if last_game is None:
            # First game or no data
            return {
                'team': team_name,
                'game_date': game_date,
                'last_game_date': None,
                'rest_days': 99,  # Well rested
                'is_b2b': False,
                'fatigue_level': 'RESTED'
            }
        
        # Calculate days between games
        rest_days = (game_date - last_game).days
        
        # Determine fatigue level
        if rest_days <= 1:
            is_b2b = True
            fatigue_level = 'B2B'  # Back-to-back = tired
        elif rest_days == 2:
            is_b2b = False
            fatigue_level = 'SHORT_REST'
        else:
            is_b2b = False
            fatigue_level = 'RESTED'
        
        return {
            'team': team_name,
            'game_date': game_date,
            'last_game_date': last_game,
            'rest_days': rest_days,
            'is_b2b': is_b2b,
            'fatigue_level': fatigue_level
        }
    
    def analyze_matchup_rest(self, away_team, home_team, game_date):
        """
        Analyze rest situation for both teams
        
        Returns combined rest score (0-10 points)
        """
        away_rest = self.calculate_rest_days(away_team, game_date)
        home_rest = self.calculate_rest_days(home_team, game_date)
        
        # Scoring system
        # Both rested = 10 points (best case)
        # One B2B = 5 points (moderate concern)
        # Both B2B = 0 points (RED FLAG)
        
        if away_rest['is_b2b'] and home_rest['is_b2b']:
            combined_score = 0  # Both tired = low scoring game
            reason = "Both teams on back-to-back (fatigued)"
        elif away_rest['is_b2b'] or home_rest['is_b2b']:
            combined_score = 5  # One tired
            if away_rest['is_b2b']:
                reason = f"{away_team} on back-to-back"
            else:
                reason = f"{home_team} on back-to-back"
        else:
            combined_score = 10  # Both rested
            reason = f"Both teams rested ({away_rest['rest_days']}+ days)"
        
        return {
            'away_rest': away_rest,
            'home_rest': home_rest,
            'combined_score': combined_score,
            'reason': reason
        }


def main():
    """Test the calculator"""
    print("Rest Days Calculator - Ready")
    print("Use this in minimum_total_predictor.py")


if __name__ == "__main__":
    main()