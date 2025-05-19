# prediction_tracker.py
import json
import os
import datetime
import statsapi
import logging

logger = logging.getLogger('MLB-HR-Predictor-Tracker')

class PredictionTracker:
    def __init__(self):
        self.tracking_file = "prediction_tracking.json"
        self.load_tracking_data()
        
    def load_tracking_data(self):
        """Load existing tracking data or create new structure"""
        if os.path.exists(self.tracking_file):
            try:
                with open(self.tracking_file, 'r') as f:
                    self.tracking_data = json.load(f)
            except Exception as e:
                logger.error(f"Error loading tracking data: {e}")
                self.initialize_tracking_data()
        else:
            self.initialize_tracking_data()
    
    def initialize_tracking_data(self):
        """Create new tracking data structure"""
        self.tracking_data = {
            "predictions": {},
            "accuracy": {
                "total_predictions": 0,
                "correct_predictions": 0,
                "locks_accuracy": 0,
                "hot_picks_accuracy": 0,
                "sleepers_accuracy": 0
            },
            "last_updated": ""
        }
    
    def save_tracking_data(self):
        """Save tracking data to file"""
        try:
            with open(self.tracking_file, 'w') as f:
                json.dump(self.tracking_data, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving tracking data: {e}")
            return False
    
    def log_predictions(self, date, categories):
        """Log new predictions for tracking"""
        if date not in self.tracking_data["predictions"]:
            self.tracking_data["predictions"][date] = {
                "locks": [],
                "hot_picks": [],
                "sleepers": [],
                "verified": False
            }
        
        # Add predictions from each category
        for category in ["locks", "hot_picks", "sleepers"]:
            for player in categories.get(category, []):
                self.tracking_data["predictions"][date][category].append({
                    "player": player["player"],
                    "team": player["team"],
                    "opponent": player["opponent"],
                    "game_id": player["game_id"],
                    "probability": player["hr_probability"],
                    "hit_hr": None  # To be updated later
                })
        
        self.tracking_data["last_updated"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return self.save_tracking_data()
    
    def verify_predictions(self, date=None):
        """Check actual game results and update predictions"""
        if date is None:
            # Default to yesterday
            yesterday = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
            date = yesterday
            
        if date not in self.tracking_data["predictions"]:
            logger.warning(f"No predictions found for {date}")
            return False
            
        if self.tracking_data["predictions"][date]["verified"]:
            logger.info(f"Predictions for {date} already verified")
            return True
            
        # Get all game results for the date
        try:
            schedule = statsapi.schedule(date=date)
            
            # Create a dictionary of players who hit home runs
            hr_hitters = set()
            
            for game in schedule:
                game_id = game['game_id']
                
                # Skip games that weren't played
                if game['status'] != 'Final':
                    continue
                
                # Get the game's boxscore to find home runs
                try:
                    boxscore = statsapi.boxscore_data(game_id)
                    
                    # Process home runs for home team
                    home_hr = self.extract_home_runs_from_boxscore(boxscore, 'home')
                    hr_hitters.update(home_hr)
                    
                    # Process home runs for away team
                    away_hr = self.extract_home_runs_from_boxscore(boxscore, 'away')
                    hr_hitters.update(away_hr)
                    
                except Exception as e:
                    logger.error(f"Error getting boxscore for game {game_id}: {e}")
            
            # Update our predictions with actual results
            predictions = self.tracking_data["predictions"][date]
            
            for category in ["locks", "hot_picks", "sleepers"]:
                for prediction in predictions[category]:
                    player_name = prediction["player"]
                    # Check if player hit a home run
                    prediction["hit_hr"] = player_name in hr_hitters
            
            # Mark as verified
            self.tracking_data["predictions"][date]["verified"] = True
            
            # Update accuracy metrics
            self.update_accuracy_metrics()
            
            # Save changes
            return self.save_tracking_data()
            
        except Exception as e:
            logger.error(f"Error verifying predictions for {date}: {e}")
            return False
    
    def extract_home_runs_from_boxscore(self, boxscore, team_type):
        """Extract players who hit HRs from boxscore data"""
        hr_hitters = set()
        
        try:
            # Navigate the boxscore data to find home runs
            if 'teams' in boxscore and team_type in boxscore['teams']:
                team_data = boxscore['teams'][team_type]
                
                # Look for home runs in batting stats
                if 'players' in team_data:
                    for player_id, player_data in team_data['players'].items():
                        if 'stats' in player_data and 'batting' in player_data['stats']:
                            batting_stats = player_data['stats']['batting']
                            if 'homeRuns' in batting_stats and batting_stats['homeRuns'] > 0:
                                player_name = player_data['person']['fullName']
                                hr_hitters.add(player_name)
        except Exception as e:
            logger.error(f"Error extracting home runs: {e}")
        
        return hr_hitters
    
    def update_accuracy_metrics(self):
        """Update overall accuracy metrics"""
        total_predictions = 0
        correct_predictions = 0
        
        category_totals = {
            "locks": {"total": 0, "correct": 0},
            "hot_picks": {"total": 0, "correct": 0},
            "sleepers": {"total": 0, "correct": 0}
        }
        
        # Process all verified predictions
        for date, predictions in self.tracking_data["predictions"].items():
            if not predictions["verified"]:
                continue
                
            for category in ["locks", "hot_picks", "sleepers"]:
                for prediction in predictions[category]:
                    if prediction["hit_hr"] is not None:  # Only count verified predictions
                        category_totals[category]["total"] += 1
                        if prediction["hit_hr"]:
                            category_totals[category]["correct"] += 1
        
        # Calculate totals
        for category, counts in category_totals.items():
            total_predictions += counts["total"]
            correct_predictions += counts["correct"]
        
        # Update accuracy metrics
        self.tracking_data["accuracy"]["total_predictions"] = total_predictions
        self.tracking_data["accuracy"]["correct_predictions"] = correct_predictions
        
        if total_predictions > 0:
            self.tracking_data["accuracy"]["overall_accuracy"] = correct_predictions / total_predictions
        
        # Update category-specific accuracy
        for category in ["locks", "hot_picks", "sleepers"]:
            if category_totals[category]["total"] > 0:
                accuracy = category_totals[category]["correct"] / category_totals[category]["total"]
                self.tracking_data["accuracy"][f"{category}_accuracy"] = accuracy
    
    def generate_accuracy_report(self):
        """Generate a human-readable accuracy report"""
        accuracy = self.tracking_data["accuracy"]
        
        report = "📊 HOME RUN PREDICTION ACCURACY REPORT 📊\n\n"
        
        # Overall stats
        total = accuracy.get("total_predictions", 0)
        correct = accuracy.get("correct_predictions", 0)
        overall_accuracy = correct / total if total > 0 else 0
        
        report += f"Overall Accuracy: {overall_accuracy:.1%} ({correct}/{total})\n\n"
        
        # Category breakdown
        report += "Category Breakdown:\n"
        for category in ["locks", "hot_picks", "sleepers"]:
            category_accuracy = accuracy.get(f"{category}_accuracy", 0)
            report += f"• {category.replace('_', ' ').title()}: {category_accuracy:.1%}\n"
        
        report += f"\nLast Updated: {self.tracking_data['last_updated']}"
        
        return report
