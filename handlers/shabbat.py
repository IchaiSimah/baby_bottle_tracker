from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from zoneinfo import ZoneInfo
from utils import load_data, save_data, find_group_for_user, create_personal_group, update_main_message, set_group_message_info, load_user_data,  update_all_group_messages
from database import add_entry_to_group, add_poop_to_group

ASK_SHABBAT_FRIDAY_POOP, ASK_SHABBAT_FRIDAY_BOTTLE, ASK_SHABBAT_SATURDAY_POOP, ASK_SHABBAT_SATURDAY_BOTTLE = range(4)

async def start_shabbat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    data = load_user_data(user_id)
    if not data:
        data = load_data()
        group_id = find_group_for_user(data, user_id)
        if not group_id:
            group_id = create_personal_group(data, user_id)
            await save_data(data, context)
            data = load_user_data(user_id)
    if not data:
        await query.edit_message_text("❌ Oups ! Impossible de trouver ou créer votre groupe personnel pour le moment. Veuillez réessayer plus tard.")
        return ConversationHandler.END
    group_id = list(data.keys())[0]
    group_data = data[group_id]
    td = group_data.get("time_difference", 0)
    if td is None:
        td = 0
    context.user_data['shabbat_group_id'] = group_id
    context.user_data['shabbat_time_difference'] = td
    # Demander le nombre de cacas vendredi soir
    keyboard = [[InlineKeyboardButton("❌ Annuler", callback_data="cancel")]]
    message = "🕯️ **Shabbat**\n\nCombien de cacas ont eu lieu vendredi soir (après le début du shabbat) ?"
    await query.edit_message_text(text=message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    context.user_data['conversation_state'] = 'shabbat_friday_poop'
    return ASK_SHABBAT_FRIDAY_POOP

async def handle_shabbat_friday_poop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query if hasattr(update, 'callback_query') and update.callback_query else None
    if query:
        await query.answer()
        value = query.data if not query.data.startswith('cancel') else None
    else:
        value = update.message.text.strip()
        await update.message.delete()
    if value is None or not value.isdigit():
        message = "❌ Merci d'entrer un nombre valide de cacas (ex: 2)."
        keyboard = [[InlineKeyboardButton("❌ Annuler", callback_data="cancel")]]
        if query:
            await query.edit_message_text(text=message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        else:
            await update_main_message(context, message, InlineKeyboardMarkup(keyboard))
        return ASK_SHABBAT_FRIDAY_POOP
    context.user_data['shabbat_friday_poop'] = int(value)
    # Demander la quantité de lait vendredi soir
    keyboard = [[InlineKeyboardButton("❌ Annuler", callback_data="cancel")]]
    message = "🕯️ **Shabbat**\n\nQuelle quantité totale de lait a été bue vendredi soir (en ml) ?"
    if query:
        await query.edit_message_text(text=message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    else:
        await update_main_message(context, message, InlineKeyboardMarkup(keyboard))
    context.user_data['conversation_state'] = 'shabbat_friday_bottle'
    return ASK_SHABBAT_FRIDAY_BOTTLE

async def handle_shabbat_friday_bottle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query if hasattr(update, 'callback_query') and update.callback_query else None
    if query:
        await query.answer()
        value = query.data if not query.data.startswith('cancel') else None
    else:
        value = update.message.text.strip()
        await update.message.delete()
    if value is None or not value.isdigit():
        message = "❌ Merci d'entrer une quantité valide (en ml, ex: 150)."
        keyboard = [[InlineKeyboardButton("❌ Annuler", callback_data="cancel")]]
        if query:
            await query.edit_message_text(text=message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        else:
            await update_main_message(context, message, InlineKeyboardMarkup(keyboard))
        return ASK_SHABBAT_FRIDAY_BOTTLE
    context.user_data['shabbat_friday_bottle'] = int(value)
    # Demander le nombre de cacas samedi midi
    keyboard = [[InlineKeyboardButton("❌ Annuler", callback_data="cancel")]]
    message = "🕯️ **Shabbat**\n\nCombien de cacas ont eu lieu samedi (avant la fin du shabbat) ?"
    if query:
        await query.edit_message_text(text=message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    else:
        await update_main_message(context, message, InlineKeyboardMarkup(keyboard))
    context.user_data['conversation_state'] = 'shabbat_saturday_poop'
    return ASK_SHABBAT_SATURDAY_POOP

async def handle_shabbat_saturday_poop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query if hasattr(update, 'callback_query') and update.callback_query else None
    if query:
        await query.answer()
        value = query.data if not query.data.startswith('cancel') else None
    else:
        value = update.message.text.strip()
        await update.message.delete()
    if value is None or not value.isdigit():
        message = "❌ Merci d'entrer un nombre valide de cacas (ex: 1)."
        keyboard = [[InlineKeyboardButton("❌ Annuler", callback_data="cancel")]]
        if query:
            await query.edit_message_text(text=message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        else:
            await update_main_message(context, message, InlineKeyboardMarkup(keyboard))
        return ASK_SHABBAT_SATURDAY_POOP
    context.user_data['shabbat_saturday_poop'] = int(value)
    # Demander la quantité de lait samedi midi
    keyboard = [[InlineKeyboardButton("❌ Annuler", callback_data="cancel")]]
    message = "🕯️ **Shabbat**\n\nQuelle quantité totale de lait a été bue samedi (en ml) ?"
    if query:
        await query.edit_message_text(text=message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    else:
        await update_main_message(context, message, InlineKeyboardMarkup(keyboard))
    context.user_data['conversation_state'] = 'shabbat_saturday_bottle'
    return ASK_SHABBAT_SATURDAY_BOTTLE

async def handle_shabbat_saturday_bottle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query if hasattr(update, 'callback_query') and update.callback_query else None
    if query:
        await query.answer()
        value = query.data if not query.data.startswith('cancel') else None
    else:
        value = update.message.text.strip()
        await update.message.delete()
    if value is None or not value.isdigit():
        message = "❌ Merci d'entrer une quantité valide (en ml, ex: 120)."
        keyboard = [[InlineKeyboardButton("❌ Annuler", callback_data="cancel")]]
        if query:
            await query.edit_message_text(text=message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        else:
            await update_main_message(context, message, InlineKeyboardMarkup(keyboard))
        return ASK_SHABBAT_SATURDAY_BOTTLE
    context.user_data['shabbat_saturday_bottle'] = int(value)
    # Ajout des entrées dans la base de données
    user_id = update.effective_user.id
    group_id = context.user_data['shabbat_group_id']
    td = context.user_data['shabbat_time_difference']
    time_difference = timedelta(hours=td)
    # Calculer les dates
    now = datetime.now(ZoneInfo("UTC")) + time_difference
    # Vendredi soir (23h)
    friday = now - timedelta(days=(now.weekday() - 4) % 7)
    friday_23h = friday.replace(hour=23, minute=0, second=0, microsecond=0)
    # Samedi midi (12h)
    saturday = friday + timedelta(days=1)
    saturday_12h = saturday.replace(hour=12, minute=0, second=0, microsecond=0)
    # Ajouter les cacas vendredi soir
    for _ in range(context.user_data['shabbat_friday_poop']):
        add_poop_to_group(int(group_id), friday_23h)
    # Ajouter le biberon vendredi soir
    if context.user_data['shabbat_friday_bottle'] > 0:
        add_entry_to_group(int(group_id), context.user_data['shabbat_friday_bottle'], friday_23h)
    # Ajouter les cacas samedi midi
    for _ in range(context.user_data['shabbat_saturday_poop']):
        add_poop_to_group(int(group_id), saturday_12h)
    # Ajouter le biberon samedi midi
    if context.user_data['shabbat_saturday_bottle'] > 0:
        add_entry_to_group(int(group_id), context.user_data['shabbat_saturday_bottle'], saturday_12h)

    # Message de succès et retour à l'accueil
    from handlers.queries import get_main_message_content
    data = load_user_data(user_id)
    message_text, keyboard = get_main_message_content(data, group_id)
    message = "✅ Les valeurs Shabbat ont bien été enregistrées !\n\n" + message_text
    
    # Update all group messages with the new content
    user_id = update.effective_user.id
    print(f"user_id: {user_id}")
        # Update all group messages with the new content
    await update_all_group_messages(context, int(group_id), message_text, keyboard, user_id)
         
    if query:
        await query.edit_message_text(text=message, reply_markup=keyboard, parse_mode="Markdown")
    else:
        await update_main_message(context, message, keyboard)
    # Nettoyer l'état
    context.user_data.pop('conversation_state', None)
    context.user_data.pop('shabbat_group_id', None)
    context.user_data.pop('shabbat_time_difference', None)
    context.user_data.pop('shabbat_friday_poop', None)
    context.user_data.pop('shabbat_friday_bottle', None)
    context.user_data.pop('shabbat_saturday_poop', None)
    context.user_data.pop('shabbat_saturday_bottle', None)
    return ConversationHandler.END 