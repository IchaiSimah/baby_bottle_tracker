import os
from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ConversationHandler, ContextTypes
from telegram import Update, BotCommand, InlineKeyboardButton, InlineKeyboardMarkup
from handlers.add import add_bottle, handle_bottle_time, handle_bottle_amount, cancel_bottle, ASK_BOTTLE_TIME, ASK_BOTTLE_AMOUNT
from handlers.poop import add_poop, handle_poop_time, handle_poop_info, cancel_poop, ASK_POOP_TIME, ASK_POOP_INFO
from handlers.delete import delete_bottle, confirm_delete_bottle, cancel_delete_bottle
from handlers.stats import show_stats
from handlers.settings import show_settings, handle_settings, handle_timezone_text_input
from handlers.groups import show_groups_menu, handle_group_actions, create_new_group, join_group
from handlers.queries import get_main_message_content
from utils import load_data, save_data, find_group_for_user, create_personal_group, load_backup_from_channel, get_group_message_info, set_group_message_info, clear_group_message_info
from config import TEST_MODE

import sys
import traceback
import threading
import http.server
import socketserver

# Optional fake server for Render
def run_fake_server():
    PORT = 8080
    Handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        httpd.serve_forever()

threading.Thread(target=run_fake_server, daemon=True).start()

async def start(update, context):
    """Initialize the main message for the user"""
    user_id = update.effective_user.id
    context.user_data['user_id'] = user_id  # Store user_id for utility functions
    
    data = load_data()
    group = find_group_for_user(data, user_id)
    if not group:
        group = create_personal_group(data, user_id)
        await save_data(data, context)
    
    # Create main message with inline keyboard
    message_text, keyboard = get_main_message_content(data, group)
    
    sent_message = await update.message.reply_text(
        message_text,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    
    set_group_message_info(data, group, user_id, sent_message.message_id, sent_message.chat_id)
    await save_data(data, context)
    
    # Delete the user's command message for clean chat
    try:
        await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=update.message.message_id)
    except Exception as e:
        print(f"Failed to delete user command message: {e}")

async def help_command(update, context):
    user_id = update.effective_user.id
    context.user_data['user_id'] = user_id  # Store user_id for utility functions
    
    data = load_data()
    group = find_group_for_user(data, user_id)
    if not group:
        group = create_personal_group(data, user_id)
        await save_data(data, context)
    
    # Create help message with return button
    help_message = "👋 **Baby Bottle Tracker Bot**\n\n" \
                  "**Fonctionnalités principales:**\n" \
                  "• 🍼 Ajouter/supprimer des biberons\n" \
                  "• 💩 Enregistrer les selles\n" \
                  "• 📊 Voir les statistiques\n" \
                  "• ⚙️ Paramètres personnalisables\n\n" \
                  "**Utilisation:**\n" \
                  "Utilisez les boutons dans le message principal pour naviguer.\n" \
                  "Toutes les actions se font dans le même message !"
    
    # Create keyboard with just a return button
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("🏠 Retour", callback_data="refresh")
    ]])
    
    # Try to update existing main message, or create new one
    message_id, chat_id = get_group_message_info(data, group, user_id)
    if message_id and chat_id:
        try:
            await context.bot.edit_message_text(
                text=help_message,
                chat_id=chat_id,
                message_id=message_id,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
        except Exception as e:
            print(f"Failed to edit main message with help: {e}")
            # Fallback: create new message
            sent_message = await update.message.reply_text(
                help_message,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
            set_group_message_info(data, group, user_id, sent_message.message_id, sent_message.chat_id)
            await save_data(data, context)
    else:
        # No existing main message, create new one
        sent_message = await update.message.reply_text(
            help_message,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        set_group_message_info(data, group, user_id, sent_message.message_id, sent_message.chat_id)
        await save_data(data, context)
    
    # Delete the user's command message for clean chat
    try:
        await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=update.message.message_id)
    except Exception as e:
        print(f"Failed to delete user command message: {e}")

async def button_handler(update, context):
    """Handle all inline keyboard button presses"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    context.user_data['user_id'] = user_id  # Store user_id for utility functions
    
    data = load_data()
    group = find_group_for_user(data, user_id)
    if not group:
        group = create_personal_group(data, user_id)
        await save_data(data, context)
    
    # Store the current message ID for this interaction (only for this session)
    context.user_data['main_message_id'] = query.message.message_id
    context.user_data['chat_id'] = query.message.chat.id
    
    action = query.data
    
    if action == "refresh":
        # Refresh main message
        message_text, keyboard = get_main_message_content(data, group)
        await query.edit_message_text(
            text=message_text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    
    elif action == "add_bottle":
        # Start add bottle flow
        context.user_data['action'] = 'add_bottle'
        return await add_bottle(update, context)
    
    elif action == "remove_bottle":
        # Show confirmation dialog for bottle deletion
        await delete_bottle(update, context)
    
    elif action == "confirm_delete":
        # Confirm bottle deletion
        await confirm_delete_bottle(update, context)
    
    elif action == "cancel_delete":
        # Cancel bottle deletion
        await cancel_delete_bottle(update, context)
    
    elif action == "add_poop":
        # Start add poop flow
        context.user_data['action'] = 'add_poop'
        return await add_poop(update, context)
    
    elif action == "stats":
        # Show statistics
        await show_stats(update, context)
    
    elif action == "settings":
        # Show settings
        await show_settings(update, context)
    
    elif action == "groups":
        # Show groups management
        await show_groups_menu(update, context)
    
    elif action.startswith("group_"):
        # Handle group management actions
        await handle_group_actions(update, context)
    
    elif action.startswith("bottle_time_"):
        # Handle bottle time selection
        time_str = action.replace("bottle_time_", "")
        return await handle_bottle_time(update, context, time_str)
    
    elif action.startswith("bottle_amount_"):
        # Handle bottle amount selection
        amount_str = action.replace("bottle_amount_", "")
        return await handle_bottle_amount(update, context, amount_str)
    
    elif action.startswith("poop_time_"):
        # Handle poop time selection
        time_str = action.replace("poop_time_", "")
        return await handle_poop_time(update, context, time_str)
    
    elif action.startswith("poop_info_"):
        # Handle poop info selection
        info = action.replace("poop_info_", "")
        if info == "none":
            info = None
        return await handle_poop_info(update, context)
    
    elif action.startswith("setting_"):
        # Handle settings changes
        setting = action.replace("setting_", "")
        return await handle_settings(update, context, setting)
    
    elif action.startswith("set_bottles_"):
        # Handle bottle count setting
        setting = action.replace("set_bottles_", "")
        return await handle_settings(update, context, f"set_bottles_{setting}")
    
    elif action.startswith("set_poops_"):
        # Handle poop count setting
        setting = action.replace("set_poops_", "")
        return await handle_settings(update, context, f"set_poops_{setting}")
    
    elif action.startswith("set_time_"):
        # Handle time setting
        setting = action.replace("set_time_", "")
        return await handle_settings(update, context, f"set_time_{setting}")
    
    elif action == "manual_time_input":
        # Handle manual time input
        return await handle_settings(update, context, "manual_time_input")
    
    elif action == "cancel":
        # Cancel current action and return to main
        message_text, keyboard = get_main_message_content(data, group)
        await query.edit_message_text(
            text=message_text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )

async def error_handler(update, context):
    print(f"Error: {context.error}")
    exc_type, exc_value, exc_traceback = sys.exc_info()
    tb_lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
    error_text = "".join(tb_lines)
    
    print("🔍 Full traceback:")
    print(error_text)
    
    # Try to show error in main message instead of creating new message
    if update and update.effective_message:
        try:
            # Get main message info
            user_id = update.effective_user.id
            data = load_data()
            group = find_group_for_user(data, user_id)
            message_id, chat_id = get_group_message_info(data, group, user_id)
            
            if message_id and chat_id:
                # Try to edit the main message with error
                from handlers.queries import get_main_message_content
                
                if group:
                    message_text, keyboard = get_main_message_content(data, group)
                    error_text = f"❌ **Une erreur s'est produite**\n\n{message_text}"
                    
                    await context.bot.edit_message_text(
                        text=error_text,
                        chat_id=chat_id,
                        message_id=message_id,
                        reply_markup=keyboard,
                        parse_mode="Markdown"
                    )
                    return
        except Exception as edit_error:
            print(f"Failed to edit main message with error: {edit_error}")
        
        # Fallback: send new error message
        await update.effective_message.reply_text("❌ Une erreur s'est produite. Veuillez réessayer. Erreur: " + str(context.error))

async def set_commands(app):
    commands = [
        BotCommand("start", "Démarrer le bot"),
        BotCommand("help", "Afficher l'aide"),
    ]
    await app.bot.set_my_commands(commands)

async def handle_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text input for time and amount selection"""
    user_id = update.effective_user.id
    context.user_data['user_id'] = user_id  # Store user_id for utility functions
    
    data = load_data()
    group = find_group_for_user(data, user_id)
    
    # Check if user is in a conversation state
    if 'conversation_state' not in context.user_data:
        # User is not in a conversation - show helpful message
        help_message = "💡 **Utilisez les boutons ci-dessous pour interagir avec le bot !**\n\n" \
                      "• 🍼 **Ajouter** - Pour ajouter un biberon\n" \
                      "• 💩 **Caca** - Pour enregistrer un caca\n" \
                      "• 📊 **Stats** - Pour voir les statistiques\n" \
                      "• ⚙️ **Paramètres** - Pour configurer l'affichage"
        
        # Send a temporary help message that will be deleted after a few seconds
        sent_message = await update.message.reply_text(
            help_message,
            parse_mode="Markdown"
        )
        
        # Delete the help message after 3 seconds
        import asyncio
        await asyncio.sleep(3)
        try:
            await context.bot.delete_message(chat_id=sent_message.chat_id, message_id=sent_message.message_id)
        except Exception as e:
            print(f"Failed to delete help message: {e}")
        
        # Delete the user's message for clean chat
        if update.message:
            try:
                await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=update.message.message_id)
            except Exception as e:
                print(f"Failed to delete user message: {e}")
        return
    
    # For text input, we need to get the stored message ID from the group data
    message_id, chat_id = get_group_message_info(data, group, user_id)
    if message_id and chat_id:
        context.user_data['main_message_id'] = message_id
        context.user_data['chat_id'] = chat_id
    
    state = context.user_data['conversation_state']
    text = update.message.text.strip()
    
    if state == 'bottle_time':
        # Handle bottle time text input
        from handlers.add import handle_bottle_time
        await handle_bottle_time(update, context, text)
        
    elif state == 'bottle_amount':
        # Handle bottle amount text input
        from handlers.add import handle_bottle_amount
        await handle_bottle_amount(update, context, text)
        
    elif state == 'poop_time':
        # Handle poop time text input
        from handlers.poop import handle_poop_time
        await handle_poop_time(update, context, text)
    
    elif state == 'poop_info':
        # Handle poop info text input
        from handlers.poop import handle_poop_info
        await handle_poop_info(update, context)
    
    elif state == 'group_rename':
        # Handle group rename text input
        from handlers.groups import rename_group
        current_group = find_group_for_user(data, user_id)
        await rename_group(update, context, current_group, text)
    
    elif state == 'group_create':
        # Handle group create text input
        from handlers.groups import create_new_group
        await create_new_group(update, context, text)
    
    elif state == 'group_join':
        # Handle group join text input
        from handlers.groups import join_group
        await join_group(update, context, text)
    
    elif state == 'timezone_input':
        # Handle timezone input text
        from handlers.settings import handle_timezone_text_input
        await handle_timezone_text_input(update, context, text)
    
    # Don't clear conversation state here - let the individual handlers do it when conversation is complete

    # Delete the user's text message for a clean chat
    if update.message:
        try:
            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=update.message.message_id)
        except Exception as e:
            print(f"Failed to delete user message: {e}")

def main():
    load_dotenv()
    if TEST_MODE:
        TOKEN = os.getenv("TEST_TOKEN")
    else:
        TOKEN = os.getenv("TELEGRAM_TOKEN")

    print("Initializing bot...")
    app = ApplicationBuilder().token(TOKEN).post_init(set_commands).build()
    # Load backup before setting up handlers
    
    print("Loading backup...")
    load_backup_from_channel()

    print("Setting up bot...")
    
    # Add bottle conversation handler
    bottle_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(add_bottle, pattern="^add_bottle$")],
        states={
            ASK_BOTTLE_TIME: [CallbackQueryHandler(handle_bottle_time, pattern="^bottle_time_")],
            ASK_BOTTLE_AMOUNT: [CallbackQueryHandler(handle_bottle_amount, pattern="^bottle_amount_")],
        },
        fallbacks=[CallbackQueryHandler(cancel_bottle, pattern="^cancel$")],
        per_message=True
    )
    
    # Add poop conversation handler
    poop_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(add_poop, pattern="^add_poop$")],
        states={
            ASK_POOP_TIME: [CallbackQueryHandler(handle_poop_time, pattern="^poop_time_")],
            ASK_POOP_INFO: [CallbackQueryHandler(handle_poop_info, pattern="^poop_info_")],
        },
        fallbacks=[CallbackQueryHandler(cancel_poop, pattern="^cancel$")],
        per_message=True
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(bottle_conv_handler)
    app.add_handler(poop_conv_handler)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_input))  # Handle text input
    app.add_error_handler(error_handler)
    
    print("Starting bot...")
    app.run_polling()

if __name__ == "__main__":
    main()