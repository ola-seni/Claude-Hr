# test_stats_fix.py
from stats_fetcher import fetch_player_stats, fetch_pitcher_stats

# Test with a few known players
test_players = ["Aaron Judge", "Shohei Ohtani", "Juan Soto"]
test_pitchers = ["Corbin Burnes", "Tyler Anderson"]

print("Testing player stats fetch...")
player_stats = fetch_player_stats(test_players)
print(f"Found stats for {len(player_stats)} players: {list(player_stats.keys())}")

print("\nTesting pitcher stats fetch...")
pitcher_stats = fetch_pitcher_stats(test_pitchers)
print(f"Found stats for {len(pitcher_stats)} pitchers: {list(pitcher_stats.keys())}")
