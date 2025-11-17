"""
NBA Minimum Alternate Fetcher
==============================
Fetches ONLY the minimum DraftKings alternate total for each game

This is the key line we're betting: the safest over (lowest total)
"""

import requests
import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo
import time
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.api_config import *
from config.season_config import CURRENT_SEASON


class MinimumAlternateFetcher:
    """Fetches minimum alternate totals from DraftKings"""
    
    def __init__(self, api_key=ODDS_API_KEY):
        self.api_key = api_key
        self.base_url = BASE_URL
        self.sport = SPORT
        
    def test_api_connection(self):
        """Test API connection and show quota"""
        print("=" * 70)
        print("TESTING ODDS API CONNECTION")
        print("=" * 70)
        
        try:
            url = f"{self.base_url}/sports/{self.sport}/odds"
            params = {
                'apiKey': self.api_key,
                'regions': REGION,
                'markets': 'totals'
            }
            
            response = requests.get(url, params=params, timeout=API_TIMEOUT)
            
            if response.status_code == 200:
                remaining = response.headers.get('x-requests-remaining', 'Unknown')
                used = response.headers.get('x-requests-used', 'Unknown')
                
                print(f"âœ“ API Connected!")
                print(f"  Requests used: {used}")
                print(f"  Requests remaining: {remaining}")
                return True
            else:
                print(f"âœ— API Error: {response.status_code}")
                print(f"  {response.text}")
                return False
                
        except Exception as e:
            print(f"âœ— Connection error: {str(e)}")
            return False
    
    def get_upcoming_games(self):
        """Get list of upcoming games"""
        print("\n" + "=" * 70)
        print("FETCHING UPCOMING NBA GAMES")
        print("=" * 70)
        
        try:
            url = f"{self.base_url}/sports/{self.sport}/odds"
            params = {
                'apiKey': self.api_key,
                'regions': REGION,
                'markets': 'totals'
            }
            
            response = requests.get(url, params=params, timeout=API_TIMEOUT)
            
            if response.status_code != 200:
                print(f"âœ— Failed to fetch games: {response.status_code}")
                return None
            
            games = response.json()
            
            if not games:
                print("âš ï¸ No upcoming games found")
                return None
            
            print(f"âœ“ Found {len(games)} upcoming games\n")
            
            # Parse game info
            game_list = []
            for game in games:
                # Parse UTC time from API
                game_time_utc = datetime.fromisoformat(game['commence_time'].replace('Z', '+00:00'))
                
                # Convert to Eastern Time
                game_time_et = game_time_utc.astimezone(ZoneInfo('America/New_York'))
                
                game_list.append({
                    'event_id': game['id'],
                    'commence_time': game_time_et,  # Store as ET
                    'home_team': game['home_team'],
                    'away_team': game['away_team']
                })
            
            df = pd.DataFrame(game_list)
            df = df.sort_values('commence_time')
            
            print("ðŸ“… UPCOMING GAMES:")
            for _, game in df.iterrows():
                # Format ET time (already converted above)
                time_str = game['commence_time'].strftime('%a %m/%d %I:%M%p ET')
                print(f"  {time_str} | {game['away_team']} @ {game['home_team']}")
            
            return df
            
        except Exception as e:
            print(f"âœ— Error: {str(e)}")
            return None
    
    def fetch_minimum_alternate(self, event_id, game_info):
        """
        Fetch minimum alternate total for a specific game
        
        CRITICAL: We only want the MINIMUM over line (safest bet)
        """
        try:
            url = f"{self.base_url}/sports/{self.sport}/events/{event_id}/odds"
            params = {
                'apiKey': self.api_key,
                'regions': REGION,
                'markets': 'alternate_totals',
                'oddsFormat': ODDS_FORMAT
            }
            
            response = requests.get(url, params=params, timeout=API_TIMEOUT)
            
            if response.status_code != 200:
                print(f"  âœ— Failed for {game_info['away_team']} @ {game_info['home_team']}")
                return None
            
            data = response.json()
            
            if 'bookmakers' not in data or len(data['bookmakers']) == 0:
                print(f"  âš ï¸ No alternate lines available yet")
                return None
            
            # Find DraftKings alternate totals
            dk_alternates = None
            for bookmaker in data['bookmakers']:
                if bookmaker['title'] == 'DraftKings':
                    for market in bookmaker['markets']:
                        if market['key'] == 'alternate_totals':
                            dk_alternates = market
                            break
                    break
            
            if not dk_alternates:
                print(f"  âš ï¸ No DraftKings alternates found")
                return None
            
            # Find MINIMUM over line (lowest total)
            over_lines = []
            for outcome in dk_alternates['outcomes']:
                if outcome['name'] == 'Over':
                    over_lines.append({
                        'line': outcome['point'],
                        'odds': outcome['price']
                    })
            
            if not over_lines:
                print(f"  âš ï¸ No over lines found")
                return None
            
            # Get the MINIMUM (lowest total = safest over bet)
            minimum_over = min(over_lines, key=lambda x: x['line'])
            
            print(f"  âœ“ {game_info['away_team']} @ {game_info['home_team']}")
            print(f"    Minimum: Over {minimum_over['line']} at {minimum_over['odds']:+d}")
            
            return {
                'event_id': event_id,
                'game_time': game_info['commence_time'],
                'away_team': game_info['away_team'],
                'home_team': game_info['home_team'],
                'minimum_total': minimum_over['line'],
                'minimum_odds': minimum_over['odds'],
                'bookmaker': 'DraftKings'
            }
            
        except Exception as e:
            print(f"  âœ— Error: {str(e)}")
            return None
    
    def fetch_all_minimums(self, games_df):
        """Fetch minimum alternates for all games"""
        print("\n" + "=" * 70)
        print("FETCHING MINIMUM ALTERNATES")
        print("=" * 70)
        print()
        
        minimums = []
        
        for idx, game in games_df.iterrows():
            minimum = self.fetch_minimum_alternate(game['event_id'], game)
            
            if minimum:
                minimums.append(minimum)
            
            # Rate limiting - be nice to API
            if idx < len(games_df) - 1:
                time.sleep(1 / REQUESTS_PER_SECOND)
        
        if minimums:
            df = pd.DataFrame(minimums)
            print(f"\nâœ“ Got minimums for {len(df)} games")
            return df
        else:
            print("\nâš ï¸ No minimums available")
            return None
    
    def save_minimums(self, minimums_df, output_dir='data'):
        """Save minimums to CSV"""
        if minimums_df is not None and len(minimums_df) > 0:
            os.makedirs(output_dir, exist_ok=True)
            
            filepath = os.path.join(output_dir, 'upcoming_games.csv')
            minimums_df.to_csv(filepath, index=False)
            print(f"\nâœ“ Saved to: {filepath}")
            return True
        return False
    
    def run(self):
        """Complete workflow"""
        print("\n" + "=" * 70)
        print("ðŸ€ NBA MINIMUM ALTERNATE FETCHER")
        print("=" * 70)
        
        # Test API
        if not self.test_api_connection():
            return False
        
        # Get upcoming games
        games = self.get_upcoming_games()
        if games is None or len(games) == 0:
            return False
        
        # Fetch minimum alternates
        minimums = self.fetch_all_minimums(games)
        
        if minimums is not None:
            # Save
            self.save_minimums(minimums)
            
            print("\n" + "=" * 70)
            print("âœ… MINIMUM ALTERNATES FETCHED!")
            print("=" * 70)
            return True
        
        return False


def main():
    """Run the fetcher"""
    fetcher = MinimumAlternateFetcher()
    fetcher.run()


if __name__ == "__main__":
    main()