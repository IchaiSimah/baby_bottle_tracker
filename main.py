import os
from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from telegram import Update, BotCommand, InlineKeyboardButton, InlineKeyboardMarkup
from handlers.add import add_bottle, handle_bottle_time, handle_bottle_amount, cancel_bottle
from handlers.poop import add_poop, handle_poop_time, handle_poop_info, cancel_poop
from handlers.delete import delete_bottle, confirm_delete_bottle, cancel_delete_bottle
from handlers.stats import show_stats
from handlers.settings import show_settings, handle_settings, handle_timezone_text_input
from handlers.groups import show_groups_menu, handle_group_actions, create_new_group, join_group
from handlers.queries import get_main_message_content, get_main_message_content_for_user
from handlers.pdf import show_pdf_menu, handle_pdf_callback, generate_pdf_report
from utils import load_data, save_data, find_group_for_user, create_personal_group, get_group_message_info, set_group_message_info, clear_group_message_info, get_performance_stats, load_user_data, safe_edit_message_text_with_query
from config import TEST_MODE
from handlers.shabbat import (
    start_shabbat,
    handle_shabbat_friday_poop,
    handle_shabbat_friday_bottle,
    handle_shabbat_saturday_poop,
    handle_shabbat_saturday_bottle
)

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
    
    # Use optimized data loading
    data = load_user_data(user_id)
    if not data:
        print("No data found")
        # Fallback to create personal group if needed
        data = load_data()
        group_id = find_group_for_user(data, user_id)
        if not group_id:
            print("Creating personal group")
            group_id = create_personal_group(data, user_id)
            print("Group created: ", group_id)
            await save_data(data, context)
            # Reload user data after creating group
            data = load_user_data(user_id)
    
    if not data:
        error_msg = "❌ Oups ! Impossible de trouver ou créer votre groupe personnel pour le moment. Merci de réessayer plus tard."
        if hasattr(update, 'message') and update.message:
            await update.message.reply_text(error_msg)
        elif hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.edit_message_text(error_msg)
        return
    
    # Get the group ID from the loaded data
    group_id = list(data.keys())[0]
    
    # Create main message with inline keyboard
    message_text, keyboard = get_main_message_content(data, group_id)
    
    sent_message = await update.message.reply_text(
        message_text,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    
    set_group_message_info(data, group_id, user_id, sent_message.message_id, sent_message.chat_id)
    await save_data(data, context)
    
    # Delete the user's command message for clean chat
    try:
        await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=update.message.message_id)
    except Exception as e:
        print(f"Failed to delete user command message: {e}")

async def help_command(update, context):
    """Show help information in the main message"""
    user_id = update.effective_user.id
    context.user_data['user_id'] = user_id  # Store user_id for utility functions
    
    # Use optimized data loading
    data = load_user_data(user_id)
    if not data:
        # Fallback to create personal group if needed
        data = load_data()
        group_id = find_group_for_user(data, user_id)
        if not group_id:
            group_id = create_personal_group(data, user_id)
            await save_data(data, context)
            # Reload user data after creating group
            data = load_user_data(user_id)
    
    if not data:
        error_msg = "❌ Oups ! Impossible de trouver ou créer votre groupe personnel pour le moment. Merci de réessayer plus tard."
        if hasattr(update, 'message') and update.message:
            await update.message.reply_text(error_msg)
        elif hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.edit_message_text(error_msg)
        return
    
    # Get the group ID from the loaded data
    group_id = list(data.keys())[0]
    
    # Create help message with return button
    help_message = "👋 **Baby Bottle Tracker Bot** 🍼\n\n" \
                  "**✨ Fonctionnalités principales :**\n" \
                  "• 🍼 Ajouter/supprimer des biberons\n" \
                  "• 💩 ajouter des cacas\n" \
                  "• 📊 Voir les statistiques\n" \
                  "• ⚙️ Paramètres personnalisables\n\n" \
                  "**🎯 Utilisation :**\n" \
                  "Utilisez les boutons dans le message principal pour naviguer.\n" \
                  "Toutes les actions se font dans le même message !"
    
    # Create keyboard with just a return button
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("🏠 Retour", callback_data="refresh")
    ]])
    
    # Get existing main message info
    message_id, chat_id = get_group_message_info(data, group_id, user_id)
    
    if message_id and chat_id:
        # Try to edit existing main message
        try:
            await context.bot.edit_message_text(
                text=help_message,
                chat_id=chat_id,
                message_id=message_id,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
        except Exception as e:
            if "Message is not modified" in str(e):
                print("ℹ️ Message content unchanged, skipping edit")
            else:
                print(f"Failed to edit main message with help: {e}")
                # If editing fails, create a new message
                sent_message = await update.message.reply_text(
                    help_message,
                    reply_markup=keyboard,
                    parse_mode="Markdown"
                )
                set_group_message_info(data, group_id, user_id, sent_message.message_id, sent_message.chat_id)
                await save_data(data, context)
    else:
        # No existing main message, create new one
        sent_message = await update.message.reply_text(
            help_message,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        set_group_message_info(data, group_id, user_id, sent_message.message_id, sent_message.chat_id)
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
    
    # Use optimized data loading
    data = load_user_data(user_id)
    if not data:
        # Fallback to create personal group if needed
        data = load_data()
        group_id = find_group_for_user(data, user_id)
        if not group_id:
            group_id = create_personal_group(data, user_id)
            await save_data(data, context)
            # Reload user data after creating group
            data = load_user_data(user_id)
    
    if not data:
        error_msg = "❌ Oups ! Impossible de trouver ou créer votre groupe personnel pour le moment. Merci de réessayer plus tard."
        if hasattr(update, 'message') and update.message:
            await update.message.reply_text(error_msg)
        elif hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.edit_message_text(error_msg)
        return
    
    # Get the group ID from the loaded data
    group_id = list(data.keys())[0]
    
    # Store the current message ID for this interaction (only for this session)
    context.user_data['main_message_id'] = query.message.message_id
    context.user_data['chat_id'] = query.message.chat.id
    
    action = query.data
    
    if action == "refresh":
        # Refresh main message using optimized function
        # Clear conversation state when returning to main
        context.user_data.pop('conversation_state', None)
        message_text, keyboard = get_main_message_content_for_user(user_id)
        try:
            await query.edit_message_text(
                text=message_text,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
        except Exception as e:
            if "Message is not modified" in str(e):
                print("ℹ️ Message content unchanged, skipping edit")
            else:
                raise e
    
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
    
    elif action == "pdf_menu":
        # Show PDF menu
        await show_pdf_menu(update, context)
    
    elif action.startswith("pdf_"):
        # Handle PDF actions
        await handle_pdf_callback(update, context)
    
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
        # Clear conversation state when canceling
        context.user_data.pop('conversation_state', None)
        message_text, keyboard = get_main_message_content(data, group_id)
        try:
            await query.edit_message_text(
                text=message_text,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
        except Exception as e:
            if "Message is not modified" in str(e):
                print("ℹ️ Message content unchanged, skipping edit")
            else:
                raise e
    
    elif action == "shabbat":
        return await start_shabbat(update, context)
    
    elif action.startswith("setting_last_bottle"):
        return await handle_settings(update, context, "last_bottle")
    elif action.startswith("set_last_bottle_"):
        setting = action.replace("set_last_bottle_", "set_last_bottle_")
        return await handle_settings(update, context, setting)
    elif action == "manual_last_bottle_input":
        return await handle_settings(update, context, "manual_last_bottle_input")

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
            group_id = find_group_for_user(data, user_id)
            message_id, chat_id = get_group_message_info(data, group_id, user_id)
            
            if message_id and chat_id:
                # Try to edit the main message with error
                from handlers.queries import get_main_message_content
                
                if group_id:
                    message_text, keyboard = get_main_message_content(data, group_id)
                    error_text = f"❌ **Une erreur s'est produite**\n\n{message_text}"
                    
                    try:
                        await context.bot.edit_message_text(
                            text=error_text,
                            chat_id=chat_id,
                            message_id=message_id,
                            reply_markup=keyboard,
                            parse_mode="Markdown"
                        )
                    except Exception as e:
                        if "Message is not modified" in str(e):
                            print("ℹ️ Message content unchanged, skipping edit")
                        else:
                            raise e
                    return
        except Exception as edit_error:
            print(f"Failed to edit main message with error: {edit_error}")
        
        # Fallback: send new error message
        await update.effective_message.reply_text("❌ Une erreur s'est produite. Veuillez réessayer. Erreur: " + str(context.error))

async def performance_command(update, context):
    """Show performance statistics for debugging"""
    user_id = update.effective_user.id
    
    # Get performance stats
    stats = get_performance_stats()
    
    message = "📊 **Performance Statistics**\n\n"
    message += f"**Cache Performance:**\n"
    message += f"• Cache hits: {stats['cache_hits']}\n"
    message += f"• Cache misses: {stats['cache_misses']}\n"
    message += f"• Hit rate: {stats['cache_hit_rate']}\n"
    message += f"• Total requests: {stats['total_requests']}\n\n"
    message += f"**Database:**\n"
    message += f"• DB calls: {stats['db_calls']}\n\n"
    message += f"**Response Times:**\n"
    message += f"• Average: {stats['avg_response_time']}\n"
    
    # Create keyboard
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("🏠 Accueil", callback_data="refresh")
    ]])
    
    await update.message.reply_text(
        message,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    
    # Delete the user's command message for clean chat
    try:
        await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=update.message.message_id)
    except Exception as e:
        print(f"Failed to delete user command message: {e}")

async def set_commands(app):
    commands = [
        BotCommand("start", "Démarrer le bot"),
        BotCommand("help", "Afficher l'aide")
    ]
    await app.bot.set_my_commands(commands)

async def handle_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text input for non-conversation cases"""
    # Check if update and user are valid
    if not update or not update.effective_user:
        return
    
    user_id = update.effective_user.id
    if not context.user_data:
        context.user_data = {}
    context.user_data['user_id'] = user_id  # Store user_id for utility functions
    
    # Use optimized data loading
    data = load_user_data(user_id)
    if not data:
        data = load_data()
    
    group_id = find_group_for_user(data, user_id)
    if not group_id:
        group_id = create_personal_group(data, user_id)
        await save_data(data, context)
    if not group_id or group_id not in data:
        error_msg = "❌ Erreur : impossible de trouver ou créer votre groupe personnel. Merci de réessayer plus tard."
        if hasattr(update, 'message') and update.message:
            await update.message.reply_text(error_msg)
        elif hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.edit_message_text(error_msg)
        return
    
    # Check if user is in a conversation state
    if 'conversation_state' not in context.user_data:
        # User is not in a conversation - show helpful message
        help_message = "💡 **aucune saisie n'est requise**\n\n" \
                      "• ⚙️ utilisez les boutons pour interagir avec le bot !"
        
        try:
            # Send a temporary help message that will be deleted after a few seconds
            if update.message:
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
        except Exception as e:
            print(f"Error sending help message: {e}")
        
        # Delete the user's message for clean chat
        if update.message and update.effective_chat:
            try:
                await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=update.message.message_id)
            except Exception as e:
                print(f"Failed to delete user message: {e}")
        return
    
    # For text input, we need to get the stored message ID from the group data
    message_id, chat_id = get_group_message_info(data, group_id, user_id)
    if message_id and chat_id:
        context.user_data['main_message_id'] = message_id
        context.user_data['chat_id'] = chat_id
    
    state = context.user_data['conversation_state']
    if not update.message or not update.message.text:
        return
    
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
        if current_group:
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
    
    elif state == 'shabbat_friday_poop':
        await handle_shabbat_friday_poop(update, context)
    elif state == 'shabbat_friday_bottle':
        await handle_shabbat_friday_bottle(update, context)
    elif state == 'shabbat_saturday_poop':
        await handle_shabbat_saturday_poop(update, context)
    elif state == 'shabbat_saturday_bottle':
        await handle_shabbat_saturday_bottle(update, context)
    
    elif state == 'last_bottle_input':
        from handlers.settings import handle_last_bottle_text_input
        await handle_last_bottle_text_input(update, context, text)
    
    # Don't clear conversation state here - let the individual handlers do it when conversation is complete

    # Delete the user's text message for a clean chat
    if update.message and update.effective_chat:
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

    if not TOKEN:
        print("❌ Error: No Telegram token found in environment variables!")
        print("Please set either TEST_TOKEN or TELEGRAM_TOKEN in your .env file")
        return

    print("Initializing bot...")
    app = ApplicationBuilder().token(TOKEN).post_init(set_commands).build()
    # No backup loading needed with Supabase
    print("Setting up bot...")

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("performance", performance_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_input))  # Handle text input
    app.add_error_handler(error_handler)
    
    print("Starting bot...")
    app.run_polling()

if __name__ == "__main__":
    main()