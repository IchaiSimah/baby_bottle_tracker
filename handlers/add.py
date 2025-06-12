from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters

from utils import load_data, save_data, find_group_for_user, create_personal_group

ASK_AMOUNT, ASK_TIME = range(2)

async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Quelle quantité de biberon avez-vous donné à votre bébé (en ml) ?")
    return ASK_AMOUNT

async def handle_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = int(update.message.text)
        context.user_data['amount'] = amount
        await update.message.reply_text("À quelle heure avez-vous donné le biberon (HH:MM) ? Ou tapez /now pour l'heure actuelle.")
        return ASK_TIME
    except ValueError:
        await update.message.reply_text("❌ Quantité invalide, merci de saisir un nombre en ml.")
        return ASK_AMOUNT

async def handle_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    try:
        time_str = update.message.text.strip()
        if time_str.lower() == "/now":
            time_str = datetime.now().strftime("%H:%M")
        else:
            datetime.strptime(time_str, "%H:%M")  # vérifie format heure

        date = datetime.now().date().strftime("%d-%m-%Y")
        timestamp = f"{date} {time_str}"
        amount = context.user_data['amount']

        data = load_data()
        group = find_group_for_user(data, user_id)
        if not group:
            group = create_personal_group(data, user_id)

        data[group]["entries"].append({"amount": amount, "time": timestamp})
        save_data(data)

        await update.message.reply_text(f"✅ Biberon de {amount}ml enregistré à {time_str}.")
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("❌ Format d'heure invalide, merci de saisir HH:MM ou /now.")
        return ASK_TIME

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Ajout annulé.")
    return ConversationHandler.END