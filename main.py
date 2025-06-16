import os
from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder, CommandHandler, ConversationHandler, MessageHandler, filters
from telegram import Update, BotCommand
from handlers.add import add, handle_amount, handle_time, cancel, ASK_AMOUNT, ASK_TIME
from handlers.poop import poop, handle_time_poop, handle_info_poop, ASK_TIME_POOP, ASK_INFO_POOP
from handlers.group import join
from handlers.queries import last, list_biberons_and_poop, total
from handlers.delete import delete
from handlers.admin import save_backup, restore_backup
from handlers.time import time, timeUpdate
from utils import load_backup_from_channel
import sys
import traceback
import asyncio
########################################################
# This part is totally optional, it's just to avoid Render errors
# If you don't use Render, just remove it
########################################################

import threading
import http.server
import socketserver


def run_fake_server():
    PORT = 8080
    Handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        httpd.serve_forever()

threading.Thread(target=run_fake_server, daemon=True).start()

########################################################
# End of fake server
########################################################

async def start(update, context):
    await update.message.reply_text(
        "👋 Hello ! Commandes disponibles :\n"
        "/add - Ajouter un biberon\n"
        "/last - Dernier biberon\n"
        "/total - Total du jour\n"
        "/list - Liste des 4 derniers biberons\n"
        "/delete - Supprime le dernier biberon\n"
        "/poop - Ajouter un caca\n\n"
        "/last - Dernier biberon et dernier caca\n"
        "/list - Liste des 4 derniers biberons et le dernier caca\n"
        "/total - Total du jour\n\n"
        "/join <nom_du_groupe> - Rejoindre un groupe\n"
        "/update_time <HH:MM> - Met à jour l'heure du bot\n"
        "/time - Affiche l'heure du bot\n\n"
        "/help - Affiche cette aide\n\n"
        "Tu peux aussi utiliser /cancel pour annuler l'ajout d'un biberon pendant un /add\n"

    )

async def help_command(update, context):
    await start(update, context)

async def error_handler(update, context):
    print(f"Error: {context.error}")
    # Récupère la trace complète
    exc_type, exc_value, exc_traceback = sys.exc_info()
    tb_lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
    error_text = "".join(tb_lines)

    # Imprime la trace complète dans la console
    print("🔍 Full traceback:")
    print(error_text)
    if update and update.effective_message:
        await update.effective_message.reply_text("❌ Une erreur s'est produite. Veuillez réessayer.")

async def set_commands(app):
        commands = [
            BotCommand("start", "Demarre le bot"),
            BotCommand("help", "Affiche l'aide"),
            BotCommand("add", "Ajoute un biberon"),
            BotCommand("delete", "Supprime le dernier biberon"),
            BotCommand("poop", "Ajoute un caca"),
            BotCommand("last", "Dernier biberon et dernier caca"),
            BotCommand("list", "Liste des derniers biberons et caca"),
            BotCommand("total", "Total du jour"),
            BotCommand("join", "Rejoint un groupe"),
            BotCommand("update_time", "Met à jour l'heure du bot"),
            BotCommand("time", "Affiche l'heure du bot"),
        ]
        await app.bot.set_my_commands(commands)


def main():
    load_dotenv()
    TOKEN = os.getenv("TELEGRAM_TOKEN")

    print("Initializing bot...")
    app = ApplicationBuilder().token(TOKEN).post_init(set_commands).build()

    # Load backup before setting up handlers
    print("Loading backup...")
    try:
        load_backup_from_channel()
        print("Backup loaded successfully")
    except Exception as e:
        print(f"Warning: Could not load backup: {e}")

    print("Setting up bot...")
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("add", add)],
        states={
            ASK_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_amount)],
            ASK_TIME: [MessageHandler(filters.TEXT | filters.COMMAND, handle_time)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    conv_poop_handler = ConversationHandler(
        entry_points=[CommandHandler("poop", poop)],
        states={
        ASK_TIME_POOP: [MessageHandler(filters.TEXT | filters.COMMAND, handle_time_poop)],
        ASK_INFO_POOP: [MessageHandler(filters.TEXT | filters.COMMAND, handle_info_poop)],
    },
    fallbacks=[CommandHandler("cancel", cancel)]
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("last", last))
    app.add_handler(CommandHandler("total", total))
    app.add_handler(CommandHandler("list", list_biberons_and_poop))
    app.add_handler(CommandHandler("delete", delete))
    app.add_handler(CommandHandler("join", join))
    app.add_handler(CommandHandler("save_backup", save_backup))
    app.add_handler(MessageHandler(filters.Document.ALL, restore_backup))
    app.add_handler(conv_handler)
    app.add_error_handler(error_handler)
    app.add_handler(CommandHandler("update_time", timeUpdate))
    app.add_handler(CommandHandler("time", time))
    app.add_handler(conv_poop_handler)
    print("Starting bot...")
    app.run_polling()

if __name__ == "__main__":
    main()