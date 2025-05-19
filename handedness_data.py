import pandas as pd
import os
import logging

logger = logging.getLogger('MLB-HR-Predictor')

# Load handedness data from separate CSV files
def load_player_handedness():
    """Load batter and pitcher handedness from CSV files"""
    # Initialize empty dictionaries
    batters_dict = {}
    pitchers_dict = {}
    
    # Load batters handedness
    batters_csv = os.path.join(os.path.dirname(__file__), 'data', 'batters_handedness.csv')
    if os.path.exists(batters_csv):
        try:
            batters_df = pd.read_csv(batters_csv)
            logger.info(f"Loaded batting handedness for {len(batters_df)} players")
            
            for _, row in batters_df.iterrows():
                # Primary name entry
                batters_dict[row['player_name']] = {
                    'mlbmid': row['mlbmid'],
                    'bats': row['bats']
                }
        except Exception as e:
            logger.error(f"Error loading batters handedness: {e}")
    else:
        logger.warning(f"Batters handedness file not found: {batters_csv}")
    
    # Load pitchers handedness
    pitchers_csv = os.path.join(os.path.dirname(__file__), 'data', 'pitchers_handedness.csv')
    if os.path.exists(pitchers_csv):
        try:
            pitchers_df = pd.read_csv(pitchers_csv)
            logger.info(f"Loaded pitching handedness for {len(pitchers_df)} players")
            
            for _, row in pitchers_df.iterrows():
                # Primary name entry
                pitchers_dict[row['player_name']] = {
                    'mlbmid': row['mlbmid'],
                    'throws': row['throws']
                }
        except Exception as e:
            logger.error(f"Error loading pitchers handedness: {e}")
    else:
        logger.warning(f"Pitchers handedness file not found: {pitchers_csv}")
    
    return batters_dict, pitchers_dict

# Load data at module import time
BATTERS_HANDEDNESS, PITCHERS_HANDEDNESS = load_player_handedness()

def get_batter_handedness(player_name):
    """Get batter handedness with name variation handling"""
    # Exact match
    if player_name in BATTERS_HANDEDNESS:
        return BATTERS_HANDEDNESS[player_name]['bats']
    
    # Try fuzzy matching on last name
    player_parts = player_name.split()
    if len(player_parts) > 1:
        player_last = player_parts[-1].lower()
        player_first = player_parts[0].lower()
        
        for name in BATTERS_HANDEDNESS:
            name_parts = name.split()
            if len(name_parts) > 1:
                if name_parts[-1].lower() == player_last:
                    # Last name matches, check first initial
                    if name_parts[0].lower().startswith(player_first[0]):
                        return BATTERS_HANDEDNESS[name]['bats']
    
    # Nothing found
    return 'Unknown'

def get_pitcher_handedness(pitcher_name):
    """Get pitcher handedness with name variation handling"""
    # Exact match
    if pitcher_name in PITCHERS_HANDEDNESS:
        return PITCHERS_HANDEDNESS[pitcher_name]['throws']
    
    # Try fuzzy matching on last name
    pitcher_parts = pitcher_name.split()
    if len(pitcher_parts) > 1:
        pitcher_last = pitcher_parts[-1].lower()
        pitcher_first = pitcher_parts[0].lower()
        
        for name in PITCHERS_HANDEDNESS:
            name_parts = name.split()
            if len(name_parts) > 1:
                if name_parts[-1].lower() == pitcher_last:
                    # Last name matches, check first initial
                    if name_parts[0].lower().startswith(pitcher_first[0]):
                        return PITCHERS_HANDEDNESS[name]['throws']
    
    # Nothing found
    return 'Unknown'