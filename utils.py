import json
import os
from dotenv import load_dotenv
from datetime import datetime, time, timedelta
from config import TEST_MODE
from zoneinfo import ZoneInfo
import threading
from database import (
    get_all_groups, create_group, set_user_message_info, get_user_message_info, clear_user_message_info, cleanup_old_data, update_group,
    get_user_group_id, get_group_data_for_user, get_group_stats_for_user, get_group_by_id
)

load_dotenv()

DATA_FILE = "biberons.json" 
MESSAGE_IDS_FILE = "message_ids.json"  # New file to store message IDs

# Global variable to track last cleanup
last_cleanup_date = None
cleanup_lock = threading.Lock()

# Only check for backup variables if we're not in test mode
if not TEST_MODE:
    print("Running in production mode with SQLite database")

def load_data():
    """Load all groups data directly from database"""
    return get_all_groups()

def load_user_data(user_id: int):
    """Load data for a specific user directly from database"""
    data = get_group_data_for_user(user_id)
    if data:
        # Format as expected by existing code
        return {str(data['id']): data}
    return {}

def load_user_stats(user_id: int, days: int = 5):
    """Load statistics data for a specific user directly from database"""
    return get_group_stats_for_user(user_id, days)

async def save_data(data, context):
    # With SQLite, data is saved immediately when operations are performed
    # This function is kept for compatibility but does nothing
    pass

def find_group_for_user(data, user_id):
    """Return the group_id for the group containing the user_id, or None."""
    # Try optimized database query first
    group_id = get_user_group_id(user_id)
    if group_id:
        return str(group_id)
    
    # Fallback to searching in loaded data
    for group_id, group_info in data.items():
        if user_id in group_info.get("users", []):
            return group_id
    
    return None

def create_personal_group(data, user_id : int):
    group_name = f"group_{user_id}"
    
    # First check if the group exists in the provided data
    for group_id, group_info in data.items():
        if group_info.get("name") == group_name:
            # Ensure users are integers
            int_users = []
            for user in group_info.get('users', []):
                try:
                    int_users.append(int(user))
                except (ValueError, TypeError):
                    continue
            
            if user_id not in int_users:
                group_info['users'].append(int(user_id))
                update_group(int(group_id), group_info)
            return group_id
    
    # If not found in data, check database efficiently
    group_id = get_user_group_id(user_id)
    if group_id:
        # Group exists, add user if not already in
        group_data = get_group_by_id(group_id)
        if group_data:
            group_users = group_data.get('users', [])
            if user_id not in group_users:
                group_data['users'].append(user_id)
                update_group(group_id, group_data)
        return str(group_id)
    
    # Sinon, crée le groupe
    new_group_id = create_group(group_name, user_id)
    if new_group_id:
        print(f"Created personal group {group_name} with ID {new_group_id}")
        return str(new_group_id)
    else:
        print(f"Failed to create personal group {group_name}")
        return None

def load_backup_from_channel():
    # No longer needed with SQLite
    pass

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
    except Exception:
        return time_str

def is_valid_time(time_str: str) -> bool:
    """Check if a time string is valid (HH:MM format)"""
    try:
        if len(time_str) != 5 or time_str[2] != ':':
            return False
        
        hours = int(time_str[:2])
        minutes = int(time_str[3:])
        
        return 0 <= hours <= 23 and 0 <= minutes <= 59
    except (ValueError, IndexError):
        return False

def getValidDate(time: str, difference: int) -> str:
    """Get a valid date string based on time and timezone difference"""
    from datetime import datetime, timedelta
    current_time = datetime.now(ZoneInfo('UTC'))
    adjusted_time = current_time + timedelta(hours=difference)
    return adjusted_time.strftime('%Y-%m-%d')

def should_run_cleanup():
    """Check if daily cleanup should run"""
    global last_cleanup_date
    current_date = datetime.now().date()
    
    if last_cleanup_date != current_date:
        return True
    return False

def run_daily_cleanup():
    """Run daily cleanup tasks"""
    with cleanup_lock:  # ← Verrou déplacé ici pour protéger toute l'opération
        if should_run_cleanup():
            global last_cleanup_date
            last_cleanup_date = datetime.now().date()
            cleanup_old_data()

def clean_data(data):
    """Clean data - no longer needed with SQLite"""
    pass

async def delete_user_message(context, chat_id, message_id):
    """Delete a user message"""
    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception as e:
        print(f"Failed to delete message: {e}")

async def update_main_message(context, message_text, keyboard, parse_mode="Markdown"):
    """Update the main message or create a new one if needed"""
    user_id = context.user_data.get('user_id')
    if not user_id:
        print("No user ID found")
        return False

    # For button interactions, use message ID from context
    message_id = context.user_data.get('main_message_id')
    chat_id = context.user_data.get('chat_id')
    
    # For text input or other cases, try stored message ID
    if not message_id or not chat_id:
        print("No message ID or chat ID found")
        data = load_data()
        group = find_group_for_user(data, user_id)
        message_info = get_group_message_info(data, group, user_id)
        if message_info:
            message_id = message_info.get('message_id')
            chat_id = message_info.get('chat_id')
    
    if message_id and chat_id:
        try:
            await context.bot.edit_message_text(
                text=message_text,
                chat_id=chat_id,
                message_id=message_id,
                reply_markup=keyboard,
                parse_mode=parse_mode
            )
            
            # SECURITY: Always re-save message info after successful update
            data = load_data()
            group = find_group_for_user(data, user_id)
            set_group_message_info(data, group, user_id, message_id, chat_id)
            print(f"🔒 Re-saved message info for user {user_id}: message_id={message_id}, chat_id={chat_id}")
            
            return True
        except Exception as e:
            error_msg = str(e)
            if "Message is not modified" in error_msg:
                # SECURITY: Still re-save message info even if content unchanged
                data = load_data()
                group = find_group_for_user(data, user_id)
                set_group_message_info(data, group, user_id, message_id, chat_id)
                print(f"🔒 Re-saved message info for user {user_id} (unchanged): message_id={message_id}, chat_id={chat_id}")
                return True
            elif "message to edit not found" in error_msg or "message to edit not found" in repr(e):
                print("Message principal supprimé, création d'un nouveau message.")
                # Créer un nouveau message principal
                sent_message = await context.bot.send_message(
                    chat_id=chat_id,
                    text=message_text,
                    reply_markup=keyboard,
                    parse_mode=parse_mode
                )
                data = load_data()
                group = find_group_for_user(data, user_id)
                set_group_message_info(data, group, user_id, sent_message.message_id, sent_message.chat_id)
                context.user_data['main_message_id'] = sent_message.message_id
                context.user_data['chat_id'] = sent_message.chat_id
                print(f"🔒 Saved new message info for user {user_id}: message_id={sent_message.message_id}, chat_id={sent_message.chat_id}")
                return True
            else:
                # Clear invalid message ID
                data = load_data()
                group = find_group_for_user(data, user_id)
                clear_group_message_info(data, group, user_id)
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
    
    # SECURITY: Always save message info after creating new message
    set_group_message_info(data, group, user_id, sent_message.message_id, sent_message.chat_id)
    context.user_data['main_message_id'] = sent_message.message_id
    context.user_data['chat_id'] = sent_message.chat_id
    
    print(f"🔒 Saved new message info for user {user_id}: message_id={sent_message.message_id}, chat_id={sent_message.chat_id}")

def get_group_message_info(data, group_id, user_id):
    """Get message ID and chat ID for a specific user in a group (by id)"""
    return get_user_message_info(group_id, user_id)

def set_group_message_info(data, group_id, user_id, message_id, chat_id):
    """Set message ID and chat ID for a specific user in a group (by id)"""
    set_user_message_info(group_id, user_id, message_id, chat_id)

def clear_group_message_info(data, group_id, user_id):
    """Clear message ID and chat ID for a specific user in a group (by id)"""
    clear_user_message_info(group_id, user_id)

async def safe_edit_message_text(update, context, text, reply_markup=None, parse_mode="Markdown"):
    """Safely edit message text, handling 'Message is not modified' error"""
    try:
        if hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.edit_message_text(
                text=text,
                reply_markup=reply_markup,
                parse_mode=parse_mode
            )
        else:
            # Fallback for other cases
            await context.bot.edit_message_text(
                text=text,
                chat_id=update.effective_chat.id,
                message_id=update.effective_message.message_id,
                reply_markup=reply_markup,
                parse_mode=parse_mode
            )
    except Exception as e:
        if "Message is not modified" in str(e):
            # Message content is identical, no need to modify
            print("ℹ️ Message content unchanged, skipping edit")
            return
        else:
            # Re-raise other errors
            raise e

async def safe_edit_message_text_with_query(query, text, reply_markup=None, parse_mode="Markdown"):
    """Safely edit message text using query, handling 'Message is not modified' error"""
    try:
        await query.edit_message_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode=parse_mode
        )
    except Exception as e:
        if "Message is not modified" in str(e):
            # Message content is identical, no need to modify
            print("ℹ️ Message content unchanged, skipping edit")
            return
        else:
            # Re-raise other errors
            raise e

async def update_all_group_messages(context, group_id: int, message_text: str, keyboard, caller_user_id: int = None, parse_mode="Markdown"):
    """Update all messages for all users in a group after data changes"""
    try:
        print(f"caller_user_id: {caller_user_id}")
        # Get all users in the group
        data = load_data()
        group_data = data.get(str(group_id))
        if not group_data:
            print(f"❌ No group data found for group {group_id}")
            return
        
        users = group_data.get('users', [])
        print(f"📊 Found {len(users)} users in group {group_id}")
        
        # Update messages for all users in the group
        for user_id in users:
            print(f"Updating message for user {user_id} in group {group_id}")
            # Skip the user who made the change
            if caller_user_id is not None and user_id == caller_user_id:
                print(f"⏭️ Skipping caller user {user_id}")
                continue
                
            # Get message info for this user
            message_info = get_group_message_info(data, str(group_id), user_id)
            if not message_info or len(message_info) < 2:
                print(f"No message info found for user {user_id} in group {group_id}")
                continue
                
            message_id, chat_id = message_info
            print(f"message_id: {message_id}, chat_id: {chat_id}")
            
            if message_id and chat_id:
                try:
                    print(f"Updating message for user {user_id} in group {group_id} step 2")
                    await context.bot.edit_message_text(
                        text=message_text,
                        chat_id=chat_id,
                        message_id=message_id,
                        reply_markup=keyboard,
                        parse_mode=parse_mode
                    )
                    print(f"✅ Updated message for user {user_id} in group {group_id}")
                    
                    # SECURITY: Re-save message info to ensure it's always up to date
                    # Even if the IDs haven't changed, this ensures the info is fresh
                    set_group_message_info(data, str(group_id), user_id, message_id, chat_id)
                    print(f"🔒 Re-saved message info for user {user_id}: message_id={message_id}, chat_id={chat_id}")
                    
                except Exception as e:
                    error_msg = str(e)
                    if "Message is not modified" in error_msg:
                        # Message content is identical, no need to modify
                        print(f"ℹ️ Message unchanged for user {user_id} in group {group_id}")
                        
                        # SECURITY: Still re-save message info even if content unchanged
                        set_group_message_info(data, str(group_id), user_id, message_id, chat_id)
                        print(f"🔒 Re-saved message info for user {user_id} (unchanged): message_id={message_id}, chat_id={chat_id}")
                        
                    elif "message to edit not found" in error_msg:
                        # Message was deleted, clear the stored info
                        print(f"⚠️ Message not found for user {user_id} in group {group_id}, clearing stored info")
                        clear_group_message_info(data, str(group_id), user_id)
                    elif "Unsupported parse_mode" in error_msg:
                        # Try without parse_mode
                        try:
                            await context.bot.edit_message_text(
                                text=message_text,
                                chat_id=chat_id,
                                message_id=message_id,
                                reply_markup=keyboard
                            )
                            print(f"✅ Updated message for user {user_id} in group {group_id} (without parse_mode)")
                            
                            # SECURITY: Re-save message info after successful update without parse_mode
                            set_group_message_info(data, str(group_id), user_id, message_id, chat_id)
                            print(f"🔒 Re-saved message info for user {user_id} (no parse_mode): message_id={message_id}, chat_id={chat_id}")
                            
                        except Exception as e2:
                            print(f"❌ Error updating message for user {user_id} in group {group_id} (without parse_mode): {e2}")
                    else:
                        print(f"❌ Error updating message for user {user_id} in group {group_id}: {e}")
            else:
                print(f"⚠️ Invalid message info for user {user_id}: message_id={message_id}, chat_id={chat_id}")
        
        print(f"💾 Updated all message info for group {group_id}")
        
    except Exception as e:
        print(f"❌ Error in update_all_group_messages: {e}")

