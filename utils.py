import json
import os
from dotenv import load_dotenv
from datetime import datetime, time, timedelta
from config import TEST_MODE
from zoneinfo import ZoneInfo
import threading
import time as time_module

load_dotenv()

DATA_FILE = "biberons.json"
MESSAGE_IDS_FILE = "message_ids.json"  # New file to store message IDs
BACKUP_CHANNEL_ID = os.getenv("BACKUP_CHANNEL_ID")
TELEGRAM_API_ID = os.getenv("TELEGRAM_API_ID")
TELEGRAM_API_HASH = os.getenv("TELEGRAM_API_HASH")
SESSION_STRING = os.getenv("STRING_SESSION")

# Global variable to track last cleanup
last_cleanup_date = None
cleanup_lock = threading.Lock()

# Only check for backup variables if we're not in test mode
if not TEST_MODE and not all([TELEGRAM_API_ID, TELEGRAM_API_HASH, BACKUP_CHANNEL_ID]):
    missing = []
    if not TELEGRAM_API_ID: missing.append("TELEGRAM_API_ID")
    if not TELEGRAM_API_HASH: missing.append("TELEGRAM_API_HASH")
    if not BACKUP_CHANNEL_ID: missing.append("BACKUP_CHANNEL_ID")
    print(f"Warning: Missing backup environment variables: {', '.join(missing)}")

def load_data():
    try:
        with open(DATA_FILE, 'r') as file:
            data = json.load(file)
            # Nettoyer les données pour s'assurer que time_difference est un nombre
            return clean_data(data)
    except FileNotFoundError:
        return {}

async def save_data(data, context):
    # Run daily cleanup if needed
    run_daily_cleanup()
    
    for group in data:
        group_data = data[group]
        entries = group_data.get("entries", [])
        poop = group_data.get("poop", [])
        
        # Get current date
        today = datetime.now().date()
        
        # Filter entries to keep only last 5 days
        if isinstance(entries, list):
            filtered_entries = []
            for entry in entries:
                try:
                    # Extract date from entry time (format: "dd-mm-yyyy HH:MM")
                    entry_date_str = entry["time"].split(" ")[0]
                    entry_date = datetime.strptime(entry_date_str, "%d-%m-%Y").date()
                    
                    # Keep only entries from last 5 days
                    if (today - entry_date).days <= 5:
                        filtered_entries.append(entry)
                except (ValueError, IndexError, KeyError):
                    # If date parsing fails, keep the entry (fallback)
                    filtered_entries.append(entry)
            
            group_data["entries"] = filtered_entries
        
        # Filter poop to keep only last 5 days
        if isinstance(poop, list):
            filtered_poop = []
            for poop_entry in poop:
                try:
                    # Extract date from poop time (format: "dd-mm-yyyy HH:MM")
                    poop_date_str = poop_entry["time"].split(" ")[0]
                    poop_date = datetime.strptime(poop_date_str, "%d-%m-%Y").date()
                    
                    # Keep only poop from last 5 days
                    if (today - poop_date).days <= 5:
                        filtered_poop.append(poop_entry)
                except (ValueError, IndexError, KeyError):
                    # If date parsing fails, keep the entry (fallback)
                    filtered_poop.append(poop_entry)
            
            group_data["poop"] = filtered_poop
            
    with open(DATA_FILE, 'w') as file:
        json.dump(data, file, indent=2)
    if TEST_MODE:
        return
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
    data[group_name] = {"users": [user_id], "entries": [], "time_difference": 0}
    return group_name

def load_backup_from_channel():
    try:
        # Import Telethon only when needed
        from telethon.sync import TelegramClient
        from telethon.sessions import StringSession
        
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
            else:
                print("❌ Aucun document trouvé dans le canal.")

    except Exception as e:
        print(f"⚠️ Erreur pendant le chargement du backup : {e}")

        
def normalize_time(time_str: str) -> str:
    """Normalize time input to HH:MM format"""
    try:
        # Remove any extra spaces
        time_str = time_str.strip()
        
        # Check if it's already in HH:MM format
        if len(time_str) == 5 and time_str[2] == ':':
            return time_str
        
        # Check if it's in H:MM format (4 characters with colon in position 1)
        if len(time_str) == 4 and time_str[1] == ':':
            hours = time_str[0]
            minutes = time_str[2:4]
            return f"0{hours}:{minutes}"
        
        # If it doesn't match any expected format, return as is (will be validated later)
        return time_str
    except (ValueError, IndexError):
        return time_str

def is_valid_time(time_str: str) -> bool:
    try:
        # Normalize the time string first
        normalized_time = normalize_time(time_str)
        
        # Vérifie si l'heure est au format HH:MM
        if not (len(normalized_time) == 5 and normalized_time[2] == ':'):
            return False
        
        hours, minutes = map(int, normalized_time.split(':'))
        # Vérifie si les heures et minutes sont dans les limites valides
        return 0 <= hours <= 23 and 0 <= minutes <= 59
    except (ValueError, IndexError):
        return False
    
def getValidDate(time: str, difference: int) -> str:
    date = (datetime.now(ZoneInfo("UTC")) + timedelta(hours=difference)).date()
    timeToCompare = datetime.strptime(time, "%H:%M").time()
    actualTime = (datetime.now(ZoneInfo("UTC")) + timedelta(hours=difference)).time()
    if actualTime < timeToCompare:
        return (date - timedelta(days=1)).strftime("%d-%m-%Y")
    else:
        return date.strftime("%d-%m-%Y")

def should_run_cleanup():
    """Check if cleanup should run (once per day)"""
    global last_cleanup_date
    today = datetime.now().date()
    
    with cleanup_lock:
        if last_cleanup_date != today:
            last_cleanup_date = today
            return True
    return False

def cleanup_old_data():
    """Clean up data older than 5 days from existing data file"""
    try:
        data = load_data()
        today = datetime.now().date()
        cleaned_groups = 0
        total_entries_removed = 0
        total_poop_removed = 0
        
        for group in data:
            group_data = data[group]
            entries = group_data.get("entries", [])
            poop = group_data.get("poop", [])
            
            original_entries_count = len(entries)
            original_poop_count = len(poop)
            
            # Filter entries to keep only last 5 days
            if isinstance(entries, list):
                filtered_entries = []
                for entry in entries:
                    try:
                        entry_date_str = entry["time"].split(" ")[0]
                        entry_date = datetime.strptime(entry_date_str, "%d-%m-%Y").date()
                        
                        if (today - entry_date).days <= 5:
                            filtered_entries.append(entry)
                    except (ValueError, IndexError, KeyError):
                        filtered_entries.append(entry)
                
                group_data["entries"] = filtered_entries
                entries_removed = original_entries_count - len(filtered_entries)
                total_entries_removed += entries_removed
            
            # Filter poop to keep only last 5 days
            if isinstance(poop, list):
                filtered_poop = []
                for poop_entry in poop:
                    try:
                        poop_date_str = poop_entry["time"].split(" ")[0]
                        poop_date = datetime.strptime(poop_date_str, "%d-%m-%Y").date()
                        
                        if (today - poop_date).days <= 5:
                            filtered_poop.append(poop_entry)
                    except (ValueError, IndexError, KeyError):
                        filtered_poop.append(poop_entry)
                
                group_data["poop"] = filtered_poop
                poop_removed = original_poop_count - len(filtered_poop)
                total_poop_removed += poop_removed
            
            cleaned_groups += 1
        
        # Save cleaned data
        with open(DATA_FILE, 'w') as file:
            json.dump(data, file, indent=2)
        
        if total_entries_removed > 0 or total_poop_removed > 0:
            print(f"🧹 Nettoyage quotidien terminé:")
            print(f"   • Groupes traités: {cleaned_groups}")
            print(f"   • Biberons supprimés: {total_entries_removed}")
            print(f"   • Cacas supprimés: {total_poop_removed}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du nettoyage: {e}")
        return False

def run_daily_cleanup():
    """Run cleanup if it's a new day"""
    if should_run_cleanup():
        cleanup_old_data()

def clean_data(data):
    """Nettoie les données pour s'assurer que time_difference est toujours un nombre"""
    for group_name, group_data in data.items():
        if isinstance(group_data, dict) and "time_difference" in group_data:
            # Si time_difference n'est pas un nombre, le convertir en 0
            if not isinstance(group_data["time_difference"], (int, float)):
                group_data["time_difference"] = 0
    return data

async def delete_user_message(context, chat_id, message_id):
    """Safely delete a user message"""
    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
        return True
    except Exception as e:
        print(f"Failed to delete user message: {e}")
        return False

async def update_main_message(context, message_text, keyboard, parse_mode="Markdown"):
    """Update the main message or create a new one if needed"""
    user_id = context.user_data.get('user_id')
    if not user_id:
        return False
    
    # For button interactions, use message ID from context
    message_id = context.user_data.get('main_message_id')
    chat_id = context.user_data.get('chat_id')
    
    # For text input or other cases, try stored message ID
    if not message_id or not chat_id:
        data = load_data()
        group = find_group_for_user(data, user_id)
        message_id, chat_id = get_group_message_info(data, group, user_id)
    
    if message_id and chat_id:
        try:
            await context.bot.edit_message_text(
                text=message_text,
                chat_id=chat_id,
                message_id=message_id,
                reply_markup=keyboard,
                parse_mode=parse_mode
            )
            return True
        except Exception as e:
            print(f"Failed to edit main message: {e}")
            # Clear invalid message ID
            data = load_data()
            group = find_group_for_user(data, user_id)
            clear_group_message_info(data, group, user_id)
            await save_data(data, context)
            context.user_data.pop('main_message_id', None)
            context.user_data.pop('chat_id', None)
    
    return False

async def ensure_main_message_exists(update, context, data, group):
    """Ensure the main message exists and is properly tracked"""
    from handlers.queries import get_main_message_content
    user_id = update.effective_user.id
    context.user_data['user_id'] = user_id  # Store user_id for utility functions
    message_text, keyboard = get_main_message_content(data, group)
    # Try to update existing message first
    if await update_main_message(context, message_text, keyboard):
        return
    # If no existing message or update failed, create new one
    if hasattr(update, 'callback_query') and update.callback_query:
        sent_message = await update.callback_query.edit_message_text(
            text=message_text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    elif hasattr(update, 'message') and update.message:
        sent_message = await update.message.reply_text(
            text=message_text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    else:
        return
    set_group_message_info(data, group, user_id, sent_message.message_id, sent_message.chat_id)
    await save_data(data, context)
    context.user_data['main_message_id'] = sent_message.message_id
    context.user_data['chat_id'] = sent_message.chat_id

def get_group_message_info(data, group, user_id):
    """Get message ID and chat ID for a specific user in a group"""
    group_data = data.get(group, {})
    user_messages = group_data.get('user_messages', {})
    user_data = user_messages.get(str(user_id), {})
    return user_data.get('main_message_id'), user_data.get('main_chat_id')

def set_group_message_info(data, group, user_id, message_id, chat_id):
    """Set message ID and chat ID for a specific user in a group"""
    if group in data:
        if 'user_messages' not in data[group]:
            data[group]['user_messages'] = {}
        data[group]['user_messages'][str(user_id)] = {
            'main_message_id': message_id,
            'main_chat_id': chat_id
        }

def clear_group_message_info(data, group, user_id):
    """Clear message ID and chat ID for a specific user in a group"""
    if group in data and 'user_messages' in data[group]:
        data[group]['user_messages'].pop(str(user_id), None)

