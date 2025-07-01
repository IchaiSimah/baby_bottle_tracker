from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from utils import load_data, find_group_for_user, load_user_data, update_all_group_messages
from database import remove_last_entry_from_group, get_language
from translations import t

async def delete_bottle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show confirmation dialog for deleting the last bottle"""
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
        if not group_id or group_id not in data:
            error_msg = t("error_create_group", language)
            if hasattr(update, 'message') and update.message:
                await update.message.reply_text(error_msg)
            elif hasattr(update, 'callback_query') and update.callback_query:
                await update.callback_query.edit_message_text(error_msg)
            return False
    
    # Get the group ID from the loaded data
    group_id = list(data.keys())[0]
    group_data = data[group_id]
    
    if not group_data["entries"]:
        await query.edit_message_text(
            t("delete_no_bottles", language),
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(t("btn_home", language), callback_data="refresh")]])
        )
        return False
    last_entry = group_data["entries"][0]
    
    # Show confirmation dialog
    message = t("delete_confirmation", language, last_entry['time'].strftime('%d-%m-%Y'), last_entry['time'].strftime('%H:%M'), last_entry['amount'])
    
    keyboard = [
        [
            InlineKeyboardButton(t("btn_yes_delete", language), callback_data="confirm_delete"),
            InlineKeyboardButton(t("btn_no_cancel", language), callback_data="cancel_delete")
        ],
        [InlineKeyboardButton(t("btn_home", language), callback_data="refresh")]
    ]
    
    await query.edit_message_text(
        text=message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    
    return True

async def confirm_delete_bottle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Actually delete the last bottle after confirmation"""
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
        if not group_id or not data[group_id]["entries"]:
            await query.edit_message_text(
                t("delete_no_bottles", language),
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(t("btn_home", language), callback_data="refresh")]])
            )
            return False
        group_data = data[group_id]
    else:
        # Get the group ID from the loaded data
        group_id = list(data.keys())[0]
        group_data = data[group_id]
    
    if not group_data["entries"]:
        await query.edit_message_text(
            t("delete_no_bottles", language),
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(t("btn_home", language), callback_data="refresh")]])
        )
        return False
    
    removed_entry = group_data["entries"][0]
    remove_last_entry_from_group(int(group_id))
    

    
    # Reload data to get updated information
    data = load_user_data(user_id)
    if not data:
        data = load_data()
    
    # Generate updated main message content
    user_id = update.effective_user.id
    from handlers.queries import get_main_message_content
    message_text, keyboard = get_main_message_content(data, group_id, language)
    
    # Update all group messages with the new content
    user_id = update.effective_user.id
    print(f"user_id: {user_id}")
        # Update all group messages with the new content
    await update_all_group_messages(context, int(group_id), message_text, keyboard, user_id)
       
    # Show confirmation
    await query.edit_message_text(
        t("delete_success", language, removed_entry['amount'], removed_entry['time'].strftime('%H:%M')),
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(t("btn_home", language), callback_data="refresh")]])
    )
    
    return True

async def cancel_delete_bottle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel the deletion and return to main"""
    query = update.callback_query
    await query.answer()
    
    # Clear conversation state when canceling
    context.user_data.pop('conversation_state', None)
    
    # Return to main message using optimized function
    from handlers.queries import get_main_message_content_for_user
    
    user_id = update.effective_user.id
    language = get_language(user_id)
    message_text, keyboard = get_main_message_content_for_user(user_id, language)
    
    await query.edit_message_text(
        text=message_text,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )    
    return True
