import os
from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from telegram import Update, BotCommand, InlineKeyboardButton, InlineKeyboardMarkup
from handlers.add import add_bottle, handle_bottle_time, handle_bottle_amount
from handlers.poop import add_poop, handle_poop_time, handle_poop_info
from handlers.delete import delete_bottle, confirm_delete_bottle, cancel_delete_bottle
from handlers.stats import show_stats
from handlers.settings import show_settings, handle_settings
from handlers.groups import show_groups_menu, handle_group_actions
from handlers.queries import get_main_message_content, get_main_message_content_for_user
from handlers.pdf import show_pdf_menu, handle_pdf_callback
from utils import load_data, save_data, find_group_for_user, create_personal_group, get_group_message_info, set_group_message_info, load_user_data
from config import TEST_MODE
from handlers.shabbat import (
    start_shabbat,
    handle_shabbat_friday_poop,
    handle_shabbat_friday_bottle,
    handle_shabbat_saturday_poop,
    handle_shabbat_saturday_bottle
)
from translations import t
from database import get_language

import sys
import traceback

async def start(update, context):
    """Initialize the main message for the user"""
    user_id = update.effective_user.id
    context.user_data['user_id'] = user_id  # Store user_id for utility functions
    
    print(f"DEBUG START: Starting /start for user {user_id}")
    
    # Use optimized data loading
    data = load_user_data(user_id)
    print(f"DEBUG START: load_user_data returned: {data}")
    if not data:
        print("No data found")
        # Fallback to create personal group if needed
        data = load_data()
        group_id = find_group_for_user(data, user_id)
        print(f"DEBUG START: find_group_for_user returned: {group_id}")
        if not group_id:
            print("Creating personal group")
            group_id = create_personal_group(data, user_id)
            if group_id:
                data = load_user_data(user_id)
    
    if not data:
        language = get_language(user_id)
        error_msg = t("error_load_data", language)
        await update.message.reply_text(error_msg)
        return
    
    # Get group info
    group_id = find_group_for_user(data, user_id)
    print(f"DEBUG START: Group ID found: {group_id}")
    
    if not group_id:
        language = get_language(user_id)
        error_msg = t("error_find_group", language)
        await update.message.reply_text(error_msg)
        return
    
    group_info = data.get(group_id, {})
    group_name = group_info.get('name', str(group_id))
    print(f"DEBUG START: Group name: {group_name}")
    
    # Check if main message exists for this group/user
    message_info = get_group_message_info(data, group_id, user_id)
    print(f"DEBUG START: Message info for group {group_id}, user {user_id}: {message_info}")
    
    # Supprimer l'ancien message principal s'il existe
    if message_info:
        # message_info est un tuple (message_id, chat_id)
        old_message_id, old_chat_id = message_info
        print(f"DEBUG START: Suppression de l'ancien message - ID: {old_message_id}, Chat: {old_chat_id}")
        try:
            await context.bot.delete_message(chat_id=old_chat_id, message_id=old_message_id)
            print(f"DEBUG START: Ancien message supprimé avec succès")
        except Exception as e:
            print(f"DEBUG START: Erreur lors de la suppression de l'ancien message: {e}")
    
    # Create main message with inline keyboard
        message_text = "loading..."
        keyboard = None
    # Toujours créer un nouveau message principal
        sent_message = await update.message.reply_text(
            message_text,
            reply_markup=keyboard,
            parse_mode="Markdown"
    )
    
    print(f"DEBUG START: Nouveau message créé - ID: {sent_message.message_id}, Chat: {sent_message.chat_id}")
    
    # Mettre à jour l'ID du message principal dans la base
    set_group_message_info(data, group_id, user_id, sent_message.message_id, sent_message.chat_id)
    await save_data(data, context)
    current = "en"
    keyboard = []
        
    # Create rows of 3 buttons each
    options = [("fr", "français"), ("en", "english"), ("he", "עברית")]
    keyboard = []
    row = []
    for option in options:
        text = f"{option[1]} {'✅' if option[0] == current else ''}"
        row.append(InlineKeyboardButton(text, callback_data=f"set_language_{option[0]}"))
    if row:
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton(t("btn_cancel", "en"), callback_data="settings")])

    message = t("language_question", "en")

    await context.bot.edit_message_text(
        chat_id=sent_message.chat_id,
        message_id=sent_message.message_id,
        text=message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    # Delete the user's command message for clean chat
    try:
        await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=update.message.message_id)
    except Exception as e:
        print(f"Failed to delete user command message: {e}")
        # After creating the main message, immediately show the language choice menu

        

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
        language = get_language(user_id)
        error_msg = t("error_create_group", language)
        if hasattr(update, 'message') and update.message:
            await update.message.reply_text(error_msg)
        elif hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.edit_message_text(error_msg)
        return
    
    # Get the group ID from the loaded data
    group_id = list(data.keys())[0]
    language = get_language(user_id)
    help_message = t("help_title", language) + t("help_features", language) + t("help_usage", language)
    # Create keyboard with just a return button
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton(t("btn_return", language), callback_data="refresh")]])
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
        language = get_language(user_id)
        error_msg = t("error_create_group", language)
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
    set_group_message_info(data, group_id, user_id, query.message.message_id, query.message.chat.id)
    
    action = query.data
    
    if action == "refresh" or action == "cancel":
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
        return await delete_bottle(update, context)

    elif action == "confirm_delete":
        # Confirm bottle deletion
        return await confirm_delete_bottle(update, context)

    elif action == "cancel_delete":
        # Cancel bottle deletion
        return await cancel_delete_bottle(update, context)

    elif action == "add_poop":
        # Start add poop flow
        context.user_data['action'] = 'add_poop'
        return await add_poop(update, context)
    
    elif action == "stats":
        # Show statistics
        return await show_stats(update, context)
    
    elif action == "settings":
        # Show settings menu
        return await show_settings(update, context)
    
    elif action == "groups":
        # Show groups menu
        return await show_groups_menu(update, context)
    
    elif action == "pdf_menu":
        # Show PDF menu
        return await show_pdf_menu(update, context)
    
    elif action == "shabbat":
        # Start Shabbat mode
        return await start_shabbat(update, context)
    
    elif action.startswith("group_"):
        # Handle group-related actions
        return await handle_group_actions(update, context)

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
    
    elif action.startswith("pdf_"):
        # Handle PDF-related actions
        return await handle_pdf_callback(update, context)
    
    elif action.startswith("setting_"):
        # Handle settings-related actions
        return await handle_settings(update, context)
    
    elif action.startswith("set_bottles_"):
        # Handle bottle count setting
        setting = action.replace("set_bottles_", "")
        return await handle_settings(update, context, f"set_bottles_{setting}")

    elif action.startswith("set_last_bottle_"):
        # Handle last bottle setting
        setting = action.replace("set_last_bottle_", "")
        return await handle_settings(update, context, f"set_last_bottle_{setting}")
    
    elif action.startswith("set_poops_"):
        # Handle poop count setting
        setting = action.replace("set_poops_", "")
        return await handle_settings(update, context, f"set_poops_{setting}")

    elif action.startswith("set_time_"):
        # Handle time setting
        setting = action.replace("set_time_", "")
        return await handle_settings(update, context, f"set_time_{setting}")

    elif action.startswith("set_language_"):
        # Handle language setting
        setting = action.replace("set_language_", "")
        return await handle_settings(update, context, f"set_language_{setting}")

    elif action == "manual_time_input":
        # Handle manual time input
        return await handle_settings(update, context, "manual_time_input")

    elif action.startswith("shabbat_"):
        # Handle Shabbat-related actions
        if action == "shabbat_friday_poop":
            return await handle_shabbat_friday_poop(update, context)
        elif action == "shabbat_friday_bottle":
            return await handle_shabbat_friday_bottle(update, context)
        elif action == "shabbat_saturday_poop":
            return await handle_shabbat_saturday_poop(update, context)
        elif action == "shabbat_saturday_bottle":
            return await handle_shabbat_saturday_bottle(update, context)
    
    elif action.startswith("delete_"):
        # Handle delete-related actions
        if action == "delete_confirm":
            return await confirm_delete_bottle(update, context)
        elif action == "delete_cancel":
            return await cancel_delete_bottle(update, context)
    
    else:
        # Unknown action
        print(f"Unknown action: {action}")
        language = get_language(user_id)
        await query.edit_message_text(t("error_unknown_action", language))

async def error_handler(update, context):
    """Handle errors gracefully"""
    print(f"Exception while handling an update: {context.error}")
    
    # Log the full traceback
    traceback.print_exception(type(context.error), context.error, context.error.__traceback__)
    
    # Try to send a user-friendly error message
    try:
        if update and update.effective_user:
            user_id = update.effective_user.id
            language = get_language(user_id)
            # Try to get user data to show error in main message
            try:
                data = load_user_data(user_id)
                if data:
                    group_id = find_group_for_user(data, user_id)
                    if group_id:
                        message_id, chat_id = get_group_message_info(data, group_id, user_id)
                        
                        if message_id and chat_id:
                            # Try to edit the main message with error
                            from handlers.queries import get_main_message_content
                            
                            if group_id:
                                message_text, keyboard = get_main_message_content(data, group_id, language)
                                error_text = f"{t('error_general', language)}**\n\n{message_text}"
                                
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
            language = get_language(user_id)
        await update.effective_message.reply_text(t("error_general", language) + " " + str(context.error))
    except Exception as e:
        print(f"Failed to send error message: {e}")

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
    language = get_language(user_id)
    group_id = find_group_for_user(data, user_id)
    if not group_id:
        group_id = create_personal_group(data, user_id)
        await save_data(data, context)
    if not group_id or group_id not in data:
        error_msg = t("error_create_group", language)
        if hasattr(update, 'message') and update.message:
            await update.message.reply_text(error_msg)
        elif hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.edit_message_text(error_msg)
        return
    
    # Check if user is in a conversation state
    if 'conversation_state' not in context.user_data:
        # User is not in a conversation - show helpful message
        help_message = t("help_no_input", language)
        
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

    elif state == 'id_check_group_join':
        # Handle group join id check
        from handlers.groups import id_check_group_join
        await id_check_group_join(update, context, text)
    
    elif state == 'last_bottle':
        from handlers.settings import handle_last_bottle_text_input
        await handle_last_bottle_text_input(update, context, text)

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
    
    # Don't clear conversation state here - let the individual handlers do it when conversation is complete

    # Delete the user's text message for a clean chat
    if update.message and update.effective_chat:
        try:
            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=update.message.message_id)
        except Exception as e:
            print(f"Failed to delete user message: {e}")

def main():
    """Main function to start the bot"""
    # Load environment variables
    load_dotenv()
    
    # Get bot token
    if TEST_MODE:
        token = os.getenv('TEST_TOKEN')
        print("Running in TEST mode")
    else:
        token = os.getenv('TELEGRAM_TOKEN')
        print("Running in PRODUCTION mode")
    
    if not token:
        print("❌ No bot token found. Please set TELEGRAM_TOKEN or TEST_TOKEN in your .env file")
        return
    
    # Create application
    application = ApplicationBuilder().token(token).post_init(set_commands).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    
    # Add callback query handler for inline keyboard buttons
    application.add_handler(CallbackQueryHandler(button_handler))
    
    # Add message handler for text input
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_input))
    
    # Add error handler
    application.add_error_handler(error_handler)
    
    print("🤖 Bot started successfully!")
    print("Press Ctrl+C to stop the bot")
    
    # Start the bot
    application.run_polling()

if __name__ == "__main__":
    main()