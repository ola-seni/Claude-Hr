import os
import datetime
import json
import logging
from mlb_hr_predictor import MLBHomeRunPredictor
from rotowire_lineups import fetch_rotowire_expected_lineups, convert_rotowire_data_to_mlb_format

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MLB-HR-Predictor-Runner")

def main():
    # Get today's date
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    current_time = datetime.datetime.now()
    
    # Initialize predictor
    predictor = MLBHomeRunPredictor()
    
    # Fetch today's games
    predictor.fetch_games()
    
    if predictor.games is None or predictor.games.empty:
        logger.error("No games found for today, exiting")
        return
    
    # Filter out games that have already started
    upcoming_games = []
    for _, game in predictor.games.iterrows():
        game_time_str = game.get('game_time', '')
        try:
            # Parse the game time
            game_time = datetime.datetime.strptime(game_time_str, "%Y-%m-%dT%H:%M:%SZ")
            # Adjust for timezone if needed
            # game_time = game_time.replace(tzinfo=datetime.timezone.utc).astimezone(tz=None)
            
            # Only include games that haven't started yet
            if game_time > current_time:
                upcoming_games.append(game['game_id'])
                logger.info(f"Game {game['game_id']} starts at {game_time_str}, adding to upcoming games")
            else:
                logger.info(f"Game {game['game_id']} has already started at {game_time_str}, skipping")
        except (ValueError, TypeError) as e:
            # If we can't parse the time, include the game by default
            upcoming_games.append(game['game_id'])
            logger.warning(f"Couldn't parse game time for {game['game_id']}: {e}, including by default")
    
    # Filter games to only upcoming ones
    if upcoming_games:
        logger.info(f"Found {len(upcoming_games)} upcoming games that haven't started yet")
        predictor.filter_games(upcoming_games)
    else:
        logger.info("No upcoming games found, all games have already started")
        return
    
    logger.info("Attempting to fetch lineups from Rotowire")
    
    # Try to get lineups from Rotowire
    rotowire_lineups = fetch_rotowire_expected_lineups(today)
    
    if rotowire_lineups:
        logger.info(f"Successfully fetched {len(rotowire_lineups)} lineups from Rotowire for {today}")
        
        # Check if any lineups actually have players
        has_players = False
        for game_id, data in rotowire_lineups.items():
            if len(data.get('home', [])) > 0 or len(data.get('away', [])) > 0:
                has_players = True
                break
        
        if has_players:
            logger.info("Found games with player lineups in Rotowire data")
            # Convert to our format
            lineups, probable_pitchers = convert_rotowire_data_to_mlb_format(rotowire_lineups, today)
            
            # Filter to only include upcoming games
            filtered_lineups = {k: v for k, v in lineups.items() if k in upcoming_games}
            filtered_pitchers = {k: v for k, v in probable_pitchers.items() if k in upcoming_games}
            
            if filtered_lineups:
                # Override the default lineup fetching
                predictor.lineups = filtered_lineups
                predictor.probable_pitchers = filtered_pitchers
                
                # Fetch weather and stats
                predictor.fetch_weather_data()
                predictor.fetch_player_stats()
                predictor.fetch_pitcher_stats()
                
                # Run predictor for all upcoming games with Rotowire data
                predictor.run()
            else:
                logger.warning("No upcoming games found in Rotowire data")
        else:
            logger.warning("Found games but no players in Rotowire lineups, falling back to MLB API")
            use_mlb_api = True
    else:
        logger.warning("Could not fetch any games from Rotowire, falling back to MLB API")
        use_mlb_api = True
    
    # If Rotowire didn't work or had no player data, fall back to MLB API
    if 'use_mlb_api' in locals() and use_mlb_api:
        logger.info("Using MLB Stats API to fetch lineups")
        
        # Fetch lineups and pitchers from MLB API
        predictor.fetch_lineups_and_pitchers()
        
        # Run predictor for all upcoming games
        predictor.run()

if __name__ == "__main__":
    main()
