import logging
import sys
import pandas as pd
import datetime
from lineup_fetcher import fetch_lineups_and_pitchers

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger('LineupFetcher-Debug')

def create_test_games():
    """Create a sample games DataFrame for testing"""
    # Create sample games data
    games_data = [
        {
            'game_id': 'NYY_NYM_2025-05-17', 
            'game_id_mlb': 777888,  # This should match a real MLB game ID
            'date': '2025-05-17',
            'home_team': 'NYY',
            'away_team': 'NYM',
            'home_team_name': 'New York Yankees',
            'away_team_name': 'New York Mets',
            'ballpark': 'Yankee Stadium',
            'game_time': '2025-05-17T17:05:00Z'
        },
        # Add more test games if needed
    ]
    
    return pd.DataFrame(games_data)

def main():
    """Test the lineup fetcher function independently"""
    logger.info("Starting lineup fetcher debug test")
    
    # Create test data
    test_games = create_test_games()
    logger.info(f"Created test games data with {len(test_games)} games")
    
    # Test early run mode
    logger.info("Testing EARLY RUN mode")
    early_lineups, early_pitchers = fetch_lineups_and_pitchers(test_games, early_run=True)
    
    # Print results
    for game_id, lineup in early_lineups.items():
        logger.info(f"EARLY RUN - Game: {game_id}")
        logger.info(f"  Home lineup ({len(lineup['home'])} players): {lineup['home']}")
        logger.info(f"  Away lineup ({len(lineup['away'])} players): {lineup['away']}")
        
    for game_id, pitchers in early_pitchers.items():
        logger.info(f"EARLY RUN - Game: {game_id}")
        logger.info(f"  Home pitcher: {pitchers['home']}")
        logger.info(f"  Away pitcher: {pitchers['away']}")
    
    # Test midday run mode
    logger.info("\nTesting MIDDAY RUN mode")
    midday_lineups, midday_pitchers = fetch_lineups_and_pitchers(test_games, early_run=False)
    
    # Print results
    for game_id, lineup in midday_lineups.items():
        logger.info(f"MIDDAY RUN - Game: {game_id}")
        logger.info(f"  Home lineup ({len(lineup['home'])} players): {lineup['home']}")
        logger.info(f"  Away lineup ({len(lineup['away'])} players): {lineup['away']}")
        
    for game_id, pitchers in midday_pitchers.items():
        logger.info(f"MIDDAY RUN - Game: {game_id}")
        logger.info(f"  Home pitcher: {pitchers['home']}")
        logger.info(f"  Away pitcher: {pitchers['away']}")
    
    logger.info("Lineup fetcher debug test complete")

if __name__ == "__main__":
    main()
