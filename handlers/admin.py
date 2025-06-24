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
            await update.message.reply_text(f"❌ Erreur lors de l'envoi du fichier : {e}")
    else:
        await update.message.reply_text("❌ Vous n'êtes pas autorisé à utiliser cette commande.")

async def restore_backup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == int(ADMIN_ID):
        try:
            document = update.message.document
            if not document:
                await update.message.reply_text("📎 Envoie un fichier .json en pièce jointe.")
                return

            filename = document.file_name or ""
            if not filename.endswith(".json"):
                await update.message.reply_text("📎 Ce fichier ne peut pas être pris en charge.")
                return

            file = await context.bot.get_file(document.file_id)
            await file.download_to_drive("biberons.json")

            await update.message.reply_text("✅ Sauvegarde restaurée avec succès ! 🎉")
        except Exception as e:
            await update.message.reply_text(f"❌ Erreur pendant la restauration : {e}")
    else:
        await update.message.reply_text("❌ Tu n'es pas autorisé à utiliser cette commande.")