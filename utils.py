import json
from telethon.sync import TelegramClient
import os
from dotenv import load_dotenv
from telethon.sessions import StringSession

load_dotenv()

DATA_FILE = "biberons.json"
BACKUP_CHANNEL_ID = os.getenv("BACKUP_CHANNEL_ID")
TELEGRAM_API_ID = os.getenv("TELEGRAM_API_ID")
TELEGRAM_API_HASH = os.getenv("TELEGRAM_API_HASH")
SESSION_STRING = os.getenv("STRING_SESSION")


if not all([TELEGRAM_API_ID, TELEGRAM_API_HASH, BACKUP_CHANNEL_ID]):
    missing = []
    if not TELEGRAM_API_ID: missing.append("TELEGRAM_API_ID")
    if not TELEGRAM_API_HASH: missing.append("TELEGRAM_API_HASH")
    if not BACKUP_CHANNEL_ID: missing.append("BACKUP_CHANNEL_ID")
    raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

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

def load_backup_from_channel():
    try:
        print("Connecting to Telegram...")
        with TelegramClient(StringSession(SESSION_STRING), int(TELEGRAM_API_ID), TELEGRAM_API_HASH) as client:
            print("Fetching latest backup...")
            messages = client.get_messages(int(BACKUP_CHANNEL_ID), limit=1)
            if messages and messages[0].document:
                print("Downloading backup file...")
                client.download_media(messages[0], "backup_biberons.json")

                print("Loading backup data...")
                with open("backup_biberons.json", "r") as f:
                    data = json.load(f)

                with open(DATA_FILE, 'w') as file_out:
                    json.dump(data, file_out, indent=2)
                    
                print("✅ Backup loaded successfully")
                client.send_message(int(BACKUP_CHANNEL_ID), "✅ Backup chargé avec succès.")
            else:
                print("❌ Aucun document trouvé dans le canal.")

    except Exception as e:
        print(f"⚠️ Erreur pendant le chargement du backup : {e}")