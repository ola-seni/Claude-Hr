# baseball_savant.py
"""
Baseball Savant integration module for MLB HR Predictor.
Provides functions to fetch and process Statcast data.
"""

import os
import json
import time
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pybaseball import statcast, playerid_lookup, statcast_batter

# Configure logging
logger = logging.getLogger('Baseball-Savant')

def safe_float(value, default=0.0):
    """Convert a value to float, handling NAType and other invalid values"""
    try:
        if pd.isna(value):  # This handles pd.NA, None, np.nan, etc.
            return default
        return float(value)
    except (ValueError, TypeError):
        return default

class BaseballSavant:
    """Class for handling Baseball Savant data integration"""
    
    def __init__(self, cache_dir='savant_cache'):
        """Initialize the Baseball Savant handler"""
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
    
    def get_player_data(self, player_names, pitcher_names):
        """
        Main interface function - get Savant data for players and pitchers
        
        Parameters:
        -----------
        player_names : list
            List of batter names to get data for
        pitcher_names : list
            List of pitcher names to get data for
            
        Returns:
        --------
        tuple
            (batter_savant_data, pitcher_savant_data) - dictionaries with enhanced metrics
        """
        # Get raw Savant data
        savant_data = self._fetch_statcast_data()
        
        if not savant_data:
            logger.warning("No Statcast data available")
            return {}, {}
            
        # Process data for specific players
        batter_data = self._match_player_data(player_names, savant_data.get('batters', {}))
        pitcher_data = self._match_player_data(pitcher_names, savant_data.get('pitchers', {}))
        
        logger.info(f"Matched Savant data for {len(batter_data)} batters and {len(pitcher_data)} pitchers")
        
        return batter_data, pitcher_data
    
    def _fetch_statcast_data(self):
        """Fetch and process Baseball Savant data with enhanced error handling"""
        # Check for cached data first
        cache_file = os.path.join(self.cache_dir, f'savant_data_{datetime.now().strftime("%Y%m%d")}.json')
        
        if os.path.exists(cache_file):
            logger.info("Loading cached Savant data")
            try:
                with open(cache_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading cached data: {e}")
                # Continue with fresh data fetch
        
        # NEW (OPTIMAL 2025 RANGE):
        end_date = "2025-04-28"  # End of optimal range
        start_date = "2025-03-28"  # Start of optimal range (120K+ events!)
        
        logger.info(f"Fetching Statcast data from {start_date} to {end_date}")
        
        try:
            # Fetch all Statcast data for the period
            data = statcast(start_dt=start_date, end_dt=end_date)
            
            if data is None or len(data) == 0:
                logger.warning("No Statcast data found for the date range - may be off-season")
                return self._create_empty_savant_data()
                
            logger.info(f"Retrieved {len(data)} Statcast events")
            
            # Process the data for batters and pitchers
            batter_data = self._process_batter_data(data)
            pitcher_data = self._process_pitcher_data(data)
            
            # Combine results
            results = {
                'batters': batter_data,
                'pitchers': pitcher_data
            }
            
            # Cache the results
            try:
                with open(cache_file, 'w') as f:
                    json.dump(results, f)
                logger.info(f"Cached Savant data to {cache_file}")
            except Exception as e:
                logger.error(f"Error caching Savant data: {e}")
            
            return results
            
        except Exception as e:
            logger.error(f"Error fetching Statcast data: {e}")
            logger.info("Falling back to empty Savant data")
            return self._create_empty_savant_data()

    
    def _create_empty_savant_data(self):
        """Create empty data structure when Savant fetch fails"""
        return {
            'batters': {},
            'pitchers': {}
        }
    
    def _process_batter_data(self, data):
        """Process Statcast data for batters"""
        batters = {}
        
        # Get unique batters
        unique_batters = data['batter'].unique()
        
        for batter_id in unique_batters:
            try:
                batter_data = data[data['batter'] == batter_id]
                
                if len(batter_data) == 0:
                    continue
                    
                # Get player name
                player_name = batter_data['player_name'].iloc[0]
                
                # Get batted ball events
                batted_balls = batter_data.dropna(subset=['launch_speed', 'launch_angle'])
                
                if len(batted_balls) < 5:  # Need at least 5 batted balls
                    continue
                    
                # Calculate metrics
                avg_ev = batted_balls['launch_speed'].mean()
                max_ev = batted_balls['launch_speed'].max()
                avg_la = batted_balls['launch_angle'].mean()
                
                # Hard hit balls
                hard_hits = batted_balls[batted_balls['launch_speed'] >= 95]
                hard_hit_pct = len(hard_hits) / len(batted_balls)
                
                # Calculate hard hit distance
                hard_hit_distance = hard_hits['hit_distance_sc'].mean() if len(hard_hits) > 0 else 0
                
                # Zone analysis
                batter_stand = batter_data['stand'].mode()[0] if not batter_data['stand'].isna().all() else 'R'
                
                # Define zones based on batter handedness
                if batter_stand == 'L':
                    pull_balls = batted_balls[batted_balls['plate_x'] > 0.5]
                    oppo_balls = batted_balls[batted_balls['plate_x'] < -0.5]
                else:
                    pull_balls = batted_balls[batted_balls['plate_x'] < -0.5]
                    oppo_balls = batted_balls[batted_balls['plate_x'] > 0.5]
                    
                center_balls = batted_balls[(batted_balls['plate_x'] >= -0.5) & (batted_balls['plate_x'] <= 0.5)]
                
                # Calculate percentages
                pull_pct = len(pull_balls) / len(batted_balls) if len(batted_balls) > 0 else 0
                center_pct = len(center_balls) / len(batted_balls) if len(batted_balls) > 0 else 0
                oppo_pct = len(oppo_balls) / len(batted_balls) if len(batted_balls) > 0 else 0
                
                # Calculate SLG by field
                def calc_slg(balls):
                    if len(balls) == 0:
                        return 0
                    singles = balls[balls['events'] == 'single'].shape[0]
                    doubles = balls[balls['events'] == 'double'].shape[0]
                    triples = balls[balls['events'] == 'triple'].shape[0]
                    homers = balls[balls['events'] == 'home_run'].shape[0]
                    
                    total_bases = singles + (2 * doubles) + (3 * triples) + (4 * homers)
                    return total_bases / len(balls)
                
                pull_slg = calc_slg(pull_balls)
                center_slg = calc_slg(center_balls)
                oppo_slg = calc_slg(oppo_balls)
                
                # Define zones by height
                up_zone = batted_balls[batted_balls['plate_z'] > 2.7]
                middle_zone = batted_balls[(batted_balls['plate_z'] >= 2.0) & (batted_balls['plate_z'] <= 2.7)]
                down_zone = batted_balls[batted_balls['plate_z'] < 2.0]
                
                # Calculate metrics by zone
                up_ev = up_zone['launch_speed'].mean() if len(up_zone) > 0 else 0
                middle_ev = middle_zone['launch_speed'].mean() if len(middle_zone) > 0 else 0
                down_ev = down_zone['launch_speed'].mean() if len(down_zone) > 0 else 0
                
                # Calculate barrel rates if available
                barrel_fn = lambda x: x[x['barrel'] == 1].shape[0] / len(x) if 'barrel' in x.columns and len(x) > 0 else 0
                up_barrel = barrel_fn(up_zone)
                middle_barrel = barrel_fn(middle_zone)
                down_barrel = barrel_fn(down_zone)
                
                # Calculate inside/outside zone performance
                in_zone = batted_balls[batted_balls['plate_x'].abs() < 0.7]
                out_zone = batted_balls[batted_balls['plate_x'].abs() >= 0.7]
                
                in_barrel = barrel_fn(in_zone)
                out_barrel = barrel_fn(out_zone)
                
                # Store batter metrics
                batters[player_name] = {
                    'avg_ev': safe_float(avg_ev),
                    'max_ev': safe_float(max_ev),
                    'avg_la': safe_float(avg_la),
                    'hard_hit_pct': safe_float(hard_hit_pct),
                    'hard_hit_distance': safe_float(hard_hit_distance),
                    'spray_angle': {
                        'pull_pct': safe_float(pull_pct),
                        'center_pct': safe_float(center_pct),
                        'oppo_pct': safe_float(oppo_pct),
                        'pull_slg': safe_float(pull_slg),
                        'center_slg': safe_float(center_slg),
                        'oppo_slg': safe_float(oppo_slg)
                    },
                    'zone_contact': {
                        'up_ev': safe_float(up_ev),
                        'middle_ev': safe_float(middle_ev),
                        'down_ev': safe_float(down_ev),
                        'up_barrel_pct': safe_float(up_barrel),
                        'middle_barrel_pct': safe_float(middle_barrel),
                        'down_barrel_pct': safe_float(down_barrel),
                        'in_barrel_pct': safe_float(in_barrel),
                        'out_barrel_pct': safe_float(out_barrel)
                    },
                    'batter_id': int(batter_id),
                    'stand': batter_stand,
                    'sample_size': len(batted_balls)
                }
            except Exception as e:
                logger.error(f"Error processing batter {batter_id}: {e}")
                continue
        
        return batters
    
    def _process_pitcher_data(self, data):
        """Process Statcast data for pitchers"""
        pitchers = {}
        
        # Get unique pitchers
        unique_pitchers = data['pitcher'].unique()
        
        for pitcher_id in unique_pitchers:
            try:
                pitcher_data = data[data['pitcher'] == pitcher_id]
                
                if len(pitcher_data) < 20:  # Require at least 20 pitches
                    continue
                    
                # Get player name
                player_name = pitcher_data['player_name'].iloc[0]
                
                # Get pitch distribution
                pitch_counts = pitcher_data['pitch_type'].value_counts()
                total_pitches = len(pitcher_data)
                
                pitch_mix = {pitch: float(count/total_pitches) for pitch, count in pitch_counts.items()}
                
                # Zone analysis
                valid_zone = pitcher_data.dropna(subset=['plate_x', 'plate_z'])
                
                if len(valid_zone) == 0:
                    continue
                    
                # Define zones
                up_zone = valid_zone[valid_zone['plate_z'] > 2.7]
                middle_z = valid_zone[(valid_zone['plate_z'] >= 2.0) & (valid_zone['plate_z'] <= 2.7)]
                down_zone = valid_zone[valid_zone['plate_z'] < 2.0]
                
                inside_rhh = valid_zone[valid_zone['plate_x'] < -0.3]
                middle_x = valid_zone[(valid_zone['plate_x'] >= -0.3) & (valid_zone['plate_x'] <= 0.3)]
                outside_rhh = valid_zone[valid_zone['plate_x'] > 0.3]
                
                # Calculate zone percentages
                up_pct = len(up_zone) / len(valid_zone)
                middle_z_pct = len(middle_z) / len(valid_zone)
                down_pct = len(down_zone) / len(valid_zone)
                
                inside_pct = len(inside_rhh) / len(valid_zone)
                middle_x_pct = len(middle_x) / len(valid_zone)
                outside_pct = len(outside_rhh) / len(valid_zone)
                
                # Determine primary tendency
                zone_pcts = {
                    'up': up_pct,
                    'down': down_pct,
                    'inside': inside_pct,
                    'outside': outside_pct
                }
                
                tendency = max(zone_pcts.items(), key=lambda x: x[1])
                
                # Store pitcher metrics
                pitchers[player_name] = {
                    'pitch_mix': pitch_mix,
                    'zone_profile': {
                        'up_pct': safe_float(up_pct),
                        'middle_z_pct': safe_float(middle_z_pct),
                        'down_pct': safe_float(down_pct),
                        'inside_pct': safe_float(inside_pct),
                        'middle_x_pct': safe_float(middle_x_pct),
                        'outside_pct': safe_float(outside_pct)
                    },
                    'primary_tendency': tendency[0],
                    'tendency_strength': safe_float(tendency[1]),
                    'pitcher_id': int(pitcher_id),
                    'sample_size': len(valid_zone)
                }
            except Exception as e:
                logger.error(f"Error processing pitcher {pitcher_id}: {e}")
                continue
        
        return pitchers
    
    def _advanced_name_matching(self, search_name, candidate_names):
        """FIXED: Advanced player name matching algorithm"""
        if not search_name or not candidate_names:
            return None
            
        # Normalize names
        search_name = search_name.lower().strip()
        
        # Step 1: Try exact match
        for name in candidate_names:
            if name.lower() == search_name:
                return name
        
        # Step 2: Parse search name into components
        search_parts = search_name.split()
        if len(search_parts) < 2:
            return None  # Need at least first and last name
            
        search_first = search_parts[0]
        search_last = search_parts[-1]
        
        # Step 3: Try matching with different formats
        for name in candidate_names:
            name_lower = name.lower()
            
            # Handle "Last, First" format in candidate names
            if ',' in name:
                # "Judge, Aaron" format
                parts = name_lower.split(',')
                if len(parts) == 2:
                    cand_last = parts[0].strip()
                    cand_first = parts[1].strip()
                    
                    # Check if both first AND last name match
                    if search_first == cand_first and search_last == cand_last:
                        return name
            else:
                # "Aaron Judge" format  
                parts = name_lower.split()
                if len(parts) >= 2:
                    cand_first = parts[0]
                    cand_last = parts[-1]
                    
                    # Check if both first AND last name match
                    if search_first == cand_first and search_last == cand_last:
                        return name
        
        # Step 4: Try with first initial matching (but still require exact last name)
        for name in candidate_names:
            name_lower = name.lower()
            
            if ',' in name:
                parts = name_lower.split(',')
                if len(parts) == 2:
                    cand_last = parts[0].strip()
                    cand_first = parts[1].strip()
                    
                    # Check first initial + exact last name
                    if (len(search_first) > 0 and len(cand_first) > 0 and 
                        search_first[0] == cand_first[0] and search_last == cand_last):
                        return name
            else:
                parts = name_lower.split()
                if len(parts) >= 2:
                    cand_first = parts[0]
                    cand_last = parts[-1]
                    
                    # Check first initial + exact last name
                    if (len(search_first) > 0 and len(cand_first) > 0 and 
                        search_first[0] == cand_first[0] and search_last == cand_last):
                        return name
        
        # Step 5: Handle name variations
        name_variations = {
            'mike': 'michael', 'nick': 'nicholas', 'rob': 'robert', 
            'alex': 'alexander', 'matt': 'matthew', 'chris': 'christopher',
            'josh': 'joshua', 'jake': 'jacob', 'tony': 'anthony'
        }
        
        # Try with name variations
        search_first_var = name_variations.get(search_first, search_first)
        
        for name in candidate_names:
            name_lower = name.lower()
            
            if ',' in name:
                parts = name_lower.split(',')
                if len(parts) == 2:
                    cand_last = parts[0].strip()
                    cand_first = parts[1].strip()
                    
                    # Check with normalized first name + exact last name
                    if ((cand_first == search_first_var or 
                         name_variations.get(cand_first, '') == search_first) 
                        and cand_last == search_last):
                        return name
            else:
                parts = name_lower.split()
                if len(parts) >= 2:
                    cand_first = parts[0]
                    cand_last = parts[-1]
                    
                    # Check with normalized first name + exact last name
                    if ((cand_first == search_first_var or 
                         name_variations.get(cand_first, '') == search_first) 
                        and cand_last == search_last):
                        return name
        
        # No match found
        return None

    # FIX 3: DEBUG THE ACTUAL NAMES
    # Add this debug method to see what names are actually in the data:

    def debug_player_names_in_cache(self):
        """Debug method to see actual player names in cached data"""
        cache_file = os.path.join(self.cache_dir, f'savant_data_{datetime.now().strftime("%Y%m%d")}.json')
        
        if os.path.exists(cache_file):
            with open(cache_file, 'r') as f:
                data = json.load(f)
            
            batters = data.get('batters', {})
            print(f"\n🔍 ACTUAL NAMES IN CACHE ({len(batters)} batters):")
            
            # Look for our test players specifically
            test_players = ['judge', 'soto', 'ohtani', 'acuna']
            
            for test_player in test_players:
                matches = [name for name in batters.keys() if test_player in name.lower()]
                if matches:
                    print(f"   '{test_player}' matches: {matches}")
                else:
                    print(f"   '{test_player}' -> NO MATCHES")
            
            # Show first 20 actual names
            print(f"\n📋 FIRST 20 ACTUAL BATTER NAMES:")
            for i, name in enumerate(list(batters.keys())[:20], 1):
                print(f"   {i:2d}. '{name}'")

    def _string_similarity(self, s1, s2):
        """Calculate string similarity ratio (0-1)"""
        # Simplistic implementation - would use proper fuzzy matching in production
        if not s1 or not s2:
            return 0
            
        # Check for substring
        if s1 in s2 or s2 in s1:
            return 0.9  # High score for substring match
        
        # Count matching characters
        matches = sum(1 for a, b in zip(s1, s2) if a == b)
        max_length = max(len(s1), len(s2))
        
        return matches / max_length if max_length > 0 else 0
    
    def _match_player_data(self, player_list, savant_data):
        """Match players from our list to Savant data using improved name matching"""
        result = {}
        
        for player_name in player_list:
            # Try advanced matching algorithm
            matched_name = self._advanced_name_matching(player_name, list(savant_data.keys()))
            
            if matched_name:
                result[player_name] = savant_data[matched_name]
        
        return result

    def fetch_seasonal_data(self, season=None):
        """
        Fetch data for an entire season for better statistical significance
        
        Parameters:
        -----------
        season : int, optional
            The season year (e.g., 2023). Defaults to current year.
        """
        if not season:
            season = datetime.now().year
        
        # Check if we have cached seasonal data
        cache_file = os.path.join(self.cache_dir, f'season_{season}_data.json')
        
        if os.path.exists(cache_file):
            logger.info(f"Loading cached seasonal data for {season}")
            try:
                with open(cache_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading cached seasonal data: {e}")
        
        logger.info(f"Fetching seasonal data for {season} (this may take a while)")
        
        # Statcast data needs to be fetched in smaller chunks to avoid timeouts
        # We'll fetch one month at a time
        all_data = pd.DataFrame()
        season_start = f"{season}-03-20"  # Approximate season start
        season_end = f"{season}-10-05"    # Approximate season end
        
        current_date = datetime.strptime(season_start, "%Y-%m-%d")
        end_date = datetime.strptime(season_end, "%Y-%m-%d")
        
        # Fetch in 2-week chunks
        while current_date < end_date:
            chunk_start = current_date.strftime("%Y-%m-%d")
            chunk_end = (current_date + timedelta(days=14)).strftime("%Y-%m-%d")
            if datetime.strptime(chunk_end, "%Y-%m-%d") > end_date:
                chunk_end = season_end
            
            logger.info(f"Fetching chunk from {chunk_start} to {chunk_end}")
            try:
                chunk_data = statcast(start_dt=chunk_start, end_dt=chunk_end)
                
                if chunk_data is not None and len(chunk_data) > 0:
                    if all_data.empty:
                        all_data = chunk_data
                    else:
                        all_data = pd.concat([all_data, chunk_data])
                    
                    logger.info(f"Retrieved {len(chunk_data)} events, total now: {len(all_data)}")
                
                # Be nice to the API
                time.sleep(5)
                
            except Exception as e:
                logger.error(f"Error fetching chunk {chunk_start} to {chunk_end}: {e}")
            
            # Move to next chunk
            current_date += timedelta(days=15)
        
        if all_data.empty:
            logger.warning(f"No data retrieved for season {season}")
            return {}
        
        # Process the data
        logger.info(f"Processing {len(all_data)} total events for season {season}")
        batter_data = self._process_batter_data(all_data)
        pitcher_data = self._process_pitcher_data(all_data)
        
        # Combine results
        results = {
            'batters': batter_data,
            'pitchers': pitcher_data,
            'season': season
        }
        
        # Cache the results
        try:
            with open(cache_file, 'w') as f:
                json.dump(results, f)
            logger.info(f"Cached seasonal data to {cache_file}")
        except Exception as e:
            logger.error(f"Error caching seasonal data: {e}")
        
        return results

    def get_ballpark_analysis(self, batter_name, season=None):
        """
        Get a batter's performance in specific ballparks
        
        Parameters:
        -----------
        batter_name : str
            The name of the batter to analyze
        season : int, optional
            The season year. Defaults to current year.
        
        Returns:
        --------
        dict
            Performance metrics by ballpark
        """
        if not season:
            season = datetime.now().year
        
        # Get seasonal data
        season_data = self.fetch_seasonal_data(season)
        
        if not season_data or 'batters' not in season_data:
            logger.warning(f"No seasonal data available for {season}")
            return {}
        
        # Try to find the batter in our data
        matched_batter = self._advanced_name_matching(batter_name, list(season_data['batters'].keys()))
        
        if not matched_batter:
            logger.warning(f"No data found for batter {batter_name}")
            return {}
        
        # Look up batter ID
        try:
            batter_id = season_data['batters'][matched_batter]['batter_id']
        except:
            logger.warning(f"Could not find batter ID for {matched_batter}")
            return {}
        
        # Fetch all data for this player from the raw Statcast data
        # Since we can't store the raw data (too large), we need to fetch it again
        # We'll fetch in smaller chunks
        logger.info(f"Fetching ballpark data for {batter_name} (ID: {batter_id})")
        
        # Statcast data needs to be fetched in smaller chunks
        all_data = pd.DataFrame()
        season_start = f"{season}-03-20"
        season_end = f"{season}-10-05"
        
        current_date = datetime.strptime(season_start, "%Y-%m-%d")
        end_date = datetime.strptime(season_end, "%Y-%m-%d")
        
        # Fetch in 2-week chunks
        while current_date < end_date:
            chunk_start = current_date.strftime("%Y-%m-%d")
            chunk_end = (current_date + timedelta(days=14)).strftime("%Y-%m-%d")
            if datetime.strptime(chunk_end, "%Y-%m-%d") > end_date:
                chunk_end = season_end
            
            try:
                chunk_data = statcast(start_dt=chunk_start, end_dt=chunk_end)
                
                if chunk_data is not None and len(chunk_data) > 0:
                    # Filter for this batter
                    batter_chunk = chunk_data[chunk_data['batter'] == batter_id]
                    
                    if not batter_chunk.empty:
                        if all_data.empty:
                            all_data = batter_chunk
                        else:
                            all_data = pd.concat([all_data, batter_chunk])
                
                # Be nice to the API
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"Error fetching chunk {chunk_start} to {chunk_end}: {e}")
            
            # Move to next chunk
            current_date += timedelta(days=15)
        
        if all_data.empty:
            logger.warning(f"No data retrieved for batter {batter_name}")
            return {}
        
        # Group by ballpark and analyze
        results = {}
        
        if 'venue' in all_data.columns:
            ballparks = all_data['venue'].unique()
            
            for ballpark in ballparks:
                park_data = all_data[all_data['venue'] == ballpark]
                
                # Filter for batted ball events
                batted_balls = park_data.dropna(subset=['launch_speed', 'launch_angle'])
                
                if len(batted_balls) < 5:  # Need minimum sample size
                    continue
                
                # Calculate metrics
                avg_ev = batted_balls['launch_speed'].mean()
                avg_la = batted_balls['launch_angle'].mean()
                hard_hits = batted_balls[batted_balls['launch_speed'] >= 95]
                hard_hit_pct = len(hard_hits) / len(batted_balls)
                
                # Calculate home runs
                hrs = batted_balls[batted_balls['events'] == 'home_run']
                hr_pct = len(hrs) / len(batted_balls) if len(batted_balls) > 0 else 0
                
                # Store results
                results[ballpark] = {
                    'games': len(park_data['game_date'].unique()),
                    'batted_balls': len(batted_balls),
                    'avg_ev': safe_float(avg_ev),
                    'avg_la': safe_float(avg_la),
                    'hard_hit_pct': safe_float(hard_hit_pct),
                    'home_runs': len(hrs),
                    'hr_pct': safe_float(hr_pct),
                    'sample_size': len(batted_balls)
                }
        
        return results

# Utility functions for easy access
def get_savant_data(player_names, pitcher_names):
    """Simple interface function to get Savant data for players and pitchers"""
    savant = BaseballSavant()
    return savant.get_player_data(player_names, pitcher_names)

# Add these at the end of baseball_savant.py

def get_seasonal_data(player_names, pitcher_names, season=None):
    """Get seasonal data for players and pitchers"""
    savant = BaseballSavant()
    seasonal_data = savant.fetch_seasonal_data(season)
    
    # Match player data
    batter_data = {}
    pitcher_data = {}
    
    if 'batters' in seasonal_data:
        batter_data = savant._match_player_data(player_names, seasonal_data['batters'])
    
    if 'pitchers' in seasonal_data:
        pitcher_data = savant._match_player_data(pitcher_names, seasonal_data['pitchers'])
    
    return batter_data, pitcher_data

def get_ballpark_data(batter_name, season=None):
    """Get ballpark-specific data for a batter"""
    savant = BaseballSavant()
    return savant.get_ballpark_analysis(batter_name, season)

def _match_player_data(self, player_list, savant_data):
    """Match players from our list to Savant data using improved name matching"""
    result = {}
    
    for player_name in player_list:
        # Try advanced matching algorithm
        matched_name = self._advanced_name_matching(player_name, list(savant_data.keys()))
        
        if matched_name:
            result[player_name] = savant_data[matched_name]
    
    return result

def get_batter_recent_form(self, player_name, days=10):
    """
    Get a batter's recent performance metrics over specified days
    
    Parameters:
    -----------
    player_name : str
        The name of the batter
    days : int
        Number of days to look back
        
    Returns:
    --------
    dict
        Recent form metrics including rolling averages
    """
    end_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=days+1)).strftime("%Y-%m-%d")
    
    cache_key = f"{player_name}_{start_date}_{end_date}_form"
    cache_file = os.path.join(self.cache_dir, f'{cache_key}.json')
    
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r') as f:
                return json.load(f)
        except:
            pass
    
    try:
        # Get player ID first
        player_search = playerid_lookup(player_name.split()[-1], player_name.split()[0])
        if player_search.empty:
            return {}
            
        player_id = int(player_search.iloc[0]['key_mlbam'])
        
        # Fetch recent data
        data = statcast_batter(start_date, end_date, player_id)
        
        if data is None or len(data) == 0:
            return {}
        
        # Calculate rolling metrics
        batted_balls = data.dropna(subset=['launch_speed', 'launch_angle'])
        
        if len(batted_balls) < 3:
            return {}
        
        # Group by game date
        daily_stats = []
        for date in batted_balls['game_date'].unique():
            day_data = batted_balls[batted_balls['game_date'] == date]
            
            daily_stats.append({
                'date': date,
                'avg_ev': safe_float(day_data['launch_speed'].mean()),
                'max_ev': safe_float(day_data['launch_speed'].max()),
                'barrel_pct': safe_float(sum(day_data['barrel'] == 1) / len(day_data)) if 'barrel' in day_data.columns else 0,
                'hard_hit_pct': safe_float(sum(day_data['launch_speed'] >= 95) / len(day_data)),
                'batted_balls': len(day_data)
            })
        
        # Calculate trend
        if len(daily_stats) >= 3:
            recent_avg_ev = np.mean([d['avg_ev'] for d in daily_stats[-3:]])
            older_avg_ev = np.mean([d['avg_ev'] for d in daily_stats[:-3]]) if len(daily_stats) > 3 else recent_avg_ev
            
            trend = 'improving' if recent_avg_ev > older_avg_ev + 1 else 'declining' if recent_avg_ev < older_avg_ev - 1 else 'stable'
        else:
            trend = 'insufficient_data'
        
        result = {
            'daily_stats': daily_stats,
            'trend': trend,
            'avg_ev_last_3': safe_float(np.mean([d['avg_ev'] for d in daily_stats[-3:]])) if len(daily_stats) >= 3 else 0,
            'max_ev_period': safe_float(max([d['max_ev'] for d in daily_stats])) if daily_stats else 0,
            'games_played': len(daily_stats)
        }
        
        # Cache the result
        try:
            with open(cache_file, 'w') as f:
                json.dump(result, f)
        except:
            pass
            
        return result
        
    except Exception as e:
        logger.error(f"Error getting recent form for {player_name}: {e}")
        return {}

def fetch_seasonal_data(self, season=None):
    """
    Fetch data for an entire season for better statistical significance
    
    Parameters:
    -----------
    season : int, optional
        The season year (e.g., 2023). Defaults to current year.
    """
    if not season:
        season = datetime.now().year
    
    # Check if we have cached seasonal data
    cache_file = os.path.join(self.cache_dir, f'season_{season}_data.json')
    
    if os.path.exists(cache_file):
        logger.info(f"Loading cached seasonal data for {season}")
        try:
            with open(cache_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading cached seasonal data: {e}")


def improve_savant_name_matching():
    """
    Add this improved version of _process_batter_data to your BaseballSavant class.
    It handles name formatting differences between MLB API and Statcast.
    """
    
    # In _process_batter_data, replace the line:
    # player_name = batter_data['player_name'].iloc[0]
    
    # With this improved version:
    player_name_raw = batter_data['player_name'].iloc[0]
    
    # Statcast often uses "Last, First" format, but MLB API uses "First Last"
    # Also handle special characters and suffixes
    if ',' in player_name_raw:
        # Convert "Last, First" to "First Last"
        parts = player_name_raw.split(',')
        player_name = f"{parts[1].strip()} {parts[0].strip()}"
    else:
        player_name = player_name_raw
    
    # Remove common suffixes that might not match
    for suffix in [' Jr.', ' Jr', ' Sr.', ' Sr', ' III', ' II', ' IV']:
        player_name = player_name.replace(suffix, '')
    
    # Store both versions in the results
    batters[player_name] = { ... }  # existing code
    
    # Also store the original format
    if player_name != player_name_raw:
        batters[player_name_raw] = batters[player_name]
    
    # Store just last name as well for partial matching
    last_name = player_name.split()[-1]
    if last_name not in batters:
        batters[last_name] = batters[player_name]


