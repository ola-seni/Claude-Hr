import os
import datetime
import json
import logging
import pandas as pd
from mlb_hr_predictor import MLBHomeRunPredictor
from rotowire_lineups import fetch_rotowire_expected_lineups, convert_rotowire_data_to_mlb_format, check_today_and_tomorrow

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MLB-HR-Predictor-Runner")

def main():
    # Determine run mode based on time
    current_hour = datetime.datetime.now().hour
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    
    # Early run mode at 6AM
    if current_hour < 10:  # Early morning run (before 10AM)
        logger.info("Executing EARLY run with Rotowire expected lineups")
        run_mode = "early"
        use_rotowire = True
    else:
        logger.info(f"Executing MIDDAY run at {current_hour}:00")
        run_mode = "midday"
        use_rotowire = False
    
    # Load game tracking data
    tracking_file = "game_tracking.json"
    tracked_games = {}
    
    if os.path.exists(tracking_file):
        with open(tracking_file, "r") as f:
            tracked_games = json.load(f)
    
    # Initialize predictor
    predictor = MLBHomeRunPredictor()
    
    # Fetch today's games
    predictor.fetch_games()
    
    # For early run, try to use Rotowire expected lineups
    if run_mode == "early" and use_rotowire:
        # Reset tracking for a new day
        tracked_games = {}
        
        # Try to get expected lineups from Rotowire for both today and tomorrow
        # This selects whichever has better lineup data
        rotowire_lineups, date_used = check_today_and_tomorrow()
        
        if rotowire_lineups:
            logger.info(f"Successfully fetched {len(rotowire_lineups)} expected lineups from Rotowire for {date_used}")
            
            # Check if any lineups actually have players
            has_players = False
            for game_id, data in rotowire_lineups.items():
                if len(data.get('home', [])) > 0 or len(data.get('away', [])) > 0:
                    has_players = True
                    break
            
            if has_players:
                logger.info("Found games with player lineups in Rotowire data")
                # Convert to our format
                lineups, probable_pitchers = convert_rotowire_data_to_mlb_format(rotowire_lineups, date_used)
                
                # Override the default lineup fetching
                predictor.lineups = lineups
                predictor.probable_pitchers = probable_pitchers
                
                # If we're using Rotowire data for tomorrow, make sure predictor knows
                if date_used != today:
                    logger.info(f"Setting predictor date to {date_used} based on Rotowire data")
                    predictor.today = date_used
                
                # Force early run mode
                predictor.early_run = True
                
                # Run predictor with Rotowire data
                predictor.run()
            else:
                logger.warning("Found games but no players in Rotowire lineups, using pitcher-only approach")
                # First, get pitchers from Rotowire (they might have pitchers but no lineups)
                pitchers_from_rotowire = {}
                for game_id, data in rotowire_lineups.items():
                    home_pitcher = data.get('home_pitcher', 'TBD')
                    away_pitcher = data.get('away_pitcher', 'TBD')
                    
                    # Only use if not TBD
                    if home_pitcher != 'TBD' or away_pitcher != 'TBD':
                        pitchers_from_rotowire[game_id] = {
                            'home': home_pitcher,
                            'away': away_pitcher
                        }
                
                # Run with standard approach to get probable pitchers
                predictor.early_run = True
                predictor.fetch_lineups_and_pitchers()
                
                # Update with any pitchers found in Rotowire
                predictor.probable_pitchers.update(pitchers_from_rotowire)
                
                # Run predictor with hybrid approach
                predictor.run()
        else:
            logger.warning("Could not fetch any games from Rotowire, falling back to standard approach")
            # Run with standard approach (probable pitchers only)
            predictor.early_run = True
            predictor.fetch_lineups_and_pitchers()
            predictor.run()
    
    # For midday run, use standard approach with confirmed lineups
    else:
        # Set to midday run mode
        predictor.early_run = False
        
        # Fetch lineups
        predictor.fetch_lineups_and_pitchers()
        
        # Get games with confirmed lineups that we haven't predicted yet
        games_with_new_lineups = []
        
        for game_id, lineups in predictor.lineups.items():
            # Only process games with confirmed lineups that we haven't predicted yet
            if (game_id not in tracked_games.get("predicted", []) and 
                len(lineups.get("home", [])) > 0 and 
                len(lineups.get("away", [])) > 0):
                games_with_new_lineups.append(game_id)
        
        if games_with_new_lineups:
            logger.info(f"Found {len(games_with_new_lineups)} games with new confirmed lineups")
            
            # Filter to only these games
            predictor.filter_games(games_with_new_lineups)
            
            # Run predictor
            predictor.run()
            
            # Update tracking
            if "predicted" not in tracked_games:
                tracked_games["predicted"] = []
            tracked_games["predicted"].extend(games_with_new_lineups)
        else:
            logger.info("No new confirmed lineups found, checking for games with any lineup data")
            
            # If we have no confirmed lineups, try to predict any games that have partial lineup data
            games_with_any_data = []
            for game_id, lineup in predictor.lineups.items():
                if (game_id not in tracked_games.get("predicted", []) and 
                    (len(lineup.get("home", [])) > 0 or len(lineup.get("away", [])) > 0)):
                    games_with_any_data.append(game_id)
            
            if games_with_any_data:
                logger.info(f"Found {len(games_with_any_data)} games with at least partial lineup data")
                
                # Filter to only these games
                predictor.filter_games(games_with_any_data)
                
                # Run predictor
                predictor.run()
                
                # Update tracking
                if "predicted" not in tracked_games:
                    tracked_games["predicted"] = []
                tracked_games["predicted"].extend(games_with_any_data)
            else:
                logger.info("No games with new lineup data found, skipping prediction run")
    
    # Save tracking data
    with open(tracking_file, "w") as f:
        json.dump(tracked_games, f)

if __name__ == "__main__":
    main()
