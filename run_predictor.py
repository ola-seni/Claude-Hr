import os
import datetime
import json
import logging
import pandas as pd
from mlb_hr_predictor import MLBHomeRunPredictor
from rotowire_lineups import fetch_rotowire_expected_lineups, convert_rotowire_data_to_mlb_format

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
        
        # Try to get expected lineups from Rotowire for tomorrow
        tomorrow = (datetime.datetime.now() + datetime.timedelta(days=1)).strftime('%Y-%m-%d')
        rotowire_lineups = fetch_rotowire_expected_lineups(tomorrow)
        
        if rotowire_lineups:
            logger.info(f"Successfully fetched {len(rotowire_lineups)} expected lineups from Rotowire")
            
            # Convert to our format
            lineups, probable_pitchers = convert_rotowire_data_to_mlb_format(rotowire_lineups, tomorrow)
            
            # Override the default lineup fetching
            predictor.lineups = lineups
            predictor.probable_pitchers = probable_pitchers
            
            # Force early run mode
            predictor.early_run = True
            
            # Run predictor
            predictor.run()
        else:
            logger.warning("Could not fetch Rotowire lineups, falling back to standard approach")
            # Run with standard approach (probable pitchers only)
            predictor.early_run = True
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
            logger.info("No new confirmed lineups found, skipping prediction run")
    
    # Save tracking data
    with open(tracking_file, "w") as f:
        json.dump(tracked_games, f)

if __name__ == "__main__":
    main()
