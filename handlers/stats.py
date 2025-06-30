from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from zoneinfo import ZoneInfo
from utils import load_data, find_group_for_user, load_user_stats
import os
import requests

async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show statistics for the last 5 days"""
    query = update.callback_query
    if not query:
        return
    
    await query.answer()
    
    user = update.effective_user
    if not user:
        return
    
    user_id = user.id
    
    # Use optimized stats loading
    stats_data = load_user_stats(user_id, 5)
    if not stats_data:
        # Fallback to old method if needed
        data = load_data()
        group_id = find_group_for_user(data, user_id)
        if not group_id or group_id not in data:
            error_msg = "❌ Oups ! Impossible de trouver ou créer votre groupe personnel pour le moment. Veuillez réessayer plus tard."
            if hasattr(update, 'message') and update.message:
                await update.message.reply_text(error_msg)
            elif hasattr(update, 'callback_query') and update.callback_query:
                await update.callback_query.edit_message_text(error_msg)
            return
        
        entries = data[group_id].get("entries", [])
        poop = data[group_id].get("poop", [])
    else:
        entries = stats_data.get("entries", [])
        poop = stats_data.get("poop", [])
    
    # Calculate stats for last 5 days
    today = datetime.now(ZoneInfo('UTC')).date()
    stats = {}
    
    for i in range(5):
        date = today - timedelta(days=i)
        date_str = date.strftime("%d-%m-%Y")
        
        # Count bottles for this date
        day_bottles = [e for e in entries if e["time"].strftime("%d-%m-%Y") == date_str]
        total_ml = sum(e["amount"] for e in day_bottles)
        bottle_count = len(day_bottles)
        
        # Count poops for this date
        day_poops = [p for p in poop if p["time"].strftime("%d-%m-%Y") == date_str]
        poop_count = len(day_poops)
        
        stats[date_str] = {
            "bottles": bottle_count,
            "total_ml": total_ml,
            "poops": poop_count,
            "date": date
        }
    
    # Generate statistics message
    message = "📊 **Statistiques des 5 derniers jours** 📈\n\n"
    
    total_bottles_5days = sum(stats[d]["bottles"] for d in stats)
    total_ml_5days = sum(stats[d]["total_ml"] for d in stats)
    total_poops_5days = sum(stats[d]["poops"] for d in stats)
    
    message += f"**📋 Résumé 5 jours :**\n"
    message += f"• 🍼 {total_bottles_5days} biberons\n"
    message += f"• 📏 {total_ml_5days}ml au total\n"
    message += f"• 💩 {total_poops_5days} changements\n"
    message += f"• 📈 Moyenne : {total_ml_5days//5 if total_bottles_5days > 0 else 0}ml/jour\n\n"
    
    message += "**📅 Détail par jour :**\n"
    for date_str in sorted(stats.keys(), reverse=True):
        day_stats = stats[date_str]
        day_name = day_stats["date"].strftime("%A")[:3]  # Short day name
        message += f"`{date_str} ({day_name}) : "
        message += f"{day_stats['bottles']} biberons, "
        message += f"{day_stats['total_ml']}ml, "
        message += f"{day_stats['poops']} changements`\n"
    
    # Add loading message for AI
    message += f"\n🤖 **Analyse IA :**\n⏳ Génération en cours..."
    
    # Create keyboard
    keyboard = [
        [InlineKeyboardButton("🏠 Accueil", callback_data="refresh")]
    ]
    
    # Show initial message with loading
    await query.edit_message_text(
        text=message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )    
    # Generate AI summary in background
    ai_summary = await generate_ai_summary(stats)
    
    # Update message with AI summary if available
    if ai_summary:
        # Remove loading message and add AI summary
        message = message.replace("\n🤖 **Analyse IA :**\n⏳ Génération en cours...", f"\n🤖 **Analyse IA :**\n{ai_summary}")
        
        await query.edit_message_text(
            text=message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    else:
        # Remove loading message if AI failed
        message = message.replace("\n🤖 **Analyse IA :**\n⏳ Génération en cours...", "")
        
        await query.edit_message_text(
            text=message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

async def generate_ai_summary(stats):
    """Generate an AI summary using Gemini if available"""
    try:
        GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
        if not GEMINI_API_KEY:
            print("GEMINI_API_KEY not found in environment variables")
            return None

        # Try different models in order of preference (higher quota first)
        models_to_try = [
            "gemini-2.5-flash-lite-preview-06-17",  # New model with 1000 requests/day quota
            "gemini-2.5-flash-latest",  # Alternative 2.5 model name
            "gemini-1.5-pro",  # Higher quota than flash
            "gemini-1.5-flash-latest",  # Original model
            "gemini-1.5-flash",  # Alternative flash model
            "gemini-pro"  # Legacy model
        ]
        
        url_base = "https://generativelanguage.googleapis.com/v1beta/models"
        
        # Prepare data for AI
        summary_data = []
        for date_str in sorted(stats.keys()):
            day_stats = stats[date_str]
            summary_data.append({
                "date": date_str,
                "bottles": day_stats["bottles"],
                "total_ml": day_stats["total_ml"],
                "poops": day_stats["poops"]
            })
        
        # Create a more detailed prompt
        prompt = f"""
        Tu es un assistant spécialisé dans l'analyse des données de suivi de bébé.
        
        Voici les données des 5 derniers jours :
        {summary_data}
        
        Analyse ces données et donne un résumé encourageant en français en 1-2 phrases maximum.
        Mentionne les tendances positives, la régularité, ou des observations utiles.
        Sois bienveillant et encourageant pour les parents. Essaie cependant d'etre le plus pertinent possible.
        
        Exemple de format : "Votre bébé montre une belle régularité avec X biberons par jour en moyenne."
        """
        
        # Properly format the JSON request
        request_data = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": prompt
                        }
                    ]
                }
            ]
        }
        
        # Try each model until one works
        for model_name in models_to_try:
            try:
                url = f"{url_base}/{model_name}:generateContent"
                params = {"key": GEMINI_API_KEY}
                
                print(f"Trying model: {model_name}")
                response = requests.post(
                    url, 
                    params=params, 
                    json=request_data,
                    headers={"Content-Type": "application/json"},
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    # Extract the text from the response
                    if 'candidates' in result and len(result['candidates']) > 0:
                        candidate = result['candidates'][0]
                        if 'content' in candidate and 'parts' in candidate['content']:
                            parts = candidate['content']['parts']
                            if len(parts) > 0 and 'text' in parts[0]:
                                ai_text = parts[0]['text'].strip()
                                print(f"✅ Success with model {model_name}: {ai_text}")
                                return ai_text
                    
                    print(f"Unexpected response format from {model_name}: {result}")
                    continue
                    
                elif response.status_code == 429:
                    print(f"❌ Quota exceeded for model {model_name}, trying next model...")
                    continue
                    
                elif response.status_code == 404:
                    print(f"❌ Model {model_name} not found (404)")
                    print(f"Response: {response.text}")
                    continue
                    
                elif response.status_code == 400:
                    print(f"❌ Bad request for model {model_name} (400)")
                    print(f"Response: {response.text}")
                    continue
                    
                else:
                    print(f"❌ Error with model {model_name}: {response.status_code}")
                    print(f"Response: {response.text}")
                    continue
                    
            except Exception as e:
                print(f"❌ Exception with model {model_name}: {e}")
                continue
        
        print("❌ All models failed")
        return None
        
    except ImportError as e:
        print(f"Gemini library not installed: {e}")
        return None
    except Exception as e:
        print(f"Erreur Gemini: {e}")
        return None 
