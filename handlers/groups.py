from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from utils import load_data, find_group_for_user, create_personal_group, save_data, ensure_main_message_exists, set_group_message_info, get_group_message_info, clear_group_message_info
from database import create_group, get_group_by_name, update_group_name, get_group_by_id, update_group
from handlers.queries import get_main_message_content
import json

# Conversation states
WAITING_GROUP_NAME = 1
WAITING_GROUP_JOIN = 2
WAITING_GROUP_RENAME = 3

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
        # Reload data only if group was created
        if group_id:
            data = load_data()
            context._cached_data = data
    
    if not group_id or group_id not in data:
        error_msg = "❌ Erreur : impossible de trouver ou créer votre groupe personnel. Merci de réessayer plus tard."
        await query.edit_message_text(error_msg)
        return
    
    group_info = data[group_id]
    group_name = group_info.get('name', 'Groupe sans nom')
    users = group_info.get('users', [])
    
    # Create groups menu message
    message = f"👥 **Gestion des Groupes**\n\n"
    message += f"**Groupe actuel :** {group_name}\n"
    message += f"**Membres :** {len(users)} utilisateur(s)\n\n"
    message += "**Options disponibles :**"
    
    # Create keyboard
    keyboard = [
        [InlineKeyboardButton("🆕 Créer un nouveau groupe", callback_data="group_create")],
        [InlineKeyboardButton("🔗 Rejoindre un groupe", callback_data="group_join")],
        [InlineKeyboardButton("✏️ Renommer le groupe", callback_data="group_rename")],
        [InlineKeyboardButton("🚪 Quitter le groupe", callback_data="group_leave")],
        [InlineKeyboardButton("🏠 Retour", callback_data="refresh")]
    ]
    
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
        # Reload data only if group was created
        if group_id:
            data = load_data()
            context._cached_data = data
    
    if not group_id or group_id not in data:
        error_msg = "❌ Erreur : impossible de trouver ou créer votre groupe personnel. Merci de réessayer plus tard."
        await query.edit_message_text(error_msg)
        return
    
    if action == "rename":
        await show_rename_group(update, context, group_id)
    elif action == "join":
        await show_join_group(update, context, action)
    elif action == "create":
        await show_create_group(update, context)
    elif action == "leave":
        await leave_group(update, context, group_id)
        return

    # Clear conversation state for other states
    if action not in ['join', 'create', 'rename']:
        context.user_data.pop('conversation_state', None)

    await save_data(data, context)

async def show_create_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show create group interface"""
    query = update.callback_query
    await query.answer()
    
    message = "🆕 **Créer un nouveau groupe**\n\n"
    message += "Entrez le nom du nouveau groupe :\n\n"
    message += "💡 **Conseils :**\n"
    message += "• Choisissez un nom descriptif\n"
    message += "• Évitez les caractères spéciaux\n"
    message += "• Le nom doit être unique"
    
    keyboard = [[InlineKeyboardButton("❌ Annuler", callback_data="refresh")]]
    
    await query.edit_message_text(
        text=message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    
    # Set conversation state
    context.user_data['conversation_state'] = 'group_create'

async def create_new_group(update: Update, context: ContextTypes.DEFAULT_TYPE, group_name: str = None):
    """Create a new group"""
    if not group_name:
        # Handle text input
        if not update.message or not update.message.text:
            return ConversationHandler.END
        
        group_name = update.message.text.strip()
    
    user_id = update.effective_user.id
    
    # Validate group name
    if len(group_name) < 2:
        error_msg = "❌ Le nom du groupe doit contenir au moins 2 caractères."
        if hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.edit_message_text(error_msg)
        else:
            await update.message.reply_text(error_msg)
        return ConversationHandler.END
    
    if len(group_name) > 50:
        error_msg = "❌ Le nom du groupe ne peut pas dépasser 50 caractères."
        if hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.edit_message_text(error_msg)
        else:
            await update.message.reply_text(error_msg)
        return ConversationHandler.END
    
    # Check if group name already exists
    existing_group = get_group_by_name(group_name)
    if existing_group:
        error_msg = f"❌ Un groupe avec le nom '{group_name}' existe déjà."
        if hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.edit_message_text(error_msg)
        else:
            await update.message.reply_text(error_msg)
        return ConversationHandler.END
    
    # Create the group
    new_group_id = create_group(group_name, user_id)
    if not new_group_id:
        error_msg = "❌ Erreur lors de la création du groupe. Veuillez réessayer."
        if hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.edit_message_text(error_msg)
        else:
            await update.message.reply_text(error_msg)
        return ConversationHandler.END
    
    # Success message
    success_msg = f"✅ **Groupe créé avec succès !**\n\n"
    success_msg += f"**Nom :** {group_name}\n"
    success_msg += f"**ID :** {new_group_id}\n\n"
    success_msg += "Vous êtes maintenant membre de ce groupe."
    
    keyboard = [[InlineKeyboardButton("🏠 Retour", callback_data="refresh")]]
    
    if hasattr(update, 'callback_query') and update.callback_query:
        await update.callback_query.edit_message_text(
            text=success_msg,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            text=success_msg,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    
    # Clear conversation state
    context.user_data.pop('conversation_state', None)
    return ConversationHandler.END

async def show_join_group(update: Update, context: ContextTypes.DEFAULT_TYPE, action: str = None):
    """Show join group interface"""
    query = update.callback_query
    await query.answer()
    
    message = "🔗 **Rejoindre un groupe**\n\n"
    message += "Entrez l'ID du groupe que vous souhaitez rejoindre :\n\n"
    message += "💡 **Comment trouver l'ID :**\n"
    message += "• Demandez à un membre du groupe\n"
    message += "• L'ID est affiché dans les paramètres du groupe"
    
    keyboard = [[InlineKeyboardButton("❌ Annuler", callback_data="refresh")]]
    
    await query.edit_message_text(
        text=message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    
    # Set conversation state
    context.user_data['conversation_state'] = 'group_join'

async def join_group(update: Update, context: ContextTypes.DEFAULT_TYPE, group_id_str: str = None):
    """Join an existing group"""
    if not group_id_str:
        # Handle text input
        if not update.message or not update.message.text:
            return ConversationHandler.END
        
        group_id_str = update.message.text.strip()
    
    user_id = update.effective_user.id
    
    # Validate group ID
    try:
        group_id = int(group_id_str)
    except ValueError:
        error_msg = "❌ L'ID du groupe doit être un nombre."
        if hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.edit_message_text(error_msg)
        else:
            await update.message.reply_text(error_msg)
        return ConversationHandler.END
    
    # Check if group exists
    group_data = get_group_by_id(group_id)
    if not group_data:
        error_msg = f"❌ Aucun groupe trouvé avec l'ID {group_id}."
        if hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.edit_message_text(error_msg)
        else:
            await update.message.reply_text(error_msg)
        return ConversationHandler.END
    
    # Check if user is already in the group
    users = group_data.get('users', [])
    if user_id in users:
        error_msg = f"❌ Vous êtes déjà membre du groupe '{group_data['name']}'."
        if hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.edit_message_text(error_msg)
        else:
            await update.message.reply_text(error_msg)
        return ConversationHandler.END
    
    # Add user to group
    users.append(user_id)
    group_data['users'] = users
    
    success = update_group(group_id, group_data)
    if not success:
        error_msg = "❌ Erreur lors de l'ajout au groupe. Veuillez réessayer."
        if hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.edit_message_text(error_msg)
        else:
            await update.message.reply_text(error_msg)
        return ConversationHandler.END
    
    # Success message
    success_msg = f"✅ **Groupe rejoint avec succès !**\n\n"
    success_msg += f"**Groupe :** {group_data['name']}\n"
    success_msg += f"**ID :** {group_id}\n\n"
    success_msg += "Vous pouvez maintenant voir et modifier les données de ce groupe."
    
    keyboard = [[InlineKeyboardButton("🏠 Retour", callback_data="refresh")]]
    
    if hasattr(update, 'callback_query') and update.callback_query:
        await update.callback_query.edit_message_text(
            text=success_msg,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            text=success_msg,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    
    # Clear conversation state
    context.user_data.pop('conversation_state', None)
    return ConversationHandler.END

async def show_rename_group(update: Update, context: ContextTypes.DEFAULT_TYPE, group_id: str):
    """Show rename group interface"""
    query = update.callback_query
    await query.answer()
    
    # Get current group name
    data = load_data()
    group_info = data.get(group_id, {})
    current_name = group_info.get('name', 'Groupe sans nom')
    
    message = f"✏️ **Renommer le groupe**\n\n"
    message += f"**Nom actuel :** {current_name}\n\n"
    message += "Entrez le nouveau nom du groupe :\n\n"
    message += "💡 **Conseils :**\n"
    message += "• Choisissez un nom descriptif\n"
    message += "• Évitez les caractères spéciaux\n"
    message += "• Le nom doit être unique"
    
    keyboard = [[InlineKeyboardButton("❌ Annuler", callback_data="refresh")]]
    
    await query.edit_message_text(
        text=message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    
    # Set conversation state
    context.user_data['conversation_state'] = 'group_rename'

async def rename_group(update: Update, context: ContextTypes.DEFAULT_TYPE, group_id: str, new_name: str = None):
    """Rename a group"""
    if not new_name:
        # Handle text input
        if not update.message or not update.message.text:
            return ConversationHandler.END
        
        new_name = update.message.text.strip()
    
    # Validate new name
    if len(new_name) < 2:
        error_msg = "❌ Le nom du groupe doit contenir au moins 2 caractères."
        if hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.edit_message_text(error_msg)
        else:
            await update.message.reply_text(error_msg)
        return ConversationHandler.END
    
    if len(new_name) > 50:
        error_msg = "❌ Le nom du groupe ne peut pas dépasser 50 caractères."
        if hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.edit_message_text(error_msg)
        else:
            await update.message.reply_text(error_msg)
        return ConversationHandler.END
    
    # Check if new name already exists
    existing_group = get_group_by_name(new_name)
    if existing_group and str(existing_group['id']) != group_id:
        error_msg = f"❌ Un groupe avec le nom '{new_name}' existe déjà."
        if hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.edit_message_text(error_msg)
        else:
            await update.message.reply_text(error_msg)
        return ConversationHandler.END
    
    # Update group name
    success = update_group_name(int(group_id), new_name)
    if not success:
        error_msg = "❌ Erreur lors du renommage du groupe. Veuillez réessayer."
        if hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.edit_message_text(error_msg)
        else:
            await update.message.reply_text(error_msg)
        return ConversationHandler.END
    
    # Success message
    success_msg = f"✅ **Groupe renommé avec succès !**\n\n"
    success_msg += f"**Nouveau nom :** {new_name}"
    
    keyboard = [[InlineKeyboardButton("🏠 Retour", callback_data="refresh")]]
    
    if hasattr(update, 'callback_query') and update.callback_query:
        await update.callback_query.edit_message_text(
            text=success_msg,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            text=success_msg,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    
    # Clear conversation state
    context.user_data.pop('conversation_state', None)
    return ConversationHandler.END

async def leave_group(update: Update, context: ContextTypes.DEFAULT_TYPE, group_id: str):
    """Leave current group and create personal group"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    # Get current group info
    data = load_data()
    group_info = data.get(group_id, {})
    group_name = group_info.get('name', 'Groupe sans nom')
    users = group_info.get('users', [])
    
    # Check if user is in the group
    if user_id not in users:
        error_msg = "❌ Vous n'êtes pas membre de ce groupe."
        await query.edit_message_text(error_msg)
        return
    
    # Remove user from group
    users.remove(user_id)
    group_info['users'] = users
    
    # Update group
    success = update_group(int(group_id), group_info)
    if not success:
        error_msg = "❌ Erreur lors de la sortie du groupe. Veuillez réessayer."
        await query.edit_message_text(error_msg)
        return
    
    # Create personal group for user
    personal_group_id = create_personal_group(data, user_id)
    if not personal_group_id:
        error_msg = "❌ Erreur lors de la création du groupe personnel. Veuillez réessayer."
        await query.edit_message_text(error_msg)
        return
    
    # Success message
    success_msg = f"✅ **Groupe quitté avec succès !**\n\n"
    success_msg += f"Vous avez quitté le groupe '{group_name}'.\n"
    success_msg += f"Un nouveau groupe personnel a été créé pour vous."
    
    keyboard = [[InlineKeyboardButton("🏠 Retour", callback_data="refresh")]]
    
    await query.edit_message_text(
        text=success_msg,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    ) 