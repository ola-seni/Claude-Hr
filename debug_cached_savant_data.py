# debug_cached_savant_data.py
# Examine the cached Statcast data to see actual player name formats

import json
import os
from collections import Counter
import pandas as pd

def examine_cached_data():
    """Look at the cached Statcast data to understand name formats"""
    
    cache_file = 'savant_cache/savant_data_20250529.json'
    
    if not os.path.exists(cache_file):
        print(f"❌ Cached file not found: {cache_file}")
        return
    
    print("🔍 EXAMINING CACHED STATCAST DATA")
    print("=" * 50)
    
    try:
        with open(cache_file, 'r') as f:
            data = json.load(f)
        
        print(f"✅ Loaded cached data successfully")
        print(f"📊 Data structure: {list(data.keys())}")
        
        # Look at batters data
        batters = data.get('batters', {})
        pitchers = data.get('pitchers', {})
        
        print(f"\n📊 SUMMARY:")
        print(f"   Batters in cache: {len(batters)}")
        print(f"   Pitchers in cache: {len(pitchers)}")
        
        # Show sample batter names
        if batters:
            print(f"\n👥 SAMPLE BATTER NAMES (first 20):")
            batter_names = list(batters.keys())[:20]
            for i, name in enumerate(batter_names, 1):
                print(f"   {i:2d}. '{name}'")
            
            print(f"\n🔍 BATTER NAME ANALYSIS:")
            
            # Analyze name patterns
            comma_names = [n for n in batters.keys() if ',' in n]
            space_names = [n for n in batters.keys() if ',' not in n and ' ' in n]
            single_names = [n for n in batters.keys() if ' ' not in n]
            
            print(f"   Names with commas: {len(comma_names)} (e.g., {comma_names[:3]})")
            print(f"   Names with spaces: {len(space_names)} (e.g., {space_names[:3]})")
            print(f"   Single names: {len(single_names)} (e.g., {single_names[:3]})")
            
            # Look for our test players
            test_players = ['Aaron Judge', 'Juan Soto', 'Ronald Acuña Jr.', 'José Altuve']
            test_variations = [
                'Judge, Aaron', 'Aaron Judge', 'Judge, A.',
                'Soto, Juan', 'Juan Soto', 'Soto, J.',
                'Acuña Jr., Ronald', 'Ronald Acuña Jr.', 'Acuna, Ronald',
                'Altuve, José', 'José Altuve', 'Altuve, Jose'
            ]
            
            print(f"\n🎯 SEARCHING FOR TEST PLAYERS:")
            for player in test_players:
                found_variations = []
                for name in batters.keys():
                    # Check if this cached name could match our test player
                    if any(part.lower() in name.lower() for part in player.split()):
                        found_variations.append(name)
                
                if found_variations:
                    print(f"   '{player}' possibly matches: {found_variations[:3]}")
                else:
                    print(f"   '{player}' -> ❌ NO MATCHES FOUND")
            
            # Look for any names containing our test players' last names
            last_names = ['Judge', 'Soto', 'Acuña', 'Acuna', 'Altuve']
            print(f"\n🔍 SEARCHING BY LAST NAMES:")
            for last_name in last_names:
                matches = [n for n in batters.keys() if last_name.lower() in n.lower()]
                if matches:
                    print(f"   '{last_name}' found in: {matches}")
                else:
                    print(f"   '{last_name}' -> ❌ NOT FOUND")
        
        # Show sample pitcher names
        if pitchers:
            print(f"\n⚾ SAMPLE PITCHER NAMES (first 10):")
            pitcher_names = list(pitchers.keys())[:10]
            for i, name in enumerate(pitcher_names, 1):
                print(f"   {i:2d}. '{name}'")
        
        # Check if the issue is with date range
        print(f"\n📅 CHECKING DATA VALIDITY:")
        if batters:
            sample_batter = list(batters.values())[0]
            sample_size = sample_batter.get('sample_size', 0)
            print(f"   Sample batter data size: {sample_size} batted balls")
            if sample_size == 0:
                print("   ⚠️  WARNING: Sample batter has 0 batted balls - data may be empty/invalid")
        
        return batters, pitchers
        
    except Exception as e:
        print(f"❌ Error examining cached data: {e}")
        return {}, {}

def test_with_realistic_dates():
    """Test with realistic past dates that should have data"""
    
    print(f"\n🕒 TESTING WITH REALISTIC DATES")
    print("=" * 50)
    
    try:
        from baseball_savant import get_savant_data
        
        # Use 2024 season dates that definitely have data
        print("🔄 Fetching fresh data from 2024 season...")
        
        # Clear the cache first so we get fresh data
        cache_dir = 'savant_cache'
        if os.path.exists(cache_dir):
            for file in os.listdir(cache_dir):
                if file.startswith('savant_data_'):
                    os.remove(os.path.join(cache_dir, file))
                    print(f"   Cleared old cache: {file}")
        
        # Test with known active players from 2024
        test_players = ["Judge, Aaron", "Soto, Juan", "Acuna Jr., Ronald"]
        test_pitchers = ["Cole, Gerrit", "Fried, Max"]
        
        print(f"   Testing players: {test_players}")
        print(f"   Testing pitchers: {test_pitchers}")
        
        # This will fetch data with today's date, which will create a cache file
        # But we should modify the fetch to use 2024 dates
        batter_data, pitcher_data = get_savant_data(test_players, test_pitchers)
        
        print(f"\n📊 RESULTS WITH CURRENT METHOD:")
        print(f"   Batters matched: {len(batter_data)}")
        print(f"   Pitchers matched: {len(pitcher_data)}")
        
        if batter_data:
            print(f"   ✅ SUCCESS! Matched batters: {list(batter_data.keys())}")
        if pitcher_data:
            print(f"   ✅ SUCCESS! Matched pitchers: {list(pitcher_data.keys())}")
        
        return len(batter_data) > 0 or len(pitcher_data) > 0
        
    except Exception as e:
        print(f"❌ Error testing with realistic dates: {e}")
        return False

def suggest_fixes():
    """Suggest specific fixes based on what we found"""
    
    print(f"\n💡 SUGGESTED FIXES")
    print("=" * 50)
    
    print("Based on the analysis, here are the likely issues and fixes:")
    
    print("\n1. 🗓️ DATE RANGE ISSUE:")
    print("   Problem: Using future dates (May 2025) with no real data")
    print("   Fix: Use 2024 season dates in baseball_savant.py")
    print("   Code: Change date range to '2024-04-01' to '2024-09-30'")
    
    print("\n2. 📝 NAME FORMAT ISSUE:")
    print("   Problem: Statcast names don't match our generated variations")
    print("   Fix: Add more name format variations based on actual data")
    print("   Code: Enhance convert_names_for_statcast_improved()")
    
    print("\n3. 🔍 MATCHING ALGORITHM:")
    print("   Problem: Name matching is too strict")
    print("   Fix: Add fuzzy matching for similar names")
    print("   Code: Use string similarity in _match_player_data()")
    
    print("\n4. 📊 DATA VALIDATION:")
    print("   Problem: Not checking if retrieved data is valid")
    print("   Fix: Validate data has actual events before processing")
    print("   Code: Add data quality checks in _fetch_statcast_data()")

def main():
    """Run the full debugging process"""
    
    print("🐛 DEBUGGING BASEBALL SAVANT NAME MATCHING")
    print("=" * 60)
    
    # Step 1: Examine cached data
    batters, pitchers = examine_cached_data()
    
    # Step 2: Test with realistic dates
    success = test_with_realistic_dates()
    
    # Step 3: Provide specific suggestions
    suggest_fixes()
    
    print(f"\n🎯 NEXT STEPS:")
    if not batters and not pitchers:
        print("1. ❌ No cached data found - run the integration test first")
    elif len(batters) == 0:
        print("1. 🗓️ Fix the date range issue (use 2024 data)")
        print("2. 📝 Examine actual player names in Statcast data")
        print("3. 🔧 Update name conversion logic")
        print("4. ✅ Re-test integration")
    else:
        print("1. 📝 Update name matching based on discovered formats")
        print("2. 🔧 Enhance fuzzy matching algorithm") 
        print("3. ✅ Re-test with improved matching")
    
    print(f"\n📄 Check the output above for specific name formats found!")

if __name__ == "__main__":
    main()
