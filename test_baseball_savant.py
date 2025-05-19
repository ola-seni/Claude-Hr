# test_baseball_savant_final.py
import pandas as pd
import numpy as np
import time
from pybaseball import statcast, playerid_lookup
import matplotlib.pyplot as plt
import os
from datetime import datetime, timedelta

def test_player_lookup(first_name, last_name):
    """Test looking up a player ID from first and last name"""
    print(f"\n=== Testing player lookup for {first_name} {last_name} ===")
    
    try:
        # Look up the player ID
        lookup_result = playerid_lookup(last_name, first_name)
        
        if lookup_result.empty:
            print(f"ERROR: No player found with name {first_name} {last_name}")
            return None
            
        # Print the result
        print(f"Found {len(lookup_result)} matches:")
        print(lookup_result[['name_first', 'name_last', 'key_mlbam']])
        
        # Return the most recent player's ID
        mlbam_id = lookup_result.iloc[0]['key_mlbam']
        print(f"Using ID: {mlbam_id}")
        return mlbam_id
        
    except Exception as e:
        print(f"ERROR during player lookup: {str(e)}")
        return None

def get_statcast_data(start_date, end_date):
    """Get statcast data for all players within a date range"""
    print(f"Fetching Statcast data from {start_date} to {end_date}")
    
    try:
        # Use the general statcast function
        data = statcast(start_dt=start_date, end_dt=end_date)
        
        print(f"Retrieved {len(data)} Statcast events total")
        return data
    except Exception as e:
        print(f"ERROR fetching Statcast data: {str(e)}")
        return pd.DataFrame()  # Return empty dataframe

def analyze_player_data(full_data, player_name, is_pitcher=False):
    """Extract and analyze data for a specific player"""
    if full_data.empty:
        print(f"No data available to analyze for {player_name}")
        return
        
    print(f"\n=== Analyzing data for {player_name} ===")
    
    # Filter by player name (try matching parts of the name)
    player_data = full_data[full_data['player_name'].str.contains(player_name, case=False, na=False)]
    
    if len(player_data) == 0:
        print(f"No data found for {player_name} in the dataset")
        return
        
    print(f"Found {len(player_data)} events for {player_name}")
    
    if is_pitcher:
        analyze_pitcher_stats(player_data, player_name)
    else:
        analyze_batter_stats(player_data, player_name)
    
    return player_data

def analyze_batter_stats(data, player_name):
    """Analyze batting performance from Statcast data"""
    print(f"\n=== Batting Analysis for {player_name} ===")
    
    # Filter to include only batted ball events
    batted_balls = data.dropna(subset=['launch_speed', 'launch_angle'])
    
    if len(batted_balls) == 0:
        print("No batted ball data available")
        return
        
    # Basic stats
    avg_ev = batted_balls['launch_speed'].mean()
    max_ev = batted_balls['launch_speed'].max() 
    avg_la = batted_balls['launch_angle'].mean()
    
    print(f"Batted Balls: {len(batted_balls)}")
    print(f"Avg Exit Velocity: {avg_ev:.1f} mph")
    print(f"Max Exit Velocity: {max_ev:.1f} mph") 
    print(f"Avg Launch Angle: {avg_la:.1f}°")
    
    # Hard hit balls (95+ mph)
    hard_hits = batted_balls[batted_balls['launch_speed'] >= 95]
    hard_hit_pct = len(hard_hits) / len(batted_balls) if len(batted_balls) > 0 else 0
    print(f"Hard Hit %: {hard_hit_pct*100:.1f}%")
    
    # Barrels (if column exists)
    if 'barrel' in batted_balls.columns:
        barrels = batted_balls[batted_balls['barrel'] == 1]
        barrel_pct = len(barrels) / len(batted_balls)
        print(f"Barrel %: {barrel_pct*100:.1f}%")
    
    # Home runs
    if 'events' in batted_balls.columns:
        hrs = batted_balls[batted_balls['events'] == 'home_run']
        print(f"Home Runs: {len(hrs)}")
        
        if len(hrs) > 0:
            hr_ev = hrs['launch_speed'].mean()
            hr_la = hrs['launch_angle'].mean()
            print(f"HR Avg Exit Velo: {hr_ev:.1f} mph")
            print(f"HR Avg Launch Angle: {hr_la:.1f}°")
    
    # Zone analysis
    if 'plate_x' in batted_balls.columns and 'plate_z' in batted_balls.columns:
        print("\nZone Performance:")
        
        # Get batter stand (L/R)
        if 'stand' in batted_balls.columns and not batted_balls['stand'].isna().all():
            # Most common stand value
            stand = batted_balls['stand'].mode()[0]
            print(f"Batter stands: {stand}")
            
            # Define zones
            if stand == 'L':
                # For LHB, positive X is pull side
                pull_side = batted_balls[batted_balls['plate_x'] > 0.5]
                oppo_side = batted_balls[batted_balls['plate_x'] < -0.5]
            else:
                # For RHB, negative X is pull side
                pull_side = batted_balls[batted_balls['plate_x'] < -0.5] 
                oppo_side = batted_balls[batted_balls['plate_x'] > 0.5]
                
            middle = batted_balls[(batted_balls['plate_x'] >= -0.5) & (batted_balls['plate_x'] <= 0.5)]
            
            # Calculate percentages
            pull_pct = len(pull_side) / len(batted_balls)
            oppo_pct = len(oppo_side) / len(batted_balls)
            middle_pct = len(middle) / len(batted_balls)
            
            print(f"Pull %: {pull_pct*100:.1f}%")
            print(f"Middle %: {middle_pct*100:.1f}%") 
            print(f"Oppo %: {oppo_pct*100:.1f}%")
            
        # Zone performance by height
        up_zone = batted_balls[batted_balls['plate_z'] > 2.7]
        middle_z = batted_balls[(batted_balls['plate_z'] >= 2.0) & (batted_balls['plate_z'] <= 2.7)]
        down_zone = batted_balls[batted_balls['plate_z'] < 2.0]
        
        print("\nPerformance by Zone Height:")
        print(f"Up Zone: {len(up_zone)} balls - {up_zone['launch_speed'].mean():.1f} mph EV") 
        print(f"Middle Zone: {len(middle_z)} balls - {middle_z['launch_speed'].mean():.1f} mph EV")
        print(f"Down Zone: {len(down_zone)} balls - {down_zone['launch_speed'].mean():.1f} mph EV")

def analyze_pitcher_stats(data, player_name):
    """Analyze pitching performance from Statcast data"""
    print(f"\n=== Pitching Analysis for {player_name} ===")
    
    # Pitch type breakdown
    if 'pitch_type' in data.columns:
        pitch_counts = data['pitch_type'].value_counts()
        total_pitches = len(data)
        
        print("Pitch Type Distribution:")
        for pitch, count in pitch_counts.items():
            pct = count / total_pitches * 100
            print(f"  {pitch}: {count} ({pct:.1f}%)")
    
    # Zone analysis
    valid_zone = data.dropna(subset=['plate_x', 'plate_z'])
    
    if len(valid_zone) > 0:
        print("\nPitch Location Analysis:")
        
        # Define zones
        up_zone = valid_zone[valid_zone['plate_z'] > 2.7].shape[0]
        middle_z = valid_zone[(valid_zone['plate_z'] >= 2.0) & (valid_zone['plate_z'] <= 2.7)].shape[0]
        down_zone = valid_zone[valid_zone['plate_z'] < 2.0].shape[0]
        
        inside_rhh = valid_zone[valid_zone['plate_x'] < -0.3].shape[0]
        middle_x = valid_zone[(valid_zone['plate_x'] >= -0.3) & (valid_zone['plate_x'] <= 0.3)].shape[0]
        outside_rhh = valid_zone[valid_zone['plate_x'] > 0.3].shape[0]
        
        total = len(valid_zone)
        
        # Print percentages
        print(f"Up Zone: {up_zone/total*100:.1f}%")
        print(f"Middle Height: {middle_z/total*100:.1f}%")
        print(f"Down Zone: {down_zone/total*100:.1f}%")
        print(f"\nInside to RHH: {inside_rhh/total*100:.1f}%")
        print(f"Middle Width: {middle_x/total*100:.1f}%")
        print(f"Outside to RHH: {outside_rhh/total*100:.1f}%")
        
        # Determine tendency
        zones = {
            'up': up_zone/total,
            'down': down_zone/total,
            'inside': inside_rhh/total,
            'outside': outside_rhh/total
        }
        
        tendency = max(zones, key=zones.get)
        print(f"\nPitcher tendency: {tendency.upper()} ({zones[tendency]*100:.1f}%)")
        
        # Create visualization
        try:
            plt.figure(figsize=(8, 8))
            plt.scatter(valid_zone['plate_x'], valid_zone['plate_z'], alpha=0.3)
            plt.grid(True)
            plt.xlim(-2, 2)
            plt.ylim(0, 5)
            plt.title(f"Pitch Location Map for {player_name}")
            plt.xlabel("Horizontal Location (ft from center)")
            plt.ylabel("Vertical Location (ft from ground)")
            
            # Draw strike zone
            strike_zone_x = [-0.85, 0.85, 0.85, -0.85, -0.85]
            strike_zone_y = [1.5, 1.5, 3.5, 3.5, 1.5]
            plt.plot(strike_zone_x, strike_zone_y, 'r-')
            
            # Save the plot
            os.makedirs('savant_test', exist_ok=True)
            safe_name = player_name.replace(' ', '_').replace("'", "")
            plt.savefig(f"savant_test/{safe_name}_pitch_map.png")
            print(f"\nPitch location map saved to savant_test/{safe_name}_pitch_map.png")
            
        except Exception as plot_error:
            print(f"Could not create visualization: {plot_error}")

def main():
    """Main test function"""
    print("=== BASEBALL SAVANT INTEGRATION TEST (FINAL) ===\n")
    
    # Define test players
    test_players = [
        {'name': 'Aaron Judge', 'first': 'Aaron', 'last': 'Judge', 'is_pitcher': False},
        {'name': 'Juan Soto', 'first': 'Juan', 'last': 'Soto', 'is_pitcher': False},
        {'name': 'Gerrit Cole', 'first': 'Gerrit', 'last': 'Cole', 'is_pitcher': True},
        {'name': 'Blake Snell', 'first': 'Blake', 'last': 'Snell', 'is_pitcher': True}
    ]
    
    # Get a single Statcast dataset for a reasonable date range (7 days from past season)
    # We'll use this same dataset for all players to avoid multiple API calls
    start_date = "2023-06-01"
    end_date = "2023-06-07"
    
    all_data = get_statcast_data(start_date, end_date)
    
    if all_data.empty:
        print("Failed to retrieve Statcast data. Exiting.")
        return
        
    # Process each player
    for player in test_players:
        print(f"\n\n>>> ANALYZING {player['name']} <<<")
        # First make sure we can look up the player
        player_id = test_player_lookup(player['first'], player['last'])
        
        # Then analyze their data from the dataset
        player_data = analyze_player_data(all_data, player['last'], player['is_pitcher'])
        
        # Add delay to avoid rate limiting
        time.sleep(1)
    
    print("\n=== TEST COMPLETE ===")

if __name__ == "__main__":
    main()
