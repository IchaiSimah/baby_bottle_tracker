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
            if not update.message.document:
                await update.message.reply_text("📎 Envoie un fichier .json en pièce jointe.")
                return
            file = await update.message.document.get_file()
            await file.download_to_drive("biberons.json")
            await update.message.reply_text("✅ Sauvegarde restaurée avec succès.")
        except Exception as e:
            await update.message.reply_text(f"Error sending file: {e}")
    else:
        await update.message.reply_text("You are not authorized to use this command.")