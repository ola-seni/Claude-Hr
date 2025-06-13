#!/usr/bin/env python3
"""
Check if the prediction model is biased toward power hitters
"""

import logging
from statistics import mean, stdev

logging.basicConfig(level=logging.INFO)

def test_prediction_bias():
    """Test if power hitters are systematically favored in predictions"""
    print("🔍 TESTING FOR POWER HITTER BIAS IN PREDICTIONS")
    print("=" * 60)
    
    # Test with clearly different player types
    contact_hitters = [
        "Luis Arraez",      # .354 AVG, elite contact
        "Jose Altuve",      # Speed, contact
        "Gleyber Torres",   # Contact over power
    ]
    
    power_hitters = [
        "Aaron Judge",      # Elite power
        "Pete Alonso",      # Pure power
        "Kyle Schwarber",   # Power, lower average
    ]
    
    balanced_hitters = [
        "Juan Soto",        # Elite all-around
        "Freddie Freeman",  # Consistent veteran
        "Mookie Betts",     # Speed/power combo
    ]
    
    print("🧪 Testing prediction bias across player types...")
    
    try:
        # Import your prediction functions
        from stats_fetcher_improved import fetch_real_player_stats
        # You'll need to import your actual prediction function here
        # from your_prediction_module import predict_home_runs  # Adjust this import
        
        # Get stats for all player types
        contact_stats, _ = fetch_real_player_stats(contact_hitters)
        power_stats, _ = fetch_real_player_stats(power_hitters)
        balanced_stats, _ = fetch_real_player_stats(balanced_hitters)
        
        print(f"\n📊 PLAYER PROFILES COMPARISON:")
        print("-" * 80)
        
        # Analyze the stat profiles
        for category, stats_dict in [("CONTACT", contact_stats), ("POWER", power_stats), ("BALANCED", balanced_stats)]:
            if stats_dict:
                avg_metrics = {
                    'avg': mean([s['avg'] for s in stats_dict.values()]),
                    'iso': mean([s['iso'] for s in stats_dict.values()]),
                    'exit_velo': mean([s['exit_velo'] for s in stats_dict.values()]),
                    'barrel_pct': mean([s['barrel_pct'] for s in stats_dict.values()]),
                    'hr_per_pa': mean([s['hr_per_pa'] for s in stats_dict.values()]),
                }
                
                print(f"\n{category} HITTERS:")
                print(f"  AVG: {avg_metrics['avg']:.3f} | ISO: {avg_metrics['iso']:.3f} | "
                      f"EV: {avg_metrics['exit_velo']:.1f} | Barrel%: {avg_metrics['barrel_pct']:.3f} | "
                      f"HR/PA: {avg_metrics['hr_per_pa']:.3f}")
        
        # Check if contact hitters are getting unfairly low power metrics
        if contact_stats and power_stats:
            contact_ev = mean([s['exit_velo'] for s in contact_stats.values()])
            power_ev = mean([s['exit_velo'] for s in power_stats.values()])
            ev_gap = power_ev - contact_ev
            
            contact_barrel = mean([s['barrel_pct'] for s in contact_stats.values()])
            power_barrel = mean([s['barrel_pct'] for s in power_stats.values()])
            barrel_gap = power_barrel - contact_barrel
            
            print(f"\n🎯 BIAS ANALYSIS:")
            print(f"Exit Velocity Gap: {ev_gap:.1f} mph")
            print(f"Barrel Rate Gap: {barrel_gap:.3f}")
            
            # Check for concerning bias patterns
            bias_flags = []
            
            if ev_gap > 5:
                bias_flags.append(f"⚠️  Large exit velocity gap: {ev_gap:.1f} mph")
            
            if barrel_gap > 0.08:
                bias_flags.append(f"⚠️  Large barrel rate gap: {barrel_gap:.3f}")
            
            # Check if contact hitters have unrealistically low power metrics
            if contact_ev < 88:
                bias_flags.append(f"⚠️  Contact hitters' exit velocity too low: {contact_ev:.1f} mph")
            
            if contact_barrel < 0.05:
                bias_flags.append(f"⚠️  Contact hitters' barrel rate too low: {contact_barrel:.3f}")
            
            if bias_flags:
                print(f"\n❌ POTENTIAL BIAS DETECTED:")
                for flag in bias_flags:
                    print(f"  {flag}")
            else:
                print(f"\n✅ No obvious bias in stat generation")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure stats_fetcher_improved.py exists")
        return False
    except Exception as e:
        print(f"❌ Error testing bias: {e}")
        return False

def analyze_prediction_weights():
    """Analyze what metrics your prediction model weights most heavily"""
    print(f"\n⚖️  ANALYZING PREDICTION MODEL WEIGHTS")
    print("=" * 60)
    
    print("To identify bias, we need to examine your prediction algorithm.")
    print("Please check these key questions:")
    print()
    print("1. 📊 Which metrics get the highest weights in your model?")
    print("   - Exit velocity")
    print("   - Barrel rate") 
    print("   - HR/FB ratio")
    print("   - ISO")
    print("   - vs. Batting average, contact rate, etc.")
    print()
    print("2. 🎯 Does your model give contact hitters credit for:")
    print("   - Higher batting averages?")
    print("   - Better plate discipline?")
    print("   - Consistent contact quality?")
    print()
    print("3. ⚡ Speed/contact players considerations:")
    print("   - Do speedy players get credit for turning singles into doubles?")
    print("   - Are line drive hitters properly valued?")
    print()
    print("4. 🏟️  Ballpark factors:")
    print("   - Are contact hitters getting fair treatment in hitter-friendly parks?")
    print("   - Do power hitters get over-weighted in small ballparks?")

def suggest_bias_fixes():
    """Suggest ways to reduce power hitter bias"""
    print(f"\n🔧 BIAS REDUCTION SUGGESTIONS")
    print("=" * 60)
    
    print("If your model is biased toward power hitters, consider:")
    print()
    print("1. 📈 Rebalance metric weights:")
    print("   - Reduce weight on exit velocity (maybe 15-20% instead of 30%+)")
    print("   - Add more weight to batting average and contact quality")
    print("   - Include plate discipline metrics (BB%, K%)")
    print()
    print("2. 🎯 Multi-factor HR prediction:")
    print("   - Contact hitters: Focus on doubles/triples that could become HRs")
    print("   - Power hitters: Focus on raw power metrics")
    print("   - Balanced players: Weight both contact and power")
    print()
    print("3. 📊 Situational adjustments:")
    print("   - Wind conditions (favor contact hitters in favorable wind)")
    print("   - Pitcher matchups (contact hitters vs hard throwers)")
    print("   - Ballpark dimensions (contact hitters in smaller parks)")
    print()
    print("4. 🔄 Dynamic weighting:")
    print("   - Recent hot streaks for contact hitters")
    print("   - Seasonal trends and adjustments")
    print("   - Opponent-specific performance")

def main():
    """Run complete bias analysis"""
    print("🚨 COMPREHENSIVE POWER HITTER BIAS ANALYSIS")
    print("=" * 80)
    
    # Test statistical bias in data generation
    test_prediction_bias()
    
    # Analyze prediction model weights
    analyze_prediction_weights()
    
    # Suggest fixes
    suggest_bias_fixes()
    
    print(f"\n" + "=" * 80)
    print("🎯 BIAS ANALYSIS COMPLETE")
    print("=" * 80)
    print("📋 Next Steps:")
    print("1. Review your prediction model's metric weights")
    print("2. Test predictions with diverse player types")
    print("3. Adjust weights if contact/speed players are undervalued")
    print("4. Monitor recommendations for balance across player types")

if __name__ == "__main__":
    main()