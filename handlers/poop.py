from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from zoneinfo import ZoneInfo
from utils import load_data, save_data, find_group_for_user, create_personal_group, is_valid_time, normalize_time, delete_user_message, update_main_message, set_group_message_info, load_user_data,  update_all_group_messages
from database import add_poop_to_group, get_language
from translations import t

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
    
    user_id = update.effective_user.id
    language = get_language(user_id)
    
    # Use optimized data loading
    data = load_user_data(user_id)
    if not data:
        # Fallback to old method if needed
        data = load_data()
        group_id = find_group_for_user(data, user_id)
        if not group_id:
            group_id = create_personal_group(data, user_id)
            await save_data(data, context)
            data = load_user_data(user_id)
    
    if not data:
        error_msg = t("error_create_group", language)
        await query.edit_message_text(error_msg)
        return
    
    # Get the group ID from the loaded data
    group_id = list(data.keys())[0]
    group_data = data[group_id]
    
    td = group_data.get("time_difference", 0)
    if td is None:
        td = 0
    time_difference = timedelta(hours=td)
    
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
        InlineKeyboardButton(t("btn_now", language), callback_data="poop_time_now"),
        InlineKeyboardButton(t("btn_cancel", language), callback_data="cancel")
    ])
    
    message = t("add_poop_time_question", language)
    
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
    if hasattr(update, 'callback_query') and update.callback_query:
        query = update.callback_query
        await query.answer()
        if not time_str:
            time_str = query.data.replace("poop_time_", "")
    else:
        query = None
        if not time_str:
            time_str = update.message.text.strip()
        await delete_user_message(context, update.effective_chat.id, update.message.message_id)
    
    user_id = update.effective_user.id
    language = get_language(user_id)
    
    # Use optimized data loading
    data = load_user_data(user_id)
    if not data:
        # Fallback to old method if needed
        data = load_data()
        group_id = find_group_for_user(data, user_id)
        if not group_id or group_id not in data:
            error_msg = t("error_create_group", language)
            if hasattr(update, 'message') and update.message:
                await update.message.reply_text(error_msg)
            elif hasattr(update, 'callback_query') and update.callback_query:
                await update.callback_query.edit_message_text(error_msg)
            return
    
    # Get the group ID from the loaded data
    group_id = list(data.keys())[0]
    group_data = data[group_id]
    
    td = group_data.get("time_difference", 0)
    if td is None:
        td = 0
    time_difference = timedelta(hours=td)
    
    try:
        if time_str.lower() == "now":
            dt = datetime.now(ZoneInfo("UTC")) + time_difference
        else:
            normalized_time = normalize_time(time_str)
            if not is_valid_time(normalized_time):
                error_msg = t("error_invalid_time", language)
                if query:
                    await query.edit_message_text(
                        error_msg,
                        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(t("btn_cancel", language), callback_data="cancel")]])
                    )
                else:
                    await update_main_message(context, error_msg, InlineKeyboardMarkup([[InlineKeyboardButton(t("btn_cancel", language), callback_data="cancel")]]))
                return ASK_POOP_TIME
            today = (datetime.now(ZoneInfo("UTC")) + time_difference).date()
            hour, minute = map(int, normalized_time.split(":"))
            dt = datetime.combine(today, datetime.min.time(), tzinfo=ZoneInfo("UTC"))
            dt = dt.replace(hour=hour, minute=minute)
            now_utc = (datetime.now(ZoneInfo("UTC")) + time_difference)
            if now_utc < dt:
                dt = dt - timedelta(days=1)
        context.user_data['poop_time'] = dt
        keyboard = [
            [InlineKeyboardButton(t("btn_finish", language), callback_data="poop_info_none")],
            [InlineKeyboardButton(t("btn_cancel", language), callback_data="cancel")]
        ]
        message = t("poop_recorded", language, dt.strftime('%H:%M'))
        context.user_data['conversation_state'] = 'poop_info'
        if query:
            await query.edit_message_text(
                text=message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
        else:
            await update_main_message(context, message, InlineKeyboardMarkup(keyboard))
            if context.user_data.get('main_message_id') and context.user_data.get('chat_id'):
                set_group_message_info(data, group_id, user_id, context.user_data['main_message_id'], context.user_data['chat_id'])
        return ASK_POOP_INFO
    except Exception as e:
        error_msg = t("error_general", language)
        if query:
            await query.edit_message_text(
                error_msg,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(t("btn_cancel", language), callback_data="cancel")]])
            )
        else:
            await update_main_message(context, error_msg, InlineKeyboardMarkup([[InlineKeyboardButton(t("btn_cancel", language), callback_data="cancel")]]))
        return ConversationHandler.END

async def handle_poop_info(update: Update, context: ContextTypes.DEFAULT_TYPE, info: str = None):
    """Handle additional info selection and save the poop entry"""
    if hasattr(update, 'callback_query') and update.callback_query:
        query = update.callback_query
        await query.answer()
        if not info:
            info = query.data.replace("poop_info_", "")
        if info == "none":
            info = None
    else:
        query = None
        if not info:
            info = update.message.text.strip()
        await delete_user_message(context, update.effective_chat.id, update.message.message_id)
    
    user_id = update.effective_user.id
    language = get_language(user_id)
    
    try:
        dt = context.user_data.get('poop_time')
        if not dt:
            error_msg = t("error_not_found_time", language)
            if query:
                await query.edit_message_text(
                    error_msg,
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(t("btn_cancel", language), callback_data="cancel")]])
                )
            else:
                data = load_user_data(user_id)
                if not data:
                    data = load_data()
                group_id = find_group_for_user(data, user_id)
                await update_main_message(context, error_msg, InlineKeyboardMarkup([[InlineKeyboardButton(t("btn_cancel", language), callback_data="cancel")]]))
            return ConversationHandler.END
        
        data = load_user_data(user_id)
        if not data:
            data = load_data()
        
        group_id = find_group_for_user(data, user_id)
        # Convert group_id to int for database function
        add_poop_to_group(int(group_id), dt, info)
        
        
        # Reload data to get the updated information including the new poop
        data = load_user_data(user_id)
        if not data:
            data = load_data()
        
        # Return to main message with updated data
        from handlers.queries import get_main_message_content
        message_text, keyboard = get_main_message_content(data, group_id, language)
        if info:
            success_text = t("poop_added_with_info", language, dt.strftime('%H:%M'), info)
        else:
            success_text = t("poop_added_success", language, dt.strftime('%H:%M'))
        success_text += f"\n\n{message_text}"
        
        if query:
            await query.edit_message_text(
                text=success_text,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
        else:
            await update_main_message(context, success_text, keyboard)
            # Store the message ID for future text inputs
            if context.user_data.get('main_message_id') and context.user_data.get('chat_id'):
                set_group_message_info(data, group_id, user_id, context.user_data['main_message_id'], context.user_data['chat_id'])
        
        # Update all group messages with the new content
        user_id = update.effective_user.id
        print(f"user_id: {user_id}")
        # Update all group messages with the new content
        await update_all_group_messages(context, int(group_id), message_text, keyboard, user_id)
        
        # Clear conversation state
        context.user_data.pop('conversation_state', None)
        context.user_data.pop('poop_time', None)
        
        return ConversationHandler.END
    except Exception as e:
        error_msg = t("error_general", language)
        if query:
            await query.edit_message_text(
                error_msg,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(t("btn_cancel", language), callback_data="cancel")]])
            )
        else:
            data = load_user_data(user_id)
            if not data:
                data = load_data()
            
            group_id = find_group_for_user(data, user_id)
            await update_main_message(context, error_msg, InlineKeyboardMarkup([[InlineKeyboardButton(t("btn_cancel", language), callback_data="cancel")]]))
        return ConversationHandler.END

