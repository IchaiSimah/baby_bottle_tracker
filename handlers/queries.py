from datetime import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from utils import load_user_data
from database import get_language
from translations import t

def format_time(time: str) -> str:
    dt_parts = time.split(' ')
    date_parts = dt_parts[0].split('-')
    time_parts = dt_parts[1].split(':')
    hour = time_parts[0].zfill(2)
    minute = time_parts[1]
    return f"{hour}:{minute} le {date_parts[0]}-{date_parts[1]}"

def get_main_message_content(data, group_id, language="fr"):
    """Generate the main message content with last 5 bottles and last poop"""
    # Handle case where group_id might be None or not in data
    if not group_id or group_id not in data:
        return t("error_load_data", language), InlineKeyboardMarkup([[
            InlineKeyboardButton(t("btn_refresh", language), callback_data="refresh")
        ]])
    
    group_data = data[group_id]
    entries = group_data.get("entries", [])
    poop = group_data.get("poop", [])
    
    # Get display settings
    bottles_to_show = group_data.get("bottles_to_show", 5)
    poops_to_show = group_data.get("poops_to_show", 1)
    
    message = t("main_dashboard", language)
    
    # Add group name to the message
    group_name = group_data.get('name', 'Groupe inconnu')
    message += t("main_group", language, group_name)
    
    # Show last bottles
    if entries:
        last_entries = entries[:bottles_to_show]
        message += t("main_last_bottles", language)
        entries_text = ""
        for entry in last_entries:
            if isinstance(entry['time'], datetime):
                time_str = entry['time'].strftime('%d-%m-%Y %H:%M')
            else:
                time_str = str(entry['time'])
            entries_text += f"`{time_str}` - *{entry['amount']}ml* 🍼\n"
        message += entries_text
    else:
        message += t("main_no_bottles", language)
    
    message += "\n"
    
    # Show last poop(s)
    if poop:
        last_poops = poop[:poops_to_show]
        message += t("main_last_poops", language, "s" if poops_to_show > 1 else "", "s" if poops_to_show > 1 else "")
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
        message += t("main_no_poops", language)
    
    # Create inline keyboard
    keyboard = [
        [
            InlineKeyboardButton(t("btn_bottle", language), callback_data="add_bottle"),
            InlineKeyboardButton(t("btn_poop", language), callback_data="add_poop"),
        ],
        [
            InlineKeyboardButton(t("btn_delete", language), callback_data="remove_bottle"),
            InlineKeyboardButton(t("btn_shabbat", language), callback_data="shabbat"),
        ],
        [
            InlineKeyboardButton(t("btn_stats", language), callback_data="stats"),
            InlineKeyboardButton(t("btn_pdf", language), callback_data="pdf_menu")
        ],
        [
            InlineKeyboardButton(t("btn_settings", language), callback_data="settings")
        ]
    ]
    return message, InlineKeyboardMarkup(keyboard)

def get_main_message_content_for_user(user_id: int):
    """Optimized version that loads only user-specific data"""
    data = load_user_data(user_id)
    language = get_language(user_id)
    if not data:
        return t("error_load_data", language), InlineKeyboardMarkup([[
            InlineKeyboardButton(t("btn_refresh", language), callback_data="refresh")
        ]])
    
    # Get the first (and only) group in the data
    group_id = list(data.keys())[0]
    return get_main_message_content(data, group_id, language)
