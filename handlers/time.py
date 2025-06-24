from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from utils import load_data, save_data, find_group_for_user
from telegram import Update
from telegram.ext import ContextTypes

async def time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    group = find_group_for_user(data, update.effective_user.id)
    if not group:
        adjusted_time = datetime.now(ZoneInfo("UTC"))
    else:
        td = data[group]["time_difference"]
        if td is None:
            td = 0
        adjusted_time = datetime.now(ZoneInfo("UTC")) + timedelta(hours=td)
    await update.message.reply_text(f"🕐 L'heure du bot est : {adjusted_time.strftime('%H:%M')}")

async def timeUpdate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    time_str = context.args[0]
    actual_time = datetime.strptime(time_str, "%H:%M").time()
    data = load_data()
    group = find_group_for_user(data, update.effective_user.id)
    now = datetime.now(ZoneInfo("UTC"))

    target_hour = actual_time.hour
    current_hour = now.hour
    diff_hour = target_hour - current_hour

    data[group]["time_difference"] = diff_hour
    await save_data(data, context)
    await update.message.reply_text(f"✅ L'heure du bot a été mise à jour à : {time_str} 🕐")