import pandas as pd
import os
import logging
import csv

logger = logging.getLogger('MLB-HR-Predictor')

# Global dictionaries
BATTERS_HANDEDNESS = {}
PITCHERS_HANDEDNESS = {}

def load_csv_file(filepath, key_field, value_fields):
    """Load CSV file with robust error handling"""
    result = {}
    logger.info(f"Attempting to load CSV from: {filepath}")
    
    if not os.path.exists(filepath):
        logger.error(f"CSV file does not exist: {filepath}")
        return result
        
    try:
        # Print file size for debugging
        file_size = os.path.getsize(filepath)
        logger.info(f"CSV file size: {file_size} bytes")
        
        # Try to open and read the first few lines to see what's in the file
        with open(filepath, 'r') as f:
            sample = f.read(200)
            logger.info(f"CSV sample: {sample}")
            
        # Process the CSV file
        with open(filepath, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Skip rows without the key field
                if key_field not in row:
                    continue
                    
                key = row[key_field]
                values = {field: row.get(field, '') for field in value_fields if field in row}
                
                # Skip rows without required values
                if not values:
                    continue
                    
                # Store the data
                result[key] = values
                
                # Also store variations to improve matching
                
                # Variation 1: Convert "Last, First" to "First Last"
                if ',' in key:
                    last, first = key.split(',', 1)
                    reversed_name = f"{first.strip()} {last.strip()}"
                    result[reversed_name] = values
                
                # Variation 2: Just the last name (helpful for partial matches)
                parts = key.split()
                if len(parts) > 1:
                    last_name = parts[-1]
                    result[last_name] = values
                
        logger.info(f"Successfully loaded {len(result)} entries from {filepath}")
        return result
    except Exception as e:
        logger.error(f"Error loading CSV file {filepath}: {e}")
        return result

def load_player_handedness():
    """Load batter and pitcher handedness from CSV files with robust error handling"""
    global BATTERS_HANDEDNESS, PITCHERS_HANDEDNESS
    
    # Try multiple possible locations
    locations = [
        '.',                           # Current directory
        os.path.dirname(__file__),     # Directory of this file
        os.path.dirname(os.path.abspath(__file__))  # Absolute path to directory of this file
    ]
    
    batters_dict = {}
    pitchers_dict = {}
    
    # Try each location for batters CSV
    for location in locations:
        batters_path = os.path.join(location, 'batters_handedness.csv')
        if os.path.exists(batters_path):
            logger.info(f"Found batters CSV at: {batters_path}")
            batters_dict = load_csv_file(batters_path, 'player_name', ['mlbmid', 'bats'])
            if batters_dict:
                break
    
    # Try each location for pitchers CSV
    for location in locations:
        pitchers_path = os.path.join(location, 'pitchers_handedness.csv')
        if os.path.exists(pitchers_path):
            logger.info(f"Found pitchers CSV at: {pitchers_path}")
            pitchers_dict = load_csv_file(pitchers_path, 'player_name', ['mlbmid', 'throws'])
            if pitchers_dict:
                break
    
    # Set global variables
    BATTERS_HANDEDNESS = batters_dict
    PITCHERS_HANDEDNESS = pitchers_dict
    
    # Log the results
    logger.info(f"Loaded {len(batters_dict)} batter entries and {len(pitchers_dict)} pitcher entries")
    
    return batters_dict, pitchers_dict

def get_batter_handedness(player_name):
    """Get batter handedness with improved name matching"""
    if not player_name:
        return 'Unknown'
    
    # Direct match
    if player_name in BATTERS_HANDEDNESS:
        return BATTERS_HANDEDNESS[player_name]['bats']
    
    # Try case-insensitive match
    player_lower = player_name.lower()
    for name, data in BATTERS_HANDEDNESS.items():
        if name.lower() == player_lower:
            return data['bats']
    
    # Handle abbreviated names (like "W. Contreras")
    if '.' in player_name:
        parts = player_name.split('.')
        if len(parts) > 1:
            last_name = parts[1].strip()
            
            # Try to find a match by last name
            for name, data in BATTERS_HANDEDNESS.items():
                name_parts = name.split()
                if len(name_parts) > 1 and name_parts[-1].lower() == last_name.lower():
                    return data['bats']
    
    # Try matching just the last name
    parts = player_name.split()
    if len(parts) > 1:
        last_name = parts[-1]
        
        for name, data in BATTERS_HANDEDNESS.items():
            name_parts = name.split()
            if len(name_parts) > 1 and name_parts[-1].lower() == last_name.lower():
                return data['bats']
    
    # No match found
    logger.warning(f"Could not find batting handedness for: {player_name}")
    return 'Unknown'

def get_pitcher_handedness(pitcher_name):
    """Get pitcher handedness with improved name matching"""
    if not pitcher_name or pitcher_name in ["TBD", "Unknown"]:
        return 'Unknown'
    
    # Direct match
    if pitcher_name in PITCHERS_HANDEDNESS:
        return PITCHERS_HANDEDNESS[pitcher_name]['throws']
    
    # Try case-insensitive match
    pitcher_lower = pitcher_name.lower()
    for name, data in PITCHERS_HANDEDNESS.items():
        if name.lower() == pitcher_lower:
            return data['throws']
    
    # Handle abbreviated names (like "G. Cole")
    if '.' in pitcher_name:
        parts = pitcher_name.split('.')
        if len(parts) > 1:
            last_name = parts[1].strip()
            
            # Try to find a match by last name
            for name, data in PITCHERS_HANDEDNESS.items():
                name_parts = name.split()
                if len(name_parts) > 1 and name_parts[-1].lower() == last_name.lower():
                    return data['throws']
    
    # Try matching just the last name
    parts = pitcher_name.split()
    if len(parts) > 1:
        last_name = parts[-1]
        
        for name, data in PITCHERS_HANDEDNESS.items():
            name_parts = name.split()
            if len(name_parts) > 1 and name_parts[-1].lower() == last_name.lower():
                return data['throws']
    
    # No match found
    logger.warning(f"Could not find pitching handedness for: {pitcher_name}")
    return 'Unknown'

# Immediately load data when module is imported
BATTERS_HANDEDNESS, PITCHERS_HANDEDNESS = load_player_handedness()

# Print sample entries for debugging
if BATTERS_HANDEDNESS:
    sample_keys = list(BATTERS_HANDEDNESS.keys())[:5]
    logger.info(f"Sample batter entries: {sample_keys}")

if PITCHERS_HANDEDNESS:
    sample_keys = list(PITCHERS_HANDEDNESS.keys())[:5]
    logger.info(f"Sample pitcher entries: {sample_keys}")
