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
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        # Parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Initialize lineups dictionary
        lineups = {}
        
        # Find all lineup containers
        lineup_containers = soup.find_all('div', class_='lineup is-mlb')
        if not lineup_containers:
            lineup_containers = soup.find_all('div', class_='lineup')
            
        logger.info(f"Found {len(lineup_containers)} lineup containers")
        
        for container in lineup_containers:
            try:
                # Get teams
                teams_div = container.find('div', class_='lineup__teams')
                if not teams_div:
                    logger.warning("No lineup__teams div found")
                    continue
                
                # Extract away and home teams
                away_div = teams_div.find('div', class_='lineup__team is-visit')
                home_div = teams_div.find('div', class_='lineup__team is-home')
                
                if not away_div or not home_div:
                    logger.warning("Could not find away or home team div")
                    continue
                
                away_team = away_div.find('div', class_='lineup__abbr').text.strip()
                home_team = home_div.find('div', class_='lineup__abbr').text.strip()
                
                logger.info(f"Found matchup: {away_team} @ {home_team}")
                
                # Convert to our team codes
                away_code = convert_rotowire_team_to_code(away_team)
                home_code = convert_rotowire_team_to_code(home_team)
                
                if not away_code or not home_code:
                    logger.warning(f"Could not convert teams: {away_team} or {home_team}")
                    continue
                
                # Create game_id
                game_id = f"{home_code}_{away_code}_{date_str}"
                
                # Find pitchers - use the player highlight divs
                pitcher_divs = container.find_all('div', class_='lineup__player-highlight-name')
                away_pitcher = "TBD"
                home_pitcher = "TBD"
                
                if len(pitcher_divs) >= 2:
                    # Extract pitcher names and remove the handedness indicator
                    away_pitcher_text = pitcher_divs[0].text.strip()
                    home_pitcher_text = pitcher_divs[1].text.strip()
                    
                    # Clean up pitcher names (remove newlines and handedness)
                    away_pitcher = away_pitcher_text.split('\n')[0].strip()
                    home_pitcher = home_pitcher_text.split('\n')[0].strip()
                
                logger.info(f"Pitchers: {away_pitcher} (A) vs {home_pitcher} (H)")
                
                # Find lineup lists
                away_list = container.find('ul', class_='lineup__list is-visit')
                home_list = container.find('ul', class_='lineup__list is-home')
                
                # Initialize lineup arrays
                away_lineup = []
                home_lineup = []
                
                # Process away lineup
                if away_list:
                    away_items = away_list.find_all('li')
                    # Skip first two items (pitcher & "Expected Lineup")
                    for item in away_items[2:]:
                        # Check if this is a player entry (contains position and name)
                        item_text = item.text.strip()
                        if '\n' in item_text:
                            # Item format is typically "POSITION\nPLAYER_NAME\nHANDEDNESS"
                            parts = item_text.split('\n')
                            if len(parts) >= 2:
                                # Extract player name (second part)
                                player_name = parts[1].strip()
                                away_lineup.append(player_name)
                
                # Process home lineup
                if home_list:
                    home_items = home_list.find_all('li')
                    # Skip first two items (pitcher & "Expected Lineup")
                    for item in home_items[2:]:
                        # Check if this is a player entry (contains position and name)
                        item_text = item.text.strip()
                        if '\n' in item_text:
                            # Item format is typically "POSITION\nPLAYER_NAME\nHANDEDNESS"
                            parts = item_text.split('\n')
                            if len(parts) >= 2:
                                # Extract player name (second part)
                                player_name = parts[1].strip()
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
                logger.error(f"Error parsing lineup container: {e}", exc_info=True)
        
        return lineups
        
    except Exception as e:
        logger.error(f"Error fetching Rotowire lineups: {e}", exc_info=True)
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
        'KAN': 'KC',  # Alternative KC
        'LA': 'LAD',  # Alternative LAD
        'LAA': 'LAA',
        'LAD': 'LAD',
        'MIA': 'MIA',
        'MIL': 'MIL',
        'MIN': 'MIN',
        'NYM': 'NYM',
        'NYY': 'NYY',
        'OAK': 'OAK',
        'ATH': 'OAK',  # Alternative for Oakland
        'PHI': 'PHI',
        'PIT': 'PIT',
        'SD': 'SD',
        'SEA': 'SEA',
        'SF': 'SF',
        'STL': 'STL',
        'TB': 'TB',
        'TEX': 'TEX',
        'TOR': 'TOR',
        'WSH': 'WSH',
        'WAS': 'WSH'  # Alternative for Washington
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

def check_today_and_tomorrow():
    """
    Check both today and tomorrow for lineups, useful for testing and early morning runs
    when tomorrow's lineups might not be posted yet.
    
    Returns:
    --------
    dict
        Best available lineups from either day
    """
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    tomorrow = (datetime.datetime.now() + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    
    # Try tomorrow first (preferred)
    tomorrow_lineups = fetch_rotowire_expected_lineups(tomorrow)
    
    # Check if we have any games with actual player lineups
    has_player_lineups = False
    for game_id, data in tomorrow_lineups.items():
        if len(data.get('home', [])) > 0 or len(data.get('away', [])) > 0:
            has_player_lineups = True
            break
    
    # If tomorrow has games with lineups, use it
    if has_player_lineups:
        logger.info(f"Using tomorrow's ({tomorrow}) lineups which have player data")
        return tomorrow_lineups, tomorrow
    
    # Otherwise try today
    today_lineups = fetch_rotowire_expected_lineups(today)
    
    # Check if today has games with lineups
    has_player_lineups = False
    for game_id, data in today_lineups.items():
        if len(data.get('home', [])) > 0 or len(data.get('away', [])) > 0:
            has_player_lineups = True
            break
    
    # If today has games with lineups, use it
    if has_player_lineups:
        logger.info(f"Using today's ({today}) lineups which have player data")
        return today_lineups, today
    
    # If neither has lineups but tomorrow has games, use tomorrow's games
    if tomorrow_lineups:
        logger.info(f"Using tomorrow's ({tomorrow}) games, but no lineups available yet")
        return tomorrow_lineups, tomorrow
    
    # As a last resort, use today's games
    logger.info(f"Using today's ({today}) games, but no lineups available yet")
    return today_lineups, today

# Sample usage
if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Test the functionality - try for today, explicitly
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    print(f"\nTesting with today's date: {today}")
    rotowire_lineups = fetch_rotowire_expected_lineups(today)
    
    if rotowire_lineups:
        print(f"\nFound {len(rotowire_lineups)} expected lineups for {today}")
        
        # Count games with actual lineups
        games_with_lineups = 0
        for game_id, data in rotowire_lineups.items():
            if len(data.get('home', [])) > 0 or len(data.get('away', [])) > 0:
                games_with_lineups += 1
        
        print(f"Games with at least partial lineups: {games_with_lineups}")
        
        # Print details of all games
        for game_id, data in rotowire_lineups.items():
            print(f"\nGame: {game_id}")
            print(f"Home Pitcher: {data['home_pitcher']}")
            print(f"Away Pitcher: {data['away_pitcher']}")
            print(f"Home Lineup ({len(data['home'])} players): {data['home']}")
            print(f"Away Lineup ({len(data['away'])} players): {data['away']}")
    else:
        print(f"Failed to fetch any lineups")
    
    # Also test the comprehensive check
    print("\nTesting check_today_and_tomorrow()")
    best_lineups, date_used = check_today_and_tomorrow()
    print(f"Best date: {date_used}, Number of games: {len(best_lineups)}")
    
    # Print sample of the best lineups
    if best_lineups:
        sample_game = next(iter(best_lineups))
        print(f"\nSample game from best lineups: {sample_game}")
        print(f"Home team: {best_lineups[sample_game]['home_team']}")
        print(f"Away team: {best_lineups[sample_game]['away_team']}")
        print(f"Home pitcher: {best_lineups[sample_game]['home_pitcher']}")
        print(f"Away pitcher: {best_lineups[sample_game]['away_pitcher']}")
        print(f"Home lineup ({len(best_lineups[sample_game]['home'])} players): {best_lineups[sample_game]['home']}")
        print(f"Away lineup ({len(best_lineups[sample_game]['away'])} players): {best_lineups[sample_game]['away']}")
