# debug_rotowire_scraping.py
# Find out why Rotowire scraper is missing games

import requests
from bs4 import BeautifulSoup
import datetime
import re

def debug_rotowire_page():
    """Download Rotowire page and analyze what games are actually there"""
    
    today = datetime.datetime.now().strftime("%m-%d-%Y")
    url = f"https://www.rotowire.com/baseball/daily-lineups.php?date={today}"
    
    print(f"=== DEBUGGING ROTOWIRE PAGE ===")
    print(f"URL: {url}")
    print(f"Today's date: {today}\n")
    
    # Download the page
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        # Save raw HTML for inspection
        with open("rotowire_debug.html", "w", encoding="utf-8") as f:
            f.write(response.text)
        print("✓ Saved raw HTML to rotowire_debug.html")
        
        # Parse with BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Strategy 1: Look for all lineup containers (current method)
        print("\n1. CURRENT SCRAPER METHOD:")
        lineup_containers = soup.find_all('div', {'class': 'lineup is-mlb'})
        print(f"Found {len(lineup_containers)} containers with 'lineup is-mlb' class")
        
        for i, container in enumerate(lineup_containers):
            try:
                teams_div = container.find('div', {'class': 'lineup__teams'})
                if teams_div:
                    away_div = teams_div.find('div', {'class': 'lineup__team is-visit'})
                    home_div = teams_div.find('div', {'class': 'lineup__team is-home'})
                    
                    if away_div and home_div:
                        away_abbr = away_div.find('div', {'class': 'lineup__abbr'})
                        home_abbr = home_div.find('div', {'class': 'lineup__abbr'})
                        
                        if away_abbr and home_abbr:
                            away_team = away_abbr.text.strip()
                            home_team = home_abbr.text.strip()
                            print(f"  Game {i+1}: {away_team} @ {home_team}")
            except Exception as e:
                print(f"  Game {i+1}: Error parsing - {e}")
        
        # Strategy 2: Look for alternative selectors
        print(f"\n2. ALTERNATIVE METHODS:")
        
        # Try different class combinations
        alt_selectors = [
            'div.lineup',
            'div[class*="lineup"]',
            'div[class*="game"]',
            'div[class*="matchup"]'
        ]
        
        for selector in alt_selectors:
            elements = soup.select(selector)
            print(f"Selector '{selector}': {len(elements)} elements")
        
        # Strategy 3: Look for team abbreviations directly
        print(f"\n3. SEARCHING FOR SPECIFIC TEAMS:")
        missing_teams = ['CLE', 'LAD', 'BAL', 'STL', 'DET', 'SF', 'PHI', 'ATL']
        
        for team in missing_teams:
            # Search for team abbreviation in the HTML
            if team in response.text:
                print(f"✓ Found '{team}' in HTML")
                
                # Find context around the team name
                lines = response.text.split('\n')
                for i, line in enumerate(lines):
                    if team in line and ('lineup' in line.lower() or 'game' in line.lower()):
                        context_start = max(0, i-2)
                        context_end = min(len(lines), i+3)
                        print(f"  Context around '{team}':")
                        for j in range(context_start, context_end):
                            print(f"    {j}: {lines[j].strip()[:100]}")
                        break
            else:
                print(f"✗ '{team}' NOT found in HTML")
        
        # Strategy 4: Look for game time patterns
        print(f"\n4. SEARCHING FOR GAME TIMES:")
        # Games usually have times like "7:05 PM" or "19:05"
        time_pattern = r'\d{1,2}:\d{2}\s*(PM|AM|ET|EST|PT|PST)?'
        times = re.findall(time_pattern, response.text, re.IGNORECASE)
        print(f"Found {len(times)} potential game times: {times[:10]}...")  # Show first 10
        
        # Strategy 5: Count total games mentioned
        print(f"\n5. GAME COUNT ANALYSIS:")
        
        # Look for patterns that might indicate games
        patterns = [
            (r'@', 'Away @ Home patterns'),
            (r'vs\.?', 'vs patterns'),  
            (r'\d{1,2}:\d{2}', 'Time patterns'),
            (r'Expected Lineup', 'Expected Lineup text'),
            (r'Confirmed Lineup', 'Confirmed Lineup text')
        ]
        
        for pattern, description in patterns:
            matches = re.findall(pattern, response.text, re.IGNORECASE)
            print(f"{description}: {len(matches)} matches")
        
        # Strategy 6: Look for JavaScript/JSON data
        print(f"\n6. LOOKING FOR JAVASCRIPT DATA:")
        
        script_tags = soup.find_all('script')
        for i, script in enumerate(script_tags):
            if script.string and ('lineup' in script.string.lower() or 'game' in script.string.lower()):
                print(f"Script {i} contains lineup/game data ({len(script.string)} chars)")
                # Show first 200 chars
                print(f"  Preview: {script.string[:200]}...")
                
                if any(team in script.string for team in missing_teams):
                    print(f"  ✓ Contains missing teams!")
                    
                    # Save this script for detailed analysis
                    with open(f"rotowire_script_{i}.js", "w") as f:
                        f.write(script.string)
                    print(f"  Saved to rotowire_script_{i}.js")
        
        print(f"\n=== SUMMARY ===")
        print(f"If you see the missing games on the website but not in our scraper,")
        print(f"the issue is likely one of these:")
        print(f"1. Games are in JavaScript/JSON data instead of HTML")
        print(f"2. Different CSS classes for some games") 
        print(f"3. Games are in a separate section of the page")
        print(f"4. The page loads content dynamically after initial load")
        print(f"\nCheck the saved files for more details:")
        print(f"- rotowire_debug.html (raw page)")
        print(f"- rotowire_script_*.js (any JS files with game data)")
        
    except Exception as e:
        print(f"✗ Error: {e}")

if __name__ == "__main__":
    debug_rotowire_page()
