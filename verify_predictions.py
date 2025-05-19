# verify_predictions.py
from prediction_tracker import PredictionTracker
import logging
import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Prediction-Verifier")

def main():
    # Calculate yesterday's date
    yesterday = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    
    logger.info(f"Verifying predictions for {yesterday}")
    
    # Initialize tracker and verify
    tracker = PredictionTracker()
    success = tracker.verify_predictions(yesterday)
    
    if success:
        logger.info(f"Successfully verified predictions for {yesterday}")
        
        # Generate and log report
        report = tracker.generate_accuracy_report()
        logger.info("\nAccuracy Report:\n" + report)
    else:
        logger.error(f"Failed to verify predictions for {yesterday}")

if __name__ == "__main__":
    main()
