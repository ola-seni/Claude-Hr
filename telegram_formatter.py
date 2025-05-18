import logging
import requests
import datetime

# Configure logging (or import your logging config)
logger = logging.getLogger('MLB-HR-Predictor')

def format_telegram_message(categories, today, early_run=False):
    """Format prediction results in a stylish, betting-focused format."""
    date_obj = datetime.datetime.strptime(today, "%Y-%m-%d")
    formatted_date = date_obj.strftime("%a, %b %d")
    time_label = "☀️ EARLY MORNING" if early_run else "⚾️ MIDDAY UPDATE"
    
    message = f"⚾️💥 MLB HOME RUN PREDICTOR 💥⚾️\n"
    message += f"📅 {formatted_date} • {time_label}\n"
    message += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    # Get all predictions
    locks = categories.get("locks", [])
    hot_picks = categories.get("hot_picks", [])
    sleepers = categories.get("sleepers", [])
    
    # Combine and sort for top picks
    all_predictions = locks + hot_picks + sleepers
    all_predictions.sort(key=lambda x: x['hr_probability'], reverse=True)
    top_3 = all_predictions[:3] if len(all_predictions) >= 3 else all_predictions
    
    # Display top 3 picks with emoji rating
    if top_3:
        message += "🏆 TODAY'S TOP HR CANDIDATES 🏆\n"
        for i, player in enumerate(top_3, 1):
            # Format probability as percentage and odds
            prob = player['hr_probability']
            prob_pct = prob * 100
            
            # Convert to American odds
            if prob >= 0.5:
                odds = int(-(prob / (1 - prob)) * 100)
                odds_str = f"{odds}"
            else:
                odds = int(((1 - prob) / prob) * 100)
                odds_str = f"+{odds}"
                
            # Add star rating
            if prob > 0.10:
                stars = "⭐⭐⭐⭐⭐"
            elif prob > 0.07:
                stars = "⭐⭐⭐⭐"
            elif prob > 0.05:
                stars = "⭐⭐⭐"
            elif prob > 0.03:
                stars = "⭐⭐"
            else:
                stars = "⭐"
                
            message += f"{i}. {player['player']} ({player['team']}) {stars}\n"
            message += f"   {prob_pct:.1f}% HR chance | Fair odds: {odds_str}\n"
        message += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    # Function to format game time
    def format_game_time(game_time_str):
        if not game_time_str:
            return "TBD"
        try:
            game_time = datetime.datetime.strptime(game_time_str, "%Y-%m-%dT%H:%M:%SZ")
            et_time = game_time - datetime.timedelta(hours=4)
            return et_time.strftime("%I:%M %p ET").lstrip("0")
        except Exception as e:
            return "TBD"
    
    # Function for the compact player entry format
    def format_player_entry(player, rank):
        # Get basic info
        team = player['team']
        opponent_pitcher = player['opponent_pitcher']
        ballpark = player['ballpark']
        game_time = format_game_time(player.get('game_time', ''))
        hr_prob = player['hr_probability']
        hr_pct = hr_prob * 100
        
        # Calculate fair odds
        if hr_prob >= 0.5:
            odds = int(-(hr_prob / (1 - hr_prob)) * 100)
            odds_str = f"{odds}"
        else:
            odds = int(((1 - hr_prob) / hr_prob) * 100)
            odds_str = f"+{odds}"
        
        # Temp in Fahrenheit
        temp = player.get('weather_temp', 0)
        
        # Determine advantage emojis
        advantages = []
        
        # Trending up / hot streak
        if player.get('hot_cold_streak', 1.0) > 1.1:
            advantages.append("🔥 Hot streak")
        
        # Park factor
        if player.get('ballpark_factor', 1.0) > 1.05:
            advantages.append("🏟️ Park boost")
        
        # Weather
        if player.get('weather_factor', 1.0) > 1.05:
            if player.get('weather_wind', 0) > 5:
                advantages.append("💨 Wind advantage")
            else:
                advantages.append("🌡️ Good temperature")
        
        # Pull tendency
        if player.get('pull_pct', 0) > 0.4:
            advantages.append("↩️ Pull tendency")
        
        # Barrel potential
        if player.get('barrel_pct', 0) > 0.08:
            advantages.append("🎯 Barrel machine")
        elif player.get('barrel_pct', 0) > 0.05:
            advantages.append("🎯 Barrel potential")
        
        # Pitcher matchup
        if player.get('pitcher_hr_per_9', 0) > 1.2:
            advantages.append("🧨 HR-prone pitcher")
        
        # Platoon advantage
        if player.get('platoon_advantage', False):
            advantages.append("⚔️ Platoon advantage")
            
        # Exit velocity
        if player.get('exit_velo', 0) > 90:
            advantages.append("💥 High exit velo")
            
        # Create the compact emoji advantages string
        adv_str = ""
        for adv in advantages[:5]:  # Limit to 5 advantages
            adv_str += adv + " • "
            
        if adv_str:
            adv_str = adv_str[:-3]  # Remove trailing " • "
        else:
            adv_str = "No significant advantages"
            
        # Create the compact entry
        entry = f"🔹 {player['player']} ({team}) - {hr_pct:.1f}% HR chance\n"
        entry += f"   🆚 vs {opponent_pitcher} @ {ballpark} • 🌡️ {temp:.1f}°F\n"
        entry += f"   ➕ {adv_str}\n"
        entry += f"   💰 Fair odds: {odds_str} | ISO: {player.get('xISO', 0):.3f} | Barrel%: {player.get('barrel_pct', 0):.3f}\n"
        entry += f"   ──────────────────────────\n\n"
        
        return entry
    
    # Add the Locks section
    message += "🔒 LOCKS 🔒\n"
    if locks:
        message += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        for i, player in enumerate(locks[:5], 1):
            message += format_player_entry(player, i)
    else:
        message += "None identified for today.\n\n"
    
    # Add the Hot Picks section
    message += "🔥 HOT PICKS 🔥\n"
    if hot_picks:
        message += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        for i, player in enumerate(hot_picks[:5], 1):
            message += format_player_entry(player, i+5)
    else:
        message += "None identified for today.\n\n"
    
    # Add the Sleepers section
    message += "💤 SLEEPERS 💤\n"
    if sleepers:
        message += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        for i, player in enumerate(sleepers[:5], 1):
            message += format_player_entry(player, i+10)
    else:
        message += "None identified for today.\n\n"
    
    # Add the HOW WE PREDICT section
    message += "⚾️ HOW WE PREDICT ⚾️\n"
    message += "Our AI crunches 16 weighted factors including:\n"
    message += "• 🔍 Recent HR rates & player trends\n"
    message += "• 📊 Advanced stats (barrel%, pull%, hard hit%, xStats)\n"
    message += "• 🏟️ Ballpark factors & dimensions\n"
    message += "• 🌡️ Real-time weather effects\n"
    message += "• ⚔️ Pitcher matchups & workload\n"
    message += "• 🔢 Historical batter-pitcher results\n\n"
    
    # Add betting guidance
    message += "💰 BETTING GUIDANCE 💰\n"
    message += "• Look for sportsbook odds higher than our fair odds\n"
    message += "• Example: Our odds +2000, sportsbook odds +2500 = value bet\n"
    message += "• Small unit sizing recommended (0.1-0.25 units per HR bet)\n"
    message += "• Consider parlaying picks for higher potential returns\n\n"
    
    message += "⚾️ MLB HOME RUN PREDICTOR | Powered by AI + Advanced Analytics"
    
    return message

def send_telegram_message(message, bot_token, chat_id):
    """Send message via Telegram bot."""
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        data = {
            "chat_id": chat_id,
            "text": message,
            # No parse_mode to avoid formatting issues
        }
        response = requests.post(url, json=data)
        
        if response.status_code == 200:
            logger.info("Telegram message sent successfully!")
            return True
        else:
            logger.error(f"Error sending Telegram message: Status {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"Exception sending Telegram message: {e}")
        return False
