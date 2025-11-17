"""
Game Results Collector - CLEAN VERSION
=======================================
Collects ALL completed games from 2025-2026 season for backtesting
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta
import time
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.api_config import BBALL_REF_BASE_URL
from config.season_config import BBALL_REF_SEASON, SEASON_START_DATE


class GameResultsCollector:
    """Collect completed game results for backtesting"""
    
    def __init__(self):
        self.base_url = BBALL_REF_BASE_URL
        self.season = BBALL_REF_SEASON
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def get_games_for_month(self, year, month):
        """Get all games for a specific month"""
        try:
            month_name = datetime(year, month, 1).strftime('%B').lower()
            url = f"{self.base_url}/leagues/NBA_{self.season}_games-{month_name}.html"
            
            print(f"  Fetching {month_name.capitalize()} {year}...")
            
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'lxml')
            
            # Find schedule table
            table = soup.find('table', {'id': 'schedule'})
            if not table:
                print(f"    [WARN] No games found")
                return None
            
            # Parse table
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                df = pd.read_html(str(table))[0]
            
            # Handle multi-level columns if present
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(-1)
            
            # Clean up - remove header rows
            if 'Date' in df.columns:
                df = df[df['Date'] != 'Date']
                df = df[df['Date'].notna()]
            else:
                print(f"    [ERROR] No 'Date' column found")
                return None
            
            # Only keep completed games (those with scores)
            pts_cols = [col for col in df.columns if col == 'PTS' or 'PTS' in str(col)]
            if len(pts_cols) < 2:
                print(f"    [WARN] No completed games yet")
                return None
            
            # Keep only rows where both scores exist
            df = df[df[pts_cols[0]].notna() & df[pts_cols[1]].notna()]
            
            if len(df) == 0:
                print(f"    [WARN] No completed games yet")
                return None
            
            # Find team columns
            visitor_col = None
            home_col = None
            
            for col in df.columns:
                if 'Visitor' in str(col):
                    visitor_col = col
                elif 'Home' in str(col):
                    home_col = col
            
            if not visitor_col or not home_col:
                print(f"    [ERROR] Could not find team columns")
                return None
            
            # Extract what we need
            result_df = pd.DataFrame({
                'Date': df['Date'],
                'Visitor': df[visitor_col],
                'Visitor_PTS': df[pts_cols[0]],
                'Home': df[home_col],
                'Home_PTS': df[pts_cols[1]]
            })
            
            # Convert scores to numeric
            result_df['Visitor_PTS'] = pd.to_numeric(result_df['Visitor_PTS'], errors='coerce')
            result_df['Home_PTS'] = pd.to_numeric(result_df['Home_PTS'], errors='coerce')
            
            # Remove any rows with missing scores
            result_df = result_df.dropna(subset=['Visitor_PTS', 'Home_PTS'])
            
            # Calculate total
            result_df['Total_Points'] = result_df['Visitor_PTS'] + result_df['Home_PTS']
            
            print(f"    [OK] Found {len(result_df)} completed games")
            
            return result_df
            
        except Exception as e:
            print(f"    [ERROR] {str(e)}")
            return None
    
    def collect_all_games(self):
        """Collect all completed games from season start to now"""
        print("=" * 70)
        print(f"COLLECTING COMPLETED GAMES (2025-2026 SEASON)")
        print("=" * 70)
        print()
        
        all_games = []
        
        # Start from October 2025 (season start)
        current_date = datetime.now()
        start_date = SEASON_START_DATE
        
        # Iterate through each month
        current = start_date
        while current <= current_date:
            month_games = self.get_games_for_month(current.year, current.month)
            
            if month_games is not None and len(month_games) > 0:
                all_games.append(month_games)
            
            # Move to next month
            if current.month == 12:
                current = datetime(current.year + 1, 1, 1)
            else:
                current = datetime(current.year, current.month + 1, 1)
            
            # Be nice to the server
            time.sleep(2)
        
        if all_games:
            # Combine all months
            complete_df = pd.concat(all_games, ignore_index=True)
            complete_df = complete_df.sort_values('Date').reset_index(drop=True)
            
            print(f"\n[OK] Total completed games: {len(complete_df)}")
            return complete_df
        else:
            print("\n[WARN] No completed games found")
            return None
    
    def save_games(self, games_df, output_dir='data'):
        """Save completed games to CSV"""
        if games_df is not None and len(games_df) > 0:
            os.makedirs(output_dir, exist_ok=True)
            
            filepath = os.path.join(output_dir, 'nba_completed_games_2025_2026.csv')
            games_df.to_csv(filepath, index=False)
            print(f"\n[OK] Saved to: {filepath}")
            
            # Display sample
            print("\nSAMPLE GAMES:")
            print(games_df.head(10).to_string(index=False))
            
            return True
        return False
    
    def run(self):
        """Complete workflow"""
        print("\n" + "=" * 70)
        print("NBA GAME RESULTS COLLECTOR")
        print("=" * 70)
        
        games = self.collect_all_games()
        
        if games is not None:
            self.save_games(games)
            
            print("\n" + "=" * 70)
            print("[SUCCESS] GAME RESULTS COLLECTED!")
            print("=" * 70)
            return True
        
        return False


def main():
    """Run the collector"""
    collector = GameResultsCollector()
    collector.run()


if __name__ == "__main__":
    main()