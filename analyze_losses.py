"""
LOSS ANALYSIS - Finding Patterns in the 10 Remaining Losses
============================================================
These games had 0 flags but still lost. Let's find what we missed.
"""

import pandas as pd
import numpy as np

# The 10 losses (5 unique games, each appears twice due to backtest methodology)
losses = [
    {
        'game': 'Toronto Raptors @ Atlanta Hawks',
        'away': 'Toronto Raptors',
        'home': 'Atlanta Hawks',
        'line': 218,
        'actual': 206,
        'missed_by': 12,
        'mc_prob': 99.4
    },
    {
        'game': 'Denver Nuggets @ Portland Trail Blazers',
        'away': 'Denver Nuggets',
        'home': 'Portland Trail Blazers',
        'line': 223,
        'actual': 216,
        'missed_by': 7,
        'mc_prob': 100.0
    },
    {
        'game': 'Chicago Bulls @ Orlando Magic',
        'away': 'Chicago Bulls',
        'home': 'Orlando Magic',
        'line': 220,
        'actual': 208,
        'missed_by': 12,
        'mc_prob': 99.8
    },
    {
        'game': 'San Antonio Spurs @ Phoenix Suns',
        'away': 'San Antonio Spurs',
        'home': 'Phoenix Suns',
        'line': 215,
        'actual': 213,
        'missed_by': 2,
        'mc_prob': 99.7
    },
    {
        'game': 'Indiana Pacers @ Golden State Warriors',
        'away': 'Indiana Pacers',
        'home': 'Golden State Warriors',
        'line': 206,
        'actual': 197,
        'missed_by': 9,
        'mc_prob': 99.8
    }
]

# Load team stats
print("=" * 80)
print("LOSS ANALYSIS - FINDING HIDDEN PATTERNS")
print("=" * 80)

team_stats = pd.read_csv('data/nba_team_stats_2025_2026.csv')

def get_team_stats(team_name):
    row = team_stats[team_stats['Team'] == team_name]
    if len(row) == 0:
        return None
    return row.iloc[0]

print("\n" + "=" * 80)
print("ANALYZING EACH LOSS")
print("=" * 80)

for loss in losses:
    print(f"\n{'='*60}")
    print(f"GAME: {loss['game']}")
    print(f"{'='*60}")
    print(f"  Line: {loss['line']} | Actual: {loss['actual']} | Missed by: {loss['missed_by']}")
    print(f"  MC Probability: {loss['mc_prob']}%")
    
    away_stats = get_team_stats(loss['away'])
    home_stats = get_team_stats(loss['home'])
    
    if away_stats is not None and home_stats is not None:
        print(f"\n  AWAY: {loss['away']}")
        print(f"    PPG: {away_stats['PPG']:.1f}")
        print(f"    ORtg: {away_stats['ORtg']:.1f}")
        print(f"    DRtg: {away_stats['DRtg']:.1f}")
        print(f"    Pace: {away_stats['Pace']:.1f}")
        
        print(f"\n  HOME: {loss['home']}")
        print(f"    PPG: {home_stats['PPG']:.1f}")
        print(f"    ORtg: {home_stats['ORtg']:.1f}")
        print(f"    DRtg: {home_stats['DRtg']:.1f}")
        print(f"    Pace: {home_stats['Pace']:.1f}")
        
        # Calculate expected
        combined_ppg = away_stats['PPG'] + home_stats['PPG']
        avg_pace = (away_stats['Pace'] + home_stats['Pace']) / 2
        
        # Matchup-based expected
        game_tempo = (away_stats['Pace'] * 0.4 + home_stats['Pace'] * 0.4 + 100.2 * 0.2)
        away_exp = (away_stats['ORtg'] * home_stats['DRtg'] / 100) * game_tempo / 100
        home_exp = (home_stats['ORtg'] * away_stats['DRtg'] / 100) * game_tempo / 100
        total_exp = away_exp + home_exp
        
        print(f"\n  ANALYSIS:")
        print(f"    Combined PPG: {combined_ppg:.1f}")
        print(f"    Matchup Expected: {total_exp:.1f}")
        print(f"    Actual: {loss['actual']}")
        print(f"    Difference: {loss['actual'] - total_exp:.1f} (actual - expected)")
        
        # Check for potential flags we missed
        print(f"\n  POTENTIAL FLAGS WE MISSED:")
        
        flags_found = []
        
        # 1. Both teams have good defense (DRtg < 114)
        if away_stats['DRtg'] < 114 and home_stats['DRtg'] < 114:
            flags_found.append(f"🛡️ BOTH teams have good defense ({away_stats['DRtg']:.1f} & {home_stats['DRtg']:.1f})")
        
        # 2. Road team has good defense
        if away_stats['DRtg'] < 113:
            flags_found.append(f"🛡️ Road team has good defense (DRtg: {away_stats['DRtg']:.1f})")
        
        # 3. Home team has elite defense
        if home_stats['DRtg'] < 112:
            flags_found.append(f"🛡️ Home team has strong defense (DRtg: {home_stats['DRtg']:.1f})")
        
        # 4. Low combined ORtg (both offenses below 118)
        if away_stats['ORtg'] < 118 and home_stats['ORtg'] < 118:
            flags_found.append(f"⚠️ Both offenses below 118 ORtg ({away_stats['ORtg']:.1f} & {home_stats['ORtg']:.1f})")
        
        # 5. One team significantly worse offense
        if away_stats['ORtg'] < 115 or home_stats['ORtg'] < 115:
            weak = loss['away'] if away_stats['ORtg'] < 115 else loss['home']
            weak_ortg = away_stats['ORtg'] if away_stats['ORtg'] < 115 else home_stats['ORtg']
            flags_found.append(f"⚠️ {weak} has weak offense (ORtg: {weak_ortg:.1f})")
        
        # 6. Away team - road games typically score less
        if away_stats['PPG'] > 118:  # High-scoring team on road
            flags_found.append(f"🚗 High-scoring road team ({away_stats['PPG']:.1f} PPG) - may underperform")
        
        # 7. Pace mismatch
        pace_diff = abs(away_stats['Pace'] - home_stats['Pace'])
        if pace_diff > 3:
            flags_found.append(f"🐢 Pace mismatch ({pace_diff:.1f} difference)")
        
        # 8. Both teams below league average pace
        if away_stats['Pace'] < 100.2 and home_stats['Pace'] < 100.2:
            flags_found.append(f"🐢 Both teams below avg pace ({away_stats['Pace']:.1f} & {home_stats['Pace']:.1f})")
        
        # 9. Home team struggling (bad record or low PPG)
        if home_stats['PPG'] < 116:
            flags_found.append(f"📉 Home team lower scoring ({home_stats['PPG']:.1f} PPG)")
        
        # 10. Combined expected below line + buffer
        if total_exp < loss['line'] + 5:
            flags_found.append(f"📊 Expected ({total_exp:.1f}) only {total_exp - loss['line']:.1f} above line")
        
        if flags_found:
            for flag in flags_found:
                print(f"    {flag}")
        else:
            print(f"    ❓ No obvious flags - pure variance")

print("\n" + "=" * 80)
print("SUMMARY OF PATTERNS FOUND")
print("=" * 80)

print("""
LOSS PATTERNS IDENTIFIED:

1. TORONTO @ ATLANTA (missed by 12)
   - Look for: Both defenses decent, offense uncertainty

2. DENVER @ PORTLAND (missed by 7)
   - Look for: Road team performance drop

3. CHICAGO @ ORLANDO (missed by 12)
   - Look for: Orlando's strong defense, Chicago inconsistency

4. SAN ANTONIO @ PHOENIX (missed by 2)
   - Very close - might be acceptable variance

5. INDIANA @ GOLDEN STATE (missed by 9)
   - Look for: Pacers struggling, Warriors defense
""")

print("\n" + "=" * 80)
print("RECOMMENDED NEW FLAGS")
print("=" * 80)

print("""
Based on this analysis, consider adding these flags:

1. BOTH_GOOD_DEFENSE: Both teams DRtg < 114
   - When both teams play decent defense, scoring drops

2. ROAD_GOOD_DEFENSE: Away team DRtg < 113  
   - Good defensive road teams suppress scoring

3. WEAK_OFFENSE_INVOLVED: Any team with ORtg < 115
   - Unpredictable low scoring potential

4. TIGHT_MARGIN: Expected total only 5-10 pts above line
   - Not enough buffer for variance

5. BOTH_BELOW_AVG_PACE: Both teams below league average
   - Slower games = fewer possessions = lower totals
""")
