import os
from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder, CommandHandler, ConversationHandler, MessageHandler, filters

from handlers.add import add, handle_amount, handle_time, cancel, ASK_AMOUNT, ASK_TIME
from handlers.group import join
from handlers.queries import last, list_biberons, total
from handlers.delete import delete
from handlers.admin import save_backup, restore_backup
from utils import load_backup_from_channel

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
        "/join <nom_du_groupe> - Rejoindre un groupe\n"
        "/help - Affiche cette aide\n"
    )

async def help_command(update, context):
    await start(update, context)

async def error_handler(update, context):
    print(f"Error: {context.error}")
    if update and update.effective_message:
        await update.effective_message.reply_text("❌ Une erreur s'est produite. Veuillez réessayer.")

async def load_backup_on_startup(app):
    try:
        print("Attempting to load backup data from channel...")
        # Wait a bit for the bot to be fully initialized
        await asyncio.sleep(5)
        await load_backup_from_channel(app)
        print("Backup data loaded successfully.")
    except Exception as e:
        print(f"Warning: Could not load backup data: {e}")
        print("Bot will continue with existing data file.")

async def main():
    load_dotenv()
    TOKEN = os.getenv("TELEGRAM_TOKEN")

    print("Initializing bot...")
    app = ApplicationBuilder().token(TOKEN).build()

    # Start backup loading in background
    asyncio.create_task(load_backup_on_startup(app))

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("add", add)],
        states={
            ASK_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_amount)],
            ASK_TIME: [MessageHandler(filters.TEXT | filters.COMMAND, handle_time)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("last", last))
    app.add_handler(CommandHandler("total", total))
    app.add_handler(CommandHandler("list", list_biberons))
    app.add_handler(CommandHandler("delete", delete))
    app.add_handler(CommandHandler("join", join))
    app.add_handler(CommandHandler("save_backup", save_backup))
    app.add_handler(MessageHandler(filters.Document.ALL, restore_backup))
    app.add_handler(conv_handler)

    app.add_error_handler(error_handler)

    print("Bot started.")
    await app.initialize()  # Ensure bot is properly initialized
    await app.start()
    await app.run_polling()
    await app.stop()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())