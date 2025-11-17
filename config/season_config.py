"""
Season Configuration
====================
Focus on 2025-2026 NBA season ONLY
"""

from datetime import datetime

# Season info
CURRENT_SEASON = "2025-2026"
SEASON_START_DATE = datetime(2024, 10, 22)  # Opening night 2024
CURRENT_DATE = datetime.now()

# Basketball Reference season identifier
BBALL_REF_SEASON = "2026"  # BBRef uses end year

# Data limits (since season just started)
GAMES_PER_TEAM_APPROX = 6  # ~6 games played per team so far
MAX_FORM_WINDOW = 6        # Use last 6 games for trends
MIN_GAMES_FOR_STATS = 3    # Need at least 3 games for reliable stats

# Scoring thresholds
CONFIDENCE_THRESHOLD_YES = 80   # 80%+ = YES (adjusted based on backtest)
CONFIDENCE_THRESHOLD_MAYBE = 70 # 70-79% = MAYBE
# Below 70% = NO (skip)

# Why 2025-2026 only?
SEASON_RATIONALE = """
- Most relevant current form
- Teams/rosters change year to year  
- Fast data collection (~180 games total so far)
- Current injuries/rotations matter most
- Historical data becomes less predictive
"""

# NBA team names (standard format)
NBA_TEAMS = [
    "Atlanta Hawks",
    "Boston Celtics",
    "Brooklyn Nets",
    "Charlotte Hornets",
    "Chicago Bulls",
    "Cleveland Cavaliers",
    "Dallas Mavericks",
    "Denver Nuggets",
    "Detroit Pistons",
    "Golden State Warriors",
    "Houston Rockets",
    "Indiana Pacers",
    "LA Clippers",
    "Los Angeles Lakers",
    "Memphis Grizzlies",
    "Miami Heat",
    "Milwaukee Bucks",
    "Minnesota Timberwolves",
    "New Orleans Pelicans",
    "New York Knicks",
    "Oklahoma City Thunder",
    "Orlando Magic",
    "Philadelphia 76ers",
    "Phoenix Suns",
    "Portland Trail Blazers",
    "Sacramento Kings",
    "San Antonio Spurs",
    "Toronto Raptors",
    "Utah Jazz",
    "Washington Wizards"
]