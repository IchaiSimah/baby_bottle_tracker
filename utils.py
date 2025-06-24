import json
import os
from dotenv import load_dotenv
from datetime import datetime, time, timedelta
from config import TEST_MODE
from zoneinfo import ZoneInfo
import threading
import time as time_module
from database import (
    get_all_groups, create_group, set_user_message_info, get_user_message_info, clear_user_message_info, cleanup_old_data, update_group,
    get_user_group_id, get_group_data_for_user, get_group_stats_for_user, get_group_by_id
)

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

# Performance optimization: Add caching
_cache = {}
_cache_lock = threading.Lock()
_cache_ttl = 300  # 5 minutes cache TTL
_last_cache_cleanup = time_module.time()

# Performance monitoring
_performance_stats = {
    'cache_hits': 0,
    'cache_misses': 0,
    'db_calls': 0,
    'response_times': []
}
_performance_lock = threading.Lock()

# Only check for backup variables if we're not in test mode
if not TEST_MODE and not all([TELEGRAM_API_ID, TELEGRAM_API_HASH, BACKUP_CHANNEL_ID]):
    missing = []
    if not TELEGRAM_API_ID: missing.append("TELEGRAM_API_ID")
    if not TELEGRAM_API_HASH: missing.append("TELEGRAM_API_HASH")
    if not BACKUP_CHANNEL_ID: missing.append("BACKUP_CHANNEL_ID")
    print(f"Warning: Missing backup environment variables: {', '.join(missing)}")

def _cleanup_cache():
    """Clean up expired cache entries"""
    global _last_cache_cleanup
    current_time = time_module.time()
    
    # Only cleanup every 60 seconds to avoid performance impact
    if current_time - _last_cache_cleanup < 60:
        return
    
    with _cache_lock:
        expired_keys = []
        for key, (value, timestamp) in _cache.items():
            if current_time - timestamp > _cache_ttl:
                expired_keys.append(key)
        
        for key in expired_keys:
            del _cache[key]
        
        _last_cache_cleanup = current_time

def _get_cache(key):
    """Get value from cache if not expired"""
    _cleanup_cache()
    with _cache_lock:
        if key in _cache:
            value, timestamp = _cache[key]
            if time_module.time() - timestamp < _cache_ttl:
                return value
            else:
                del _cache[key]
    return None

def _set_cache(key, value):
    """Set value in cache with current timestamp"""
    with _cache_lock:
        _cache[key] = (value, time_module.time())

def load_data():
    """Load data with caching to reduce database calls"""
    start_time = time_module.time()
    cache_key = "all_groups_data"
    cached_data = _get_cache(cache_key)
    
    if cached_data is not None:
        response_time = time_module.time() - start_time
        _record_performance(True, response_time)
        return cached_data
    
    _record_db_call()
    data = get_all_groups()
    _set_cache(cache_key, data)
    
    response_time = time_module.time() - start_time
    _record_performance(False, response_time)
    return data

def load_user_data(user_id: int):
    """Load data for a specific user - much more efficient than loading all data"""
    start_time = time_module.time()
    cache_key = f"user_data_{user_id}"
    cached_data = _get_cache(cache_key)
    
    if cached_data is not None:
        response_time = time_module.time() - start_time
        _record_performance(True, response_time)
        return cached_data
    
    _record_db_call()
    data = get_group_data_for_user(user_id)
    if data:
        # Format as expected by existing code
        formatted_data = {str(data['id']): data}
        _set_cache(cache_key, formatted_data)
        
        response_time = time_module.time() - start_time
        _record_performance(False, response_time)
        return formatted_data
    
    response_time = time_module.time() - start_time
    _record_performance(False, response_time)
    return {}

def load_user_stats(user_id: int, days: int = 5):
    """Load statistics data for a specific user - optimized for stats"""
    start_time = time_module.time()
    cache_key = f"user_stats_{user_id}_{days}"
    cached_data = _get_cache(cache_key)
    
    if cached_data is not None:
        response_time = time_module.time() - start_time
        _record_performance(True, response_time)
        return cached_data
    
    _record_db_call()
    data = get_group_stats_for_user(user_id, days)
    _set_cache(cache_key, data)
    
    response_time = time_module.time() - start_time
    _record_performance(False, response_time)
    return data

def invalidate_user_cache(user_id: int):
    """Invalidate cache for a specific user"""
    with _cache_lock:
        keys_to_remove = []
        for key in _cache.keys():
            if f"user_data_{user_id}" in key or f"user_stats_{user_id}" in key or f"user_group_{user_id}" in key:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del _cache[key]

def invalidate_cache():
    """Invalidate all cached data - call this when data changes"""
    with _cache_lock:
        _cache.clear()

async def save_data(data, context):
    # This is now a no-op, as all changes are instantly reflected in Supabase
    # But we need to invalidate cache when data changes
    invalidate_cache()
    pass

def find_group_for_user(data, user_id):
    """Return the group_id for the group containing the user_id, or None."""
    # Use cache for user-group mapping
    cache_key = f"user_group_{user_id}"
    cached_group = _get_cache(cache_key)
    
    if cached_group is not None:
        return cached_group
    
    # Try optimized database query first
    group_id = get_user_group_id(user_id)
    if group_id:
        _set_cache(cache_key, str(group_id))
        return str(group_id)
    
    # Fallback to searching in loaded data
    for group_id, group_info in data.items():
        if user_id in group_info.get("users", []):
            _set_cache(cache_key, group_id)
            return group_id
    
    _set_cache(cache_key, None)
    return None

def create_personal_group(data, user_id : int):
    group_name = f"group_{user_id}"
    
    # First check if the group exists in the provided data
    for group_id, group_info in data.items():
        if group_info['name'] == group_name:
            # Ajoute l'utilisateur s'il n'est pas déjà dedans
            group_users = group_info.get('users', [])
            # Convert all user IDs to integers for comparison
            int_users = []
            for user in group_users:
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
    create_group(group_name, user_id)
    # Get the created group ID efficiently
    return str(get_user_group_id(user_id))

def load_backup_from_channel():
    # No longer needed with Supabase
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

def run_daily_cleanup():
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
            error_msg = str(e)
            if "Message is not modified" in error_msg:
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
    set_group_message_info(data, group, user_id, sent_message.message_id, sent_message.chat_id)
    context.user_data['main_message_id'] = sent_message.message_id
    context.user_data['chat_id'] = sent_message.chat_id

def get_group_message_info(data, group_id, user_id):
    """Get message ID and chat ID for a specific user in a group (by id)"""
    return get_user_message_info(group_id, user_id)

def set_group_message_info(data, group_id, user_id, message_id, chat_id):
    """Set message ID and chat ID for a specific user in a group (by id)"""
    set_user_message_info(group_id, user_id, message_id, chat_id)

def clear_group_message_info(data, group_id, user_id):
    """Clear message ID and chat ID for a specific user in a group (by id)"""
    clear_user_message_info(group_id, user_id)

def get_performance_stats():
    """Get current performance statistics"""
    with _performance_lock:
        total_requests = _performance_stats['cache_hits'] + _performance_stats['cache_misses']
        cache_hit_rate = (_performance_stats['cache_hits'] / total_requests * 100) if total_requests > 0 else 0
        avg_response_time = sum(_performance_stats['response_times']) / len(_performance_stats['response_times']) if _performance_stats['response_times'] else 0
        
        return {
            'cache_hits': _performance_stats['cache_hits'],
            'cache_misses': _performance_stats['cache_misses'],
            'cache_hit_rate': f"{cache_hit_rate:.1f}%",
            'db_calls': _performance_stats['db_calls'],
            'avg_response_time': f"{avg_response_time:.3f}s",
            'total_requests': total_requests
        }

def _record_performance(cache_hit: bool, response_time: float):
    """Record performance metrics"""
    with _performance_lock:
        if cache_hit:
            _performance_stats['cache_hits'] += 1
        else:
            _performance_stats['cache_misses'] += 1
        
        _performance_stats['response_times'].append(response_time)
        
        # Keep only last 100 response times to avoid memory bloat
        if len(_performance_stats['response_times']) > 100:
            _performance_stats['response_times'] = _performance_stats['response_times'][-100:]

def _record_db_call():
    """Record a database call"""
    with _performance_lock:
        _performance_stats['db_calls'] += 1

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

