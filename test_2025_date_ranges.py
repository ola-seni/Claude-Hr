# test_2025_date_ranges.py
# Test different 2025 date ranges to find what data is actually available

import pandas as pd
from pybaseball import statcast
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('DateRangeTester')

def test_2025_date_ranges():
    """Test various 2025 date ranges to see what data is available"""
    
    print("🗓️ TESTING 2025 MLB SEASON DATE RANGES")
    print("=" * 60)
    print("Finding optimal date range for current 2025 season data...")
    
    # Define test date ranges (all in 2025)
    test_ranges = [
        # Most recent (what we were trying)
        ("2025-05-20", "2025-05-28", "Most Recent Week"),
        ("2025-05-14", "2025-05-28", "Last 2 Weeks"), 
        
        # Go back a bit more (in case there's a delay)
        ("2025-05-01", "2025-05-15", "Early May 2025"),
        ("2025-04-15", "2025-04-30", "Mid-Late April 2025"),
        ("2025-04-01", "2025-04-15", "Early April 2025"),
        
        # Season start (should definitely have data)
        ("2025-03-25", "2025-04-05", "Season Opening"),
        
        # Larger ranges for more data
        ("2025-04-01", "2025-05-01", "Full April 2025"),
        ("2025-03-28", "2025-04-28", "First Month of Season"),
    ]
    
    results = []
    
    for start_date, end_date, description in test_ranges:
        print(f"\n🔍 Testing: {description} ({start_date} to {end_date})")
        
        try:
            # Test the date range
            data = statcast(start_dt=start_date, end_dt=end_date)
            
            if data is None or len(data) == 0:
                print(f"   ❌ No data returned")
                results.append({
                    'range': description,
                    'start': start_date,
                    'end': end_date,
                    'events': 0,
                    'batters': 0,
                    'pitchers': 0,
                    'status': 'No Data'
                })
            else:
                # Analyze the data
                total_events = len(data)
                unique_batters = data['batter'].nunique() if 'batter' in data.columns else 0
                unique_pitchers = data['pitcher'].nunique() if 'pitcher' in data.columns else 0
                
                print(f"   ✅ SUCCESS: {total_events:,} events, {unique_batters} batters, {unique_pitchers} pitchers")
                
                # Show some sample player names if available
                if 'player_name' in data.columns and not data['player_name'].isna().all():
                    sample_names = data['player_name'].dropna().unique()[:5]
                    print(f"   👥 Sample players: {list(sample_names)}")
                
                results.append({
                    'range': description,
                    'start': start_date,
                    'end': end_date,
                    'events': total_events,
                    'batters': unique_batters,
                    'pitchers': unique_pitchers,
                    'status': 'Success'
                })
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            results.append({
                'range': description,
                'start': start_date,
                'end': end_date,
                'events': 0,
                'batters': 0,
                'pitchers': 0,
                'status': f'Error: {str(e)[:50]}'
            })
    
    # Summary of results
    print(f"\n📊 SUMMARY OF 2025 DATE RANGE TESTS")
    print("=" * 60)
    
    successful_ranges = [r for r in results if r['events'] > 0]
    
    if successful_ranges:
        print(f"✅ Found {len(successful_ranges)} working date ranges:")
        
        # Sort by number of events (descending)
        successful_ranges.sort(key=lambda x: x['events'], reverse=True)
        
        for i, result in enumerate(successful_ranges, 1):
            print(f"{i}. {result['range']}: {result['events']:,} events ({result['batters']} batters)")
            print(f"   📅 {result['start']} to {result['end']}")
        
        # Recommend the best range
        best_range = successful_ranges[0]
        print(f"\n🎯 RECOMMENDED DATE RANGE:")
        print(f"   Range: {best_range['start']} to {best_range['end']}")
        print(f"   Description: {best_range['range']}")
        print(f"   Data: {best_range['events']:,} events, {best_range['batters']} batters, {best_range['pitchers']} pitchers")
        
        return best_range['start'], best_range['end']
        
    else:
        print("❌ No working date ranges found for 2025 season!")
        print("This suggests either:")
        print("1. PyBaseball library has a delay getting 2025 data")
        print("2. MLB Statcast API issues")
        print("3. Different parameters needed for current season")
        
        return None, None

def test_with_recommended_dates():
    """Test our integration with the best 2025 date range"""
    
    print(f"\n🚀 TESTING INTEGRATION WITH OPTIMAL 2025 DATES")
    print("=" * 60)
    
    # First find the best date range
    start_date, end_date = test_2025_date_ranges()
    
    if not start_date:
        print("❌ No good date range found - cannot test integration")
        return False
    
    print(f"\n🔄 Testing Baseball Savant integration with {start_date} to {end_date}...")
    
    try:
        # Test with known 2025 players (should be active)
        test_players = ["Aaron Judge", "Juan Soto", "Shohei Ohtani", "Ronald Acuna Jr."]
        test_pitchers = ["Gerrit Cole", "Tyler Glasnow", "Zack Wheeler"]
        
        print(f"Test players: {test_players}")
        print(f"Test pitchers: {test_pitchers}")
        
        # Get data for this date range
        data = statcast(start_dt=start_date, end_dt=end_date)
        
        if data is None or len(data) == 0:
            print("❌ No data retrieved for testing")
            return False
        
        # Look for our test players in the data
        player_names_in_data = data['player_name'].dropna().unique()
        
        print(f"\n🔍 SEARCHING FOR TEST PLAYERS IN 2025 DATA:")
        
        found_players = []
        for test_player in test_players:
            # Look for matches
            matches = []
            for data_name in player_names_in_data:
                # Check if test player parts are in data name
                test_parts = test_player.lower().split()
                data_parts = data_name.lower().split()
                
                # Look for last name match
                if len(test_parts) >= 2 and len(data_parts) >= 2:
                    if test_parts[-1] in data_parts or any(test_part in data_name.lower() for test_part in test_parts):
                        matches.append(data_name)
            
            if matches:
                print(f"   ✅ '{test_player}' found as: {matches[:3]}")
                found_players.extend(matches[:1])  # Take first match
            else:
                print(f"   ❌ '{test_player}' not found")
        
        if found_players:
            print(f"\n🎉 SUCCESS: Found {len(found_players)} test players in 2025 data!")
            print(f"   Players found: {found_players}")
            
            # Test the actual matching logic
            print(f"\n🧪 Testing name matching logic...")
            from baseball_savant import BaseballSavant
            savant = BaseballSavant()
            
            # Process a small subset of data to test matching
            sample_data = data.head(1000)  # Just first 1000 events for speed
            batter_data = savant._process_batter_data(sample_data)
            
            print(f"   Processed {len(batter_data)} batter entries from sample data")
            
            # Try to match our test players
            matched_players = savant._match_player_data(test_players, batter_data)
            
            print(f"   Matched {len(matched_players)} test players:")
            for player, data in matched_players.items():
                print(f"     ✅ {player}: {data.get('sample_size', 0)} batted balls")
            
            if len(matched_players) > 0:
                print(f"\n🎉 FULL INTEGRATION SUCCESS with 2025 data!")
                return True
            else:
                print(f"\n⚠️  Data found but name matching still needs work")
                return False
        else:
            print(f"\n❌ No test players found in 2025 data")
            return False
            
    except Exception as e:
        print(f"❌ Error testing integration: {e}")
        return False

def main():
    """Run comprehensive 2025 date range testing"""
    
    print("🎯 2025 MLB SEASON DATA AVAILABILITY TEST")
    print("=" * 60)
    print("Finding the best date range for current 2025 season predictions...")
    
    # Test different 2025 date ranges
    success = test_with_recommended_dates()
    
    if success:
        print(f"\n✅ SOLUTION FOUND: Use the recommended 2025 date range above")
        print(f"   Update your baseball_savant.py to use these dates instead of May 14-28")
    else:
        print(f"\n❌ Need further investigation:")
        print(f"   1. Check if PyBaseball needs updates")
        print(f"   2. Try different MLB data sources")
        print(f"   3. Check MLB Statcast API status")
        print(f"   4. Consider using slightly older 2025 data (early season)")

if __name__ == "__main__":
    main()
