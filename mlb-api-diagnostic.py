import statsapi
import logging
import sys
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger('MLB-API-Diagnostics')

def check_available_seasons():
    """Check what seasons are available in the MLB Stats API"""
    try:
        # Try to get the list of seasons
        seasons_data = statsapi.get('seasons', {})
        logger.info(f"Seasons data structure: {type(seasons_data)}")
        
        if isinstance(seasons_data, dict) and 'seasons' in seasons_data:
            seasons = seasons_data['seasons']
            if seasons:
                latest_season = max(season.get('seasonId', 0) for season in seasons)
                logger.info(f"Latest season available: {latest_season}")
                
                # Print the 5 most recent seasons
                recent_seasons = sorted(
                    [s for s in seasons if 'seasonId' in s],
                    key=lambda x: x['seasonId'],
                    reverse=True
                )[:5]
                
                logger.info("5 most recent seasons:")
                for s in recent_seasons:
                    logger.info(f"Season ID: {s.get('seasonId')}, Name: {s.get('seasonName', 'Unknown')}")
        else:
            logger.warning("Unexpected response format from seasons endpoint")
    except Exception as e:
        logger.error(f"Error getting seasons: {e}")

def test_player_stats(player_name="Aaron Judge", season=2025):
    """Test getting stats for a specific player and season"""
    try:
        # Look up player ID
        player_search = statsapi.lookup_player(player_name)
        if not player_search:
            logger.warning(f"Player not found: {player_name}")
            return
            
        player_id = player_search[0]['id']
        logger.info(f"Found player ID for {player_name}: {player_id}")
        
        # Try to get stats for specified season
        logger.info(f"Attempting to get stats for season {season}")
        stats_response = statsapi.player_stat_data(
            player_id, 
            group="hitting", 
            type="season", 
            sportId=1,
            season=season
        )
        
        # Log response structure
        logger.info(f"API Response type: {type(stats_response)}")
        logger.info(f"API Response keys: {stats_response.keys() if isinstance(stats_response, dict) else 'Not a dict'}")
        
        # Check if we got any stats
        if isinstance(stats_response, dict) and 'stats' in stats_response:
            stats = stats_response['stats']
            logger.info(f"Stats found: {len(stats)} stat groups")
            
            for i, stat_group in enumerate(stats):
                if 'type' in stat_group and 'displayName' in stat_group['type']:
                    logger.info(f"Stat group {i}: {stat_group['type']['displayName']}")
                    if 'stats' in stat_group:
                        sample_stats = dict(list(stat_group['stats'].items())[:5]) if isinstance(stat_group['stats'], dict) else "Not a dict"
                        logger.info(f"Sample stats: {sample_stats}")
                else:
                    logger.info(f"Stat group {i}: Missing type info")
        else:
            logger.warning("No stats found in response")
            
        # Try to get games for the season
        try:
            today = f"{season}-05-17"  # Use May 17 for the test
            schedule = statsapi.schedule(date=today)
            logger.info(f"Schedule for {today}: {len(schedule)} games")
            if schedule:
                logger.info(f"First game: {schedule[0]}")
        except Exception as e:
            logger.error(f"Error getting schedule: {e}")
            
    except Exception as e:
        logger.error(f"Error in test: {e}")

def main():
    logger.info("Starting MLB Stats API diagnostics")
    
    # Check available seasons
    logger.info("Checking available seasons...")
    check_available_seasons()
    
    # Test with 2024 (likely current real season)
    logger.info("\nTesting with 2024 season...")
    test_player_stats(season=2024)
    
    # Test with 2025 (your target season)
    logger.info("\nTesting with 2025 season...")
    test_player_stats(season=2025)
    
    logger.info("Diagnostics complete")

if __name__ == "__main__":
    main()
