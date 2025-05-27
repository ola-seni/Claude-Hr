# run_backtest.py
import logging
import sys
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from backtesting_framework import MLBBacktester, run_backtest
import json
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('backtest.log')
    ]
)

logger = logging.getLogger('BacktestRunner')

def quick_backtest():
    """Run a quick backtest for demonstration"""
    print("🚀 RUNNING QUICK BACKTEST DEMO")
    print("=" * 50)
    
    # Test with recent dates
    backtester = run_backtest(
        start_date="2024-06-01", 
        end_date="2024-06-30", 
        sample_days=5  # Just 5 days for demo
    )
    
    return backtester

def full_season_backtest():
    """Run comprehensive backtesting on full season"""
    print("🚀 RUNNING FULL SEASON BACKTEST")
    print("=" * 50)
    
    # Full 2024 season backtest
    backtester = MLBBacktester("2024-04-01", "2024-09-30")
    report = backtester.run_full_backtest(
        sample_days=50,  # Sample 50 days for reasonable runtime
        optimize_weights=True
    )
    
    print(report)
    
    # Generate visualizations
    create_backtest_visualizations(backtester)
    
    return backtester

def create_backtest_visualizations(backtester):
    """Create visualizations of backtest results"""
    if not backtester.backtest_results:
        logger.warning("No results to visualize")
        return
    
    # Set up the plotting style
    plt.style.use('seaborn-v0_8')
    sns.set_palette("husl")
    
    # Create results directory
    viz_dir = 'backtest_visualizations'
    os.makedirs(viz_dir, exist_ok=True)
    
    df = pd.DataFrame(backtester.backtest_results)
    
    # 1. Calibration Plot
    create_calibration_plot(backtester.performance_metrics.get('calibration', []), viz_dir)
    
    # 2. Factor Importance Plot
    create_factor_importance_plot(backtester.factor_importance, viz_dir)
    
    # 3. Prediction Distribution
    create_prediction_distribution_plot(df, viz_dir)
    
    # 4. Performance by Category
    create_category_performance_plot(backtester.performance_metrics.get('category_performance', {}), viz_dir)
    
    # 5. Probability vs Actual Rate
    create_probability_bins_plot(backtester.performance_metrics.get('bin_performance', []), viz_dir)
    
    logger.info(f"📊 Visualizations saved to {viz_dir}/")

def create_calibration_plot(calibration_data, viz_dir):
    """Create calibration plot showing predicted vs actual rates"""
    if not calibration_data:
        return
    
    fig, ax = plt.subplots(figsize=(10, 8))
    
    df_cal = pd.DataFrame(calibration_data)
    
    # Plot perfect calibration line
    ax.plot([0, 0.2], [0, 0.2], 'k--', alpha=0.7, label='Perfect Calibration')
    
    # Plot actual calibration
    ax.scatter(df_cal['predicted_rate'], df_cal['actual_rate'], 
               s=df_cal['count']*2, alpha=0.7, color='blue', label='Model Calibration')
    
    ax.set_xlabel('Predicted HR Probability')
    ax.set_ylabel('Actual HR Rate')
    ax.set_title('Model Calibration: Predicted vs Actual HR Rates')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f'{viz_dir}/calibration_plot.png', dpi=300, bbox_inches='tight')
    plt.close()

def create_factor_importance_plot(factor_importance, viz_dir):
    """Create factor importance visualization"""
    if not factor_importance:
        return
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
    
    # Top 10 factors by predictive power
    top_factors = list(factor_importance.items())[:10]
    factors = [f[0] for f in top_factors]
    powers = [abs(f[1]['predictive_power']) for f in top_factors]
    weights = [f[1]['current_weight'] for f in top_factors]
    
    # Predictive Power plot
    bars1 = ax1.barh(factors, powers, color='steelblue', alpha=0.7)
    ax1.set_xlabel('Predictive Power (HR Rate Difference)')
    ax1.set_title('Top Factors by Predictive Power')
    ax1.grid(True, alpha=0.3)
    
    # Add value labels
    for i, bar in enumerate(bars1):
        width = bar.get_width()
        ax1.text(width + 0.001, bar.get_y() + bar.get_height()/2, 
                f'{powers[i]:.3f}', ha='left', va='center', fontsize=9)
    
    # Current Weights plot
    bars2 = ax2.barh(factors, weights, color='orange', alpha=0.7)
    ax2.set_xlabel('Current Weight in Model')
    ax2.set_title('Current Factor Weights')
    ax2.grid(True, alpha=0.3)
    
    # Add value labels
    for i, bar in enumerate(bars2):
        width = bar.get_width()
        ax2.text(width + 0.002, bar.get_y() + bar.get_height()/2, 
                f'{weights[i]:.3f}', ha='left', va='center', fontsize=9)
    
    plt.tight_layout()
    plt.savefig(f'{viz_dir}/factor_importance.png', dpi=300, bbox_inches='tight')
    plt.close()

def create_prediction_distribution_plot(df, viz_dir):
    """Create prediction distribution plots"""
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
    
    # 1. Histogram of predicted probabilities
    ax1.hist(df['predicted_prob'], bins=50, alpha=0.7, color='skyblue', edgecolor='black')
    ax1.set_xlabel('Predicted HR Probability')
    ax1.set_ylabel('Number of Predictions')
    ax1.set_title('Distribution of Predicted Probabilities')
    ax1.grid(True, alpha=0.3)
    
    # 2. Predicted vs Actual (scatter)
    ax2.scatter(df['predicted_prob'], df['hit_hr'], alpha=0.3)
    ax2.set_xlabel('Predicted HR Probability')
    ax2.set_ylabel('Actually Hit HR (0/1)')
    ax2.set_title('Predicted Probability vs Actual Outcome')
    ax2.grid(True, alpha=0.3)
    
    # 3. HR vs No HR distributions
    hr_yes = df[df['hit_hr'] == 1]['predicted_prob']
    hr_no = df[df['hit_hr'] == 0]['predicted_prob']
    
    ax3.hist(hr_no, bins=30, alpha=0.7, label='No HR', color='lightcoral')
    ax3.hist(hr_yes, bins=30, alpha=0.7, label='Hit HR', color='lightgreen')
    ax3.set_xlabel('Predicted HR Probability')
    ax3.set_ylabel('Count')
    ax3.set_title('Probability Distribution by Actual Outcome')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # 4. ROC-like curve (predicted probability vs hit rate)
    thresholds = np.arange(0, 0.15, 0.005)
    hit_rates = []
    counts = []
    
    for threshold in thresholds:
        above_threshold = df[df['predicted_prob'] >= threshold]
        if len(above_threshold) > 0:
            hit_rate = above_threshold['hit_hr'].mean()
            count = len(above_threshold)
        else:
            hit_rate = 0
            count = 0
        hit_rates.append(hit_rate)
        counts.append(count)
    
    ax4.plot(thresholds, hit_rates, 'o-', color='purple')
    ax4.set_xlabel('Probability Threshold')
    ax4.set_ylabel('Actual HR Rate Above Threshold')
    ax4.set_title('HR Rate vs Probability Threshold')
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f'{viz_dir}/prediction_distributions.png', dpi=300, bbox_inches='tight')
    plt.close()

def create_category_performance_plot(category_performance, viz_dir):
    """Create category performance visualization"""
    if not category_performance:
        return
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    categories = list(category_performance.keys())
    predicted_rates = [category_performance[cat]['predicted_rate'] * 100 for cat in categories]
    actual_rates = [category_performance[cat]['actual_rate'] * 100 for cat in categories]
    counts = [category_performance[cat]['count'] for cat in categories]
    
    # Predicted vs Actual rates
    x = np.arange(len(categories))
    width = 0.35
    
    bars1 = ax1.bar(x - width/2, predicted_rates, width, label='Predicted Rate', alpha=0.8, color='steelblue')
    bars2 = ax1.bar(x + width/2, actual_rates, width, label='Actual Rate', alpha=0.8, color='orange')
    
    ax1.set_xlabel('Category')
    ax1.set_ylabel('HR Rate (%)')
    ax1.set_title('Predicted vs Actual HR Rates by Category')
    ax1.set_xticks(x)
    ax1.set_xticklabels([cat.title() for cat in categories])
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Add value labels
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                    f'{height:.1f}%', ha='center', va='bottom', fontsize=9)
    
    # Sample sizes
    bars3 = ax2.bar(categories, counts, color='green', alpha=0.7)
    ax2.set_xlabel('Category')
    ax2.set_ylabel('Number of Predictions')
    ax2.set_title('Sample Size by Category')
    ax2.grid(True, alpha=0.3)
    
    # Add value labels
    for bar in bars3:
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height + max(counts)*0.01,
                f'{int(height)}', ha='center', va='bottom', fontsize=10)
    
    plt.tight_layout()
    plt.savefig(f'{viz_dir}/category_performance.png', dpi=300, bbox_inches='tight')
    plt.close()

def create_probability_bins_plot(bin_performance, viz_dir):
    """Create probability bins performance plot"""
    if not bin_performance:
        return
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    ranges = [bp['range'] for bp in bin_performance]
    predicted = [bp['predicted_rate'] * 100 for bp in bin_performance]
    actual = [bp['actual_rate'] * 100 for bp in bin_performance]
    counts = [bp['count'] for bp in bin_performance]
    
    # Predicted vs Actual by bin
    x = np.arange(len(ranges))
    width = 0.35
    
    ax1.bar(x - width/2, predicted, width, label='Predicted', alpha=0.8, color='skyblue')
    ax1.bar(x + width/2, actual, width, label='Actual', alpha=0.8, color='salmon')
    
    ax1.set_xlabel('Probability Range')
    ax1.set_ylabel('HR Rate (%)')
    ax1.set_title('HR Rates by Probability Bin')
    ax1.set_xticks(x)
    ax1.set_xticklabels(ranges, rotation=45)
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Sample sizes by bin
    ax2.bar(ranges, counts, color='lightgreen', alpha=0.7)
    ax2.set_xlabel('Probability Range')
    ax2.set_ylabel('Number of Predictions')
    ax2.set_title('Sample Size by Probability Bin')
    ax2.tick_params(axis='x', rotation=45)
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f'{viz_dir}/probability_bins.png', dpi=300, bbox_inches='tight')
    plt.close()

def analyze_existing_predictions():
    """Analyze your existing prediction_tracking.json file"""
    tracking_file = "prediction_tracking.json"
    
    if not os.path.exists(tracking_file):
        logger.warning(f"No existing {tracking_file} found")
        return
    
    print("📊 ANALYZING EXISTING PREDICTION HISTORY")
    print("=" * 50)
    
    try:
        with open(tracking_file, 'r') as f:
            tracking_data = json.load(f)
        
        predictions = tracking_data.get('predictions', {})
        
        if not predictions:
            print("No historical predictions found in tracking file")
            return
        
        # Analyze existing predictions
        total_days = len(predictions)
        total_predictions = 0
        total_correct = 0
        category_stats = {'locks': {'total': 0, 'correct': 0}, 
                         'hot_picks': {'total': 0, 'correct': 0}, 
                         'sleepers': {'total': 0, 'correct': 0}}
        
        for date, day_data in predictions.items():
            if not day_data.get('verified', False):
                continue
                
            for category in ['locks', 'hot_picks', 'sleepers']:
                for pred in day_data.get(category, []):
                    total_predictions += 1
                    category_stats[category]['total'] += 1
                    
                    if pred.get('hit_hr', False):
                        total_correct += 1
                        category_stats[category]['correct'] += 1
        
        # Print results
        print(f"📅 Days with predictions: {total_days}")
        print(f"📊 Total predictions: {total_predictions}")
        print(f"✅ Overall accuracy: {total_correct/total_predictions*100:.1f}%" if total_predictions > 0 else "N/A")
        
        print(f"\n📂 Category Performance:")
        for category, stats in category_stats.items():
            if stats['total'] > 0:
                accuracy = stats['correct'] / stats['total'] * 100
                print(f"  {category.title()}: {accuracy:.1f}% ({stats['correct']}/{stats['total']})")
        
    except Exception as e:
        logger.error(f"Error analyzing existing predictions: {e}")

def main():
    """Main runner function"""
    print("🎯 MLB HR PREDICTION BACKTESTING SYSTEM")
    print("=" * 50)
    
    # First analyze existing tracking
    analyze_existing_predictions()
    
    print("\nChoose an option:")
    print("1. Quick Demo (5 days)")
    print("2. Full Season Backtest (50 days)")
    print("3. Custom Backtest")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == "1":
        backtester = quick_backtest()
    elif choice == "2":
        backtester = full_season_backtest()
    elif choice == "3":
        start_date = input("Start date (YYYY-MM-DD): ").strip()
        end_date = input("End date (YYYY-MM-DD): ").strip()
        sample_days = int(input("Number of days to sample: ").strip())
        
        backtester = run_backtest(start_date, end_date, sample_days)
        create_backtest_visualizations(backtester)
    else:
        print("Invalid choice")
        return
    
    print("\n✅ Backtesting complete!")
    print("Check the 'backtest_cache' directory for detailed results")
    print("Check the 'backtest_visualizations' directory for charts")

if __name__ == "__main__":
    main()
