import os
import pandas as pd
import numpy as np
import datetime
import time
import requests
import pybaseball
import statsapi  # MLB Stats API for current 2025 data
from pybaseball import statcast_batter, statcast_pitcher, playerid_lookup
import logging
from math import sin, cos, radians
import warnings
from lineup_fetcher import fetch_lineups_and_pitchers
from lineup_fetcher import fetch_lineups_and_pitchers
from stats_fetcher import fetch_player_stats, fetch_pitcher_stats, get_player_names_from_lineups, get_pitcher_names_from_probable_pitchers
from telegram_formatter import format_telegram_message, send_telegram_message
from prediction_tracker import PredictionTracker
from baseball_savant import get_savant_data, get_seasonal_data, get_ballpark_data

warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger('MLB-HR-Predictor')

# Constants
OPENWEATHER_API = os.environ.get("OPENWEATHER_API_KEY", "2b7cfd728d429c2877bb971e1d2d81fd")
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "8192445369:AAHmn6oHdWOaPtD9KJGfgGsP9iGZaraQu4o")
CHAT_ID = int(os.environ.get("TELEGRAM_CHAT_ID", "248150489"))

# Ballpark data with HR factors and orientation
BALLPARKS = {
    'NYY': {'name':'Yankee Stadium',               'lat':40.8296,'lon':-73.9262,'factor':1.15,'orient':75.0},
    'BOS': {'name':'Fenway Park',                  'lat':42.3467,'lon':-71.0972,'factor':1.03,'orient':45.0},
    'TOR': {'name':'Rogers Centre',                'lat':43.6418,'lon':-79.3891,'factor':1.02,'orient':345.0},
    'BAL': {'name':'Oriole Park at Camden Yards',  'lat':39.2838,'lon':-76.6215,'factor':1.02,'orient':31.0},
    'TB':  {'name':'Tropicana Field',              'lat':27.7682,'lon':-82.6534,'factor':0.95,'orient':359.0},
    'CLE': {'name':'Progressive Field',            'lat':41.4962,'lon':-81.6852,'factor':0.98,'orient':0.0},
    'DET': {'name':'Comerica Park',                'lat':42.3390,'lon':-83.0485,'factor':0.92,'orient':150.0},
    'CWS': {'name':'Guaranteed Rate Field',        'lat':41.8299,'lon':-87.6338,'factor':1.12,'orient':127.0},
    'KC':  {'name':'Kauffman Stadium',             'lat':39.0517,'lon':-94.4803,'factor':0.85,'orient':46.0},
    'MIN': {'name':'Target Field',                 'lat':44.9817,'lon':-93.2776,'factor':1.01,'orient':129.0},
    'HOU': {'name':'Minute Maid Park',             'lat':29.7572,'lon':-95.3556,'factor':1.18,'orient':343.0},
    'LAA': {'name':'Angel Stadium',                'lat':33.8003,'lon':-117.8827,'factor':1.05,'orient':44.0},
    'OAK': {'name':'Oakland Coliseum',             'lat':37.7516,'lon':-122.2005,'factor':0.90,'orient':55.0},
    'SEA': {'name':'T-Mobile Park',                'lat':47.5914,'lon':-122.3325,'factor':0.94,'orient':49.0},
    'TEX': {'name':'Globe Life Field',             'lat':32.7473,'lon':-97.0832,'factor':1.00,'orient':30.0},
    'ATL': {'name':'Truist Park',                  'lat':33.8907,'lon':-84.4676,'factor':1.05,'orient':145.0},
    'MIA': {'name':'loanDepot Park',               'lat':25.7784,'lon':-80.2197,'factor':0.87,'orient':128.0},
    'NYM': {'name':'Citi Field',                   'lat':40.7571,'lon':-73.8458,'factor':0.97,'orient':13.0},
    'PHI': {'name':'Citizens Bank Park',           'lat':39.9058,'lon':-75.1666,'factor':1.10,'orient':9.0},
    'WSH': {'name':'Nationals Park',               'lat':38.8730,'lon':-77.0074,'factor':1.02,'orient':28.0},
    'CHC': {'name':'Wrigley Field',                'lat':41.9483,'lon':-87.6555,'factor':1.08,'orient':37.0},
    'CIN': {'name':'Great American Ball Park',     'lat':39.0970,'lon':-84.5066,'factor':1.18,'orient':122.0},
    'MIL': {'name':'American Family Field',        'lat':43.0280,'lon':-87.9712,'factor':1.08,'orient':129.0},
    'PIT': {'name':'PNC Park',                     'lat':40.4468,'lon':-80.0061,'factor':0.93,'orient':116.0},
    'STL': {'name':'Busch Stadium',                'lat':38.6226,'lon':-90.1928,'factor':0.95,'orient':62.0},
    'ARI': {'name':'Chase Field',                  'lat':33.4452,'lon':-112.0667,'factor':1.04,'orient':0.0},
    'COL': {'name':'Coors Field',                  'lat':39.7561,'lon':-104.9941,'factor':1.35,'orient':4.0},
    'LAD': {'name':'Dodger Stadium',               'lat':34.0739,'lon':-118.2400,'factor':0.98,'orient':26.0},
    'SD':  {'name':'Petco Park',                   'lat':32.7076,'lon':-117.1569,'factor':0.94,'orient':0.0},
    'SF':  {'name':'Oracle Park',                  'lat':37.7786,'lon':-122.3893,'factor':0.90,'orient':85.0},
}

# Team codes mapping
TEAM_CODES = {
    'Angels': 'LAA', 'Astros': 'HOU', 'Athletics': 'OAK', 'Blue Jays': 'TOR',
    'Braves': 'ATL', 'Brewers': 'MIL', 'Cardinals': 'STL', 'Cubs': 'CHC',
    'D-backs': 'ARI', 'Diamondbacks': 'ARI', 'Dodgers': 'LAD', 'Giants': 'SF',
    'Guardians': 'CLE', 'Indians': 'CLE', 'Mariners': 'SEA', 'Marlins': 'MIA',
    'Mets': 'NYM', 'Nationals': 'WSH', 'Orioles': 'BAL', 'Padres': 'SD',
    'Phillies': 'PHI', 'Pirates': 'PIT', 'Rangers': 'TEX', 'Rays': 'TB',
    'Red Sox': 'BOS', 'Reds': 'CIN', 'Rockies': 'COL', 'Royals': 'KC',
    'Tigers': 'DET', 'Twins': 'MIN', 'White Sox': 'CWS', 'Yankees': 'NYY'
}

# Weight factors for HR prediction - rebalanced to maintain proper scaling
WEIGHTS = {
    # Core metrics - keep these strong
    'recent_hr_rate': 0.10,            # Recent 7-10 day HR rate (slightly reduced)
    'season_hr_rate': 0.07,            # Season HR rate (unchanged - foundational)
    'ballpark_factor': 0.05,           # Ballpark HR factor (slightly reduced)
    'pitcher_hr_allowed': 0.06,        # Pitcher HR/9 rate (slightly reduced)
    
    # Contact quality metrics - consolidated influence
    'barrel_pct': 0.05,                # Barrel percentage (reduced)
    'exit_velocity': 0.04,             # Exit velocity (reduced)
    'hard_hit_pct': 0.04,              # Hard hit % (reduced)
    'launch_angle': 0.03,              # Launch angle (reduced)
    
    # Batted ball direction metrics - consolidated
    'pull_pct': 0.04,                  # Pull percentage (reduced)
    'fly_ball_rate': 0.02,             # Fly ball rate (unchanged - already small)
    'hr_fb_ratio': 0.03,               # HR to fly ball ratio (unchanged)
    
    # Matchup factors - slightly reduced
    'platoon_advantage': 0.03,         # Platoon advantage (unchanged)
    'vs_pitch_type': 0.02,             # Batter vs pitch type (reduced)
    'pitcher_gb_fb_ratio': 0.02,       # Pitcher ground ball to fly ball ratio (reduced)
    'pitcher_workload': 0.02,          # Pitcher workload/fatigue (unchanged)
    'batter_vs_pitcher': 0.03,         # Historical matchup (reduced)
    
    # Contextual factors
    'weather_factor': 0.03,            # Weather conditions (reduced)
    'home_away_split': 0.02,           # Home/Away splits (reduced)
    'hot_cold_streak': 0.04,           # Hot/cold streak (reduced)
    
    # Advanced metrics
    'xISO': 0.06,                      # Expected Isolated Power (slightly reduced)
    'xwOBA': 0.05,                     # Expected wOBA (reduced)
    
    # New threshold-based factors
    'slg_factor': 0.05,                # SLG threshold (reduced)
    'iso_factor': 0.05,                # ISO threshold (reduced)
    'l15_barrel_factor': 0.04,         # Last 15 days barrel% threshold (reduced)
    'l15_ev_factor': 0.04,             # Last 15 days exit velo threshold (reduced)
    'barrel_rate_factor': 0.04,        # Barrel rate threshold (reduced)
    'exit_velo_factor': 0.04,          # Exit velo threshold (reduced)
    'hr_pct_factor': 0.04,             # HR% threshold (reduced)
    
    # New complex metrics
    'hard_hit_distance': 0.05,         # Hard hit distance factor
    'pitch_specific': 0.04,            # Pitch-specific performance
    'spray_angle': 0.04,               # Spray angle/pull vs oppo power
    'zone_contact': 0.04,              # Zone location contact quality
    'park_specific': 0.04              # Park-specific performance
}

class MLBHomeRunPredictor:
    def __init__(self):
        self.today = datetime.datetime.now().strftime('%Y-%m-%d')
        self.today_dt = datetime.datetime.now()
        self.early_run = self.today_dt.hour < 12
        self.games = None
        self.lineups = {}
        self.probable_pitchers = {}
        self.weather_data = {}
        self.player_stats = {}
        self.pitcher_stats = {}
        self.recent_player_stats = {}
        self.recent_pitcher_stats = {}
        
        logger.info(f"Initializing HR predictor for {self.today} - {'Early' if self.early_run else 'Midday'} run")
        
    def fetch_games(self):
        """Fetch today's games using MLB Stats API"""
        try:
            # Get today's schedule from MLB Stats API
            schedule = statsapi.schedule(date=self.today)
            
            # Create a list to store game data
            games_list = []
            
            # Process each game in the schedule
            for game in schedule:
                # Skip if game is already completed or in progress
                if game['status'] not in ['Scheduled', 'Pre-Game', 'Warmup']:
                    continue
                
                # Get team codes
                home_team = self.convert_mlb_team_to_code(game['home_name'])
                away_team = self.convert_mlb_team_to_code(game['away_name'])
                
                # Skip if we couldn't determine both teams
                if not home_team or not away_team:
                    continue
                
                # Create game ID
                game_id = f"{home_team}_{away_team}_{self.today}"
                
                # Add game to our list
                game_data = {
                    'game_id': game_id,
                    'date': self.today,
                    'home_team': home_team,
                    'away_team': away_team,
                    'home_team_name': game['home_name'],
                    'away_team_name': game['away_name'],
                    'ballpark': game['venue_name'],
                    'ballpark_factor': BALLPARKS[home_team]['factor'] if home_team in BALLPARKS else 1.0,
                    'ballpark_lat': BALLPARKS[home_team]['lat'] if home_team in BALLPARKS else 0,
                    'ballpark_lon': BALLPARKS[home_team]['lon'] if home_team in BALLPARKS else 0,
                    'ballpark_orient': BALLPARKS[home_team]['orient'] if home_team in BALLPARKS else 0,
                    'game_time': game['game_datetime'],
                    'game_id_mlb': game['game_id']  # Store MLB game ID for later use
                }
                
                games_list.append(game_data)
            
            # Convert to DataFrame
            self.games = pd.DataFrame(games_list)
            
            if self.games.empty:
                logger.warning("No upcoming games found for today")
                return False
                
            logger.info(f"Found {len(self.games)} upcoming games for today")
            return True
            
        except Exception as e:
            logger.error(f"Error fetching games: {e}")
            return False

    def convert_mlb_team_to_code(self, team_name):
        """Convert MLB API team name to our team code format"""
        # Direct mappings for MLB API team names
        mlb_team_mappings = {
            'Angels': 'LAA', 'Astros': 'HOU', 'Athletics': 'OAK', 'Blue Jays': 'TOR',
            'Braves': 'ATL', 'Brewers': 'MIL', 'Cardinals': 'STL', 'Cubs': 'CHC',
            'D-backs': 'ARI', 'Diamondbacks': 'ARI', 'Dodgers': 'LAD', 'Giants': 'SF',
            'Guardians': 'CLE', 'Indians': 'CLE', 'Mariners': 'SEA', 'Marlins': 'MIA',
            'Mets': 'NYM', 'Nationals': 'WSH', 'Orioles': 'BAL', 'Padres': 'SD',
            'Phillies': 'PHI', 'Pirates': 'PIT', 'Rangers': 'TEX', 'Rays': 'TB',
            'Red Sox': 'BOS', 'Reds': 'CIN', 'Rockies': 'COL', 'Royals': 'KC',
            'Tigers': 'DET', 'Twins': 'MIN', 'White Sox': 'CWS', 'Yankees': 'NYY'
        }
        
        # Check direct match
        if team_name in mlb_team_mappings:
            return mlb_team_mappings[team_name]
            
        # Try partial match
        for name, code in mlb_team_mappings.items():
            if team_name.lower() in name.lower() or name.lower() in team_name.lower():
                return code
                
        logger.warning(f"Couldn't find team code for: {team_name}")
        return None
        
    def get_team_name(self, team_code):
        """Convert team code to team name"""
        for name, code in TEAM_CODES.items():
            if code == team_code:
                return name
                
        return "Unknown"
        
    def fetch_weather_data(self):
        """Fetch weather data for each ballpark"""
        for _, game in self.games.iterrows():
            try:
                lat = game['ballpark_lat']
                lon = game['ballpark_lon']
                
                if lat == 0 or lon == 0:
                    logger.warning(f"No coordinates for {game['ballpark']}")
                    self.weather_data[game['game_id']] = {
                        'temp': 72,  # Default temperature
                        'humidity': 50,  # Default humidity
                        'wind_speed': 0,  # Default wind speed
                        'wind_deg': 0  # Default wind direction
                    }
                    continue
                    
                # Check if ballpark is a dome (Tropicana Field, etc.)
                if game['home_team'] == 'TB':  # Tropicana Field is a dome
                    self.weather_data[game['game_id']] = {
                        'temp': 72,  # Default dome temperature
                        'humidity': 50,  # Default dome humidity
                        'wind_speed': 0,  # No wind in dome
                        'wind_deg': 0  # No wind direction in dome
                    }
                    continue
                    
                # Call OpenWeather API
                url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OPENWEATHER_API}&units=imperial"
                response = requests.get(url)
                data = response.json()
                
                if response.status_code == 200:
                    self.weather_data[game['game_id']] = {
                        'temp': data['main']['temp'],
                        'humidity': data['main']['humidity'],
                        'wind_speed': data['wind']['speed'],
                        'wind_deg': data['wind']['deg'] if 'deg' in data['wind'] else 0
                    }
                    logger.info(f"Weather for {game['ballpark']}: {self.weather_data[game['game_id']]}")
                else:
                    logger.warning(f"Weather API error for {game['ballpark']}: {data.get('message', 'Unknown error')}")
                    # Use default values
                    self.weather_data[game['game_id']] = {
                        'temp': 72,
                        'humidity': 50,
                        'wind_speed': 0,
                        'wind_deg': 0
                    }
                    
                # Avoid rate limiting
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error fetching weather for {game['ballpark']}: {e}")
                # Use default values
                self.weather_data[game['game_id']] = {
                    'temp': 72,
                    'humidity': 50,
                    'wind_speed': 0,
                    'wind_deg': 0
                }

    def filter_games(self, game_ids):
        """Filter games to only include specific game IDs"""
        if self.games is not None and not self.games.empty:
            self.games = self.games[self.games['game_id'].isin(game_ids)]
            # Also filter lineups and probable pitchers
            filtered_lineups = {k: v for k, v in self.lineups.items() if k in game_ids}
            filtered_pitchers = {k: v for k, v in self.probable_pitchers.items() if k in game_ids}
            self.lineups = filtered_lineups
            self.probable_pitchers = filtered_pitchers
            return True
        return False
                
    def fetch_lineups_and_pitchers(self):
        """Fetch lineups and probable pitchers for today's games using external function"""
        # Call the external function and store the results
        self.lineups, self.probable_pitchers = fetch_lineups_and_pitchers(
            games=self.games,
            early_run=self.early_run
        )
        
        # Log the results
        logger.info(f"Fetched lineups and pitchers for {len(self.lineups)} games")
        
        # Return success
        return len(self.lineups) > 0
                
                
    def fetch_player_stats(self):
        """Fetch player stats using external function"""
        # Get player names from lineups
        player_names = get_player_names_from_lineups(self.lineups)
        
        # Call the external function and store the results
        self.player_stats, self.recent_player_stats = fetch_player_stats(player_names)
        
        # Log the results
        logger.info(f"Fetched stats for {len(self.player_stats)} players")
        
        # Return success
        return len(self.player_stats) > 0
            
    def set_default_player_stats(self, player_name):
        """Set default stats for a player when data cannot be fetched"""
        # Set default values for season stats
        self.player_stats[player_name] = {
            'games': 0, 'hr': 0, 'ab': 0, 'pa': 0, 'hr_per_game': 0, 
            'hr_per_pa': 0, 'pull_pct': 0, 'fb_pct': 0, 'hard_pct': 0,
            'barrel_pct': 0, 'exit_velo': 0, 'launch_angle': 0, 'bats': 'Unknown',
            'hard_hit_pct': 0, 'hr_fb_ratio': 0,
            'vs_fastball': 1.0, 'vs_breaking': 1.0, 'vs_offspeed': 1.0,
            'home_factor': 1.0, 'road_factor': 1.0,
            'hot_cold_streak': 1.0, 'streak_duration': 0,
            'batter_history': {},
            'xwOBA': 0.320, 'xISO': 0.150  # League average defaults
        }
        
        # Set default values for recent stats
        self.recent_player_stats[player_name] = {
            'games': 0, 'hr': 0, 'pa': 0, 'hr_per_pa': 0, 'hr_per_game': 0,
            'barrel_pct': 0, 'exit_velo': 0, 'launch_angle': 0,
            'pull_pct': 0, 'fb_pct': 0, 'hard_pct': 0, 'hard_hit_pct': 0,
            'hr_fb_ratio': 0, 'vs_fastball': 1.0, 'vs_breaking': 1.0, 'vs_offspeed': 1.0,
            'home_factor': 1.0, 'road_factor': 1.0,
            'hot_cold_streak': 1.0, 'streak_duration': 0,
            'xwOBA': 0.320, 'xISO': 0.150  # League average defaults
        }

    def fetch_pitcher_stats(self):
        """Fetch pitcher stats using external function"""
        # Get pitcher names from probable pitchers
        pitcher_names = get_pitcher_names_from_probable_pitchers(self.probable_pitchers)
        
        # Call the external function and store the results
        self.pitcher_stats, self.recent_pitcher_stats = fetch_pitcher_stats(pitcher_names)
        
        # Log the results
        logger.info(f"Fetched stats for {len(self.pitcher_stats)} pitchers")
        
        # Return success
        return len(self.pitcher_stats) > 0
    
            
    def set_default_pitcher_stats(self, pitcher_name):
        """Set default stats for a pitcher when data cannot be fetched"""
        # Set default values for season stats
        self.pitcher_stats[pitcher_name] = {
            'games': 0, 'ip': 0, 'hr': 0, 'hr_per_9': 0, 
            'fb_pct': 0.35, 'gb_pct': 0.45, 'hard_pct': 0.30, 'barrel_pct': 0.05, 
            'exit_velo': 88, 'throws': 'Unknown', 'gb_fb_ratio': 1.0,
            'fastball_pct': 0.60, 'breaking_pct': 0.25, 'offspeed_pct': 0.15,
            'recent_workload': 0
        }
        
        # Set default values for recent stats
        self.recent_pitcher_stats[pitcher_name] = {
            'games': 0, 'ip': 0, 'hr': 0, 'hr_per_9': 0,
            'barrel_pct': 0.05, 'exit_velo': 88, 'fb_pct': 0.35, 
            'gb_pct': 0.45, 'hard_pct': 0.30, 'gb_fb_ratio': 1.0,
            'recent_workload': 0
        }

    def calculate_platoon_advantage(self, batter, pitcher):
        """Calculate platoon advantage based on batter and pitcher handedness"""
        try:
            # Get batter and pitcher handedness
            batter_hand = self.player_stats.get(batter, {}).get('bats', 'Unknown')
            pitcher_hand = self.pitcher_stats.get(pitcher, {}).get('throws', 'Unknown')
            
            # If either handedness is unknown, return neutral factor
            if batter_hand == 'Unknown' or pitcher_hand == 'Unknown':
                return 1.0
                
            # Switch hitters have advantage against all pitchers
            if batter_hand == 'S':
                return 1.15  # 15% advantage
                
            # Right-handed batters have advantage against left-handed pitchers
            if batter_hand == 'R' and pitcher_hand == 'L':
                return 1.10  # 10% advantage
                
            # Left-handed batters have advantage against right-handed pitchers
            if batter_hand == 'L' and pitcher_hand == 'R':
                return 1.12  # 12% advantage
                
            # Same-handed matchup (slight disadvantage)
            return 0.95  # 5% disadvantage
            
        except Exception as e:
            logger.error(f"Error calculating platoon advantage for {batter} vs {pitcher}: {e}")
            return 1.0  # Default neutral factor

    def integrate_savant_data(self):
        """Integrate Baseball Savant data into existing stats"""
        logger.info("Integrating Baseball Savant data")
        
        # Get player and pitcher names
        player_names = get_player_names_from_lineups(self.lineups)
        pitcher_names = get_pitcher_names_from_probable_pitchers(self.probable_pitchers)

        # Get recent data (last 15 days)
        batter_savant, pitcher_savant = get_savant_data(player_names, pitcher_names)
        
        # Get seasonal data for more statistical significance
        batter_season, pitcher_season = get_seasonal_data(player_names, pitcher_names)
        
        # Integrate data (prioritize recent data, fall back to seasonal)
        for player_name in self.player_stats:
            # Get recent data if available, otherwise use seasonal
            savant_data = batter_savant.get(player_name, batter_season.get(player_name, {}))
            
            if savant_data:
                # Update spray angle data
                spray_data = savant_data.get('spray_angle', {})
                self.player_stats[player_name]['spray_angle'] = {
                    'pull_pct': spray_data.get('pull_pct', self.player_stats[player_name].get('pull_pct', 0.4)),
                    'center_pct': spray_data.get('center_pct', 0.33),
                    'oppo_pct': spray_data.get('oppo_pct', 0.27),
                    'pull_slg': spray_data.get('pull_slg', 0.5),
                    'center_slg': spray_data.get('center_slg', 0.5),
                    'oppo_slg': spray_data.get('oppo_slg', 0.5)
                }
                
                # Update zone contact data
                zone_data = savant_data.get('zone_contact', {})
                self.player_stats[player_name]['zone_contact'] = {
                    'up_barrel_pct': zone_data.get('up_barrel_pct', 0.05),
                    'middle_barrel_pct': zone_data.get('middle_barrel_pct', 0.05),
                    'down_barrel_pct': zone_data.get('down_barrel_pct', 0.05),
                    'in_barrel_pct': zone_data.get('in_barrel_pct', 0.05),
                    'out_barrel_pct': zone_data.get('out_barrel_pct', 0.05)
                }
                
                logger.info(f"Updated Savant data for batter: {player_name}")
                
                # NEW CODE: Check if player is in away games and add ballpark-specific data
                for _, game in self.games.iterrows():
                    game_id = game['game_id']
                    home_team = game['home_team']
                    
                    # Check if player is in this game
                    for lineup_game_id, lineup in self.lineups.items():
                        if game_id == lineup_game_id:
                            if player_name in lineup.get('home', []):
                                # Player is playing in their home park - no need for ballpark analysis
                                break
                            elif player_name in lineup.get('away', []):
                                # Player is visiting - check their history in this ballpark
                                ballpark_data = get_ballpark_data(player_name)
                                
                                # Get this ballpark's name
                                ballpark_name = game.get('ballpark', '')
                                
                                if ballpark_name in ballpark_data:
                                    # Add ballpark-specific performance
                                    self.player_stats[player_name]['ballpark_history'] = ballpark_data[ballpark_name]
                                    logger.info(f"Added ballpark history for {player_name} in {ballpark_name}")
        
        # Integrate pitcher data
        for pitcher_name, savant_data in pitcher_savant.items():
            if pitcher_name in self.pitcher_stats:
                # Update zone profile
                zone_profile = savant_data.get('zone_profile', {})
                self.pitcher_stats[pitcher_name]['zone_profile'] = zone_profile
                
                # Update primary tendency
                self.pitcher_stats[pitcher_name]['primary_tendency'] = savant_data.get('primary_tendency', 'mixed')
                
                logger.info(f"Updated Savant data for pitcher: {pitcher_name}")

    def calculate_streak_factor(self, batter):
        """Calculate hot/cold streak factor based on recent performance"""
        try:
            # Get recent streak information
            hot_cold_streak = self.recent_player_stats.get(batter, {}).get('hot_cold_streak', 1.0)
            streak_duration = self.recent_player_stats.get(batter, {}).get('streak_duration', 0)
            
            # Weight the streak based on duration
            # Very short streaks (1-2 games) have minimal impact
            # Longer streaks (5+ games) have more significant impact
            if streak_duration <= 2:
                # Short streak - reduce impact
                streak_factor = 1.0 + (hot_cold_streak - 1.0) * 0.5
            elif streak_duration >= 5:
                # Long streak - full impact
                streak_factor = hot_cold_streak
            else:
                # Medium streak - partial impact
                streak_factor = 1.0 + (hot_cold_streak - 1.0) * 0.75
                
            return streak_factor
            
        except Exception as e:
            logger.error(f"Error calculating streak factor for {batter}: {e}")
            return 1.0  # Default neutral factor

    def calculate_pitcher_matchup(self, batter, pitcher):
        """Calculate matchup vs pitcher's main pitch types"""
        try:
            # Get batter's performance vs different pitch types
            vs_fastball = self.player_stats.get(batter, {}).get('vs_fastball', 1.0)
            vs_breaking = self.player_stats.get(batter, {}).get('vs_breaking', 1.0)
            vs_offspeed = self.player_stats.get(batter, {}).get('vs_offspeed', 1.0)
            
            # Get pitcher's pitch mix
            fastball_pct = self.pitcher_stats.get(pitcher, {}).get('fastball_pct', 0.6)
            breaking_pct = self.pitcher_stats.get(pitcher, {}).get('breaking_pct', 0.25)
            offspeed_pct = self.pitcher_stats.get(pitcher, {}).get('offspeed_pct', 0.15)
            
            # Weight matchup by pitcher's usage
            matchup_factor = (
                vs_fastball * fastball_pct +
                vs_breaking * breaking_pct +
                vs_offspeed * offspeed_pct
            )
            
            return matchup_factor
            
        except Exception as e:
            logger.error(f"Error calculating pitcher matchup for {batter} vs {pitcher}: {e}")
            return 1.0  # Default neutral factor

    
    def calculate_weather_factor(self, game_id, player_name):
        """Calculate weather factor for HR probability"""
        try:
            # Get weather data for the game
            weather = self.weather_data.get(game_id, {})
            
            # Get ballpark data
            game = self.games[self.games['game_id'] == game_id].iloc[0]
            ballpark_orient = game['ballpark_orient']
            
            # Default factor
            weather_factor = 1.0
            
            # Temperature factor (higher temp = more HRs)
            # Based on research showing ~1% increase per degree F above 70
            temp = weather.get('temp', 72)
            temp_factor = 1.0 + (temp - 70) * 0.01 if temp > 70 else 1.0 - (70 - temp) * 0.005
            
            # Wind factor
            wind_speed = weather.get('wind_speed', 0)
            wind_deg = weather.get('wind_deg', 0)
            
            # If significant wind
            if wind_speed > 5:
                # Calculate the relative angle between wind direction and ballpark orientation
                # Wind direction: 0 = from North, 90 = from East, etc.
                # We want to find if wind is blowing out (tailwind for HR)
                
                # Convert ballpark orientation to the opposite direction (wind coming from)
                park_wind_direction = (ballpark_orient + 180) % 360
                
                # Calculate the difference between wind direction and park direction
                wind_angle_diff = min(abs(wind_deg - park_wind_direction), 
                                      360 - abs(wind_deg - park_wind_direction))
                
                # If wind is blowing out (within 45 degrees of park orientation)
                if wind_angle_diff < 45:
                    # Tailwind - increases HR probability
                    wind_factor = 1.0 + (wind_speed * 0.02)  # 2% increase per mph
                # If wind is blowing in (within 45 degrees of opposite direction)
                elif wind_angle_diff > 135:
                    # Headwind - decreases HR probability
                    wind_factor = 1.0 - (wind_speed * 0.02)  # 2% decrease per mph
                # If wind is crosswind
                else:
                    # Crosswind - minimal effect
                    wind_factor = 1.0
                    
                # Cap the wind factor within reasonable limits
                wind_factor = max(0.7, min(1.5, wind_factor))
            else:
                # Minimal wind effect
                wind_factor = 1.0
                
            # Humidity factor (lower humidity = more HRs)
            # Based on research showing humid air reduces HR distance
            humidity = weather.get('humidity', 50)
            humidity_factor = 1.0 - (humidity - 50) * 0.001 if humidity > 50 else 1.0 + (50 - humidity) * 0.001
            
            # Combine factors
            weather_factor = temp_factor * wind_factor * humidity_factor
            
            # Cap within reasonable limits
            weather_factor = max(0.7, min(1.5, weather_factor))
            
            return weather_factor
            
        except Exception as e:
            logger.error(f"Error calculating weather factor for {game_id}, {player_name}: {e}")
            return 1.0  # Default neutral factor
            
    def calculate_batter_vs_pitcher(self, batter, pitcher):
        """Calculate batter vs pitcher historical matchup factor"""
        try:
            # In a real implementation, you would use MLB's API to get actual batter vs pitcher stats
            # For this example, we'll simulate the matchup with random factors
            
            # See if we already have this matchup calculated
            if pitcher in self.player_stats.get(batter, {}).get('batter_history', {}):
                return self.player_stats[batter]['batter_history'][pitcher]
                
            # Simulate a history based on some PA threshold
            pa_threshold = np.random.randint(0, 20)  # Random number of PA history
            
            if pa_threshold < 3:
                # No significant history
                matchup_factor = 1.0
            else:
                # Some history exists, generate a random factor
                # The more PA, the more significant the factor can be
                max_deviation = min(0.5, pa_threshold * 0.03)  # Max 50% deviation
                matchup_factor = np.random.normal(1.0, max_deviation)
                
                # Cap within reasonable limits
                matchup_factor = max(0.5, min(1.5, matchup_factor))
                
            # Store for future use
            if batter in self.player_stats:
                if 'batter_history' not in self.player_stats[batter]:
                    self.player_stats[batter]['batter_history'] = {}
                self.player_stats[batter]['batter_history'][pitcher] = matchup_factor
                
            return matchup_factor
            
        except Exception as e:
            logger.error(f"Error calculating batter vs pitcher history for {batter} vs {pitcher}: {e}")
            return 1.0  # Default neutral factor
            
    def calculate_home_away_factor(self, batter, is_home_team):
        """Calculate home/away split factor"""
        try:
            # Get home and road factors
            home_factor = self.recent_player_stats.get(batter, {}).get('home_factor', 1.0)
            road_factor = self.recent_player_stats.get(batter, {}).get('road_factor', 1.0)
            
            # Return the appropriate factor based on home/away status
            return home_factor if is_home_team else road_factor
            
        except Exception as e:
            logger.error(f"Error calculating home/away factor for {batter}: {e}")
            return 1.0  # Default neutral factor
            
    def calculate_xwOBA(self, batter):
        """Calculate expected wOBA based on quality of contact metrics"""
        try:
            # Get quality of contact metrics
            exit_velo = self.player_stats.get(batter, {}).get('exit_velo', 0)
            launch_angle = self.player_stats.get(batter, {}).get('launch_angle', 0)
            barrel_pct = self.player_stats.get(batter, {}).get('barrel_pct', 0)
            hard_hit_pct = self.player_stats.get(batter, {}).get('hard_hit_pct', 0)
            
            # In a real implementation, we would use actual Statcast data and models
            # Here we'll simulate xwOBA based on our available metrics
            
            # Baseline league average wOBA (roughly)
            base_woba = 0.320
            
            # Adjust based on quality of contact metrics
            # These are rough approximations based on general relationships
            
            # Exit velocity premium (every mph above 87 adds to xwOBA)
            exit_velo_adj = (exit_velo - 87) * 0.003 if exit_velo > 87 else (exit_velo - 87) * 0.002
            
            # Launch angle adjustment (optimal range around 10-30 degrees)
            if 10 <= launch_angle <= 30:
                # Optimal line drive / fly ball range
                angle_diff = min(abs(launch_angle - 20), 10)  # Distance from optimal 20 degrees
                launch_angle_adj = 0.015 * (1.0 - angle_diff / 10)
            elif 0 <= launch_angle < 10:
                # Ground balls (low value)
                launch_angle_adj = -0.020 + (launch_angle * 0.003)
            elif 30 < launch_angle <= 45:
                # High fly balls (decreasing value)
                launch_angle_adj = 0.010 - ((launch_angle - 30) * 0.003)
            else:
                # Extreme angles (pop-ups or choppers)
                launch_angle_adj = -0.025
                
            # Barrel and hard hit adjustments
            barrel_adj = barrel_pct * 0.400  # Barrels strongly influence xwOBA
            hard_hit_adj = hard_hit_pct * 0.150  # Hard hit balls also boost xwOBA
            
            # Compute final xwOBA
            xwoba = base_woba + exit_velo_adj + launch_angle_adj + barrel_adj + hard_hit_adj
            
            # Cap within reasonable limits
            return max(0.200, min(0.500, xwoba))
            
        except Exception as e:
            logger.error(f"Error calculating xwOBA for {batter}: {e}")
            return 0.320  # Return league average as fallback
            
    def calculate_xISO(self, batter):
        """Calculate expected ISO (Isolated Power) based on batted ball metrics"""
        try:
            # Get relevant metrics
            exit_velo = self.player_stats.get(batter, {}).get('exit_velo', 0)
            launch_angle = self.player_stats.get(batter, {}).get('launch_angle', 0)
            barrel_pct = self.player_stats.get(batter, {}).get('barrel_pct', 0)
            hard_hit_pct = self.player_stats.get(batter, {}).get('hard_hit_pct', 0)
            pull_pct = self.player_stats.get(batter, {}).get('pull_pct', 0)
            hr_fb_ratio = self.player_stats.get(batter, {}).get('hr_fb_ratio', 0)
            
            # In a real implementation, we would use actual Statcast data and models
            # Here we'll simulate xISO based on our available metrics
            
            # Baseline league average ISO (roughly)
            base_iso = 0.150
            
            # Exit velocity is highly correlated with ISO
            # For every 1 mph above 88, ISO increases by ~0.007
            exit_velo_adj = (exit_velo - 88) * 0.007 if exit_velo > 88 else (exit_velo - 88) * 0.005
            
            # Launch angle optimization - ideal for power is 15-35 degrees
            if 15 <= launch_angle <= 35:
                # Optimal launch angle for power
                angle_diff = min(abs(launch_angle - 25), 10)  # Distance from optimal 25 degrees
                launch_angle_adj = 0.040 * (1.0 - angle_diff / 10)
            elif 0 <= launch_angle < 15:
                # Too low (ground balls, low line drives)
                launch_angle_adj = -0.050 + (launch_angle * 0.005)
            elif 35 < launch_angle <= 50:
                # High fly balls (still can be home runs but less efficient)
                launch_angle_adj = 0.020 - ((launch_angle - 35) * 0.002)
            else:
                # Extreme angles (pop-ups or choppers)
                launch_angle_adj = -0.060
                
            # Barrel and hard hit adjustments - very strong influence on ISO
            barrel_adj = barrel_pct * 0.750  # Barrels are extremely indicative of power
            hard_hit_adj = hard_hit_pct * 0.250  # Hard hit balls boost ISO
            
            # Pull tendency adjustment - pull hitters generate more power
            pull_adj = (pull_pct - 0.40) * 0.150 if pull_pct > 0.40 else 0
            
            # HR/FB adjustment - indicates ability to convert fly balls to HRs
            hr_fb_adj = hr_fb_ratio * 0.300
            
            # Compute final xISO
            xiso = base_iso + exit_velo_adj + launch_angle_adj + barrel_adj + hard_hit_adj + pull_adj + hr_fb_adj
            
            # Cap within reasonable limits
            return max(0.050, min(0.400, xiso))
            
        except Exception as e:
            logger.error(f"Error calculating xISO for {batter}: {e}")
            return 0.150  # Return league average as fallback
            
    def calculate_workload_factor(self, pitcher):
        """Calculate pitcher workload factor (fatigue effect on HR probability)"""
        try:
            # Get recent workload
            recent_workload = self.pitcher_stats.get(pitcher, {}).get('recent_workload', 0)
            
            # Pitchers with higher recent workload are more susceptible to HRs
            # Thresholds:
            # < 50 pitches in last 7 days: well-rested (factor < 1.0)
            # 50-100 pitches: normal (factor = 1.0)
            # > 100 pitches: potential fatigue (factor > 1.0)
            # > 200 pitches: significant fatigue (factor >> 1.0)
            
            if recent_workload < 50:
                # Well-rested
                return max(0.8, 1.0 - (50 - recent_workload) * 0.004)
            elif recent_workload <= 100:
                # Normal workload
                return 1.0
            else:
                # Elevated workload / potential fatigue
                return min(1.5, 1.0 + (recent_workload - 100) * 0.003)
                
        except Exception as e:
            logger.error(f"Error calculating workload factor for {pitcher}: {e}")
            return 1.0  # Default neutral factor

    def get_pitcher_primary_pitch(self, pitcher):
        """Determine primary pitch type for a pitcher"""
        pitcher_data = self.pitcher_stats.get(pitcher, {})
        
        # Find highest usage pitch
        fastball_pct = pitcher_data.get('fastball_pct', 0.6)
        breaking_pct = pitcher_data.get('breaking_pct', 0.25)
        offspeed_pct = pitcher_data.get('offspeed_pct', 0.15)
        
        # Return the pitch type with highest usage
        if fastball_pct >= breaking_pct and fastball_pct >= offspeed_pct:
            return 'fastball'
        elif breaking_pct >= fastball_pct and breaking_pct >= offspeed_pct:
            return 'breaking'
        else:
            return 'offspeed'

    def is_ballpark_pull_friendly(self, team_code, batter_hand):
        """Determine if ballpark is pull-friendly for this batter's handedness"""
        # Right-handed pull hitters (to left field)
        rhb_pull_friendly = ['NYY', 'HOU', 'BOS', 'CIN', 'CHC', 'COL']
        
        # Left-handed pull hitters (to right field)
        lhb_pull_friendly = ['NYY', 'BAL', 'HOU', 'TEX', 'CIN', 'MIL', 'COL', 'PHI']
        
        if batter_hand == 'R' and team_code in rhb_pull_friendly:
            return True
        elif batter_hand == 'L' and team_code in lhb_pull_friendly:
            return True
        elif batter_hand == 'S':  # Switch hitters get advantage in all pull-friendly parks
            return team_code in rhb_pull_friendly or team_code in lhb_pull_friendly
        
        return False

    def get_pitcher_zone_tendency(self, pitcher):
        """Determine where pitcher tends to locate pitches"""
        pitcher_data = self.pitcher_stats.get(pitcher, {})
        
        # This is a simplified model since we don't have actual pitch location data
        # Use some pitcher characteristics to estimate tendencies
        
        fb_pct = pitcher_data.get('fb_pct', 0.35)
        gb_pct = pitcher_data.get('gb_pct', 0.45)
        throws = pitcher_data.get('throws', 'Unknown')
        
        # Pitchers with high fly ball rates tend to pitch up in the zone
        # Pitchers with high ground ball rates tend to pitch down in the zone
        
        if fb_pct > 0.40:
            return 'up'
        elif gb_pct > 0.50:
            return 'down'
        elif throws == 'L':
            # Left-handed pitchers tend to pitch more outside to righties, inside to lefties
            return 'out'
        elif throws == 'R':
            # Right-handed pitchers have various tendencies
            return 'mixed'
        
        return 'mixed'  # Default

    def analyze_handedness_data(self):
        """Analyze and log handedness data for debugging"""
        bats_values = {}
        throws_values = {}
        
        # Count handedness values in player stats
        for player, stats in self.player_stats.items():
            bats = stats.get('bats', 'Unknown')
            if bats in bats_values:
                bats_values[bats] += 1
            else:
                bats_values[bats] = 1
        
        # Count handedness values in pitcher stats        
        for pitcher, stats in self.pitcher_stats.items():
            throws = stats.get('throws', 'Unknown')
            if throws in throws_values:
                throws_values[throws] += 1
            else:
                throws_values[throws] = 1
        
        logger.info(f"Batter handedness distribution: {bats_values}")
        logger.info(f"Pitcher handedness distribution: {throws_values}")
        
        # Return 'Unknown' percentages for monitoring
        total_batters = sum(bats_values.values())
        total_pitchers = sum(throws_values.values())
        
        unknown_batter_pct = bats_values.get('Unknown', 0) / total_batters if total_batters > 0 else 0
        unknown_pitcher_pct = throws_values.get('Unknown', 0) / total_pitchers if total_pitchers > 0 else 0
        
        return {
            'unknown_batter_pct': unknown_batter_pct,
            'unknown_pitcher_pct': unknown_pitcher_pct
        }
            
    def predict_home_runs(self):
        """Predict HR probability for all players in lineups"""
        hr_predictions = []
        
        for _, game in self.games.iterrows():
            game_id = game['game_id']
            home_team = game['home_team']
            away_team = game['away_team']
            ballpark_factor = game['ballpark_factor']
            
            # Get pitchers
            home_pitcher = self.probable_pitchers.get(game_id, {}).get('home', 'Unknown')
            away_pitcher = self.probable_pitchers.get(game_id, {}).get('away', 'Unknown')
            
            # Process home team batters
            home_batters = self.lineups.get(game_id, {}).get('home', [])
            self._process_team_batters(
                hr_predictions, 
                home_batters, 
                home_team, 
                away_team, 
                away_pitcher, 
                game, 
                game_id, 
                ballpark_factor, 
                is_home_team=True
            )
            
            # Process away team batters
            away_batters = self.lineups.get(game_id, {}).get('away', [])
            self._process_team_batters(
                hr_predictions, 
                away_batters, 
                away_team, 
                home_team, 
                home_pitcher, 
                game, 
                game_id, 
                ballpark_factor, 
                is_home_team=False
            )
                    
        # Convert to DataFrame and sort by HR probability
        predictions_df = pd.DataFrame(hr_predictions)
        if not predictions_df.empty:
            predictions_df = predictions_df.sort_values(by='hr_probability', ascending=False)
            
        return predictions_df

    def _process_team_batters(self, hr_predictions, batters, team, opponent_team, opponent_pitcher, game, game_id, ballpark_factor, is_home_team):
        """Process batters for a team and calculate HR probabilities"""
        for batter in batters:
            # Skip if we don't have stats for this player
            if batter not in self.player_stats:
                continue
            # Skip if player has insufficient data
            if self.player_stats[batter].get('games', 0) < 4:
                logger.info(f"Skipping {batter} - insufficient games played (<4)")
                continue
            # Skip if simulated data
            if self.player_stats[batter].get('is_simulated', False):
                logger.info(f"Skipping {batter} - using simulated data")
                continue
                
            # Calculate HR probability components
            
            # Recent HR rate
            recent_hr_rate = self.recent_player_stats.get(batter, {}).get('hr_per_pa', 0)
            
            # Season HR rate
            season_hr_rate = self.player_stats.get(batter, {}).get('hr_per_pa', 0)
            
            # Pitcher HR allowed rate
            pitcher_hr_rate = self.pitcher_stats.get(opponent_pitcher, {}).get('hr_per_9', 0) / 9  # Per PA
            
            # Weather factor
            weather_factor = self.calculate_weather_factor(game_id, batter)
            
            # Platoon advantage
            platoon_factor = self.calculate_platoon_advantage(batter, opponent_pitcher)
            
            # Barrel percentage (proxy for quality contact)
            barrel_pct = self.player_stats.get(batter, {}).get('barrel_pct', 0)
            
            # Exit velocity - normalize for calculation
            exit_velo_normalized = self.player_stats.get(batter, {}).get('exit_velo', 0) / 100  # Normalize
            
            # Raw exit velocity - for thresholds
            exit_velo = self.player_stats.get(batter, {}).get('exit_velo', 0)
            
            # Fly ball rate
            fly_ball_rate = self.player_stats.get(batter, {}).get('fb_pct', 0)
            
            # Pull percentage (critical for HR)
            pull_pct = self.player_stats.get(batter, {}).get('pull_pct', 0)
            
            # Hard hit percentage
            hard_hit_pct = self.player_stats.get(batter, {}).get('hard_hit_pct', 0)
            
            # Launch angle (optimal range boost)
            launch_angle = self.player_stats.get(batter, {}).get('launch_angle', 0)
            launch_angle_factor = 1.0
            if 20 <= launch_angle <= 40:  # Optimal launch angle range for HRs
                # Peak at around 28-32 degrees
                angle_diff = min(abs(launch_angle - 30), 10)  # How far from optimal 30 degrees
                launch_angle_factor = 1.0 + (1.0 - angle_diff / 10)  # Higher boost closer to optimal
            
            # Pitcher ground ball to fly ball ratio
            pitcher_gb_fb = self.pitcher_stats.get(opponent_pitcher, {}).get('gb_fb_ratio', 1.0)
            # Convert to a factor (lower GB/FB ratio = more fly balls = more HR risk)
            pitcher_gb_fb_factor = 1.0 + (1.0 - min(pitcher_gb_fb, 2.0) / 2.0)
            
            # HR/FB ratio (HR efficiency)
            hr_fb_ratio = self.player_stats.get(batter, {}).get('hr_fb_ratio', 0)
            
            # Batter vs Pitch Type matchup
            pitch_type_matchup = self.calculate_pitcher_matchup(batter, opponent_pitcher)
            
            # Pitcher workload/fatigue
            pitcher_workload = self.calculate_workload_factor(opponent_pitcher)
            
            # Batter vs Pitcher history
            batter_vs_pitcher = self.calculate_batter_vs_pitcher(batter, opponent_pitcher)
            
            # Home/Away split factor
            home_away_factor = self.calculate_home_away_factor(batter, is_home_team)
            
            # Hot/Cold streak factor
            streak_factor = self.calculate_streak_factor(batter)

            # SLG factor (threshold-based)
            slg = self.player_stats.get(batter, {}).get('slg', 0)
            if slg > 0.550:  # Ideal threshold
                slg_factor = 1.4
            elif slg > 0.500:  # Minimum threshold
                slg_factor = 1.2
            else:
                slg_factor = 1.0

            # ISO factor (threshold-based)
            iso = self.player_stats.get(batter, {}).get('iso', 0)
            if iso > 0.300:  # Ideal threshold
                iso_factor = 1.4
            elif iso > 0.250:  # Minimum threshold
                iso_factor = 1.2
            else:
                iso_factor = 1.0

            # L15 Barrel factor
            l15_barrel = self.recent_player_stats.get(batter, {}).get('barrel_pct', 0)
            if l15_barrel > 0.25:  # 25%+ threshold
                l15_barrel_factor = 1.5
            else:
                l15_barrel_factor = 1.0

            # L15 Exit Velocity factor
            l15_ev = self.recent_player_stats.get(batter, {}).get('exit_velo', 0)
            if l15_ev > 95:  # 95+ MPH threshold
                l15_ev_factor = 1.4
            else:
                l15_ev_factor = 1.0

            # Season barrel rate factor
            if barrel_pct > 0.20:  # 20%+ threshold
                barrel_rate_factor = 1.5
            else:
                barrel_rate_factor = 1.0

            # Season exit velocity factor
            if exit_velo > 95:  # 95+ MPH threshold
                exit_velo_factor = 1.4
            else:
                exit_velo_factor = 1.0

            # HR% factor - use hr_per_pa as it's the same metric
            hr_pct = season_hr_rate  # Use existing hr_per_pa as hr_pct
            if hr_pct > 0.10:  # 10%+ threshold
                hr_pct_factor = 1.5
            else:
                hr_pct_factor = 1.0
            
            # Expected ISO
            xiso = self.recent_player_stats.get(batter, {}).get('xISO', 0.150)
            # Convert to a factor (higher xISO = higher HR probability)
            # League average xISO is ~0.150, so normalize around that
            xiso_factor = 1.0 + ((xiso - 0.150) * 4)  # Scale the difference
            
            # Expected wOBA
            xwoba = self.recent_player_stats.get(batter, {}).get('xwOBA', 0.320)
            # Convert to a factor (higher xwOBA = higher overall offensive value)
            # League average xwOBA is ~0.320, so normalize around that
            xwoba_factor = 1.0 + ((xwoba - 0.320) * 2)  # Scale the difference

            # Hard Hit Distance factor
            hard_hit_distance = self.player_stats.get(batter, {}).get('hard_hit_distance', 0)
            if hard_hit_distance > 380:
                hard_hit_distance_factor = 1.4
            elif hard_hit_distance > 350:
                hard_hit_distance_factor = 1.2
            else:
                hard_hit_distance_factor = 1.0

            # Pitch-specific performance factor
            primary_pitch = self.get_pitcher_primary_pitch(opponent_pitcher)
            pitch_specific_data = self.player_stats.get(batter, {}).get('pitch_specific', {})
            pitch_hr_rate = pitch_specific_data.get(f'{primary_pitch}_hr_rate', 0)

            if season_hr_rate > 0:
                pitch_specific_factor = 1.0 + (pitch_hr_rate / season_hr_rate - 1.0) 
            else:
                pitch_specific_factor = 1.0
                
            pitch_specific_factor = max(0.8, min(1.5, pitch_specific_factor))

            # Spray Angle factor
            spray_data = self.player_stats.get(batter, {}).get('spray_angle', {})
            ballpark_pull_friendly = self.is_ballpark_pull_friendly(
                game['home_team'], self.player_stats.get(batter, {}).get('bats', 'R')
            )

            if ballpark_pull_friendly and spray_data.get('pull_pct', 0) > 0.45:
                # Pull hitter in pull-friendly park
                spray_angle_factor = 1.3
            elif not ballpark_pull_friendly and spray_data.get('oppo_pct', 0) > 0.30:
                # Opposite field hitter in opposite-field friendly park
                spray_angle_factor = 1.2
            else:
                spray_angle_factor = 1.0

            # Zone Contact factor
            zone_data = self.player_stats.get(batter, {}).get('zone_contact', {})
            pitcher_zone_tendency = self.get_pitcher_zone_tendency(opponent_pitcher)

            if pitcher_zone_tendency == 'up' and zone_data.get('up_barrel_pct', 0) > 0.15:
                # Batter barrels high pitches well, facing high-ball pitcher
                zone_contact_factor = 1.3
            elif pitcher_zone_tendency == 'down' and zone_data.get('down_barrel_pct', 0) > 0.15:
                # Batter barrels low pitches well, facing low-ball pitcher
                zone_contact_factor = 1.3
            elif pitcher_zone_tendency == 'in' and zone_data.get('in_barrel_pct', 0) > 0.15:
                # Batter barrels inside pitches well
                zone_contact_factor = 1.2
            elif pitcher_zone_tendency == 'out' and zone_data.get('out_barrel_pct', 0) > 0.15:
                # Batter barrels outside pitches well
                zone_contact_factor = 1.2
            else:
                zone_contact_factor = 1.0

            # Park-specific performance
            park_specific_factor = 1.0  # Default
            if game['home_team'] in BALLPARKS:
                # Use the ballpark factor as a base
                park_factor = BALLPARKS[game['home_team']].get('factor', 1.0)
                
                # If batter has above-average power metrics, amplify the park effect
                if self.player_stats.get(batter, {}).get('xISO', 0) > 0.180:
                    park_specific_factor = 1.0 + (park_factor - 1.0) * 1.2
                else:
                    park_specific_factor = 1.0 + (park_factor - 1.0) * 0.8
            
            # Calculate weighted HR probability
            hr_prob = (
                WEIGHTS['recent_hr_rate'] * recent_hr_rate +
                WEIGHTS['season_hr_rate'] * season_hr_rate +
                WEIGHTS['ballpark_factor'] * (ballpark_factor - 1) +  # Convert to modifier
                WEIGHTS['pitcher_hr_allowed'] * pitcher_hr_rate +
                WEIGHTS['weather_factor'] * (weather_factor - 1) +  # Convert to modifier
                WEIGHTS['barrel_pct'] * barrel_pct +
                WEIGHTS['platoon_advantage'] * (platoon_factor - 1) +  # Convert to modifier
                WEIGHTS['exit_velocity'] * exit_velo_normalized +  # Use normalized version
                WEIGHTS['fly_ball_rate'] * fly_ball_rate +
                WEIGHTS['pull_pct'] * pull_pct +
                WEIGHTS['hard_hit_pct'] * hard_hit_pct +
                WEIGHTS['launch_angle'] * (launch_angle_factor - 1) +  # Convert to modifier
                WEIGHTS['pitcher_gb_fb_ratio'] * (pitcher_gb_fb_factor - 1) +  # Convert to modifier
                WEIGHTS['hr_fb_ratio'] * hr_fb_ratio +
                WEIGHTS['vs_pitch_type'] * (pitch_type_matchup - 1) +  # Convert to modifier
                WEIGHTS['pitcher_workload'] * (pitcher_workload - 1) +  # Convert to modifier
                WEIGHTS['batter_vs_pitcher'] * (batter_vs_pitcher - 1) +  # Convert to modifier
                WEIGHTS['home_away_split'] * (home_away_factor - 1) +  # Convert to modifier
                WEIGHTS['hot_cold_streak'] * (streak_factor - 1) +  # Convert to modifier
                WEIGHTS['xISO'] * (xiso_factor - 1) +  # Convert to modifier
                WEIGHTS['xwOBA'] * (xwoba_factor - 1) +  # Convert to modifier
                WEIGHTS['slg_factor'] * (slg_factor - 1) +
                WEIGHTS['iso_factor'] * (iso_factor - 1) +
                WEIGHTS['l15_barrel_factor'] * (l15_barrel_factor - 1) +
                WEIGHTS['l15_ev_factor'] * (l15_ev_factor - 1) +
                WEIGHTS['barrel_rate_factor'] * (barrel_rate_factor - 1) +  # Added barrel rate factor
                WEIGHTS['exit_velo_factor'] * (exit_velo_factor - 1) +  # Added exit velo factor
                WEIGHTS['hr_pct_factor'] * (hr_pct_factor - 1) +
                WEIGHTS['hard_hit_distance'] * (hard_hit_distance_factor - 1) +
                WEIGHTS['pitch_specific'] * (pitch_specific_factor - 1) +
                WEIGHTS['spray_angle'] * (spray_angle_factor - 1) +
                WEIGHTS['zone_contact'] * (zone_contact_factor - 1) +
                WEIGHTS['park_specific'] * (park_specific_factor - 1)
            )
        
        # Apply base rate (league average HR rate is ~3%)
        base_hr_rate = 0.03
        final_hr_prob = base_hr_rate * (1 + hr_prob)
        
        # Cap probability within reasonable limits
        final_hr_prob = max(0.01, min(0.25, final_hr_prob))
        
        # Add prediction
        hr_predictions.append({
            'player': batter,
            'team': team,
            'team_name': game['home_team_name'] if is_home_team else game['away_team_name'],
            'opponent': opponent_team,
            'opponent_name': game['away_team_name'] if is_home_team else game['home_team_name'],
            'opponent_pitcher': opponent_pitcher,
            'ballpark': game['ballpark'],
            'ballpark_factor': ballpark_factor,
            'weather_temp': self.weather_data.get(game_id, {}).get('temp', 0),
            'weather_wind': self.weather_data.get(game_id, {}).get('wind_speed', 0),
            'weather_factor': weather_factor,
            'platoon_advantage': platoon_factor > 1,
            'bats': self.player_stats.get(batter, {}).get('bats', '?'),
            'throws': self.pitcher_stats.get(opponent_pitcher, {}).get('throws', '?'),
            'recent_hr_rate': recent_hr_rate,
            'season_hr_rate': season_hr_rate,
            'pitcher_hr_rate': pitcher_hr_rate,
            'barrel_pct': barrel_pct,
            'exit_velo': exit_velo,  # Use raw exit velo for output
            'launch_angle': launch_angle,
            'pull_pct': pull_pct,
            'hard_hit_pct': hard_hit_pct,
            'pitcher_gb_fb': pitcher_gb_fb,
            'hr_fb_ratio': hr_fb_ratio,
            'pitch_type_matchup': pitch_type_matchup,
            'pitcher_workload': pitcher_workload,
            'batter_vs_pitcher': batter_vs_pitcher,
            'home_away_factor': home_away_factor,
            'streak_factor': streak_factor,
            'xISO': xiso,
            'xwOBA': xwoba,
            'slg': slg,
            'iso': iso,
            'l15_barrel_pct': l15_barrel,
            'l15_exit_velo': l15_ev,
            'hr_pct': hr_pct,  # Using season_hr_rate
            'hard_hit_distance': hard_hit_distance,
            'hard_hit_distance_factor': hard_hit_distance_factor,
            'primary_pitch': primary_pitch,
            'pitch_specific_factor': pitch_specific_factor,
            'spray_angle_factor': spray_angle_factor,
            'zone_contact_factor': zone_contact_factor,
            'park_specific_factor': park_specific_factor,
            'hr_probability': final_hr_prob,
            'game_id': game_id,
            'game_time': game['game_time'],
            'is_home_team': is_home_team
        })
        
    def categorize_predictions(self, predictions_df, top_n=10):
        """Categorize HR predictions into tiers"""
        if predictions_df.empty:
            return {"locks": [], "hot_picks": [], "sleepers": []}
            
        # Get top N predictions
        top_predictions = predictions_df.head(top_n)
        
        # Determine thresholds for categories
        # Locks: Top 15% probability
        # Hot picks: Next 30% probability
        # Sleepers: Remaining players with decent probability
        
        if len(top_predictions) >= 5:
            # For larger sets, use percentiles
            prob_threshold_lock = top_predictions['hr_probability'].quantile(0.85)
            prob_threshold_hot = top_predictions['hr_probability'].quantile(0.55)
            
            locks = top_predictions[top_predictions['hr_probability'] >= prob_threshold_lock]
            hot_picks = top_predictions[(top_predictions['hr_probability'] < prob_threshold_lock) & 
                                       (top_predictions['hr_probability'] >= prob_threshold_hot)]
            sleepers = top_predictions[top_predictions['hr_probability'] < prob_threshold_hot]
        else:
            # For smaller sets, use fixed splits
            # Locks: 1-2 players
            # Hot picks: Next 2-3 players
            # Sleepers: Remaining players
            num_locks = max(1, len(top_predictions) // 5)
            num_hot_picks = max(1, len(top_predictions) // 3)
            
            locks = top_predictions.head(num_locks)
            hot_picks = top_predictions.iloc[num_locks:num_locks+num_hot_picks]
            sleepers = top_predictions.iloc[num_locks+num_hot_picks:]
            
        # Convert to dictionaries for output
        locks_dict = locks.to_dict('records') if not locks.empty else []
        hot_picks_dict = hot_picks.to_dict('records') if not hot_picks.empty else []
        sleepers_dict = sleepers.to_dict('records') if not sleepers.empty else []
        
        return {"locks": locks_dict, "hot_picks": hot_picks_dict, "sleepers": sleepers_dict}
        
    def format_telegram_message(self, categories):
        """Format prediction results for Telegram using external function"""
        return format_telegram_message(
            categories=categories,
            today=self.today,
            early_run=self.early_run
        )

    def send_telegram_message(self, message):
        """Send message via Telegram bot using external function"""
        return send_telegram_message(
            message=message,
            bot_token=BOT_TOKEN,
            chat_id=CHAT_ID
        )
            
    def run(self):
        """Run the HR prediction pipeline"""
        try:
            # Step 1: Fetch games
            if not self.fetch_games():
                logger.error("Failed to fetch games, exiting")
                return False
                
            # Step 2: Fetch weather data
            self.fetch_weather_data()
            
            # Step 3: Fetch lineups and pitchers
            self.fetch_lineups_and_pitchers()
            
            # Step 4: Fetch player and pitcher stats
            self.fetch_player_stats()
            self.fetch_pitcher_stats()

            # Analyze handedness data after fetching stats
            handedness_stats = self.analyze_handedness_data()
            if handedness_stats['unknown_batter_pct'] > 0.3:
                logger.warning(f"High percentage of unknown batter handedness: {handedness_stats['unknown_batter_pct']:.1%}")
            if handedness_stats['unknown_pitcher_pct'] > 0.3:
                logger.warning(f"High percentage of unknown pitcher handedness: {handedness_stats['unknown_pitcher_pct']:.1%}")


            # Step 5: Integrate Baseball Savant data (just one line!)
            self.integrate_savant_data()


            # Step 6: Predict HR probabilities
            predictions_df = self.predict_home_runs()
            
            if predictions_df.empty:
                logger.error("No predictions generated, exiting")
                return False
                
            # Step 7: Categorize predictions
            categories = self.categorize_predictions(predictions_df)
            
            # Step 8: Format and send Telegram message
            message = self.format_telegram_message(categories)
            self.send_telegram_message(message)
            
            # Print message to console as well
            print(message)
            
            return True
            
        except Exception as e:
            logger.error(f"Error in prediction pipeline: {e}")
            return False

if __name__ == "__main__":
    predictor = MLBHomeRunPredictor()
    predictor.run()
