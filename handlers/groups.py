from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from utils import load_data, save_data, find_group_for_user, create_personal_group, delete_user_message, update_main_message, ensure_main_message_exists, invalidate_user_cache, invalidate_cache
from database import update_group, create_group, update_group_name, get_all_groups, get_user_group_id
import re

async def show_groups_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show groups management menu"""
    query = update.callback_query
    await query.answer()
    
    # Use cached data if available, otherwise load once
    data = getattr(context, '_cached_data', None)
    if data is None:
        data = load_data()
        context._cached_data = data
    
    user_id = update.effective_user.id
    group_id = find_group_for_user(data, user_id)
    
    # Only create personal group if user has no group
    if not group_id:
        group_id = create_personal_group(data, user_id)
        # Invalidate cache and reload data only if group was created
        if group_id:
            invalidate_cache()
            data = load_data()
            context._cached_data = data
    
    if not group_id or group_id not in data:
        error_msg = "❌ Erreur : impossible de trouver ou créer votre groupe personnel. Merci de réessayer plus tard."
        await query.edit_message_text(error_msg)
        return
    
    # Get current group info
    group_info = data[group_id]
    group_name = group_info.get('name', str(group_id))
    member_count = len(group_info.get("users", []))
    
    message = f"👥 **Gestion des Groupes**\n\n"
    message += f"**Groupe actuel :** `{group_name}`\n"
    message += f"**Membres :** {member_count}\n"
    
    # Convert group_id to string for startswith check
    group_id_str = str(group_id)
    if group_id_str.startswith("group_"):
        message += "\n*Vous êtes dans un groupe personnel*\n"
    else:
        message += "\n*Vous êtes dans un groupe partagé*\n"
    
    # Create keyboard
    keyboard = [
        [InlineKeyboardButton("✏️ Renommer le groupe", callback_data="group_rename")],
        [InlineKeyboardButton("🔗 Rejoindre un groupe", callback_data="group_join")],
        [InlineKeyboardButton("➕ Créer un groupe", callback_data="group_create")],
    ]
    
    if not group_id_str.startswith("group_"):
        keyboard.append([InlineKeyboardButton("🚪 Quitter le groupe", callback_data="group_leave")])
    
    keyboard.append([
        InlineKeyboardButton("🏠 Accueil", callback_data="refresh"),
        InlineKeyboardButton("❌ Annuler", callback_data="cancel")
    ])
    
    await query.edit_message_text(
        text=message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def handle_group_actions(update: Update, context: ContextTypes.DEFAULT_TYPE, action: str = None):
    """Handle group management actions"""
    query = update.callback_query
    await query.answer()
    
    if not action:
        action = query.data.replace("group_", "")
    
    # Use cached data if available, otherwise load once
    data = getattr(context, '_cached_data', None)
    if data is None:
        data = load_data()
        context._cached_data = data
    
    user_id = update.effective_user.id
    group_id = find_group_for_user(data, user_id)
    
    # Only create personal group if user has no group
    if not group_id:
        group_id = create_personal_group(data, user_id)
        # Invalidate cache and reload data only if group was created
        if group_id:
            invalidate_cache()
            data = load_data()
            context._cached_data = data
    
    if not group_id or group_id not in data:
        error_msg = "❌ Erreur : impossible de trouver ou créer votre groupe personnel. Merci de réessayer plus tard."
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
    # Use data from context if available, otherwise load once
    data = getattr(context, '_cached_data', None)
    if data is None:
        data = load_data()
        context._cached_data = data
    
    message = f"✏️ **Renommer le groupe**\n\n"
    message += f"Groupe actuel : `{data[current_group_id]['name']}`\n\n"
    message += "*Tapez le nouveau nom du groupe :*\n"
    message += "• 3-20 caractères\n"
    message += "• Lettres, chiffres, espaces, tirets\n"
    message += "• Pas de caractères spéciaux"
    
    # Set conversation state for text input
    context.user_data['conversation_state'] = 'group_rename'
    
    keyboard = [[InlineKeyboardButton("🏠 Accueil", callback_data="refresh")]]
    
    await query.edit_message_text(
        text=message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def show_join_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show join group interface"""
    query = update.callback_query
    
    message = "🔗 **Rejoindre un groupe**\n\n"
    message += "*Tapez le nom exact du groupe à rejoindre :*\n"
    message += "• Le nom doit correspondre exactement\n"
    message += "• Respectez les majuscules/minuscules\n"
    message += "• Le groupe doit exister"
    
    # Set conversation state for text input
    context.user_data['conversation_state'] = 'group_join'
    
    keyboard = [[InlineKeyboardButton("🏠 Accueil", callback_data="refresh")]]
    
    await query.edit_message_text(
        text=message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def show_create_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show create group interface"""
    query = update.callback_query
    
    message = "➕ **Créer un nouveau groupe**\n\n"
    message += "*Tapez le nom du nouveau groupe :*\n"
    message += "• 3-20 caractères\n"
    message += "• Lettres, chiffres, espaces, tirets\n"
    message += "• Pas de caractères spéciaux\n"
    message += "• Nom unique requis"
    
    # Set conversation state for text input
    context.user_data['conversation_state'] = 'group_create'
    
    keyboard = [[InlineKeyboardButton("🏠 Accueil", callback_data="refresh")]]
    
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
    
    # Validate new name
    if not is_valid_group_name(new_name):
        message = "❌ **Nom invalide**\n\nLe nom doit contenir 3-20 caractères et ne peut contenir que des lettres, chiffres, espaces et tirets."
        keyboard = [[InlineKeyboardButton("🏠 Accueil", callback_data="refresh")]]
        
        # Clear conversation state for invalid name
        context.user_data.pop('conversation_state', None)
        
        if query:
            await query.edit_message_text(
                message,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            # For text input, update main message using utility function
            await update_main_message(context, message, InlineKeyboardMarkup(keyboard))
        return
    
    # Use cached data if available, otherwise load once
    data = getattr(context, '_cached_data', None)
    if data is None:
        data = load_data()
        context._cached_data = data
    
    # Check if name already exists using loaded data instead of database call
    for group_id, group_info in data.items():
        if group_info['name'] == new_name:
            message = f"❌ **Nom déjà pris**\n\nLe groupe `{new_name}` existe déjà."
            keyboard = [[InlineKeyboardButton("🏠 Accueil", callback_data="refresh")]]
            
            # Clear conversation state for duplicate name
            context.user_data.pop('conversation_state', None)
            
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
    print(f"DEBUG: Renaming group {current_group_id_int} to '{new_name}'")
    if update_group_name(current_group_id_int, new_name):
        print(f"DEBUG: Group renamed successfully in database")
        # Invalidate ALL caches to ensure fresh data
        invalidate_cache()  # Invalidate global cache
        invalidate_user_cache(user_id)  # Invalidate user cache
        _clear_context_cache(context)  # Clear context cache
        
        # Recharge les données du groupe après la modification (avec cache invalidé)
        data = load_data()
        print(f"DEBUG: Reloaded data, group name is now: {data.get(str(current_group_id_int), {}).get('name', 'NOT FOUND')}")
        # Clear conversation state after successful rename
        context.user_data.pop('conversation_state', None)
        # Return to main menu
        from handlers.queries import get_main_message_content
        group_id = find_group_for_user(data, user_id)
        print(f"DEBUG: Found group_id: {group_id}")
        message_text, main_keyboard = get_main_message_content(data, group_id)
        print(f"DEBUG: Generated message with group name: {data.get(group_id, {}).get('name', 'NOT FOUND')}")
        
        # Add confirmation message to avoid "Message is not modified" error
        success_text = f"✅ **Groupe renommé !**\n\nLe groupe a été renommé en `{new_name}`\n\n{message_text}"
        
        if query:
            print(f"DEBUG: Updating via callback query")
            await query.edit_message_text(
                text=success_text,
                reply_markup=main_keyboard,
                parse_mode="Markdown"
            )
        else:
            print(f"DEBUG: Updating via text input")
            # For text input, update main message using utility function
            await update_main_message(context, success_text, main_keyboard)

    else:
        # Error updating group name
        message = "❌ **Erreur**\n\nImpossible de renommer le groupe. Veuillez réessayer."
        keyboard = [[InlineKeyboardButton("🏠 Accueil", callback_data="refresh")]]
        
        # Clear conversation state for database error
        context.user_data.pop('conversation_state', None)
        
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
    
    # Use cached data if available, otherwise load once
    data = getattr(context, '_cached_data', None)
    if data is None:
        data = load_data()
        context._cached_data = data
    
    user_id = update.effective_user.id
    current_group_id = find_group_for_user(data, user_id)
    
    # Find the target group by name
    target_group_id = None
    for group_id, group_info in data.items():
        if group_info.get('name') == target_group_name:
            target_group_id = group_id
            break
    
    # Check if group exists
    if target_group_id is None:
        message = "❌ **Groupe introuvable**\n\nCe groupe n'existe pas.\nVérifiez le nom et réessayez."
        keyboard = [[InlineKeyboardButton("🏠 Accueil", callback_data="refresh")]]
        
        # Clear conversation state for group not found
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
    
    # Check if user is already in this group
    if current_group_id == target_group_id:
        message = f"ℹ️ **Déjà dans le groupe**\n\nVous êtes déjà dans `{target_group_name}`."
        keyboard = [[InlineKeyboardButton("🏠 Accueil", callback_data="refresh")]]
        
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
            # Invalidate cache for this user
            invalidate_user_cache(user_id)
    
    # Add user to target group
    data[target_group_id]["users"].append(int(user_id))
    # Convert group_id to int for database function
    update_group(int(target_group_id), data[target_group_id])
    
    # Invalidate cache for this user
    invalidate_cache()  # Invalidate global cache
    invalidate_user_cache(user_id)  # Invalidate user cache
    _clear_context_cache(context)  # Clear context cache
    
    # Recharge les données du groupe après la modification (avec cache invalidé)
    data = load_data()
    # Clear conversation state after successful join
    context.user_data.pop('conversation_state', None)
    # Return to main menu
    from handlers.queries import get_main_message_content
    group_id = find_group_for_user(data, user_id)
    message_text, main_keyboard = get_main_message_content(data, group_id)
    
    # Add confirmation message to avoid "Message is not modified" error
    success_text = f"✅ **Groupe rejoint !**\n\nVous avez rejoint le groupe `{target_group_name}`\n\n{message_text}"
    
    if query:
        await query.edit_message_text(
            text=success_text,
            reply_markup=main_keyboard,
            parse_mode="Markdown"
        )
    else:
        # For text input, update main message using utility function
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
    
    # Validate new name
    if not is_valid_group_name(new_name):
        message = "❌ **Nom invalide**\n\nLe nom doit contenir 3-20 caractères et ne peut contenir que des lettres, chiffres, espaces et tirets."
        keyboard = [[InlineKeyboardButton("🏠 Accueil", callback_data="refresh")]]
        
        # Clear conversation state for invalid name
        context.user_data.pop('conversation_state', None)
        
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
    
    # Use cached data if available, otherwise load once
    data = getattr(context, '_cached_data', None)
    if data is None:
        data = load_data()
        context._cached_data = data
    
    user_id = update.effective_user.id
    current_group_id = find_group_for_user(data, user_id)
    
    # Check if name already exists using loaded data instead of database call
    for group_id, group_info in data.items():
        if group_info['name'] == new_name:
            message = f"❌ **Nom déjà pris**\n\nLe groupe `{new_name}` existe déjà."
            keyboard = [[InlineKeyboardButton("🏠 Accueil", callback_data="refresh")]]
            
            # Clear conversation state for duplicate name
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
            # Invalidate cache for this user
            invalidate_user_cache(user_id)
    
    # Create new group
    create_group(new_name, user_id)
    # Invalidate cache for this user
    invalidate_cache()  # Invalidate global cache
    invalidate_user_cache(user_id)  # Invalidate user cache
    _clear_context_cache(context)  # Clear context cache
    # Recharge les données du groupe après la création (avec cache invalidé)
    data = load_data()
    # Clear conversation state after successful creation
    context.user_data.pop('conversation_state', None)
    # Return to main menu
    from handlers.queries import get_main_message_content
    group_id = find_group_for_user(data, user_id)
    message_text, main_keyboard = get_main_message_content(data, group_id)
    
    # Add confirmation message to avoid "Message is not modified" error
    success_text = f"✅ **Groupe créé !**\n\nLe groupe `{new_name}` a été créé\n\n{message_text}"
    
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
    
    # Use cached data if available, otherwise load once
    data = getattr(context, '_cached_data', None)
    if data is None:
        data = load_data()
        context._cached_data = data
    
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
    
    # Invalidate cache once at the end
    invalidate_cache()  # Invalidate global cache
    _clear_context_cache(context)  # Clear context cache
    
    # Recharge les données du groupe après la modification (avec cache invalidé)
    data = load_data()
    # Clear conversation state after leaving group
    context.user_data.pop('conversation_state', None)
    
    # Return to main menu
    from handlers.queries import get_main_message_content
    group_id = find_group_for_user(data, user_id)
    message_text, main_keyboard = get_main_message_content(data, group_id)
    
    # Add confirmation message to avoid "Message is not modified" error
    success_text = f"✅ **Groupe quitté !**\n\nVous êtes retourné à votre groupe personnel\n\n{message_text}"
    
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