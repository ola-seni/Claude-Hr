#!/usr/bin/env python3
"""
Test your actual prediction model for bias using known player archetypes
"""

import logging
from statistics import mean

logging.basicConfig(level=logging.INFO)

def test_known_player_archetypes():
    """Test prediction model with clearly defined player types"""
    print("🎯 TESTING PREDICTION MODEL WITH KNOWN PLAYER ARCHETYPES")
    print("=" * 70)
    
    # Known player archetypes with clear differences
    test_players = {
        "contact_elite": ["Luis Arraez"],  # .354 AVG, elite contact, minimal power
        "contact_speed": ["Jose Altuve"],  # Speed + contact, moderate power  
        "power_pure": ["Kyle Schwarber"],  # Pure power, poor contact (.197 AVG)
        "power_elite": ["Aaron Judge"],    # Elite power + decent contact
        "balanced": ["Juan Soto"],         # Elite all-around
    }
    
    try:
        from stats_fetcher_improved import fetch_real_player_stats
        # You'll need to import your actual prediction function
        # from your_predictor import predict_home_runs_for_game  # Adjust this
        
        print("\n📊 FETCHING STATS FOR ARCHETYPE PLAYERS:")
        print("-" * 50)
        
        all_player_stats = {}
        for archetype, players in test_players.items():
            stats, _ = fetch_real_player_stats(players)
            if stats:
                player_name = players[0]
                if player_name in stats:
                    all_player_stats[archetype] = {
                        'name': player_name,
                        'stats': stats[player_name]
                    }
                    
                    # Display key metrics
                    s = stats[player_name]
                    print(f"{archetype:12} | {player_name:15} | "
                          f"AVG: {s['avg']:.3f} | ISO: {s['iso']:.3f} | "
                          f"EV: {s['exit_velo']:4.1f} | Barrel: {s['barrel_pct']:.3f}")
        
        # Check if the stats make sense for each archetype
        print(f"\n🔍 ARCHETYPE VALIDATION:")
        print("-" * 50)
        
        issues = []
        
        if 'contact_elite' in all_player_stats and 'power_pure' in all_player_stats:
            contact_avg = all_player_stats['contact_elite']['stats']['avg']
            power_avg = all_player_stats['power_pure']['stats']['avg'] 
            
            if power_avg > contact_avg:
                issues.append(f"❌ Power hitter has higher AVG ({power_avg:.3f}) than contact hitter ({contact_avg:.3f})")
            else:
                print(f"✅ Contact hitter has higher AVG: {contact_avg:.3f} vs {power_avg:.3f}")
        
        if 'power_pure' in all_player_stats and 'contact_elite' in all_player_stats:
            power_iso = all_player_stats['power_pure']['stats']['iso']
            contact_iso = all_player_stats['contact_elite']['stats']['iso']
            
            if power_iso <= contact_iso:
                issues.append(f"❌ Power hitter doesn't have higher ISO ({power_iso:.3f}) than contact hitter ({contact_iso:.3f})")
            else:
                print(f"✅ Power hitter has higher ISO: {power_iso:.3f} vs {contact_iso:.3f}")
        
        if issues:
            print(f"\n🚨 STAT GENERATION ISSUES:")
            for issue in issues:
                print(f"  {issue}")
            print(f"  → Your algorithm may be incorrectly generating player profiles")
        
        return all_player_stats
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Need to import your actual prediction function")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_prediction_rankings(player_stats):
    """Test if your prediction model ranks players appropriately"""
    print(f"\n🏆 PREDICTION RANKING TEST")
    print("=" * 50)
    
    if not player_stats:
        print("❌ No player stats available for ranking test")
        return
    
    print("TO TEST YOUR MODEL'S BIAS:")
    print("1. Run your prediction model on these players for the same game/matchup")
    print("2. Check the HR probability rankings")
    print("3. See if contact hitters ever rank higher than expected")
    print()
    
    print("Expected realistic rankings (context-dependent):")
    print("• Elite Power (Judge) - Often highest, especially vs breaking balls")
    print("• Pure Power (Schwarber) - High vs RHP, lower vs elite pitching") 
    print("• Balanced (Soto) - Consistently high across matchups")
    print("• Contact+Speed (Altuve) - Should rank higher in small ballparks")
    print("• Elite Contact (Arraez) - Should rank higher vs hard throwers")
    print()
    
    print("🚨 RED FLAGS FOR BIAS:")
    print("• Power hitters ALWAYS rank 1-2-3 regardless of context")
    print("• Contact hitters NEVER rank in top 3")
    print("• No variation based on ballpark, pitcher, or situation")
    print("• Rankings ignore batting average and contact quality entirely")

def analyze_prediction_weights():
    """Help analyze the actual weights in the prediction model"""
    print(f"\n⚖️  PREDICTION MODEL WEIGHT ANALYSIS")
    print("=" * 50)
    
    print("EXAMINE YOUR PREDICTION ALGORITHM FOR:")
    print()
    print("1. 📊 METRIC WEIGHTS:")
    print("   What % of the prediction comes from:")
    print("   • Exit Velocity: ____%")
    print("   • Barrel Rate: ____%") 
    print("   • HR/FB Ratio: ____%")
    print("   • ISO: ____%")
    print("   • Batting Average: ____%")
    print("   • Contact Quality: ____%")
    print()
    print("2. 🚨 BIAS WARNING SIGNS:")
    print("   • Exit Velocity + Barrel Rate > 50% of total weight")
    print("   • Batting Average < 10% of total weight")
    print("   • No adjustments for player type (contact vs power)")
    print("   • Same weights used for all situations")
    print()
    print("3. ✅ BALANCED APPROACH:")
    print("   • Multiple metrics weighted appropriately")
    print("   • Contact quality factors included")
    print("   • Situational adjustments (ballpark, pitcher, weather)")
    print("   • Different weights for different player archetypes")

def suggest_specific_fixes():
    """Suggest specific fixes based on common bias patterns"""
    print(f"\n🔧 SPECIFIC BIAS FIXES")
    print("=" * 50)
    
    print("IMMEDIATE ACTIONS:")
    print()
    print("1. 🎯 TEST WITH EXTREME CASES:")
    print("   • Luis Arraez vs Kyle Schwarber in Coors Field")
    print("   • Does Arraez ever rank higher? (He should in some contexts)")
    print()
    print("2. 📉 REDUCE POWER METRIC DOMINANCE:")
    print("   • Exit Velocity: Reduce from 30% → 20%")
    print("   • Barrel Rate: Reduce from 25% → 15%")
    print("   • Add Batting Average: 15% weight")
    print("   • Add Contact Consistency: 10% weight")
    print()
    print("3. 🏟️  ADD SITUATIONAL FACTORS:")
    print("   • Small ballparks: +15% for contact hitters")
    print("   • vs Hard throwers (95+ mph): +20% for contact hitters")
    print("   • Favorable wind: +10% for contact hitters")
    print()
    print("4. 📈 DYNAMIC ADJUSTMENTS:")
    print("   • Recent hot streaks: Boost contact hitters more")
    print("   • Pitcher fatigue: Favor contact hitters late in games")
    print("   • Clutch situations: Consider batting average heavily")

def main():
    """Run comprehensive bias testing"""
    print("🚨 COMPREHENSIVE PREDICTION MODEL BIAS TEST")
    print("=" * 70)
    
    # Test with known archetypes
    player_stats = test_known_player_archetypes()
    
    # Test prediction rankings
    test_prediction_rankings(player_stats)
    
    # Analyze prediction weights
    analyze_prediction_weights()
    
    # Suggest fixes
    suggest_specific_fixes()
    
    print(f"\n" + "=" * 70)
    print("🎯 NEXT STEPS:")
    print("1. Run your actual prediction model on the archetype players")
    print("2. Check if contact hitters ever rank in top 3")
    print("3. Adjust metric weights if power dominates (>50% total weight)")
    print("4. Add situational factors that favor contact/speed players")
    print("5. Test again with balanced recommendations")

if __name__ == "__main__":
    main()