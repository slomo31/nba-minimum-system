"""
API Configuration
=================
Settings for The Odds API (paid plan)
"""

# Your Odds API key (paid plan)
ODDS_API_KEY = "a03349ac7178eb60a825d19bd27014ce"

# API settings
BASE_URL = "https://api.the-odds-api.com/v4"
SPORT = "basketball_nba"
BOOKMAKER = "draftkings"  # Focus on DraftKings only
REGION = "us"
MARKET = "alternate_totals"
ODDS_FORMAT = "american"

# Rate limiting (be nice to API)
REQUESTS_PER_SECOND = 1
API_TIMEOUT = 10  # seconds

# Basketball Reference (for stats scraping)
BBALL_REF_BASE_URL = "https://www.basketball-reference.com"
