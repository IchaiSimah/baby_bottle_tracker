from datetime import datetime, timedelta
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters
from zoneinfo import ZoneInfo
from utils import load_data, save_data, find_group_for_user, create_personal_group, is_valid_time, getValidDate
from config import TEST_MODE

ASK_AMOUNT, ASK_TIME = range(2)


def round_to_nearest_quarter_hour(minutes, base=15):

    fraction = minutes % base
    if fraction == 0:
        return minutes  
    elif fraction < (base / 2):
        rounded = minutes - fraction
    else:
        rounded = minutes + (base - fraction)
    return int(rounded)

async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    user_id = update.effective_user.id
    group = find_group_for_user(data, user_id)
    if not group:
        group = create_personal_group(data, user_id)
    if not "time_difference" in data[group]:
        data[group]["time_difference"] = 0
    if not "last_bottle" in data[group]:
        await update.message.reply_text("Quelle quantité de biberon avez-vous donné à votre bébé (en ml) ?")
    else:
        await update.message.reply_text(f"Quelle quantité de biberon avez-vous donné à votre bébé (en ml)? /{data[group]['last_bottle']}ml?")
    await save_data(data, context)
    return ASK_AMOUNT

async def handle_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    user_id = update.effective_user.id
    group = find_group_for_user(data, user_id)
    time_difference = timedelta(hours=data[group]["time_difference"])
    try:
        if update.message.text == "/cancel":
            await update.message.reply_text("❌ Ajout annulé.", reply_markup=ReplyKeyboardRemove())
            return ConversationHandler.END
        if "last_bottle" in data[group] and update.message.text == f"/{data[group]['last_bottle']}ml":
            amount = data[group]["last_bottle"]
        else:
                amount = int(update.message.text)
        context.user_data['amount'] = amount
        if TEST_MODE:
            current_time = (datetime.now(ZoneInfo("UTC")) + time_difference).replace(hour=0, minute=50)
        else:
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
        keyboard = [[KeyboardButton(hour)] for hour in suggestions]
        message = f"À quelle heure avez-vous donné le biberon (HH:MM) ? Ou tapez /now pour l'heure actuelle."
        await update.message.reply_text(message, reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True))

        # if data[group]["time_difference"] == 0:
        #     await update.message.reply_text("Vous pouvez mettre à jour l'heure du bot avec la commande /timeUpdate <HH:MM>",parse_mode="Markdown")
        return ASK_TIME
    except ValueError as e:
        await update.message.reply_text(f"❌ Quantité invalide, merci de saisir un nombre en ml.")
        print(e)
        return ASK_AMOUNT



async def handle_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    user_id = update.effective_user.id
    group = find_group_for_user(data, user_id)
    time_difference = timedelta(hours=data[group]["time_difference"])

    try:
        date = datetime.now().date().strftime("%d-%m-%Y")
        time_str = update.message.text.strip()
        if time_str == "/cancel":
            await update.message.reply_text("❌ Ajout annulé.", reply_markup=ReplyKeyboardRemove())
            return ConversationHandler.END
            
        if time_str.lower() == "/now":
            time_str = (datetime.now(ZoneInfo("UTC")) + time_difference).strftime("%d-%m-%Y %H:%M")
            date = time_str.split(" ")[0]
            time_str = time_str.split(" ")[1]
        else:
            if time_str.startswith("/"):
                time_str = time_str[1:]
            date = getValidDate(time_str, data[group]["time_difference"])
            
        #we check if the time is valid
        if not is_valid_time(time_str):
            await update.message.reply_text(
                "❌ Format d'heure invalide. Merci d'utiliser le format HH:MM (ex: 14:30)\n"
            )
            return ASK_TIME

        timestamp = f"{date} {time_str}"
        amount = context.user_data['amount']

        data[group]["entries"].append({"amount": amount, "time": timestamp})
        data[group]["last_bottle"] = amount
        await save_data(data, context)

        await update.message.reply_text(f"✅ Biberon de {amount}ml enregistré à {time_str}.", reply_markup = ReplyKeyboardRemove())
        return ConversationHandler.END
    except ValueError as e:
        await update.message.reply_text("❌ Format d'heure invalide, merci de saisir HH:MM ou /now.")
        print(e)
        return ASK_TIME

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Ajout annulé.", reply_markup = ReplyKeyboardRemove())
    return ConversationHandler.END