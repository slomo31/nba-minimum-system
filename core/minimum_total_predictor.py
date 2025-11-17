"""
Minimum Total Predictor - MAIN ENGINE
======================================
Calculates probability that a game goes OVER the minimum alternate total

Uses all factors:
- Offensive Power (30 pts)
- Game Pace (25 pts)
- Recent Form (20 pts)
- Buffer Analysis (15 pts)
- Rest/Fatigue (10 pts)

Total: 100 points = 100% confidence
"""

import pandas as pd
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analyzers.recent_form_analyzer import RecentFormAnalyzer
from analyzers.rest_days_calculator import RestDaysCalculator
from analyzers.pace_analyzer import PaceAnalyzer


class MinimumTotalPredictor:
    """Main prediction engine"""
    
    def __init__(self, team_stats_df, completed_games_df):
        """
        Args:
            team_stats_df: Current season team stats
            completed_games_df: Completed games for form/rest analysis
        """
        self.team_stats = team_stats_df
        self.completed_games = completed_games_df
        
        # Initialize analyzers
        self.form_analyzer = RecentFormAnalyzer(completed_games_df, team_stats_df)
        self.rest_calculator = RestDaysCalculator(completed_games_df)
        self.pace_analyzer = PaceAnalyzer(team_stats_df)
    
    def get_team_stats(self, team_name):
        """Get team stats"""
        team_data = self.team_stats[self.team_stats['Team'] == team_name]
        
        if len(team_data) == 0:
            return None
        
        return team_data.iloc[0]
    
    def calculate_offensive_power_score(self, away_team, home_team):
        """
        Factor 1: Offensive Power (30 points max)
        
        Elite offense (avg ORtg >= 116) = 30 pts
        Strong (114+) = 20 pts
        Above avg (112+) = 10 pts
        Weak (<110) = 0 pts (RED FLAG)
        """
        away_stats = self.get_team_stats(away_team)
        home_stats = self.get_team_stats(home_team)
        
        if away_stats is None or home_stats is None:
            return {'score': 0, 'reason': 'Missing team stats'}
        
        avg_ortg = (away_stats['ORtg'] + home_stats['ORtg']) / 2
        
        if avg_ortg >= 116:
            score = 30
            reason = f"Elite offense (avg ORtg: {avg_ortg:.1f})"
        elif avg_ortg >= 114:
            score = 20
            reason = f"Strong offense (avg ORtg: {avg_ortg:.1f})"
        elif avg_ortg >= 112:
            score = 10
            reason = f"Above-avg offense (avg ORtg: {avg_ortg:.1f})"
        else:
            score = 0
            reason = f"Weak offense (avg ORtg: {avg_ortg:.1f}) - RED FLAG"
        
        return {'score': score, 'reason': reason, 'ortg': avg_ortg}
    
    def calculate_buffer_score(self, away_team, home_team, minimum_total):
        """
        Factor 4: Buffer Analysis (15 points max)
        
        How much higher teams average vs minimum
        
        ADJUSTED THRESHOLDS (less strict based on diagnostic):
        Buffer 20+ = 15 pts (strong safety margin)
        Buffer 15+ = 10 pts (good margin)
        Buffer 10+ = 7 pts (moderate margin)
        Buffer 5+ = 3 pts (small margin)
        Buffer <5 = 0 pts (too tight)
        """
        away_stats = self.get_team_stats(away_team)
        home_stats = self.get_team_stats(home_team)
        
        if away_stats is None or home_stats is None:
            return {'score': 0, 'reason': 'Missing team stats'}
        
        combined_avg = away_stats['PPG'] + home_stats['PPG']
        buffer = combined_avg - minimum_total
        
        if buffer >= 20:
            score = 15
            reason = f"Strong buffer ({buffer:.1f} pts above minimum)"
        elif buffer >= 15:
            score = 10
            reason = f"Good buffer ({buffer:.1f} pts above minimum)"
        elif buffer >= 10:
            score = 7
            reason = f"Moderate buffer ({buffer:.1f} pts above minimum)"
        elif buffer >= 5:
            score = 3
            reason = f"Small buffer ({buffer:.1f} pts)"
        else:
            score = 0
            reason = f"Buffer too tight ({buffer:.1f} pts) - SKIP"
        
        return {'score': score, 'reason': reason, 'buffer': buffer}
    
    def predict_game(self, away_team, home_team, minimum_total, game_date):
        """
        Main prediction function
        
        Returns:
            {
                'away_team': away_team,
                'home_team': home_team,
                'minimum_total': minimum_total,
                'total_score': 92,  # Out of 100
                'confidence': 92%,
                'factors': {
                    'offensive_power': {'score': 30, 'reason': '...'},
                    'pace': {'score': 25, 'reason': '...'},
                    'form': {'score': 20, 'reason': '...'},
                    'buffer': {'score': 15, 'reason': '...'},
                    'rest': {'score': 10, 'reason': '...'}
                },
                'reasoning': ['Elite offense', 'Fast pace', ...]
            }
        """
        factors = {}
        reasoning = []
        
        # Factor 1: Offensive Power (30 pts)
        offensive = self.calculate_offensive_power_score(away_team, home_team)
        factors['offensive_power'] = offensive
        if offensive['score'] > 0:
            reasoning.append(offensive['reason'])
        
        # Factor 2: Pace (25 pts)
        pace = self.pace_analyzer.project_game_pace(away_team, home_team)
        factors['pace'] = pace
        if pace['pace_score'] > 0:
            reasoning.append(pace['reason'])
        
        # Factor 3: Recent Form (20 pts)
        form = self.form_analyzer.analyze_matchup_form(away_team, home_team)
        factors['form'] = form
        if form['combined_score'] > 0:
            reasoning.append(form['reason'])
        
        # Factor 4: Buffer (15 pts)
        buffer = self.calculate_buffer_score(away_team, home_team, minimum_total)
        factors['buffer'] = buffer
        if buffer['score'] > 0:
            reasoning.append(buffer['reason'])
        
        # Factor 5: Rest (10 pts)
        rest = self.rest_calculator.analyze_matchup_rest(away_team, home_team, game_date)
        factors['rest'] = rest
        if rest['combined_score'] > 0:
            reasoning.append(rest['reason'])
        
        # Calculate total score
        total_score = (
            offensive['score'] +
            pace['pace_score'] +
            form['combined_score'] +
            buffer['score'] +
            rest['combined_score']
        )
        
        # Confidence = score / 100
        confidence = total_score
        
        return {
            'away_team': away_team,
            'home_team': home_team,
            'minimum_total': minimum_total,
            'total_score': total_score,
            'confidence': confidence,
            'factors': factors,
            'reasoning': reasoning
        }
    
    def predict_all_games(self, upcoming_games_df):
        """
        Predict for all upcoming games
        
        Args:
            upcoming_games_df: DataFrame with columns:
                - away_team
                - home_team
                - minimum_total
                - minimum_odds
                - game_time
        
        Returns:
            List of predictions
        """
        predictions = []
        
        for _, game in upcoming_games_df.iterrows():
            prediction = self.predict_game(
                away_team=game['away_team'],
                home_team=game['home_team'],
                minimum_total=game['minimum_total'],
                game_date=game['game_time']
            )
            
            # Add game info
            prediction['game_time'] = game['game_time']
            prediction['minimum_odds'] = game['minimum_odds']
            
            predictions.append(prediction)
        
        return predictions


def main():
    """Test the predictor"""
    print("Minimum Total Predictor - Ready")
    print("This is the main engine - use in master_workflow.py")


if __name__ == "__main__":
    main()