from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from utils import load_data, find_group_for_user, load_user_data, update_all_group_messages
from database import remove_last_entry_from_group

async def delete_bottle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show confirmation dialog for deleting the last bottle"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    # Use optimized data loading
    data = load_user_data(user_id)
    if not data:
        # Fallback to old method if needed
        data = load_data()
        group_id = find_group_for_user(data, user_id)
        if not group_id or group_id not in data:
            error_msg = "❌ Oups ! Impossible de trouver ou créer votre groupe personnel pour le moment. Veuillez réessayer plus tard."
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
            "❌ Aucun biberon à supprimer dans votre groupe pour le moment.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Accueil", callback_data="refresh")]])
        )
        return False
    last_entry = group_data["entries"][0]
    
    # Show confirmation dialog
    message = f"🗑️ **Confirmer la suppression** ⚠️\n\n"
    message += f"Voulez-vous vraiment supprimer ce biberon ?\n\n"
    message += f"**🍼 Dernier biberon :**\n"
    message += f"• 📅 Date : {last_entry['time'].strftime('%d-%m-%Y')}\n"
    message += f"• 🕐 Heure : {last_entry['time'].strftime('%H:%M')}\n"
    message += f"• 🍼 Quantité : {last_entry['amount']}ml\n"
    
    keyboard = [
        [
            InlineKeyboardButton("✅ Oui, supprimer", callback_data="confirm_delete"),
            InlineKeyboardButton("❌ Non, annuler", callback_data="cancel_delete")
        ],
        [InlineKeyboardButton("🏠 Accueil", callback_data="refresh")]
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
    
    # Use optimized data loading
    data = load_user_data(user_id)
    if not data:
        # Fallback to old method if needed
        data = load_data()
        group_id = find_group_for_user(data, user_id)
        if not group_id or not data[group_id]["entries"]:
            await query.edit_message_text(
                "❌ Oups ! Aucun biberon à supprimer pour le moment.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Accueil", callback_data="refresh")]])
            )
            return False
        group_data = data[group_id]
    else:
        # Get the group ID from the loaded data
        group_id = list(data.keys())[0]
        group_data = data[group_id]
    
    if not group_data["entries"]:
        await query.edit_message_text(
            "❌ Oups ! Aucun biberon à supprimer pour le moment.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Accueil", callback_data="refresh")]])
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
    message_text, keyboard = get_main_message_content(data, group_id)
    
    # Update all group messages with the new content
    user_id = update.effective_user.id
    print(f"user_id: {user_id}")
        # Update all group messages with the new content
    await update_all_group_messages(context, int(group_id), message_text, keyboard, user_id)
       
    # Show confirmation
    await query.edit_message_text(
        f"✅ **Biberon supprimé avec succès !** 🗑️\n\nSupprimé : {removed_entry['amount']}ml à {removed_entry['time'].strftime('%H:%M')}",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Accueil", callback_data="refresh")]])
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
    message_text, keyboard = get_main_message_content_for_user(user_id)
    
    await query.edit_message_text(
        text=message_text,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )    
    return True
