# MLB Home Run Predictor

An AI-powered tool that predicts daily MLB home run probabilities using advanced metrics, weather data, and matchup analysis.

![Baseball Home Run](https://img.shields.io/badge/MLB-Home%20Run%20Predictor-blue)
![Python](https://img.shields.io/badge/Python-3.9+-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

## Overview

This project uses machine learning techniques and baseball analytics to predict which players are most likely to hit home runs on any given day. The system analyzes over 25 different factors including:

- Recent player performance and hot/cold streaks
- Ballpark factors and dimensions
- Real-time weather conditions (temperature, wind speed, wind direction, humidity)
- Batter vs pitcher matchups
- Platoon advantages (L/R matchups)
- Advanced Statcast metrics (barrel%, exit velocity, launch angle)
- Spray angle analysis (pull/center/opposite field performance)
- Zone contact quality (performance by pitch location)
- Park-specific player history
- Pitch-specific performance metrics

Predictions are categorized into "Locks," "Hot Picks," and "Sleepers," and delivered via Telegram messages with detailed analytics.

## Features

- **Multi-tiered Scheduling**: 
  - **Early Morning Run (6AM)**: Makes predictions using probable pitchers 
  - **Four Midday Runs**: Updates predictions at 10AM, 1PM, 4PM, and 7PM when lineups are confirmed
  - **Next-Day Verification (9AM)**: Automatically verifies previous day's predictions

- **Advanced Data Integration**:
  - **MLB Stats API**: Direct integration with official MLB data
  - **Baseball Savant**: Advanced Statcast metrics and spray charts
  - **Rotowire Backup**: Alternative lineup source if MLB API fails
  - **Prediction Tracking**: Historical accuracy tracking to refine the model

- **Real-time Weather Analysis**:
  - Temperature and humidity effects
  - Wind speed and direction analysis relative to ballpark orientation
  - Custom weather factors for domed stadiums

- **Comprehensive Matchup Analysis**:
  - L/R Platoon advantages
  - Batter performance against specific pitch types
  - Pitcher workload/fatigue tracking
  - Park-specific player performance history

- **Detailed Telegram Reports**: 
  - Provides comprehensive analysis with emojis and MLB stats
  - Includes key metrics, matchup edges, and analytics-driven insights

## Requirements

- Python 3.9+
- MLB Stats API access
- OpenWeather API key
- Telegram Bot Token

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/mlb-hr-predictor.git
   cd mlb-hr-predictor
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables (or use .env file):
   ```bash
   export TELEGRAM_BOT_TOKEN="your_telegram_bot_token"
   export TELEGRAM_CHAT_ID="your_telegram_chat_id"
   export OPENWEATHER_API_KEY="your_openweather_api_key"
   ```

## Configuration

Modify the constants in `mlb_hr_predictor.py` to adjust:
- HR prediction weights
- Ballpark factors
- Team codes
- Other model parameters

## Usage

### Manual Run

```bash
# Run with current settings
python mlb_hr_predictor.py

# To run at specific time of day
python run_predictor.py
```

### Automated GitHub Action

The repository is configured with GitHub Actions to run automatically:
- 6:00 AM: Early run with probable pitchers
- 10:00 AM, 1:00 PM, 4:00 PM, 7:00 PM: Lineup check runs
- 9:00 AM: Verification of previous day's predictions

## File Structure

- **Core Prediction System**:
  - `mlb_hr_predictor.py`: Main predictor class and algorithm
  - `run_predictor.py`: Entry point for scheduled runs
  - `verify_predictions.py`: Validates prediction accuracy
  - `prediction_tracker.py`: Tracks and analyzes prediction history

- **Data Fetching**:
  - `lineup_fetcher.py`: Handles lineup and pitcher data retrieval from MLB API
  - `rotowire_lineups.py`: Alternative lineup source from Rotowire
  - `stats_fetcher.py`: Fetches player and pitcher statistics
  - `baseball_savant.py`: Integrates advanced Statcast metrics

- **Output Formatting**:
  - `telegram_formatter.py`: Formats predictions for Telegram messages

- **Configuration**:
  - `.github/workflows/schedule.yml`: GitHub Actions workflow configuration

- **Development Tools**:
  - `debug_lineup_fetcher.py`: Debug tool for lineup retrieval
  - `debug_stats_fetcher.py`: Debug tool for statistics
  - `mlb-api-diagnostic.py`: Diagnostic tool for MLB API
  - `rotowire_debug_script.py`: Debug tool for Rotowire integration

## How It Works

1. **Data Collection**: 
   - Fetches games, lineups, weather data from multiple sources
   - Integrates advanced Statcast metrics from Baseball Savant
   - Falls back to alternate sources if primary sources fail

2. **Factor Analysis**: 
   - Evaluates 25+ different factors for each batter
   - Combines traditional stats with advanced metrics
   - Applies contextual factors (weather, ballpark, matchups)

3. **Probability Calculation**: 
   - Uses weighted factors to calculate HR probability
   - Adjusts weights based on predictive power
   - Normalizes across different metric scales

4. **Categorization**: 
   - Groups predictions into Locks, Hot Picks, and Sleepers
   - Ranks players by probability within each category

5. **Delivery**: 
   - Formats and sends detailed reports via Telegram
   - Includes comprehensive analytics and matchup advantages

6. **Verification**:
   - Tracks actual home runs hit each day
   - Calculates prediction accuracy by category
   - Maintains historical performance metrics

## Factors Considered

The predictor evaluates these key factors (with customizable weights):

### Core Metrics:
- Recent HR rate (7-10 day performance)
- Season HR rate
- Ballpark HR factor
- Pitcher HR allowed rate

### Contact Quality Metrics:
- Barrel percentage
- Exit velocity 
- Hard hit percentage
- Launch angle
- Hard hit distance

### Directional Metrics:
- Pull percentage
- Fly ball rate
- HR to fly ball ratio
- Spray angle (pull/center/oppo)
- Zone contact (performance by pitch location)

### Matchup Factors:
- Platoon advantage (L/R matchups)
- Pitcher ground ball to fly ball ratio
- Pitcher workload/fatigue
- Batter vs pitch type performance
- Park-specific player history

### Contextual Factors:
- Weather conditions (temp, humidity, wind)
- Home/away splits
- Hot/cold streaks

### Advanced Metrics:
- Expected ISO (xISO)
- Expected wOBA (xwOBA)
- SLG threshold effects
- Barrel rate threshold effects

## Sample Output

```
⚾️💥 MLB HOME RUN PREDICTIONS - 2025-05-17 🔥 MIDDAY (CONFIRMED LINEUPS) 🔥 💥⚾️

📊 Today's Top Home Run Picks 📊
Powered by AI + 16 key HR factors including:
🔍 Recent hot streaks, quality of contact metrics
🏟️ Ballpark factors, weather conditions
⚔️ Pitcher matchups & platoon advantages

🔒 ABSOLUTE LOCKS 🔒

1. Juan Soto (NYY) vs Griffin Canning - 5.2% HR chance
   📍 Yankee Stadium vs New York Mets | ⏰ 3:05 PM ET
   👉 L batter vs R pitcher | 🌡️ 89.7°F, 💨 8.0 mph winds (favorable for HR)
   💪 STRENGTHS:
   • ISO: 0.312 (ELITE) 💪
   • SLG: 0.567 (ELITE) 🚀
   • L15 Barrel%: 0.275 (ELITE) 🎯
   • xISO: 0.301 (Elite) 📈
   • Barrel%: 0.098 (Elite) 🎯
   • Exit Velo: 92.3 mph 💥
   • HR/FB: 23.5% ⚾
   • Recent Form: HOT 🔥

   ⚔️ MATCHUP EDGES:
   • Park Factor: 1.15 (HR-friendly) 🏟️
   • Platoon Advantage: YES ✓
   • Pitcher HR/9: 1.68 (vulnerable) 🚀
   • GB/FB Ratio: 0.87 (fly ball pitcher) ↗️
   • Pitcher Fatigue: HIGH 😓

   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

2. Jordan Lawlar (ARI) vs Germán Márquez - 4.7% HR chance
   📍 Chase Field vs Colorado Rockies | ⏰ 7:10 PM ET
   👉 R batter vs R pitcher | 🌡️ 89.7°F, 💨 8.0 mph winds (favorable for HR)
   💪 STRENGTHS:
   • xISO: 0.220 (Strong) 📈
   • xwOBA: 0.342 (Above Average) 📊
   • Exit Velo: 91.4 mph 💥
   • Hard Hit%: 44.2% 💪
   • HR/FB: 19.8% ⚾

   ⚔️ MATCHUP EDGES:
   • Park Factor: 1.04 (HR-friendly) 🏟️
   • Pitcher HR/9: 1.42 (vulnerable) 🚀
   • GB/FB Ratio: 0.92 (fly ball pitcher) ↗️

   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Prediction Accuracy

The system tracks prediction accuracy automatically using the `prediction_tracker.py` module. Each day at 9:00 AM, the `verify_predictions.py` script runs to check the previous day's predictions against actual results.

Historical accuracy metrics are maintained for:
- Overall prediction accuracy
- Category-specific accuracy (Locks, Hot Picks, Sleepers)
- Player-specific performance

This data is used to continuously refine the model and improve prediction quality.

## Baseball Savant Integration

The system integrates advanced metrics from Baseball Savant through the `baseball_savant.py` module, providing:

- Player-specific spray charts and pull tendencies
- Zone-based contact quality analysis
- Pitch-specific performance data
- Hard hit distance metrics
- Ballpark-specific player history

These Statcast metrics significantly enhance prediction accuracy by capturing quality of contact details beyond traditional statistics.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- MLB Stats API for game and player data
- PyBaseball for additional baseball statistics
- Baseball Savant for advanced Statcast metrics
- OpenWeather API for weather data

## Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the issues page.

## Disclaimer

This tool is for educational and entertainment purposes only. Always gamble responsibly.