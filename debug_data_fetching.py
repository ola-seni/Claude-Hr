# debug_data_fetching.py
# Test why lineup and pitcher fetching is failing

import pandas as pd
import datetime
import logging
import statsapi
from lineup_fetcher import fetch_lineups_and_pitchers
from rotowire_lineups import fetch_rotowire_expected_lineups, convert_rotowire_data_to_mlb_format

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('DataFetchDebug')

def test_mlb_api_direct():
    """Test MLB Stats API directly"""
    print("=== TESTING MLB STATS API DIRECTLY ===\n")
    
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    
    try:
        # Test 1: Get today's schedule
        print("1. Testing schedule fetch...")
        schedule = statsapi.schedule(date=today)
        print(f"✓ Found {len(schedule)} games in schedule")
        
        for i, game in enumerate(schedule[:3]):  # Show first 3 games
            print(f"  Game {i+1}: {game.get('away_name', 'Unknown')} @ {game.get('home_name', 'Unknown')}")
            print(f"    Status: {game.get('status', 'Unknown')}")
            print(f"    Game ID: {game.get('game_id', 'Unknown')}")
            print(f"    Time: {game.get('game_datetime', 'Unknown')}")
            
            # Test 2: Try to get probable pitchers for this game
            game_id = game.get('game_id')
            if game_id:
                try:
                    pitchers = statsapi.game_probable_pitchers(game_id)
                    print(f"    Probable Pitchers Result: {pitchers}")
                    
                    if isinstance(pitchers, dict):
                        home_pitcher = pitchers.get('home', {}).get('fullName', 'Not found')
                        away_pitcher = pitchers.get('away', {}).get('fullName', 'Not found')
                        print(f"    Home Pitcher: {home_pitcher}")
                        print(f"    Away Pitcher: {away_pitcher}")
                    else:
                        print(f"    Unexpected pitcher data format: {type(pitchers)}")
                        
                except Exception as e:
                    print(f"    ✗ Error getting pitchers: {e}")
                
                # Test 3: Try to get game data
                try:
                    game_data = statsapi.get('game', {'gamePk': game_id})
                    print(f"    Game data keys: {list(game_data.keys()) if isinstance(game_data, dict) else 'Not dict'}")
                    
                    if 'gameData' in game_data and 'probablePitchers' in game_data['gameData']:
                        prob_pitchers = game_data['gameData']['probablePitchers']
                        print(f"    Probable pitchers from game data: {prob_pitchers}")
                        
                except Exception as e:
                    print(f"    ✗ Error getting game data: {e}")
            
            print()
            
    except Exception as e:
        print(f"✗ MLB API test failed: {e}")

def test_rotowire_direct():
    """Test Rotowire scraping directly"""
    print("=== TESTING ROTOWIRE SCRAPING DIRECTLY ===\n")
    
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    
    try:
        print("1. Testing Rotowire lineup fetch...")
        rotowire_data = fetch_rotowire_expected_lineups(today)
        
        if rotowire_data:
            print(f"✓ Found {len(rotowire_data)} games from Rotowire")
            
            for game_id, data in list(rotowire_data.items())[:3]:  # Show first 3
                print(f"\n  Game: {game_id}")
                print(f"    Home team: {data.get('home_team', 'Unknown')}")
                print(f"    Away team: {data.get('away_team', 'Unknown')}")
                print(f"    Home pitcher: {data.get('home_pitcher', 'Unknown')}")
                print(f"    Away pitcher: {data.get('away_pitcher', 'Unknown')}")
                print(f"    Home lineup ({len(data.get('home', []))} players): {data.get('home', [])[:3]}...")
                print(f"    Away lineup ({len(data.get('away', []))} players): {data.get('away', [])[:3]}...")
        else:
            print("✗ No data returned from Rotowire")
            
    except Exception as e:
        print(f"✗ Rotowire test failed: {e}")

def test_integrated_fetching():
    """Test the integrated fetching function"""
    print("=== TESTING INTEGRATED LINEUP FETCHING ===\n")
    
    # Create sample games DataFrame (like your predictor does)
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    
    try:
        # Get schedule first
        schedule = statsapi.schedule(date=today)
        games_list = []
        
        for game in schedule[:3]:  # Test first 3 games
            home_team = convert_mlb_team_to_code(game['home_name'])
            away_team = convert_mlb_team_to_code(game['away_name'])
            
            if home_team and away_team:
                game_data = {
                    'game_id': f"{home_team}_{away_team}_{today}",
                    'game_id_mlb': game['game_id'],
                    'home_team': home_team,
                    'away_team': away_team,
                    'home_team_name': game['home_name'],
                    'away_team_name': game['away_name']
                }
                games_list.append(game_data)
        
        if games_list:
            games_df = pd.DataFrame(games_list)
            print(f"Created test games DataFrame with {len(games_df)} games")
            
            # Test the actual fetching function
            print("\n2. Testing fetch_lineups_and_pitchers function...")
            lineups, pitchers = fetch_lineups_and_pitchers(games_df, early_run=False)
            
            print(f"✓ Function returned {len(lineups)} lineups and {len(pitchers)} pitcher sets")
            
            for game_id in lineups.keys():
                lineup = lineups[game_id]
                pitcher_set = pitchers.get(game_id, {})
                
                print(f"\n  Game: {game_id}")
                print(f"    Home lineup: {len(lineup.get('home', []))} players")
                print(f"    Away lineup: {len(lineup.get('away', []))} players")
                print(f"    Home pitcher: {pitcher_set.get('home', 'Not found')}")
                print(f"    Away pitcher: {pitcher_set.get('away', 'Not found')}")
                
                if lineup.get('home'):
                    print(f"    Sample home players: {lineup['home'][:3]}")
                if lineup.get('away'):
                    print(f"    Sample away players: {lineup['away'][:3]}")
        else:
            print("✗ No games to test with")
            
    except Exception as e:
        print(f"✗ Integrated test failed: {e}")

def convert_mlb_team_to_code(team_name):
    """Convert MLB API team name to team code"""
    mappings = {
        'Angels': 'LAA', 'Astros': 'HOU', 'Athletics': 'OAK', 'Blue Jays': 'TOR',
        'Braves': 'ATL', 'Brewers': 'MIL', 'Cardinals': 'STL', 'Cubs': 'CHC',
        'D-backs': 'ARI', 'Diamondbacks': 'ARI', 'Dodgers': 'LAD', 'Giants': 'SF',
        'Guardians': 'CLE', 'Indians': 'CLE', 'Mariners': 'SEA', 'Marlins': 'MIA',
        'Mets': 'NYM', 'Nationals': 'WSH', 'Orioles': 'BAL', 'Padres': 'SD',
        'Phillies': 'PHI', 'Pirates': 'PIT', 'Rangers': 'TEX', 'Rays': 'TB',
        'Red Sox': 'BOS', 'Reds': 'CIN', 'Rockies': 'COL', 'Royals': 'KC',
        'Tigers': 'DET', 'Twins': 'MIN', 'White Sox': 'CWS', 'Yankees': 'NYY'
    }
    
    if team_name in mappings:
        return mappings[team_name]
    
    # Try partial match
    for name, code in mappings.items():
        if team_name.lower() in name.lower() or name.lower() in team_name.lower():
            return code
    
    return None

def test_specific_game():
    """Test fetching data for a specific game"""
    print("=== TESTING SPECIFIC GAME ===\n")
    
    # Let's test one of the games you mentioned
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    
    try:
        schedule = statsapi.schedule(date=today)
        
        # Find CLE vs LAD game
        target_game = None
        for game in schedule:
            if ('Cleveland' in game.get('away_name', '') and 'Los Angeles Dodgers' in game.get('home_name', '')) or \
               ('Guardians' in game.get('away_name', '') and 'Dodgers' in game.get('home_name', '')):
                target_game = game
                break
        
        if target_game:
            print(f"Found target game: {target_game.get('away_name')} @ {target_game.get('home_name')}")
            game_id = target_game.get('game_id')
            
            # Test multiple methods to get pitcher data
            print("\nMethod 1: game_probable_pitchers")
            try:
                pitchers1 = statsapi.game_probable_pitchers(game_id)
                print(f"Result: {pitchers1}")
            except Exception as e:
                print(f"Failed: {e}")
            
            print("\nMethod 2: game data")
            try:
                game_data = statsapi.get('game', {'gamePk': game_id})
                if 'gameData' in game_data and 'probablePitchers' in game_data['gameData']:
                    pitchers2 = game_data['gameData']['probablePitchers']
                    print(f"Result: {pitchers2}")
                else:
                    print("No probable pitchers in game data")
            except Exception as e:
                print(f"Failed: {e}")
            
            print("\nMethod 3: schedule data")
            try:
                schedule_detailed = statsapi.schedule(game_id=game_id)
                if schedule_detailed:
                    game_info = schedule_detailed[0]
                    print(f"Schedule keys: {list(game_info.keys())}")
                    home_pitcher = game_info.get('home_probable_pitcher', 'Not found')
                    away_pitcher = game_info.get('away_probable_pitcher', 'Not found')
                    print(f"Home pitcher: {home_pitcher}")
                    print(f"Away pitcher: {away_pitcher}")
            except Exception as e:
                print(f"Failed: {e}")
                
        else:
            print("Target game not found in today's schedule")
            print("Available games:")
            for game in schedule[:5]:
                print(f"  {game.get('away_name')} @ {game.get('home_name')}")
                
    except Exception as e:
        print(f"Specific game test failed: {e}")

def main():
    """Run all tests"""
    print("DEBUGGING DATA FETCHING ISSUES")
    print("=" * 50)
    
    test_mlb_api_direct()
    print("\n" + "=" * 50 + "\n")
    
    test_rotowire_direct()
    print("\n" + "=" * 50 + "\n")
    
    test_integrated_fetching()
    print("\n" + "=" * 50 + "\n")
    
    test_specific_game()
    print("\n" + "=" * 50)
    print("DEBUG COMPLETE")

if __name__ == "__main__":
    main()
