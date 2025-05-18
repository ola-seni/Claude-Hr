import requests
from bs4 import BeautifulSoup
import pandas as pd
import logging
import datetime
import re
import time

logger = logging.getLogger('MLB-HR-Predictor')

def check_today_and_tomorrow():
    """
    Check today's lineups only.
    
    Returns:
    --------
    tuple
        (lineups dict, date string used)
    """
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    
    # Get today's lineups
    today_lineups = fetch_rotowire_expected_lineups(today)
    
    # Check if we have any games with actual player lineups
    has_player_lineups = False
    for game_id, data in today_lineups.items():
        if len(data.get('home', [])) > 0 or len(data.get('away', [])) > 0:
            has_player_lineups = True
            break
    
    logger.info(f"Using today's ({today}) lineups")
    return today_lineups, today

def fetch_rotowire_expected_lineups(date_str=None):
    """
    Fetch expected lineups from Rotowire for a given date.
    
    Parameters:
    -----------
    date_str : str, optional
        Date in format 'YYYY-MM-DD', defaults to today's date
        
    Returns:
    --------
    dict
        Dictionary of lineups by game_id
    """
    # Set up date (today by default)
    if date_str is None:
        today = datetime.datetime.now()
        date_str = today.strftime("%Y-%m-%d")
    
    # Format date for the URL (YYYY-MM-DD to MM-DD-YYYY)
    url_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").strftime("%m-%d-%Y")
    
    # Rotowire URL - if no date parameter is provided, it shows today's lineups
    url = f"https://www.rotowire.com/baseball/daily-lineups.php"
    if url_date:
        url += f"?date={url_date}"
    
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
        
        # Find all lineup boxes
        lineup_boxes = soup.find_all('div', {'class': 'lineup__box'})
        
        if not lineup_boxes:
            logger.warning("No lineup boxes found. Trying alternative selectors.")
            # Try alternative selectors for lineup containers
            lineup_boxes = soup.find_all('div', {'class': 'lineup is-mlb'})
            if not lineup_boxes:
                lineup_boxes = soup.find_all('div', {'class': 'lineup'})
        
        logger.info(f"Found {len(lineup_boxes)} lineup boxes")
        
        for box in lineup_boxes:
            try:
                # Find teams
                away_team_div = box.find('div', {'class': 'lineup__team is-visit'})
                home_team_div = box.find('div', {'class': 'lineup__team is-home'})
                
                if not away_team_div or not home_team_div:
                    logger.warning("Could not find team divs")
                    continue
                
                # Get team names - first try abbr, then fall back to main team text
                away_team_abbr = away_team_div.find('div', {'class': 'lineup__abbr'})
                home_team_abbr = home_team_div.find('div', {'class': 'lineup__abbr'})
                
                if away_team_abbr and home_team_abbr:
                    away_team = away_team_abbr.text.strip()
                    home_team = home_team_abbr.text.strip()
                else:
                    # Try alternative text
                    away_team = away_team_div.text.strip()
                    home_team = home_team_div.text.strip()
                    
                    # Clean up team names if needed
                    away_team = away_team.split('\n')[0].strip() if '\n' in away_team else away_team
                    home_team = home_team.split('\n')[0].strip() if '\n' in home_team else home_team
                
                logger.info(f"Found matchup: {away_team} @ {home_team}")
                
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
                
                # Use the most direct method to find pitchers
                pitchers = box.find_all('div', {'class': 'lineup__player-highlight-name'})
                if len(pitchers) >= 2:
                    # Get pitcher names and clean them
                    away_pitcher_text = pitchers[0].text.strip()
                    home_pitcher_text = pitchers[1].text.strip()
                    
                    # Remove handedness info if present
                    away_pitcher = away_pitcher_text.split('\n')[0].strip() if '\n' in away_pitcher_text else away_pitcher_text
                    home_pitcher = home_pitcher_text.split('\n')[0].strip() if '\n' in home_pitcher_text else home_pitcher_text
                else:
                    # Fallback method to find pitchers
                    away_pitcher_elem = box.select_one('div.lineup__team-players.is-visit li.lineup__player:first-child')
                    home_pitcher_elem = box.select_one('div.lineup__team-players.is-home li.lineup__player:first-child')
                    
                    if away_pitcher_elem and away_pitcher_elem.find('a'):
                        away_pitcher = away_pitcher_elem.find('a').text.strip()
                    
                    if home_pitcher_elem and home_pitcher_elem.find('a'):
                        home_pitcher = home_pitcher_elem.find('a').text.strip()
                
                logger.info(f"Pitchers: {away_pitcher} (A) vs {home_pitcher} (H)")
                
                # Find lineups
                away_lineup = []
                home_lineup = []
                
                # First try the main lineup lists
                away_list = box.find('ul', {'class': 'lineup__list is-visit'})
                home_list = box.find('ul', {'class': 'lineup__list is-home'})
                
                # Process away lineup
                if away_list:
                    # Find the status first (Confirmed, Expected, etc.)
                    status_li = away_list.find('li', {'class': re.compile('lineup__status.*')})
                    if status_li:
                        away_status = status_li.text.strip()
                        logger.info(f"Away team status: {away_status}")
                    
                    # Find player items using regex that matches all player classes
                    away_players = away_list.find_all('li', {'class': re.compile('lineup__player.*')})
                    
                    for player in away_players:
                        # Get player name from anchor tag
                        player_link = player.find('a')
                        if player_link:
                            # Try to get from title attribute first, then text
                            if 'title' in player_link.attrs:
                                player_name = player_link['title'].strip()
                            else:
                                player_name = player_link.text.strip()
                            
                            # Skip pitchers and duplicates
                            if player.find('div', {'class': 'lineup__pos'}) and player.find('div', {'class': 'lineup__pos'}).text.strip() != 'P':
                                away_lineup.append(player_name)
                
                # Process home lineup
                if home_list:
                    # Find the status first (Confirmed, Expected, etc.)
                    status_li = home_list.find('li', {'class': re.compile('lineup__status.*')})
                    if status_li:
                        home_status = status_li.text.strip()
                        logger.info(f"Home team status: {home_status}")
                    
                    # Find player items using regex that matches all player classes
                    home_players = home_list.find_all('li', {'class': re.compile('lineup__player.*')})
                    
                    for player in home_players:
                        # Get player name from anchor tag
                        player_link = player.find('a')
                        if player_link:
                            # Try to get from title attribute first, then text
                            if 'title' in player_link.attrs:
                                player_name = player_link['title'].strip()
                            else:
                                player_name = player_link.text.strip()
                            
                            # Skip pitchers and duplicates
                            if player.find('div', {'class': 'lineup__pos'}) and player.find('div', {'class': 'lineup__pos'}).text.strip() != 'P':
                                home_lineup.append(player_name)
                
                # Fallback to alternative structure if needed
                if not away_lineup:
                    # Try alternative method
                    away_players = box.select('div.lineup__team-players.is-visit li:not(:first-child)')
                    for player in away_players:
                        player_link = player.find('a')
                        if player_link:
                            player_name = player_link.text.strip()
                            away_lineup.append(player_name)
                
                if not home_lineup:
                    # Try alternative method
                    home_players = box.select('div.lineup__team-players.is-home li:not(:first-child)')
                    for player in home_players:
                        player_link = player.find('a')
                        if player_link:
                            player_name = player_link.text.strip()
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
                logger.error(f"Error parsing lineup box: {e}")
        
        # If no lineups found but boxes were present, save HTML for debugging
        if not lineups and lineup_boxes:
            with open(f"rotowire_debug_{date_str}.html", "w", encoding="utf-8") as f:
                f.write(response.text)
            logger.warning(f"Could not extract lineups from {len(lineup_boxes)} boxes, saved HTML for debugging")
        
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
        'CHW': 'CWS',  # Alternative for White Sox
        'DET': 'DET',
        'HOU': 'HOU',
        'KC': 'KC',
        'KAN': 'KC',  # Alternative KC
        'KCR': 'KC',  # Another alternative
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
        'SFG': 'SF',  # Alternative
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
        today = datetime.datetime.now()
        date_str = today.strftime("%Y-%m-%d")
    
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
    
    # Test the functionality - get today's lineups
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    print(f"\nFetching expected lineups for today ({today})")
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
            print(f"Home team: {data['home_team']}")
            print(f"Away team: {data['away_team']}")
            print(f"Home Pitcher: {data['home_pitcher']}")
            print(f"Away Pitcher: {data['away_pitcher']}")
            print(f"Home Lineup ({len(data['home'])} players): {data['home']}")
            print(f"Away Lineup ({len(data['away'])} players): {data['away']}")
    else:
        print(f"Failed to fetch any lineups")
    
    # Convert to MLB format
    if rotowire_lineups:
        print("\nConverting to MLB format...")
        lineup_data, pitcher_data = convert_rotowire_data_to_mlb_format(rotowire_lineups)
        print(f"Converted {len(lineup_data)} games")
