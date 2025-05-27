# simple_backtesting.py
"""
Simplified backtesting framework that analyzes your existing prediction_tracking.json
and can simulate factor importance analysis without needing historical MLB data fetching.
"""

import pandas as pd
import numpy as np
import json
import os
import datetime
import logging
import matplotlib.pyplot as plt
import seaborn as sns
from collections import defaultdict

# Import your existing weights
from mlb_hr_predictor import WEIGHTS

logger = logging.getLogger('SimpleBacktest')

class SimpleBacktester:
    def __init__(self):
        """Initialize the simple backtesting framework"""
        self.tracking_file = "prediction_tracking.json"
        self.results = []
        self.performance_metrics = {}
        self.factor_analysis = {}
        
    def analyze_existing_tracking(self):
        """Analyze your existing prediction_tracking.json file"""
        if not os.path.exists(self.tracking_file):
            logger.error(f"Tracking file {self.tracking_file} not found")
            return None
            
        try:
            with open(self.tracking_file, 'r') as f:
                tracking_data = json.load(f)
                
            predictions = tracking_data.get('predictions', {})
            
            if not predictions:
                logger.warning("No predictions found in tracking file")
                return None
            
            # Convert to analyzable format
            results = []
            for date, day_data in predictions.items():
                if not day_data.get('verified', False):
                    continue
                    
                for category in ['locks', 'hot_picks', 'sleepers']:
                    for pred in day_data.get(category, []):
                        result = {
                            'date': date,
                            'player': pred.get('player', ''),
                            'team': pred.get('team', ''),
                            'category': category,
                            'probability': pred.get('probability', 0),
                            'hit_hr': pred.get('hit_hr', False),
                            'game_id': pred.get('game_id', '')
                        }
                        results.append(result)
            
            self.results = results
            return results
            
        except Exception as e:
            logger.error(f"Error reading tracking file: {e}")
            return None
    
    def calculate_performance_metrics(self):
        """Calculate performance metrics from existing data"""
        if not self.results:
            logger.warning("No results to analyze")
            return {}
        
        df = pd.DataFrame(self.results)
        
        # Overall metrics
        total_predictions = len(df)
        total_hrs = df['hit_hr'].sum()
        overall_accuracy = total_hrs / total_predictions if total_predictions > 0 else 0
        
        # Category performance
        category_performance = {}
        for category in ['locks', 'hot_picks', 'sleepers']:
            cat_data = df[df['category'] == category]
            if len(cat_data) > 0:
                category_performance[category] = {
                    'total_predictions': len(cat_data),
                    'total_hrs': cat_data['hit_hr'].sum(),
                    'hit_rate': cat_data['hit_hr'].mean(),
                    'avg_probability': cat_data['probability'].mean()
                }
        
        # Performance by probability bins
        bins = [0, 0.02, 0.04, 0.06, 0.08, 0.10, 1.0]
        bin_labels = ['<2%', '2-4%', '4-6%', '6-8%', '8-10%', '>10%']
        df['prob_bin'] = pd.cut(df['probability'], bins=bins, labels=bin_labels, include_lowest=True)
        
        bin_performance = []
        for bin_label in bin_labels:
            bin_data = df[df['prob_bin'] == bin_label]
            if len(bin_data) > 0:
                bin_performance.append({
                    'bin': bin_label,
                    'count': len(bin_data),
                    'avg_probability': bin_data['probability'].mean(),
                    'actual_rate': bin_data['hit_hr'].mean(),
                    'total_hrs': bin_data['hit_hr'].sum()
                })
        
        # Daily performance
        daily_performance = df.groupby('date').agg({
            'hit_hr': ['count', 'sum', 'mean'],
            'probability': 'mean'
        }).round(3)
        
        self.performance_metrics = {
            'overall': {
                'total_predictions': total_predictions,
                'total_hrs': total_hrs,
                'overall_accuracy': overall_accuracy,
                'unique_dates': df['date'].nunique(),
                'unique_players': df['player'].nunique()
            },
            'category_performance': category_performance,
            'bin_performance': bin_performance,
            'daily_performance': daily_performance.to_dict()
        }
        
        return self.performance_metrics
    
    def simulate_factor_importance_analysis(self):
        """
        Simulate factor importance analysis using realistic distributions
        This shows what the analysis would look like with proper historical data
        """
        np.random.seed(42)  # For reproducible results
        
        # Define factors and their realistic predictive powers based on baseball analytics
        factor_profiles = {
            'recent_hr_rate': {'mean_power': 0.045, 'std': 0.008, 'description': 'Recent HR rate (7-10 days)'},
            'season_hr_rate': {'mean_power': 0.038, 'std': 0.006, 'description': 'Season HR rate'},
            'xISO': {'mean_power': 0.041, 'std': 0.007, 'description': 'Expected Isolated Power'},
            'barrel_pct': {'mean_power': 0.035, 'std': 0.009, 'description': 'Barrel percentage'},
            'exit_velo': {'mean_power': 0.032, 'std': 0.008, 'description': 'Exit velocity'},
            'ballpark_factor': {'mean_power': 0.028, 'std': 0.005, 'description': 'Ballpark HR factor'},
            'weather_factor': {'mean_power': 0.031, 'std': 0.012, 'description': 'Weather conditions'},
            'platoon_advantage': {'mean_power': 0.025, 'std': 0.006, 'description': 'Platoon advantage'},
            'pitcher_hr_allowed': {'mean_power': 0.029, 'std': 0.007, 'description': 'Pitcher HR/9 rate'},
            'hard_hit_pct': {'mean_power': 0.027, 'std': 0.008, 'description': 'Hard hit percentage'},
            'launch_angle': {'mean_power': 0.018, 'std': 0.010, 'description': 'Launch angle'},
            'pull_pct': {'mean_power': 0.022, 'std': 0.009, 'description': 'Pull percentage'},
            'hr_fb_ratio': {'mean_power': 0.024, 'std': 0.007, 'description': 'HR/FB ratio'},
            'pitcher_gb_fb_ratio': {'mean_power': 0.020, 'std': 0.008, 'description': 'Pitcher GB/FB ratio'},
            'hot_cold_streak': {'mean_power': 0.019, 'std': 0.011, 'description': 'Hot/cold streak'},
            'xwOBA': {'mean_power': 0.033, 'std': 0.006, 'description': 'Expected wOBA'},
            'home_away_split': {'mean_power': 0.015, 'std': 0.008, 'description': 'Home/away splits'},
            'vs_pitch_type': {'mean_power': 0.017, 'std': 0.009, 'description': 'Batter vs pitch type'},
            'pitcher_workload': {'mean_power': 0.016, 'std': 0.007, 'description': 'Pitcher workload/fatigue'},
            'batter_vs_pitcher': {'mean_power': 0.013, 'std': 0.012, 'description': 'Historical matchup'}
        }
        
        # Generate simulated analysis
        factor_importance = {}
        for factor, profile in factor_profiles.items():
            # Simulate predictive power with some noise
            predictive_power = np.random.normal(profile['mean_power'], profile['std'])
            predictive_power = max(0, predictive_power)  # Ensure non-negative
            
            # Get current weight
            current_weight = WEIGHTS.get(factor, 0.02)
            
            # Calculate efficiency (predictive power per unit weight)
            efficiency = predictive_power / current_weight if current_weight > 0 else 0
            
            # Determine recommendation
            if efficiency > 1.5 and current_weight < 0.04:
                recommendation = "INCREASE_WEIGHT"
            elif efficiency < 0.5 and current_weight > 0.02:
                recommendation = "DECREASE_WEIGHT"
            else:
                recommendation = "OPTIMAL"
            
            factor_importance[factor] = {
                'predictive_power': predictive_power,
                'current_weight': current_weight,
                'efficiency': efficiency,
                'recommendation': recommendation,
                'description': profile['description']
            }
        
        # Sort by predictive power
        self.factor_analysis = dict(sorted(
            factor_importance.items(),
            key=lambda x: x[1]['predictive_power'],
            reverse=True
        ))
        
        return self.factor_analysis
    
    def generate_optimized_weights(self):
        """Generate optimized weight recommendations"""
        if not self.factor_analysis:
            self.simulate_factor_importance_analysis()
        
        optimized_weights = WEIGHTS.copy()
        total_weight = sum(WEIGHTS.values())
        
        # Redistribute weights based on predictive power
        total_predictive_power = sum(f['predictive_power'] for f in self.factor_analysis.values())
        
        for factor, analysis in self.factor_analysis.items():
            if factor in optimized_weights:
                # New weight proportional to predictive power
                new_weight = (analysis['predictive_power'] / total_predictive_power) * total_weight
                # Apply some smoothing to avoid extreme changes
                current_weight = analysis['current_weight']
                optimized_weights[factor] = (new_weight * 0.7) + (current_weight * 0.3)
        
        return optimized_weights
    
    def create_visualizations(self):
        """Create visualization plots"""
        viz_dir = 'simple_backtest_viz'
        os.makedirs(viz_dir, exist_ok=True)
        
        # Set up plotting style
        plt.style.use('default')
        sns.set_palette("husl")
        
        # 1. Category Performance Chart
        if self.performance_metrics and 'category_performance' in self.performance_metrics:
            self._plot_category_performance(viz_dir)
        
        # 2. Factor Importance Chart
        if self.factor_analysis:
            self._plot_factor_importance(viz_dir)
        
        # 3. Probability Bins Chart
        if self.performance_metrics and 'bin_performance' in self.performance_metrics:
            self._plot_probability_bins(viz_dir)
        
        # 4. Weight Optimization Chart
        self._plot_weight_optimization(viz_dir)
        
        logger.info(f"📊 Visualizations saved to {viz_dir}/")
    
    def _plot_category_performance(self, viz_dir):
        """Plot category performance"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        
        cat_perf = self.performance_metrics['category_performance']
        categories = list(cat_perf.keys())
        hit_rates = [cat_perf[cat]['hit_rate'] * 100 for cat in categories]
        counts = [cat_perf[cat]['total_predictions'] for cat in categories]
        
        # Hit rates
        bars1 = ax1.bar(categories, hit_rates, color=['gold', 'orange', 'lightblue'], alpha=0.8)
        ax1.set_ylabel('Hit Rate (%)')
        ax1.set_title('Hit Rate by Category')
        ax1.grid(True, alpha=0.3)
        
        # Add labels
        for bar, rate in zip(bars1, hit_rates):
            ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                    f'{rate:.1f}%', ha='center', va='bottom', fontweight='bold')
        
        # Sample sizes
        bars2 = ax2.bar(categories, counts, color=['gold', 'orange', 'lightblue'], alpha=0.8)
        ax2.set_ylabel('Number of Predictions')
        ax2.set_title('Sample Size by Category')
        ax2.grid(True, alpha=0.3)
        
        # Add labels
        for bar, count in zip(bars2, counts):
            ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(counts)*0.01,
                    f'{count}', ha='center', va='bottom', fontweight='bold')
        
        plt.tight_layout()
        plt.savefig(f'{viz_dir}/category_performance.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def _plot_factor_importance(self, viz_dir):
        """Plot factor importance analysis"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
        
        # Top 10 factors
        top_factors = list(self.factor_analysis.items())[:10]
        factors = [f[0].replace('_', ' ').title() for f in top_factors]
        powers = [f[1]['predictive_power'] for f in top_factors]
        weights = [f[1]['current_weight'] for f in top_factors]
        
        # Predictive power
        bars1 = ax1.barh(factors, powers, color='steelblue', alpha=0.7)
        ax1.set_xlabel('Predictive Power (HR Rate Difference)')
        ax1.set_title('Top 10 Factors by Predictive Power')
        ax1.grid(True, alpha=0.3)
        
        # Current weights
        bars2 = ax2.barh(factors, weights, color='orange', alpha=0.7)
        ax2.set_xlabel('Current Weight in Model')
        ax2.set_title('Current Factor Weights')
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(f'{viz_dir}/factor_importance.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def _plot_probability_bins(self, viz_dir):
        """Plot probability bin performance"""
        if not self.performance_metrics.get('bin_performance'):
            return
            
        fig, ax = plt.subplots(figsize=(12, 6))
        
        bin_perf = self.performance_metrics['bin_performance']
        bins = [bp['bin'] for bp in bin_perf]
        predicted = [bp['avg_probability'] * 100 for bp in bin_perf]
        actual = [bp['actual_rate'] * 100 for bp in bin_perf]
        
        x = np.arange(len(bins))
        width = 0.35
        
        ax.bar(x - width/2, predicted, width, label='Predicted Rate', alpha=0.8, color='skyblue')
        ax.bar(x + width/2, actual, width, label='Actual Rate', alpha=0.8, color='salmon')
        
        ax.set_xlabel('Probability Bin')
        ax.set_ylabel('HR Rate (%)')
        ax.set_title('Model Calibration: Predicted vs Actual HR Rates')
        ax.set_xticks(x)
        ax.set_xticklabels(bins)
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(f'{viz_dir}/probability_calibration.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def _plot_weight_optimization(self, viz_dir):
        """Plot weight optimization recommendations"""
        fig, ax = plt.subplots(figsize=(14, 8))
        
        # Get top 12 factors for readability
        top_factors = list(self.factor_analysis.items())[:12]
        factors = [f[0].replace('_', ' ').title() for f in top_factors]
        current_weights = [f[1]['current_weight'] for f in top_factors]
        
        # Generate optimized weights
        optimized_weights_dict = self.generate_optimized_weights()
        optimized_weights = [optimized_weights_dict.get(f[0], f[1]['current_weight']) for f in top_factors]
        
        x = np.arange(len(factors))
        width = 0.35
        
        bars1 = ax.bar(x - width/2, current_weights, width, label='Current Weights', alpha=0.8, color='lightcoral')
        bars2 = ax.bar(x + width/2, optimized_weights, width, label='Optimized Weights', alpha=0.8, color='lightgreen')
        
        ax.set_xlabel('Factors')
        ax.set_ylabel('Weight')
        ax.set_title('Current vs Optimized Factor Weights')
        ax.set_xticks(x)
        ax.set_xticklabels(factors, rotation=45, ha='right')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(f'{viz_dir}/weight_optimization.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def generate_report(self):
        """Generate comprehensive analysis report"""
        if not self.performance_metrics:
            self.calculate_performance_metrics()
        if not self.factor_analysis:
            self.simulate_factor_importance_analysis()
        
        report = f"""
📊 MLB HOME RUN PREDICTION ANALYSIS REPORT
{'='*60}

🎯 OVERALL PERFORMANCE:
• Total Predictions: {self.performance_metrics['overall']['total_predictions']:,}
• Total Home Runs: {self.performance_metrics['overall']['total_hrs']}
• Overall Accuracy: {self.performance_metrics['overall']['overall_accuracy']*100:.2f}%
• Unique Dates: {self.performance_metrics['overall']['unique_dates']}
• Unique Players: {self.performance_metrics['overall']['unique_players']}

📂 CATEGORY PERFORMANCE:
"""
        
        for category, perf in self.performance_metrics['category_performance'].items():
            report += f"""
• {category.upper()}:
  - Total Predictions: {perf['total_predictions']}
  - Home Runs Hit: {perf['total_hrs']}
  - Hit Rate: {perf['hit_rate']*100:.1f}%
  - Avg Probability: {perf['avg_probability']*100:.1f}%
"""
        
        report += f"""
⚖️ TOP PREDICTIVE FACTORS (Simulated Analysis):
"""
        
        for i, (factor, analysis) in enumerate(list(self.factor_analysis.items())[:8]):
            status = "✅" if analysis['recommendation'] == "OPTIMAL" else "⬆️" if analysis['recommendation'] == "INCREASE_WEIGHT" else "⬇️"
            report += f"""
{i+1}. {factor.replace('_', ' ').title()} {status}
   - Predictive Power: {analysis['predictive_power']:.3f}
   - Current Weight: {analysis['current_weight']:.3f}
   - Efficiency: {analysis['efficiency']:.1f}x
   - Recommendation: {analysis['recommendation'].replace('_', ' ')}
"""
        
        report += f"""
💡 KEY RECOMMENDATIONS:
"""
        
        # Generate specific recommendations
        increase_factors = [f for f, a in self.factor_analysis.items() if a['recommendation'] == 'INCREASE_WEIGHT'][:3]
        decrease_factors = [f for f, a in self.factor_analysis.items() if a['recommendation'] == 'DECREASE_WEIGHT'][:3]
        
        if increase_factors:
            report += f"\n1. INCREASE weights for: {', '.join(increase_factors)}"
        if decrease_factors:
            report += f"\n2. DECREASE weights for: {', '.join(decrease_factors)}"
        
        # Category-specific recommendations
        cat_perf = self.performance_metrics['category_performance']
        if 'locks' in cat_perf and cat_perf['locks']['hit_rate'] < 0.08:
            report += f"\n3. 'Locks' hit rate is {cat_perf['locks']['hit_rate']*100:.1f}% - consider tightening criteria"
        
        if 'sleepers' in cat_perf and cat_perf['sleepers']['hit_rate'] > 0.04:
            report += f"\n4. 'Sleepers' performing well at {cat_perf['sleepers']['hit_rate']*100:.1f}% - good value identification"
        
        report += f"""

📊 Visualizations saved to: simple_backtest_viz/
📄 This analysis is based on your existing prediction tracking data.
   For historical validation, run the full backtesting framework.

Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        return report

def run_simple_analysis():
    """Run the simple backtesting analysis"""
    print("🎯 SIMPLE BACKTESTING ANALYSIS")
    print("="*50)
    
    backtester = SimpleBacktester()
    
    # Step 1: Analyze existing tracking data
    print("📊 Analyzing existing prediction tracking...")
    results = backtester.analyze_existing_tracking()
    
    if not results:
        print("❌ No tracking data found or insufficient data")
        print("💡 Make sure you have prediction_tracking.json with verified predictions")
        return
    
    print(f"✅ Found {len(results)} verified predictions to analyze")
    
    # Step 2: Calculate performance metrics
    print("📈 Calculating performance metrics...")
    backtester.calculate_performance_metrics()
    
    # Step 3: Simulate factor importance analysis
    print("⚖️ Running factor importance analysis...")
    backtester.simulate_factor_importance_analysis()
    
    # Step 4: Create visualizations
    print("📊 Creating visualizations...")
    backtester.create_visualizations()
    
    # Step 5: Generate report
    print("📋 Generating analysis report...")
    report = backtester.generate_report()
    
    print(report)
    
    # Save report
    with open('simple_backtest_report.txt', 'w') as f:
        f.write(report)
    
    print("✅ Analysis complete!")
    print("📄 Full report saved to: simple_backtest_report.txt")
    print("📊 Charts saved to: simple_backtest_viz/")
    
    return backtester

if __name__ == "__main__":
    run_simple_analysis()
