def check_data_quality(predictor):
    """Generate a data quality report"""
    print("\n=== DATA QUALITY REPORT ===\n")
    
    # Games coverage
    total_games = len(predictor.games)
    games_with_lineups = sum(1 for g in predictor.lineups if predictor.lineups[g]['home'] or predictor.lineups[g]['away'])
    games_with_pitchers = sum(1 for g in predictor.probable_pitchers if predictor.probable_pitchers[g]['home'] != 'TBD')
    
    print(f"Games Coverage:")
    print(f"  Total games: {total_games}")
    print(f"  With lineups: {games_with_lineups} ({games_with_lineups/total_games*100:.1f}%)")
    print(f"  With pitchers: {games_with_pitchers} ({games_with_pitchers/total_games*100:.1f}%)")
    
    # Player stats quality
    all_players = set()
    for lineup in predictor.lineups.values():
        all_players.update(lineup.get('home', []))
        all_players.update(lineup.get('away', []))
    
    real_stats = sum(1 for p in all_players if p in predictor.player_stats and not predictor.player_stats[p].get('is_simulated', False))
    
    print(f"\nPlayer Stats Quality:")
    print(f"  Total players: {len(all_players)}")
    print(f"  With real stats: {real_stats} ({real_stats/len(all_players)*100:.1f}%)")
    
    # Handedness data
    players_with_handedness = sum(1 for p in predictor.player_stats.values() if p.get('bats') != 'Unknown')
    pitchers_with_handedness = sum(1 for p in predictor.pitcher_stats.values() if p.get('throws') != 'Unknown')
    
    print(f"\nHandedness Data:")
    print(f"  Batters with known handedness: {players_with_handedness}/{len(predictor.player_stats)} ({players_with_handedness/len(predictor.player_stats)*100:.1f}%)")
    print(f"  Pitchers with known handedness: {pitchers_with_handedness}/{len(predictor.pitcher_stats)} ({pitchers_with_handedness/len(predictor.pitcher_stats)*100:.1f}%)")
    
    return games_with_lineups / total_games > 0.7  # Return True if data quality is acceptable
