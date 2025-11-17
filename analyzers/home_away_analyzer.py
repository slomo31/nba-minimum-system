"""
Home/Away Analyzer
==================
Analyzes home court advantage impact on scoring
"""

import pandas as pd
import numpy as np


class HomeAwayAnalyzer:
    """Analyze home/away splits"""
    
    def __init__(self, completed_games_df):
        self.games = completed_games_df
    
    def get_team_home_away_splits(self, team_name):
        """Calculate team's scoring at home vs away"""
        # Home games
        home_games = self.games[self.games['Home'] == team_name]
        home_ppg = home_games['Home_PTS'].mean() if len(home_games) > 0 else None
        
        # Away games
        away_games = self.games[self.games['Visitor'] == team_name]
        away_ppg = away_games['Visitor_PTS'].mean() if len(away_games) > 0 else None
        
        return {
            'team': team_name,
            'home_ppg': round(home_ppg, 1) if home_ppg else None,
            'away_ppg': round(away_ppg, 1) if away_ppg else None,
            'home_advantage': round(home_ppg - away_ppg, 1) if (home_ppg and away_ppg) else 0
        }
    
    def analyze_matchup(self, away_team, home_team):
        """
        Minimal impact on minimum total predictions
        Home court helps but doesn't change minimum much
        
        Returns: Small adjustment factor
        """
        away_splits = self.get_team_home_away_splits(away_team)
        home_splits = self.get_team_home_away_splits(home_team)
        
        # Home teams typically score +2-3 more
        # This is already baked into PPG, so minimal adjustment needed
        
        return {
            'away_splits': away_splits,
            'home_splits': home_splits,
            'note': 'Home advantage minimal for minimum totals'
        }


def main():
    print("Home/Away Analyzer - Ready")


if __name__ == "__main__":
    main()
