from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from utils import load_data, save_data, find_group_for_user, create_personal_group, normalize_time, ensure_main_message_exists, update_main_message, set_group_message_info, invalidate_user_cache
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from config import TEST_MODE
from database import update_group

async def show_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show settings menu"""
    query = update.callback_query
    await query.answer()
    
    data = load_data()
    user_id = update.effective_user.id
    group_id = find_group_for_user(data, user_id)
    if not group_id:
        group_id = create_personal_group(data, user_id)
        await save_data(data, context)
        data = load_data()
    
    if not group_id or group_id not in data:
        error_msg = "❌ Erreur : impossible de trouver ou créer votre groupe personnel. Merci de réessayer plus tard."
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
    time_difference = td
    adjusted_time = datetime.now(ZoneInfo("UTC")) + timedelta(hours=time_difference)
    
    message = "⚙️ **Paramètres:**\n\n"
    message += f"**Affichage principal:**\n"
    message += f"• 🍼 Biberons affichés: {bottles_to_show}\n"
    message += f"• 💩 Cacas affichés: {poops_to_show}\n\n"
    message += f"**Fuseau horaire:**\n"
    message += f"• 🕐 Décalage: {time_difference:+d}h\n"
    message += f"• ⏰ Heure actuelle: {adjusted_time.strftime('%H:%M')}\n\n"
    message += "**Modifier les paramètres:**"
    
    # Create keyboard for settings
    keyboard = [
        [
            InlineKeyboardButton(f"🍼 Biberons: {bottles_to_show}", callback_data="setting_bottles"),
            InlineKeyboardButton(f"💩 Cacas: {poops_to_show}", callback_data="setting_poops")
        ],
        [
            
        ],
        [
            InlineKeyboardButton("🕐 Changer l'heure", callback_data="setting_timezone")
        ],
        [
            InlineKeyboardButton("👥 Groupes", callback_data="groups")
        ],
        [
            InlineKeyboardButton("🏠 Accueil", callback_data="refresh"),
            InlineKeyboardButton("❌ Annuler", callback_data="cancel")
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
    group_id = find_group_for_user(data, user_id)
    
    if not group_id or group_id not in data:
        error_msg = "❌ Erreur : impossible de trouver ou créer votre groupe personnel. Merci de réessayer plus tard."
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
        
        keyboard.append([InlineKeyboardButton("❌ Annuler", callback_data="settings")])
        
        message = "🍼 **Choisissez le nombre de biberons à afficher:**"
        
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
        
        keyboard.append([InlineKeyboardButton("❌ Annuler", callback_data="settings")])
        
        message = "💩 **Choisissez le nombre de cacas à afficher:**"
        
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
        # Invalidate cache for this user
        invalidate_user_cache(user_id)
        # Recharge les données du groupe après la modification
        data = load_data()
        await show_settings(update, context)
    
    elif setting.startswith("set_poops_"):
        count = int(setting.replace("set_poops_", ""))
        data[group_id]["poops_to_show"] = count
        # Convert group_id to int for database function
        update_group(int(group_id), data[group_id])
        # Invalidate cache for this user
        invalidate_user_cache(user_id)
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
        
        message = f"🕐 **Configuration de l'heure:**\n\n" \
                 f"**Heure actuellement enregistrée:** {current_time.strftime('%H:%M')}\n" \
                 f"**Heure UTC du serveur:** {utc_time.strftime('%H:%M')}\n\n" \
                 f"**Quelle heure est-il chez vous actuellement ?**"
        
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
        
        keyboard.append([InlineKeyboardButton("❌ Annuler", callback_data="settings")])
        
        # Add manual input option
        keyboard.append([InlineKeyboardButton("✏️ Saisir manuellement", callback_data="manual_time_input")])
        
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
            # Invalidate cache for this user
            invalidate_user_cache(user_id)
            # Recharge les données du groupe après la modification
            data = load_data()
            adjusted_time = datetime.now(ZoneInfo("UTC")) + timedelta(hours=diff_hour)
            message = f"✅ **Heure mise à jour avec succès !**\n\n" \
                     f"**Votre heure:** {time_str}\n" \
                     f"**Heure UTC:** {now.strftime('%H:%M')}\n" \
                     f"**Décalage calculé:** {diff_hour:+d}h\n\n" \
                     f"🕐 L'heure du bot est maintenant synchronisée avec votre fuseau horaire."
            keyboard = [[InlineKeyboardButton("🏠 Retour aux paramètres", callback_data="settings")]]
            await query.edit_message_text(
                text=message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
        except ValueError:
            message = "❌ **Erreur:** Format d'heure invalide.\n\n" \
                     f"**Format attendu:** HH:MM ou H:MM\n" \
                     f"**Exemples:** 14:30, 7:30"
            keyboard = [[InlineKeyboardButton("❌ Annuler", callback_data="settings")]]
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
        
        keyboard.append([InlineKeyboardButton("❌ Annuler", callback_data="cancel")])
        
        message = "👥 **Choisissez un groupe:**"
        
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
            "❌ Opération annulée.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🏠 Accueil", callback_data="refresh")
            ]])
        )
    
    elif setting == "settings":
        # Show settings menu
        await show_settings(update, context)
    
    elif setting == "manual_time_input":
        # Set the conversation state for manual timezone input
        context.user_data['conversation_state'] = 'timezone_input'
        message = "✏️ **Saisissez l'heure locale au format HH:MM (ex: 14:30)**"
        keyboard = [[InlineKeyboardButton("❌ Annuler", callback_data="settings")]]
        await query.edit_message_text(
            text=message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

async def handle_timezone_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE, time_str: str):
    """Handle manual timezone text input"""
    user_id = update.effective_user.id
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
        # Invalidate cache for this user
        invalidate_user_cache(user_id)
        # Recharge les données du groupe après la modification
        data = load_data()
        # Clear conversation state
        context.user_data.pop('conversation_state', None)
        # Show confirmation
        adjusted_time = datetime.now(ZoneInfo("UTC")) + timedelta(hours=diff_hour)
        message = f"✅ **Heure mise à jour avec succès !**\n\n" \
                 f"**Votre heure:** {normalized_time}\n" \
                 f"**Heure UTC:** {now.strftime('%H:%M')}\n" \
                 f"**Décalage calculé:** {diff_hour:+d}h\n\n" \
                 f"🕐 L'heure du bot est maintenant synchronisée avec votre fuseau horaire."
        keyboard = [[InlineKeyboardButton("🏠 Retour aux paramètres", callback_data="settings")]]
        # Use utility function to update main message
        await ensure_main_message_exists(update, context, data, group_id)
        await update_main_message(context, message, InlineKeyboardMarkup(keyboard))
    except Exception as e:

        message = f"❌ **Erreur:** le format de l'heure est invalide\n\n" \
                 f"**Format attendu:** HH:MM ou H:MM\n" \
                 f"**Exemples:** 14:30, 7:30\n\n" \
                 f"veuillez réessayer en entrant l'heure au format attendu"
        keyboard = [[InlineKeyboardButton("❌ Annuler", callback_data="settings")]]
        await ensure_main_message_exists(update, context, data, group_id)
        await update_main_message(context, message, InlineKeyboardMarkup(keyboard)) 