from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from utils import load_data, save_data, find_group_for_user, create_personal_group, delete_user_message, update_main_message
from database import get_language
from database import update_group, create_group, update_group_name,  get_user_group_id
import re
from translations import t

async def show_groups_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show groups management menu"""
    query = update.callback_query
    await query.answer()
    
    data = load_data()
    user_id = update.effective_user.id
    language = get_language(user_id)
    group_id = find_group_for_user(data, user_id)
    
    # Only create personal group if user has no group
    if not group_id:
        group_id = create_personal_group(data, user_id)
    
    if not group_id or group_id not in data:
        error_msg = t("error_find_group", language)
        await query.edit_message_text(error_msg, parse_mode="Markdown")
        return
    
    # Get current group info
    group_info = data[group_id]
    group_name = group_info.get('name', str(group_id))
    group_id_str = str(group_id)
    member_count = len(group_info.get("users", []))
    
    message = t("groups_title", language)
    message += t("groups_current", language, group_name, group_id_str, member_count)
    
    # Convert group_id to string for startswith check
    if group_id_str.startswith("group_"):
        message += t("groups_personal", language)
    else:
        message += t("groups_shared", language)
    
    # Create keyboard
    keyboard = [
        [InlineKeyboardButton(t("btn_rename_group", language), callback_data="group_rename")],
        [InlineKeyboardButton(t("btn_join_group", language), callback_data="group_join")],
        [InlineKeyboardButton(t("btn_create_group", language), callback_data="group_create")],
    ]
    
    if not group_id_str.startswith("group_"):
        keyboard.append([InlineKeyboardButton(t("btn_leave_group", language), callback_data="group_leave")])
    
    keyboard.append([
        InlineKeyboardButton(t("btn_home", language), callback_data="refresh"),
        InlineKeyboardButton(t("btn_cancel", language), callback_data="cancel")
    ])
    
    await query.edit_message_text(
        text=message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="MarkdownV2"
    )

async def handle_group_actions(update: Update, context: ContextTypes.DEFAULT_TYPE, action: str = None):
    """Handle group management actions"""
    query = update.callback_query
    await query.answer()
    
    if not action:
        action = query.data.replace("group_", "")
    
    data = load_data()
    
    user_id = update.effective_user.id
    group_id = find_group_for_user(data, user_id)
    
    # Only create personal group if user has no group
    if not group_id:
        group_id = create_personal_group(data, user_id)
    
    if not group_id or group_id not in data:
        error_msg = t("error_find_group", get_language(user_id))
        await query.edit_message_text(error_msg)
        return
    
    if action == "rename":
        await show_rename_group(update, context, group_id)
    elif action == "join":
        await show_join_group(update, context)
    elif action == "create":
        await show_create_group(update, context)
    elif action == "leave":
        await leave_group(update, context, group_id)
        return

    # Clear conversation state for other states
    if action not in ['join', 'create', 'rename']:
        context.user_data.pop('conversation_state', None)

    await save_data(data, context)

async def show_rename_group(update: Update, context: ContextTypes.DEFAULT_TYPE, current_group_id: str):
    """Show rename group interface"""
    query = update.callback_query
    language = get_language(update.effective_user.id)
    data = load_data()
    
    message = t("rename_group_title", language, data[current_group_id]['name'])
    
    # Set conversation state for text input
    context.user_data['conversation_state'] = 'group_rename'
    
    keyboard = [[InlineKeyboardButton(t("btn_home", language), callback_data="refresh")]]
    
    await query.edit_message_text(
        text=message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def show_join_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show join group interface"""
    query = update.callback_query
    language = get_language(update.effective_user.id)
    message = t("join_group_title", language)
    
    # Set conversation state for text input
    context.user_data['conversation_state'] = 'group_join'
    
    keyboard = [[InlineKeyboardButton(t("btn_home", language), callback_data="refresh")]]
    
    await query.edit_message_text(
        text=message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def show_create_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show create group interface"""
    query = update.callback_query
    language = get_language(update.effective_user.id)
    message = t("create_group_title", language)
    
    # Set conversation state for text input
    context.user_data['conversation_state'] = 'group_create'
    
    keyboard = [[InlineKeyboardButton(t("btn_home", language), callback_data="refresh")]]
    
    await query.edit_message_text(
        text=message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

def _clear_context_cache(context):
    """Clear cached data from context"""
    if hasattr(context, '_cached_data'):
        delattr(context, '_cached_data')

async def rename_group(update: Update, context: ContextTypes.DEFAULT_TYPE, current_group_id: str, new_name: str):
    """Rename the current group"""
    # Check if this is a callback query or text input
    if hasattr(update, 'callback_query') and update.callback_query:
        query = update.callback_query
        await query.answer()
    else:
        query = None
        # Delete user message for clean chat
        await delete_user_message(context, update.effective_chat.id, update.message.message_id)
    language = get_language(update.effective_user.id)
    # Validate new name
    if not is_valid_group_name(new_name):
        message = t("rename_group_error", language)
        
        # Create keyboard with retry and return options
        keyboard = [
            [InlineKeyboardButton(t("btn_home", language), callback_data="refresh")],
            [InlineKeyboardButton(t("btn_return_settings", language), callback_data="settings")]
        ]
        
        # Keep conversation state active for retry
        context.user_data['conversation_state'] = 'group_rename'
        
        if query:
            await query.edit_message_text(
                message,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            # For text input, update main message using utility function
            await update_main_message(context, message, InlineKeyboardMarkup(keyboard))
        return
    
    data = load_data()
    
    # Check if name already exists using loaded data instead of database call
    for group_id, group_info in data.items():
        if group_info['name'] == new_name:
            message = t("rename_group_exists", language, new_name)
            
            # Create keyboard with retry and return options
            keyboard = [
                [InlineKeyboardButton(t("btn_home", language), callback_data="refresh")],
                [InlineKeyboardButton(t("btn_return_settings", language), callback_data="settings")]
            ]
            
            # Keep conversation state active for retry
            context.user_data['conversation_state'] = 'group_rename'
            
            if query:
                await query.edit_message_text(
                    message,
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            else:
                # For text input, update main message using utility function
                await update_main_message(context, message, InlineKeyboardMarkup(keyboard))
            return
    
    # Rename the group in the database
    current_group_id_int = int(current_group_id)
    user_id = update.effective_user.id
    if update_group_name(current_group_id_int, new_name):
        # Clear conversation state after successful rename
        context.user_data.pop('conversation_state', None)
        # Return to main menu
        from handlers.queries import get_main_message_content
        data = load_data()
        group_id = find_group_for_user(data, user_id)
        message_text, main_keyboard = get_main_message_content(data, group_id)
        
        success_text = t("rename_group_success", language, new_name, message_text)
        
        if query:
            await query.edit_message_text(
                text=success_text,
                reply_markup=main_keyboard,
                parse_mode="Markdown"
            )
        else:
            # For text input, update main message using utility function
            await update_main_message(context, success_text, main_keyboard)

    else:
        # Error updating group name
        message = t("rename_group_error", language)
        
        # Create keyboard with retry and return options
        keyboard = [
            [InlineKeyboardButton(t("btn_home", language), callback_data="refresh")],
            [InlineKeyboardButton(t("btn_return_settings", language), callback_data="settings")]
        ]
        
        # Keep conversation state active for retry
        context.user_data['conversation_state'] = 'group_rename'
        
        if query:
            await query.edit_message_text(
                message,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            # For text input, update main message with error
            data = load_data()
            user_id = update.effective_user.id
            group_id = find_group_for_user(data, user_id)
            await update_main_message(context, message, InlineKeyboardMarkup(keyboard))

async def join_group(update: Update, context: ContextTypes.DEFAULT_TYPE, target_group_name: str):
    """Join an existing group"""
    # Check if this is a callback query or text input
    if hasattr(update, 'callback_query') and update.callback_query:
        query = update.callback_query
        await query.answer()
    else:
        query = None
        # Delete user message for clean chat
        await delete_user_message(context, update.effective_chat.id, update.message.message_id)
    
    data = load_data()
    
    user_id = update.effective_user.id
    current_group_id = find_group_for_user(data, user_id)
    
    # Find the target group by name
    target_group_id = None
    for group_id, group_info in data.items():
        if group_info.get('name') == target_group_name:
            target_group_id = group_id
            break
    language = get_language(user_id)
    # Check if group exists
    if target_group_id is None:
        message = t("join_group_not_found", language, target_group_name)
        
        # Create keyboard with retry and return options
        keyboard = [
            [InlineKeyboardButton(t("btn_home", language), callback_data="refresh")],
            [InlineKeyboardButton(t("btn_return_settings", language), callback_data="settings")]
        ]
        
        context.user_data['conversation_state'] = 'group_join'
        
        if query:
            await query.edit_message_text(
                message,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            # For text input, update main message with error
            group_id = find_group_for_user(data, user_id)            
            await update_main_message(context, message, InlineKeyboardMarkup(keyboard))
        return
    
    # Check if user is already in this group
    if current_group_id == target_group_id:
        message = t("join_group_already_member", language, target_group_name)
        
        # Create keyboard with return options
        keyboard = [
            [InlineKeyboardButton(t("btn_home", language), callback_data="refresh")],
            [InlineKeyboardButton(t("btn_return_settings", language), callback_data="settings")]
        ]
        
        # Clear conversation state for already in group
        context.user_data.pop('conversation_state', None)
        
        if query:
            await query.edit_message_text(
                message,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            # For text input, update main message with error
            group_id = find_group_for_user(data, user_id)
            await update_main_message(context, message, InlineKeyboardMarkup(keyboard))
        return
    
    # Remove user from current group

    if current_group_id:
        message = t("join_group_id_check", language, target_group_name)
        keyboard = [
            [InlineKeyboardButton(t("btn_home", language), callback_data="refresh")],
            [InlineKeyboardButton(t("btn_return_settings", language), callback_data="settings")]
        ]
        await update_main_message(context, message, InlineKeyboardMarkup(keyboard))
        context.user_data['conversation_state'] = 'id_check_group_join'
        context.user_data['target_group_id'] = target_group_id
        return
    
async def id_check_group_join(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    await delete_user_message(context, update.effective_chat.id, update.message.message_id)
    data = load_data()
    user_id = update.effective_user.id
    language = get_language(user_id)
    target_group_id = context.user_data['target_group_id']
    current_group_id = find_group_for_user(data, user_id)
    if text != str(target_group_id):
        message = t("join_group_id_incorrect", language)
        keyboard = [
            [InlineKeyboardButton(t("btn_home", language), callback_data="refresh")],
            [InlineKeyboardButton(t("btn_return_settings", language), callback_data="settings")]
        ]
        await update_main_message(context, message, InlineKeyboardMarkup(keyboard))
        return 
    else:
        group_users = data[current_group_id]["users"]
        # Convert all user IDs to integers for comparison
        int_users = []
        for user in group_users:
            try:
                int_users.append(int(user))
            except (ValueError, TypeError):
                continue
        
        if user_id in int_users:
            data[current_group_id]["users"].remove(str(user_id) if str(user_id) in group_users else user_id)
            # Convert group_id to int for database function
            update_group(int(current_group_id), data[current_group_id])
    
    # Add user to target group
    data[target_group_id]["users"].append(int(user_id))
    # Convert group_id to int for database function
    update_group(int(target_group_id), data[target_group_id])
    
    # Clear conversation state after successful join
    context.user_data.pop('conversation_state', None)
    # Return to main menu
    from handlers.queries import get_main_message_content
    group_id = find_group_for_user(data, user_id)
    message_text, main_keyboard = get_main_message_content(data, group_id)
    target_group_name = data[target_group_id]['name']
    # Add confirmation message to avoid "Message is not modified" error
    success_text = t("join_group_success", language, target_group_name, message_text)
    await update_main_message(context, success_text, main_keyboard)

async def create_new_group(update: Update, context: ContextTypes.DEFAULT_TYPE, new_name: str):
    """Create a new group"""
    # Check if this is a callback query or text input
    if hasattr(update, 'callback_query') and update.callback_query:
        query = update.callback_query
        await query.answer()
    else:
        query = None
        # Delete user message for clean chat
        await delete_user_message(context, update.effective_chat.id, update.message.message_id)
    language = get_language(update.effective_user.id)
    # Validate new name
    if not is_valid_group_name(new_name):
        message = t("create_group_invalid_name", language)
        
        # Create keyboard with retry and return options
        keyboard = [
            [InlineKeyboardButton(t("btn_home", language), callback_data="refresh")],
            [InlineKeyboardButton(t("btn_return_settings", language), callback_data="settings")]
        ]
        
        # Keep conversation state active for retry
        context.user_data['conversation_state'] = 'group_create'
        
        if query:
            await query.edit_message_text(
                message,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            # For text input, update main message with error
            data = load_data()
            user_id = update.effective_user.id
            group_id = find_group_for_user(data, user_id)
            await update_main_message(context, message, InlineKeyboardMarkup(keyboard))
        return
    
    data = load_data()
    
    user_id = update.effective_user.id
    current_group_id = find_group_for_user(data, user_id)
    
    # Check if name already exists using loaded data instead of database call
    for group_id, group_info in data.items():
        if group_info['name'] == new_name:
            message = t("create_group_exists", language, new_name)
            
            # Create keyboard with retry and return options
            keyboard = [
                [InlineKeyboardButton(t("btn_home", language), callback_data="refresh")],
                [InlineKeyboardButton(t("btn_return_settings", language), callback_data="settings")]
            ]
            
            # Keep conversation state active for retry
            context.user_data['conversation_state'] = 'group_create'
            
            if query:
                await query.edit_message_text(
                    message,
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            else:
                # For text input, update main message with error
                group_id = find_group_for_user(data, user_id)
                await update_main_message(context, message, InlineKeyboardMarkup(keyboard))
            return
    
    # Remove user from current group
    if current_group_id and current_group_id in data:
        group_users = data[current_group_id].get("users", [])
        # Convert all user IDs to integers for comparison
        int_users = []
        for user in group_users:
            try:
                int_users.append(int(user))
            except (ValueError, TypeError):
                continue
        
        if user_id in int_users:
            data[current_group_id]["users"].remove(str(user_id) if str(user_id) in group_users else user_id)
            # Update the current group in database
            update_group(int(current_group_id), data[current_group_id])
    
    # Create new group
    create_group(new_name, user_id)
    # Clear conversation state after successful creation
    context.user_data.pop('conversation_state', None)
    # Return to main menu
    from handlers.queries import get_main_message_content
    data = load_data()
    group_id = find_group_for_user(data, user_id)
    message_text, main_keyboard = get_main_message_content(data, group_id)
    
    # Add confirmation message to avoid "Message is not modified" error
    success_text = t("create_group_success", language, new_name, message_text)
    
    if query:
        await query.edit_message_text(
            text=success_text,
            reply_markup=main_keyboard,
            parse_mode="Markdown"
        )
    else:
        # For text input, update main message using utility function
        await update_main_message(context, success_text, main_keyboard)

async def leave_group(update: Update, context: ContextTypes.DEFAULT_TYPE, current_group_id: str):
    """Leave current group and return to personal group"""
    # Check if this is a callback query or text input
    if hasattr(update, 'callback_query') and update.callback_query:
        query = update.callback_query
        await query.answer()
    else:
        query = None
    
    data = load_data()
    
    user_id = update.effective_user.id
    
    # Remove user from current group
    if current_group_id:
        group_users = data[current_group_id]["users"]
        # Convert all user IDs to integers for comparison
        int_users = []
        for user in group_users:
            try:
                int_users.append(int(user))
            except (ValueError, TypeError):
                continue
        
        if user_id in int_users:
            data[current_group_id]["users"].remove(str(user_id) if str(user_id) in group_users else user_id)
            # Convert group_id to int for database function
            update_group(int(current_group_id), data[current_group_id])
    
    # Create or use personal group (highly optimized)
    personal_group_name = f"group_{user_id}"
    personal_group_id = None
    
    # Check if personal group already exists in current data
    for group_id, group_info in data.items():
        if group_info.get('name') == personal_group_name:
            personal_group_id = group_id
            # Ensure user is in the group
            if user_id not in group_info.get('users', []):
                group_info['users'].append(user_id)
                update_group(int(group_id), group_info)
            break
    
    # If personal group doesn't exist, create it directly in database
    if personal_group_id is None:
        create_group(personal_group_name, user_id)
        # Get the created group ID efficiently
        personal_group_id = get_user_group_id(user_id)
    
    # Clear conversation state after leaving group
    context.user_data.pop('conversation_state', None)
    
    # Return to main menu
    from handlers.queries import get_main_message_content
    group_id = find_group_for_user(data, user_id)
    message_text, main_keyboard = get_main_message_content(data, group_id)
    language = get_language(user_id)
    # Add confirmation message to avoid "Message is not modified" error
    success_text = t("leave_group_success", language, message_text)
    
    if query:
        await query.edit_message_text(
            text=success_text,
            reply_markup=main_keyboard,
            parse_mode="Markdown"
        )
    else:
        # For text input, update main message using utility function
        await update_main_message(context, success_text, main_keyboard)

def is_valid_group_name(name: str) -> bool:
    """Validate group name format"""
    if len(name) < 3 or len(name) > 20:
        return False
    
    # Allow letters, numbers, spaces, and hyphens
    pattern = r'^[a-zA-Z0-9\s\-]+$'
    return bool(re.match(pattern, name)) 