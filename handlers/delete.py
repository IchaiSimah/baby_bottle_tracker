from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from utils import load_data, save_data, find_group_for_user

async def delete_bottle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show confirmation dialog for deleting the last bottle"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    data = load_data()
    group = find_group_for_user(data, user_id)
    if not group:
        await query.edit_message_text(
            "❌ Vous n'êtes dans aucun groupe, rien à supprimer.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🏠 Accueil", callback_data="refresh")
            ]])
        )
        return False
    
    if not data[group]["entries"]:
        await query.edit_message_text(
            "❌ Aucun biberon à supprimer dans votre groupe.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🏠 Accueil", callback_data="refresh")
            ]])
        )
        return False
    
    # Get the last entry for confirmation
    last_entry = data[group]["entries"][-1]
    
    # Show confirmation dialog
    message = f"🗑️ **Confirmer la suppression**\n\n"
    message += f"Voulez-vous vraiment supprimer ce biberon ?\n\n"
    message += f"**Dernier biberon :**\n"
    message += f"• 📅 Date : {last_entry['time'].split(' ')[0]}\n"
    message += f"• 🕐 Heure : {last_entry['time'].split(' ')[1]}\n"
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
    data = load_data()
    group = find_group_for_user(data, user_id)
    
    if not group or not data[group]["entries"]:
        await query.edit_message_text(
            "❌ Erreur : Aucun biberon à supprimer.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🏠 Accueil", callback_data="refresh")
            ]])
        )
        return False
    
    # Remove the last entry
    removed_entry = data[group]["entries"].pop()
    await save_data(data, context)
    
    # Show confirmation
    await query.edit_message_text(
        f"✅ **Biberon supprimé !**\n\n"
        f"Supprimé : {removed_entry['amount']}ml à {removed_entry['time'].split(' ')[1]}",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🏠 Accueil", callback_data="refresh")
        ]])
    )
    
    return True

async def cancel_delete_bottle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel the deletion and return to main"""
    query = update.callback_query
    await query.answer()
    
    # Return to main message
    from handlers.queries import get_main_message_content
    from utils import load_data, find_group_for_user
    
    user_id = update.effective_user.id
    data = load_data()
    group = find_group_for_user(data, user_id)
    message_text, keyboard = get_main_message_content(data, group)
    
    await query.edit_message_text(
        text=message_text,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    
    return True