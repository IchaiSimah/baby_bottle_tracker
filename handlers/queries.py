from datetime import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from utils import load_user_data

def format_time(time: str) -> str:
    dt_parts = time.split(' ')
    date_parts = dt_parts[0].split('-')
    time_parts = dt_parts[1].split(':')
    hour = time_parts[0].zfill(2)
    minute = time_parts[1]
    return f"{hour}:{minute} le {date_parts[0]}-{date_parts[1]}"

def get_main_message_content(data, group_id):
    """Generate the main message content with last 5 bottles and last poop"""
    # Handle case where group_id might be None or not in data
    if not group_id or group_id not in data:
        return "❌ Oups ! Impossible de charger vos données pour le moment. Veuillez réessayer.", InlineKeyboardMarkup([[
            InlineKeyboardButton("🔄 Actualiser", callback_data="refresh")
        ]])
    
    group_data = data[group_id]
    entries = group_data.get("entries", [])
    poop = group_data.get("poop", [])
    
    # Get display settings
    bottles_to_show = group_data.get("bottles_to_show", 5)
    poops_to_show = group_data.get("poops_to_show", 1)
    
    message = "🍼 **Suivi Bébé - Tableau de Bord**\n\n"
    
    # Add group name to the message
    group_name = group_data.get('name', 'Groupe inconnu')
    message += f"**👥 Groupe :** `{group_name}`\n\n"
    
    # Show last bottles
    if entries:
        last_entries = entries[:bottles_to_show]
        message += f"🍼 **Derniers biberons :**\n"
        entries_text = ""
        for entry in last_entries:
            if isinstance(entry['time'], datetime):
                time_str = entry['time'].strftime('%d-%m-%Y %H:%M')
            else:
                time_str = str(entry['time'])
            entries_text += f"`{time_str}` - *{entry['amount']}ml* 🍼\n"
        message += entries_text
    else:
        message += "🍼 **pensez à mettre l'heure a jour dans les paramètres !**\n"
        message += "_Aucun biberon enregistré pour le moment_ 📝\n"
    
    message += "\n"
    
    # Show last poop(s)
    if poop:
        last_poops = poop[:poops_to_show]
        message += f"💩 **Dernier{'s' if poops_to_show > 1 else ''} caca{'s' if poops_to_show > 1 else ''} :**\n"
        poop_text = ""
        for p in last_poops:
            if isinstance(p['time'], datetime):
                poop_time = p['time'].strftime('%d-%m-%Y %H:%M')
            else:
                poop_time = str(p['time']) if p['time'] else '??'
            poop_text += f"`{poop_time}`"
            if p.get('info'):
                poop_text += f" _{p['info']}_"
            poop_text += " 💩\n"
        message += poop_text
    else:
        message += "_Aucu enregistré pour le moment_ 📝\n"
    
    # Create inline keyboard
    keyboard = [
        [
            InlineKeyboardButton("🍼 Biberon", callback_data="add_bottle"),
            InlineKeyboardButton("💩 Caca", callback_data="add_poop"),
        ],
        [
            InlineKeyboardButton("❌ Supprimer", callback_data="remove_bottle"),
            InlineKeyboardButton("🕯️ Shabbat", callback_data="shabbat"),
        ],
        [
            InlineKeyboardButton("📊 Statistiques", callback_data="stats"),
            InlineKeyboardButton("📄 PDF", callback_data="pdf_menu")
        ],
        [
            InlineKeyboardButton("⚙️ Paramètres", callback_data="settings")
        ]
    ]
    return message, InlineKeyboardMarkup(keyboard)

def get_main_message_content_for_user(user_id: int):
    """Optimized version that loads only user-specific data"""
    data = load_user_data(user_id)
    if not data:
        return "❌ Oups ! Impossible de charger vos données pour le moment. Veuillez réessayer.", InlineKeyboardMarkup([[
            InlineKeyboardButton("🔄 Actualiser", callback_data="refresh")
        ]])
    
    # Get the first (and only) group in the data
    group_id = list(data.keys())[0]
    return get_main_message_content(data, group_id)
