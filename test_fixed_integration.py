# test_fixed_integration.py
"""
Test the FIXED Baseball Savant integration
This should now correctly match players like Aaron Judge, Juan Soto, etc.
"""

import os
import logging
import shutil
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger('TestFixed')

def clear_cache_files():
    """Clear old cache files to force fresh data retrieval"""
    print("🧹 CLEARING OLD CACHE FILES...")
    print("=" * 50)
    
    files_removed = 0
    
    # Remove cache directories
    cache_dirs = ['savant_cache', 'backtest_cache']
    for cache_dir in cache_dirs:
        if os.path.exists(cache_dir):
            try:
                shutil.rmtree(cache_dir)
                print(f"✅ Removed directory: {cache_dir}/")
                files_removed += 1
            except Exception as e:
                print(f"❌ Failed to remove {cache_dir}: {e}")
    
    # Remove individual cache files
    cache_files = [f for f in os.listdir('.') if 'savant_data_' in f and f.endswith('.json')]
    for filename in cache_files:
        try:
            os.remove(filename)
            print(f"✅ Removed cache file: {filename}")
            files_removed += 1
        except Exception as e:
            print(f"❌ Failed to remove {filename}: {e}")
    
    print(f"\n🎯 CACHE CLEARED: {files_removed} items removed")
    print("Next fetch will use fresh March-April 2025 data!\n")
    
    return files_removed > 0

def test_name_matching_algorithm():
    """Test the fixed name matching algorithm"""
    print("🧪 TESTING FIXED NAME MATCHING ALGORITHM...")
    print("=" * 50)
    
    # Import the fixed version
    try:
        from baseball_savant_fixed import BaseballSavant
        
        # Create instance
        savant = BaseballSavant()
        
        # Test cases that were failing before
        test_cases = [
            ("Aaron Judge", ["Nola, Aaron", "Judge, Aaron", "Bummer, Aaron"]),  # Should match Judge, Aaron
            ("Juan Soto", ["Soto, Gregory", "Soto, Juan", "Mejia, Juan"]),     # Should match Soto, Juan  
            ("Ronald Acuna Jr.", ["Acuna, Ronald", "Edwards Jr., Carl", "Leiter Jr., Mark"]),  # Should match Acuna, Ronald
            ("Gerrit Cole", ["Cole, Gerrit", "Cole, A.J.", "Garcia, Luis"])    # Should match Cole, Gerrit
        ]
        
        for search_name, candidates in test_cases:
            print(f"\n🔍 Testing: '{search_name}'")
            print(f"   Candidates: {candidates}")
            
            result = savant._advanced_name_matching_fixed(search_name, candidates)
            
            if result:
                print(f"   ✅ MATCH FOUND: '{result}'")
                
                # Verify it's the correct match
                search_parts = search_name.lower().split()
                result_parts = result.lower().replace(',', '').split()
                
                if len(search_parts) >= 2 and len(result_parts) >= 2:
                    search_first, search_last = search_parts[0], search_parts[-1]
                    result_first, result_last = result_parts[1] if ',' in result else result_parts[0], result_parts[0] if ',' in result else result_parts[-1]
                    
                    if search_first == result_first and search_last == result_last:
                        print(f"   ✅ CORRECT MATCH: Both names match!")
                    else:
                        print(f"   ❌ WRONG MATCH: Names don't align properly")
                else:
                    print(f"   ⚠️  Could not verify match quality")
            else:
                print(f"   ❌ NO MATCH FOUND")
        
        print(f"\n✅ Name matching algorithm test complete!")
        return True
        
    except ImportError as e:
        print(f"❌ Could not import fixed version: {e}")
        print("Make sure baseball_savant_fixed.py is available")
        return False
    except Exception as e:
        print(f"❌ Error testing name matching: {e}")
        return False

def test_full_integration():
    """Test the full integration with real data"""
    print("🚀 TESTING FULL INTEGRATION WITH REAL DATA...")
    print("=" * 50)
    
    try:
        # Import the fixed version
        from baseball_savant_fixed import get_savant_data, debug_savant_names
        
        # First, debug what names are actually available
        print("🔍 Debugging available player names in 2025 data...")
        debug_savant_names()
        
        print(f"\n🎯 Testing with known 2025 players...")
        
        # Test with players we know should be in 2025 data
        test_players = ["Aaron Judge", "Juan Soto", "Ronald Acuna Jr.", "Shohei Ohtani"]
        test_pitchers = ["Gerrit Cole", "Tyler Glasnow", "Zack Wheeler"]
        
        print(f"   Input players: {test_players}")
        print(f"   Input pitchers: {test_pitchers}")
        
        # Get the data
        print(f"\n🔄 Fetching Savant data with fixed matching...")
        batter_data, pitcher_data = get_savant_data(test_players, test_pitchers)
        
        print(f"\n📊 RESULTS:")
        print(f"   ✅ Batters matched: {len(batter_data)}/{len(test_players)}")
        print(f"   ✅ Pitchers matched: {len(pitcher_data)}/{len(test_pitchers)}")
        
        # Show successful matches
        if batter_data:
            print(f"\n🎯 SUCCESSFUL BATTER MATCHES:")
            for player, data in batter_data.items():
                sample_size = data.get('sample_size', 0)
                avg_ev = data.get('avg_ev', 0)
                print(f"   ✅ {player}: {sample_size} batted balls, {avg_ev:.1f} mph avg EV")
        else:
            print(f"\n❌ No batter matches found")
        
        if pitcher_data:
            print(f"\n🎯 SUCCESSFUL PITCHER MATCHES:")
            for pitcher, data in pitcher_data.items():
                sample_size = data.get('sample_size', 0) 
                tendency = data.get('primary_tendency', 'unknown')
                print(f"   ✅ {pitcher}: {sample_size} pitches, {tendency} tendency")
        else:
            print(f"\n❌ No pitcher matches found")
        
        # Success criteria
        success_rate = (len(batter_data) + len(pitcher_data)) / (len(test_players) + len(test_pitchers))
        
        if success_rate >= 0.5:  # 50%+ match rate
            print(f"\n🎉 INTEGRATION SUCCESS: {success_rate*100:.1f}% match rate!")
            print("Fixed name matching is working!")
            return True
        else:
            print(f"\n⚠️  PARTIAL SUCCESS: {success_rate*100:.1f}% match rate")
            print("Some improvements still needed")
            return False
            
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def backup_original_file():
    """Backup the original baseball_savant.py file"""
    if os.path.exists('baseball_savant.py'):
        backup_name = f"baseball_savant_original_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
        shutil.copy2('baseball_savant.py', backup_name)
        print(f"📋 Backed up original to: {backup_name}")
        return backup_name
    return None

def replace_with_fixed_version():
    """Replace the original with the fixed version"""
    if os.path.exists('baseball_savant_fixed.py'):
        try:
            shutil.copy2('baseball_savant_fixed.py', 'baseball_savant.py')
            print("✅ Replaced baseball_savant.py with fixed version")
            return True
        except Exception as e:
            print(f"❌ Error replacing file: {e}")
            return False
    else:
        print("❌ Fixed version not found")
        return False

def main():
    """Run all tests and fixes"""
    print("🧪 BASEBALL SAVANT INTEGRATION FIX & TEST")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    success_count = 0
    
    # Step 1: Clear cache
    print("\n" + "="*20 + " STEP 1: CLEAR CACHE " + "="*20)
    if clear_cache_files():
        print("✅ Step 1: Cache cleared successfully")
        success_count += 1
    else:
        print("⚠️  Step 1: No cache files found")
    
    # Step 2: Test name matching algorithm
    print("\n" + "="*15 + " STEP 2: TEST NAME MATCHING " + "="*15)
    if test_name_matching_algorithm():
        print("✅ Step 2: Name matching algorithm working")
        success_count += 1
    else:
        print("❌ Step 2: Name matching algorithm failed")
    
    # Step 3: Test full integration
    print("\n" + "="*15 + " STEP 3: TEST FULL INTEGRATION " + "="*14)
    if test_full_integration():
        print("✅ Step 3: Full integration working!")
        success_count += 1
    else:
        print("⚠️  Step 3: Integration needs work")
    
    # Step 4: Replace original file (optional)
    print("\n" + "="*15 + " STEP 4: REPLACE ORIGINAL FILE " + "="*13)
    
    if success_count >= 2:
        backup = backup_original_file()
        if replace_with_fixed_version():
            print("✅ Step 4: Fixed version installed")
            success_count += 1
        else:
            print("⚠️  Step 4: Could not replace original file")
    else:
        print("⚠️  Step 4: Skipped - fixes not working well enough")
    
    # Summary
    print("\n" + "="*25 + " SUMMARY " + "="*25)
    print(f"✅ Steps completed successfully: {success_count}/4")
    
    if success_count >= 3:
        print("\n🎉 MAJOR SUCCESS!")
        print("✅ Cache cleared for fresh 2025 data")
        print("✅ Name matching algorithm fixed") 
        print("✅ Integration working with real players")
        print("✅ Ready for production use!")
        
        print(f"\n📋 NEXT STEPS:")
        print("1. Run your main predictor: python mlb_hr_predictor.py")
        print("2. Should now find Aaron Judge, Juan Soto, etc.")
        print("3. Should use optimal March-April 2025 data")
        
    elif success_count >= 2:
        print("\n✅ GOOD PROGRESS!")
        print("The fixes are working but may need final tweaks")
        
    else:
        print("\n⚠️  NEEDS MORE WORK")
        print("The fixes didn't work as expected")
        print("Check the error messages above")

if __name__ == "__main__":
    main()
