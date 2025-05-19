import logging
import requests
import datetime
import time

# Configure logging (or import your logging config)
logger = logging.getLogger('MLB-HR-Predictor')

def format_telegram_message(categories, today, early_run=False):
    """Format prediction results in a stylish, analytics-focused format."""
    date_obj = datetime.datetime.strptime(today, "%Y-%m-%d")
    formatted_date = date_obj.strftime("%Y-%m-%d")
    time_label = "☀️ EARLY MORNING (PROBABLE PITCHERS)" if early_run else "🔥 MIDDAY (CONFIRMED LINEUPS) 🔥"
    
    message = f"⚾️💥 MLB HOME RUN PREDICTIONS - {formatted_date} {time_label} 💥⚾️\n\n"
    
    # Add analytics intro
    message += f"📊 Today's Top Home Run Picks 📊\n"
    message += f"Powered by AI + 16 key HR factors including:\n"
    message += f"🔍 Recent hot streaks, quality of contact metrics\n"
    message += f"🏟️ Ballpark factors, weather conditions\n"
    message += f"⚔️ Pitcher matchups & platoon advantages\n\n"
    
    # Format each category
    def format_player_entry(player, rank):
        # Format game time
        game_time_str = player.get('game_time', '')
        try:
            game_time = datetime.datetime.strptime(game_time_str, "%Y-%m-%dT%H:%M:%SZ")
            # Adjust for ET timezone (UTC-4)
            game_time = game_time - datetime.timedelta(hours=4)
            time_display = game_time.strftime("%I:%M %p ET").lstrip("0")
        except:
            time_display = "TBD"
        
        # Get basic info
        batter_name = player['player']
        team = player['team']
        opponent = player['opponent_name']
        pitcher_name = player['opponent_pitcher']
        ballpark = player['ballpark']
        hr_pct = player['hr_probability'] * 100
        
        # Get handedness matchup
        batter_hand = player.get('bats', '?')
        pitcher_hand = player.get('throws', '?')
        handedness = f"👉 {batter_hand} batter vs {pitcher_hand} pitcher" if batter_hand != '?' and pitcher_hand != '?' else ""
        
        # Weather info
        temp = player.get('weather_temp', 0)
        wind = player.get('weather_wind', 0)
        weather_favorable = player.get('weather_factor', 1.0) > 1.05
        weather_str = f"🌡️ {temp:.1f}°F, 💨 {wind:.1f} mph winds ({'favorable for HR' if weather_favorable else 'neutral/unfavorable'})"
        
        # Analytics breakdown
        entry = f"{rank}. {batter_name} ({team}) vs {pitcher_name} - {hr_pct:.1f}% HR chance\n"
        entry += f"   📍 {ballpark} vs {opponent} | ⏰ {time_display}\n"
        entry += f"   {handedness} | {weather_str}\n"
        
        # Strengths section
        entry += f"   💪 STRENGTHS:\n"
        
        if player.get('iso', 0) > 0.250:
            entry += f"   • ISO: {player.get('iso', 0):.3f} ({'ELITE' if player.get('iso', 0) > 0.300 else 'STRONG'}) 💪\n"

        if player.get('slg', 0) > 0.500:
            entry += f"   • SLG: {player.get('slg', 0):.3f} ({'ELITE' if player.get('slg', 0) > 0.550 else 'STRONG'}) 🚀\n"

        if player.get('l15_barrel_pct', 0) > 0.25:
            entry += f"   • L15 Barrel%: {player.get('l15_barrel_pct', 0):.3f} (ELITE) 🎯\n"

        if player.get('l15_exit_velo', 0) > 95:
            entry += f"   • L15 Exit Velo: {player.get('l15_exit_velo', 0):.1f} mph (ELITE) 💥\n"

        if player.get('hr_pct', 0) > 0.10:
            entry += f"   • HR%: {player.get('hr_pct', 0)*100:.1f}% (ELITE) ⚾\n"
        
        # Power metrics
        iso_rating = "Elite" if player.get('xISO', 0) > 0.200 else "Strong" if player.get('xISO', 0) > 0.150 else "Average"
        barrel_rating = "Elite" if player.get('barrel_pct', 0) > 0.08 else "Strong" if player.get('barrel_pct', 0) > 0.05 else "Average"
        
        entry += f"   • xISO: {player.get('xISO', 0):.3f} ({iso_rating}) 📈\n"
        entry += f"   • Barrel%: {player.get('barrel_pct', 0):.3f} ({barrel_rating}) 🎯\n"
        entry += f"   • Exit Velo: {player.get('exit_velo', 0):.1f} mph 💥\n"
        
        if player.get('hr_fb_ratio', 0) > 0:
            entry += f"   • HR/FB: {player.get('hr_fb_ratio', 0)*100:.1f}% ⚾\n"
            
        # Form information
        if player.get('hot_cold_streak', 1.0) > 1.1:
            entry += f"   • Recent Form: HOT 🔥\n"
        
        # Matchup edges section
        entry += f"\n   ⚔️ MATCHUP EDGES:\n"
        
        if player.get('ballpark_factor', 1.0) > 1.03:
            entry += f"   • Park Factor: {player.get('ballpark_factor', 1.0):.2f} (HR-friendly) 🏟️\n"
        
        if player.get('platoon_advantage', False):
            entry += f"   • Platoon Advantage: YES ✓\n"
            
        # Pitcher metrics
        if 'pitcher_hr_rate' in player:
            entry += f"   • Pitcher HR/9: {player.get('pitcher_hr_rate', 0)*9:.2f} (vulnerable) 🚀\n"
        elif player.get('recent_hr_rate', 0) > 0:
            entry += f"   • Pitcher HR Rate: {player.get('recent_hr_rate', 0):.3f} (vulnerable) 🚀\n"
            
        if player.get('pitcher_gb_fb', 0) < 1.0:
            entry += f"   • GB/FB Ratio: {player.get('pitcher_gb_fb', 1.0):.2f} (fly ball pitcher) ↗️\n"
            
        if player.get('pitcher_workload', 1.0) > 1.1:
            entry += f"   • Pitcher Fatigue: HIGH 😓\n"
        
        entry += "\n   " + "━" * 30 + "\n\n"
        
        return entry
    
    # Add the Locks section
    locks = categories.get("locks", [])
    message += "🔒 ABSOLUTE LOCKS 🔒\n\n"
    if locks:
        for i, player in enumerate(locks[:5], 1):
            message += format_player_entry(player, i)
    else:
        message += "None identified for today.\n\n"
    
    # Add the Hot Picks section
    hot_picks = categories.get("hot_picks", [])
    message += "🔥 HOT PICKS 🔥\n\n"
    if hot_picks:
        for i, player in enumerate(hot_picks[:5], 1):
            message += format_player_entry(player, i)
    else:
        message += "None identified for today.\n\n"
    
    # Add the Sleepers section
    sleepers = categories.get("sleepers", [])
    message += "💤 VALUE SLEEPERS 💤\n\n"
    if sleepers:
        for i, player in enumerate(sleepers[:5], 1):
            message += format_player_entry(player, i)
    else:
        message += "None identified for today.\n\n"
    
    return message

# Add to telegram_formatter.py

def send_telegram_message(message, bot_token, chat_id):
    """Send message via Telegram bot with support for long messages."""
    try:
        # Telegram has a 4096 character limit
        MAX_LENGTH = 4000  # Slightly less than 4096 for safety
        
        # If message is shorter than limit, send as one message
        if len(message) <= MAX_LENGTH:
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            data = {
                "chat_id": chat_id,
                "text": message
            }
            response = requests.post(url, json=data)
            
            if response.status_code == 200:
                logger.info("Telegram message sent successfully!")
                return True
            else:
                logger.error(f"Error sending Telegram message: Status {response.status_code}")
                return False
        
        # Split long message into chunks and send as multiple messages
        chunks = []
        current_chunk = ""
        
        # Split by sections to avoid breaking up a player's info
        sections = []
        
        # First check if the message has natural section breaks
        if '🔒 ABSOLUTE LOCKS 🔒' in message:
            # Split by major headers
            headers = ['⚾️💥 MLB HOME RUN PREDICTIONS', 
                      '🔒 ABSOLUTE LOCKS 🔒', 
                      '🔥 HOT PICKS 🔥', 
                      '💤 VALUE SLEEPERS 💤']
            
            # Get section between each header
            last_pos = 0
            for i in range(len(headers)):
                if i < len(headers) - 1:
                    # Find this header and the next
                    start = message.find(headers[i], last_pos)
                    end = message.find(headers[i+1], start)
                    
                    if start != -1 and end != -1:
                        sections.append(message[start:end])
                        last_pos = end
                else:
                    # Last section goes to the end
                    start = message.find(headers[i], last_pos)
                    if start != -1:
                        sections.append(message[start:])
        else:
            # No clear sections, just use the whole message
            sections = [message]
        
        # Now process each section, potentially splitting further if needed
        for section in sections:
            if len(section) <= MAX_LENGTH:
                chunks.append(section)
            else:
                # Very long section - split by players
                players = section.split("\n\n")
                current_chunk = ""
                
                for player in players:
                    # If adding this player would exceed limit, start a new chunk
                    if len(current_chunk) + len(player) + 2 > MAX_LENGTH:
                        if current_chunk:
                            chunks.append(current_chunk)
                        current_chunk = player
                    else:
                        if current_chunk:
                            current_chunk += "\n\n" + player
                        else:
                            current_chunk = player
                
                # Add the last chunk if not empty
                if current_chunk:
                    chunks.append(current_chunk)
        
        # Send each chunk as a separate message
        success = True
        for i, chunk in enumerate(chunks):
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            prefix = f"(Part {i+1}/{len(chunks)}) " if len(chunks) > 1 else ""
            
            data = {
                "chat_id": chat_id,
                "text": prefix + chunk.strip()
            }
            response = requests.post(url, json=data)
            
            if response.status_code != 200:
                logger.error(f"Error sending Telegram part {i+1}: Status {response.status_code}")
                success = False
            
            # Add a small delay between messages to avoid rate limiting
            if i < len(chunks) - 1:
                time.sleep(1)
        
        if success:
            logger.info(f"Telegram message sent successfully in {len(chunks)} parts!")
            return True
        else:
            logger.error("Error sending some Telegram message parts")
            return False
            
    except Exception as e:
        logger.error(f"Exception sending Telegram message: {e}")
        return False
