import requests
from bs4 import BeautifulSoup
import datetime
import os
import re

def debug_rotowire_html():
    """
    Download and analyze the Rotowire lineups page to understand its HTML structure.
    This will help us properly extract the lineups.
    """
    # Today's date for URL
    today = datetime.datetime.now().strftime("%m-%d-%Y")
    
    # Rotowire URL
    url = f"https://www.rotowire.com/baseball/daily-lineups.php?date={today}"
    
    print(f"Downloading Rotowire HTML from: {url}")
    
    # Make request with headers to mimic a browser
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Referer": "https://www.rotowire.com/baseball/",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }
    
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    
    # Save the HTML file
    filename = f"rotowire_debug_{today.replace('-', '_')}.html"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(response.text)
    
    print(f"Saved HTML to {filename}")
    
    # Parse the HTML to examine structure
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Find lineup containers
    lineup_containers = soup.find_all('div', class_='lineup is-mlb')
    if not lineup_containers:
        lineup_containers = soup.find_all('div', class_='lineup')
    
    print(f"\nFound {len(lineup_containers)} lineup containers")
    
    # Check first container in detail
    if lineup_containers:
        container = lineup_containers[0]
        
        # Print classes on the first container
        print(f"\nClasses on first container: {container.get('class')}")
        
        # Look for team names
        teams_div = container.find('div', class_='lineup__teams')
        if teams_div:
            print("\nFound teams div")
            away_div = teams_div.find('div', class_='lineup__team is-visit')
            home_div = teams_div.find('div', class_='lineup__team is-home')
            
            if away_div and home_div:
                away_team = away_div.find('div', class_='lineup__abbr')
                home_team = home_div.find('div', class_='lineup__abbr')
                
                if away_team and home_team:
                    print(f"Matchup: {away_team.text.strip()} @ {home_team.text.strip()}")
        
        # Try to find a player in lineup
        print("\nLooking for player links...")
        all_player_links = container.find_all('a')
        
        for i, link in enumerate(all_player_links[:10]):  # Show first 10 player links
            print(f"Player link {i}: class={link.get('class')}, text={link.text.strip()}")
        
        # Find all divs with "player" in class name
        player_divs = container.find_all(lambda tag: tag.name == 'div' and 
                                         tag.get('class') and 
                                         any('player' in c for c in tag.get('class')))
        
        print(f"\nFound {len(player_divs)} divs with 'player' in class name")
        for i, div in enumerate(player_divs[:10]):  # Show first 10 
            print(f"Player div {i}: class={div.get('class')}, text={div.text.strip()[:50]}...")
        
        # Print the full HTML of the first container to a separate file for detailed analysis
        with open(f"rotowire_container_debug_{today.replace('-', '_')}.html", "w", encoding="utf-8") as f:
            f.write(str(container))
        
        print(f"\nFull HTML of first container saved to rotowire_container_debug_{today.replace('-', '_')}.html")
        
        # Check for lineup lists
        away_list = container.find('ul', class_='lineup__list is-visit')
        home_list = container.find('ul', class_='lineup__list is-home')
        
        print("\nChecking lineup lists:")
        print(f"Away lineup list found: {away_list is not None}")
        print(f"Home lineup list found: {home_list is not None}")
        
        if away_list:
            away_items = away_list.find_all('li')
            print(f"Away lineup items: {len(away_items)}")
            for i, item in enumerate(away_items[:3]):  # Show first 3
                print(f"  Item {i}: {item.text.strip()[:50]}...")
        
        if home_list:
            home_items = home_list.find_all('li')
            print(f"Home lineup items: {len(home_items)}")
            for i, item in enumerate(home_items[:3]):  # Show first 3
                print(f"  Item {i}: {item.text.strip()[:50]}...")
        
        # Try alternative CSS selectors
        css_tests = [
            'ul.lineup__list li',
            'a.lineup__player',
            'div.lineup__player-name',
            'div.lineup__player-name a',
            'div.lineup__position-players a',
            'div.lineup__player-highlight-name',
            'span.lineup__player-name'
        ]
        
        print("\nTrying various CSS selectors:")
        for selector in css_tests:
            elements = container.select(selector)
            print(f"Selector '{selector}': {len(elements)} elements found")
            if elements:
                for i, el in enumerate(elements[:3]):  # Show first 3
                    print(f"  Element {i}: {el.text.strip()[:50]}...")

if __name__ == "__main__":
    debug_rotowire_html()
