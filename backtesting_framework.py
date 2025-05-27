# backtesting_framework.py
import pandas as pd
import numpy as np
import datetime
import logging
import json
import os
from collections import defaultdict
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import precision_score, recall_score, roc_auc_score, confusion_matrix
from sklearn.model_selection import ParameterGrid
import statsapi
import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# Import your existing components
from mlb_hr_predictor import MLBHomeRunPredictor, WEIGHTS, BALLPARKS
from stats_fetcher import fetch_player_stats, fetch_pitcher_stats
from lineup_fetcher import fetch_lineups_and_pitchers

logger = logging.getLogger('MLB-HR-Backtesting')

class MLBBacktester:
    def __init__(self, start_date, end_date, cache_dir='backtest_cache'):
        """
        Initialize the backtesting framework
        
        Parameters:
        -----------
        start_date : str
            Start date for backtesting (YYYY-MM-DD)
        end_date : str
            End date for backtesting (YYYY-MM-DD)
        cache_dir : str
            Directory to cache historical data
        """
        self.start_date = start_date
        self.end_date = end_date
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        
        # Results storage
        self.backtest_results = []
        self.factor_importance = {}
        self.optimal_weights = {}
        self.performance_metrics = {}
        
        logger.info(f"Initialized backtester for {start_date} to {end_date}")
    
    def run_full_backtest(self, sample_days=None, optimize_weights=True):
        """
        Run comprehensive backtesting
        
        Parameters:
        -----------
        sample_days : int, optional
            Number of days to sample (for faster testing). None = all days
        optimize_weights : bool
            Whether to run weight optimization
        """
        logger.info("🚀 Starting comprehensive backtesting...")
        
        # Step 1: Get historical dates to test
        test_dates = self._generate_test_dates(sample_days)
        logger.info(f"Testing {len(test_dates)} dates")
        
        # Step 2: Run predictions for each date
        logger.info("📊 Running historical predictions...")
        self._run_historical_predictions(test_dates)
        
        # Step 3: Analyze results
        logger.info("🔍 Analyzing prediction performance...")
        self._analyze_performance()
        
        # Step 4: Factor importance analysis
        logger.info("⚖️ Analyzing factor importance...")
        self._analyze_factor_importance()
        
        # Step 5: Weight optimization (if requested)
        if optimize_weights:
            logger.info("🎯 Optimizing prediction weights...")
            self._optimize_weights()
        
        # Step 6: Generate comprehensive report
        logger.info("📋 Generating backtest report...")
        report = self._generate_report()
        
        logger.info("✅ Backtesting complete!")
        return report
    
    def _generate_test_dates(self, sample_days=None):
        """Generate list of dates to test"""
        start = datetime.datetime.strptime(self.start_date, '%Y-%m-%d')
        end = datetime.datetime.strptime(self.end_date, '%Y-%m-%d')
        
        # Generate all dates in range
        dates = []
        current = start
        while current <= end:
            # Only include dates that likely had MLB games (April-October)
            if 4 <= current.month <= 10:
                dates.append(current.strftime('%Y-%m-%d'))
            current += datetime.timedelta(days=1)
        
        # Sample if requested
        if sample_days and len(dates) > sample_days:
            dates = np.random.choice(dates, sample_days, replace=False).tolist()
            dates.sort()
        
        return dates
    
    def _run_historical_predictions(self, test_dates):
        """Run predictions for historical dates"""
        results = []
        
        for i, date in enumerate(test_dates):
            try:
                logger.info(f"Processing {date} ({i+1}/{len(test_dates)})")
                
                # Get historical data for this date
                historical_data = self._get_historical_data(date)
                
                if not historical_data:
                    logger.warning(f"No data available for {date}")
                    continue
                
                # Run predictions using historical data
                predictions = self._run_predictions_for_date(date, historical_data)
                
                # Get actual home runs that occurred
                actual_hrs = self._get_actual_home_runs(date)
                
                # Combine predictions with actual results
                day_results = self._combine_predictions_and_actuals(date, predictions, actual_hrs)
                results.extend(day_results)
                
                # Cache results periodically
                if len(results) % 100 == 0:
                    self._save_intermediate_results(results)
                
                # Rate limiting
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Error processing {date}: {e}")
                continue
        
        self.backtest_results = results
        self._save_results()
        return results
    
    def _get_historical_data(self, date):
        """Get all historical data needed for predictions on a specific date"""
        cache_file = os.path.join(self.cache_dir, f"historical_data_{date}.json")
        
        # Check cache first
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        
        try:
            # Get games for this date
            schedule = statsapi.schedule(date=date)
            
            if not schedule:
                return None
            
            # Filter to completed games only
            completed_games = [g for g in schedule if g['status'] == 'Final']
            
            if not completed_games:
                return None
            
            historical_data = {
                'date': date,
                'games': completed_games,
                'weather': {},  # We'll simulate weather for backtesting
            }
            
            # Cache the data
            with open(cache_file, 'w') as f:
                json.dump(historical_data, f)
            
            return historical_data
            
        except Exception as e:
            logger.error(f"Error fetching historical data for {date}: {e}")
            return None
    
    def _run_predictions_for_date(self, date, historical_data):
        """Run the prediction model for a specific historical date"""
        try:
            # Create a mock predictor instance for this date
            predictor = MLBHomeRunPredictor()
            predictor.today = date
            predictor.today_dt = datetime.datetime.strptime(date, '%Y-%m-%d')
            predictor.early_run = False  # Use confirmed lineups
            
            # Convert historical games to DataFrame format
            games_list = []
            for game in historical_data['games']:
                home_team = predictor.convert_mlb_team_to_code(game['home_name'])
                away_team = predictor.convert_mlb_team_to_code(game['away_name'])
                
                if home_team and away_team:
                    game_data = {
                        'game_id': f"{home_team}_{away_team}_{date}",
                        'game_id_mlb': game['game_id'],
                        'home_team': home_team,
                        'away_team': away_team,
                        'home_team_name': game['home_name'],
                        'away_team_name': game['away_name'],
                        'ballpark': game.get('venue_name', 'Unknown'),
                        'ballpark_factor': predictor.BALLPARKS.get(home_team, {}).get('factor', 1.0),
                        'ballpark_lat': predictor.BALLPARKS.get(home_team, {}).get('lat', 0),
                        'ballpark_lon': predictor.BALLPARKS.get(home_team, {}).get('lon', 0),
                        'ballpark_orient': predictor.BALLPARKS.get(home_team, {}).get('orient', 0),
                        'game_time': game.get('game_datetime', ''),
                    }
                    games_list.append(game_data)
            
            if not games_list:
                return []
            
            predictor.games = pd.DataFrame(games_list)
            
            # Simulate weather (in real implementation, you might cache historical weather)
            for game_id in predictor.games['game_id']:
                predictor.weather_data[game_id] = {
                    'temp': np.random.normal(75, 10),  # Simulate typical game temp
                    'humidity': np.random.normal(60, 15),
                    'wind_speed': np.random.normal(8, 5),
                    'wind_deg': np.random.uniform(0, 360)
                }
            
            # For backtesting, we'll simulate lineups and stats
            # In a full implementation, you might try to get historical lineups
            predictor.lineups = self._simulate_lineups_for_games(predictor.games)
            predictor.probable_pitchers = self._simulate_pitchers_for_games(predictor.games)
            
            # Fetch stats (this will get season stats up to that date)
            predictor.fetch_player_stats()
            predictor.fetch_pitcher_stats()
            
            # Run predictions
            predictions_df = predictor.predict_home_runs()
            
            return predictions_df.to_dict('records') if not predictions_df.empty else []
            
        except Exception as e:
            logger.error(f"Error running predictions for {date}: {e}")
            return []
    
    def _simulate_lineups_for_games(self, games_df):
        """Simulate lineups for backtesting (simplified)"""
        lineups = {}
        
        # Common player names by team (simplified for backtesting)
        team_players = {
            'NYY': ['Aaron Judge', 'Giancarlo Stanton', 'Anthony Rizzo', 'Gleyber Torres'],
            'LAD': ['Mookie Betts', 'Freddie Freeman', 'Will Smith', 'Max Muncy'],
            'HOU': ['Jose Altuve', 'Alex Bregman', 'Yordan Alvarez', 'Kyle Tucker'],
            # Add more teams as needed for backtesting
        }
        
        for _, game in games_df.iterrows():
            game_id = game['game_id']
            home_team = game['home_team']
            away_team = game['away_team']
            
            # Generate simulated lineups
            home_lineup = team_players.get(home_team, [f"{home_team} Player {i}" for i in range(1, 10)])
            away_lineup = team_players.get(away_team, [f"{away_team} Player {i}" for i in range(1, 10)])
            
            lineups[game_id] = {
                'home': home_lineup[:9],
                'away': away_lineup[:9]
            }
        
        return lineups
    
    def _simulate_pitchers_for_games(self, games_df):
        """Simulate probable pitchers for backtesting"""
        pitchers = {}
        
        for _, game in games_df.iterrows():
            game_id = game['game_id']
            home_team = game['home_team']
            away_team = game['away_team']
            
            pitchers[game_id] = {
                'home': f"{home_team} Pitcher",
                'away': f"{away_team} Pitcher"
            }
        
        return pitchers
    
    def _get_actual_home_runs(self, date):
        """Get actual home runs that occurred on this date"""
        cache_file = os.path.join(self.cache_dir, f"actual_hrs_{date}.json")
        
        # Check cache
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        
        actual_hrs = []
        
        try:
            # Get games for this date
            schedule = statsapi.schedule(date=date)
            
            for game in schedule:
                if game['status'] == 'Final':
                    game_id = game['game_id']
                    
                    try:
                        # Get boxscore to find home runs
                        boxscore = statsapi.boxscore_data(game_id)
                        
                        # Extract home runs from both teams
                        for team_type in ['home', 'away']:
                            if team_type in boxscore.get('teams', {}):
                                team_data = boxscore['teams'][team_type]
                                
                                if 'players' in team_data:
                                    for player_id, player_data in team_data['players'].items():
                                        if 'stats' in player_data and 'batting' in player_data['stats']:
                                            batting_stats = player_data['stats']['batting']
                                            hrs = batting_stats.get('homeRuns', 0)
                                            
                                            if hrs > 0:
                                                player_name = player_data['person']['fullName']
                                                actual_hrs.append({
                                                    'date': date,
                                                    'player': player_name,
                                                    'team': team_type,
                                                    'game_id': game_id,
                                                    'hrs': hrs
                                                })
                        
                        # Rate limiting
                        time.sleep(0.2)
                        
                    except Exception as e:
                        logger.error(f"Error getting boxscore for game {game_id}: {e}")
                        continue
            
            # Cache results
            with open(cache_file, 'w') as f:
                json.dump(actual_hrs, f)
            
            return actual_hrs
            
        except Exception as e:
            logger.error(f"Error getting actual HRs for {date}: {e}")
            return []
    
    def _combine_predictions_and_actuals(self, date, predictions, actual_hrs):
        """Combine predictions with actual results"""
        results = []
        
        # Create lookup for actual HRs
        actual_hr_players = {hr['player'] for hr in actual_hrs}
        
        for pred in predictions:
            player = pred['player']
            hit_hr = player in actual_hr_players
            
            result = {
                'date': date,
                'player': player,
                'team': pred.get('team', ''),
                'predicted_prob': pred['hr_probability'],
                'hit_hr': hit_hr,
                'prediction_correct': hit_hr,  # Will refine this based on probability thresholds
                # Include all prediction factors for analysis
                **{k: v for k, v in pred.items() if k not in ['player', 'team', 'hr_probability']}
            }
            results.append(result)
        
        return results
    
    def _analyze_performance(self):
        """Analyze prediction performance"""
        if not self.backtest_results:
            logger.warning("No backtest results to analyze")
            return
        
        df = pd.DataFrame(self.backtest_results)
        
        # Overall metrics
        total_predictions = len(df)
        total_hrs_predicted = df['predicted_prob'].sum()
        total_hrs_actual = df['hit_hr'].sum()
        
        # Calibration analysis (are predicted probabilities realistic?)
        calibration = self._analyze_calibration(df)
        
        # Performance by probability bins
        bin_performance = self._analyze_by_probability_bins(df)
        
        # Category performance (simulate Locks/Hot Picks/Sleepers)
        category_performance = self._analyze_category_performance(df)
        
        self.performance_metrics = {
            'total_predictions': total_predictions,
            'total_hrs_predicted': total_hrs_predicted,
            'total_hrs_actual': total_hrs_actual,
            'calibration': calibration,
            'bin_performance': bin_performance,
            'category_performance': category_performance,
            'overall_accuracy': total_hrs_actual / total_predictions if total_predictions > 0 else 0
        }
        
        return self.performance_metrics
    
    def _analyze_calibration(self, df):
        """Analyze how well predicted probabilities match actual rates"""
        bins = np.arange(0, 0.21, 0.01)  # 0% to 20% in 1% bins
        
        calibration_data = []
        for i in range(len(bins)-1):
            bin_start, bin_end = bins[i], bins[i+1]
            
            mask = (df['predicted_prob'] >= bin_start) & (df['predicted_prob'] < bin_end)
            bin_data = df[mask]
            
            if len(bin_data) > 0:
                predicted_rate = bin_data['predicted_prob'].mean()
                actual_rate = bin_data['hit_hr'].mean()
                count = len(bin_data)
                
                calibration_data.append({
                    'bin_start': bin_start,
                    'bin_end': bin_end,
                    'predicted_rate': predicted_rate,
                    'actual_rate': actual_rate,
                    'count': count,
                    'calibration_error': abs(predicted_rate - actual_rate)
                })
        
        return calibration_data
    
    def _analyze_by_probability_bins(self, df):
        """Analyze performance by probability ranges"""
        thresholds = [0.02, 0.04, 0.06, 0.08, 0.10, 1.0]
        bin_performance = []
        
        for i in range(len(thresholds)):
            if i == 0:
                mask = df['predicted_prob'] < thresholds[i]
                label = f"<{thresholds[i]*100:.0f}%"
            else:
                mask = (df['predicted_prob'] >= thresholds[i-1]) & (df['predicted_prob'] < thresholds[i])
                label = f"{thresholds[i-1]*100:.0f}%-{thresholds[i]*100:.0f}%"
            
            bin_data = df[mask]
            
            if len(bin_data) > 0:
                bin_performance.append({
                    'range': label,
                    'count': len(bin_data),
                    'predicted_rate': bin_data['predicted_prob'].mean(),
                    'actual_rate': bin_data['hit_hr'].mean(),
                    'total_hrs': bin_data['hit_hr'].sum()
                })
        
        return bin_performance
    
    def _analyze_category_performance(self, df):
        """Analyze performance by prediction categories"""
        # Sort by probability and create categories
        df_sorted = df.sort_values('predicted_prob', ascending=False)
        
        total_predictions = len(df_sorted)
        locks_size = max(1, int(total_predictions * 0.05))  # Top 5%
        hot_picks_size = max(1, int(total_predictions * 0.15))  # Next 15%
        
        categories = {
            'locks': df_sorted.head(locks_size),
            'hot_picks': df_sorted.iloc[locks_size:locks_size+hot_picks_size],
            'sleepers': df_sorted.iloc[locks_size+hot_picks_size:]
        }
        
        category_performance = {}
        for category, data in categories.items():
            if len(data) > 0:
                category_performance[category] = {
                    'count': len(data),
                    'predicted_rate': data['predicted_prob'].mean(),
                    'actual_rate': data['hit_hr'].mean(),
                    'total_hrs': data['hit_hr'].sum(),
                    'hit_rate': data['hit_hr'].sum() / len(data)
                }
        
        return category_performance
    
    def _analyze_factor_importance(self):
        """Analyze which factors are most predictive of home runs"""
        if not self.backtest_results:
            return
        
        df = pd.DataFrame(self.backtest_results)
        
        # Factors to analyze (based on your prediction features)
        factors = [
            'recent_hr_rate', 'season_hr_rate', 'ballpark_factor', 'weather_factor',
            'barrel_pct', 'exit_velo', 'launch_angle', 'pull_pct', 'hard_hit_pct',
            'platoon_advantage', 'pitcher_hr_rate', 'xISO', 'xwOBA'
        ]
        
        factor_importance = {}
        
        for factor in factors:
            if factor in df.columns:
                # Calculate correlation with actual HRs
                correlation = df[factor].corr(df['hit_hr'])
                
                # Calculate predictive power by binning
                try:
                    # Split into high/low groups
                    median_val = df[factor].median()
                    high_group = df[df[factor] >= median_val]
                    low_group = df[df[factor] < median_val]
                    
                    high_hr_rate = high_group['hit_hr'].mean() if len(high_group) > 0 else 0
                    low_hr_rate = low_group['hit_hr'].mean() if len(low_group) > 0 else 0
                    
                    predictive_power = high_hr_rate - low_hr_rate
                    
                    factor_importance[factor] = {
                        'correlation': correlation,
                        'predictive_power': predictive_power,
                        'high_group_hr_rate': high_hr_rate,
                        'low_group_hr_rate': low_hr_rate,
                        'current_weight': WEIGHTS.get(factor, 0)
                    }
                except:
                    factor_importance[factor] = {
                        'correlation': correlation,
                        'predictive_power': 0,
                        'current_weight': WEIGHTS.get(factor, 0)
                    }
        
        # Sort by predictive power
        self.factor_importance = dict(sorted(
            factor_importance.items(),
            key=lambda x: abs(x[1]['predictive_power']),
            reverse=True
        ))
        
        return self.factor_importance
    
    def _optimize_weights(self):
        """Optimize prediction weights based on backtest results"""
        if not self.backtest_results:
            logger.warning("No backtest results for weight optimization")
            return
        
        logger.info("Running weight optimization...")
        
        # This is a simplified optimization - in practice you might use more sophisticated methods
        # like genetic algorithms, Bayesian optimization, or gradient descent
        
        # Get top performing factors
        top_factors = list(self.factor_importance.keys())[:10]  # Top 10 factors
        
        # Define parameter grid for optimization
        weight_ranges = {}
        for factor in top_factors:
            current_weight = WEIGHTS.get(factor, 0.05)
            # Test weights around current value
            weight_ranges[factor] = [
                current_weight * 0.5,
                current_weight * 0.75,
                current_weight,
                current_weight * 1.25,
                current_weight * 1.5
            ]
        
        # Grid search (simplified)
        best_score = 0
        best_weights = WEIGHTS.copy()
        
        # Sample a subset of combinations to avoid explosion
        param_grid = ParameterGrid(weight_ranges)
        sample_size = min(100, len(list(param_grid)))  # Max 100 combinations
        
        for i, weights in enumerate(param_grid):
            if i >= sample_size:
                break
                
            # Test these weights
            score = self._evaluate_weight_combination(weights)
            
            if score > best_score:
                best_score = score
                best_weights.update(weights)
        
        self.optimal_weights = best_weights
        logger.info(f"Weight optimization complete. Best score: {best_score:.4f}")
        
        return self.optimal_weights
    
    def _evaluate_weight_combination(self, weight_updates):
        """Evaluate a specific weight combination"""
        # This would re-run predictions with new weights and measure performance
        # For now, we'll use a simplified scoring based on factor importance
        score = 0
        
        for factor, weight in weight_updates.items():
            if factor in self.factor_importance:
                # Score based on predictive power * weight alignment
                predictive_power = abs(self.factor_importance[factor]['predictive_power'])
                score += predictive_power * weight
        
        return score
    
    def _generate_report(self):
        """Generate comprehensive backtest report"""
        report = {
            'summary': {
                'backtest_period': f"{self.start_date} to {self.end_date}",
                'total_predictions': len(self.backtest_results),
                'total_dates_tested': len(set(r['date'] for r in self.backtest_results)),
                'generated_at': datetime.datetime.now().isoformat()
            },
            'performance_metrics': self.performance_metrics,
            'factor_importance': self.factor_importance,
            'optimal_weights': self.optimal_weights,
            'recommendations': self._generate_recommendations()
        }
        
        # Save detailed report
        report_file = os.path.join(self.cache_dir, 'backtest_report.json')
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Generate readable summary
        readable_report = self._format_readable_report(report)
        
        return readable_report
    
    def _generate_recommendations(self):
        """Generate actionable recommendations based on backtest results"""
        recommendations = []
        
        if self.factor_importance:
            # Top factors recommendation
            top_3_factors = list(self.factor_importance.keys())[:3]
            recommendations.append(f"Top predictive factors: {', '.join(top_3_factors)}")
            
            # Underweighted factors
            underweighted = []
            for factor, metrics in self.factor_importance.items():
                if metrics['predictive_power'] > 0.01 and metrics['current_weight'] < 0.03:
                    underweighted.append(factor)
            
            if underweighted:
                recommendations.append(f"Consider increasing weights for: {', '.join(underweighted[:3])}")
        
        if self.performance_metrics:
            # Calibration recommendations
            calibration = self.performance_metrics.get('calibration', [])
            if calibration:
                avg_error = np.mean([c['calibration_error'] for c in calibration])
                if avg_error > 0.02:
                    recommendations.append("Model predictions are poorly calibrated - consider recalibration")
        
        return recommendations
    
    def _format_readable_report(self, report):
        """Format report for human reading"""
        readable = f"""
📊 MLB HOME RUN PREDICTION BACKTEST REPORT
{'='*50}

🗓️ BACKTEST PERIOD: {report['summary']['backtest_period']}
📈 TOTAL PREDICTIONS: {report['summary']['total_predictions']:,}
📅 DATES TESTED: {report['summary']['total_dates_tested']}

🎯 PERFORMANCE SUMMARY:
"""
        
        if 'performance_metrics' in report and report['performance_metrics']:
            metrics = report['performance_metrics']
            readable += f"""
• Overall Accuracy: {metrics.get('overall_accuracy', 0)*100:.2f}%
• Total HRs Predicted: {metrics.get('total_hrs_predicted', 0):.1f}
• Total HRs Actual: {metrics.get('total_hrs_actual', 0)}
"""
            
            # Category performance
            if 'category_performance' in metrics:
                readable += f"\n📂 CATEGORY PERFORMANCE:\n"
                for category, perf in metrics['category_performance'].items():
                    readable += f"""
• {category.upper()}:
  - Predictions: {perf['count']}
  - Hit Rate: {perf['hit_rate']*100:.1f}%
  - Avg Predicted: {perf['predicted_rate']*100:.2f}%
  - Actual Rate: {perf['actual_rate']*100:.2f}%
"""
        
        # Factor importance
        if 'factor_importance' in report and report['factor_importance']:
            readable += f"\n⚖️ TOP PREDICTIVE FACTORS:\n"
            for i, (factor, metrics) in enumerate(list(report['factor_importance'].items())[:5]):
                readable += f"{i+1}. {factor}: Power={metrics['predictive_power']:.4f}, Weight={metrics['current_weight']:.3f}\n"
        
        # Recommendations
        if 'recommendations' in report and report['recommendations']:
            readable += f"\n💡 RECOMMENDATIONS:\n"
            for i, rec in enumerate(report['recommendations'], 1):
                readable += f"{i}. {rec}\n"
        
        readable += f"\n📄 Full report saved to: {self.cache_dir}/backtest_report.json\n"
        
        return readable
    
    def _save_results(self):
        """Save backtest results"""
        results_file = os.path.join(self.cache_dir, 'backtest_results.json')
        with open(results_file, 'w') as f:
            json.dump(self.backtest_results, f)
    
    def _save_intermediate_results(self, results):
        """Save intermediate results during processing"""
        temp_file = os.path.join(self.cache_dir, 'backtest_results_temp.json')
        with open(temp_file, 'w') as f:
            json.dump(results, f)

# Convenience function for easy usage
def run_backtest(start_date, end_date, sample_days=10):
    """
    Convenience function to run a backtest
    
    Parameters:
    -----------
    start_date : str
        Start date (YYYY-MM-DD)
    end_date : str  
        End date (YYYY-MM-DD)
    sample_days : int
        Number of days to sample for testing
    """
    backtester = MLBBacktester(start_date, end_date)
    report = backtester.run_full_backtest(sample_days=sample_days)
    print(report)
    return backtester

# Example usage
if __name__ == "__main__":
    # Test with a small sample
    backtester = run_backtest("2024-07-01", "2024-07-31", sample_days=5)
