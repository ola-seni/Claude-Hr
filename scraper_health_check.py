# Add this to your run_predictor.py or create a separate health check

def check_scraper_health(rotowire_lineups, mlb_games_count):
    """Monitor scraper performance daily"""
    
    if not rotowire_lineups:
        logger.warning("🚨 SCRAPER ALERT: No games found by Rotowire scraper")
        return False
    
    games_found = len(rotowire_lineups)
    
    # Health checks
    if games_found < mlb_games_count * 0.7:  # Found <70% of expected games
        logger.warning(f"🚨 SCRAPER ALERT: Only found {games_found}/{mlb_games_count} games ({games_found/mlb_games_count*100:.1f}%)")
        return False
    
    # Check team diversity (should see different teams)
    teams_found = set()
    for game_data in rotowire_lineups.values():
        teams_found.add(game_data.get('home_team', ''))
        teams_found.add(game_data.get('away_team', ''))
    
    teams_found.discard('')  # Remove empty strings
    
    if len(teams_found) < 10:  # Should see at least 10 different teams on most days
        logger.warning(f"🚨 SCRAPER ALERT: Only found {len(teams_found)} unique teams")
        return False
    
    # All good!
    logger.info(f"✅ SCRAPER HEALTH: {games_found} games, {len(teams_found)} teams - Looking good!")
    return True

# Usage in your main code:
# check_scraper_health(rotowire_data, len(schedule))
