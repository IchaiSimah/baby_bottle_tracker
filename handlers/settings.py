from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from utils import load_data, save_data, find_group_for_user, create_personal_group, normalize_time, ensure_main_message_exists, update_main_message
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from config import TEST_MODE
from database import update_group, get_language, update_language
from translations import t

async def show_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show settings menu"""
    query = update.callback_query
    await query.answer()
    
    data = load_data()
    user_id = update.effective_user.id
    language = get_language(user_id)
    group_id = find_group_for_user(data, user_id)
    if not group_id:
        group_id = create_personal_group(data, user_id)
        await save_data(data, context)
        data = load_data()
    
    if not group_id or group_id not in data:
        error_msg = t("error_create_group", language)
        if hasattr(update, 'message') and update.message:
            await update.message.reply_text(error_msg)
        elif hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.edit_message_text(error_msg)
        return
    
    # Get current settings
    bottles_to_show = data[group_id].get("bottles_to_show", 5)
    poops_to_show = data[group_id].get("poops_to_show", 1)
    td = data[group_id].get("time_difference", 0)
    if td is None:
        td = 0
    last_bottle = data[group_id].get("last_bottle", 120)
    time_difference = td
    adjusted_time = datetime.now(ZoneInfo("UTC")) + timedelta(hours=time_difference)
    
    message = t("settings_title", language)
    message += t("settings_display", language, bottles_to_show, poops_to_show, last_bottle)
    message += t("settings_timezone", language, time_difference, adjusted_time.strftime('%H:%M'))
    message += t("settings_modify", language)
    
    # Create keyboard for settings
    keyboard = [
        [
            InlineKeyboardButton(t("btn_bottles_count", language, bottles_to_show), callback_data="setting_bottles"),
            InlineKeyboardButton(t("btn_poops_count", language, poops_to_show), callback_data="setting_poops")
        ],
        [
            InlineKeyboardButton(t("btn_bottle_size", language), callback_data="setting_last_bottle"),
            InlineKeyboardButton(t("btn_change_time", language), callback_data="setting_timezone")
        ],
        [
            InlineKeyboardButton(t("btn_groups", language), callback_data="groups"),
            InlineKeyboardButton(t("btn_language", language), callback_data="setting_language")
        ],
        [
            InlineKeyboardButton(t("btn_home", language), callback_data="refresh")
        ]
    ]
    
    await query.edit_message_text(
        text=message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def handle_settings(update: Update, context: ContextTypes.DEFAULT_TYPE, setting: str = None):
    """Handle settings changes"""
    query = update.callback_query
    await query.answer()
    
    if not setting:
        # Extract setting from callback data
        setting = query.data.replace("setting_", "")
    
    data = load_data()
    user_id = update.effective_user.id
    language = get_language(user_id)
    group_id = find_group_for_user(data, user_id)
    
    if not group_id or group_id not in data:
        error_msg = t("error_create_group", language)
        if hasattr(update, 'message') and update.message:
            await update.message.reply_text(error_msg)
        elif hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.edit_message_text(error_msg)
        return
    
    if setting == "bottles":
        # Show bottle count options
        current = data[group_id].get("bottles_to_show", 5)
        keyboard = []
        
        # Create rows of 3 buttons each
        options = [3, 4, 5, 6, 7, 8, 9, 10]
        for i in range(0, len(options), 3):
            row = []
            for j in range(3):
                if i + j < len(options):
                    option = options[i + j]
                    text = f"{option} {'✅' if option == current else ''}"
                    row.append(InlineKeyboardButton(text, callback_data=f"set_bottles_{option}"))
            keyboard.append(row)
        
        keyboard.append([InlineKeyboardButton(t("btn_cancel", language), callback_data="settings")])
        
        message = t("bottles_count_question", language)
        
        await query.edit_message_text(
            text=message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    
    elif setting == "poops":
        # Show poop count options
        current = data[group_id].get("poops_to_show", 1)
        keyboard = []
        
        # Create rows of 3 buttons each
        options = [1, 2, 3, 4, 5]
        for i in range(0, len(options), 3):
            row = []
            for j in range(3):
                if i + j < len(options):
                    option = options[i + j]
                    text = f"{option} {'✅' if option == current else ''}"
                    row.append(InlineKeyboardButton(text, callback_data=f"set_poops_{option}"))
            keyboard.append(row)
        
        keyboard.append([InlineKeyboardButton(t("btn_cancel", language), callback_data="settings")])
        
        message = t("poops_count_question", language)
        
        await query.edit_message_text(
            text=message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    
    elif setting.startswith("set_bottles_"):
        count = int(setting.replace("set_bottles_", ""))
        data[group_id]["bottles_to_show"] = count
        # Convert group_id to int for database function
        update_group(int(group_id), data[group_id])

        # Recharge les données du groupe après la modification
        data = load_data()
        await show_settings(update, context)
    
    elif setting.startswith("set_poops_"):
        count = int(setting.replace("set_poops_", ""))
        data[group_id]["poops_to_show"] = count
        # Convert group_id to int for database function
        update_group(int(group_id), data[group_id])
        # Recharge les données du groupe après la modification
        data = load_data()
        await show_settings(update, context)
    
    elif setting == "timezone":
        td = data[group_id].get("time_difference", 0)
        if td is None:
            td = 0
        current_diff = td
        current_time = datetime.now(ZoneInfo("UTC")) + timedelta(hours=current_diff)
        utc_time = datetime.now(ZoneInfo("UTC"))
        
        message = t("timezone_title", language, current_time.strftime('%H:%M'), utc_time.strftime('%H:%M'))
        
        # Create keyboard with time suggestions (current time ± 2 hours)
        keyboard = []
        current_hour = current_time.hour
        
        # Create time suggestions
        suggestions = []
        for i in range(-2, 3):  # -2h to +2h from current time
            suggested_hour = (current_hour + i) % 24
            suggested_time = f"{suggested_hour:02d}:{current_time.minute:02d}"
            suggestions.append(suggested_time)
        
        # Create rows of 3 buttons each
        for i in range(0, len(suggestions), 3):
            row = []
            for j in range(3):
                if i + j < len(suggestions):
                    time_str = suggestions[i + j]
                    row.append(InlineKeyboardButton(time_str, callback_data=f"set_time_{time_str}"))
            keyboard.append(row)
        
        keyboard.append([InlineKeyboardButton(t("btn_cancel", language), callback_data="settings")])
        
        # Add manual input option
        keyboard.append([InlineKeyboardButton(t("btn_manual_input", language), callback_data="manual_time_input")])
        
        await query.edit_message_text(
            text=message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    
    elif setting.startswith("set_time_"):
        time_str = setting.replace("set_time_", "")
        try:
            selected_time = datetime.strptime(time_str, "%H:%M").time()
            now = datetime.now(ZoneInfo("UTC"))
            target_hour = selected_time.hour
            current_hour = now.hour
            diff_hour = target_hour - current_hour
            if diff_hour > 12:
                diff_hour -= 24
            elif diff_hour < -12:
                diff_hour += 24
            data[group_id]["time_difference"] = diff_hour
            # Convert group_id to int for database function
            update_group(int(group_id), data[group_id])
            # Recharge les données du groupe après la modification
            data = load_data()
            adjusted_time = datetime.now(ZoneInfo("UTC")) + timedelta(hours=diff_hour)
            message = t("timezone_success", language, time_str, now.strftime('%H:%M'), diff_hour)
            keyboard = [[InlineKeyboardButton(t("btn_return_settings", language), callback_data="settings")]]
            await query.edit_message_text(
                text=message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
        except ValueError:
            message = t("timezone_error", language)
            keyboard = [[InlineKeyboardButton(t("btn_cancel", language), callback_data="settings")]]
            await query.edit_message_text(
                text=message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
    
    elif setting == "groups":
        # Show groups
        groups = list(data.keys())
        keyboard = []
        
        for group in groups:
            keyboard.append([InlineKeyboardButton(group, callback_data=f"group_{group}")])
        
        keyboard.append([InlineKeyboardButton(t("btn_cancel", language), callback_data="cancel")])
        
        message = t("groups_title", language)
        
        await query.edit_message_text(
            text=message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    
    elif setting.startswith("group_"):
        # Set group
        group = setting.replace("group_", "")
        data[group] = {}
        # No save_data here; persistence is handled elsewhere
        # Show confirmation and return to settings
        await show_settings(update, context)
    
    elif setting == "refresh":
        # Refresh settings
        await show_settings(update, context)
    
    elif setting == "cancel":
        # Cancel operation
        # Clear conversation state when canceling
        context.user_data.pop('conversation_state', None)
        await query.edit_message_text(
            t("operation_cancelled", language),
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton(t("btn_home", language), callback_data="refresh")
            ]])
        )
    
    elif setting == "settings":
        # Show settings menu
        await show_settings(update, context)
    
    elif setting == "manual_time_input":
        # Set the conversation state for manual timezone input
        context.user_data['conversation_state'] = 'timezone_input'
        message = t("timezone_manual_input", language)
        keyboard = [[InlineKeyboardButton(t("btn_cancel", language), callback_data="settings")]]
        await query.edit_message_text(
            text=message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    
    elif setting == "last_bottle":
        context.user_data['conversation_state'] = 'last_bottle'
        # Show quick choices for last bottle + manual input
        current = data[group_id].get("last_bottle", 120)
        quick_choices = [current -10, current, current + 10, current + 20, current + 30, current + 40]
        keyboard = []
        row = []
        for value in quick_choices:
            text = f"{value}ml {'✅' if value == current else ''}"
            row.append(InlineKeyboardButton(text, callback_data=f"set_last_bottle_{value}"))
            if len(row) == 2:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)
        keyboard.append([InlineKeyboardButton(t("btn_cancel", language), callback_data="settings")])
        message = t("bottle_size_question", language, current)
        await query.edit_message_text(
            text=message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    elif setting.startswith("set_last_bottle_"):
        value = int(setting.replace("set_last_bottle_", ""))
        data[group_id]["last_bottle"] = value
        update_group(int(group_id), data[group_id])
        data = load_data()
        message = t("bottle_size_success", language, value)
        keyboard = [[InlineKeyboardButton(t("btn_return_settings", language), callback_data="settings")]]
        await query.edit_message_text(
            text=message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    elif setting == "language":
            # Show poop count options
        current = get_language(user_id)
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
        keyboard.append([InlineKeyboardButton(t("btn_cancel", language), callback_data="settings")])

        message = t("language_question", language)

        await query.edit_message_text(
            text=message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    
    elif setting.startswith("set_language_"):
        language = setting.replace("set_language_", "")
        update_language(user_id, language)
        context.user_data.pop('conversation_state', None)
        # Recharge les données du groupe après la modification
        data = load_data()
        await show_settings(update, context)
    


async def handle_timezone_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE, time_str: str):
    """Handle manual timezone text input"""
    user_id = update.effective_user.id
    language = get_language(user_id)
    data = load_data()
    group_id = find_group_for_user(data, user_id)
    try:
        # Normalize the time input
        normalized_time = normalize_time(time_str)
        # Parse the input time
        selected_time = datetime.strptime(normalized_time, "%H:%M").time()
        now = datetime.now(ZoneInfo("UTC"))
        # Calculate time difference
        target_hour = selected_time.hour
        current_hour = now.hour
        diff_hour = target_hour - current_hour
        # Handle day boundary cases
        if diff_hour > 12:
            diff_hour -= 24
        elif diff_hour < -12:
            diff_hour += 24
        # Update the time difference and persist to Supabase
        data[group_id]["time_difference"] = diff_hour
        # Convert group_id to int for database function
        update_group(int(group_id), data[group_id])
        # Recharge les données du groupe après la modification
        data = load_data()
        # Clear conversation state
        context.user_data.pop('conversation_state', None)
        # Show confirmation
        adjusted_time = datetime.now(ZoneInfo("UTC")) + timedelta(hours=diff_hour)
        message = t("timezone_success", language, normalized_time, now.strftime('%H:%M'), diff_hour)
        keyboard = [[InlineKeyboardButton(t("btn_return_settings", language), callback_data="settings")]]
        # Use utility function to update main message
        await ensure_main_message_exists(update, context, data, group_id)
        await update_main_message(context, message, InlineKeyboardMarkup(keyboard))
    except Exception as e:

        message = t("timezone_manual_error", language)
        keyboard = [[InlineKeyboardButton(t("btn_cancel", language), callback_data="settings")]]
        await ensure_main_message_exists(update, context, data, group_id)
        await update_main_message(context, message, InlineKeyboardMarkup(keyboard))

async def handle_last_bottle_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE, value_str: str):
    user_id = update.effective_user.id
    language = get_language(user_id)
    data = load_data()
    group_id = find_group_for_user(data, user_id)
    try:
        value = int(value_str.strip())
        if value <= 0:
            raise ValueError
        data[group_id]["last_bottle"] = value
        update_group(int(group_id), data[group_id])
        data = load_data()
        context.user_data.pop('conversation_state', None)
        message = t("bottle_size_success", language, value)
        keyboard = [[InlineKeyboardButton(t("btn_return_settings", language), callback_data="settings")]]
        await ensure_main_message_exists(update, context, data, group_id)
        await update_main_message(context, message, InlineKeyboardMarkup(keyboard))
    except Exception:
        message = t("bottle_size_error", language)
        keyboard = [[InlineKeyboardButton(t("btn_cancel", language), callback_data="settings")]]
        await ensure_main_message_exists(update, context, data, group_id)
        await update_main_message(context, message, InlineKeyboardMarkup(keyboard)) 

