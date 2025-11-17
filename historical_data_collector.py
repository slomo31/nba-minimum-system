"""
DATA CLEANUP - Fix Team Names and Dates
========================================
Fixes two issues in historical data:
1. Removes asterisks from team names in stats file
2. Converts date format in games file

Usage:
    python fix_historical_data.py
"""

import pandas as pd
import os


def fix_team_stats():
    """Remove asterisks from team names"""
    print("\nFixing team_stats.csv...")
    
    filepath = 'data/historical/2024_2025/team_stats.csv'
    
    if not os.path.exists(filepath):
        print(f"[ERROR] File not found: {filepath}")
        return False
    
    df = pd.read_csv(filepath)
    
    # Remove asterisks from team names
    df['Team'] = df['Team'].str.replace('*', '', regex=False)
    
    # Save back
    df.to_csv(filepath, index=False)
    
    print(f"[OK] Fixed {len(df)} team names")
    print("Sample teams:")
    print(df['Team'].head(5).tolist())
    
    return True


def fix_completed_games():
    """Fix date format in games file"""
    print("\nFixing completed_games.csv...")
    
    filepath = 'data/historical/2024_2025/completed_games.csv'
    
    if not os.path.exists(filepath):
        print(f"[ERROR] File not found: {filepath}")
        return False
    
    df = pd.read_csv(filepath)
    
    # Convert date format
    # From: "Fri, Apr 11, 2025"
    # To: "2025-04-11"
    df['Date'] = pd.to_datetime(df['Date'], format='mixed')
    df['Date'] = df['Date'].dt.strftime('%Y-%m-%d')
    
    # Save back
    df.to_csv(filepath, index=False)
    
    print(f"[OK] Fixed {len(df)} game dates")
    print("Date range:")
    print(f"  First: {df['Date'].min()}")
    print(f"  Last: {df['Date'].max()}")
    
    return True


def main():
    print("\n" + "="*70)
    print("HISTORICAL DATA CLEANUP")
    print("="*70)
    
    # Fix team stats
    if not fix_team_stats():
        return False
    
    # Fix completed games
    if not fix_completed_games():
        return False
    
    print("\n" + "="*70)
    print("[SUCCESS] DATA CLEANUP COMPLETE!")
    print("="*70)
    print("\nNow run: python full_season_backtest.py")
    print()
    
    return True


if __name__ == "__main__":
    main()