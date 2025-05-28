import logging
import time
import statsapi
from datetime import datetime

logger = logging.getLogger("MLB-HR-Predictor")

def fetch_player_stats(player_names, generate_simulated_stats=False):
    """Fetch batting stats for given players using MLB Stats API"""
    logger.info(f"Fetching stats for {len(player_names)} players using MLB Stats API")
    all_player_stats = {}
    skipped_players = []
    
    for player_name in player_names:
        try:
            # Search for player
            player_search = statsapi.lookup_player(player_name)
            
            if not player_search:
                logger.info(f"Player not found: {player_name}")
                skipped_players.append(player_name)
                continue
            
            # Get the first match (most relevant)
            player_info = player_search[0]
            player_id = player_info['id']  # Define player_id HERE
            
            # Get player stats for 2025 season
            try:
                player_stats_response = statsapi.player_stat_data(
                    player_id, 
                    group="hitting", 
                    type="season", 
                    sportId=1,
                    season=2025
                )
                
                # Extract stats
                if 'stats' in player_stats_response:
                    stats = player_stats_response['stats']
                    
                    if isinstance(stats, list) and len(stats) > 0:
                        all_stats = stats[0].get('stats', {})
                        
                        # Check if player has meaningful stats
                        games = int(all_stats.get('gamesPlayed', 0))
                        if games < 3:  # Lowered threshold for early season
                            logger.info(f"Insufficient games for {player_name}: {games}")
                            skipped_players.append(player_name)
                            continue
                        
                        # Process stats
                        player_data = {
                            'player_id': player_id,
                            'player_name': player_name,
                            'games': games,
                            'plate_appearances': int(all_stats.get('plateAppearances', 0)),
                            'at_bats': int(all_stats.get('atBats', 0)),
                            'hits': int(all_stats.get('hits', 0)),
                            'doubles': int(all_stats.get('doubles', 0)),
                            'triples': int(all_stats.get('triples', 0)),
                            'home_runs': int(all_stats.get('homeRuns', 0)),
                            'runs': int(all_stats.get('runs', 0)),
                            'rbi': int(all_stats.get('rbi', 0)),
                            'walks': int(all_stats.get('baseOnBalls', 0)),
                            'strikeouts': int(all_stats.get('strikeOuts', 0)),
                            'stolen_bases': int(all_stats.get('stolenBases', 0)),
                            'caught_stealing': int(all_stats.get('caughtStealing', 0)),
                            'batting_avg': float(all_stats.get('avg', 0)),
                            'obp': float(all_stats.get('obp', 0)),
                            'slg': float(all_stats.get('slg', 0)),
                            'ops': float(all_stats.get('ops', 0)),
                            'is_simulated': False,
                            'bats': 'Unknown'  # Will be populated later
                        }
                        
                        # Calculate HR rate
                        if player_data['at_bats'] > 0:
                            player_data['hr_rate'] = player_data['home_runs'] / player_data['at_bats']
                        else:
                            player_data['hr_rate'] = 0.0
                        
                        all_player_stats[player_name] = player_data
                        logger.info(f"✓ Found stats for {player_name}: {games}G, {player_data['home_runs']}HR, {player_data['at_bats']}AB")
                    else:
                        logger.info(f"No 2025 stats available for {player_name}")
                        skipped_players.append(player_name)
                else:
                    logger.info(f"No stats data in response for {player_name}")
                    skipped_players.append(player_name)
                    
            except Exception as e:
                logger.error(f"Error fetching stats for {player_name} (ID: {player_id}): {str(e)}")
                skipped_players.append(player_name)
                
        except Exception as e:
            # This is where the error was happening - player_id wasn't defined yet
            logger.error(f"Error processing {player_name}: {str(e)}")
            skipped_players.append(player_name)
        
        # Rate limiting
        time.sleep(0.2)
    
    if skipped_players:
        logger.info(f"Skipped {len(skipped_players)} players due to missing or insufficient data")
        logger.info(f"First 10 skipped players: {', '.join(skipped_players[:10])}...")
    
    logger.info(f"Fetched stats for {len(all_player_stats)} players")
    return all_player_stats


def fetch_pitcher_stats(pitcher_names):
    """Fetch pitching stats for given pitchers using MLB Stats API"""
    logger.info(f"Fetching stats for {len(pitcher_names)} pitchers using MLB Stats API")
    all_pitcher_stats = {}
    
    for pitcher_name in pitcher_names:
        try:
            # Skip TBD pitchers
            if pitcher_name.upper() == 'TBD':
                continue
                
            # Search for pitcher
            pitcher_search = statsapi.lookup_player(pitcher_name)
            
            if not pitcher_search:
                logger.info(f"Pitcher not found: {pitcher_name}")
                continue
            
            # Get the first match
            pitcher_info = pitcher_search[0]
            pitcher_id = pitcher_info['id']  # Define pitcher_id HERE
            
            # Get pitcher stats for 2025 season
            try:
                pitcher_stats_response = statsapi.player_stat_data(
                    pitcher_id,
                    group="pitching",
                    type="season",
                    sportId=1,
                    season=2025
                )
                
                if 'stats' in pitcher_stats_response:
                    stats = pitcher_stats_response['stats']
                    
                    if isinstance(stats, list) and len(stats) > 0:
                        all_stats = stats[0].get('stats', {})
                        
                        # Check if pitcher has meaningful stats
                        innings = float(all_stats.get('inningsPitched', 0))
                        if innings < 5:  # Lowered threshold for early season
                            logger.info(f"Insufficient innings for {pitcher_name}: {innings}")
                            continue
                        
                        pitcher_data = {
                            'pitcher_id': pitcher_id,
                            'pitcher_name': pitcher_name,
                            'games': int(all_stats.get('gamesPlayed', 0)),
                            'games_started': int(all_stats.get('gamesStarted', 0)),
                            'innings_pitched': innings,
                            'hits_allowed': int(all_stats.get('hits', 0)),
                            'runs_allowed': int(all_stats.get('runs', 0)),
                            'earned_runs': int(all_stats.get('earnedRuns', 0)),
                            'home_runs_allowed': int(all_stats.get('homeRuns', 0)),
                            'walks_allowed': int(all_stats.get('baseOnBalls', 0)),
                            'strikeouts': int(all_stats.get('strikeOuts', 0)),
                            'era': float(all_stats.get('era', 0)),
                            'whip': float(all_stats.get('whip', 0)),
                            'batting_avg_against': float(all_stats.get('avg', 0)),
                            'throws': 'Unknown'  # Will be populated later
                        }
                        
                        # Calculate HR/9
                        if pitcher_data['innings_pitched'] > 0:
                            pitcher_data['hr_per_9'] = (pitcher_data['home_runs_allowed'] * 9) / pitcher_data['innings_pitched']
                        else:
                            pitcher_data['hr_per_9'] = 0.0
                        
                        all_pitcher_stats[pitcher_name] = pitcher_data
                        logger.info(f"✓ Found stats for pitcher {pitcher_name}: {innings}IP, {pitcher_data['home_runs_allowed']}HR allowed")
                        
            except Exception as e:
                logger.error(f"Error fetching pitcher stats for {pitcher_name} (ID: {pitcher_id}): {str(e)}")
                
        except Exception as e:
            # This is where the error was happening for pitchers
            logger.error(f"Error processing pitcher {pitcher_name}: {str(e)}")
        
        # Rate limiting
        time.sleep(0.2)
    
    logger.info(f"Fetched stats for {len(all_pitcher_stats)} pitchers")
    return all_pitcher_stats


def get_player_names_from_lineups(lineups):
    """Extract all unique player names from lineups"""
    player_names = set()
    
    for game_id, game_lineups in lineups.items():
        for team in ['home', 'away']:
            if team in game_lineups and game_lineups[team]:
                for player in game_lineups[team]:
                    if player and isinstance(player, str) and player.strip():
                        player_names.add(player.strip())
    
    return list(player_names)


def get_pitcher_names_from_probable_pitchers(probable_pitchers):
    """Extract all unique pitcher names from probable pitchers"""
    pitcher_names = set()
    
    for game_id, pitchers in probable_pitchers.items():
        for team in ['home', 'away']:
            if team in pitchers and pitchers[team]:
                pitcher_name = pitchers[team]
                if pitcher_name and isinstance(pitcher_name, str) and pitcher_name.upper() != 'TBD':
                    pitcher_names.add(pitcher_name.strip())
    
    return list(pitcher_names)