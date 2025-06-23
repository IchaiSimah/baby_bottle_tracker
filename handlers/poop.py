from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters, CallbackQueryHandler
from zoneinfo import ZoneInfo
from utils import load_data, save_data, find_group_for_user, create_personal_group, is_valid_time, normalize_time, getValidDate, delete_user_message, update_main_message, ensure_main_message_exists, set_group_message_info
from config import TEST_MODE

ASK_POOP_TIME, ASK_POOP_INFO = range(2)

def round_to_nearest_quarter_hour(minutes, base=15):
    fraction = minutes % base
    if fraction == 0:
        return minutes  
    elif fraction < (base / 2):
        rounded = minutes - fraction
    else:
        rounded = minutes + (base - fraction)
    return int(rounded)

async def add_poop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start the add poop flow - show time selection"""
    query = update.callback_query
    await query.answer()
    
    data = load_data()
    user_id = update.effective_user.id
    group = find_group_for_user(data, user_id)
    if not group:
        group = create_personal_group(data, user_id)
        await save_data(data, context)
    
    time_difference = timedelta(hours=data[group].get("time_difference", 0))
    
    # Generate time suggestions

    current_time = datetime.now(ZoneInfo("UTC")) + time_difference
    
    suggestions = []
    for minutes in [60, 45, 30, 15]:
        suggestion_time = current_time - timedelta(minutes=minutes)
        minutes_rounded = round_to_nearest_quarter_hour(suggestion_time.minute)
        hour_rounded = suggestion_time.hour
        if minutes_rounded == 60:
            minutes_rounded = 0
            hour_rounded += 1
        if hour_rounded == 24:
            hour_rounded = 0
        suggested_time = datetime.now().replace(hour=hour_rounded, minute=minutes_rounded)
        suggestions.append(suggested_time.strftime("%H:%M"))
    
    # Create keyboard with time buttons
    keyboard = []
    for time_str in suggestions:
        keyboard.append([InlineKeyboardButton(time_str, callback_data=f"poop_time_{time_str}")])
    
    # Add "Now" and "Cancel" buttons
    keyboard.append([
        InlineKeyboardButton("🕐 Maintenant", callback_data="poop_time_now"),
        InlineKeyboardButton("❌ Annuler", callback_data="cancel")
    ])
    
    message = "⏰ **Choisissez l'heure du caca:**\n\n*Ou tapez une heure manuellement (ex: 14:30)*"
    
    # Set conversation state for text input
    context.user_data['conversation_state'] = 'poop_time'
    
    await query.edit_message_text(
        text=message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    
    return ASK_POOP_TIME

async def handle_poop_time(update: Update, context: ContextTypes.DEFAULT_TYPE, time_str: str = None):
    """Handle time selection and ask for additional info"""
    # Check if this is a callback query or text message
    if hasattr(update, 'callback_query') and update.callback_query:
        query = update.callback_query
        await query.answer()
        if not time_str:
            # Extract time from callback data
            time_str = query.data.replace("poop_time_", "")
    else:
        # This is a text message - delete it immediately
        query = None
        if not time_str:
            time_str = update.message.text.strip()
        # Delete user message for clean chat
        await delete_user_message(context, update.effective_chat.id, update.message.message_id)
    
    data = load_data()
    user_id = update.effective_user.id
    group = find_group_for_user(data, user_id)
    time_difference = timedelta(hours=data[group].get("time_difference", 0))
    try:
        if time_str.lower() == "now":
            time_str = (datetime.now(ZoneInfo("UTC")) + time_difference).strftime("%d-%m-%Y %H:%M")
            date = time_str.split(" ")[0]
            time_str = time_str.split(" ")[1]
        else:
            date = getValidDate(time_str, data[group].get("time_difference", 0))
        # Normalize and validate time format
        normalized_time = normalize_time(time_str)
        if not is_valid_time(normalized_time):
            error_msg = "❌ Format d'heure invalide. Veuillez réessayer."
            if query:
                await query.edit_message_text(
                    error_msg,
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("❌ Annuler", callback_data="cancel")
                    ]])
                )
            else:
                # Use utility function to update main message
                await ensure_main_message_exists(update, context, data, group)
                await update_main_message(context, error_msg, InlineKeyboardMarkup([[
                    InlineKeyboardButton("❌ Annuler", callback_data="cancel")
                ]]))
            return ASK_POOP_TIME
        # Store normalized time in context
        context.user_data['poop_time'] = f"{date} {normalized_time}"
        # Ask for additional info with predefined options
        keyboard = [
            [InlineKeyboardButton("✅ Terminer", callback_data="poop_info_none")],
            [InlineKeyboardButton("❌ Annuler", callback_data="cancel")]
        ]
        message = f"💩 **Caca enregistré à {normalized_time}**\n\nCliquez sur 'Terminer' pour enregistrer sans information supplémentaire.\n\n*Ou tapez une information.*"
        
        # Set conversation state for text input
        context.user_data['conversation_state'] = 'poop_info'
        
        if query:
            await query.edit_message_text(
                text=message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
        else:
            # Use utility function to update main message
            await ensure_main_message_exists(update, context, data, group)
            await update_main_message(context, message, InlineKeyboardMarkup(keyboard))
            # Store the message ID for future text inputs
            if context.user_data.get('main_message_id') and context.user_data.get('chat_id'):
                set_group_message_info(data, group, user_id, context.user_data['main_message_id'], context.user_data['chat_id'])
                await save_data(data, context)
        return ASK_POOP_INFO
    except Exception as e:
        error_msg = f"❌ Erreur: {str(e)}"
        if query:
            await query.edit_message_text(
                error_msg,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("❌ Annuler", callback_data="cancel")
                ]])
            )
        else:
            # Use utility function to update main message
            await ensure_main_message_exists(update, context, data, group)
            await update_main_message(context, error_msg, InlineKeyboardMarkup([[
                InlineKeyboardButton("❌ Annuler", callback_data="cancel")
            ]]))
            # Store the message ID for future text inputs
            if context.user_data.get('main_message_id') and context.user_data.get('chat_id'):
                set_group_message_info(data, group, user_id, context.user_data['main_message_id'], context.user_data['chat_id'])
                await save_data(data, context)
        return ConversationHandler.END

async def handle_poop_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle additional info selection and save the poop entry"""
    # Check if this is a callback query or text message
    if hasattr(update, 'callback_query') and update.callback_query:
        query = update.callback_query
        await query.answer()
        # Extract info from callback data
        info = query.data.replace("poop_info_", "")
        if info == "none":
            info = None
    else:
        # This is a text message - delete it immediately
        query = None
        info = update.message.text.strip()
        # Delete user message for clean chat
        await delete_user_message(context, update.effective_chat.id, update.message.message_id)
    
    try:
        timestamp = context.user_data.get('poop_time')
        
        if not timestamp:
            error_msg = "❌ Erreur: temps non trouvé. Veuillez recommencer."
            if query:
                await query.edit_message_text(
                    error_msg,
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("❌ Annuler", callback_data="cancel")
                    ]])
                )
            else:
                # Use utility function to update main message
                data = load_data()
                user_id = update.effective_user.id
                group = find_group_for_user(data, user_id)
                await ensure_main_message_exists(update, context, data, group)
                await update_main_message(context, error_msg, InlineKeyboardMarkup([[
                    InlineKeyboardButton("❌ Annuler", callback_data="cancel")
                ]]))
            return ConversationHandler.END
        
        # Save the poop entry
        data = load_data()
        user_id = update.effective_user.id
        group = find_group_for_user(data, user_id)
        
        if "poop" not in data[group]:
            data[group]["poop"] = []
        
        data[group]["poop"].append({
            "time": timestamp,
            "info": info
        })
        
        await save_data(data, context)
        
        # Show success message and return to main
        from handlers.queries import get_main_message_content
        message_text, keyboard = get_main_message_content(data, group)
        
        success_text = f"✅ **Caca enregistré à {timestamp.split(' ')[1]} !**"
        if info:
            success_text += f"\nInfo: {info}"
        success_text += f"\n\n{message_text}"
        
        if query:
            await query.edit_message_text(
                text=success_text,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
        else:
            # Use utility function to update main message
            await ensure_main_message_exists(update, context, data, group)
            await update_main_message(context, success_text, keyboard)
            # Store the message ID for future text inputs
            if context.user_data.get('main_message_id') and context.user_data.get('chat_id'):
                set_group_message_info(data, group, user_id, context.user_data['main_message_id'], context.user_data['chat_id'])
                await save_data(data, context)
        
        # Clear conversation state when complete
        context.user_data.pop('conversation_state', None)
        return ConversationHandler.END
        
    except Exception as e:
        error_msg = f"❌ Erreur: {str(e)}"
        if query:
            await query.edit_message_text(
                error_msg,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("❌ Annuler", callback_data="cancel")
                ]])
            )
        else:
            # Use utility function to update main message
            data = load_data()
            user_id = update.effective_user.id
            group = find_group_for_user(data, user_id)
            await ensure_main_message_exists(update, context, data, group)
            await update_main_message(context, error_msg, InlineKeyboardMarkup([[
                InlineKeyboardButton("❌ Annuler", callback_data="cancel")
            ]]))
            # Store the message ID for future text inputs
            if context.user_data.get('main_message_id') and context.user_data.get('chat_id'):
                set_group_message_info(data, group, user_id, context.user_data['main_message_id'], context.user_data['chat_id'])
                await save_data(data, context)
        return ConversationHandler.END

async def cancel_poop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel the add poop flow and return to main"""
    query = update.callback_query
    await query.answer()
    
    data = load_data()
    user_id = update.effective_user.id
    group = find_group_for_user(data, user_id)
    
    # Clear conversation state
    context.user_data.pop('conversation_state', None)
    
    from handlers.queries import get_main_message_content
    message_text, keyboard = get_main_message_content(data, group)
    
    await query.edit_message_text(
        text=message_text,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    
    return ConversationHandler.END