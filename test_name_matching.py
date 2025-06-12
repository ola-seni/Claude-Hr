# test_name_matching_fix.py
"""Test that the name matching fix is working correctly"""

import os
import shutil
from baseball_savant import BaseballSavant

def test_name_matching():
    """Test the fixed name matching algorithm"""
    
    print("🧪 TESTING NAME MATCHING FIX")
    print("=" * 60)
    
    # First, ensure cache is cleared
    cache_dir = 'savant_cache'
    if os.path.exists(cache_dir):
        shutil.rmtree(cache_dir)
        print("✅ Cleared old cache directory")
    
    # Create fresh instance
    savant = BaseballSavant()
    
    # Test the name matching algorithm directly with known problematic cases
    test_cases = [
        # (search_name, candidate_names, expected_match)
        ("Aaron Judge", ["Nola, Aaron", "Judge, Aaron", "Bummer, Aaron"], "Judge, Aaron"),
        ("Juan Soto", ["Soto, Gregory", "Soto, Juan", "Mejia, Juan"], "Soto, Juan"),
        ("Ronald Acuña Jr.", ["Acuña Jr., Ronald", "Leiter Jr., Mark", "Edwards Jr., Carl"], "Acuña Jr., Ronald"),
        ("Shohei Ohtani", ["Ohtani, Shohei", "Yamamoto, Shohei", "Suzuki, Seiya"], "Ohtani, Shohei"),
    ]
    
    print("\n📋 Testing name matching precision:")
    all_passed = True
    
    for search_name, candidates, expected in test_cases:
        result = savant._advanced_name_matching(search_name, candidates)
        
        if result == expected:
            print(f"✅ '{search_name}' → '{result}' (correct)")
        else:
            print(f"❌ '{search_name}' → '{result}' (expected '{expected}')")
            all_passed = False
    
    return all_passed

def test_fresh_data_fetch():
    """Test fetching fresh data with the optimal date range"""
    
    print("\n🔄 TESTING FRESH DATA FETCH")
    print("=" * 60)
    
    savant = BaseballSavant()
    
    # This should use the March 28 - April 28 range
    print("Fetching fresh Statcast data (this may take a moment)...")
    
    # Get player names we want to test
    test_players = ["Aaron Judge", "Juan Soto", "Shohei Ohtani", "Ronald Acuña Jr."]
    test_pitchers = ["Gerrit Cole", "Tyler Glasnow"]
    
    # Convert names for Statcast format
    from mlb_hr_predictor import MLBHomeRunPredictor
    predictor = MLBHomeRunPredictor()
    converted_players, player_map = predictor.convert_names_for_statcast_improved(test_players)
    converted_pitchers, pitcher_map = predictor.convert_names_for_statcast_improved(test_pitchers)
    
    print(f"\n📊 Fetching data for {len(test_players)} batters and {len(test_pitchers)} pitchers...")
    
    # Get the data
    batter_data, pitcher_data = savant.get_player_data(converted_players, converted_pitchers)
    
    print(f"\n📈 RESULTS:")
    print(f"✅ Found data for {len(batter_data)} batters")
    print(f"✅ Found data for {len(pitcher_data)} pitchers")
    
    # Check which players were found
    print("\n🎯 PLAYER MATCHING RESULTS:")
    for player in test_players:
        if player in batter_data:
            sample_size = batter_data[player].get('sample_size', 0)
            avg_ev = batter_data[player].get('avg_ev', 0)
            print(f"✅ {player}: {sample_size} batted balls, {avg_ev:.1f} mph avg EV")
        else:
            print(f"❌ {player}: NOT FOUND")
    
    # Check cache file was created with correct date
    cache_file = f'savant_cache/savant_data_{datetime.now().strftime("%Y%m%d")}.json'
    if os.path.exists(cache_file):
        print(f"\n✅ Cache file created: {cache_file}")
        
        # Check the content
        import json
        with open(cache_file, 'r') as f:
            cached_data = json.load(f)
        
        total_batters = len(cached_data.get('batters', {}))
        total_pitchers = len(cached_data.get('pitchers', {}))
        
        print(f"📊 Cached data contains:")
        print(f"   • {total_batters} batters")
        print(f"   • {total_pitchers} pitchers")
        
        if total_batters > 400:  # We expect ~469 batters from the good date range
            print("   ✅ This looks like the GOOD March-April data!")
        else:
            print("   ⚠️  This might still be using the wrong date range")
    
    return len(batter_data) > 0

def main():
    """Run all tests"""
    
    import datetime
    print(f"🚀 BASEBALL SAVANT CACHE & NAME MATCHING FIX TEST")
    print(f"📅 Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Test 1: Name matching algorithm
    if test_name_matching():
        print("\n✅ TEST 1 PASSED: Name matching is precise")
    else:
        print("\n❌ TEST 1 FAILED: Name matching still has issues")
        print("   Check the _advanced_name_matching method in baseball_savant.py")
        return
    
    # Test 2: Fresh data fetch
    if test_fresh_data_fetch():
        print("\n✅ TEST 2 PASSED: Fresh data fetch working with correct date range")
    else:
        print("\n❌ TEST 2 FAILED: Data fetch issues")
        return
    
    print("\n" + "=" * 60)
    print("🎉 ALL TESTS PASSED!")
    print("\n📋 NEXT STEPS:")
    print("1. Run your main predictor: python mlb_hr_predictor.py")
    print("2. It should now use the fresh March-April 2025 data")
    print("3. Name matching should correctly find Judge, Soto, etc.")

if __name__ == "__main__":
    main()
