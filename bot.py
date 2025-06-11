import json
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, ConversationHandler, MessageHandler, filters

import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")



DATA_FILE = "biberons.json"
ASK_AMOUNT, ASK_TIME = range(2)

# load and save data
def load_data():
    try:
        with open(DATA_FILE, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

def save_data(data):
    with open(DATA_FILE, 'w') as file:
        json.dump(data, file, indent=2)

# find the group to which the user belongs
def find_group_for_user(data, user_id):
    for group_name, group_info in data.items():
        if user_id in group_info.get("users", []):
            return group_name
    return None

# create a personal group for a user
def create_personal_group(data, user_id):
    group_name = f"group_{user_id}"
    data[group_name] = {"users": [user_id], "entries": []}
    return group_name

# command /add : start the conversation
async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Quelle quantité de biberon avez-vous donné à votre bébé (en ml) ?")
    return ASK_AMOUNT

# handle the amount
async def handle_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = int(update.message.text)
        context.user_data['amount'] = amount
        await update.message.reply_text("À quelle heure avez-vous donné le biberon (HH:MM) ? Ou tapez /now pour l'heure actuelle.")
        return ASK_TIME
    except ValueError:
        await update.message.reply_text("❌ Quantité invalide, merci de saisir un nombre en ml.")
        return ASK_AMOUNT

# handle the time and save in the group
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

# command /last : last biberon of the group
async def last(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    data = load_data()
    group = find_group_for_user(data, user_id)
    if not group:
        await update.message.reply_text("Vous n'êtes dans aucun groupe et aucun biberon enregistré.")
        return
    entries = data[group]["entries"]
    if not entries:
        await update.message.reply_text("Aucun biberon enregistré dans votre groupe.")
        return
    last_entry = entries[-1]
    await update.message.reply_text(f"🍼 Dernier biberon: {last_entry['amount']}ml à {last_entry['time']}")

# command /list : 4 last biberons of the group
async def list_biberons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    data = load_data()
    group = find_group_for_user(data, user_id)
    if not group:
        await update.message.reply_text("Vous n'êtes dans aucun groupe et aucun biberon enregistré.")
        return
    entries = data[group]["entries"]
    if not entries:
        await update.message.reply_text("Aucun biberon enregistré.")
        return
    last_entries = entries[-4:]
    await update.message.reply_text(f"🍼 Liste des 4 derniers biberons:")
    for entry in last_entries:
        await update.message.reply_text(f"{entry['amount']}ml à {entry['time']}")

# command /total : total of the day of the group
async def total(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    data = load_data()
    group = find_group_for_user(data, user_id)
    if not group:
        await update.message.reply_text("Vous n'êtes dans aucun groupe et aucun biberon enregistré.")
        return
    today = datetime.now().strftime("%d-%m-%Y")
    total_ml = sum(entry["amount"] for entry in data[group]["entries"] if today in entry["time"])
    await update.message.reply_text(f"📊 Total aujourd'hui : {total_ml}ml")

# command /delete : delete the last biberon of the group
async def delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    data = load_data()
    group = find_group_for_user(data, user_id)
    if not group:
        await update.message.reply_text("Vous n'êtes dans aucun groupe, rien à supprimer.")
        return
    if not data[group]["entries"]:
        await update.message.reply_text("Aucun biberon à supprimer dans votre groupe.")
        return
    data[group]["entries"].pop()
    save_data(data)
    await update.message.reply_text(f"✅ Dernier biberon supprimé dans {group}.")

# command /join to join an existing group
async def join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if len(context.args) == 0:
        await update.message.reply_text("Utilisation: /join <nom_du_groupe>")
        return
    group_name = context.args[0]
    data = load_data()
    if group_name not in data:
        await update.message.reply_text(f"Le groupe {group_name} n'existe pas.")
        return
    if user_id in data[group_name]["users"]:
        await update.message.reply_text(f"Tu fais déjà partie du groupe {group_name}.")
        return
    # Retirer l'utilisateur d'un autre groupe s'il est dedans
    old_group = find_group_for_user(data, user_id)
    if old_group:
        data[old_group]["users"].remove(user_id)
    # Ajouter dans le nouveau groupe
    data[group_name]["users"].append(user_id)
    save_data(data)
    await update.message.reply_text(f"✅ Tu as rejoint le groupe {group_name}.")

# command /start and /help
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Hello ! Commandes disponibles :\n"
        "/add - Ajouter un biberon\n"
        "/last - Dernier biberon\n"
        "/total - Total du jour\n"
        "/list - Liste des 4 derniers biberons\n"
        "/delete - Supprime le dernier biberon\n"
        "/join <nom_du_groupe> - Rejoindre un groupe\n"
        "/help - Affiche cette aide\n"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)

# error handling
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    print(f"Error: {context.error}")
    if update and update.effective_message:
        await update.effective_message.reply_text("❌ Une erreur s'est produite. Veuillez réessayer.")

def main():
    print("🚀 Initializing bot...")
    app = ApplicationBuilder().token(TOKEN).build()


    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("add", add)],
        states={
            ASK_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_amount)],
            ASK_TIME: [MessageHandler(filters.TEXT | filters.COMMAND, handle_time)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("last", last))
    app.add_handler(CommandHandler("total", total))
    app.add_handler(CommandHandler("list", list_biberons))
    app.add_handler(CommandHandler("delete", delete))
    app.add_handler(CommandHandler("join", join))
    app.add_handler(conv_handler)
    app.add_error_handler(error_handler)

    print("✅ Bot initialized successfully!")
    print("🤖 Bot is now running! You can interact with it on Telegram.")
    print("Press Ctrl+C to stop the bot.")

    app.run_polling()

if __name__ == "__main__":
    main()