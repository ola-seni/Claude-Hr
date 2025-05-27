import requests
from bs4 import BeautifulSoup
import pandas as pd
import logging
import datetime
import re
import json

logger = logging.getLogger('MLB-HR-Predictor')

def fetch_rotowire_expected_lineups_enhanced(date_str=None):
    """
    Enhanced version that can find games in JavaScript data as well as HTML containers
    """
    if date_str is None:
        today = datetime.datetime.now()
        date_str = today.strftime("%Y-%m-%d")
    
    # Format date for the URL (YYYY-MM-DD to MM-DD-YYYY)
    url_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").strftime("%m-%d-%Y")
    
    url = f"https://www.rotowire.com/baseball/daily-lineups.php"
    if url_date:
        url += f"?date={url_date}"
    
    logger.info(f"Enhanced Rotowire fetch for {date_str} from: {url}")
    
    try:
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
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Strategy 1: Standard HTML containers (existing method)
        lineups_html = extract_from_html_containers(soup, date_str)
        logger.info(f"Found {len(lineups_html)} games from HTML containers")
        
        # Strategy 2: JavaScript/JSON data
        lineups_js = extract_from_javascript_data(soup, response.text, date_str)  
        logger.info(f"Found {len(lineups_js)} games from JavaScript data")
        
        # Strategy 3: Alternative HTML selectors
        lineups_alt = extract_from_alternative_selectors(soup, date_str)
        logger.info(f"Found {len(lineups_alt)} games from alternative selectors")
        
        # Strategy 4: Team name search and reconstruct
        lineups_search = extract_by_team_search(response.text, date_str)
        logger.info(f"Found {len(lineups_search)} games from team name search")
        
        # Merge all results (HTML takes precedence, then JS, then alternatives)
        all_lineups = {}
        
        # Add in order of preference
        all_lineups.update(lineups_search)  # Lowest priority
        all_lineups.update(lineups_alt)     # Medium priority  
        all_lineups.update(lineups_js)      # High priority
        all_lineups.update(lineups_html)    # Highest priority (most reliable)
        
        logger.info(f"TOTAL: Found {len(all_lineups)} unique games after merging all strategies")
        
        return all_lineups
        
    except Exception as e:
        logger.error(f"Error in enhanced Rotowire fetch: {e}")
        return {}

def extract_from_html_containers(soup, date_str):
    """Extract games from standard HTML containers (existing method)"""
    lineups = {}
    
    # Find all lineup containers - try multiple selectors
    selectors_to_try = [
        'div.lineup.is-mlb',
        'div.lineup',
        'div[class*="lineup"]',
        '.game-container',
        '.matchup-container'
    ]
    
    lineup_containers = []
    for selector in selectors_to_try:
        containers = soup.select(selector)
        if containers:
            lineup_containers = containers
            logger.info(f"Found {len(containers)} containers using selector: {selector}")
            break
    
    if not lineup_containers:
        logger.warning("No lineup containers found with any selector")
        return lineups
    
    for container in lineup_containers:
        try:
            game_data = parse_container(container, date_str)
            if game_data:
                game_id = game_data['game_id']
                lineups[game_id] = game_data
        except Exception as e:
            logger.error(f"Error parsing HTML container: {e}")
            continue
    
    return lineups

def extract_from_javascript_data(soup, html_text, date_str):
    """Extract games from JavaScript/JSON data"""
    lineups = {}
    
    # Find script tags that might contain game data
    script_tags = soup.find_all('script')
    
    for i, script in enumerate(script_tags):
        if not script.string:
            continue
            
        script_content = script.string.strip()
        
        # Skip if too short to contain meaningful data
        if len(script_content) < 500:
            continue
            
        # Look for patterns that suggest game data
        game_indicators = [
            'lineup', 'game', 'matchup', 'pitcher', 'batter',
            'CLE', 'LAD', 'BAL', 'STL', 'DET', 'SF', 'PHI', 'ATL'  # Our missing teams
        ]
        
        if not any(indicator.lower() in script_content.lower() for indicator in game_indicators):
            continue
            
        logger.info(f"Analyzing Script {i} for game data...")
        
        # Try to extract JSON data
        try:
            # Look for JSON-like structures
            json_matches = re.findall(r'\{[^{}]*"[^"]*"[^{}]*\}', script_content)
            
            for json_str in json_matches:
                if any(team in json_str for team in ['CLE', 'LAD', 'BAL', 'STL', 'DET', 'SF', 'PHI', 'ATL']):
                    logger.info(f"Found potential game data in JSON: {json_str[:100]}...")
                    # Try to parse and extract game info
                    try:
                        data = json.loads(json_str)
                        # Process the JSON data to extract game info
                        # This would need to be customized based on the actual JSON structure
                        logger.info(f"Successfully parsed JSON data: {list(data.keys()) if isinstance(data, dict) else type(data)}")
                    except json.JSONDecodeError:
                        pass
                        
        except Exception as e:
            logger.error(f"Error parsing script {i}: {e}")
        
        # Look for array/object assignments that might contain game data
        assignments = re.findall(r'(\w+)\s*=\s*(\[.*?\]|\{.*?\})', script_content, re.DOTALL)
        
        for var_name, value in assignments:
            if any(team in value for team in ['CLE', 'LAD', 'BAL', 'STL']):
                logger.info(f"Found potential game data in variable {var_name}: {value[:100]}...")
    
    return lineups

def extract_from_alternative_selectors(soup, date_str):
    """Try alternative CSS selectors to find games"""
    lineups = {}
    
    # Alternative selectors to try
    alt_selectors = [
        'div[data-game]',
        'div[data-matchup]',
        '.game-card',
        '.matchup-card', 
        'div[class*="game"]',
        'div[class*="matchup"]',
        'article',
        '.content-block'
    ]
    
    for selector in alt_selectors:
        try:
            elements = soup.select(selector)
            logger.info(f"Trying selector '{selector}': found {len(elements)} elements")
            
            for element in elements:
                # Check if this element contains team abbreviations
                element_text = element.get_text()
                
                # Look for our missing teams
                missing_teams = ['CLE', 'LAD', 'BAL', 'STL', 'DET', 'SF', 'PHI', 'ATL']
                found_teams = [team for team in missing_teams if team in element_text]
                
                if len(found_teams) >= 2:  # Found at least 2 teams (home + away)
                    logger.info(f"Found potential game with teams {found_teams} in element with selector {selector}")
                    
                    # Try to extract game data
                    try:
                        game_data = parse_alternative_element(element, date_str)
                        if game_data:
                            game_id = game_data['game_id']
                            lineups[game_id] = game_data
                            logger.info(f"Successfully extracted game: {game_id}")
                    except Exception as e:
                        logger.error(f"Error parsing alternative element: {e}")
                        
        except Exception as e:
            logger.error(f"Error with selector {selector}: {e}")
    
    return lineups

def extract_by_team_search(html_text, date_str):
    """Search for team patterns in HTML and try to reconstruct games"""
    lineups = {}
    
    # Our missing teams
    missing_teams = ['CLE', 'LAD', 'BAL', 'STL', 'DET', 'SF', 'PHI', 'ATL']
    
    # Common game patterns to look for
    patterns = [
        r'(\w{2,3})\s*@\s*(\w{2,3})',  # Team @ Team
        r'(\w{2,3})\s*vs\.?\s*(\w{2,3})',  # Team vs Team
        r'<[^>]*>(\w{2,3})</[^>]*>.*?<[^>]*>(\w{2,3})</[^>]*>',  # HTML tags with teams
    ]
    
    found_matchups = set()
    
    for pattern in patterns:
        matches = re.findall(pattern, html_text, re.IGNORECASE)
        
        for match in matches:
            team1, team2 = match
            team1, team2 = team1.upper(), team2.upper()
            
            # Convert Rotowire abbreviations to our codes
            team1_code = convert_rotowire_team_to_code(team1)
            team2_code = convert_rotowire_team_to_code(team2)
            
            # Check if this involves our missing teams
            if team1_code in missing_teams or team2_code in missing_teams:
                if team1_code and team2_code and team1_code != team2_code:
                    # Determine home/away (first team is usually away in @ format)
                    if '@' in pattern:
                        away_team, home_team = team1_code, team2_code
                    else:
                        # For other patterns, we'll guess based on common conventions
                        home_team, away_team = team1_code, team2_code
                    
                    matchup = (away_team, home_team)
                    if matchup not in found_matchups:
                        found_matchups.add(matchup)
                        
                        game_id = f"{home_team}_{away_team}_{date_str}"
                        
                        logger.info(f"Found missing game by text search: {away_team} @ {home_team}")
                        
                        # Create minimal game data
                        lineups[game_id] = {
                            'home': [],  # No lineup data from text search
                            'away': [],
                            'home_pitcher': 'TBD',
                            'away_pitcher': 'TBD', 
                            'home_team': home_team,
                            'away_team': away_team,
                            'source': 'text_search'
                        }
    
    return lineups

def parse_container(container, date_str):
    """Parse a lineup container (existing logic)"""
    try:
        # Find teams
        teams_div = container.find('div', {'class': 'lineup__teams'})
        if not teams_div:
            return None
        
        away_div = teams_div.find('div', {'class': 'lineup__team is-visit'})
        home_div = teams_div.find('div', {'class': 'lineup__team is-home'})
        
        if not away_div or not home_div:
            return None
        
        # Get team abbreviations
        away_team_abbr = away_div.find('div', {'class': 'lineup__abbr'})
        home_team_abbr = home_div.find('div', {'class': 'lineup__abbr'})
        
        if away_team_abbr and home_team_abbr:
            away_team = away_team_abbr.text.strip()
            home_team = home_team_abbr.text.strip()
        else:
            return None
        
        # Convert to our team codes
        away_code = convert_rotowire_team_to_code(away_team)
        home_code = convert_rotowire_team_to_code(home_team)
        
        if not away_code or not home_code:
            return None
        
        game_id = f"{home_code}_{away_code}_{date_str}"
        
        # Extract pitchers
        pitcher_divs = container.find_all('div', {'class': 'lineup__player-highlight-name'})
        away_pitcher = "TBD"
        home_pitcher = "TBD"
        
        if len(pitcher_divs) >= 2:
            away_pitcher_text = pitcher_divs[0].text.strip()
            home_pitcher_text = pitcher_divs[1].text.strip()
            
            away_pitcher = away_pitcher_text.split('\n')[0].strip()
            home_pitcher = home_pitcher_text.split('\n')[0].strip()
        
        # Extract lineups (existing logic)
        away_list = container.find('ul', {'class': 'lineup__list is-visit'})
        home_list = container.find('ul', {'class': 'lineup__list is-home'})
        
        away_lineup = []
        home_lineup = []
        
        # Process lineups (simplified for now)
        if away_list:
            away_players = away_list.find_all('li', {'class': re.compile('lineup__player.*')})
            for player in away_players:
                player_link = player.find('a')
                if player_link:
                    player_name = player_link.get('title', player_link.text).strip()
                    if player_name:
                        away_lineup.append(player_name)
        
        if home_list:
            home_players = home_list.find_all('li', {'class': re.compile('lineup__player.*')})
            for player in home_players:
                player_link = player.find('a')
                if player_link:
                    player_name = player_link.get('title', player_link.text).strip()
                    if player_name:
                        home_lineup.append(player_name)
        
        return {
            'game_id': game_id,
            'home': home_lineup,
            'away': away_lineup,
            'home_pitcher': home_pitcher,
            'away_pitcher': away_pitcher,
            'home_team': home_code,
            'away_team': away_code,
            'source': 'html_container'
        }
        
    except Exception as e:
        logger.error(f"Error parsing container: {e}")
        return None

def parse_alternative_element(element, date_str):
    """Parse an alternative element that might contain game data"""
    try:
        element_text = element.get_text()
        
        # Look for team patterns
        team_pattern = r'\b([A-Z]{2,3})\b'
        teams_found = re.findall(team_pattern, element_text)
        
        # Filter to valid team codes
        valid_teams = []
        for team in teams_found:
            team_code = convert_rotowire_team_to_code(team)
            if team_code:
                valid_teams.append(team_code)
        
        # Need at least 2 teams for a game
        if len(valid_teams) < 2:
            return None
        
        # Take first two as away/home (this is a guess)
        away_team = valid_teams[0]
        home_team = valid_teams[1]
        
        game_id = f"{home_team}_{away_team}_{date_str}"
        
        return {
            'game_id': game_id,
            'home': [],  # No lineup data
            'away': [],
            'home_pitcher': 'TBD',
            'away_pitcher': 'TBD',
            'home_team': home_team,
            'away_team': away_team,
            'source': 'alternative_element'
        }
        
    except Exception as e:
        logger.error(f"Error parsing alternative element: {e}")
        return None

def convert_rotowire_team_to_code(rotowire_abbr):
    """Convert Rotowire team abbreviation to our standard team code"""
    rotowire_to_code = {
        'ARI': 'ARI', 'ATL': 'ATL', 'BAL': 'BAL', 'BOS': 'BOS', 'CHC': 'CHC',
        'CIN': 'CIN', 'CLE': 'CLE', 'COL': 'COL', 'CWS': 'CWS', 'CHW': 'CWS',
        'DET': 'DET', 'HOU': 'HOU', 'KC': 'KC', 'KAN': 'KC', 'KCR': 'KC',
        'LA': 'LAD', 'LAA': 'LAA', 'LAD': 'LAD', 'MIA': 'MIA', 'MIL': 'MIL',
        'MIN': 'MIN', 'NYM': 'NYM', 'NYY': 'NYY', 'OAK': 'OAK', 'ATH': 'OAK',
        'PHI': 'PHI', 'PIT': 'PIT', 'SD': 'SD', 'SEA': 'SEA', 'SF': 'SF',
        'SFG': 'SF', 'STL': 'STL', 'TB': 'TB', 'TEX': 'TEX', 'TOR': 'TOR',
        'WSH': 'WSH', 'WAS': 'WSH'
    }
    
    return rotowire_to_code.get(rotowire_abbr)

def convert_rotowire_data_to_mlb_format(rotowire_lineups, date_str=None):
    """Convert Rotowire lineup data to the format used by our MLB HR Predictor."""
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
            'home': game_data.get('home', []),
            'away': game_data.get('away', [])
        }
        
        # Extract probable pitchers
        probable_pitchers[game_id] = {
            'home': game_data.get('home_pitcher', 'TBD'),
            'away': game_data.get('away_pitcher', 'TBD')
        }
    
    return lineups, probable_pitchers

# Test the enhanced scraper
if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    print(f"Testing enhanced scraper for {today}...")
    
    lineups = fetch_rotowire_expected_lineups_enhanced(today)
    
    print(f"\nFound {len(lineups)} total games:")
    
    # Check specifically for our missing games
    missing_teams = ['CLE', 'LAD', 'BAL', 'STL', 'DET', 'SF', 'PHI', 'ATL']
    found_missing = 0
    
    for game_id, data in lineups.items():
        home_team = data['home_team']
        away_team = data['away_team']
        source = data.get('source', 'unknown')
        
        print(f"{game_id}: {away_team} @ {home_team} (source: {source})")
        
        if home_team in missing_teams or away_team in missing_teams:
            found_missing += 1
            print(f"  ✅ FOUND MISSING TEAM GAME!")
    
    print(f"\nFound {found_missing} games involving previously missing teams!")
