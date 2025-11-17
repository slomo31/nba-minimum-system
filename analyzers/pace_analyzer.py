"""
Pace Analyzer
=============
Projects game pace and impact on scoring

Fast pace = more possessions = more points
Slow pace = fewer possessions = fewer points (risky for minimum)
"""

import pandas as pd


class PaceAnalyzer:
    """Analyze game pace projections"""
    
    def __init__(self, team_stats_df):
        """
        Args:
            team_stats_df: DataFrame with team Pace stats
        """
        self.team_stats = team_stats_df
    
    def get_team_pace(self, team_name):
        """Get team's pace"""
        team_data = self.team_stats[self.team_stats['Team'] == team_name]
        
        if len(team_data) == 0:
            return 100.0  # League average
        
        return team_data['Pace'].values[0]
    
    def project_game_pace(self, away_team, home_team):
        """
        Project game pace (average of both teams)
        
        Returns pace score (0-25 points)
        """
        away_pace = self.get_team_pace(away_team)
        home_pace = self.get_team_pace(home_team)
        
        avg_pace = (away_pace + home_pace) / 2
        
        # Scoring system (ADJUSTED - less strict based on diagnostic)
        # Fast pace (100+) = 25 points (easy minimum)
        # Above average pace (98+) = 15 points
        # Average pace (96+) = 8 points
        # Slow pace (<96) = 0 points (RED FLAG)
        
        if avg_pace >= 100:
            score = 25
            reason = f"Fast pace ({avg_pace:.1f})"
        elif avg_pace >= 98:
            score = 15
            reason = f"Above average pace ({avg_pace:.1f})"
        elif avg_pace >= 96:
            score = 8
            reason = f"Average pace ({avg_pace:.1f})"
        else:
            score = 0  # RED FLAG
            reason = f"Slow pace ({avg_pace:.1f}) - risky"
        
        return {
            'away_pace': round(away_pace, 1),
            'home_pace': round(home_pace, 1),
            'projected_pace': round(avg_pace, 1),
            'pace_score': score,
            'reason': reason
        }


def main():
    print("Pace Analyzer - Ready")


if __name__ == "__main__":
    main()