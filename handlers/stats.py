from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from utils import load_data, find_group_for_user, create_personal_group, save_data, load_user_stats, invalidate_user_cache
import os

async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show statistics for the last 5 days"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
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
    today = datetime.now().date()
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
        # Check if Gemini API is available
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        if not gemini_api_key:
            print("GEMINI_API_KEY not found in environment variables")
            return None
        
        print(f"Gemini API key found: {gemini_api_key[:10]}...")
        
        # Import Gemini
        import google.generativeai as genai
        
        genai.configure(api_key=gemini_api_key)
        
        # Try different models in order of preference
        models_to_try = ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-pro']
        model = None
        
        for model_name in models_to_try:
            try:
                print(f"Trying model: {model_name}")
                model = genai.GenerativeModel(model_name)
                # Test the model with a simple request
                test_response = model.generate_content("Test")
                print(f"✅ Model {model_name} works!")
                break
            except Exception as e:
                print(f"❌ Model {model_name} failed: {e}")
                continue
        
        if not model:
            print("❌ No working Gemini model found")
            return None
        
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
        
        print("Sending request to Gemini...")
        response = model.generate_content(prompt)
        result = response.text.strip()
        print(f"Gemini response: {result}")
        
        return result
        
    except ImportError as e:
        print(f"Gemini library not installed: {e}")
        return None
    except Exception as e:
        print(f"Erreur Gemini: {e}")
        return None 