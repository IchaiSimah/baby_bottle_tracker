from telegram import Update
from telegram.ext import ContextTypes
from datetime import datetime, time, timedelta
from utils import load_data, save_data, find_group_for_user

async def join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if len(context.args) == 0:
        await update.message.reply_text("Utilisation: /join <nom_du_groupe>")
        return
    group_name = context.args[0]
    data = load_data()
    if group_name not in data:
        await update.message.reply_text(f"Le groupe {group_name} n'existe pas.")
        return
    if user_id in data[group_name]["users"]:
        await update.message.reply_text(f"Tu fais déjà partie du groupe {group_name}.")
        return
    old_group = find_group_for_user(data, user_id)
    if old_group:
        data[old_group]["users"].remove(user_id)
    data[group_name]["users"].append(user_id)
    data[group_name]["time_difference"] = timedelta(0)
    await save_data(data, context)
    await update.message.reply_text(f"✅ Tu as rejoint le groupe {group_name}.")