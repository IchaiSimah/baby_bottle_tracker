from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from utils import load_data, save_data, find_group_for_user, create_personal_group
import re

async def show_groups_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show the groups management menu"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    data = load_data()
    group = find_group_for_user(data, user_id)
    
    if not group:
        group = create_personal_group(data, user_id)
        await save_data(data, context)
    
    # Get current group info
    group_info = data[group]
    group_name = group
    member_count = len(group_info.get("users", []))
    
    message = f"👥 **Gestion des Groupes**\n\n"
    message += f"**Groupe actuel :** `{group_name}`\n"
    message += f"**Membres :** {member_count}\n"
    
    if group.startswith("group_"):
        message += "\n*Vous êtes dans un groupe personnel*\n"
    else:
        message += "\n*Vous êtes dans un groupe partagé*\n"
    
    # Create keyboard
    keyboard = [
        [InlineKeyboardButton("✏️ Renommer le groupe", callback_data="group_rename")],
        [InlineKeyboardButton("🔗 Rejoindre un groupe", callback_data="group_join")],
        [InlineKeyboardButton("➕ Créer un groupe", callback_data="group_create")],
    ]
    
    if not group.startswith("group_"):
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
    
    user_id = update.effective_user.id
    data = load_data()
    current_group = find_group_for_user(data, user_id)
    
    if action == "rename":
        await show_rename_group(update, context, current_group)
    elif action == "join":
        await show_join_group(update, context)
    elif action == "create":
        await show_create_group(update, context)
    elif action == "leave":
        await leave_group(update, context, current_group)

    # Clear conversation state for other states
    if action != 'group_join':
        context.user_data.pop('conversation_state', None)

    # Handle group join text input
    if action == 'group_join':
        from handlers.groups import join_group
        await join_group(update, context, query.data.split('_')[1])

    await save_data(data, context)

    await show_groups_menu(update, context)

async def show_rename_group(update: Update, context: ContextTypes.DEFAULT_TYPE, current_group: str):
    """Show rename group interface"""
    query = update.callback_query
    
    message = f"✏️ **Renommer le groupe**\n\n"
    message += f"Groupe actuel : `{current_group}`\n\n"
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

async def rename_group(update: Update, context: ContextTypes.DEFAULT_TYPE, current_group: str, new_name: str):
    """Rename the current group"""
    # Check if this is a callback query or text input
    if hasattr(update, 'callback_query') and update.callback_query:
        query = update.callback_query
        await query.answer()
    else:
        query = None
    
    # Validate new name
    if not is_valid_group_name(new_name):
        message = "❌ **Nom invalide**\n\nLe nom doit contenir 3-20 caractères et ne peut contenir que des lettres, chiffres, espaces et tirets."
        keyboard = [[InlineKeyboardButton("🏠 Accueil", callback_data="refresh")]]
        
        if query:
            await query.edit_message_text(
                message,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            # For text input, return to main
            from handlers.queries import get_main_message_content
            data = load_data()
            user_id = update.effective_user.id
            group = find_group_for_user(data, user_id)
            message_text, main_keyboard = get_main_message_content(data, group)
            message_id = context.user_data.get('main_message_id')
            chat_id = context.user_data.get('chat_id')
            if message_id and chat_id:
                await context.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id,
                    text=message_text,
                    reply_markup=main_keyboard,
                    parse_mode="Markdown"
                )
            else:
                sent = await update.message.reply_text(
                    text=message_text,
                    reply_markup=main_keyboard,
                    parse_mode="Markdown"
                )
                context.user_data['main_message_id'] = sent.message_id
                context.user_data['chat_id'] = sent.chat_id
        return
    
    data = load_data()
    
    # Check if name already exists
    if new_name in data:
        message = f"❌ **Nom déjà pris**\n\nLe groupe `{new_name}` existe déjà."
        keyboard = [[InlineKeyboardButton("🏠 Accueil", callback_data="refresh")]]
        
        if query:
            await query.edit_message_text(
                message,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            # For text input, return to main
            from handlers.queries import get_main_message_content
            group = find_group_for_user(data, update.effective_user.id)
            message_text, main_keyboard = get_main_message_content(data, group)
            message_id = context.user_data.get('main_message_id')
            chat_id = context.user_data.get('chat_id')
            if message_id and chat_id:
                await context.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id,
                    text=message_text,
                    reply_markup=main_keyboard,
                    parse_mode="Markdown"
                )
            else:
                sent = await update.message.reply_text(
                    text=message_text,
                    reply_markup=main_keyboard,
                    parse_mode="Markdown"
                )
                context.user_data['main_message_id'] = sent.message_id
                context.user_data['chat_id'] = sent.chat_id
        return
    
    # Rename the group
    group_data = data.pop(current_group)
    data[new_name] = group_data
    
    await save_data(data, context)
    
    message = f"✅ **Groupe renommé !**\n\n`{current_group}` → `{new_name}`"
    keyboard = [[InlineKeyboardButton("🏠 Accueil", callback_data="refresh")]]
    
    if query:
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        # For text input, return to main
        from handlers.queries import get_main_message_content
        group = find_group_for_user(data, update.effective_user.id)
        message_text, main_keyboard = get_main_message_content(data, group)
        message_id = context.user_data.get('main_message_id')
        chat_id = context.user_data.get('chat_id')
        if message_id and chat_id:
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=message_text,
                reply_markup=main_keyboard,
                parse_mode="Markdown"
            )
        else:
            sent = await update.message.reply_text(
                text=message_text,
                reply_markup=main_keyboard,
                parse_mode="Markdown"
            )
            context.user_data['main_message_id'] = sent.message_id
            context.user_data['chat_id'] = sent.chat_id

async def join_group(update: Update, context: ContextTypes.DEFAULT_TYPE, target_group: str):
    """Join an existing group"""
    # Check if this is a callback query or text input
    if hasattr(update, 'callback_query') and update.callback_query:
        query = update.callback_query
        await query.answer()
    else:
        query = None
    
    data = load_data()
    user_id = update.effective_user.id
    current_group = find_group_for_user(data, user_id)
    
    # Check if group exists
    if target_group not in data:
        message = "❌ **Groupe introuvable**\n\nCe groupe n'existe pas.\nVérifiez le nom et réessayez."
        keyboard = [[InlineKeyboardButton("🏠 Accueil", callback_data="refresh")]]
        
        if query:
            await query.edit_message_text(
                message,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            # For text input, return to main
            from handlers.queries import get_main_message_content
            group = find_group_for_user(data, user_id)
            message_text, main_keyboard = get_main_message_content(data, group)
            message_id = context.user_data.get('main_message_id')
            chat_id = context.user_data.get('chat_id')
            if message_id and chat_id:
                await context.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id,
                    text=message_text,
                    reply_markup=main_keyboard,
                    parse_mode="Markdown"
                )
            else:
                sent = await update.message.reply_text(
                    text=message_text,
                    reply_markup=main_keyboard,
                    parse_mode="Markdown"
                )
                context.user_data['main_message_id'] = sent.message_id
                context.user_data['chat_id'] = sent.chat_id
        return
    
    # Check if user is already in this group
    if current_group == target_group:
        message = f"ℹ️ **Déjà dans le groupe**\n\nVous êtes déjà dans `{target_group}`."
        keyboard = [[InlineKeyboardButton("🏠 Accueil", callback_data="refresh")]]
        
        if query:
            await query.edit_message_text(
                message,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            # For text input, return to main
            from handlers.queries import get_main_message_content
            group = find_group_for_user(data, user_id)
            message_text, main_keyboard = get_main_message_content(data, group)
            message_id = context.user_data.get('main_message_id')
            chat_id = context.user_data.get('chat_id')
            if message_id and chat_id:
                await context.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id,
                    text=message_text,
                    reply_markup=main_keyboard,
                    parse_mode="Markdown"
                )
            else:
                sent = await update.message.reply_text(
                    text=message_text,
                    reply_markup=main_keyboard,
                    parse_mode="Markdown"
                )
                context.user_data['main_message_id'] = sent.message_id
                context.user_data['chat_id'] = sent.chat_id
        return
    
    # Remove user from current group
    if current_group and current_group in data:
        if user_id in data[current_group].get("users", []):
            data[current_group]["users"].remove(user_id)
    
    # Add user to target group
    if "users" not in data[target_group]:
        data[target_group]["users"] = []
    data[target_group]["users"].append(user_id)
    
    await save_data(data, context)
    
    member_count = len(data[target_group]["users"])
    message = f"✅ **Groupe rejoint !**\n\nVous avez rejoint `{target_group}`\nMembres : {member_count}"
    keyboard = [[InlineKeyboardButton("🏠 Accueil", callback_data="refresh")]]
    
    if query:
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        # For text input, return to main
        from handlers.queries import get_main_message_content
        group = find_group_for_user(data, user_id)
        message_text, main_keyboard = get_main_message_content(data, group)
        message_id = context.user_data.get('main_message_id')
        chat_id = context.user_data.get('chat_id')
        if message_id and chat_id:
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=message_text,
                reply_markup=main_keyboard,
                parse_mode="Markdown"
            )
        else:
            sent = await update.message.reply_text(
                text=message_text,
                reply_markup=main_keyboard,
                parse_mode="Markdown"
            )
            context.user_data['main_message_id'] = sent.message_id
            context.user_data['chat_id'] = sent.chat_id

async def create_new_group(update: Update, context: ContextTypes.DEFAULT_TYPE, new_name: str):
    """Create a new group"""
    # Check if this is a callback query or text input
    if hasattr(update, 'callback_query') and update.callback_query:
        query = update.callback_query
        await query.answer()
    else:
        query = None
    
    # Validate new name
    if not is_valid_group_name(new_name):
        message = "❌ **Nom invalide**\n\nLe nom doit contenir 3-20 caractères et ne peut contenir que des lettres, chiffres, espaces et tirets."
        keyboard = [[InlineKeyboardButton("🏠 Accueil", callback_data="refresh")]]
        
        if query:
            await query.edit_message_text(
                message,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            # For text input, return to main
            from handlers.queries import get_main_message_content
            data = load_data()
            user_id = update.effective_user.id
            group = find_group_for_user(data, user_id)
            message_text, main_keyboard = get_main_message_content(data, group)
            message_id = context.user_data.get('main_message_id')
            chat_id = context.user_data.get('chat_id')
            if message_id and chat_id:
                await context.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id,
                    text=message_text,
                    reply_markup=main_keyboard,
                    parse_mode="Markdown"
                )
            else:
                sent = await update.message.reply_text(
                    text=message_text,
                    reply_markup=main_keyboard,
                    parse_mode="Markdown"
                )
                context.user_data['main_message_id'] = sent.message_id
                context.user_data['chat_id'] = sent.chat_id
        return
    
    data = load_data()
    user_id = update.effective_user.id
    current_group = find_group_for_user(data, user_id)
    
    # Check if name already exists
    if new_name in data:
        message = f"❌ **Nom déjà pris**\n\nLe groupe `{new_name}` existe déjà."
        keyboard = [[InlineKeyboardButton("🏠 Accueil", callback_data="refresh")]]
        
        if query:
            await query.edit_message_text(
                message,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            # For text input, return to main
            from handlers.queries import get_main_message_content
            group = find_group_for_user(data, user_id)
            message_text, main_keyboard = get_main_message_content(data, group)
            message_id = context.user_data.get('main_message_id')
            chat_id = context.user_data.get('chat_id')
            if message_id and chat_id:
                await context.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id,
                    text=message_text,
                    reply_markup=main_keyboard,
                    parse_mode="Markdown"
                )
            else:
                sent = await update.message.reply_text(
                    text=message_text,
                    reply_markup=main_keyboard,
                    parse_mode="Markdown"
                )
                context.user_data['main_message_id'] = sent.message_id
                context.user_data['chat_id'] = sent.chat_id
        return
    
    # Remove user from current group
    if current_group and current_group in data:
        if user_id in data[current_group].get("users", []):
            data[current_group]["users"].remove(user_id)
    
    # Create new group
    data[new_name] = {
        "users": [user_id],
        "entries": [],
        "poop": [],
        "time_difference": 0,
        "bottles_to_show": 5,
        "poops_to_show": 1
    }
    
    await save_data(data, context)
    
    message = f"✅ **Groupe créé !**\n\nNouveau groupe : `{new_name}`\nVous en êtes le premier membre."
    keyboard = [[InlineKeyboardButton("🏠 Accueil", callback_data="refresh")]]
    
    if query:
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        # For text input, return to main
        from handlers.queries import get_main_message_content
        group = find_group_for_user(data, user_id)
        message_text, main_keyboard = get_main_message_content(data, group)
        message_id = context.user_data.get('main_message_id')
        chat_id = context.user_data.get('chat_id')
        if message_id and chat_id:
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=message_text,
                reply_markup=main_keyboard,
                parse_mode="Markdown"
            )
        else:
            sent = await update.message.reply_text(
                text=message_text,
                reply_markup=main_keyboard,
                parse_mode="Markdown"
            )
            context.user_data['main_message_id'] = sent.message_id
            context.user_data['chat_id'] = sent.chat_id

async def leave_group(update: Update, context: ContextTypes.DEFAULT_TYPE, current_group: str):
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
    if current_group in data:
        if user_id in data[current_group].get("users", []):
            data[current_group]["users"].remove(user_id)
    
    # Create or use personal group
    personal_group = f"group_{user_id}"
    if personal_group not in data:
        data[personal_group] = {
            "users": [user_id],
            "entries": [],
            "poop": [],
            "time_difference": 0,
            "bottles_to_show": 5,
            "poops_to_show": 1
        }
    else:
        data[personal_group]["users"] = [user_id]
    
    await save_data(data, context)
    
    message = f"✅ **Groupe quitté !**\n\nVous êtes maintenant dans votre groupe personnel : `{personal_group}`"
    keyboard = [[InlineKeyboardButton("🏠 Accueil", callback_data="refresh")]]
    
    if query:
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        # For text input, return to main
        from handlers.queries import get_main_message_content
        group = find_group_for_user(data, user_id)
        message_text, main_keyboard = get_main_message_content(data, group)
        message_id = context.user_data.get('main_message_id')
        chat_id = context.user_data.get('chat_id')
        if message_id and chat_id:
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=message_text,
                reply_markup=main_keyboard,
                parse_mode="Markdown"
            )
        else:
            sent = await update.message.reply_text(
                text=message_text,
                reply_markup=main_keyboard,
                parse_mode="Markdown"
            )
            context.user_data['main_message_id'] = sent.message_id
            context.user_data['chat_id'] = sent.chat_id

def is_valid_group_name(name: str) -> bool:
    """Validate group name format"""
    if len(name) < 3 or len(name) > 20:
        return False
    
    # Allow letters, numbers, spaces, and hyphens
    pattern = r'^[a-zA-Z0-9\s\-]+$'
    return bool(re.match(pattern, name)) 