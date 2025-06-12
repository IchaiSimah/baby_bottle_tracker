from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes

from utils import load_data, find_group_for_user

async def last(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    data = load_data()
    group = find_group_for_user(data, user_id)
    if not group:
        await update.message.reply_text("Vous n'êtes dans aucun groupe et aucun biberon enregistré.")
        return
    entries = data[group]["entries"]
    if not entries:
        await update.message.reply_text("Aucun biberon enregistré dans votre groupe.")
        return
    last_entry = entries[-1]
    await update.message.reply_text(f"🍼 Dernier biberon: {last_entry['amount']}ml à {last_entry['time']}")

async def list_biberons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    data = load_data()
    group = find_group_for_user(data, user_id)
    if not group:
        await update.message.reply_text("Vous n'êtes dans aucun groupe et aucun biberon enregistré.")
        return
    entries = data[group]["entries"]
    if not entries:
        await update.message.reply_text("Aucun biberon enregistré.")
        return
    last_entries = entries[-4:]
    message = "🍼 *Liste des 4 derniers biberons:*\n\n"
    for i, entry in enumerate(last_entries, 1):
        dt_parts = entry['time'].split(' ')
        date_parts = dt_parts[0].split('-')
        time_parts = dt_parts[1].split(':')

        hour = time_parts[0].zfill(2)
        minute = time_parts[1]
        formatted_time = f"{hour}:{minute}"
        formatted_date = f"{date_parts[0]}-{date_parts[1]}"

        amount = f"{entry['amount']:>3}ml"
        line = f"`{i}. {amount} à {formatted_time} le {formatted_date}`\n"
        message += line

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