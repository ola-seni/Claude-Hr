# test_lineup_fix.py
# Quick test of the fixed lineup fetcher

import pandas as pd
import datetime
import logging
import statsapi
from lineup_fetcher import fetch_lineups_and_pitchers

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('TestLineupFix')

def quick_test():
    """Test the fixed lineup fetcher on a few games"""
    print("=== TESTING FIXED LINEUP FETCHER ===\n")
    
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    
    # Get a few games from MLB API
    try:
        schedule = statsapi.schedule(date=today)
        print(f"✓ Found {len(schedule)} games in MLB schedule")
        
        # Create test games DataFrame (just like your predictor does)
        games_list = []
        for game in schedule[:5]:  # Test first 5 games
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
        
        if not games_list:
            print("✗ No games to test")
            return
            
        games_df = pd.DataFrame(games_list)
        print(f"Created test DataFrame with {len(games_df)} games\n")
        
        # Test the FIXED lineup fetcher
        print("Testing FIXED fetch_lineups_and_pitchers function...")
        lineups, pitchers = fetch_lineups_and_pitchers(games_df, early_run=False)
        
        print(f"\n=== RESULTS ===")
        print(f"✓ Got data for {len(lineups)} games")
        
        # Show detailed results
        games_with_lineups = 0
        games_with_pitchers = 0
        total_players = 0
        
        for game_id in lineups.keys():
            lineup = lineups[game_id]
            pitcher_set = pitchers.get(game_id, {})
            
            home_count = len(lineup.get('home', []))
            away_count = len(lineup.get('away', []))
            home_pitcher = pitcher_set.get('home', 'TBD')
            away_pitcher = pitcher_set.get('away', 'TBD')
            
            total_players += home_count + away_count
            
            if home_count > 0 or away_count > 0:
                games_with_lineups += 1
            
            if home_pitcher != 'TBD' or away_pitcher != 'TBD':
                games_with_pitchers += 1
            
            print(f"\n{game_id}:")
            print(f"  Lineups: Home={home_count}, Away={away_count}")
            print(f"  Pitchers: {home_pitcher} vs {away_pitcher}")
            
            if home_count > 0:
                print(f"  Sample home: {lineup['home'][:3]}...")
            if away_count > 0:
                print(f"  Sample away: {lineup['away'][:3]}...")
            
            # Status
            if home_count == 0 and away_count == 0 and home_pitcher == 'TBD' and away_pitcher == 'TBD':
                print(f"  ⚠️  WOULD STILL BE SKIPPED: No data")
            elif home_count == 0 and away_count == 0:
                print(f"  ⚠️  WOULD BE SKIPPED: Empty lineups (but has pitchers)")
            else:
                print(f"  ✅ WOULD BE PROCESSED")
        
        print(f"\n=== SUMMARY ===")
        print(f"Total games: {len(lineups)}")
        print(f"Games with lineups: {games_with_lineups}")
        print(f"Games with pitchers: {games_with_pitchers}")
        print(f"Total players found: {total_players}")
        print(f"Average players per game: {total_players/len(lineups) if lineups else 0:.1f}")
        
        # Compare to what you saw before
        print(f"\n=== IMPROVEMENT CHECK ===")
        if games_with_pitchers >= len(lineups) * 0.8:  # 80%+ have pitchers
            print("✅ PITCHER FETCHING: MUCH IMPROVED")
        else:
            print("⚠️  PITCHER FETCHING: Still has issues")
            
        if games_with_lineups >= len(lineups) * 0.6:  # 60%+ have lineups
            print("✅ LINEUP FETCHING: MUCH IMPROVED")
        else:
            print("⚠️  LINEUP FETCHING: Still has issues")
            
        if total_players > len(lineups) * 10:  # Average >10 players per game
            print("✅ PLAYER DATA: MUCH IMPROVED")
        else:
            print("⚠️  PLAYER DATA: Still limited")
            
    except Exception as e:
        print(f"✗ Test failed: {e}")

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

if __name__ == "__main__":
    quick_test()
