# debug_game_skipping.py
# Run this to see exactly why games are being skipped

import logging
from mlb_hr_predictor import MLBHomeRunPredictor

# Set up detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def debug_game_processing():
    """Debug why games are being skipped"""
    predictor = MLBHomeRunPredictor()
    
    print("=== DEBUGGING GAME SKIPPING ===\n")
    
    # Step 1: Check game fetching
    print("1. Fetching games...")
    if predictor.fetch_games():
        print(f"✓ Found {len(predictor.games)} games")
        for _, game in predictor.games.iterrows():
            print(f"  - {game['away_team']} @ {game['home_team']} ({game['game_id']})")
    else:
        print("✗ Failed to fetch games")
        return
    
    # Step 2: Check lineup fetching
    print("\n2. Fetching lineups...")
    predictor.fetch_lineups_and_pitchers()
    
    print(f"✓ Lineup data for {len(predictor.lineups)} games")
    print(f"✓ Pitcher data for {len(predictor.probable_pitchers)} games")
    
    # Step 3: Detailed analysis of each game
    print("\n3. Game-by-game analysis:")
    for _, game in predictor.games.iterrows():
        game_id = game['game_id']
        print(f"\n--- {game_id} ---")
        
        # Check lineup data
        if game_id in predictor.lineups:
            lineup = predictor.lineups[game_id]
            home_count = len(lineup.get('home', []))
            away_count = len(lineup.get('away', []))
            print(f"  Lineups: Home={home_count}, Away={away_count}")
            
            if home_count > 0:
                print(f"    Home players: {lineup['home'][:3]}..." if home_count > 3 else f"    Home players: {lineup['home']}")
            if away_count > 0:
                print(f"    Away players: {lineup['away'][:3]}..." if away_count > 3 else f"    Away players: {lineup['away']}")
        else:
            print(f"  ✗ No lineup data")
        
        # Check pitcher data
        if game_id in predictor.probable_pitchers:
            pitchers = predictor.probable_pitchers[game_id]
            print(f"  Pitchers: Home={pitchers.get('home', 'None')}, Away={pitchers.get('away', 'None')}")
        else:
            print(f"  ✗ No pitcher data")
        
        # Determine if this game would be skipped
        skip_reasons = []
        
        if game_id not in predictor.lineups:
            skip_reasons.append("No lineup data")
        else:
            lineup = predictor.lineups[game_id]
            home_count = len(lineup.get('home', []))
            away_count = len(lineup.get('away', []))
            
            if home_count == 0 and away_count == 0:
                skip_reasons.append("Empty lineups")
            
            if home_count > 15:
                skip_reasons.append("Home lineup too large (>15)")
            
            if away_count > 15:
                skip_reasons.append("Away lineup too large (>15)")
        
        if skip_reasons:
            print(f"  ⚠️  WOULD BE SKIPPED: {', '.join(skip_reasons)}")
        else:
            print(f"  ✓ Would be processed")
    
    # Step 4: Check player stats availability
    print("\n4. Checking player stats...")
    predictor.fetch_player_stats()
    
    all_players = set()
    for lineup in predictor.lineups.values():
        all_players.update(lineup.get('home', []))
        all_players.update(lineup.get('away', []))
    
    print(f"Total unique players: {len(all_players)}")
    print(f"Players with stats: {len(predictor.player_stats)}")
    
    missing_stats = all_players - set(predictor.player_stats.keys())
    if missing_stats:
        print(f"Players missing stats ({len(missing_stats)}): {list(missing_stats)[:5]}...")
    
    # Step 5: Simulate prediction run
    print("\n5. Simulating prediction run...")
    try:
        predictions = predictor.predict_home_runs()
        print(f"✓ Generated {len(predictions)} predictions")
        if len(predictions) > 0:
            print(f"Top prediction: {predictions.iloc[0]['player']} - {predictions.iloc[0]['hr_probability']:.3f}")
    except Exception as e:
        print(f"✗ Prediction failed: {e}")
    
    print("\n=== DEBUG COMPLETE ===")

if __name__ == "__main__":
    debug_game_processing()
