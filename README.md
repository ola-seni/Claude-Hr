# MLB Home Run Predictor

An AI-powered tool that predicts daily MLB home run probabilities using advanced metrics, weather data, and matchup analysis.

![Baseball Home Run](https://img.shields.io/badge/MLB-Home%20Run%20Predictor-blue)
![Python](https://img.shields.io/badge/Python-3.9+-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

## Overview

This project uses machine learning techniques and baseball analytics to predict which players are most likely to hit home runs on any given day. The system analyzes 16 different factors including:

- Recent player performance and hot/cold streaks
- Ballpark factors and dimensions
- Real-time weather conditions
- Batter vs pitcher matchups
- Platoon advantages (L/R matchups)
- Advanced metrics (barrel%, exit velocity, launch angle)

Predictions are categorized into "Locks," "Hot Picks," and "Sleepers," and delivered via Telegram messages with detailed analytics.

## Features

- **Early Morning Run (6AM)**: Makes predictions using probable pitchers 
- **Midday Runs**: Updates predictions when lineups are confirmed
- **Real-time Weather**: Incorporates temperature, humidity, and wind data
- **L/R Matchup Analysis**: Considers platoon advantages
- **Detailed Telegram Reports**: Provides comprehensive analysis with emojis and MLB stats
- **GitHub Actions Integration**: Automates daily runs and updates

## Requirements

- Python 3.9+
- MLB Stats API access
- OpenWeather API key
- Telegram Bot Token

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/ola-seni/Claude-Hr.git
   cd Claude-Hr
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

Modify the constants in `mlb-hr-predictor.py` to adjust:
- HR prediction weights
- Ballpark factors
- Team codes
- Other model parameters

## Usage

### Manual Run

```bash
# Run with current settings
python mlb-hr-predictor.py

# To run at specific time of day
python run_predictor.py
```

### Automated GitHub Action

The repository is configured with GitHub Actions to run automatically:
- 6:00 AM: Early run with probable pitchers
- 10:00 AM, 1:00 PM, 4:00 PM, 7:00 PM: Lineup check runs

## File Structure

- `mlb-hr-predictor.py`: Main predictor class and algorithm
- `lineup_fetcher.py`: Handles lineup and pitcher data retrieval
- `stats_fetcher.py`: Fetches player and pitcher statistics
- `telegram_formatter.py`: Formats predictions for Telegram messages
- `run_predictor.py`: Entry point for scheduled runs
- `.github/workflows/schedule.yml`: GitHub Actions workflow configuration

## How It Works

1. **Data Collection**: Fetches games, lineups, weather, and player stats
2. **Factor Analysis**: Evaluates 16 different factors for each batter
3. **Probability Calculation**: Uses weighted factors to calculate HR probability
4. **Categorization**: Groups predictions into Locks, Hot Picks, and Sleepers
5. **Delivery**: Formats and sends detailed reports via Telegram

## Factors Considered

The predictor evaluates these key factors (with customizable weights):
- Recent HR rate (7-10 day performance)
- Season HR rate
- Ballpark HR factor
- Pitcher HR allowed rate
- Weather conditions (temp, humidity, wind)
- Barrel percentage
- Platoon advantage (L/R matchups)
- Exit velocity
- Fly ball rate
- Pull percentage
- Hard hit percentage
- Launch angle
- Pitcher ground ball to fly ball ratio
- HR to fly ball ratio
- Batter vs pitch type performance
- Pitcher workload/fatigue

## Sample Output

```
⚾️💥 MLB HOME RUN PREDICTIONS - 2025-05-17 🔥 MIDDAY (CONFIRMED LINEUPS) 🔥 💥⚾️

📊 Today's Top Home Run Picks 📊
Powered by AI + 16 key HR factors including:
🔍 Recent hot streaks, quality of contact metrics
🏟️ Ballpark factors, weather conditions
⚔️ Pitcher matchups & platoon advantages

🔒 ABSOLUTE LOCKS 🔒
1. Jordan Lawlar (ARI) - 4.7% HR chance
   🆚 Colorado Rockies @ Chase Field
   ⚾ vs Germán Márquez • 👉 R batter vs R pitcher 👉
   🌡️ 89.7°F, 💨 8.0 mph winds (favorable for HR)
   💪 Batter profile: 🔥 Hot streak (recent HR rate), ⚡ Elite HR/FB ratio
   🔍 Matchup edges: 🚀 Facing fly ball pitcher, 😓 Facing fatigued pitcher
   📊 xStats: 0.220 xISO, 0.342 xwOBA
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- MLB Stats API for game and player data
- PyBaseball for additional baseball statistics
- OpenWeather API for weather data

## Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the issues page.

## Disclaimer

This tool is for educational and entertainment purposes only. Always gamble responsibly.
