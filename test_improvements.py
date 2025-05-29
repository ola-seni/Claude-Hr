# test_improvements.py - Quick test of your Baseball Savant integration

import logging
from datetime import datetime
import pandas as pd

# Set up logging to see all the messages
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger('Test')

def test_name_conversion():
    """Test the improved name conversion"""
    
    # Import your predictor
    from mlb_hr_predictor import MLBHomeRunPredictor
    
    # Create predictor instance
    predictor = MLBHomeRunPredictor()
    
    # Test players with various name formats
    test_players = [
        "Aaron Judge",           # Standard format
        "José Altuve",          # Accent
        "Ronald Acuña Jr.",     # Jr suffix  
        "Francisco Lindor",     # Standard
        "Julio Rodríguez",      # Accent
        "Vladimir Guerrero Jr." # Jr suffix
    ]
    
    print("🧪 TESTING NAME CONVERSION...")
    print("=" * 50)
    
    # Test the conversion function
    converted_names, name_map = predictor.convert_names_for_statcast_improved(test_players)
    
    print(f"✅ INPUT: {len(test_players)} player names")
    print(f"✅ OUTPUT: {len(converted_names)} name variations")
    print(f"✅ MAPPING: {len(name_map)} entries")
    
    print("\n📋 NAME VARIATIONS CREATED:")
    for original in test_players:
        variations = [name for name, orig in name_map.items() if orig == original]
        print(f"'{original}' -> {len(variations)} variations")
        for var in variations[:3]:  # Show first 3
            print(f"    • {var}")
        if len(variations) > 3:
            print(f"    • ... and {len(variations)-3} more")
    
    return converted_names, name_map

def test_savant_integration():
    """Test Baseball Savant data fetching"""
    
    print("\n🎯 TESTING BASEBALL SAVANT INTEGRATION...")
    print("=" * 50)
    
    try:
        from baseball_savant import get_savant_data
        
        # Test with a few known players
        test_players = ["Judge, Aaron", "Soto, Juan"]  # Statcast format
        test_pitchers = ["Cole, Gerrit"]
        
        print(f"Testing with players: {test_players}")
        print(f"Testing with pitchers: {test_pitchers}")
        
        # Try to get data
        batter_data, pitcher_data = get_savant_data(test_players, test_pitchers)
        
        print(f"\n📊 RESULTS:")
        print(f"✅ Batter data returned: {len(batter_data)} players")
        print(f"✅ Pitcher data returned: {len(pitcher_data)} pitchers")
        
        # Show sample data
        if batter_data:
            sample_player = list(batter_data.keys())[0]
            sample_data = batter_data[sample_player]
            print(f"\n📋 SAMPLE BATTER DATA ({sample_player}):")
            for key, value in list(sample_data.items())[:5]:
                print(f"    • {key}: {value}")
        
        if pitcher_data:
            sample_pitcher = list(pitcher_data.keys())[0]
            sample_data = pitcher_data[sample_pitcher]
            print(f"\n📋 SAMPLE PITCHER DATA ({sample_pitcher}):")
            for key, value in list(sample_data.items())[:5]:
                print(f"    • {key}: {value}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error fetching Savant data: {e}")
        return False

def test_integration_workflow():
    """Test the full integration workflow"""
    
    print("\n🚀 TESTING FULL INTEGRATION WORKFLOW...")
    print("=" * 50)
    
    try:
        from mlb_hr_predictor import MLBHomeRunPredictor
        
        # Create minimal test setup
        predictor = MLBHomeRunPredictor()
        
        # Mock some lineups (like you'd get from games)
        predictor.lineups = {
            'TEST_GAME_1': {
                'home': ['Aaron Judge', 'Juan Soto', 'Anthony Rizzo'],
                'away': ['Ronald Acuña Jr.', 'Freddie Freeman', 'Mookie Betts']
            }
        }
        
        predictor.probable_pitchers = {
            'TEST_GAME_1': {
                'home': 'Gerrit Cole',
                'away': 'Max Fried'
            }
        }
        
        print("✅ Mock data created")
        print(f"    • Players: {sum(len(lineup['home']) + len(lineup['away']) for lineup in predictor.lineups.values())}")
        print(f"    • Pitchers: {sum(2 for _ in predictor.probable_pitchers.values())}")
        
        # Try to run the integration
        print("\n🔄 Running integrate_savant_data()...")
        predictor.integrate_savant_data()
        
        print("✅ Integration completed without errors!")
        
        # Check if any data was actually integrated
        enhanced_players = 0
        for player_name in predictor.player_stats:
            if 'spray_angle' in predictor.player_stats[player_name]:
                enhanced_players += 1
        
        print(f"📊 INTEGRATION RESULTS:")
        print(f"    • Total players: {len(predictor.player_stats)}")
        print(f"    • Enhanced with Savant: {enhanced_players}")
        
        if enhanced_players > 0:
            print("🎉 SUCCESS: Savant data integration is working!")
            return True
        else:
            print("⚠️  WARNING: No players were enhanced with Savant data")
            return False
            
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("🧪 BASEBALL SAVANT INTEGRATION TEST SUITE")
    print("=" * 60)
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test 1: Name conversion
    try:
        test_name_conversion()
        print("✅ Test 1 PASSED: Name conversion working")
    except Exception as e:
        print(f"❌ Test 1 FAILED: {e}")
    
    # Test 2: Data fetching  
    try:
        if test_savant_integration():
            print("✅ Test 2 PASSED: Savant data fetching working")
        else:
            print("⚠️  Test 2 PARTIAL: Savant integration has issues")
    except Exception as e:
        print(f"❌ Test 2 FAILED: {e}")
    
    # Test 3: Full workflow
    try:
        if test_integration_workflow():
            print("✅ Test 3 PASSED: Full integration working")
        else:
            print("⚠️  Test 3 PARTIAL: Integration needs improvement")
    except Exception as e:
        print(f"❌ Test 3 FAILED: {e}")
    
    print("\n" + "=" * 60)
    print("🏁 TEST SUITE COMPLETE")
    print("\nℹ️  If any tests failed, check:")
    print("   • Internet connection")
    print("   • PyBaseball package installed: pip install pybaseball")
    print("   • File paths are correct")

if __name__ == "__main__":
    main()
