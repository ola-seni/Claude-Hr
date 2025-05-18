import requests
from bs4 import BeautifulSoup
import pandas as pd
import logging
import datetime
import time
import re

logger = logging.getLogger('MLB-HR-Predictor')

def fetch_rotowire_expected_lineups(date_str=None):
    """
    Fetch expected lineups from Rotowire for a given date.
    
    Parameters:
    -----------
    date_str : str, optional
        Date in format 'YYYY-MM-DD', defaults to tomorrow's date
        
    Returns:
    --------
    dict
        Dictionary of lineups by game_id
    """
    # Set up date (tomorrow by default for early morning runs)
    if date_str is None:
        tomorrow = datetime.datetime.now() + datetime.timedelta(days=1)
        date_str = tomorrow.strftime("%Y-%m-%d")
    
    # Format date for the URL (YYYY-MM-DD to MM-DD-YYYY)
    url_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").strftime("%m-%d-%Y")
    
    # Rotowire URL
    url = f"https://www.rotowire.com/baseball/daily-lineups.php?date={url_date}"
    
    logger.info(f"Fetching Rotowire expected lineups for {date_str} from: {url}")
    
    try:
        # Make request with headers to mimic a browser
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Referer": "https://www.rotowire.com/baseball/",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Cache-Control": "max-age=0"
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        # Parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Initialize lineups dictionary
        lineups = {}
        
        # Find all lineup containers
        lineup_containers = soup.find_all('div', class_='lineup')
        
        for container in lineup_containers:
            try:
                # Get teams
                teams_div = container.find('div', class_='lineup__teams')
                if not teams_div:
                    continue
                
                # Extract away and home teams
                away_div = teams_div.find('div', class_='lineup__team is-visit')
                home_div = teams_div.find('div', class_='lineup__team is-home')
                
                if not away_div or not home_div:
                    continue
                
                away_team = away_div.find('div', class_='lineup__abbr').text.strip()
                home_team = home_div.find('div', class_='lineup__abbr').text.strip()
                
                # Convert to our team codes
                away_code = convert_rotowire_team_to_code(away_team)
                home_code = convert_rotowire_team_to_code(home_team)
                
                if not away_code or not home_code:
                    logger.warning(f"Could not convert teams: {away_team} or {home_team}")
                    continue
                
                # Create game_id
                game_id = f"{home_code}_{away_code}_{date_str}"
                
                # Find pitchers
                away_pitcher = "TBD"
                home_pitcher = "TBD"
                
                # Try to find confirmed starters
                pitcher_divs = container.find_all('div', class_='lineup__player-highlight-name')
                if len(pitcher_divs) >= 2:
                    away_pitcher = pitcher_divs[0].text.strip()
                    home_pitcher = pitcher_divs[1].text.strip()
                
                # Initialize lineup arrays
                away_lineup = []
                home_lineup = []
                
                # Get away lineup
                away_players_div = container.find('ul', class_='lineup__list is-visit')
                if away_players_div:
                    for player_li in away_players_div.find_all('li'):
                        player_name_div = player_li.find('div', class_='lineup__player-name')
                        if player_name_div:
                            player_name = player_name_div.find('a').text.strip()
                            away_lineup.append(player_name)
                
                # Get home lineup
                home_players_div = container.find('ul', class_='lineup__list is-home')
                if home_players_div:
                    for player_li in home_players_div.find_all('li'):
                        player_name_div = player_li.find('div', class_='lineup__player-name')
                        if player_name_div:
                            player_name = player_name_div.find('a').text.strip()
                            home_lineup.append(player_name)
                
                # Store lineups
                lineups[game_id] = {
                    'home': home_lineup,
                    'away': away_lineup,
                    'home_pitcher': home_pitcher,
                    'away_pitcher': away_pitcher,
                    'home_team': home_code,
                    'away_team': away_code
                }
                
                logger.info(f"Found expected lineup for {game_id}: {len(home_lineup)} home players, {len(away_lineup)} away players")
                
            except Exception as e:
                logger.error(f"Error parsing lineup container: {e}")
        
        return lineups
        
    except Exception as e:
        logger.error(f"Error fetching Rotowire lineups: {e}")
        return {}

def convert_rotowire_team_to_code(rotowire_abbr):
    """Convert Rotowire team abbreviation to our standard team code"""
    # Rotowire uses different abbreviations than our code
    rotowire_to_code = {
        'ARI': 'ARI',
        'ATL': 'ATL',
        'BAL': 'BAL',
        'BOS': 'BOS',
        'CHC': 'CHC',
        'CIN': 'CIN',
        'CLE': 'CLE',
        'COL': 'COL',
        'CWS': 'CWS',
        'DET': 'DET',
        'HOU': 'HOU',
        'KC': 'KC',
        'LAA': 'LAA',
        'LAD': 'LAD',
        'MIA': 'MIA',
        'MIL': 'MIL',
        'MIN': 'MIN',
        'NYM': 'NYM',
        'NYY': 'NYY',
        'OAK': 'OAK',
        'PHI': 'PHI',
        'PIT': 'PIT',
        'SD': 'SD',
        'SEA': 'SEA',
        'SF': 'SF',
        'STL': 'STL',
        'TB': 'TB',
        'TEX': 'TEX',
        'TOR': 'TOR',
        'WSH': 'WSH'
    }
    
    return rotowire_to_code.get(rotowire_abbr)

def convert_rotowire_data_to_mlb_format(rotowire_lineups, date_str=None):
    """
    Convert Rotowire lineup data to the format used by our MLB HR Predictor.
    
    Parameters:
    -----------
    rotowire_lineups : dict
        Dictionary of lineups from Rotowire
    date_str : str, optional
        Date in YYYY-MM-DD format
        
    Returns:
    --------
    tuple
        (lineups, probable_pitchers) in the format expected by the predictor
    """
    if date_str is None:
        tomorrow = datetime.datetime.now() + datetime.timedelta(days=1)
        date_str = tomorrow.strftime("%Y-%m-%d")
    
    # Initialize results
    lineups = {}
    probable_pitchers = {}
    
    # Process each game
    for game_id, game_data in rotowire_lineups.items():
        # Extract lineups
        lineups[game_id] = {
            'home': game_data['home'],
            'away': game_data['away']
        }
        
        # Extract probable pitchers
        probable_pitchers[game_id] = {
            'home': game_data['home_pitcher'],
            'away': game_data['away_pitcher']
        }
    
    return lineups, probable_pitchers

# Sample usage
if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Test the functionality
    tomorrow = (datetime.datetime.now() + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    rotowire_lineups = fetch_rotowire_expected_lineups(tomorrow)
    
    if rotowire_lineups:
        print(f"Successfully fetched {len(rotowire_lineups)} expected lineups for {tomorrow}")
        
        # Convert to MLB format
        lineups, probable_pitchers = convert_rotowire_data_to_mlb_format(rotowire_lineups, tomorrow)
        
        # Print first game as example
        first_game = next(iter(lineups))
        print(f"\nExample Game: {first_game}")
        print(f"Home Team: {probable_pitchers[first_game]['home']}")
        print(f"Away Team: {probable_pitchers[first_game]['away']}")
        print(f"Home Lineup: {lineups[first_game]['home']}")
        print(f"Away Lineup: {lineups[first_game]['away']}")
    else:
        print(f"Failed to fetch lineups for {tomorrow}")
