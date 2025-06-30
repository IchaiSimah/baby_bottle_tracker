import os
import json
import sqlite3
import shutil
from datetime import datetime, date
from typing import Dict, List, Optional, Any
from config import DATABASE_PATH, GROUPS_TABLE, ENTRIES_TABLE, POOP_TABLE, USER_MESSAGES_TABLE
from dateutil import parser as date_parser
import threading
from zoneinfo import ZoneInfo

# Thread-local storage for database connections
_local = threading.local()

def get_db_connection():
    """Get a database connection for the current thread"""
    if not hasattr(_local, 'connection'):
        # Ensure data directory exists
        os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
        _local.connection = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        _local.connection.row_factory = sqlite3.Row  # Enable dict-like access
    return _local.connection

def close_db_connection():
    """Close the database connection for the current thread"""
    if hasattr(_local, 'connection'):
        _local.connection.close()
        delattr(_local, 'connection')

# Helper to parse timestamp from SQLite
def parse_time(ts):
    if ts is None:
        return None
    if isinstance(ts, datetime):
        # Si c'est déjà un datetime, s'assurer qu'il a une timezone
        if ts.tzinfo is None:
            # Si pas de timezone, supposer UTC
            return ts.replace(tzinfo=ZoneInfo('UTC'))
        else:
            # Si a une timezone, convertir à UTC
            return ts.astimezone(ZoneInfo('UTC'))
    try:
        parsed_time = date_parser.parse(ts)
        # S'assurer que le datetime parsé a une timezone
        if parsed_time.tzinfo is None:
            # Si pas de timezone, supposer UTC
            return parsed_time.replace(tzinfo=ZoneInfo('UTC'))
        else:
            # Si a une timezone, convertir à UTC
            return parsed_time.astimezone(ZoneInfo('UTC'))
    except Exception:
        return None

# Performance optimization: Add targeted query functions
def get_user_group_id(user_id: int) -> Optional[int]:
    """Get group ID for a specific user - robust version (no JSON1 dependency)"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        # 1. Chercher d'abord un groupe partagé
        cursor.execute(f"SELECT id, users, name FROM {GROUPS_TABLE} WHERE name NOT LIKE 'group_%' ORDER BY id ASC")
        for row in cursor.fetchall():
            try:
                users = row['users']
                if users:
                    users_list = json.loads(users)
                    if int(user_id) in users_list:
                        return row['id']
            except Exception as e:
                continue
        # 2. Sinon, chercher un groupe perso
        cursor.execute(f"SELECT id, users, name FROM {GROUPS_TABLE} WHERE name LIKE 'group_%' ORDER BY id ASC")
        for row in cursor.fetchall():
            try:
                users = row['users']
                if users:
                    users_list = json.loads(users)
                    if int(user_id) in users_list:
                        return row['id']
            except Exception as e:
                continue
        return None
    except Exception as e:
        print(f"Error getting group for user {user_id}: {e}")
        return None

def get_group_data_for_user(user_id: int) -> Optional[Dict]:
    """Get only the data needed for a specific user's group"""
    try:
        group_id = get_user_group_id(user_id)
        if not group_id:
            return None
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get group basic info
        cursor.execute(f"""
            SELECT * FROM {GROUPS_TABLE} WHERE id = ?
        """, (group_id,))
        group_row = cursor.fetchone()
        
        if not group_row:
            return None
        
        # Get only recent entries (last 10) instead of all
        cursor.execute(f"""
            SELECT * FROM {ENTRIES_TABLE} 
            WHERE group_id = ? 
            ORDER BY time DESC 
            LIMIT 10
        """, (group_id,))
        entries_data = cursor.fetchall()
        
        # Get only recent poop (last 5) instead of all
        cursor.execute(f"""
            SELECT * FROM {POOP_TABLE} 
            WHERE group_id = ? 
            ORDER BY time DESC 
            LIMIT 5
        """, (group_id,))
        poop_data = cursor.fetchall()
        
        # Get user message info
        cursor.execute(f"""
            SELECT * FROM {USER_MESSAGES_TABLE} 
            WHERE group_id = ? AND user_id = ?
        """, (group_id, user_id))
        messages_data = cursor.fetchall()
        
        # Format entries
        entries = []
        for entry in entries_data:
            entries.append({
                'amount': entry['amount'],
                'time': parse_time(entry['time'])
            })
        
        # Format poop
        poop = []
        for poop_entry in poop_data:
            poop.append({
                'time': parse_time(poop_entry['time']),
                'info': poop_entry['info']
            })
        
        # Format user messages
        user_messages = {}
        for msg in messages_data:
            user_messages[str(msg['user_id'])] = {
                'main_message_id': msg['main_message_id'],
                'main_chat_id': msg['main_chat_id']
            }
        
        # Parse users JSON
        users = []
        if group_row['users']:
            try:
                users = json.loads(group_row['users'])
            except:
                users = []
        
        return {
            'id': group_id,
            'name': group_row['name'],
            'users': users,
            'entries': entries,
            'poop': poop,
            'time_difference': group_row['time_difference'] or 0,
            'last_bottle': group_row['last_bottle'] or 0,
            'bottles_to_show': group_row['bottles_to_show'] or 5,
            'poops_to_show': group_row['poops_to_show'] or 1,
            'user_messages': user_messages
        }
    except Exception as e:
        print(f"Error getting group data for user {user_id}: {e}")
        return None

def get_group_stats_for_user(user_id: int, days: int = 5) -> Optional[Dict]:
    """Get statistics data for a specific user - optimized for stats display"""
    try:
        group_id = get_user_group_id(user_id)
        if not group_id:
            return None
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get entries for the last N days only
        from datetime import timedelta
        cutoff_date = (datetime.now(ZoneInfo('UTC')) - timedelta(days=days)).isoformat()
        
        cursor.execute(f"""
            SELECT * FROM {ENTRIES_TABLE} 
            WHERE group_id = ? AND time >= ?
            ORDER BY time DESC
        """, (group_id, cutoff_date))
        entries_data = cursor.fetchall()
        
        cursor.execute(f"""
            SELECT * FROM {POOP_TABLE} 
            WHERE group_id = ? AND time >= ?
            ORDER BY time DESC
        """, (group_id, cutoff_date))
        poop_data = cursor.fetchall()
        
        # Format entries
        entries = []
        for entry in entries_data:
            entries.append({
                'amount': entry['amount'],
                'time': parse_time(entry['time'])
            })
        
        # Format poop
        poop = []
        for poop_entry in poop_data:
            poop.append({
                'time': parse_time(poop_entry['time']),
                'info': poop_entry['info']
            })
        
        return {
            'entries': entries,
            'poop': poop
        }
    except Exception as e:
        print(f"Error getting group stats for user {user_id}: {e}")
        return None

def get_all_groups() -> Dict[str, Dict]:
    """Get all groups with their data - for compatibility with existing code"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get all groups
        cursor.execute(f"SELECT * FROM {GROUPS_TABLE}")
        groups_data = cursor.fetchall()
        
        result = {}
        for group_row in groups_data:
            group_id = str(group_row['id'])
            
            # Get entries for this group
            cursor.execute(f"""
                SELECT * FROM {ENTRIES_TABLE} 
                WHERE group_id = ? 
                ORDER BY time DESC
            """, (group_row['id'],))
            entries_data = cursor.fetchall()
            
            # Get poop for this group
            cursor.execute(f"""
                SELECT * FROM {POOP_TABLE} 
                WHERE group_id = ? 
                ORDER BY time DESC
            """, (group_row['id'],))
            poop_data = cursor.fetchall()
            
            # Get user messages for this group
            cursor.execute(f"""
                SELECT * FROM {USER_MESSAGES_TABLE} 
                WHERE group_id = ?
            """, (group_row['id'],))
            messages_data = cursor.fetchall()
            
            # Format entries
            entries = []
            for entry in entries_data:
                entries.append({
                    'amount': entry['amount'],
                    'time': parse_time(entry['time'])
                })
            
            # Format poop
            poop = []
            for poop_entry in poop_data:
                poop.append({
                    'time': parse_time(poop_entry['time']),
                    'info': poop_entry['info']
                })
            
            # Format user messages
            user_messages = {}
            for msg in messages_data:
                user_messages[str(msg['user_id'])] = {
                    'main_message_id': msg['main_message_id'],
                    'main_chat_id': msg['main_chat_id']
                }
            
            # Parse users JSON
            users = []
            if group_row['users']:
                try:
                    users = json.loads(group_row['users'])
                except:
                    users = []
            
            result[group_id] = {
                'id': group_row['id'],
                'name': group_row['name'],
                'users': users,
                'entries': entries,
                'poop': poop,
                'time_difference': group_row['time_difference'] or 0,
                'last_bottle': group_row['last_bottle'] or 0,
                'bottles_to_show': group_row['bottles_to_show'] or 5,
                'poops_to_show': group_row['poops_to_show'] or 1,
                'user_messages': user_messages
            }
        
        return result
    except Exception as e:
        print(f"Error getting all groups: {e}")
        return {}

def get_group_by_id(group_id: int) -> Optional[Dict]:
    """Get a specific group by ID"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(f"SELECT * FROM {GROUPS_TABLE} WHERE id = ?", (group_id,))
        group_row = cursor.fetchone()
        
        if not group_row:
            return None
        
        # Get entries for this group
        cursor.execute(f"""
            SELECT * FROM {ENTRIES_TABLE} 
            WHERE group_id = ? 
            ORDER BY time DESC
        """, (group_id,))
        entries_data = cursor.fetchall()
        
        # Get poop for this group
        cursor.execute(f"""
            SELECT * FROM {POOP_TABLE} 
            WHERE group_id = ? 
            ORDER BY time DESC
        """, (group_id,))
        poop_data = cursor.fetchall()
        
        # Get user messages for this group
        cursor.execute(f"""
            SELECT * FROM {USER_MESSAGES_TABLE} 
            WHERE group_id = ?
        """, (group_id,))
        messages_data = cursor.fetchall()
        
        # Format entries
        entries = []
        for entry in entries_data:
            entries.append({
                'amount': entry['amount'],
                'time': parse_time(entry['time'])
            })
        
        # Format poop
        poop = []
        for poop_entry in poop_data:
            poop.append({
                'time': parse_time(poop_entry['time']),
                'info': poop_entry['info']
            })
        
        # Format user messages
        user_messages = {}
        for msg in messages_data:
            user_messages[str(msg['user_id'])] = {
                'main_message_id': msg['main_message_id'],
                'main_chat_id': msg['main_chat_id']
            }
        
        # Parse users JSON
        users = []
        if group_row['users']:
            try:
                users = json.loads(group_row['users'])
            except:
                users = []
        
        return {
            'id': group_row['id'],
            'name': group_row['name'],
            'users': users,
            'entries': entries,
            'poop': poop,
            'time_difference': group_row['time_difference'] or 0,
            'last_bottle': group_row['last_bottle'] or 0,
            'bottles_to_show': group_row['bottles_to_show'] or 5,
            'poops_to_show': group_row['poops_to_show'] or 1,
            'user_messages': user_messages
        }
    except Exception as e:
        print(f"Error getting group by ID {group_id}: {e}")
        return None

def get_group_by_name(group_name: str) -> Optional[Dict]:
    """Get a specific group by name"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(f"SELECT id FROM {GROUPS_TABLE} WHERE name = ?", (group_name,))
        group_row = cursor.fetchone()
        
        if group_row:
            return get_group_by_id(group_row['id'])
        return None
    except Exception as e:
        print(f"Error getting group by name {group_name}: {e}")
        return None

def create_group(group_name: str, user_id: int) -> Optional[int]:
    """Create a new group and return the group ID"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if group already exists
        cursor.execute(f"SELECT id FROM {GROUPS_TABLE} WHERE name = ?", (group_name,))
        if cursor.fetchone():
            return None
        
        # Create new group
        users_json = json.dumps([user_id])
        cursor.execute(f"""
            INSERT INTO {GROUPS_TABLE} (name, users, time_difference, last_bottle, bottles_to_show, poops_to_show)
            VALUES (?, ?, 3, 0, 5, 1)
        """, (group_name, users_json))
        
        # Get the created group ID
        group_id = cursor.lastrowid
        
        conn.commit()
        print(f"Created group {group_name} with ID {group_id}")
        return group_id
    except Exception as e:
        print(f"Error creating group {group_name}: {e}")
        return None

def update_group(group_id: int, group_data: Dict) -> bool:
    """Update group data"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Update group basic info
        cursor.execute(f"""
            UPDATE {GROUPS_TABLE} 
            SET name = ?, users = ?, time_difference = ?, last_bottle = ?, 
                bottles_to_show = ?, poops_to_show = ?
            WHERE id = ?
        """, (
            group_data.get('name', ''),
            json.dumps(group_data.get('users', [])),
            group_data.get('time_difference', 3),
            group_data.get('last_bottle', 0),
            group_data.get('bottles_to_show', 5),
            group_data.get('poops_to_show', 1),
            group_id
        ))
        
        # Update entries
        cursor.execute(f"DELETE FROM {ENTRIES_TABLE} WHERE group_id = ?", (group_id,))
        for entry in group_data.get('entries', []):
            cursor.execute(f"""
                INSERT INTO {ENTRIES_TABLE} (group_id, amount, time)
                VALUES (?, ?, ?)
            """, (group_id, entry['amount'], entry['time'].isoformat()))
        
        # Update poop
        cursor.execute(f"DELETE FROM {POOP_TABLE} WHERE group_id = ?", (group_id,))
        for poop_entry in group_data.get('poop', []):
            cursor.execute(f"""
                INSERT INTO {POOP_TABLE} (group_id, time, info)
                VALUES (?, ?, ?)
            """, (group_id, poop_entry['time'].isoformat(), poop_entry.get('info')))
        
        # Update user messages
        cursor.execute(f"DELETE FROM {USER_MESSAGES_TABLE} WHERE group_id = ?", (group_id,))
        for user_id_str, msg_info in group_data.get('user_messages', {}).items():
            cursor.execute(f"""
                INSERT INTO {USER_MESSAGES_TABLE} (group_id, user_id, main_message_id, main_chat_id)
                VALUES (?, ?, ?, ?)
            """, (group_id, int(user_id_str), msg_info.get('main_message_id'), msg_info.get('main_chat_id')))
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Error updating group {group_id}: {e}")
        return False

def add_entry_to_group(group_id: int, amount: int, time: datetime) -> bool:
    """Add a bottle entry to a group"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(f"""
            INSERT INTO {ENTRIES_TABLE} (group_id, amount, time)
            VALUES (?, ?, ?)
        """, (group_id, amount, time.isoformat()))
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Error adding entry to group {group_id}: {e}")
        return False

def remove_last_entry_from_group(group_id: int) -> bool:
    """Remove the last bottle entry from a group"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get the last entry
        cursor.execute(f"""
            SELECT id FROM {ENTRIES_TABLE} 
            WHERE group_id = ? 
            ORDER BY time DESC 
            LIMIT 1
        """, (group_id,))
        
        last_entry = cursor.fetchone()
        if not last_entry:
            return False
        
        # Delete the last entry
        cursor.execute(f"DELETE FROM {ENTRIES_TABLE} WHERE id = ?", (last_entry['id'],))
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Error removing last entry from group {group_id}: {e}")
        return False

def add_poop_to_group(group_id: int, time: datetime, info: Optional[str] = None) -> bool:
    """Add a poop entry to a group"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(f"""
            INSERT INTO {POOP_TABLE} (group_id, time, info)
            VALUES (?, ?, ?)
        """, (group_id, time.isoformat(), info))
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Error adding poop to group {group_id}: {e}")
        return False

def set_user_message_info(group_id: int, user_id: int, message_id: int, chat_id: int) -> bool:
    """Set user message information"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if record exists
        cursor.execute(f"""
            SELECT id FROM {USER_MESSAGES_TABLE} 
            WHERE group_id = ? AND user_id = ?
        """, (group_id, user_id))
        
        existing = cursor.fetchone()
        if existing:
            # Update existing record
            cursor.execute(f"""
                UPDATE {USER_MESSAGES_TABLE} 
                SET main_message_id = ?, main_chat_id = ?
                WHERE group_id = ? AND user_id = ?
            """, (message_id, chat_id, group_id, user_id))
        else:
            # Insert new record
            cursor.execute(f"""
                INSERT INTO {USER_MESSAGES_TABLE} (group_id, user_id, main_message_id, main_chat_id)
                VALUES (?, ?, ?, ?)
            """, (group_id, user_id, message_id, chat_id))
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Error setting user message info: {e}")
        return False

def get_user_message_info(group_id: int, user_id: int) -> tuple:
    """Get user message information"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(f"""
            SELECT main_message_id, main_chat_id FROM {USER_MESSAGES_TABLE} 
            WHERE group_id = ? AND user_id = ?
        """, (group_id, user_id))
        
        result = cursor.fetchone()
        if result:
            return (result['main_message_id'], result['main_chat_id'])
        print(f"No message info found for user {user_id} in group {group_id}")
        return (None, None)
    except Exception as e:
        print(f"Error getting user message info: {e}")
        return (None, None)

def clear_user_message_info(group_id: int, user_id: int) -> bool:
    """Clear user message information"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(f"""
            DELETE FROM {USER_MESSAGES_TABLE} 
            WHERE group_id = ? AND user_id = ?
        """, (group_id, user_id))
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Error clearing user message info: {e}")
        return False

def create_database_backup() -> bool:
    """Create a backup of the database before cleanup"""
    try:
        if not os.path.exists(DATABASE_PATH):
            print("Database file not found, skipping backup")
            return False
        
        # Create backup directory if it doesn't exist
        backup_dir = os.path.join(os.path.dirname(DATABASE_PATH), "backups")
        os.makedirs(backup_dir, exist_ok=True)
        
        # Generate backup filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"baby_bottle_tracker_backup_{timestamp}.db"
        backup_path = os.path.join(backup_dir, backup_filename)
        
        # Copy database file
        shutil.copy2(DATABASE_PATH, backup_path)
        
        # Keep only the last 7 backups to avoid disk space issues
        backup_files = [f for f in os.listdir(backup_dir) if f.startswith("baby_bottle_tracker_backup_") and f.endswith(".db")]
        backup_files.sort(reverse=True)  # Sort by name (timestamp) descending
        
        if len(backup_files) > 7:
            for old_backup in backup_files[7:]:
                old_backup_path = os.path.join(backup_dir, old_backup)
                try:
                    os.remove(old_backup_path)
                    print(f"Removed old backup: {old_backup}")
                except Exception as e:
                    print(f"Failed to remove old backup {old_backup}: {e}")
        
        print(f"Database backup created: {backup_path}")
        return True
    except Exception as e:
        print(f"Error creating database backup: {e}")
        return False

def cleanup_old_data() -> bool:
    """Clean up old data (entries older than 32 days) and create backup"""
    try:
        # Create backup before cleanup
        backup_success = create_database_backup()
        if not backup_success:
            print("Warning: Backup failed, but continuing with cleanup")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        from datetime import timedelta
        cutoff_date = (datetime.now(ZoneInfo('UTC')) - timedelta(days=32)).isoformat()
        
        # Delete old entries
        cursor.execute(f"DELETE FROM {ENTRIES_TABLE} WHERE time < ?", (cutoff_date,))
        entries_deleted = cursor.rowcount
        
        # Delete old poop entries
        cursor.execute(f"DELETE FROM {POOP_TABLE} WHERE time < ?", (cutoff_date,))
        poop_deleted = cursor.rowcount
        
        conn.commit()
        
        if entries_deleted > 0 or poop_deleted > 0:
            print(f"Cleaned up {entries_deleted} old entries and {poop_deleted} old poop entries")
        
        return True
    except Exception as e:
        print(f"Error cleaning up old data: {e}")
        return False

def update_group_name(group_id: int, new_name: str) -> bool:
    """Update group name"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(f"UPDATE {GROUPS_TABLE} SET name = ? WHERE id = ?", (new_name, group_id))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error updating group name: {e}")
        return False

def cleanup_user_ids():
    """Clean up user IDs in groups - remove invalid entries"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get all groups
        cursor.execute(f"SELECT id, users FROM {GROUPS_TABLE}")
        groups = cursor.fetchall()
        
        for group in groups:
            if group['users']:
                try:
                    users = json.loads(group['users'])
                    # Filter out invalid user IDs (keep only integers)
                    valid_users = [uid for uid in users if isinstance(uid, int)]
                    
                    if len(valid_users) != len(users):
                        # Update with cleaned user list
                        cursor.execute(f"UPDATE {GROUPS_TABLE} SET users = ? WHERE id = ?", 
                                     (json.dumps(valid_users), group['id']))
                        print(f"Cleaned user IDs for group {group['id']}: removed {len(users) - len(valid_users)} invalid entries")
                except Exception as e:
                    print(f"Error cleaning user IDs for group {group['id']}: {e}")
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Error in cleanup_user_ids: {e}")
        return False 