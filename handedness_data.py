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
def normalize_name_for_matching(name):
    """Normalize names for better matching"""
    if not name:
        return ""
    
    # Remove common abbreviations
    name = name.replace("Jr.", "").replace("Sr.", "").replace("III", "").replace("II", "")
    
    # Handle different formats
    if "," in name:  # "Last, First" format
        parts = name.split(",")
        name = f"{parts[1].strip()} {parts[0].strip()}"
    
    # Remove extra spaces and convert to lowercase
    name = " ".join(name.split()).lower()
    
    return name

def get_batter_handedness(player_name):
    """Get batter handedness with enhanced matching"""
    if not player_name:
        return 'Unknown'
    
    # Strategy 1: Direct match
    if player_name in BATTERS_HANDEDNESS:
        return BATTERS_HANDEDNESS[player_name]['bats']
    
    # Strategy 2: Case-insensitive match
    player_lower = player_name.lower()
    for name, data in BATTERS_HANDEDNESS.items():
        if name.lower() == player_lower:
            logger.info(f"✅ Handedness match (case): '{player_name}' -> '{name}' -> {data['bats']}")
            return data['bats']
    
    # Strategy 3: Try "Last, First" format (CSV is likely in this format)
    if ' ' in player_name and ',' not in player_name:
        parts = player_name.split()
        if len(parts) >= 2:
            # Convert "Ronald Acuna" to "Acuna, Ronald"
            first, last = parts[0], parts[-1]
            reversed_name = f"{last}, {first}"
            
            if reversed_name in BATTERS_HANDEDNESS:
                logger.info(f"✅ Handedness match (reversed): '{player_name}' -> '{reversed_name}' -> {BATTERS_HANDEDNESS[reversed_name]['bats']}")
                return BATTERS_HANDEDNESS[reversed_name]['bats']
            
            # Also try case-insensitive reversed
            for name, data in BATTERS_HANDEDNESS.items():
                if name.lower() == reversed_name.lower():
                    logger.info(f"✅ Handedness match (reversed+case): '{player_name}' -> '{name}' -> {data['bats']}")
                    return data['bats']
    
    # Strategy 4: Handle names with accents (Ronald Acuna vs Ronald Acuña)
    import unicodedata
    normalized_input = unicodedata.normalize('NFKD', player_name).encode('ASCII', 'ignore').decode('ASCII').lower()
    
    for name, data in BATTERS_HANDEDNESS.items():
        normalized_csv = unicodedata.normalize('NFKD', name).encode('ASCII', 'ignore').decode('ASCII').lower()
        if normalized_csv == normalized_input:
            logger.info(f"✅ Handedness match (normalized): '{player_name}' -> '{name}' -> {data['bats']}")
            return data['bats']
    
    # Strategy 5: Known players manual override
    known_players = {
        'ronald acuna': 'R', 'ronald acuña': 'R', 'acuna jr': 'R', 'acuña jr': 'R',
        'aaron judge': 'R', 'judge': 'R',
        'shohei ohtani': 'L', 'ohtani': 'L',
        'juan soto': 'L', 'soto': 'L',
        'mookie betts': 'R', 'betts': 'R',
        'vladimir guerrero': 'R', 'guerrero jr': 'R',
        'kyle schwarber': 'L', 'schwarber': 'L',
        'corbin carroll': 'L', 'carroll': 'L',
        'cal raleigh': 'S', 'raleigh': 'S',
        'matthew lugo': 'R', 'lugo': 'R',
        'logan davidson': 'R', 'davidson': 'R',
        'kody clemens': 'L', 'clemens': 'L',
        'daulton varsho': 'L', 'varsho': 'L',
        'carson kelly': 'R', 'kelly': 'R',
        'seiya suzuki': 'R', 'suzuki': 'R'
    }
    
    normalized_input = normalized_input.strip()
    if normalized_input in known_players:
        logger.info(f"✅ Known player handedness: '{player_name}' -> {known_players[normalized_input]}")
        return known_players[normalized_input]
    
    # Try just last name in known players
    if ' ' in player_name:
        last_name = player_name.split()[-1].lower()
        if last_name in known_players:
            logger.info(f"✅ Known player (last name): '{player_name}' -> {known_players[last_name]}")
            return known_players[last_name]
    
    # Strategy 6: Partial last name match (more careful)
    if ' ' in player_name:
        last_name = player_name.split()[-1].lower()
        matches = []
        
        for name, data in BATTERS_HANDEDNESS.items():
            if last_name in name.lower() and len(name.split()) >= 2:
                csv_last = name.split()[-1].lower() if ',' not in name else name.split(',')[0].lower()
                if csv_last == last_name:
                    matches.append((name, data['bats']))
        
        # If exactly one match, use it
        if len(matches) == 1:
            logger.info(f"✅ Handedness match (last name): '{player_name}' -> '{matches[0][0]}' -> {matches[0][1]}")
            return matches[0][1]
    
    # No match found
    logger.warning(f"❌ Could not find batting handedness for: {player_name}")
    return 'Unknown'

def get_pitcher_handedness(pitcher_name):
    """Get pitcher handedness with enhanced matching"""
    if not pitcher_name or pitcher_name in ["TBD", "Unknown"]:
        return 'Unknown'
    
    # Strategy 1: Direct match
    if pitcher_name in PITCHERS_HANDEDNESS:
        return PITCHERS_HANDEDNESS[pitcher_name]['throws']
    
    # Strategy 2: Case-insensitive match
    pitcher_lower = pitcher_name.lower()
    for name, data in PITCHERS_HANDEDNESS.items():
        if name.lower() == pitcher_lower:
            logger.info(f"✅ Pitcher handedness match (case): '{pitcher_name}' -> '{name}' -> {data['throws']}")
            return data['throws']
    
    # Strategy 3: Try "Last, First" format
    if ' ' in pitcher_name and ',' not in pitcher_name:
        parts = pitcher_name.split()
        if len(parts) >= 2:
            first, last = parts[0], parts[-1]
            reversed_name = f"{last}, {first}"
            
            if reversed_name in PITCHERS_HANDEDNESS:
                logger.info(f"✅ Pitcher handedness (reversed): '{pitcher_name}' -> '{reversed_name}' -> {PITCHERS_HANDEDNESS[reversed_name]['throws']}")
                return PITCHERS_HANDEDNESS[reversed_name]['throws']
    
    # Strategy 4: Known pitchers manual override
    known_pitchers = {
        'zack wheeler': 'R', 'wheeler': 'R',
        'paul skenes': 'R', 'skenes': 'R',
        'clarke schmidt': 'R', 'schmidt': 'R',
        'yusei kikuchi': 'L', 'kikuchi': 'L',
        'jacob degrom': 'R', 'degrom': 'R',
        'gerrit cole': 'R', 'cole': 'R',
        'lance mccullers': 'R', 'mccullers jr': 'R',
        'aj smith-shawver': 'R', 'smith-shawver': 'R',
        'trevor williams': 'R', 'williams': 'R',
        'tyler mahle': 'R', 'mahle': 'R',
        'jakob junis': 'R', 'junis': 'R',
        'drew rasmussen': 'R', 'rasmussen': 'R',
        'tanner gordon': 'R', 'gordon': 'R'
    }
    
    # Normalize for lookup
    import unicodedata
    normalized_input = unicodedata.normalize('NFKD', pitcher_name).encode('ASCII', 'ignore').decode('ASCII').lower().strip()
    
    if normalized_input in known_pitchers:
        logger.info(f"✅ Known pitcher handedness: '{pitcher_name}' -> {known_pitchers[normalized_input]}")
        return known_pitchers[normalized_input]
    
    # Try just last name
    if ' ' in pitcher_name:
        last_name = pitcher_name.split()[-1].lower()
        if last_name in known_pitchers:
            logger.info(f"✅ Known pitcher (last name): '{pitcher_name}' -> {known_pitchers[last_name]}")
            return known_pitchers[last_name]
    
    # Strategy 5: Partial match by last name
    if ' ' in pitcher_name:
        last_name = pitcher_name.split()[-1].lower()
        matches = []
        
        for name, data in PITCHERS_HANDEDNESS.items():
            if last_name in name.lower() and len(name.split()) >= 2:
                csv_last = name.split()[-1].lower() if ',' not in name else name.split(',')[0].lower()
                if csv_last == last_name:
                    matches.append((name, data['throws']))
        
        if len(matches) == 1:
            logger.info(f"✅ Pitcher handedness (last name): '{pitcher_name}' -> '{matches[0][0]}' -> {matches[0][1]}")
            return matches[0][1]
    
    logger.warning(f"❌ Could not find pitching handedness for: {pitcher_name}")
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
