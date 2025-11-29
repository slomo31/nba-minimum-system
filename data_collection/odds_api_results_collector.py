"""
NBA Game Results Collector - Using The Odds API
================================================
Fetches completed game scores in real-time (much faster than BBRef)

Uses your existing Odds API subscription to get:
- Completed game scores
- Final totals
- Updates within minutes of games ending
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import os
import sys

# Add parent directory to path for config imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from config.api_config import ODDS_API_KEY, BASE_URL, SPORT
except ImportError:
    # Fallback if config not found
    ODDS_API_KEY = os.getenv('ODDS_API_KEY', '')
    BASE_URL = "https://api.the-odds-api.com/v4"
    SPORT = "basketball_nba"


class OddsAPIResultsCollector:
    """Collects game results using The Odds API scores endpoint"""
    
    def __init__(self, api_key=None):
        self.api_key = api_key or ODDS_API_KEY
        self.base_url = BASE_URL
        self.sport = SPORT
        
    def fetch_scores(self, days_back=3):
        """
        Fetch completed game scores
        
        Args:
            days_back: How many days back to fetch (default 3)
            
        Returns:
            DataFrame with completed games
        """
        print("\n" + "=" * 70)
        print("🏀 FETCHING NBA SCORES (The Odds API)")
        print("=" * 70)
        
        try:
            # The Odds API scores endpoint
            url = f"{self.base_url}/sports/{self.sport}/scores"
            
            params = {
                'apiKey': self.api_key,
                'daysFrom': days_back  # Get games from last N days
            }
            
            response = requests.get(url, params=params, timeout=30)
            
            # Check API usage
            remaining = response.headers.get('x-requests-remaining', 'Unknown')
            used = response.headers.get('x-requests-used', 'Unknown')
            print(f"  API Requests - Used: {used} | Remaining: {remaining}")
            
            if response.status_code != 200:
                print(f"  [ERROR] API returned {response.status_code}")
                print(f"  {response.text}")
                return None
            
            games = response.json()
            
            if not games:
                print("  [WARNING] No games returned")
                return None
            
            print(f"  ✓ Found {len(games)} games")
            
            # Parse completed games
            completed = []
            pending = 0
            
            for game in games:
                # Check if game is completed
                if not game.get('completed', False):
                    pending += 1
                    continue
                
                # Get scores
                scores = game.get('scores', [])
                if not scores or len(scores) < 2:
                    continue
                
                # Parse team scores
                home_team = game.get('home_team', '')
                away_team = game.get('away_team', '')
                
                home_score = None
                away_score = None
                
                for score in scores:
                    if score.get('name') == home_team:
                        home_score = int(score.get('score', 0))
                    elif score.get('name') == away_team:
                        away_score = int(score.get('score', 0))
                
                if home_score is None or away_score is None:
                    continue
                
                # Parse game time
                commence_time = game.get('commence_time', '')
                if commence_time:
                    game_dt = datetime.fromisoformat(commence_time.replace('Z', '+00:00'))
                    game_dt_et = game_dt.astimezone(ZoneInfo('America/New_York'))
                    date_str = game_dt_et.strftime('%a, %b %d, %Y')
                else:
                    date_str = 'Unknown'
                
                total_points = home_score + away_score
                
                completed.append({
                    'Date': date_str,
                    'Visitor': away_team,
                    'Visitor_PTS': float(away_score),
                    'Home': home_team,
                    'Home_PTS': float(home_score),
                    'Total_Points': float(total_points),
                    'game_id': game.get('id', ''),
                    'commence_time': commence_time
                })
            
            print(f"  ✓ Completed games: {len(completed)}")
            print(f"  ⏳ Pending/In-progress: {pending}")
            
            if completed:
                df = pd.DataFrame(completed)
                return df
            
            return None
            
        except Exception as e:
            print(f"  [ERROR] {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def update_completed_games(self, output_file='data/nba_completed_games_2025_2026.csv'):
        """
        Update the completed games CSV with latest scores
        
        Merges new scores with existing data, avoiding duplicates
        """
        print("\n" + "=" * 70)
        print("📊 UPDATING COMPLETED GAMES")
        print("=" * 70)
        
        # Fetch latest scores (use 3 days to stay within API limits)
        new_games = self.fetch_scores(days_back=3)
        
        if new_games is None or len(new_games) == 0:
            print("  [WARNING] No new games to add")
            return False
        
        # Load existing data
        if os.path.exists(output_file):
            existing = pd.read_csv(output_file)
            print(f"  ✓ Loaded {len(existing)} existing games")
        else:
            existing = pd.DataFrame(columns=['Date', 'Visitor', 'Visitor_PTS', 'Home', 'Home_PTS', 'Total_Points'])
            print("  ✓ Creating new file")
        
        # Create unique key for matching (teams + date)
        def make_key(row):
            # Normalize team names and date for matching
            visitor = str(row.get('Visitor', '')).strip()
            home = str(row.get('Home', '')).strip()
            date = str(row.get('Date', '')).strip()
            return f"{visitor}|{home}|{date}"
        
        existing['_key'] = existing.apply(make_key, axis=1)
        new_games['_key'] = new_games.apply(make_key, axis=1)
        
        # Find truly new games
        existing_keys = set(existing['_key'].tolist())
        new_mask = ~new_games['_key'].isin(existing_keys)
        truly_new = new_games[new_mask]
        
        print(f"  ✓ New games to add: {len(truly_new)}")
        
        if len(truly_new) > 0:
            # Show new games
            print("\n  NEW GAMES:")
            for _, row in truly_new.iterrows():
                print(f"    {row['Date']}: {row['Visitor']} ({row['Visitor_PTS']:.0f}) @ {row['Home']} ({row['Home_PTS']:.0f}) = {row['Total_Points']:.0f}")
            
            # Combine and save
            # Keep only standard columns
            cols_to_keep = ['Date', 'Visitor', 'Visitor_PTS', 'Home', 'Home_PTS', 'Total_Points']
            
            existing_clean = existing[cols_to_keep] if all(c in existing.columns for c in cols_to_keep) else existing.drop(columns=['_key'], errors='ignore')
            new_clean = truly_new[cols_to_keep]
            
            combined = pd.concat([existing_clean, new_clean], ignore_index=True)
            
            # Remove any duplicates (same teams, same date)
            combined = combined.drop_duplicates(subset=['Visitor', 'Home', 'Date'], keep='last')
            
            # Sort by date (most recent first for display, but keep all)
            combined.to_csv(output_file, index=False)
            print(f"\n  ✓ Saved {len(combined)} total games to {output_file}")
            
            return True
        else:
            print("  No new games to add")
            return False
    
    def show_recent_games(self, n=10):
        """Display most recent completed games"""
        print("\n" + "=" * 70)
        print(f"📋 LAST {n} COMPLETED GAMES")
        print("=" * 70)
        
        games = self.fetch_scores(days_back=3)
        
        if games is None or len(games) == 0:
            print("  No completed games found")
            return
        
        # Sort by commence_time descending
        if 'commence_time' in games.columns:
            games = games.sort_values('commence_time', ascending=False)
        
        print(f"\n  {'Date':<20} {'Away':<25} {'Home':<25} {'Total':<8}")
        print("  " + "-" * 80)
        
        for _, row in games.head(n).iterrows():
            date = row.get('Date', '?')[:20]
            away = f"{row['Visitor']} ({row['Visitor_PTS']:.0f})"
            home = f"{row['Home']} ({row['Home_PTS']:.0f})"
            total = row['Total_Points']
            print(f"  {date:<20} {away:<25} {home:<25} {total:<8.0f}")


def main():
    """Main function to collect results"""
    print("\n" + "=" * 70)
    print("🏀 NBA GAME RESULTS COLLECTOR (Odds API)")
    print("=" * 70)
    
    collector = OddsAPIResultsCollector()
    
    # Show recent games
    collector.show_recent_games(15)
    
    # Update the CSV
    collector.update_completed_games()
    
    print("\n" + "=" * 70)
    print("✅ DONE!")
    print("=" * 70)


if __name__ == "__main__":
    main()