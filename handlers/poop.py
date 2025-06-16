from datetime import datetime, timedelta
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters
from zoneinfo import ZoneInfo
from utils import load_data, save_data, find_group_for_user, create_personal_group, is_valid_time

ASK_TIME_POOP, ASK_INFO_POOP = range(2)


def round_to_nearest_quarter_hour(minutes, base=15):

    fraction = minutes % base
    if fraction == 0:
        return minutes  
    elif fraction < (base / 2):
        rounded = minutes - fraction
    else:
        rounded = minutes + (base - fraction)
    return int(rounded)

async def poop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    user_id = update.effective_user.id
    group = find_group_for_user(data, user_id)
    if not group:
        group = create_personal_group(data, user_id)
    if not "time_difference" in data[group]:
        data[group]["time_difference"] = 0
    time_difference = timedelta(hours=data[group]["time_difference"])
    current_time = datetime.now(ZoneInfo("UTC")) + time_difference

    message = f"À quelle heure a t il fait un caca 💩?  Ou tapez /now pour l'heure actuelle."
    await update.message.reply_text(message)
    return ASK_TIME_POOP



async def handle_time_poop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    user_id = update.effective_user.id
    group = find_group_for_user(data, user_id)
    time_difference = timedelta(hours=data[group]["time_difference"])
    try:
        time_str = update.message.text.strip()
        if time_str == "/cancel":
            await update.message.reply_text("❌ Ajout annulé.", reply_markup = ReplyKeyboardRemove())
            return ConversationHandler.END
        if time_str.lower() == "/now":
            time_str = (datetime.now(ZoneInfo("UTC")) + time_difference).strftime("%H:%M")
        elif time_str.startswith("/"):
            time_str = time_str[1:]
        else:
            datetime.strptime(time_str, "%H:%M")  
        if not is_valid_time(time_str):
            await update.message.reply_text(
                "❌ Format d'heure invalide. Merci d'utiliser le format HH:MM (ex: 14:30)\n"
            )
            return ASK_TIME_POOP

        await update.message.reply_text("information additionnelle? (optionnel) /no pour passer")
        context.user_data['time'] = time_str
        return ASK_INFO_POOP
    except ValueError as e:
        await update.message.reply_text("❌ Format d'heure invalide, merci de saisir HH:MM ou /now.")
        print(e)
        return ASK_TIME_POOP

async def handle_info_poop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    user_id = update.effective_user.id
    group = find_group_for_user(data, user_id)

    info = update.message.text.strip()

    if info == "/cancel":
        await update.message.reply_text("❌ Ajout annulé.", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END

    if info == "/no":
        info = None
    elif info.startswith("/"):
        await update.message.reply_text(
            "❌ Format d'information invalide. Merci de saisir une information, /no ou /cancel pour annuler.",
            reply_markup=ReplyKeyboardRemove()
        )
        return ASK_INFO_POOP

    if "time" not in context.user_data:
        await update.message.reply_text("⛔ Temps introuvable. Veuillez recommencer.")
        return ConversationHandler.END
    date = datetime.now().date().strftime("%d-%m-%Y")
    timestamp = f"{date} {context.user_data['time']}"
    if "poop" not in data[group]:
        data[group]["poop"] = []
    
    data[group]["poop"].append({
        "time": timestamp,
        "info": info
    })

    await save_data(data, context)

    await update.message.reply_text(
        f"✅ Caca enregistré à {context.user_data['time']}.",
        reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Ajout annulé.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END