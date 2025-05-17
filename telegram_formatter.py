import logging

# Configure logging (or import your logging config)
logger = logging.getLogger('MLB-HR-Predictor')

def format_telegram_message(categories, today, early_run=False):
    """
    Format prediction results for Telegram message with enhanced details and emojis.
    
    Parameters:
    -----------
    categories : dict
        Dictionary with "locks", "hot_picks", and "sleepers" lists of player predictions
    today : str
        Today's date in YYYY-MM-DD format
    early_run : bool, default=False
        Whether this is an early morning run (True) or midday run with confirmed lineups (False)
        
    Returns:
    --------
    str
        Formatted message for Telegram
    """
    time_label = "☀️ EARLY MORNING (6AM) ☀️" if early_run else "🔥 MIDDAY (CONFIRMED LINEUPS) 🔥"
    
    message = f"⚾️💥 MLB HOME RUN PREDICTIONS - {today} {time_label} 💥⚾️\n\n"
    
    # Add header with prediction info
    message += "📊 Today's Top Home Run Picks 📊\n"
    message += "Powered by AI + 16 key HR factors including:\n"
    message += "🔍 Recent hot streaks, quality of contact metrics\n"
    message += "🏟️ Ballpark factors, weather conditions\n"
    message += "⚔️ Pitcher matchups & platoon advantages\n\n"
    
    # Add locks section with enhanced details
    message += "🔒 ABSOLUTE LOCKS 🔒\n"
    if categories["locks"]:
        for i, player in enumerate(categories["locks"], 1):
            # Get handedness information with fallbacks
            batter_hand = player.get('bats', '?')
            pitcher_hand = player.get('pitcher_throws', player.get('throws', '?'))
            
            # Emojis for handedness
            lefty_emoji = "👈"  # Left-handed
            righty_emoji = "👉"  # Right-handed
            switch_emoji = "🔄"  # Switch hitter
            
            # Get batter handedness emoji
            if batter_hand == 'L':
                batter_emoji = lefty_emoji
            elif batter_hand == 'R':
                batter_emoji = righty_emoji
            elif batter_hand == 'S':
                batter_emoji = switch_emoji
            else:
                batter_emoji = "❓"
                
            # Get pitcher handedness emoji
            if pitcher_hand == 'L':
                pitcher_emoji = lefty_emoji
            elif pitcher_hand == 'R':
                pitcher_emoji = righty_emoji
            else:
                pitcher_emoji = "❓"
            
            # Player name with team and chance
            message += f"{i}. {player['player']} ({player['team']}) - {player['hr_probability']:.1%} HR chance\n"
            
            # Matchup details with handedness
            message += f"   🆚 {player['opponent_name']} @ {player['ballpark']}\n"
            
            # Pitcher info with handedness
            pitcher_name = player['opponent_pitcher'] if player['opponent_pitcher'] not in ['Unknown', 'TBD'] else '🤔 TBD'
            message += f"   ⚾ vs {pitcher_name}"
            
            # Add handedness matchup
            if pitcher_name != '🤔 TBD' and batter_hand != '?' and pitcher_hand != '?':
                message += f" • {batter_emoji} {batter_hand} batter vs {pitcher_hand} pitcher {pitcher_emoji}"
            message += "\n"
            
            # Add platoon advantage as a separate line if applicable
            if player.get('platoon_advantage', False):
                if batter_hand == 'L' and pitcher_hand == 'R':
                    message += f"   ⭐ L vs R platoon advantage! (Lefty batter vs righty pitcher)\n"
                elif batter_hand == 'R' and pitcher_hand == 'L':
                    message += f"   ⭐ R vs L platoon advantage! (Righty batter vs lefty pitcher)\n"
                elif batter_hand == 'S':
                    message += f"   ⭐ Switch hitter advantage vs {pitcher_hand} pitcher\n"
            
            # Weather details
            message += f"   🌡️ {player['weather_temp']:.1f}°F"
            if player.get('weather_wind', 0) > 5:
                message += f", 💨 {player['weather_wind']:.1f} mph winds"
            if player.get('weather_factor', 1.0) > 1.1:
                message += " (favorable for HR)"
            elif player.get('weather_factor', 1.0) < 0.9:
                message += " (unfavorable for HR)"
            message += "\n"
            
            # Season and recent stats
            message += f"   📈 Season: {player.get('hr', 0)} HR in {player.get('games', 0)} G"
            if 'recent_hr' in player:
                message += f" • Last 7: {player['recent_hr']} HR"
            message += "\n"
            
            # Batter strengths - detailed breakdown
            message += "   💪 Batter profile: "
            strengths = []
            
            if player.get('recent_hr_rate', 0) > 0.05:
                strengths.append("🔥 Hot streak (recent HR rate)")
            elif player.get('hot_cold_streak', 1.0) > 1.2:
                strengths.append("🔥 Heating up")
                
            if player.get('exit_velo', 0) > 90:
                strengths.append(f"💥 {player['exit_velo']:.1f} mph exit velo")
                
            if 25 <= player.get('launch_angle', 0) <= 35:
                strengths.append(f"📐 Optimal launch angle ({player['launch_angle']:.1f}°)")
                
            if player.get('barrel_pct', 0) > 0.1:
                strengths.append(f"🎯 Barrel machine ({player['barrel_pct']:.1%})")
                
            if player.get('pull_pct', 0) > 0.4:
                strengths.append("↩️ Strong pull tendency")
                
            if player.get('hard_hit_pct', 0) > 0.4:
                strengths.append("👊 Elite hard contact")
            elif player.get('hard_hit_pct', 0) > 0.35:
                strengths.append("👊 Good hard contact")
                
            if player.get('hr_fb_ratio', 0) > 0.2:
                strengths.append("⚡ Elite HR/FB ratio")
            elif player.get('hr_fb_ratio', 0) > 0.15:
                strengths.append("⚡ Strong HR/FB ratio")
                
            message += ", ".join(strengths) + "\n"
            
            # Matchup advantages
            advantages = []
            if player.get('ballpark_factor', 1.0) > 1.1:
                advantages.append(f"🏟️ HR-friendly park ({player['ballpark_factor']:.2f}x)")
                
            # Platoon already handled above, so we don't need to repeat it here
                
            if player.get('pitch_type_matchup', 1.0) > 1.1:
                advantages.append("🎯 Strong vs pitcher's arsenal")
                
            if player.get('pitcher_gb_fb', 1.0) < 0.8:
                advantages.append("🚀 Facing fly ball pitcher")
                
            if player.get('pitcher_workload', 1.0) > 1.1:
                advantages.append("😓 Facing fatigued pitcher")
                
            if player.get('batter_vs_pitcher', 1.0) > 1.1:
                advantages.append("📈 Historical success vs pitcher")
                
            if advantages:
                message += "   🔍 Matchup edges: " + ", ".join(advantages) + "\n"
                
            # Add xStats (expected stats)
            message += f"   📊 xStats: {player.get('xISO', 0):.3f} xISO, {player.get('xwOBA', 0):.3f} xwOBA\n"
            
            message += "\n"
    else:
        message += "None identified for today.\n\n"
        
    # Add hot picks section with similar detailed format
    message += "🔥 HOT PICKS 🔥\n"
    if categories["hot_picks"]:
        for i, player in enumerate(categories["hot_picks"], 1):
            # Get handedness information with fallbacks
            batter_hand = player.get('bats', '?')
            pitcher_hand = player.get('pitcher_throws', player.get('throws', '?'))
            
            # Player name with team and chance
            message += f"{i}. {player['player']} ({player['team']}) - {player['hr_probability']:.1%} HR chance\n"
            
            # Matchup details
            message += f"   🆚 {player['opponent_name']} @ {player['ballpark']}\n"
            
            # Pitcher info with possible handedness
            pitcher_name = player['opponent_pitcher'] if player['opponent_pitcher'] not in ['Unknown', 'TBD'] else '🤔 TBD'
            message += f"   ⚾ vs {pitcher_name}"
            
            # Add handedness if available
            if pitcher_name != '🤔 TBD' and batter_hand != '?' and pitcher_hand != '?':
                message += f" • {batter_hand} vs {pitcher_hand}"
                
                # Add platoon note
                if player.get('platoon_advantage', False):
                    message += " (✅ advantage)"
            
            message += "\n"
            
            # Weather details
            message += f"   🌡️ {player['weather_temp']:.1f}°F"
            if player.get('weather_wind', 0) > 5:
                message += f", 💨 {player['weather_wind']:.1f} mph winds"
            if player.get('weather_factor', 1.0) > 1.05:
                message += " (favorable)"
            elif player.get('weather_factor', 1.0) < 0.95:
                message += " (unfavorable)"
            message += "\n"
            
            # Key strengths (slightly condensed compared to locks)
            strengths = []
            if player.get('recent_hr_rate', 0) > 0.04:
                strengths.append("🔥 Hot bat")
            if player.get('ballpark_factor', 1.0) > 1.05:
                strengths.append("🏟️ HR-friendly park")
            if player.get('platoon_advantage', False):
                strengths.append(f"👍 {batter_hand} vs {pitcher_hand}")
            if player.get('barrel_pct', 0) > 0.08:
                strengths.append("🎯 Quality contact")
            if player.get('hard_hit_pct', 0) > 0.35:
                strengths.append("💪 Hard hitter")
            if player.get('exit_velo', 0) > 88:
                strengths.append(f"💥 {player['exit_velo']:.1f} mph exit velo")
            if player.get('pitch_type_matchup', 1.0) > 1.05:
                strengths.append("🎯 Matchup advantage")
            if player.get('hr_fb_ratio', 0) > 0.12:
                strengths.append("⚡ HR efficiency")
            
            if strengths:
                message += f"   ➕ Key factors: {', '.join(strengths)}\n"
                
            message += "\n"
    else:
        message += "None identified for today.\n\n"
        
    # Add sleepers section (more concise but still detailed)
    message += "😴 SLEEPER PICKS 😴\n"
    if categories["sleepers"]:
        for i, player in enumerate(categories["sleepers"], 1):
            # Get basic handedness
            batter_hand = player.get('bats', '?')
            pitcher_hand = player.get('pitcher_throws', player.get('throws', '?'))
            
            # Player name with team and chance
            message += f"{i}. {player['player']} ({player['team']}) - {player['hr_probability']:.1%} HR chance\n"
            
            # Matchup and weather in one line
            pitcher_name = player['opponent_pitcher'] if player['opponent_pitcher'] not in ['Unknown', 'TBD'] else '🤔 TBD'
            
            # Simplified matchup line with handedness if available
            matchup_info = f"   🆚 vs {pitcher_name} @ {player['ballpark']} • 🌡️ {player['weather_temp']:.1f}°F"
            if batter_hand != '?' and pitcher_hand != '?' and pitcher_name != '🤔 TBD':
                matchup_info += f" • {batter_hand}/{pitcher_hand}"
                if player.get('platoon_advantage', False):
                    matchup_info += "✅"
            
            message += matchup_info + "\n"
            
            # Condensed factors
            factors = []
            if player.get('recent_hr_rate', 0) > 0.03 or player.get('streak_factor', 1.0) > 1.0:
                factors.append("🔄 Trending up")
            if player.get('ballpark_factor', 1.0) > 1.0:
                factors.append("🏟️ Park boost")
            if player.get('platoon_advantage', False):
                factors.append(f"👍 {batter_hand}/{pitcher_hand}")
            if player.get('pull_pct', 0) > 0.3:
                factors.append("↩️ Pull tendency")
            if player.get('barrel_pct', 0) > 0.05:
                factors.append("🎯 Barrel potential")
            if player.get('pitch_type_matchup', 1.0) > 1.0:
                factors.append("⚔️ Good matchup")
            if 20 <= player.get('launch_angle', 0) <= 40:
                factors.append("📐 Good angle")
            
            if factors:
                message += f"   ➕ {' • '.join(factors)}\n"
                
            message += "\n"
    else:
        message += "None identified for today.\n\n"
    
    # Add fun footer with methodology details
    message += "⚾️ HOW WE PREDICT ⚾️\n"
    message += "Our AI crunches 16 weighted factors including:\n"
    message += "• 🔍 Recent HR rates & player trends\n"
    message += "• 📊 Advanced stats (barrel%, pull%, hard hit%, xStats)\n"
    message += "• 🏟️ Ballpark factors & dimensions\n"
    message += "• 🌡️ Real-time weather effects\n"
    message += "• ⚔️ Pitcher matchups & workload\n"
    message += "• 🔢 Historical batter-pitcher results\n\n"
    
    message += "⚡ Good luck today! Bet responsibly and enjoy the long balls! 💥"
    
    return message

def send_telegram_message(message, bot_token, chat_id):
    """
    Send message via Telegram bot.
    
    Parameters:
    -----------
    message : str
        The formatted message to send
    bot_token : str
        Telegram bot token
    chat_id : int or str
        Telegram chat ID to send the message to
        
    Returns:
    --------
    bool
        True if message was sent successfully, False otherwise
    """
    import requests
    
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        data = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "HTML"
        }
        response = requests.post(url, json=data)
        
        if response.status_code == 200:
            logger.info("Telegram message sent successfully")
            return True
        else:
            logger.error(f"Error sending Telegram message: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Exception sending Telegram message: {e}")
        return False
