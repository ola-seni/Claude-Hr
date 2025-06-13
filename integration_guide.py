#!/usr/bin/env python3
"""
Integration Guide: Deploy the Unbiased MLB HR Prediction System
"""

import os
import shutil
from datetime import datetime

def backup_current_system():
    """Backup your current system before making changes"""
    print("🔄 BACKING UP CURRENT SYSTEM")
    print("=" * 40)
    
    backup_dir = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(backup_dir, exist_ok=True)
    
    files_to_backup = [
        'stats_fetcher.py',
        'mlb_hr_predictor.py',
        'predict_home_runs.py',
        'main.py'
    ]
    
    backed_up = 0
    for file in files_to_backup:
        if os.path.exists(file):
            shutil.copy(file, f"{backup_dir}/{file}")
            print(f"✅ Backed up: {file}")
            backed_up += 1
    
    print(f"📁 Backup created: {backup_dir}/ ({backed_up} files)")
    return backup_dir

def deploy_unbiased_stats():
    """Deploy the unbiased stats fetcher"""
    print("\n🔧 DEPLOYING UNBIASED STATS FETCHER")
    print("=" * 40)
    
    print("1. Save the 'Complete Bias Fix' code as 'stats_fetcher_unbiased.py'")
    print("2. Replace your current stats_fetcher.py:")
    print("   cp stats_fetcher_unbiased.py stats_fetcher.py")
    print("3. Or import the new functions in your main predictor")
    
def update_prediction_algorithm():
    """Guide to update prediction algorithm"""
    print("\n⚖️  UPDATING PREDICTION ALGORITHM")
    print("=" * 40)
    
    print("FIND YOUR PREDICTION FUNCTION:")
    print("Look for files containing HR probability calculations")
    print("Common locations:")
    print("• mlb_hr_predictor.py")
    print("• predict_home_runs.py") 
    print("• main.py")
    print()
    
    print("REPLACE YOUR PREDICTION LOGIC WITH:")
    print("1. Import: from stats_fetcher import calculate_unbiased_hr_probability")
    print("2. Replace calls to your old prediction function")
    print("3. Use the new rebalanced weights")
    print()
    
    print("KEY CHANGES NEEDED:")
    print("❌ OLD WEIGHTS (Biased):")
    print("   • Exit Velocity: 25%+")
    print("   • Barrel Rate: 20%+") 
    print("   • HR/FB Ratio: 15%+")
    print("   • ISO: 15%+")
    print("   • Batting Average: 5% or less")
    print()
    print("✅ NEW WEIGHTS (Unbiased):")
    print("   • Exit Velocity: 15%")
    print("   • Barrel Rate: 10%")
    print("   • HR/FB Ratio: 10%")
    print("   • Batting Average: 15% ← BIG INCREASE!")
    print("   • Contact Quality: 10% ← NEW!")
    print("   • Clutch Factor: 5% ← NEW!")
    print("   • ISO: 10%")
    print("   • Situational: 25%")

def test_integration():
    """Test the integrated system"""
    print("\n🧪 TESTING INTEGRATION")
    print("=" * 40)
    
    print("STEP 1: Test the unbiased stats fetcher")
    print("python3 stats_fetcher_unbiased.py")
    print("Expected: Different HR/FB ratios for different players")
    print()
    
    print("STEP 2: Test full prediction system")
    print("python3 mlb_hr_predictor.py")
    print("Expected results:")
    print("✅ Contact hitters (Arraez, Altuve) appear in recommendations")
    print("✅ Different HR/FB ratios (not all 28.0%)")
    print("✅ Wider probability ranges (e.g., 1.5% to 5.2%)")
    print("✅ Rankings change based on ballpark context")
    print()
    
    print("BIAS CHECKLIST:")
    print("□ Luis Arraez appears in small ballpark games")
    print("□ Jose Altuve ranks higher vs hard throwers") 
    print("□ Kyle Schwarber doesn't always rank #1")
    print("□ HR/FB ratios vary by player (8% to 25% range)")
    print("□ Probability ranges are wider (not 3.6% to 3.8%)")

def troubleshooting():
    """Common integration issues"""
    print("\n🔧 TROUBLESHOOTING")
    print("=" * 40)
    
    print("ISSUE: Still getting identical HR/FB ratios")
    print("FIX: Check that you're using fetch_unbiased_player_stats()")
    print("     Not the old fetch_player_stats()")
    print()
    
    print("ISSUE: Still no contact hitters in recommendations")  
    print("FIX: Make sure you're using calculate_unbiased_hr_probability()")
    print("     Check that batting average weight is 15%")
    print()
    
    print("ISSUE: Import errors")
    print("FIX: Save the complete bias fix code as stats_fetcher_unbiased.py first")
    print("     Then update your imports")
    print()
    
    print("ISSUE: Players missing from recommendations")
    print("FIX: Check minimum probability threshold")
    print("     Should be 0.008 (0.8%) not higher")

def main():
    """Complete integration guide"""
    print("🚀 COMPLETE BIAS FIX INTEGRATION GUIDE")
    print("=" * 60)
    print("This guide will help you deploy the unbiased system")
    print()
    
    # Step 1: Backup
    backup_dir = backup_current_system()
    
    # Step 2: Deploy stats
    deploy_unbiased_stats()
    
    # Step 3: Update prediction
    update_prediction_algorithm()
    
    # Step 4: Test
    test_integration()
    
    # Step 5: Troubleshooting
    troubleshooting()
    
    print(f"\n" + "=" * 60)
    print("🎯 DEPLOYMENT CHECKLIST:")
    print("□ 1. Backup created")
    print("□ 2. Save 'Complete Bias Fix' as stats_fetcher_unbiased.py")
    print("□ 3. Replace stats_fetcher.py or update imports")
    print("□ 4. Update prediction algorithm weights")
    print("□ 5. Test with: python3 mlb_hr_predictor.py") 
    print("□ 6. Verify contact hitters appear in output")
    print("□ 7. Verify HR/FB ratios vary by player")
    print()
    print(f"📁 Your backup is safe in: {backup_dir}/")
    print("🎉 Once deployed, your system will be UNBIASED!")

if __name__ == "__main__":
    main()