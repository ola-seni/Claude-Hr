# test_enhanced_scraper.py
import logging
import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)

# Import both versions for comparison
from rotowire_lineups import fetch_rotowire_expected_lineups as original_fetch
from enhanced_rotowire_lineups import fetch_rotowire_expected_lineups_enhanced as enhanced_fetch

def compare_scrapers():
    """Compare the original and enhanced scrapers"""
    print("=== COMPARING ROTOWIRE SCRAPERS ===\n")
    
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    
    # Teams we're specifically looking for (the missing ones)
    target_teams = ['CLE', 'LAD', 'BAL', 'STL', 'DET', 'SF', 'PHI', 'ATL']
    
    print("1. TESTING ORIGINAL SCRAPER...")
    original_lineups = original_fetch(today)
    
    print(f"\n2. TESTING ENHANCED SCRAPER...")
    enhanced_lineups = enhanced_fetch(today)
    
    print(f"\n=== RESULTS COMPARISON ===")
    print(f"Original scraper: {len(original_lineups)} games")
    print(f"Enhanced scraper: {len(enhanced_lineups)} games")
    print(f"Improvement: +{len(enhanced_lineups) - len(original_lineups)} games")
    
    # Check for target teams
    def find_target_teams(lineups, scraper_name):
        found_teams = set()
        found_games = []
        
        for game_id, data in lineups.items():
            home_team = data.get('home_team', '')
            away_team = data.get('away_team', '')
            
            for team in target_teams:
                if team in [home_team, away_team]:
                    found_teams.add(team)
                    found_games.append(f"{away_team} @ {home_team}")
        
        print(f"\n{scraper_name}:")
        print(f"  Target teams found: {sorted(found_teams)} ({len(found_teams)}/{len(target_teams)})")
        print(f"  Target games found: {len(found_games)}")
        
        for game in found_games:
            print(f"    ✅ {game}")
        
        missing_teams = set(target_teams) - found_teams
        if missing_teams:
            print(f"  Still missing: {sorted(missing_teams)}")
        
        return found_teams, found_games
    
    # Analyze results
    orig_teams, orig_games = find_target_teams(original_lineups, "ORIGINAL SCRAPER")
    enh_teams, enh_games = find_target_teams(enhanced_lineups, "ENHANCED SCRAPER")
    
    # Show improvement
    newly_found = enh_teams - orig_teams
    if newly_found:
        print(f"\n🎉 NEWLY FOUND TEAMS: {sorted(newly_found)}")
    
    newly_found_games = set(enh_games) - set(orig_games)
    if newly_found_games:
        print(f"🎉 NEWLY FOUND GAMES:")
        for game in newly_found_games:
            print(f"    ✅ {game}")
    
    # Show enhanced scraper details
    print(f"\n=== ENHANCED SCRAPER DETAILS ===")
    sources = {}
    for game_id, data in enhanced_lineups.items():
        source = data.get('source', 'unknown')
        if source not in sources:
            sources[source] = 0
        sources[source] += 1
    
    print("Games by source:")
    for source, count in sources.items():
        print(f"  {source}: {count} games")
    
    # Check if the enhancement worked
    if len(enhanced_lineups) > len(original_lineups):
        print(f"\n✅ SUCCESS: Enhanced scraper found {len(enhanced_lineups) - len(original_lineups)} additional games!")
    elif len(enh_teams) > len(orig_teams):
        print(f"\n✅ PARTIAL SUCCESS: Enhanced scraper found {len(enh_teams) - len(orig_teams)} additional target teams!")
    else:
        print(f"\n⚠️  No improvement found - may need further debugging")
    
    return enhanced_lineups

if __name__ == "__main__":
    enhanced_results = compare_scrapers()
