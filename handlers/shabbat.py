from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from zoneinfo import ZoneInfo
from utils import load_data, save_data, find_group_for_user, create_personal_group, update_main_message, load_user_data,  update_all_group_messages
from database import add_entry_to_group, add_poop_to_group, get_language
from translations import t

ASK_SHABBAT_FRIDAY_POOP, ASK_SHABBAT_FRIDAY_BOTTLE, ASK_SHABBAT_SATURDAY_POOP, ASK_SHABBAT_SATURDAY_BOTTLE = range(4)

async def start_shabbat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    data = load_user_data(user_id)
    language = get_language(user_id)
    if not data:
        data = load_data()
        group_id = find_group_for_user(data, user_id)
        if not group_id:
            group_id = create_personal_group(data, user_id)
            await save_data(data, context)
            data = load_user_data(user_id)
    if not data:
        await query.edit_message_text(t("error_load_data", language))
        return
    group_id = list(data.keys())[0]
    group_data = data[group_id]
    td = group_data.get("time_difference", 0)
    if td is None:
        td = 0
    context.user_data['shabbat_group_id'] = group_id
    context.user_data['shabbat_time_difference'] = td
    # Demander le nombre de cacas vendredi soir
    keyboard = [[InlineKeyboardButton(t("btn_cancel", language), callback_data="cancel")]]
    message = t("shabbat_friday_poop", language)
    await query.edit_message_text(text=message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    context.user_data['conversation_state'] = 'shabbat_friday_poop'

async def handle_shabbat_friday_poop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    language = get_language(user_id)
    query = update.callback_query if hasattr(update, 'callback_query') and update.callback_query else None
    if query:
        await query.answer()
        value = query.data if not query.data.startswith('cancel') else None
    else:
        value = update.message.text.strip()
        await update.message.delete()
    if value is None or not value.isdigit():
        message = t("shabbat_invalid_number", language)
        keyboard = [[InlineKeyboardButton(t("btn_cancel", language), callback_data="cancel")]]
        if query:
            await query.edit_message_text(text=message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        else:
            await update_main_message(context, message, InlineKeyboardMarkup(keyboard))
        return
    context.user_data['shabbat_friday_poop'] = int(value)
    # Demander la quantité de lait vendredi soir
    keyboard = [[InlineKeyboardButton(t("btn_cancel", language), callback_data="cancel")]]
    message = t("shabbat_friday_bottle", language)
    if query:
        await query.edit_message_text(text=message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    else:
        await update_main_message(context, message, InlineKeyboardMarkup(keyboard))
    # Passer à l'état suivant pour router les entrées de texte
    context.user_data['conversation_state'] = 'shabbat_friday_bottle'

async def handle_shabbat_friday_bottle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gère la saisie de la quantité de lait vendredi soir"""
    user_id = update.effective_user.id
    language = get_language(user_id)
    query = update.callback_query if hasattr(update, 'callback_query') and update.callback_query else None
    if query:
        await query.answer()
        value = query.data if not query.data.startswith('cancel') else None
    else:
        value = update.message.text.strip()
        await update.message.delete()
    if value is None or not value.isdigit():
        message = t("shabbat_invalid_amount", language)
        keyboard = [[InlineKeyboardButton(t("btn_cancel", language), callback_data="cancel")]]
        if query:
            await query.edit_message_text(text=message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        else:
            await update_main_message(context, message, InlineKeyboardMarkup(keyboard))
        return
    context.user_data['shabbat_friday_bottle'] = int(value)
    # Demander le nombre de cacas samedi midi
    keyboard = [[InlineKeyboardButton(t("btn_cancel", language), callback_data="cancel")]]
    message = t("shabbat_saturday_poop", language)
    if query:
        await query.edit_message_text(text=message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    else:
        await update_main_message(context, message, InlineKeyboardMarkup(keyboard))
    context.user_data['conversation_state'] = 'shabbat_saturday_poop'

async def handle_shabbat_saturday_poop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    language = get_language(user_id)
    query = update.callback_query if hasattr(update, 'callback_query') and update.callback_query else None
    if query:
        await query.answer()
        value = query.data if not query.data.startswith('cancel') else None
    else:
        value = update.message.text.strip()
        await update.message.delete()
    if value is None or not value.isdigit():
        message = t("shabbat_invalid_number", language)
        keyboard = [[InlineKeyboardButton(t("btn_cancel", language), callback_data="cancel")]]
        if query:
            await query.edit_message_text(text=message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        else:
            await update_main_message(context, message, InlineKeyboardMarkup(keyboard))
        return
    context.user_data['shabbat_saturday_poop'] = int(value)
    # Demander la quantité de lait samedi midi
    keyboard = [[InlineKeyboardButton(t("btn_cancel", language), callback_data="cancel")]]
    message = t("shabbat_saturday_bottle", language)
    if query:
        await query.edit_message_text(text=message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    else:
        await update_main_message(context, message, InlineKeyboardMarkup(keyboard))
    context.user_data['conversation_state'] = 'shabbat_saturday_bottle'

async def handle_shabbat_saturday_bottle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    language = get_language(user_id)
    query = update.callback_query if hasattr(update, 'callback_query') and update.callback_query else None
    if query:
        await query.answer()
        value = query.data if not query.data.startswith('cancel') else None
    else:
        value = update.message.text.strip()
        await update.message.delete()
    if value is None or not value.isdigit():
        message = t("shabbat_invalid_amount", language)
        keyboard = [[InlineKeyboardButton(t("btn_cancel", language), callback_data="cancel")]]
        if query:
            await query.edit_message_text(text=message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        else:
            await update_main_message(context, message, InlineKeyboardMarkup(keyboard))
        return
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
    message_text, keyboard = get_main_message_content(data, group_id, language)
    message = t("shabbat_success", language) + "\n\n" + message_text
    
    # Update all group messages with the new content
    user_id = update.effective_user.id
    await update_all_group_messages(context, int(group_id), message_text, keyboard, user_id)
         
    if query:
        await query.edit_message_text(text=message, reply_markup=keyboard, parse_mode="Markdown")
    else:
        await update_main_message(context, message, keyboard)
    # Nettoyer l'état de conversation
    context.user_data.pop('conversation_state', None)
    context.user_data.pop('shabbat_group_id', None)
    context.user_data.pop('shabbat_time_difference', None)
    context.user_data.pop('shabbat_friday_poop', None)
    context.user_data.pop('shabbat_friday_bottle', None)
    context.user_data.pop('shabbat_saturday_poop', None)
    context.user_data.pop('shabbat_saturday_bottle', None) 

async def show_shabbat_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show Shabbat mode menu"""
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
        error_msg = t("error_load_data", language)
        await query.edit_message_text(error_msg)
        return
    
    # Get the group ID from the loaded data
    group_id = list(data.keys())[0]
    group_data = data[group_id]
    
    # Check if Shabbat mode is active
    shabbat_mode = group_data.get("shabbat_mode", False)
    
    if shabbat_mode:
        message = t("shabbat_active", language)
        keyboard = [
            [InlineKeyboardButton(t("btn_disable_shabbat", language), callback_data="shabbat_disable")],
            [InlineKeyboardButton(t("btn_home", language), callback_data="refresh")]
        ]
    else:
        message = t("shabbat_inactive", language)
        keyboard = [
            [InlineKeyboardButton(t("btn_enable_shabbat", language), callback_data="shabbat_enable")],
            [InlineKeyboardButton(t("btn_home", language), callback_data="refresh")]
        ]
    
    await query.edit_message_text(
        text=message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def enable_shabbat_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Enable Shabbat mode"""
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
        error_msg = t("error_load_data", language)
        await query.edit_message_text(error_msg)
        return
    
    # Get the group ID from the loaded data
    group_id = list(data.keys())[0]
    group_data = data[group_id]
    
    # Enable Shabbat mode
    group_data["shabbat_mode"] = True
    group_data["shabbat_start"] = datetime.now(ZoneInfo("UTC")).isoformat()
    
    # Save to database
    from database import update_group
    update_group(int(group_id), group_data)
    
    # Reload data
    data = load_user_data(user_id)
    if not data:
        data = load_data()
    
    # Return to main message with updated data
    from handlers.queries import get_main_message_content
    message_text, keyboard = get_main_message_content(data, group_id, language)
    
    # Update all group messages
    await update_all_group_messages(context, int(group_id), message_text, keyboard, user_id)
    
    success_msg = t("shabbat_enabled", language)
    keyboard = [[InlineKeyboardButton(t("btn_home", language), callback_data="refresh")]]
    
    await query.edit_message_text(
        text=success_msg,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def disable_shabbat_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Disable Shabbat mode"""
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
        error_msg = t("error_load_data", language)
        await query.edit_message_text(error_msg)
        return
    
    # Get the group ID from the loaded data
    group_id = list(data.keys())[0]
    group_data = data[group_id]
    
    # Disable Shabbat mode
    group_data["shabbat_mode"] = False
    if "shabbat_start" in group_data:
        del group_data["shabbat_start"]
    
    # Save to database
    from database import update_group
    update_group(int(group_id), group_data)
    
    # Reload data
    data = load_user_data(user_id)
    if not data:
        data = load_data()
    
    # Return to main message with updated data
    from handlers.queries import get_main_message_content
    message_text, keyboard = get_main_message_content(data, group_id, language)
    
    # Update all group messages
    await update_all_group_messages(context, int(group_id), message_text, keyboard, user_id)
    
    success_msg = t("shabbat_disabled", language)
    keyboard = [[InlineKeyboardButton(t("btn_home", language), callback_data="refresh")]]
    
    await query.edit_message_text(
        text=success_msg,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def add_shabbat_bottle(update: Update, context: ContextTypes.DEFAULT_TYPE, amount: int, time_str: str = None):
    """Add a bottle during Shabbat mode (without updating messages)"""
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
        return False
    
    # Get the group ID from the loaded data
    group_id = list(data.keys())[0]
    group_data = data[group_id]
    
    # Check if Shabbat mode is active
    if not group_data.get("shabbat_mode", False):
        return False
    
    # Parse time if provided, otherwise use current time
    if time_str:
        try:
            # Parse time string (format: HH:MM)
            hour, minute = map(int, time_str.split(":"))
            today = datetime.now(ZoneInfo("UTC")).date()
            dt = datetime.combine(today, datetime.min.time(), tzinfo=ZoneInfo("UTC"))
            dt = dt.replace(hour=hour, minute=minute)
        except:
            dt = datetime.now(ZoneInfo("UTC"))
    else:
        dt = datetime.now(ZoneInfo("UTC"))
    
    # Add the bottle entry to the database
    add_entry_to_group(int(group_id), amount, dt)
    
    return True 