import logging
import sys
import pandas as pd
import numpy as np
from stats_fetcher import fetch_player_stats, fetch_pitcher_stats, get_player_names_from_lineups, get_pitcher_names_from_probable_pitchers

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger('StatsFetcher-Debug')

def create_test_lineups_and_pitchers():
    """Create sample lineups and pitchers for testing"""
    # Create sample lineups
    lineups = {
        'NYY_NYM_2025-05-17': {
            'home': ['Aaron Judge', 'Juan Soto', 'Anthony Volpe', 'Anthony Rizzo', 'Gleyber Torres', 
                    'Alex Verdugo', 'Giancarlo Stanton', 'Austin Wells', 'DJ LeMahieu'],
            'away': ['Francisco Lindor', 'Brandon Nimmo', 'Pete Alonso', 'Jeff McNeil', 'Starling Marte',
                    'Luis Torrens', 'Luis Guillorme', 'Mark Vientos', 'Harrison Bader']
        },
        'BOS_ATL_2025-05-17': {
            'home': ['Rafael Devers', 'Trevor Story', 'Masataka Yoshida', 'Jarren Duran', 'Connor Wong',
                    'Ceddanne Rafaela', 'Vaughn Grissom', 'Wilyer Abreu', 'David Hamilton'],
            'away': ['Ronald Acuña Jr.', 'Ozzie Albies', 'Austin Riley', 'Matt Olson', 'Marcell Ozuna',
                    'Sean Murphy', 'Michael Harris II', 'Orlando Arcia', 'Drake Baldwin']
        }
    }
    
    # Create sample probable pitchers
    probable_pitchers = {
        'NYY_NYM_2025-05-17': {
            'home': 'Clarke Schmidt',
            'away': 'Griffin Canning'
        },
        'BOS_ATL_2025-05-17': {
            'home': 'Tanner Houck',
            'away': 'Max Fried'
        }
    }
    
    return lineups, probable_pitchers

def main():
    """Test the stats fetcher functions independently"""
    logger.info("Starting stats fetcher debug test")
    
    # Create test data
    lineups, probable_pitchers = create_test_lineups_and_pitchers()
    logger.info(f"Created test data with {len(lineups)} games")
    
    # Extract player names
    player_names = get_player_names_from_lineups(lineups)
    logger.info(f"Extracted {len(player_names)} player names from lineups")
    
    # Extract pitcher names
    pitcher_names = get_pitcher_names_from_probable_pitchers(probable_pitchers)
    logger.info(f"Extracted {len(pitcher_names)} pitcher names from probable pitchers")
    
    # Fetch player stats
    logger.info("Fetching player stats...")
    player_stats, recent_player_stats = fetch_player_stats(player_names)
    logger.info(f"Fetched stats for {len(player_stats)} players")
    
    # Print sample player stats
    if player_stats:
        sample_player = next(iter(player_stats))
        logger.info(f"Sample player stats for {sample_player}:")
        logger.info(f"  Games: {player_stats[sample_player]['games']}")
        logger.info(f"  HR: {player_stats[sample_player]['hr']}")
        logger.info(f"  HR/Game: {player_stats[sample_player]['hr_per_game']:.3f}")
        logger.info(f"  Exit Velo: {player_stats[sample_player]['exit_velo']:.1f}")
        logger.info(f"  Launch Angle: {player_stats[sample_player]['launch_angle']:.1f}")
        logger.info(f"  Barrel%: {player_stats[sample_player]['barrel_pct']:.3f}")
    
    # Fetch pitcher stats
    logger.info("\nFetching pitcher stats...")
    pitcher_stats, recent_pitcher_stats = fetch_pitcher_stats(pitcher_names)
    logger.info(f"Fetched stats for {len(pitcher_stats)} pitchers")
    
    # Print sample pitcher stats
    if pitcher_stats:
        sample_pitcher = next(iter(pitcher_stats))
        logger.info(f"Sample pitcher stats for {sample_pitcher}:")
        logger.info(f"  Games: {pitcher_stats[sample_pitcher]['games']}")
        logger.info(f"  IP: {pitcher_stats[sample_pitcher]['ip']:.1f}")
        logger.info(f"  HR/9: {pitcher_stats[sample_pitcher]['hr_per_9']:.2f}")
        logger.info(f"  GB/FB: {pitcher_stats[sample_pitcher]['gb_fb_ratio']:.2f}")
        logger.info(f"  Fastball%: {pitcher_stats[sample_pitcher]['fastball_pct']:.3f}")
    
    logger.info("Stats fetcher debug test complete")

if __name__ == "__main__":
    main()
