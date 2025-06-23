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

        
def is_valid_time(time_str: str) -> bool:
    try:
        # Vérifie si l'heure est au format HH:MM
        if not (len(time_str) == 5 and time_str[2] == ':'):
            return False
        
        hours, minutes = map(int, time_str.split(':'))
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

