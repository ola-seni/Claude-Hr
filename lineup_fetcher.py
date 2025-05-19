import logging
import statsapi
import numpy as np
import datetime
from rotowire_lineups import fetch_rotowire_expected_lineups, convert_rotowire_data_to_mlb_format

# Configure logging
logger = logging.getLogger('MLB-HR-Predictor')

def fetch_lineups_and_pitchers(games, early_run=False):
    """
    Fetch lineups and probable pitchers for MLB games.
    
    Parameters:
    -----------
    games : pandas.DataFrame
        DataFrame containing game information with columns like 'game_id', 'game_id_mlb', 'home_team', 'away_team',
        'home_team_name', 'away_team_name', etc.
    early_run : bool, default=False
        Whether this is an early morning run (True) or midday run with confirmed lineups (False)
        
    Returns:
    --------
    tuple
        (lineups, probable_pitchers) where:
        - lineups is a dict mapping game_id to dict with 'home' and 'away' lists of player names
        - probable_pitchers is a dict mapping game_id to dict with 'home' and 'away' pitcher names
    """
    # Initialize result dictionaries
    lineups = {}
    probable_pitchers = {}
    
    # Also initialize results from Rotowire (used as fallback)
    rotowire_data = None
    
    # Try to get Rotowire data first (will be used as fallback)
    try:
        today_str = datetime.datetime.now().strftime("%Y-%m-%d")
        rotowire_data = fetch_rotowire_expected_lineups(today_str)
        logger.info(f"Fetched {len(rotowire_data)} games from Rotowire")
    except Exception as e:
        logger.warning(f"Failed to fetch Rotowire data: {e}")
    
    # Process each game
    for _, game in games.iterrows():
        try:
            game_id = game['game_id']
            mlb_game_id = game['game_id_mlb']
            home_team = game['home_team']
            away_team = game['away_team']
            
            logger.info(f"Fetching lineups and pitchers for game: {away_team} @ {home_team} (MLB Game ID: {mlb_game_id})")
            
            # Initialize default values
            home_lineup = []
            away_lineup = []
            home_pitcher = "TBD"
            away_pitcher = "TBD"
            
            # For early run, focus mainly on probable pitchers
            if early_run:
                try:
                    # Get probable pitchers for early run
                    probable_pitchers_data = statsapi.game_probable_pitchers(mlb_game_id)
                    
                    # Extract pitcher names if data is valid
                    if isinstance(probable_pitchers_data, dict) and 'home' in probable_pitchers_data and 'away' in probable_pitchers_data:
                        home_pitcher = probable_pitchers_data.get('home', {}).get('fullName', 'TBD')
                        away_pitcher = probable_pitchers_data.get('away', {}).get('fullName', 'TBD')
                    else:
                        # Fall back to alternative sources
                        try:
                            # Try getting from game data
                            game_data = statsapi.get('game', {'gamePk': mlb_game_id})
                            if 'gameData' in game_data and 'probablePitchers' in game_data['gameData']:
                                pitchers_data = game_data['gameData']['probablePitchers']
                                if 'home' in pitchers_data and 'fullName' in pitchers_data['home']:
                                    home_pitcher = pitchers_data['home']['fullName']
                                if 'away' in pitchers_data and 'fullName' in pitchers_data['away']:
                                    away_pitcher = pitchers_data['away']['fullName']
                        except Exception as e:
                            logger.warning(f"Error getting pitchers from game data: {e}")
                            
                        # If still no pitchers, try schedule
                        if home_pitcher == "TBD" or away_pitcher == "TBD":
                            try:
                                schedule = statsapi.schedule(game_id=mlb_game_id)
                                if schedule and len(schedule) > 0:
                                    game_info = schedule[0]
                                    if home_pitcher == "TBD":
                                        home_pitcher = game_info.get('home_probable_pitcher', 'TBD')
                                    if away_pitcher == "TBD":
                                        away_pitcher = game_info.get('away_probable_pitcher', 'TBD')
                            except Exception as e:
                                logger.warning(f"Error getting pitchers from schedule: {e}")
                except Exception as e:
                    logger.warning(f"Error getting probable pitchers: {e}")
                    
                # Log the pitchers we found
                logger.info(f"Probable pitchers for {game_id}: Home - {home_pitcher}, Away - {away_pitcher}")
                
                # For early run, use Rotowire for projected lineups
                if rotowire_data and game_id in rotowire_data:
                    rotowire_game = rotowire_data[game_id]
                    home_lineup = rotowire_game.get('home', [])
                    away_lineup = rotowire_game.get('away', [])
                    logger.info(f"Using Rotowire projected lineups for early run: Home - {len(home_lineup)} players, Away - {len(away_lineup)} players")
                    
                    # Update pitchers if Rotowire has them
                    if home_pitcher == "TBD" and 'home_pitcher' in rotowire_game:
                        home_pitcher = rotowire_game['home_pitcher']
                    if away_pitcher == "TBD" and 'away_pitcher' in rotowire_game:
                        away_pitcher = rotowire_game['away_pitcher']
            
            # For midday run, try to get confirmed lineups from MLB API
            else:
                try:
                    # Different approach: use game_data to get current lineups
                    game_data = statsapi.get('game', {'gamePk': mlb_game_id})
                    
                    # Extract pitchers from game data
                    if 'gameData' in game_data and 'probablePitchers' in game_data['gameData']:
                        pitcher_data = game_data['gameData']['probablePitchers']
                        if 'home' in pitcher_data and 'fullName' in pitcher_data['home']:
                            home_pitcher = pitcher_data['home']['fullName']
                        if 'away' in pitcher_data and 'fullName' in pitcher_data['away']:
                            away_pitcher = pitcher_data['away']['fullName']
                    
                    # Extract lineups from game data - liveData section
                    if 'liveData' in game_data and 'boxscore' in game_data['liveData']:
                        boxscore = game_data['liveData']['boxscore']
                        
                        # Try to get batting orders
                        if 'teams' in boxscore:
                            # Home team lineup
                            if 'home' in boxscore['teams'] and 'battingOrder' in boxscore['teams']['home']:
                                batting_order = boxscore['teams']['home']['battingOrder']
                                home_players = boxscore['teams']['home'].get('players', {})
                                
                                for player_id in batting_order:
                                    player_key = f"ID{player_id}"
                                    if player_key in home_players:
                                        player_name = home_players[player_key].get('person', {}).get('fullName')
                                        if player_name and player_name not in home_lineup:
                                            home_lineup.append(player_name)
                            
                            # Away team lineup
                            if 'away' in boxscore['teams'] and 'battingOrder' in boxscore['teams']['away']:
                                batting_order = boxscore['teams']['away']['battingOrder']
                                away_players = boxscore['teams']['away'].get('players', {})
                                
                                for player_id in batting_order:
                                    player_key = f"ID{player_id}"
                                    if player_key in away_players:
                                        player_name = away_players[player_key].get('person', {}).get('fullName')
                                        if player_name and player_name not in away_lineup:
                                            away_lineup.append(player_name)
                    
                    # If we got lineups, log the success
                    if home_lineup or away_lineup:
                        logger.info(f"Successfully retrieved MLB lineups for {game_id}: Home - {len(home_lineup)} players, Away - {len(away_lineup)} players")
                
                except Exception as e:
                    logger.warning(f"Error getting confirmed lineups from MLB API: {e}")
                
                # If MLB API didn't give us lineups, try Rotowire
                if not home_lineup or not away_lineup:
                    if rotowire_data and game_id in rotowire_data:
                        rotowire_game = rotowire_data[game_id]
                        
                        if not home_lineup and 'home' in rotowire_game:
                            home_lineup = rotowire_game['home']
                            logger.info(f"Using Rotowire lineup for home team: {len(home_lineup)} players")
                            
                        if not away_lineup and 'away' in rotowire_game:
                            away_lineup = rotowire_game['away']
                            logger.info(f"Using Rotowire lineup for away team: {len(away_lineup)} players")
                            
                        # Update pitchers if needed
                        if home_pitcher == "TBD" and 'home_pitcher' in rotowire_game:
                            home_pitcher = rotowire_game['home_pitcher']
                        if away_pitcher == "TBD" and 'away_pitcher' in rotowire_game:
                            away_pitcher = rotowire_game['away_pitcher']
            
            # Validate lineups - make sure they're not suspicious (like full rosters)
            if len(home_lineup) > 15:
                logger.warning(f"Suspiciously large home lineup ({len(home_lineup)} players) - likely a full roster. Using empty lineup instead.")
                home_lineup = []
                
            if len(away_lineup) > 15:
                logger.warning(f"Suspiciously large away lineup ({len(away_lineup)} players) - likely a full roster. Using empty lineup instead.")
                away_lineup = []
            
            # Store lineups and pitchers in result dictionaries
            lineups[game_id] = {
                'home': home_lineup,
                'away': away_lineup
            }
            
            probable_pitchers[game_id] = {
                'home': home_pitcher,
                'away': away_pitcher
            }
            
            # Log the final results
            logger.info(f"Final lineups for {game_id}: Home - {len(home_lineup)} players, Away - {len(away_lineup)} players")
            logger.info(f"Final pitchers for {game_id}: Home - {home_pitcher}, Away - {away_pitcher}")
            
        except Exception as e:
            logger.error(f"Error fetching lineups/pitchers for {game_id}: {e}")
            # Set empty defaults
            lineups[game_id] = {'home': [], 'away': []}
            probable_pitchers[game_id] = {'home': 'TBD', 'away': 'TBD'}
    
    return lineups, probable_pitchers
