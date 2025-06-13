#!/usr/bin/env python3
"""
Run this first to diagnose why all players have the same stats
"""

import logging
import pandas as pd
from datetime import datetime, timedelta
import statsapi

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('DataDiagnostic')

def diagnose_player_stats():
    """Check what's happening with player stats fetching"""
    print("🔍 DIAGNOSING PLAYER STATS FETCHING")
    print("=" * 60)
    
    # Test with a few well-known current players
    test_players = ["Aaron Judge", "Juan Soto", "Shohei Ohtani", "Mookie Betts", "Ronald Acuna Jr."]
    
    try:
        from stats_fetcher import fetch_player_stats
        
        print(f"📊 Testing stats for: {test_players}")
        player_stats, recent_stats = fetch_player_stats(test_players)
        
        print(f"\n📈 RESULTS:")
        print(f"Players found: {len(player_stats)}/{len(test_players)}")
        
        if len(player_stats) == 0:
            print("❌ CRITICAL ISSUE: No player stats found at all!")
            return False
        
        # Check if all players have the same values (indicating defaults)
        print(f"\n🔍 CHECKING FOR DEFAULT VALUES:")
        
        key_metrics = ['exit_velo', 'barrel_pct', 'hr_fb_ratio', 'hard_hit_pct', 'xISO']
        
        for metric in key_metrics:
            values = []
            for player, stats in player_stats.items():
                if metric in stats:
                    values.append(stats[metric])
            
            if values:
                unique_values = set(values)
                print(f"  {metric}: {len(unique_values)} unique values from {len(values)} players")
                
                if len(unique_values) == 1:
                    print(f"    ❌ ALL PLAYERS HAVE SAME VALUE: {list(unique_values)[0]}")
                else:
                    print(f"    ✅ Values vary: {sorted(unique_values)[:5]}...")
        
        # Show actual player data
        print(f"\n📋 SAMPLE PLAYER DATA:")
        for i, (player, stats) in enumerate(list(player_stats.items())[:3]):
            print(f"\n{i+1}. {player}:")
            print(f"   Games: {stats.get('games', 'N/A')}")
            print(f"   HR: {stats.get('hr', 'N/A')}")
            print(f"   Exit Velo: {stats.get('exit_velo', 'N/A')}")
            print(f"   Barrel%: {stats.get('barrel_pct', 'N/A')}")
            print(f"   HR/FB: {stats.get('hr_fb_ratio', 'N/A')}")
            print(f"   xISO: {stats.get('xISO', 'N/A')}")
            print(f"   Is Simulated: {stats.get('is_simulated', 'N/A')}")
        
        return len(player_stats) > 0
        
    except Exception as e:
        print(f"❌ Error testing player stats: {e}")
        return False

def diagnose_mlb_api():
    """Test if MLB Stats API is working"""
    print("\n🏟️ DIAGNOSING MLB STATS API")
    print("=" * 60)
    
    try:
        # Test 1: Can we search for a player?
        print("Test 1: Player search...")
        search_result = statsapi.lookup_player("Aaron Judge")
        
        if search_result:
            player_id = search_result[0]['id']
            print(f"✅ Found Aaron Judge, ID: {player_id}")
            
            # Test 2: Can we get season stats?
            print("Test 2: Season stats...")
            stats_response = statsapi.player_stat_data(
                player_id, 
                group="hitting", 
                type="season", 
                sportId=1,
                season=2024  # Try 2024 first since 2025 might not be fully available
            )
            
            if 'stats' in stats_response and stats_response['stats']:
                stats = stats_response['stats'][0].get('stats', {})
                games = stats.get('gamesPlayed', 0)
                hrs = stats.get('homeRuns', 0)
                avg = stats.get('avg', 0)
                
                print(f"✅ 2024 Stats: {games} games, {hrs} HR, {avg} AVG")
                
                # Test 3: Try 2025 stats
                print("Test 3: 2025 stats...")
                stats_2025 = statsapi.player_stat_data(
                    player_id, 
                    group="hitting", 
                    type="season", 
                    sportId=1,
                    season=2025
                )
                
                if 'stats' in stats_2025 and stats_2025['stats']:
                    stats_25 = stats_2025['stats'][0].get('stats', {})
                    games_25 = stats_25.get('gamesPlayed', 0)
                    hrs_25 = stats_25.get('homeRuns', 0)
                    
                    if games_25 > 0:
                        print(f"✅ 2025 Stats: {games_25} games, {hrs_25} HR")
                        return True
                    else:
                        print(f"⚠️  2025 Stats: No games played yet")
                        return True  # API works, just no 2025 data yet
                else:
                    print(f"⚠️  2025 Stats: No data available")
                    return True  # API works, just no 2025 data
            else:
                print(f"❌ Could not get season stats")
                return False
        else:
            print(f"❌ Could not find Aaron Judge")
            return False
            
    except Exception as e:
        print(f"❌ MLB API Error: {e}")
        return False

def diagnose_savant_integration():
    """Test Baseball Savant integration"""
    print("\n⚾ DIAGNOSING BASEBALL SAVANT INTEGRATION")
    print("=" * 60)
    
    try:
        from baseball_savant import get_savant_data
        
        test_players = ["Aaron Judge", "Juan Soto"]
        test_pitchers = ["Gerrit Cole"]
        
        print(f"🔄 Testing Savant data for: {test_players}")
        
        batter_data, pitcher_data = get_savant_data(test_players, test_pitchers)
        
        print(f"📊 Savant Results:")
        print(f"  Batters found: {len(batter_data)}")
        print(f"  Pitchers found: {len(pitcher_data)}")
        
        if batter_data:
            print(f"\n✅ Sample Savant batter data:")
            for player, data in list(batter_data.items())[:2]:
                print(f"  {player}:")
                print(f"    Sample size: {data.get('sample_size', 'N/A')}")
                print(f"    Avg EV: {data.get('avg_ev', 'N/A')}")
                print(f"    Hard hit %: {data.get('hard_hit_pct', 'N/A')}")
                print(f"    Barrel %: {data.get('barrel_pct', 'N/A') if 'barrel_pct' in data else 'N/A'}")
        else:
            print(f"❌ No Savant batter data found")
        
        return len(batter_data) > 0 or len(pitcher_data) > 0
        
    except Exception as e:
        print(f"❌ Savant Error: {e}")
        return False

def main():
    """Run complete diagnostic"""
    print("🚨 DATA QUALITY DIAGNOSTIC - FINDING WHY ALL PLAYERS HAVE SAME STATS")
    print("=" * 80)
    print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = []
    
    # Test each component
    results.append(("MLB API", diagnose_mlb_api()))
    results.append(("Player Stats", diagnose_player_stats()))
    results.append(("Savant Integration", diagnose_savant_integration()))
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 DIAGNOSTIC SUMMARY")
    print("=" * 80)
    
    for test_name, passed in results:
        status = "✅ WORKING" if passed else "❌ BROKEN"
        print(f"{test_name:20} {status}")
    
    working_count = sum(1 for _, passed in results if passed)
    
    if working_count == 0:
        print("\n🚨 CRITICAL: All systems are broken!")
        print("📋 Next steps:")
        print("1. Check internet connection")
        print("2. Verify MLB API is not down")
        print("3. Check Python package versions")
        
    elif working_count <= 1:
        print("\n⚠️  MAJOR ISSUES: Multiple systems broken")
        print("📋 This explains why you're getting default values")
        print("We need to fix the data fetching first")
        
    else:
        print("\n🤔 PARTIAL ISSUES: Some systems working")
        print("📋 The problem might be in data integration/processing")
    
    print(f"\n🎯 DIAGNOSIS COMPLETE - {working_count}/3 systems working")
    
    if working_count < 3:
        print("\n📋 RECOMMENDED NEXT STEP:")
        print("Run the step-by-step fix: python step_by_step_fix.py")

if __name__ == "__main__":
    main()
