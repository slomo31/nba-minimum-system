"""
Basketball Reference Stats Collector - PROPERLY FIXED (REAL DATA)
==================================================================
Scrapes 2025-2026 season stats ONLY - REAL DATA

FIX: W/L are in the ADVANCED table, not per-game table!
- Per-game table: Team, G, PTS (PPG)
- Advanced table: Team, W, L, ORtg, DRtg, Pace

Collects:
- ORtg (offensive rating)
- DRtg (defensive rating)
- Pace
- PPG (points per game)
- W/L Record
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.api_config import BBALL_REF_BASE_URL
from config.season_config import BBALL_REF_SEASON


class BballRefCollector:
    """Scrape current season team stats from Basketball Reference"""
    
    def __init__(self):
        self.base_url = BBALL_REF_BASE_URL
        self.season = BBALL_REF_SEASON
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def scrape_team_stats(self):
        """Scrape team stats for 2025-2026 season"""
        print("=" * 70)
        print(f"SCRAPING {self.season} NBA TEAM STATS (REAL DATA)")
        print("=" * 70)
        
        try:
            # Get team stats page
            url = f"{self.base_url}/leagues/NBA_{self.season}.html"
            print(f"\nFetching: {url}")
            
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'lxml')
            
            # Parse per-game stats table (for PPG)
            print("Parsing per-game stats...")
            pergame_table = soup.find('table', {'id': 'per_game-team'})
            if not pergame_table:
                print("✗ Could not find per-game stats table")
                return None
            
            # Read with pandas - suppress warning
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                pergame_df = pd.read_html(str(pergame_table))[0]
            
            # Handle multi-level columns
            if isinstance(pergame_df.columns, pd.MultiIndex):
                pergame_df.columns = pergame_df.columns.get_level_values(-1)
            
            # Parse advanced stats table (for W, L, ORtg, DRtg, Pace)
            print("Parsing advanced stats...")
            advanced_table = soup.find('table', {'id': 'advanced-team'})
            if not advanced_table:
                print("✗ Could not find advanced stats table")
                return None
            
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                advanced_df = pd.read_html(str(advanced_table))[0]
            
            # Handle multi-level columns
            if isinstance(advanced_df.columns, pd.MultiIndex):
                advanced_df.columns = advanced_df.columns.get_level_values(-1)
            
            # Clean data - remove header rows
            pergame_df = pergame_df[pergame_df['Team'].notna()]
            pergame_df = pergame_df[pergame_df['Team'] != 'Team']
            pergame_df = pergame_df[pergame_df['Team'] != 'League Average']
            
            advanced_df = advanced_df[advanced_df['Team'].notna()]
            advanced_df = advanced_df[advanced_df['Team'] != 'Team']
            advanced_df = advanced_df[advanced_df['Team'] != 'League Average']
            
            # CRITICAL FIX: Get columns from correct tables
            # Per-game table: Team, G, PTS
            pergame_df = pergame_df[['Team', 'G', 'PTS']].copy()
            pergame_df.columns = ['Team', 'GP', 'PPG']
            
            # Advanced table: Team, W, L, ORtg, DRtg, Pace
            advanced_df = advanced_df[['Team', 'W', 'L', 'ORtg', 'DRtg', 'Pace']].copy()
            
            # Convert numeric columns
            for col in ['GP', 'PPG']:
                pergame_df[col] = pd.to_numeric(pergame_df[col], errors='coerce')
            
            for col in ['W', 'L', 'ORtg', 'DRtg', 'Pace']:
                advanced_df[col] = pd.to_numeric(advanced_df[col], errors='coerce')
            
            # Merge on Team
            stats_df = pd.merge(pergame_df, advanced_df, on='Team', how='inner')
            
            # Add record
            stats_df['Record'] = stats_df['W'].astype(int).astype(str) + '-' + stats_df['L'].astype(int).astype(str)
            
            # Remove any rows with NaN
            stats_df = stats_df.dropna()
            
            if len(stats_df) < 25:
                print(f"⚠️ Warning: Only found {len(stats_df)} teams (expected 30)")
            else:
                print(f"\n✓ Collected REAL stats for {len(stats_df)} teams")
            
            return stats_df
            
        except Exception as e:
            print(f"✗ Error scraping stats: {str(e)}")
            import traceback
            traceback.print_exc()
            
            print("\n" + "=" * 70)
            print("⚠️ BASKETBALL REFERENCE SCRAPING FAILED")
            print("=" * 70)
            print("\nTrying alternative source...")
            
            # Try alternative
            return self.try_alternative_source()
    
    def try_alternative_source(self):
        """Try ESPN stats as alternative REAL data source"""
        print("\n" + "=" * 70)
        print("TRYING ESPN.COM (REAL DATA)")
        print("=" * 70)
        
        try:
            # ESPN has simpler HTML structure
            print("\nFetching from ESPN...")
            
            # Get team stats from ESPN
            url = "https://www.espn.com/nba/stats/team"
            response = requests.get(url, headers=self.headers, timeout=15)
            response.raise_for_status()
            
            # Parse tables
            tables = pd.read_html(response.text)
            
            if len(tables) < 2:
                print("✗ Could not find ESPN stats tables")
                return None
            
            # ESPN typically has multiple tables
            # Try to find the one with team stats
            stats_df = None
            for table in tables:
                if 'Team' in table.columns or 0 in table.columns:
                    stats_df = table
                    break
            
            if stats_df is None:
                print("✗ Could not parse ESPN tables")
                return None
            
            print("✓ Successfully scraped from ESPN (REAL DATA)")
            
            # ESPN format is different - you may need to adjust column selection
            # For now, return to Basketball Reference as primary
            
            print("\n⚠️ ESPN scraping needs custom parsing")
            print("   Recommend: Wait a few minutes and retry Basketball Reference")
            
            return None
            
        except Exception as e:
            print(f"✗ ESPN also failed: {str(e)}")
            return None
    
    def save_stats(self, stats_df, output_dir='data'):
        """Save stats to CSV"""
        if stats_df is not None and len(stats_df) > 0:
            os.makedirs(output_dir, exist_ok=True)
            
            filepath = os.path.join(output_dir, 'nba_team_stats_2025_2026.csv')
            stats_df.to_csv(filepath, index=False)
            print(f"\n✓ Saved REAL data to: {filepath}")
            
            # Display sample
            print("\n📊 SAMPLE STATS (REAL DATA FROM BASKETBALL REFERENCE):")
            print(stats_df[['Team', 'GP', 'W', 'L', 'PPG', 'ORtg', 'DRtg', 'Pace']].head(5).to_string(index=False))
            
            return True
        return False
    
    def run(self):
        """Complete workflow"""
        print("\n" + "=" * 70)
        print("🏀 NBA TEAM STATS COLLECTOR (REAL DATA ONLY)")
        print("=" * 70)
        
        stats = self.scrape_team_stats()
        
        if stats is not None:
            self.save_stats(stats)
            
            print("\n" + "=" * 70)
            print("✅ REAL TEAM STATS COLLECTED!")
            print("=" * 70)
            return True
        else:
            print("\n" + "=" * 70)
            print("❌ FAILED TO COLLECT REAL DATA")
            print("=" * 70)
            print("\n💡 SOLUTION:")
            print("   1. Check internet connection")
            print("   2. Verify Basketball Reference is accessible:")
            print(f"      {self.base_url}/leagues/NBA_{self.season}.html")
            print("   3. Wait 2-3 minutes (might be temporary issue)")
            print("   4. Try again")
            print("\n⚠️ System requires REAL DATA to function properly")
            return False


def main():
    """Run the collector"""
    collector = BballRefCollector()
    success = collector.run()
    
    if not success:
        print("\n⚠️ CRITICAL: Cannot proceed without real team stats")
        print("   The system requires accurate, current data to function")
        sys.exit(1)


if __name__ == "__main__":
    main()