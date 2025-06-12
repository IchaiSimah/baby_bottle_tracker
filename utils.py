import json

DATA_FILE = "biberons.json"
BACKUP_CHANNEL_ID = -1002871053724

def load_data():
    try:
        with open(DATA_FILE, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

async def save_data(data, context):
    with open(DATA_FILE, 'w') as file:
        json.dump(data, file, indent=2)
    try:
        with open(DATA_FILE, "rb") as f:
            await context.bot.send_document(chat_id=BACKUP_CHANNEL_ID, document=f, filename="backup_biberons.json", caption="🧠 Nouvelle sauvegarde")
    except Exception as e:
        print(f"Erreur d'envoi de sauvegarde : {e}")

def find_group_for_user(data, user_id):
    for group_name, group_info in data.items():
        if user_id in group_info.get("users", []):
            return group_name
    return None

def create_personal_group(data, user_id):
    group_name = f"group_{user_id}"
    data[group_name] = {"users": [user_id], "entries": []}
    return group_name