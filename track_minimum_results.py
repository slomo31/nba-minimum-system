"""
Minimum Total System - Results Tracker
=======================================
Analyzes all past predictions against actual game results

This script:
1. Loads all decision files from output_archive/decisions/
2. Matches predictions against completed games
3. Shows YES bets (with W-L record)
4. Shows NO bets (with missed opportunities)
"""

import pandas as pd
import os
from datetime import datetime
import glob


def load_all_decisions():
    """Load all decision CSVs from archive"""
    decision_files = glob.glob('output_archive/decisions/*_decisions.csv')
    
    if not decision_files:
        print("No decision files found in output_archive/decisions/")
        return None
    
    all_decisions = []
    
    for file in sorted(decision_files):
        df = pd.read_csv(file)
        # Add source file for reference
        df['source_file'] = os.path.basename(file)
        all_decisions.append(df)
    
    combined = pd.concat(all_decisions, ignore_index=True)
    print(f"Loaded {len(combined)} predictions from {len(decision_files)} files")
    
    # Remove duplicates - keep highest confidence prediction for each unique game
    # Create a unique key for each game (date + teams)
    combined['game_time_parsed'] = pd.to_datetime(combined['game_time'], utc=True)
    combined['game_key'] = (
        combined['game_time_parsed'].dt.date.astype(str) + '_' + 
        combined['away_team'] + '_' + 
        combined['home_team']
    )
    
    # Sort by confidence (highest first) and keep first occurrence of each game
    combined = combined.sort_values('confidence', ascending=False)
    deduplicated = combined.drop_duplicates(subset='game_key', keep='first')
    
    duplicates_removed = len(combined) - len(deduplicated)
    if duplicates_removed > 0:
        print(f"Removed {duplicates_removed} duplicate predictions (kept highest confidence for each game)")
    
    print(f"Analyzing {len(deduplicated)} unique games")
    
    return deduplicated


def load_completed_games():
    """Load completed games with results"""
    try:
        games = pd.read_csv('data/nba_completed_games_2025_2026.csv')
        print(f"Loaded {len(games)} completed games")
        return games
    except FileNotFoundError:
        print("Warning: No completed games file found")
        return pd.DataFrame()


def match_predictions_to_results(decisions_df, completed_games_df):
    """Match each prediction to its actual result"""
    
    if completed_games_df.empty:
        print("No completed games to match against")
        return decisions_df
    
    # Parse game_time to date (handle timezone-aware strings)
    decisions_df['game_date'] = pd.to_datetime(decisions_df['game_time'], utc=True).dt.date
    completed_games_df['Date'] = pd.to_datetime(completed_games_df['Date']).dt.date
    
    # Add result columns
    decisions_df['actual_total'] = None
    decisions_df['result'] = 'PENDING'
    
    matched_count = 0
    
    for idx, pred in decisions_df.iterrows():
        # Try to find matching game
        game_date = pred['game_date']
        away = pred['away_team']
        home = pred['home_team']
        
        # Find in completed games - check BOTH orientations AND +/- 1 day for timezone differences
        # (Predictions are in UTC, games recorded in local time)
        from datetime import timedelta
        dates_to_check = [
            game_date,
            game_date - timedelta(days=1),  # Game might be day before due to timezone
            game_date + timedelta(days=1)   # Or day after
        ]
        
        match = completed_games_df[
            (completed_games_df['Date'].isin(dates_to_check)) &
            (
                ((completed_games_df['Visitor'] == away) & (completed_games_df['Home'] == home)) |
                ((completed_games_df['Visitor'] == home) & (completed_games_df['Home'] == away))
            )
        ]
        
        if len(match) > 0:
            actual_total = match.iloc[0]['Total_Points']
            decisions_df.at[idx, 'actual_total'] = actual_total
            
            # Determine if prediction won or lost
            minimum = pred['minimum_total']
            
            if pred['decision'] in ['YES', 'MAYBE']:
                # YES/MAYBE bet wins if actual > minimum
                if actual_total > minimum:
                    decisions_df.at[idx, 'result'] = 'WIN'
                else:
                    decisions_df.at[idx, 'result'] = 'LOSS'
                matched_count += 1
            
            elif pred['decision'] == 'NO':
                # NO means we didn't bet, but track if we SHOULD have
                if actual_total > minimum:
                    decisions_df.at[idx, 'result'] = 'WOULD_WIN'
                else:
                    decisions_df.at[idx, 'result'] = 'CORRECT_SKIP'
                matched_count += 1
    
    print(f"Matched {matched_count} predictions to completed games")
    
    return decisions_df


def generate_report(decisions_df):
    """Generate the performance report"""
    
    print("\n" + "=" * 80)
    print("MINIMUM TOTAL SYSTEM - 2025-2026 SEASON RESULTS")
    print("=" * 80)
    print()
    
    # Filter YES and NO bets
    yes_bets = decisions_df[decisions_df['decision'] == 'YES'].copy()
    no_bets = decisions_df[decisions_df['decision'] == 'NO'].copy()
    
    # YES BETS SECTION
    if len(yes_bets) > 0:
        wins = len(yes_bets[yes_bets['result'] == 'WIN'])
        losses = len(yes_bets[yes_bets['result'] == 'LOSS'])
        pending = len(yes_bets[yes_bets['result'] == 'PENDING'])
        
        win_pct = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0
        
        print(f"YES BETS (80%+ confidence): {wins}-{losses} ({win_pct:.1f}%) - {pending} pending")
        print("-" * 80)
        print()
        
        # Show completed games
        completed_yes = yes_bets[yes_bets['result'] != 'PENDING'].sort_values('game_date')
        
        for _, row in completed_yes.iterrows():
            status = "✓ WIN" if row['result'] == 'WIN' else "✗ LOSS"
            date_str = row['game_date'].strftime('%Y-%m-%d')
            
            print(f"{status} | {date_str} | {row['game']}")
            print(f"     Line: {row['minimum_total']:.1f} | Actual: {row['actual_total']:.1f} | Conf: {row['confidence']}%")
            print()
        
        # Show pending games
        if pending > 0:
            print()
            print(f"⏳ PENDING ({pending} games not yet completed):")
            print()
            pending_yes = yes_bets[yes_bets['result'] == 'PENDING'].sort_values('game_date')
            for _, row in pending_yes.iterrows():
                date_str = row['game_date'].strftime('%Y-%m-%d')
                print(f"     {date_str} | {row['game']} | Line: {row['minimum_total']:.1f}")
    else:
        print("YES BETS (80%+ confidence): No bets yet this season")
        print("-" * 80)
    
    # MAYBE BETS SECTION
    print()
    print()
    maybe_bets = decisions_df[decisions_df['decision'] == 'MAYBE'].copy()
    
    if len(maybe_bets) > 0:
        maybe_wins = len(maybe_bets[maybe_bets['result'] == 'WIN'])
        maybe_losses = len(maybe_bets[maybe_bets['result'] == 'LOSS'])
        maybe_pending = len(maybe_bets[maybe_bets['result'] == 'PENDING'])
        
        maybe_win_pct = (maybe_wins / (maybe_wins + maybe_losses) * 100) if (maybe_wins + maybe_losses) > 0 else 0
        
        print(f"MAYBE BETS (75-79% confidence): {maybe_wins}-{maybe_losses} ({maybe_win_pct:.1f}%) - {maybe_pending} pending")
        print("-" * 80)
        print()
        
        # Show completed MAYBE bets
        completed_maybe = maybe_bets[maybe_bets['result'] != 'PENDING'].sort_values('game_date')
        
        if len(completed_maybe) > 0:
            for _, row in completed_maybe.iterrows():
                status = "✓ WIN" if row['result'] == 'WIN' else "✗ LOSS"
                date_str = row['game_date'].strftime('%Y-%m-%d')
                
                print(f"{status} | {date_str} | {row['game']}")
                print(f"     Line: {row['minimum_total']:.1f} | Actual: {row['actual_total']:.1f} | Conf: {row['confidence']}%")
                print()
        
        # Show pending MAYBE games
        if maybe_pending > 0:
            print()
            print(f"⏳ PENDING ({maybe_pending} games not yet completed):")
            print()
            pending_maybe = maybe_bets[maybe_bets['result'] == 'PENDING'].sort_values('game_date')
            for _, row in pending_maybe.iterrows():
                date_str = row['game_date'].strftime('%Y-%m-%d')
                print(f"     {date_str} | {row['game']} | Line: {row['minimum_total']:.1f}")
    else:
        print("MAYBE BETS (75-79% confidence): No MAYBE bets this season")
        print("-" * 80)
    
    # NO BETS SECTION
    print()
    print()
    print(f"NO BETS: {len(no_bets)} games skipped")
    print("-" * 80)
    print()
    
    if len(no_bets) > 0:
        missed_opportunities = 0
        correct_skips = 0
        
        completed_no = no_bets[no_bets['result'] != 'PENDING'].sort_values('game_date')
        
        for _, row in completed_no.iterrows():
            date_str = row['game_date'].strftime('%Y-%m-%d')
            
            if row['result'] == 'WOULD_WIN':
                status = "⚠️  MISSED"
                missed_opportunities += 1
            else:
                status = "✓ CORRECT"
                correct_skips += 1
            
            if pd.notna(row['actual_total']):
                print(f"{status} | {date_str} | {row['game']}")
                print(f"        Line: {row['minimum_total']:.1f} | Actual: {row['actual_total']:.1f} | Conf: {row['confidence']}%")
                print()
        
        if missed_opportunities > 0:
            print()
            print(f"⚠️  MISSED {missed_opportunities} OPPORTUNITIES (would have won if we bet)")
        
        if correct_skips > 0:
            print(f"✓ {correct_skips} CORRECT SKIPS (game went under minimum)")
    
    print()
    print("=" * 80)
    
    # Final summary
    if len(yes_bets) > 0 and (wins + losses) > 0:
        total_wagered = (wins + losses) * 3  # 3% per bet
        roi = ((wins * 3 * 0.31) - (losses * 3)) / total_wagered * 100  # Assuming -450 odds = 0.31 profit
        
        print()
        print("SUMMARY")
        print("-" * 80)
        print(f"Completed YES bets: {wins + losses}")
        print(f"Win rate: {win_pct:.1f}%")
        print(f"Estimated ROI: {roi:+.1f}% (assuming -450 avg odds)")
        print()


def main():
    """Main execution"""
    
    # Load all data
    print("Loading data...")
    print()
    
    decisions = load_all_decisions()
    if decisions is None:
        return
    
    completed_games = load_completed_games()
    
    print()
    
    # Match predictions to results
    print("Matching predictions to results...")
    decisions_with_results = match_predictions_to_results(decisions, completed_games)
    
    # Generate report
    generate_report(decisions_with_results)
    
    # Save the matched data for future reference
    decisions_with_results.to_csv('min_total_results_tracker.csv', index=False)
    print()
    print("Full results saved to: min_total_results_tracker.csv")
    print()


if __name__ == "__main__":
    main()