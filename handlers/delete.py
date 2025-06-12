from telegram import Update
from telegram.ext import ContextTypes

from utils import load_data, save_data, find_group_for_user

async def delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    data = load_data()
    group = find_group_for_user(data, user_id)
    if not group:
        await update.message.reply_text("Vous n'êtes dans aucun groupe, rien à supprimer.")
        return
    if not data[group]["entries"]:
        await update.message.reply_text("Aucun biberon à supprimer dans votre groupe.")
        return
    data[group]["entries"].pop()
    await save_data(data, context)
    await update.message.reply_text(f"✅ Dernier biberon supprimé dans {group}.")