import logging
import statsapi
import numpy as np

# Configure logging (or import your logging config)
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
    
    for _, game in games.iterrows():
        try:
            game_id = game['game_id']
            mlb_game_id = game['game_id_mlb']
            home_team = game['home_team']
            away_team = game['away_team']
            
            logger.info(f"Fetching lineups and pitchers for game: {away_team} @ {home_team} (MLB Game ID: {mlb_game_id})")
            
            # For early run, use probable pitchers from MLB API
            if early_run:
                # Get probable pitchers
                try:
                    # Try the standard probable_pitchers endpoint
                    probable_pitchers_data = statsapi.game_probable_pitchers(mlb_game_id)
                    
                    # Check if we got proper data
                    if isinstance(probable_pitchers_data, dict) and 'home' in probable_pitchers_data and 'away' in probable_pitchers_data:
                        home_probable = probable_pitchers_data.get('home', {}).get('fullName', '')
                        away_probable = probable_pitchers_data.get('away', {}).get('fullName', '')
                    else:
                        # Alternative approach: check the game data itself
                        game_data = statsapi.get('game', {'gamePk': mlb_game_id})
                        if isinstance(game_data, dict):
                            # Navigate the response to find pitcher info
                            home_probable = ''
                            away_probable = ''
                            
                            # Try different possible paths for pitcher info
                            if 'gameData' in game_data and 'probablePitchers' in game_data['gameData']:
                                pitchers_data = game_data['gameData']['probablePitchers']
                                if 'home' in pitchers_data and 'fullName' in pitchers_data['home']:
                                    home_probable = pitchers_data['home']['fullName']
                                if 'away' in pitchers_data and 'fullName' in pitchers_data['away']:
                                    away_probable = pitchers_data['away']['fullName']
                            
                            # Try another possible structure
                            elif 'teams' in game_data:
                                teams_data = game_data['teams']
                                if 'home' in teams_data and 'probablePitcher' in teams_data['home']:
                                    home_pitcher = teams_data['home']['probablePitcher']
                                    if isinstance(home_pitcher, dict) and 'fullName' in home_pitcher:
                                        home_probable = home_pitcher['fullName']
                                
                                if 'away' in teams_data and 'probablePitcher' in teams_data['away']:
                                    away_pitcher = teams_data['away']['probablePitcher']
                                    if isinstance(away_pitcher, dict) and 'fullName' in away_pitcher:
                                        away_probable = away_pitcher['fullName']
                        else:
                            # Fall back to using schedule data
                            try:
                                schedule = statsapi.schedule(game_id=mlb_game_id)
                                if schedule and len(schedule) > 0:
                                    game_info = schedule[0]
                                    home_probable = game_info.get('home_probable_pitcher', '')
                                    away_probable = game_info.get('away_probable_pitcher', '')
                            except Exception as e:
                                logger.warning(f"Error getting schedule for pitcher info: {e}")
                                home_probable = ""
                                away_probable = ""
                except Exception as e:
                    logger.warning(f"Error getting probable pitchers: {e}")
                    # Fall back to schedule info
                    try:
                        schedule = statsapi.schedule(game_id=mlb_game_id)
                        if schedule and len(schedule) > 0:
                            game_info = schedule[0]
                            home_probable = game_info.get('home_probable_pitcher', '')
                            away_probable = game_info.get('away_probable_pitcher', '')
                        else:
                            home_probable = ""
                            away_probable = ""
                    except Exception as e2:
                        logger.warning(f"Error getting schedule for pitcher info: {e2}")
                        home_probable = ""
                        away_probable = ""
                
                # Clean up empty or None values
                if not home_probable or home_probable is None:
                    # Try to get team's rotation if probable not available
                    try:
                        home_team_id = statsapi.lookup_team(game['home_team_name'])[0]['id']
                        home_roster = statsapi.get('team_roster', {'teamId': home_team_id})
                        pitchers = [player['person']['fullName'] for player in home_roster.get('roster', []) 
                                   if player.get('position', {}).get('code') == '1']  # Pitchers are code 1
                        
                        if pitchers:
                            home_probable = pitchers[0]  # Use first pitcher in roster as fallback
                        else:
                            home_probable = "TBD"
                    except:
                        home_probable = "TBD"
                        
                if not away_probable or away_probable is None:
                    # Try to get team's rotation if probable not available
                    try:
                        away_team_id = statsapi.lookup_team(game['away_team_name'])[0]['id']
                        away_roster = statsapi.get('team_roster', {'teamId': away_team_id})
                        pitchers = [player['person']['fullName'] for player in away_roster.get('roster', []) 
                                   if player.get('position', {}).get('code') == '1']  # Pitchers are code 1
                        
                        if pitchers:
                            away_probable = pitchers[0]  # Use first pitcher in roster as fallback
                        else:
                            away_probable = "TBD"
                    except:
                        away_probable = "TBD"
                
                logger.info(f"Probable pitchers for {game_id}: Home - {home_probable}, Away - {away_probable}")
                
                # Store probable pitchers
                probable_pitchers[game_id] = {
                    'home': home_probable,
                    'away': away_probable
                }
                
                # Get projected lineups based on recent games
                # In early run, we'll use team rosters and project likely starters
                try:
                    # Get team rosters
                    home_team_id = statsapi.lookup_team(game['home_team_name'])[0]['id']
                    away_team_id = statsapi.lookup_team(game['away_team_name'])[0]['id']
                    
                    home_roster = statsapi.get('team_roster', {'teamId': home_team_id})
                    away_roster = statsapi.get('team_roster', {'teamId': away_team_id})
                    
                    # Extract players from roster response
                    home_players = [player['person']['fullName'] for player in home_roster.get('roster', []) 
                                  if player.get('position', {}).get('code') not in ['1', '10']]  # Exclude pitchers
                    away_players = [player['person']['fullName'] for player in away_roster.get('roster', [])
                                  if player.get('position', {}).get('code') not in ['1', '10']]  # Exclude pitchers
                    
                    # Take first 9 position players as projected lineup
                    home_lineup = home_players[:9] if len(home_players) >= 9 else home_players
                    away_lineup = away_players[:9] if len(away_players) >= 9 else away_players
                    
                    logger.info(f"Projected lineups for {game_id}: Home - {len(home_lineup)} players, Away - {len(away_lineup)} players")
                except Exception as e:
                    logger.warning(f"Error getting projected lineups: {e}")
                    # Fallback if roster lookup fails
                    home_lineup = []
                    away_lineup = []
                
                # Store projected lineups
                lineups[game_id] = {
                    'home': home_lineup,
                    'away': away_lineup
                }
                
            # For midday run, get confirmed lineups if available
            else:
                # Try to get actual lineup cards
                try:
                    # Different approach: use game_data to get current lineups
                    game_data = statsapi.get('game', {'gamePk': mlb_game_id})
                    
                    # Initialize default values
                    home_lineup = []
                    away_lineup = []
                    home_pitcher = "TBD"
                    away_pitcher = "TBD"
                    
                    # Extract lineups from game data if available
                    if isinstance(game_data, dict):
                        # Try to get lineups from different possible paths in the response
                        
                        # First try for pitchers - look in gameData section
                        if 'gameData' in game_data and 'probablePitchers' in game_data['gameData']:
                            pitcher_data = game_data['gameData']['probablePitchers']
                            if 'home' in pitcher_data and 'fullName' in pitcher_data['home']:
                                home_pitcher = pitcher_data['home']['fullName']
                            if 'away' in pitcher_data and 'fullName' in pitcher_data['away']:
                                away_pitcher = pitcher_data['away']['fullName']
                        
                        # If not found, try another path for pitchers in teams section
                        elif 'teams' in game_data:
                            if 'home' in game_data['teams'] and 'probablePitcher' in game_data['teams']['home']:
                                home_pitcher_data = game_data['teams']['home']['probablePitcher']
                                if isinstance(home_pitcher_data, dict) and 'fullName' in home_pitcher_data:
                                    home_pitcher = home_pitcher_data['fullName']
                            
                            if 'away' in game_data['teams'] and 'probablePitcher' in game_data['teams']['away']:
                                away_pitcher_data = game_data['teams']['away']['probablePitcher']
                                if isinstance(away_pitcher_data, dict) and 'fullName' in away_pitcher_data:
                                    away_pitcher = away_pitcher_data['fullName']
                        
                        # For lineups - try to find in liveData section
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
                                            if player_name:
                                                home_lineup.append(player_name)
                                
                                # Away team lineup
                                if 'away' in boxscore['teams'] and 'battingOrder' in boxscore['teams']['away']:
                                    batting_order = boxscore['teams']['away']['battingOrder']
                                    away_players = boxscore['teams']['away'].get('players', {})
                                    
                                    for player_id in batting_order:
                                        player_key = f"ID{player_id}"
                                        if player_key in away_players:
                                            player_name = away_players[player_key].get('person', {}).get('fullName')
                                            if player_name:
                                                away_lineup.append(player_name)
                    
                    # Fall back to schedule data if needed
                    if (not home_lineup or not away_lineup or 
                        home_pitcher == "TBD" or away_pitcher == "TBD"):
                        try:
                            schedule = statsapi.schedule(game_id=mlb_game_id)
                            if schedule and len(schedule) > 0:
                                game_info = schedule[0]
                                
                                # Update pitchers if needed
                                if home_pitcher == "TBD":
                                    home_pitcher = game_info.get('home_probable_pitcher', 'TBD')
                                if away_pitcher == "TBD":
                                    away_pitcher = game_info.get('away_probable_pitcher', 'TBD')
                        except Exception as e:
                            logger.warning(f"Error getting schedule info: {e}")
                    
                    # If still no lineup, fall back to team rosters
                    if not home_lineup or not away_lineup:
                        try:
                            # Get team rosters
                            home_team_id = statsapi.lookup_team(game['home_team_name'])[0]['id']
                            away_team_id = statsapi.lookup_team(game['away_team_name'])[0]['id']
                            
                            if not home_lineup:
                                home_roster = statsapi.get('team_roster', {'teamId': home_team_id})
                                home_players = [player['person']['fullName'] for player in home_roster.get('roster', []) 
                                            if player.get('position', {}).get('code') not in ['1', '10']]  # Exclude pitchers
                                home_lineup = home_players[:9] if len(home_players) >= 9 else home_players
                            
                            if not away_lineup:
                                away_roster = statsapi.get('team_roster', {'teamId': away_team_id})
                                away_players = [player['person']['fullName'] for player in away_roster.get('roster', [])
                                            if player.get('position', {}).get('code') not in ['1', '10']]  # Exclude pitchers
                                away_lineup = away_players[:9] if len(away_players) >= 9 else away_players
                        except Exception as e:
                            logger.warning(f"Error getting roster data: {e}")
                    
                    logger.info(f"Confirmed lineups for {game_id}: Home - {len(home_lineup)} players, Away - {len(away_lineup)} players")
                    logger.info(f"Confirmed pitchers for {game_id}: Home - {home_pitcher}, Away - {away_pitcher}")
                    
                    # Store confirmed lineups
                    lineups[game_id] = {
                        'home': home_lineup,
                        'away': away_lineup
                    }
                    
                    # Store confirmed pitchers
                    probable_pitchers[game_id] = {
                        'home': home_pitcher,
                        'away': away_pitcher
                    }
                    
                except Exception as e:
                    logger.warning(f"Error getting confirmed lineups for {game_id}: {e}")
                    
                    # Fall back to early run method if lineup cards not available
                    logger.warning(f"Lineup cards not available for {game_id}, using projected lineups")
                    
                    # Use the same code as early run for fallback
                    try:
                        # Get probable pitchers as fallback
                        try:
                            probable_pitchers_data = statsapi.game_probable_pitchers(mlb_game_id)
                            if isinstance(probable_pitchers_data, dict) and 'home' in probable_pitchers_data and 'away' in probable_pitchers_data:
                                home_probable = probable_pitchers_data.get('home', {}).get('fullName', 'TBD')
                                away_probable = probable_pitchers_data.get('away', {}).get('fullName', 'TBD')
                            else:
                                # Try schedule data
                                schedule = statsapi.schedule(game_id=mlb_game_id)
                                if schedule and len(schedule) > 0:
                                    game_info = schedule[0]
                                    home_probable = game_info.get('home_probable_pitcher', 'TBD')
                                    away_probable = game_info.get('away_probable_pitcher', 'TBD')
                                else:
                                    home_probable = "TBD"
                                    away_probable = "TBD"
                        except:
                            # Try schedule data
                            try:
                                schedule = statsapi.schedule(game_id=mlb_game_id)
                                if schedule and len(schedule) > 0:
                                    game_info = schedule[0]
                                    home_probable = game_info.get('home_probable_pitcher', 'TBD')
                                    away_probable = game_info.get('away_probable_pitcher', 'TBD')
                                else:
                                    home_probable = "TBD"
                                    away_probable = "TBD"
                            except:
                                home_probable = "TBD"
                                away_probable = "TBD"
                        
                        # Get team rosters for projected lineups
                        home_team_id = statsapi.lookup_team(game['home_team_name'])[0]['id']
                        away_team_id = statsapi.lookup_team(game['away_team_name'])[0]['id']
                        
                        home_roster = statsapi.get('team_roster', {'teamId': home_team_id})
                        away_roster = statsapi.get('team_roster', {'teamId': away_team_id})
                        
                        home_players = [player['person']['fullName'] for player in home_roster.get('roster', []) 
                                       if player.get('position', {}).get('code') not in ['1', '10']]
                        away_players = [player['person']['fullName'] for player in away_roster.get('roster', [])
                                       if player.get('position', {}).get('code') not in ['1', '10']]
                        
                        home_lineup = home_players[:9] if len(home_players) >= 9 else home_players
                        away_lineup = away_players[:9] if len(away_players) >= 9 else away_players
                        
                        lineups[game_id] = {
                            'home': home_lineup,
                            'away': away_lineup
                        }
                        
                        probable_pitchers[game_id] = {
                            'home': home_probable,
                            'away': away_probable
                        }
                        
                    except Exception as e2:
                        logger.error(f"Error creating fallback lineups for {game_id}: {e2}")
                        # Set empty defaults
                        lineups[game_id] = {'home': [], 'away': []}
                        probable_pitchers[game_id] = {'home': 'TBD', 'away': 'TBD'}
                
        except Exception as e:
            logger.error(f"Error fetching lineups/pitchers for {game_id}: {e}")
            # Set empty defaults
            lineups[game_id] = {'home': [], 'away': []}
            probable_pitchers[game_id] = {'home': 'TBD', 'away': 'TBD'}
            
    return lineups, probable_pitchers
