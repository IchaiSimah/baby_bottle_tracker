from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from zoneinfo import ZoneInfo
from utils import load_data, save_data, find_group_for_user, create_personal_group, is_valid_time, getValidDate
from config import TEST_MODE

ASK_BOTTLE_TIME, ASK_BOTTLE_AMOUNT = range(2)

def round_to_nearest_quarter_hour(minutes, base=15):
    fraction = minutes % base
    if fraction == 0:
        return minutes  
    elif fraction < (base / 2):
        rounded = minutes - fraction
    else:
        rounded = minutes + (base - fraction)
    return int(rounded)

async def add_bottle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start the add bottle flow - show time selection"""
    query = update.callback_query
    await query.answer()
    
    data = load_data()
    user_id = update.effective_user.id
    group = find_group_for_user(data, user_id)
    if not group:
        group = create_personal_group(data, user_id)
        await save_data(data, context)
    
    time_difference = timedelta(hours=data[group].get("time_difference", 0))
    
    # Generate time suggestions

    current_time = datetime.now(ZoneInfo("UTC")) + time_difference
    
    suggestions = []
    for minutes in [60, 45, 30, 15]:
        suggestion_time = current_time - timedelta(minutes=minutes)
        minutes_rounded = round_to_nearest_quarter_hour(suggestion_time.minute)
        hour_rounded = suggestion_time.hour
        if minutes_rounded == 60:
            minutes_rounded = 0
            hour_rounded += 1
        if hour_rounded == 24:
            hour_rounded = 0
        suggested_time = datetime.now().replace(hour=hour_rounded, minute=minutes_rounded)
        suggestions.append(suggested_time.strftime("%H:%M"))
    
    # Create keyboard with time buttons
    keyboard = []
    for time_str in suggestions:
        keyboard.append([InlineKeyboardButton(time_str, callback_data=f"bottle_time_{time_str}")])
    
    # Add "Now" and "Cancel" buttons
    keyboard.append([
        InlineKeyboardButton("🕐 Maintenant", callback_data="bottle_time_now"),
        InlineKeyboardButton("❌ Annuler", callback_data="cancel")
    ])
    
    message = "⏰ **Choisissez l'heure du biberon:**\n\n*Ou tapez une heure manuellement (ex: 14:30)*"
    
    # Set conversation state for text input
    context.user_data['conversation_state'] = 'bottle_time'
    
    await query.edit_message_text(
        text=message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    
    return ASK_BOTTLE_TIME

async def handle_bottle_time(update: Update, context: ContextTypes.DEFAULT_TYPE, time_str: str = None):
    """Handle time selection and show amount selection"""
    # Check if this is a callback query or text message
    if hasattr(update, 'callback_query') and update.callback_query:
        query = update.callback_query
        await query.answer()
        if not time_str:
            # Extract time from callback data
            time_str = query.data.replace("bottle_time_", "")
    else:
        # This is a text message
        query = None
        if not time_str:
            time_str = update.message.text.strip()
    data = load_data()
    user_id = update.effective_user.id
    group = find_group_for_user(data, user_id)
    time_difference = timedelta(hours=data[group].get("time_difference", 0))
    try:
        if time_str.lower() == "now":
            time_str = (datetime.now(ZoneInfo("UTC")) + time_difference).strftime("%d-%m-%Y %H:%M")
            date = time_str.split(" ")[0]
            time_str = time_str.split(" ")[1]
        else:
            date = getValidDate(time_str, data[group].get("time_difference", 0))
        # Validate time format
        if not is_valid_time(time_str):
            error_msg = "❌ Format d'heure invalide. Veuillez réessayer."
            if query:
                await query.edit_message_text(
                    error_msg,
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("❌ Annuler", callback_data="cancel")
                    ]])
                )
            else:
                # Edit main message if possible
                message_id = context.user_data.get('main_message_id')
                chat_id = context.user_data.get('chat_id')
                if message_id and chat_id:
                    await context.bot.edit_message_text(
                        error_msg,
                        chat_id=chat_id,
                        message_id=message_id,
                        reply_markup=InlineKeyboardMarkup([[
                            InlineKeyboardButton("❌ Annuler", callback_data="cancel")
                        ]])
                    )
                else:
                    sent = await update.message.reply_text(error_msg)
                    context.user_data['main_message_id'] = sent.message_id
                    context.user_data['chat_id'] = sent.chat_id
            return ASK_BOTTLE_TIME
        # Store time in context
        context.user_data['bottle_time'] = f"{date} {time_str}"
        # Show amount selection
        last_bottle = data[group].get("last_bottle", 120)
        # Create amount buttons
        keyboard = []
        amounts = [last_bottle, last_bottle - 20, last_bottle - 10, last_bottle + 10, last_bottle + 20]
        amounts = list(dict.fromkeys(amounts))  # Remove duplicates while preserving order
        # Create rows of 2 buttons each
        for i in range(0, len(amounts), 2):
            row = []
            row.append(InlineKeyboardButton(f"{amounts[i]}ml", callback_data=f"bottle_amount_{amounts[i]}"))
            if i + 1 < len(amounts):
                row.append(InlineKeyboardButton(f"{amounts[i+1]}ml", callback_data=f"bottle_amount_{amounts[i+1]}"))
            keyboard.append(row)
        # Add cancel button
        keyboard.append([InlineKeyboardButton("❌ Annuler", callback_data="cancel")])
        message = f"🍼 **Choisissez la quantité (ml):**\n\nDernier biberon: {last_bottle}ml\n\n*Ou tapez une quantité manuellement (ex: 110)*"
        # Set conversation state for text input
        context.user_data['conversation_state'] = 'bottle_amount'
        if query:
            await query.edit_message_text(
                text=message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
        else:
            message_id = context.user_data.get('main_message_id')
            chat_id = context.user_data.get('chat_id')
            if message_id and chat_id:
                await context.bot.edit_message_text(
                    text=message,
                    chat_id=chat_id,
                    message_id=message_id,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="Markdown"
                )
            else:
                sent = await update.message.reply_text(
                    text=message,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="Markdown"
                )
                context.user_data['main_message_id'] = sent.message_id
                context.user_data['chat_id'] = sent.chat_id
        return ASK_BOTTLE_AMOUNT
    except Exception as e:
        error_msg = f"❌ Erreur: {str(e)}"
        if query:
            await query.edit_message_text(
                error_msg,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("❌ Annuler", callback_data="cancel")
                ]])
            )
        else:
            message_id = context.user_data.get('main_message_id')
            chat_id = context.user_data.get('chat_id')
            if message_id and chat_id:
                await context.bot.edit_message_text(
                    error_msg,
                    chat_id=chat_id,
                    message_id=message_id,
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("❌ Annuler", callback_data="cancel")
                    ]])
                )
            else:
                sent = await update.message.reply_text(error_msg)
                context.user_data['main_message_id'] = sent.message_id
                context.user_data['chat_id'] = sent.chat_id
        return ConversationHandler.END

async def handle_bottle_amount(update: Update, context: ContextTypes.DEFAULT_TYPE, amount_str: str = None):
    """Handle amount selection and save the bottle entry"""
    # Check if this is a callback query or text message
    if hasattr(update, 'callback_query') and update.callback_query:
        query = update.callback_query
        await query.answer()
        if not amount_str:
            # Extract amount from callback data
            amount_str = query.data.replace("bottle_amount_", "")
    else:
        # This is a text message
        query = None
        if not amount_str:
            amount_str = update.message.text.strip()
    try:
        amount = int(amount_str)
        timestamp = context.user_data.get('bottle_time')
        if not timestamp:
            error_msg = "❌ Erreur: temps non trouvé. Veuillez recommencer."
            if query:
                await query.edit_message_text(
                    error_msg,
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("❌ Annuler", callback_data="cancel")
                    ]])
                )
            else:
                message_id = context.user_data.get('main_message_id')
                chat_id = context.user_data.get('chat_id')
                if message_id and chat_id:
                    await context.bot.edit_message_text(
                        error_msg,
                        chat_id=chat_id,
                        message_id=message_id,
                        reply_markup=InlineKeyboardMarkup([[
                            InlineKeyboardButton("❌ Annuler", callback_data="cancel")
                        ]])
                    )
                else:
                    sent = await update.message.reply_text(error_msg)
                    context.user_data['main_message_id'] = sent.message_id
                    context.user_data['chat_id'] = sent.chat_id
            return ConversationHandler.END
        # Save the bottle entry
        data = load_data()
        user_id = update.effective_user.id
        group = find_group_for_user(data, user_id)
        data[group]["entries"].append({"amount": amount, "time": timestamp})
        data[group]["last_bottle"] = amount
        await save_data(data, context)
        # Show success message and return to main
        from handlers.queries import get_main_message_content
        message_text, keyboard = get_main_message_content(data, group)
        success_text = f"✅ **Biberon de {amount}ml enregistré !**\n\n{message_text}"
        if query:
            await query.edit_message_text(
                text=success_text,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
        else:
            message_id = context.user_data.get('main_message_id')
            chat_id = context.user_data.get('chat_id')
            if message_id and chat_id:
                await context.bot.edit_message_text(
                    text=success_text,
                    chat_id=chat_id,
                    message_id=message_id,
                    reply_markup=keyboard,
                    parse_mode="Markdown"
                )
            else:
                sent = await update.message.reply_text(
                    text=success_text,
                    reply_markup=keyboard,
                    parse_mode="Markdown"
                )
                context.user_data['main_message_id'] = sent.message_id
                context.user_data['chat_id'] = sent.chat_id
        return ConversationHandler.END
    except ValueError:
        error_msg = "❌ Quantité invalide. Veuillez réessayer."
        if query:
            await query.edit_message_text(
                error_msg,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("❌ Annuler", callback_data="cancel")
                ]])
            )
        else:
            message_id = context.user_data.get('main_message_id')
            chat_id = context.user_data.get('chat_id')
            if message_id and chat_id:
                await context.bot.edit_message_text(
                    error_msg,
                    chat_id=chat_id,
                    message_id=message_id,
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("❌ Annuler", callback_data="cancel")
                    ]])
                )
            else:
                sent = await update.message.reply_text(error_msg)
                context.user_data['main_message_id'] = sent.message_id
                context.user_data['chat_id'] = sent.chat_id
        return ASK_BOTTLE_AMOUNT
    except Exception as e:
        error_msg = f"❌ Erreur: {str(e)}"
        if query:
            await query.edit_message_text(
                error_msg,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("❌ Annuler", callback_data="cancel")
                ]])
            )
        else:
            message_id = context.user_data.get('main_message_id')
            chat_id = context.user_data.get('chat_id')
            if message_id and chat_id:
                await context.bot.edit_message_text(
                    error_msg,
                    chat_id=chat_id,
                    message_id=message_id,
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("❌ Annuler", callback_data="cancel")
                    ]])
                )
            else:
                sent = await update.message.reply_text(error_msg)
                context.user_data['main_message_id'] = sent.message_id
                context.user_data['chat_id'] = sent.chat_id
        return ConversationHandler.END

async def cancel_bottle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel the add bottle flow and return to main"""
    query = update.callback_query
    await query.answer()
    
    data = load_data()
    user_id = update.effective_user.id
    group = find_group_for_user(data, user_id)
    
    # Clear conversation state
    context.user_data.pop('conversation_state', None)
    
    from handlers.queries import get_main_message_content
    message_text, keyboard = get_main_message_content(data, group)
    
    await query.edit_message_text(
        text=message_text,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    
    return ConversationHandler.END