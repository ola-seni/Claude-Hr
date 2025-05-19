import logging
import statsapi
import numpy as np
import time
from handedness_data import get_batter_handedness, get_pitcher_handedness

# Configure logging (or import your logging config)
logger = logging.getLogger('MLB-HR-Predictor')

def extract_batter_handedness(player_data):
    """Extract player batting handedness - prioritize CSV data"""
    try:
        # Always try CSV first for any player with a name
        if isinstance(player_data, dict) and 'fullName' in player_data:
            player_name = player_data['fullName']
            csv_handedness = get_batter_handedness(player_name)
            
            # If we got valid handedness from CSV, use it
            if csv_handedness != 'Unknown':
                return csv_handedness
                
        # Only if CSV lookup fails, fall back to MLB API data
        if not isinstance(player_data, dict):
            return 'Unknown'
            
        # Try multiple paths to find handedness
        if 'batSide' in player_data and isinstance(player_data['batSide'], dict) and 'code' in player_data['batSide']:
            return player_data['batSide']['code']
        elif 'bat_side' in player_data and isinstance(player_data['bat_side'], dict) and 'code' in player_data['bat_side']:
            return player_data['bat_side']['code']
        
        # Try alternate structure
        bat_side = player_data.get('batSide', {})
        if isinstance(bat_side, str):
            if bat_side in ['R', 'L', 'S']:
                return bat_side
        
        # If player name contains "(L)" or "(R)" pattern common in some data
        if 'fullName' in player_data:
            name = player_data['fullName']
            if '(R)' in name:
                return 'R'
            elif '(L)' in name:
                return 'L'
            elif '(S)' in name:
                return 'S'
    except Exception as e:
        logger.error(f"Error in extract_batter_handedness: {e}")
            
    return 'Unknown'

def extract_pitcher_handedness(pitcher_data):
    """Extract pitcher throwing handedness - prioritize CSV data"""
    try:
        # Always try CSV first for any pitcher with a name
        if isinstance(pitcher_data, dict) and 'fullName' in pitcher_data:
            pitcher_name = pitcher_data['fullName']
            csv_handedness = get_pitcher_handedness(pitcher_name)
            
            # If we got valid handedness from CSV, use it
            if csv_handedness != 'Unknown':
                return csv_handedness
                
        # Only if CSV lookup fails, fall back to MLB API data
        if not isinstance(pitcher_data, dict):
            return 'Unknown'
            
        # Try multiple paths to find handedness
        if 'pitchHand' in pitcher_data and isinstance(pitcher_data['pitchHand'], dict) and 'code' in pitcher_data['pitchHand']:
            return pitcher_data['pitchHand']['code']
        elif 'pitch_hand' in pitcher_data and isinstance(pitcher_data['pitch_hand'], dict) and 'code' in pitcher_data['pitch_hand']:
            return pitcher_data['pitch_hand']['code']
        
        # Try alternate structure
        pitch_hand = pitcher_data.get('pitchHand', {})
        if isinstance(pitch_hand, str):
            if pitch_hand in ['R', 'L']:
                return pitch_hand
                
        # If pitcher name contains "(LHP)" or "(RHP)" pattern common in some data
        if 'fullName' in pitcher_data:
            name = pitcher_data['fullName']
            if 'RHP' in name or '(R)' in name:
                return 'R'
            elif 'LHP' in name or '(L)' in name:
                return 'L'
    except Exception as e:
        logger.error(f"Error in extract_pitcher_handedness: {e}")
            
    return 'Unknown'

def fetch_player_stats(player_names, generate_simulated_stats=False):
    """
    Fetch season and recent stats for all players using MLB Stats API.
    
    Parameters:
    -----------
    player_names : set
        Set of player names to fetch stats for
    generate_simulated_stats : bool, default=False
        Whether to generate simulated stats if real stats aren't available
        
    Returns:
    --------
    tuple
        (player_stats, recent_player_stats) dictionaries mapping player names to their stats
    """
    # Initialize result dictionaries
    player_stats = {}
    recent_player_stats = {}
    
    # Skip messages for players without stats
    skipped_players = []
    
    # Fetch stats for each player
    logger.info(f"Fetching stats for {len(player_names)} players using MLB Stats API")
    
    try:
        # Process each player
        for player_name in player_names:
            try:
                # Look up player ID
                player_search = None
                try:
                    player_search = statsapi.lookup_player(player_name)
                except Exception as lookup_err:
                    logger.info(f"Could not look up player {player_name}")
                    skipped_players.append(player_name)
                    continue  # Skip this player - no simulated data
                    
                if not player_search or not isinstance(player_search, list) or len(player_search) == 0:
                    logger.info(f"Player not found in MLB API: {player_name}")
                    skipped_players.append(player_name)
                    continue  # Skip this player - no simulated data
                    
                # Check if player_search is formatted correctly
                if not isinstance(player_search[0], dict):
                    logger.info(f"Invalid player search result for {player_name}")
                    skipped_players.append(player_name)
                    continue  # Skip this player - no simulated data
                
                player_id = player_search[0].get('id')
                if not player_id:
                    logger.info(f"Could not get player ID for {player_name}")
                    skipped_players.append(player_name)
                    continue  # Skip this player - no simulated data
                    
                # Get handedness with safer access
                bats = 'Unknown'
                if isinstance(player_search[0], dict):
                    bats = extract_batter_handedness(player_search[0])
                
                # Get player's 2025 season stats
                player_stats_response = None
                try:
                    player_stats_response = statsapi.player_stat_data(
                        player_id, 
                        group="hitting", 
                        type="season", 
                        sportId=1,
                        season=2025  # Use 2025 season
                    )
                except Exception as stats_err:
                    logger.info(f"Error getting stats for {player_name}")
                    skipped_players.append(player_name)
                    continue  # Skip this player - no simulated data
                
                # Handle the direct stats structure from the API
                all_stats = {}
                if isinstance(player_stats_response, dict) and 'stats' in player_stats_response:
                    raw_stats = player_stats_response['stats']
                    
                    # The stats could be directly in the response or in groups
                    if isinstance(raw_stats, dict):
                        # Stats are directly in the response
                        all_stats = raw_stats
                    elif isinstance(raw_stats, list) and len(raw_stats) > 0:
                        # Stats are in a list, take the first group
                        if isinstance(raw_stats[0], dict) and 'stats' in raw_stats[0]:
                            all_stats = raw_stats[0]['stats']
                
                # If no usable stats found, skip this player
                if not all_stats:
                    logger.info(f"No usable stats found for {player_name}")
                    skipped_players.append(player_name)
                    continue  # Skip this player - no simulated data
                
                # Extract or estimate key season stats
                games = int(all_stats.get('gamesPlayed', 0)) if all_stats.get('gamesPlayed') else 0
                
                # Skip players with insufficient games
                if games < 4:
                    logger.info(f"Insufficient games for {player_name} ({games} games)")
                    skipped_players.append(player_name)
                    continue  # Skip players with very few games
                
                hr = int(all_stats.get('homeRuns', 0)) if all_stats.get('homeRuns') else 0
                ab = int(all_stats.get('atBats', 0)) if all_stats.get('atBats') else games * 3.5
                pa = int(all_stats.get('plateAppearances', 0)) if all_stats.get('plateAppearances') else ab * 1.1
                
                # Handle batting average, could be formatted in different ways
                avg_value = all_stats.get('avg', all_stats.get('battingAverage', '.250'))
                if isinstance(avg_value, (int, float)):
                    avg = float(avg_value)
                elif isinstance(avg_value, str):
                    avg = float(avg_value.replace('.', '0.')) if avg_value.replace('.', '').isdigit() else 0.250
                else:
                    avg = 0.250  # Default
                
                # Handle OBP
                obp_value = all_stats.get('obp', all_stats.get('onBasePercentage', '.320'))
                if isinstance(obp_value, (int, float)):
                    obp = float(obp_value)
                elif isinstance(obp_value, str):
                    obp = float(obp_value.replace('.', '0.')) if obp_value.replace('.', '').isdigit() else 0.320
                else:
                    obp = 0.320  # Default
                
                # Handle SLG
                slg_value = all_stats.get('slg', all_stats.get('sluggingPercentage', '.400'))
                if isinstance(slg_value, (int, float)):
                    slg = float(slg_value)
                elif isinstance(slg_value, str):
                    slg = float(slg_value.replace('.', '0.')) if slg_value.replace('.', '').isdigit() else 0.400
                else:
                    slg = 0.400  # Default
                
                # Handle OPS
                ops_value = all_stats.get('ops', all_stats.get('onBasePlusSlugging', '.720'))
                if isinstance(ops_value, (int, float)):
                    ops = float(ops_value)
                elif isinstance(ops_value, str):
                    ops = float(ops_value.replace('.', '0.')) if ops_value.replace('.', '').isdigit() else 0.720
                else:
                    ops = 0.720  # Default
                
                # If key stats are missing or zero, skip this player
                if games == 0 or ab == 0 or pa == 0:
                    logger.info(f"Missing key stats for {player_name}")
                    skipped_players.append(player_name)
                    continue  # Skip this player - insufficient data
                
                # Calculate additional stats
                hr_per_game = hr / games if games > 0 else 0
                hr_per_pa = hr / pa if pa > 0 else 0
                
                # Generate derived stats based on available data
                # Placeholder values that would normally come from Statcast
                pull_pct = 0.40
                if slg > 0.500:  # Power hitters tend to pull more
                    pull_pct = 0.45
                
                fb_pct = 0.35  # Default
                if hr_per_pa > 0.04:  # Power hitters tend to hit more fly balls
                    fb_pct = 0.42
                
                # Estimate hard hit percentage (can correlate with SLG)
                hard_pct = min(0.50, slg)  # Rough correlation
                
                # Estimate HR/FB ratio
                hr_fb = 0.12  # League average
                if hr > 0:
                    est_fb = ab * fb_pct  # Estimated fly balls
                    hr_fb = min(0.30, hr / est_fb if est_fb > 0 else 0.12)
                
                # Calculate home/away splits - randomized for simulation
                home_factor = np.random.normal(1.0, 0.2)
                
                # Store player stats
                player_stats[player_name] = {
                    'games': games,
                    'hr': hr,
                    'ab': ab,
                    'pa': pa,
                    'hr_per_game': hr_per_game,
                    'hr_per_pa': hr_per_pa,  # This is already HR%
                    'slg': slg,  # Add SLG explicitly
                    'iso': slg - avg,  # Add ISO explicitly 
                    'pull_pct': pull_pct,
                    'fb_pct': fb_pct,
                    'hard_pct': hard_pct,
                    'hr_fb_ratio': hr_fb,
                    'barrel_pct': hard_pct * fb_pct * 0.5,  # Estimated
                    'exit_velo': 85 + (hard_pct * 10),  # Estimated
                    'launch_angle': 10 + (fb_pct * 20),  # Estimated
                    'hard_hit_pct': hard_pct,
                    'vs_fastball': np.random.normal(1.0, 0.2),  # Estimated
                    'vs_breaking': np.random.normal(1.0, 0.2),  # Estimated
                    'vs_offspeed': np.random.normal(1.0, 0.2),  # Estimated
                    'bats': bats,
                    'home_factor': home_factor,
                    'road_factor': 2.0 - home_factor,
                    'hot_cold_streak': 1.0,  # Default, will update with recent stats
                    'streak_duration': 0,
                    'batter_history': {},
                    'xwOBA': (obp * 1.8 + slg) / 3,  # Estimated xwOBA based on OBP and SLG
                    'xISO': slg - avg,  # ISO = SLG - AVG
                    # New metrics
                    'hard_hit_distance': calculate_hard_hit_distance(85 + (hard_pct * 10), 10 + (fb_pct * 20), hard_pct),
                    'pitch_specific': {
                        'fastball_hr_rate': hr_per_pa * np.random.uniform(0.8, 1.2),
                        'breaking_hr_rate': hr_per_pa * np.random.uniform(0.6, 1.0),
                        'offspeed_hr_rate': hr_per_pa * np.random.uniform(0.7, 1.1)
                    },
                    'spray_angle': {
                        'pull_pct': pull_pct,  # Already have this
                        'center_pct': np.random.uniform(0.25, 0.40),
                        'oppo_pct': 1.0 - pull_pct - np.random.uniform(0.25, 0.40),
                        'pull_slg': min(0.800, slg * 1.2),
                        'center_slg': slg,
                        'oppo_slg': slg * (0.7 if pull_pct > 0.45 else 0.9)
                    },
                    'zone_contact': {
                        'up_barrel_pct': (hard_pct * fb_pct * 0.5) * (1.2 if (10 + (fb_pct * 20)) > 15 else 0.8),
                        'down_barrel_pct': (hard_pct * fb_pct * 0.5) * (0.8 if (10 + (fb_pct * 20)) > 15 else 1.2),
                        'in_barrel_pct': (hard_pct * fb_pct * 0.5) * (1.1 if pull_pct > 0.42 else 0.9),
                        'out_barrel_pct': (hard_pct * fb_pct * 0.5) * (0.9 if pull_pct > 0.42 else 1.1)
                    },
                    'park_hr_factors': {}  # Will be populated based on ballpark factors
                }
                
                # For recent stats, use a slightly modified version of season stats
                # Real API implementation would get actual recent performance
                recent_factor = np.random.normal(1.0, 0.3)  # Random variation factor
                recent_games = min(7, games)
                recent_pa = int(recent_games * (pa / games)) if games > 0 else 25
                recent_hr = max(0, int(hr_per_game * recent_games * recent_factor))
                
                recent_hr_per_pa = recent_hr / recent_pa if recent_pa > 0 else 0
                recent_hr_per_game = recent_hr / recent_games if recent_games > 0 else 0
                
                # Calculate hot/cold streak based on recent performance vs season
                hot_cold_streak = 1.0
                streak_duration = 0
                
                if hr_per_pa > 0 and recent_hr_per_pa > 0:
                    hr_ratio = recent_hr_per_pa / hr_per_pa
                    if hr_ratio > 1.2:  # Hot streak
                        hot_cold_streak = min(1.5, 1.0 + (hr_ratio - 1.0))
                        streak_duration = recent_games
                    elif hr_ratio < 0.8:  # Cold streak
                        hot_cold_streak = max(0.6, 1.0 - (1.0 - hr_ratio))
                        streak_duration = recent_games
                
                # Store recent stats
                recent_player_stats[player_name] = {
                    'games': recent_games,
                    'hr': recent_hr,
                    'pa': recent_pa,
                    'hr_per_pa': recent_hr_per_pa,
                    'hr_per_game': recent_hr_per_game,
                    'barrel_pct': player_stats[player_name]['barrel_pct'] * recent_factor,
                    'exit_velo': player_stats[player_name]['exit_velo'] * np.random.uniform(0.95, 1.05),
                    'launch_angle': player_stats[player_name]['launch_angle'],
                    'pull_pct': player_stats[player_name]['pull_pct'],
                    'fb_pct': player_stats[player_name]['fb_pct'],
                    'hard_pct': player_stats[player_name]['hard_pct'] * recent_factor,
                    'hard_hit_pct': player_stats[player_name]['hard_hit_pct'] * recent_factor,
                    'hr_fb_ratio': player_stats[player_name]['hr_fb_ratio'] * recent_factor,
                    'vs_fastball': player_stats[player_name]['vs_fastball'],
                    'vs_breaking': player_stats[player_name]['vs_breaking'],
                    'vs_offspeed': player_stats[player_name]['vs_offspeed'],
                    'home_factor': player_stats[player_name]['home_factor'],
                    'road_factor': player_stats[player_name]['road_factor'],
                    'hot_cold_streak': hot_cold_streak,
                    'streak_duration': streak_duration,
                    'xwOBA': (obp * 1.8 + slg) / 3 * recent_factor,  # Estimated xwOBA
                    'xISO': (slg - avg) * recent_factor  # ISO = SLG - AVG
                }
                    
            except Exception as e:
                logger.error(f"Error processing stats for {player_name}: {e}")
                skipped_players.append(player_name)
                continue  # Skip this player - no simulated data
                
    except Exception as e:
        logger.error(f"Error fetching player stats: {e}")
    
    # Log the players we skipped (only if there are any)
    if skipped_players:
        logger.info(f"Skipped {len(skipped_players)} players due to missing or insufficient data")
        if len(skipped_players) <= 10:
            logger.info(f"Skipped players: {', '.join(skipped_players)}")
        else:
            logger.info(f"First 10 skipped players: {', '.join(skipped_players[:10])}...")
    
    return player_stats, recent_player_stats

def fetch_pitcher_stats(pitcher_names):
    """
    Fetch season and recent stats for all pitchers using MLB Stats API.
    
    Parameters:
    -----------
    pitcher_names : set
        Set of pitcher names to fetch stats for
        
    Returns:
    --------
    tuple
        (pitcher_stats, recent_pitcher_stats) dictionaries mapping pitcher names to their stats
    """
    # Initialize result dictionaries
    pitcher_stats = {}
    recent_pitcher_stats = {}
    
    # Fetch stats for each pitcher
    logger.info(f"Fetching stats for {len(pitcher_names)} pitchers using MLB Stats API")
    
    try:
        # Process each pitcher
        for pitcher_name in pitcher_names:
            try:
                # Look up pitcher ID
                pitcher_search = None
                try:
                    pitcher_search = statsapi.lookup_player(pitcher_name)
                except Exception as e:
                    logger.warning(f"Error looking up pitcher {pitcher_name}: {e}")
                    set_default_pitcher_stats(pitcher_name, pitcher_stats, recent_pitcher_stats)
                    continue
                    
                if not pitcher_search:
                    logger.warning(f"Pitcher not found in MLB API: {pitcher_name}")
                    set_default_pitcher_stats(pitcher_name, pitcher_stats, recent_pitcher_stats)
                    continue
                
                # Check if pitcher_search is a valid list with dictionary items
                if not isinstance(pitcher_search, list) or len(pitcher_search) == 0:
                    logger.warning(f"Invalid pitcher search result format for {pitcher_name}: {type(pitcher_search)}")
                    set_default_pitcher_stats(pitcher_name, pitcher_stats, recent_pitcher_stats)
                    continue
                
                # Check if the first item is a dictionary
                if not isinstance(pitcher_search[0], dict):
                    logger.warning(f"Invalid pitcher search result for {pitcher_name}: {type(pitcher_search[0])}")
                    set_default_pitcher_stats(pitcher_name, pitcher_stats, recent_pitcher_stats)
                    continue
                
                player_id = pitcher_search[0].get('id')
                if not player_id:
                    logger.warning(f"Could not get pitcher ID for {pitcher_name}")
                    set_default_pitcher_stats(pitcher_name, pitcher_stats, recent_pitcher_stats)
                    continue
                
                # Get handedness with safe access
                throws = 'Unknown'
                if isinstance(pitcher_search[0], dict):
                    throws = extract_pitcher_handedness(pitcher_search[0])
                
                # Try to get real stats from MLB API
                pitcher_stats_response = None
                try:
                    pitcher_stats_response = statsapi.player_stat_data(
                        player_id, 
                        group="pitching", 
                        type="season", 
                        sportId=1,
                        season=2025  # Use 2025 season
                    )
                except Exception as e:
                    logger.warning(f"Error getting pitcher stats for {pitcher_name}: {e}")
                    # Continue with simulated stats
                
                # Handle the direct stats structure from the API
                all_stats = {}
                if isinstance(pitcher_stats_response, dict) and 'stats' in pitcher_stats_response:
                    raw_stats = pitcher_stats_response['stats']
                    
                    # The stats could be directly in the response or in groups
                    if isinstance(raw_stats, dict):
                        # Stats are directly in the response
                        all_stats = raw_stats
                    elif isinstance(raw_stats, list) and len(raw_stats) > 0:
                        # Stats are in a list, take the first group
                        if isinstance(raw_stats[0], dict) and 'stats' in raw_stats[0]:
                            all_stats = raw_stats[0]['stats']
                
                # If no real stats, we'll generate simulated stats
                if not all_stats:
                    # Generate simulated stats for the 2025 season
                    games = np.random.randint(5, 15)  # Games played so far
                    games_started = np.random.randint(0, games)  # Games started
                    relief_apps = games - games_started
                    innings_pitched = np.random.uniform(games_started * 5, games_started * 6 + relief_apps * 1)  # Innings pitched
                    hr_allowed = np.random.randint(1, 10)  # Home runs allowed
                else:
                    # Extract real stats
                    games = int(all_stats.get('gamesPlayed', 0)) if all_stats.get('gamesPlayed') else np.random.randint(5, 15)
                    games_started = int(all_stats.get('gamesStarted', 0)) if all_stats.get('gamesStarted') else np.random.randint(0, games)
                    relief_apps = games - games_started
                    
                    # Handle innings pitched
                    ip_value = all_stats.get('inningsPitched', all_stats.get('ip', '0'))
                    if isinstance(ip_value, (int, float)):
                        innings_pitched = float(ip_value)
                    elif isinstance(ip_value, str) and ip_value:
                        try:
                            innings_pitched = float(ip_value)
                        except ValueError:
                            innings_pitched = games_started * 5.5  # Estimate
                    else:
                        innings_pitched = games_started * 5.5  # Estimate
                    
                    # Handle HR allowed
                    hr_allowed = int(all_stats.get('homeRuns', 0)) if all_stats.get('homeRuns') else np.random.randint(1, 10)
                
                # Calculate HR/9
                hr_per_9 = (hr_allowed * 9) / innings_pitched if innings_pitched > 0 else 0
                
                # Generate or extract ERA
                if all_stats and all_stats.get('era'):
                    era_value = all_stats.get('era')
                    if isinstance(era_value, (int, float)):
                        era = float(era_value)
                    elif isinstance(era_value, str) and era_value:
                        try:
                            era = float(era_value)
                        except ValueError:
                            era = np.random.uniform(3.00, 5.00)
                    else:
                        era = np.random.uniform(3.00, 5.00)
                else:
                    era = np.random.uniform(3.00, 5.00)
                
                # Generate batted ball profile based on pitcher type/quality
                if era < 3.50:  # Top-tier pitcher
                    pitcher_type = 'GB'  # Ground ball pitcher (better)
                elif era > 5.00:  # Struggling pitcher
                    pitcher_type = 'FB'  # Fly ball pitcher (riskier)
                else:  # Average pitcher
                    pitcher_type = np.random.choice(['GB', 'FB', 'Neutral'], p=[0.33, 0.33, 0.34])
                
                if pitcher_type == 'GB':
                    gb_pct = np.random.uniform(0.45, 0.55)
                    fb_pct = np.random.uniform(0.25, 0.35)
                elif pitcher_type == 'FB':
                    gb_pct = np.random.uniform(0.30, 0.40)
                    fb_pct = np.random.uniform(0.40, 0.50)
                else:  # Neutral
                    gb_pct = np.random.uniform(0.40, 0.45)
                    fb_pct = np.random.uniform(0.35, 0.40)
                    
                gb_fb_ratio = gb_pct / fb_pct if fb_pct > 0 else 1.0
                
                # Quality of contact allowed
                hard_pct = np.random.uniform(0.30, 0.40)
                if era < 3.50:
                    hard_pct -= 0.05  # Better pitchers allow less hard contact
                elif era > 5.00:
                    hard_pct += 0.05  # Worse pitchers allow more hard contact
                
                # Pitch mix based on handedness
                if throws == 'L':  # Lefties use more off-speed
                    fastball_pct = np.random.uniform(0.45, 0.60)
                    breaking_pct = np.random.uniform(0.20, 0.35)
                else:  # Righties use more breaking
                    fastball_pct = np.random.uniform(0.50, 0.65)
                    breaking_pct = np.random.uniform(0.25, 0.40)
                    
                offspeed_pct = 1.0 - fastball_pct - breaking_pct
                
                # Recent workload
                recent_starts = min(2, games_started)  # Up to 2 starts in last 7 days
                recent_relief = min(3, relief_apps)  # Up to 3 relief appearances
                recent_workload = (recent_starts * 95) + (recent_relief * 20)  # Average pitches
                
                # Store pitcher stats
                pitcher_stats[pitcher_name] = {
                    'games': games,
                    'ip': innings_pitched,
                    'hr': hr_allowed,
                    'hr_per_9': hr_per_9,
                    'fb_pct': fb_pct,
                    'gb_pct': gb_pct,
                    'hard_pct': hard_pct,
                    'gb_fb_ratio': gb_fb_ratio,
                    'barrel_pct': hard_pct * fb_pct * 0.5,  # Estimated
                    'exit_velo': 85 + (hard_pct * 10),  # Estimated
                    'throws': throws,
                    'fastball_pct': fastball_pct,
                    'breaking_pct': breaking_pct,
                    'offspeed_pct': offspeed_pct,
                    'recent_workload': recent_workload
                }
                
                # Generate recent stats (last 7 days)
                # Apply random variation to simulate recent performance
                performance_factor = np.random.normal(1.0, 0.3)
                
                # Recent games and innings
                recent_games = recent_starts + recent_relief
                recent_ip = (recent_starts * 5.5) + (recent_relief * 1.2)  # Average IP
                
                # Recent HR allowed with variation
                recent_hr_factor = performance_factor  # Higher = worse for pitchers
                recent_hr = max(0, int((hr_per_9 * recent_ip / 9) * recent_hr_factor))
                
                # Recent HR rate
                recent_hr_per_9 = (recent_hr * 9) / recent_ip if recent_ip > 0 else 0
                
                # Store recent stats
                recent_pitcher_stats[pitcher_name] = {
                    'games': recent_games,
                    'ip': recent_ip,
                    'hr': recent_hr,
                    'hr_per_9': recent_hr_per_9,
                    'barrel_pct': pitcher_stats[pitcher_name]['barrel_pct'] * performance_factor,
                    'exit_velo': pitcher_stats[pitcher_name]['exit_velo'] * np.random.uniform(0.95, 1.05),
                    'fb_pct': fb_pct * np.random.uniform(0.9, 1.1),
                    'gb_pct': gb_pct * np.random.uniform(0.9, 1.1),
                    'hard_pct': hard_pct * np.random.uniform(0.9, 1.1),
                    'gb_fb_ratio': gb_fb_ratio * np.random.uniform(0.9, 1.1),
                    'recent_workload': recent_workload
                }
                    
            except Exception as e:
                logger.error(f"Error processing stats for pitcher {pitcher_name}: {e}")
                set_default_pitcher_stats(pitcher_name, pitcher_stats, recent_pitcher_stats)
                
    except Exception as e:
        logger.error(f"Error fetching pitcher stats: {e}")
    
    return pitcher_stats, recent_pitcher_stats

def generate_simulated_player_stats(player_name, player_stats_dict, recent_player_stats_dict):
    """
    Generate realistic simulated stats for a player when actual stats aren't available.
    
    Parameters:
    -----------
    player_name : str
        Name of the player to generate stats for
    player_stats_dict : dict
        Dictionary to store the player's season stats
    recent_player_stats_dict : dict
        Dictionary to store the player's recent stats
    """
    logger.info(f"Generating simulated stats for {player_name}")
    
    # Randomize player profile
    # Player types: Power Hitter, Contact Hitter, Balanced Hitter
    player_type = np.random.choice(['Power', 'Contact', 'Balanced'], p=[0.3, 0.3, 0.4])
    
    # Randomize games played (25-50 for 2025 season so far)
    games = np.random.randint(25, 50)
    
    # Plate appearances based on games (3.5-4.5 PA per game)
    pa_per_game = np.random.uniform(3.5, 4.5)
    pa = int(games * pa_per_game)
    
    # At bats (slightly less than PA due to walks)
    ab = int(pa * np.random.uniform(0.85, 0.92))
    
    # Generate batting average based on player type
    if player_type == 'Power':
        avg = np.random.uniform(0.230, 0.280)
    elif player_type == 'Contact':
        avg = np.random.uniform(0.270, 0.320)
    else:  # Balanced
        avg = np.random.uniform(0.250, 0.300)
        
    # Hits
    hits = int(ab * avg)
    
    # Generate power metrics based on player type
    if player_type == 'Power':
        hr_percentage = np.random.uniform(0.04, 0.07)  # 4-7% of ABs
        iso = np.random.uniform(0.200, 0.300)
    elif player_type == 'Contact':
        hr_percentage = np.random.uniform(0.01, 0.03)  # 1-3% of ABs
        iso = np.random.uniform(0.100, 0.170)
    else:  # Balanced
        hr_percentage = np.random.uniform(0.025, 0.045)  # 2.5-4.5% of ABs
        iso = np.random.uniform(0.150, 0.220)
    
    # HR, 2B, 3B
    hr = max(0, int(ab * hr_percentage))
    doubles_percentage = np.random.uniform(0.04, 0.07)  # 4-7% of ABs are doubles
    doubles = max(0, int(ab * doubles_percentage))
    triples_percentage = np.random.uniform(0.003, 0.01)  # 0.3-1% of ABs are triples
    triples = max(0, int(ab * triples_percentage))
    
    # Singles (remaining hits)
    singles = max(0, hits - hr - doubles - triples)
    
    # Calculate SLG
    total_bases = singles + (doubles * 2) + (triples * 3) + (hr * 4)
    slg = total_bases / ab if ab > 0 else 0
    
    # Calculate OBP (slightly higher than AVG)
    obp = avg + np.random.uniform(0.050, 0.100)
    
    # Calculate OPS
    ops = obp + slg
    
    # HR per game and per PA
    hr_per_game = hr / games if games > 0 else 0
    hr_per_pa = hr / pa if pa > 0 else 0
    
    # Batted ball metrics
    if player_type == 'Power':
        pull_pct = np.random.uniform(0.42, 0.50)
        fb_pct = np.random.uniform(0.38, 0.48)
        hard_pct = np.random.uniform(0.38, 0.48)
    elif player_type == 'Contact':
        pull_pct = np.random.uniform(0.30, 0.40)
        fb_pct = np.random.uniform(0.28, 0.38)
        hard_pct = np.random.uniform(0.28, 0.38)
    else:  # Balanced
        pull_pct = np.random.uniform(0.35, 0.45)
        fb_pct = np.random.uniform(0.33, 0.43)
        hard_pct = np.random.uniform(0.33, 0.43)
    
    # HR/FB ratio
    hr_fb = min(0.30, hr / (ab * fb_pct) if (ab * fb_pct) > 0 else 0.10)
    
    # Quality of contact metrics
    barrel_pct = hard_pct * fb_pct * 0.5
    exit_velo = 85 + (hard_pct * 15)
    launch_angle = 10 + (fb_pct * 25)
    
    # Randomize batter handedness
    bats = np.random.choice(['R', 'L', 'S'], p=[0.65, 0.30, 0.05])
    
    # Home/away splits
    home_factor = np.random.normal(1.0, 0.2)
    
    # Pitch type performance
    vs_fastball = np.random.normal(1.0, 0.2)
    vs_breaking = np.random.normal(1.0, 0.2)
    vs_offspeed = np.random.normal(1.0, 0.2)
    
    # Store season stats
    player_stats_dict[player_name] = {
        'games': games,
        'hr': hr,
        'ab': ab,
        'pa': pa,
        'hr_per_game': hr_per_game,
        'hr_per_pa': hr_per_pa,
        'pull_pct': pull_pct,
        'fb_pct': fb_pct,
        'hard_pct': hard_pct,
        'hr_fb_ratio': hr_fb,
        'barrel_pct': barrel_pct,
        'exit_velo': exit_velo,
        'launch_angle': launch_angle,
        'hard_hit_pct': hard_pct,
        'vs_fastball': vs_fastball,
        'vs_breaking': vs_breaking,
        'vs_offspeed': vs_offspeed,
        'bats': bats,
        'home_factor': home_factor,
        'road_factor': 2.0 - home_factor,
        'hot_cold_streak': 1.0,
        'streak_duration': 0,
        'batter_history': {},
        'xwOBA': (obp * 1.8 + slg) / 3,
        'xISO': iso,
        'is_simulated': True 
    }
    
    # Generate recent stats with some variance from season stats
    recent_factor = np.random.normal(1.0, 0.3)  # Random hot/cold factor
    recent_games = min(7, games)
    recent_pa = int(recent_games * pa_per_game)
    recent_hr = max(0, int(recent_games * hr_per_game * recent_factor))
    recent_hr_per_pa = recent_hr / recent_pa if recent_pa > 0 else 0
    
    # Determine hot/cold streak based on recent performance
    streak_factor = 1.0
    streak_duration = 0
    
    if hr_per_pa > 0 and recent_hr_per_pa > 0:
        hr_ratio = recent_hr_per_pa / hr_per_pa
        if hr_ratio > 1.2:  # Hot streak
            streak_factor = min(1.5, 1.0 + (hr_ratio - 1.0))
            streak_duration = recent_games
        elif hr_ratio < 0.8:  # Cold streak
            streak_factor = max(0.6, 1.0 - (1.0 - hr_ratio))
            streak_duration = recent_games
    
    # Store recent stats with variance
    recent_player_stats_dict[player_name] = {
        'games': recent_games,
        'hr': recent_hr,
        'pa': recent_pa,
        'hr_per_pa': recent_hr_per_pa,
        'hr_per_game': recent_hr / recent_games if recent_games > 0 else 0,
        'barrel_pct': barrel_pct * recent_factor,
        'exit_velo': exit_velo * np.random.uniform(0.95, 1.05),
        'launch_angle': launch_angle * np.random.uniform(0.95, 1.05),
        'pull_pct': pull_pct * np.random.uniform(0.95, 1.05),
        'fb_pct': fb_pct * np.random.uniform(0.95, 1.05),
        'hard_pct': hard_pct * recent_factor,
        'hard_hit_pct': hard_pct * recent_factor,
        'hr_fb_ratio': hr_fb * recent_factor,
        'vs_fastball': vs_fastball,
        'vs_breaking': vs_breaking,
        'vs_offspeed': vs_offspeed,
        'home_factor': home_factor,
        'road_factor': 2.0 - home_factor,
        'hot_cold_streak': streak_factor,
        'streak_duration': streak_duration,
        'xwOBA': (obp * 1.8 + slg) / 3 * recent_factor,
        'xISO': iso * recent_factor,
        'is_simulated': True 
    }

def set_default_pitcher_stats(pitcher_name, pitcher_stats_dict, recent_pitcher_stats_dict):
    """
    Set default stats for a pitcher when data cannot be fetched.
    
    Parameters:
    -----------
    pitcher_name : str
        Name of the pitcher to set default stats for
    pitcher_stats_dict : dict
        Dictionary to store the pitcher's season stats
    recent_pitcher_stats_dict : dict
        Dictionary to store the pitcher's recent stats
    """
    # Set default values for season stats
    pitcher_stats_dict[pitcher_name] = {
        'games': 0, 'ip': 0, 'hr': 0, 'hr_per_9': 0, 
        'fb_pct': 0.35, 'gb_pct': 0.45, 'hard_pct': 0.30, 'barrel_pct': 0.05, 
        'exit_velo': 88, 'throws': 'Unknown', 'gb_fb_ratio': 1.0,
        'fastball_pct': 0.60, 'breaking_pct': 0.25, 'offspeed_pct': 0.15,
        'recent_workload': 0
    }
    
    # Set default values for recent stats
    recent_pitcher_stats_dict[pitcher_name] = {
        'games': 0, 'ip': 0, 'hr': 0, 'hr_per_9': 0,
        'barrel_pct': 0.05, 'exit_velo': 88, 'fb_pct': 0.35, 
        'gb_pct': 0.45, 'hard_pct': 0.30, 'gb_fb_ratio': 1.0,
        'recent_workload': 0
    }

def get_player_names_from_lineups(lineups):
    """
    Extract all player names from lineups dictionary.
    
    Parameters:
    -----------
    lineups : dict
        Dictionary mapping game_id to dict with 'home' and 'away' lists of player names
        
    Returns:
    --------
    set
        Set of all player names
    """
    player_names = set()
    for game_id, lineup in lineups.items():
        player_names.update(lineup.get('home', []))
        player_names.update(lineup.get('away', []))
            
    # Remove any empty strings or None values
    player_names = {name for name in player_names if name and isinstance(name, str)}
    return player_names

def get_pitcher_names_from_probable_pitchers(probable_pitchers):
    """
    Extract all pitcher names from probable_pitchers dictionary.
    
    Parameters:
    -----------
    probable_pitchers : dict
        Dictionary mapping game_id to dict with 'home' and 'away' pitcher names
        
    Returns:
    --------
    set
        Set of all pitcher names
    """
    pitcher_names = set()
    for game_id, pitchers in probable_pitchers.items():
        if isinstance(pitchers, dict):
            pitcher_names.add(pitchers.get('home', ''))
            pitcher_names.add(pitchers.get('away', ''))
        
    # Remove any empty strings, None values, or "Unknown" or "TBD"
    pitcher_names = {name for name in pitcher_names if name and isinstance(name, str) and name not in ["Unknown", "TBD"]}
    return pitcher_names

def show_handedness_data_stats():
    """Log stats about available handedness data"""
    bats_values = {}
    throws_values = {}
    
    # Count handedness values in player stats
    for player, stats in player_stats.items():
        bats = stats.get('bats', 'Unknown')
        if bats in bats_values:
            bats_values[bats] += 1
        else:
            bats_values[bats] = 1
    
    # Count handedness values in pitcher stats        
    for pitcher, stats in pitcher_stats.items():
        throws = stats.get('throws', 'Unknown')
        if throws in throws_values:
            throws_values[throws] += 1
        else:
            throws_values[throws] = 1
    
    logger.info(f"Batter handedness distribution: {bats_values}")
    logger.info(f"Pitcher handedness distribution: {throws_values}")

def calculate_hard_hit_distance(exit_velo, launch_angle, hard_pct):
    """Calculate estimated average distance for hard hit balls (95+ mph exit velo)"""
    # Base distance for 95 mph exit velo at optimal launch angle
    base_distance = 350
    
    # Adjust for higher exit velocities
    velo_factor = (exit_velo - 95) * 2 if exit_velo > 95 else 0
    
    # Adjust for launch angle (optimal ~25-30 degrees)
    if 25 <= launch_angle <= 30:
        angle_factor = 20  # Optimal
    elif 20 <= launch_angle < 25 or 30 < launch_angle <= 35:
        angle_factor = 10  # Very good
    elif 15 <= launch_angle < 20 or 35 < launch_angle <= 40:
        angle_factor = 0   # Good
    elif 10 <= launch_angle < 15 or 40 < launch_angle <= 45:
        angle_factor = -10  # Suboptimal
    else:
        angle_factor = -20  # Poor for distance
    
    # Hard hit percentage factor - players who hit the ball hard more often
    # tend to have better distance on their hard hit balls
    hard_factor = (hard_pct - 0.3) * 50 if hard_pct > 0.3 else 0
    
    # Calculate distance with adjustments
    distance = base_distance + velo_factor + angle_factor + hard_factor
    
    # Cap within reasonable limits
    return max(320, min(450, distance))
