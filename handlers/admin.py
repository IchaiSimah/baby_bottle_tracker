from telegram import Update
from telegram.ext import ContextTypes
from dotenv import load_dotenv
import os

from utils import load_data, save_data

load_dotenv()
ADMIN_ID = os.getenv("ADMIN_ID")

async def save_backup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == int(ADMIN_ID):
        try:
            await update.message.reply_document(document=open("biberons.json", "rb"))
        except Exception as e:
            await update.message.reply_text(f"Error sending file: {e}")
    else:
        await update.message.reply_text("You are not authorized to use this command.")

async def restore_backup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == int(ADMIN_ID):
        try:
            file = await update.message.document
            filename = file.file_name or ""
            if not filename.endswith(".json"):
                await update.message.reply_text("📎 Ce fichier ne peut pas être pris en charge.")
                return
            await file.download_to_drive("biberons.json")
            await update.message.reply_text("✅ Sauvegarde restaurée avec succès.")
        except Exception as e:
            await update.message.reply_text(f"Error charging file: {e}")
    else:
        await update.message.reply_text("You are not authorized to use this command.")