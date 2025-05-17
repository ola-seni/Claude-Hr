# Create a new file called run_predictor.py
import os
import datetime
import json
import logging
from mlb_hr_predictor import MLBHomeRunPredictor  # Import your main class

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MLB-HR-Predictor-Runner")

def main():
    # Determine run mode based on time
    current_hour = datetime.datetime.now().hour
    
    # Early run mode at 6AM
    if current_hour == 6:
        logger.info("Executing EARLY run with probable pitchers")
        run_mode = "early"
    else:
        logger.info(f"Executing LINEUP CHECK run at {current_hour}:00")
        run_mode = "lineup_check"
    
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
    
    # Early run handles all games
    if run_mode == "early":
        # Reset tracking for a new day
        tracked_games = {}
        # Run early morning predictions
        predictor.early_run = True
        predictor.run()
        
    # Lineup check runs only handle games with newly available lineups
    else:
        # Fetch lineups without predictions yet
        predictor.early_run = False
        predictor.fetch_lineups_and_pitchers()
        
        # Get games with confirmed lineups that we haven't predicted yet
        games_with_new_lineups = []
        
        for game_id, lineups in predictor.lineups.items():
            if (game_id not in tracked_games.get("predicted", []) and 
                len(lineups.get("home", [])) > 0 and 
                len(lineups.get("away", [])) > 0):
                games_with_new_lineups.append(game_id)
        
        if games_with_new_lineups:
            logger.info(f"Found {len(games_with_new_lineups)} games with new lineups")
            # Filter to only these games
            predictor.filter_games(games_with_new_lineups)
            predictor.run()
            
            # Update tracking
            if "predicted" not in tracked_games:
                tracked_games["predicted"] = []
            tracked_games["predicted"].extend(games_with_new_lineups)
        else:
            logger.info("No new lineups found, skipping prediction run")
    
    # Save tracking data
    with open(tracking_file, "w") as f:
        json.dump(tracked_games, f)

if __name__ == "__main__":
    main()
