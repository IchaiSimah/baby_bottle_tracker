from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from utils import load_data, find_group_for_user

def format_time(time: str) -> str:
    dt_parts = time.split(' ')
    date_parts = dt_parts[0].split('-')
    time_parts = dt_parts[1].split(':')
    hour = time_parts[0].zfill(2)
    minute = time_parts[1]
    return f"{hour}:{minute} le {date_parts[0]}-{date_parts[1]}"

def get_main_message_content(data, group):
    """Generate the main message content with last 5 bottles and last poop"""
    entries = data[group].get("entries", [])
    poop = data[group].get("poop", [])
    
    # Get display settings
    bottles_to_show = data[group].get("bottles_to_show", 5)
    poops_to_show = data[group].get("poops_to_show", 1)
    
    message = "🍼 **Baby Bottle Tracker**\n\n"
    
    # Show last bottles
    if entries:
        last_entries = entries[-bottles_to_show:]
        message += f"**Derniers biberons:**\n"
        for i, entry in enumerate(reversed(last_entries), 1):
            formatted_time = format_time(entry['time'])
            amount = f"{entry['amount']:>3}ml"
            message += f"`{i}. {amount} à {formatted_time}`\n"
    else:
        message += "**Aucun biberon enregistré**\n"
    
    message += "\n"
    
    # Show last poop(s)
    if poop:
        last_poops = poop[-poops_to_show:]
        message += f"**Dernier{'s' if poops_to_show > 1 else ''} caca{'s' if poops_to_show > 1 else ''}:**\n"
        for i, poop_entry in enumerate(reversed(last_poops), 1):
            formatted_time = format_time(poop_entry['time'])
            message += f"`{i}. {formatted_time}"
            if poop_entry.get('info'):
                message += f" - {poop_entry['info']}"
            message += "`\n"
    else:
        message += "**Aucun caca enregistré**\n"
    
    # Create inline keyboard
    keyboard = [
        [
            InlineKeyboardButton("🍼 Ajouter", callback_data="add_bottle"),
            InlineKeyboardButton("❌ Supprimer", callback_data="remove_bottle")
        ],
        [
            InlineKeyboardButton("💩 Caca", callback_data="add_poop"),
            InlineKeyboardButton("📊 Stats", callback_data="stats")
        ],
        [
            InlineKeyboardButton("⚙️ Paramètres", callback_data="settings")
        ]
    ]
    
    return message, InlineKeyboardMarkup(keyboard)

async def last(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    data = load_data()
    group = find_group_for_user(data, user_id)
    if not group:
        await update.message.reply_text("Vous n'êtes dans aucun groupe et aucun biberon enregistré.")
        return
    entries = data[group]["entries"]
    if not "poop" in data[group]:
        data[group]["poop"] = []
    poop = data[group]["poop"]
    if not entries:
        await update.message.reply_text("Aucun biberon enregistré dans votre groupe.")
    else:
        last_entry = entries[-1]
        formatted_time = format_time(last_entry['time'])
        await update.message.reply_text(f"🍼 Dernier biberon: {last_entry['amount']}ml à {formatted_time}")
    if poop:
        last_poop = poop[-1]
        message = "💩 *Dernier caca:*\n"
        formatted_time = format_time(last_poop['time'])
        message += f"`{formatted_time} "
        if last_poop['info']:
            message += f" - {last_poop['info']}"
        message += "`\n"
        await update.message.reply_text(message)

async def list_biberons_and_poop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    data = load_data()
    group = find_group_for_user(data, user_id)
    if not group:
        await update.message.reply_text("Vous n'êtes dans aucun groupe et aucun biberon enregistré.")
        return
    entries = data[group]["entries"]
    if not "poop" in data[group]:
        data[group]["poop"] = []
    poop = data[group]["poop"]
    if not entries and not poop:
        await update.message.reply_text("Aucun biberon ou caca enregistré.")
        return
    if entries:
        last_entries = entries[-4:]
        message = "🍼 *Liste des 4 derniers biberons:*\n\n"
    for i, entry in enumerate(last_entries, 1):
        formatted_time = format_time(entry['time'])
        amount = f"{entry['amount']:>3}ml"
        line = f"`{i}. {amount} à {formatted_time}`\n"
        message += line

    await update.message.reply_text(message, parse_mode="Markdown")
    if poop:
        last_poop = poop[-1]
        message = "💩 *Dernier caca:*\n"
        formatted_time = format_time(last_poop['time'])
        message += f"`{formatted_time} "
        if last_poop['info']:
            message += f" - {last_poop['info']}"
        message += "`\n"
        await update.message.reply_text(message, parse_mode="Markdown")

async def total(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    data = load_data()
    group = find_group_for_user(data, user_id)
    if not group:
        await update.message.reply_text("Vous n'êtes dans aucun groupe et aucun biberon enregistré.")
        return
    today = datetime.now().strftime("%d-%m-%Y")
    total_ml = sum(entry["amount"] for entry in data[group]["entries"] if today in entry["time"])
    await update.message.reply_text(f"📊 Total aujourd'hui : {total_ml}ml")