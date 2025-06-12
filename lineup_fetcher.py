import logging
import statsapi
import numpy as np
import datetime
from enhanced_rotowire_lineups import fetch_rotowire_expected_lineups_enhanced as fetch_rotowire_expected_lineups

# Configure logging
logger = logging.getLogger('MLB-HR-Predictor')

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

def get_alternative_team_codes(team_code):
    """Get alternative team codes that might be used by different sources"""
    alternatives = {
        'LAD': ['LA', 'LAD', 'LOS'],
        'LAA': ['ANA', 'LAA', 'LA'],  
        'SF': ['SFG', 'SF', 'GIA'],
        'TB': ['TAM', 'TB', 'TBR'],
        'CWS': ['CHW', 'CWS', 'SOX'],
        'WSH': ['WAS', 'WSH', 'NAT'],
        'KC': ['KAN', 'KC', 'KCR'],
        'SD': ['SDP', 'SD', 'PAD'],
        'ARI': ['ARI', 'ARZ', 'DIA'],
        'CLE': ['CLE', 'IND', 'GUA'],  # Guardians vs Indians
        'OAK': ['OAK', 'ATH', 'AS'],
        'MIA': ['MIA', 'FLA', 'MAR']
    }
    
    return alternatives.get(team_code, [team_code])

def fuzzy_team_match(code1, code2):
    """Check if two team codes might refer to the same team"""
    if not code1 or not code2:
        return False
        
    # Exact match
    if code1 == code2:
        return True
    
    # Check if one is contained in the other
    if code1 in code2 or code2 in code1:
        return True
    
    # Check alternatives
    alt1 = get_alternative_team_codes(code1)
    alt2 = get_alternative_team_codes(code2)
    
    return any(a1 == a2 for a1 in alt1 for a2 in alt2)

def find_rotowire_match(mlb_home_team, mlb_away_team, rotowire_data):
    """Enhanced function to find Rotowire game matches using multiple strategies"""
    # Strategy 1: Try exact game ID match
    game_id = f"{mlb_home_team}_{mlb_away_team}_{datetime.datetime.now().strftime('%Y-%m-%d')}"
    if game_id in rotowire_data:
        return rotowire_data[game_id], "exact_id_match"
    
    # Strategy 2: Try team code matching
    for roto_game_id, roto_data in rotowire_data.items():
        roto_home = roto_data.get('home_team', '')
        roto_away = roto_data.get('away_team', '')
        
        if roto_home == mlb_home_team and roto_away == mlb_away_team:
            return roto_data, "team_code_match"
    
    # Strategy 3: Try alternative team codes
    alt_home_codes = get_alternative_team_codes(mlb_home_team)
    alt_away_codes = get_alternative_team_codes(mlb_away_team)
    
    for roto_game_id, roto_data in rotowire_data.items():
        roto_home = roto_data.get('home_team', '')
        roto_away = roto_data.get('away_team', '')
        
        # Check all combinations of alternative codes
        if ((roto_home in alt_home_codes and roto_away in alt_away_codes) or
            (roto_home == mlb_home_team and roto_away in alt_away_codes) or
            (roto_home in alt_home_codes and roto_away == mlb_away_team)):
            return roto_data, "alternative_codes"
    
    # Strategy 4: Try reverse matching (sometimes home/away are flipped)
    for roto_game_id, roto_data in rotowire_data.items():
        roto_home = roto_data.get('home_team', '')
        roto_away = roto_data.get('away_team', '')
        
        if roto_home == mlb_away_team and roto_away == mlb_home_team:
            # Flip the lineups since home/away are reversed
            flipped_data = roto_data.copy()
            flipped_data['home'] = roto_data.get('away', [])
            flipped_data['away'] = roto_data.get('home', [])
            flipped_data['home_pitcher'] = roto_data.get('away_pitcher', 'TBD')
            flipped_data['away_pitcher'] = roto_data.get('home_pitcher', 'TBD')
            return flipped_data, "reverse_match"
    
    # Strategy 5: Fuzzy name matching (last resort)
    for roto_game_id, roto_data in rotowire_data.items():
        roto_home = roto_data.get('home_team', '')
        roto_away = roto_data.get('away_team', '')
        
        if (fuzzy_team_match(mlb_home_team, roto_home) and 
            fuzzy_team_match(mlb_away_team, roto_away)):
            return roto_data, "fuzzy_match"
    
    return None, "no_match"

def fetch_lineups_and_pitchers(games, early_run=False):
    """
    Fetch lineups and probable pitchers for MLB games with enhanced matching.
    """
    # Initialize result dictionaries
    lineups = {}
    probable_pitchers = {}
    
    # Get Rotowire data first using ENHANCED scraper
    rotowire_data = None
    try:
        today_str = datetime.datetime.now().strftime("%Y-%m-%d")
        rotowire_data = fetch_rotowire_expected_lineups(today_str)
        logger.info(f"✅ Enhanced Rotowire scraper fetched {len(rotowire_data)} games")
    except Exception as e:
        logger.warning(f"❌ Enhanced Rotowire scraper failed: {e}")
    
    # Process each game from MLB API
    for _, game in games.iterrows():
        try:
            game_id = game['game_id']
            mlb_game_id = game['game_id_mlb']
            home_team = game['home_team']
            away_team = game['away_team']
            
            logger.info(f"Processing game: {away_team} @ {home_team} (MLB Game ID: {mlb_game_id})")
            
            # Initialize defaults
            home_lineup = []
            away_lineup = []
            home_pitcher = "TBD"
            away_pitcher = "TBD"
            
            # STEP 1: Get pitcher data from MLB API
            try:
                game_data = statsapi.get('game', {'gamePk': mlb_game_id})
                
                if 'gameData' in game_data and 'probablePitchers' in game_data['gameData']:
                    pitcher_data = game_data['gameData']['probablePitchers']
                    
                    if 'home' in pitcher_data and 'fullName' in pitcher_data['home']:
                        home_pitcher = pitcher_data['home']['fullName']
                    if 'away' in pitcher_data and 'fullName' in pitcher_data['away']:
                        away_pitcher = pitcher_data['away']['fullName']
                        
                    logger.info(f"Got pitchers from MLB API: {away_pitcher} vs {home_pitcher}")
                    
            except Exception as e:
                logger.warning(f"Error getting MLB API pitchers for {game_id}: {e}")
            
            # STEP 2: Enhanced Rotowire matching
            if rotowire_data:
                rotowire_match, match_type = find_rotowire_match(home_team, away_team, rotowire_data)
                
                if rotowire_match:
                    home_lineup = rotowire_match.get('home', [])
                    away_lineup = rotowire_match.get('away', [])
                    
                    # Update pitchers if we don't have them from MLB API
                    if home_pitcher == "TBD" and 'home_pitcher' in rotowire_match:
                        home_pitcher = rotowire_match['home_pitcher']
                    if away_pitcher == "TBD" and 'away_pitcher' in rotowire_match:
                        away_pitcher = rotowire_match['away_pitcher']
                        
                    logger.info(f"✅ Enhanced Rotowire match for {game_id} using {match_type}")
                else:
                    logger.warning(f"❌ No Enhanced Rotowire match found for {game_id} ({away_team} @ {home_team})")
            
            # STEP 3: Try MLB API for confirmed lineups (midday runs)
            if not early_run and (not home_lineup or not away_lineup):
                try:
                    game_data = statsapi.get('game', {'gamePk': mlb_game_id})
                    
                    if 'liveData' in game_data and 'boxscore' in game_data['liveData']:
                        boxscore = game_data['liveData']['boxscore']
                        
                        if 'teams' in boxscore:
                            # Get home team batting order
                            if 'home' in boxscore['teams'] and 'battingOrder' in boxscore['teams']['home']:
                                batting_order = boxscore['teams']['home']['battingOrder']
                                home_players = boxscore['teams']['home'].get('players', {})
                                
                                for player_id in batting_order:
                                    player_key = f"ID{player_id}"
                                    if player_key in home_players:
                                        player_name = home_players[player_key].get('person', {}).get('fullName')
                                        if player_name and player_name not in home_lineup:
                                            home_lineup.append(player_name)
                            
                            # Get away team batting order
                            if 'away' in boxscore['teams'] and 'battingOrder' in boxscore['teams']['away']:
                                batting_order = boxscore['teams']['away']['battingOrder']
                                away_players = boxscore['teams']['away'].get('players', {})
                                
                                for player_id in batting_order:
                                    player_key = f"ID{player_id}"
                                    if player_key in away_players:
                                        player_name = away_players[player_key].get('person', {}).get('fullName')
                                        if player_name and player_name not in away_lineup:
                                            away_lineup.append(player_name)
                            
                            if home_lineup or away_lineup:
                                logger.info(f"Got lineups from MLB API for {game_id}")
                                
                except Exception as e:
                    logger.warning(f"Error getting MLB API lineups for {game_id}: {e}")
            
            # Validate lineup sizes
            if len(home_lineup) > 15:
                logger.warning(f"Large home lineup ({len(home_lineup)}) for {game_id}, truncating to 9")
                home_lineup = home_lineup[:9]
                
            if len(away_lineup) > 15:
                logger.warning(f"Large away lineup ({len(away_lineup)}) for {game_id}, truncating to 9")
                away_lineup = away_lineup[:9]
            
            # Store results
            lineups[game_id] = {
                'home': home_lineup,
                'away': away_lineup
            }
            
            probable_pitchers[game_id] = {
                'home': home_pitcher,
                'away': away_pitcher
            }
            
            logger.info(f"Final result for {game_id}: {len(home_lineup)}H/{len(away_lineup)}A players, {home_pitcher} vs {away_pitcher}")
            
        except Exception as e:
            logger.error(f"Error processing game {game_id}: {e}")
            # Set empty defaults but don't skip the game
            lineups[game_id] = {'home': [], 'away': []}
            probable_pitchers[game_id] = {'home': 'TBD', 'away': 'TBD'}
    
    # STEP 4: Add any Enhanced Rotowire-only games that MLB API didn't have
    if rotowire_data:
        for roto_game_id, roto_data in rotowire_data.items():
            if roto_game_id not in lineups and len(roto_data.get('home', [])) > 0:
                logger.info(f"Adding Enhanced Rotowire-only game: {roto_game_id}")
                lineups[roto_game_id] = {
                    'home': roto_data.get('home', []),
                    'away': roto_data.get('away', [])
                }
                probable_pitchers[roto_game_id] = {
                    'home': roto_data.get('home_pitcher', 'TBD'),
                    'away': roto_data.get('away_pitcher', 'TBD')
                }
    
    logger.info(f"🎉 ENHANCED RESULT: {len(lineups)} games with lineups, {len(probable_pitchers)} games with pitchers")
    
    return lineups, probable_pitchers
