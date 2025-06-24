import os
from datetime import datetime, date
from typing import Dict, List, Optional, Any
from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY, GROUPS_TABLE, ENTRIES_TABLE, POOP_TABLE, USER_MESSAGES_TABLE
from dateutil import parser as date_parser

# Initialize Supabase client
supabase: Client = None

def get_supabase_client() -> Client:
    """Get or create Supabase client"""
    global supabase
    if supabase is None:
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables")
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    return supabase

# Helper to parse timestamp from Supabase
def parse_time(ts):
    if ts is None:
        return None
    if isinstance(ts, datetime):
        return ts
    try:
        return date_parser.parse(ts)
    except Exception:
        return None

def _invalidate_cache():
    """Invalidate cache - imported here to avoid circular imports"""
    try:
        from utils import invalidate_cache
        invalidate_cache()
    except ImportError:
        pass  # utils module not available during import

def _invalidate_user_cache(user_id: int):
    """Invalidate user cache - imported here to avoid circular imports"""
    try:
        from utils import invalidate_user_cache
        invalidate_user_cache(user_id)
    except ImportError:
        pass  # utils module not available during import

# Performance optimization: Add targeted query functions
def get_user_group_id(user_id: int) -> Optional[int]:
    """Get group ID for a specific user - much faster than loading all groups"""
    try:
        client = get_supabase_client()
        # Users are stored as integers in the database
        print(f"test1: {user_id}")
        response = client.table(GROUPS_TABLE).select("id").contains("users", [str(user_id)]).execute()
        print(f"test2: {response.data}")
        if response.data:
            return response.data[0]['id']
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
        
        client = get_supabase_client()
        
        # Get group basic info
        group_response = client.table(GROUPS_TABLE).select("*").eq('id', group_id).execute()
        if not group_response.data:
            return None
        
        group_row = group_response.data[0]
        
        # Get only recent entries (last 10) instead of all
        entries_response = client.table(ENTRIES_TABLE).select("*").eq('group_id', group_id).order('time', desc=True).limit(10).execute()
        
        # Get only recent poop (last 5) instead of all
        poop_response = client.table(POOP_TABLE).select("*").eq('group_id', group_id).order('time', desc=True).limit(5).execute()
        
        # Get user message info
        messages_response = client.table(USER_MESSAGES_TABLE).select("*").eq('group_id', group_id).eq('user_id', user_id).execute()
        
        # Format entries
        entries = []
        for entry in entries_response.data:
            entries.append({
                'amount': entry['amount'],
                'time': parse_time(entry['time'])
            })
        
        # Format poop
        poop = []
        for poop_entry in poop_response.data:
            poop.append({
                'time': parse_time(poop_entry['time']),
                'info': poop_entry.get('info')
            })
        
        # Format user messages
        user_messages = {}
        for msg in messages_response.data:
            user_messages[str(msg['user_id'])] = {
                'main_message_id': msg['main_message_id'],
                'main_chat_id': msg['main_chat_id']
            }
        
        return {
            'id': group_id,
            'name': group_row['name'],
            'users': group_row.get('users', []),
            'entries': entries,
            'poop': poop,
            'time_difference': group_row.get('time_difference', 0) or 0,
            'last_bottle': group_row.get('last_bottle', 0) or 0,
            'bottles_to_show': group_row.get('bottles_to_show', 5),
            'poops_to_show': group_row.get('poops_to_show', 1),
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
        
        client = get_supabase_client()
        
        # Get entries for the last N days only
        from datetime import timedelta
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        entries_response = client.table(ENTRIES_TABLE).select("*").eq('group_id', group_id).gte('time', cutoff_date).order('time', desc=True).execute()
        poop_response = client.table(POOP_TABLE).select("*").eq('group_id', group_id).gte('time', cutoff_date).order('time', desc=True).execute()
        
        # Format entries
        entries = []
        for entry in entries_response.data:
            entries.append({
                'amount': entry['amount'],
                'time': parse_time(entry['time'])
            })
        
        # Format poop
        poop = []
        for poop_entry in poop_response.data:
            poop.append({
                'time': parse_time(poop_entry['time']),
                'info': poop_entry.get('info')
            })
        
        return {
            'entries': entries,
            'poop': poop
        }
    except Exception as e:
        print(f"Error getting stats for user {user_id}: {e}")
        return None

# Groups operations
def get_all_groups() -> Dict[str, Dict]:
    """Get all groups from database and format them like the old JSON structure, using group_id as key"""
    try:
        client = get_supabase_client()
        
        # Get all groups with a single query
        groups_response = client.table(GROUPS_TABLE).select("*").execute()
        
        if not groups_response.data:
            return {}
        
        # Get all group IDs
        group_ids = [group['id'] for group in groups_response.data]
        
        # Get all entries for all groups in one query
        entries_response = client.table(ENTRIES_TABLE).select("*").in_('group_id', group_ids).order('time', desc=True).execute()
        
        # Get all poop for all groups in one query
        poop_response = client.table(POOP_TABLE).select("*").in_('group_id', group_ids).order('time', desc=True).execute()
        
        # Get all user messages for all groups in one query
        messages_response = client.table(USER_MESSAGES_TABLE).select("*").in_('group_id', group_ids).execute()
        
        # Organize entries by group_id
        entries_by_group = {}
        for entry in entries_response.data:
            group_id = entry['group_id']
            if group_id not in entries_by_group:
                entries_by_group[group_id] = []
            entries_by_group[group_id].append({
                'amount': entry['amount'],
                'time': parse_time(entry['time'])
            })
        
        # Organize poop by group_id
        poop_by_group = {}
        for poop_entry in poop_response.data:
            group_id = poop_entry['group_id']
            if group_id not in poop_by_group:
                poop_by_group[group_id] = []
            poop_by_group[group_id].append({
                'time': parse_time(poop_entry['time']),
                'info': poop_entry.get('info')
            })
        
        # Organize user messages by group_id
        messages_by_group = {}
        for msg in messages_response.data:
            group_id = msg['group_id']
            if group_id not in messages_by_group:
                messages_by_group[group_id] = {}
            messages_by_group[group_id][str(msg['user_id'])] = {
                'main_message_id': msg['main_message_id'],
                'main_chat_id': msg['main_chat_id']
            }
        
        # Build final result
        groups = {}
        for group_row in groups_response.data:
            group_id = group_row['id']
            
            # Ensure users are stored as integers
            users = group_row.get('users', [])
            int_users = []
            for user in users:
                try:
                    int_users.append(int(user))
                except (ValueError, TypeError):
                    print(f"Warning: Invalid user ID in group {group_id}: {user}")
                    continue
            
            groups[str(group_id)] = {
                'id': group_id,
                'name': group_row['name'],
                'users': int_users,
                'entries': entries_by_group.get(group_id, []),
                'poop': poop_by_group.get(group_id, []),
                'time_difference': group_row.get('time_difference', 0) or 0,
                'last_bottle': group_row.get('last_bottle', 0) or 0,
                'bottles_to_show': group_row.get('bottles_to_show', 5),
                'poops_to_show': group_row.get('poops_to_show', 1),
                'user_messages': messages_by_group.get(group_id, {})
            }
        
        return groups
        
    except Exception as e:
        print(f"Error getting groups from database: {e}")
        return {}

def get_group_by_id(group_id: int) -> Optional[Dict]:
    """Get a specific group from database by id"""
    try:
        client = get_supabase_client()
        group_response = client.table(GROUPS_TABLE).select("*").eq('id', group_id).execute()
        if not group_response.data:
            return None
        group_row = group_response.data[0]
        entries_response = client.table(ENTRIES_TABLE).select("*").eq('group_id', group_id).order('time', desc=True).execute()
        poop_response = client.table(POOP_TABLE).select("*").eq('group_id', group_id).order('time', desc=True).execute()
        messages_response = client.table(USER_MESSAGES_TABLE).select("*").eq('group_id', group_id).execute()
        entries = []
        for entry in entries_response.data:
            entries.append({
                'amount': entry['amount'],
                'time': parse_time(entry['time'])
            })
        poop = []
        for poop_entry in poop_response.data:
            poop.append({
                'time': parse_time(poop_entry['time']),
                'info': poop_entry.get('info')
            })
        user_messages = {}
        for msg in messages_response.data:
            user_messages[str(msg['user_id'])] = {
                'main_message_id': msg['main_message_id'],
                'main_chat_id': msg['main_chat_id']
            }
        # Ensure users are stored as integers
        users = group_row.get('users', [])
        int_users = []
        for user in users:
            try:
                int_users.append(int(user))
            except (ValueError, TypeError):
                print(f"Warning: Invalid user ID in group {group_id}: {user}")
                continue
        
        return {
            'id': group_id,
            'name': group_row['name'],
            'users': int_users,
            'entries': entries,
            'poop': poop,
            'time_difference': group_row.get('time_difference', 0) or 0,
            'last_bottle': group_row.get('last_bottle', 0) or 0,
            'bottles_to_show': group_row.get('bottles_to_show', 5),
            'poops_to_show': group_row.get('poops_to_show', 1),
            'user_messages': user_messages
        }
    except Exception as e:
        print(f"Error getting group id={group_id} from database: {e}")
        return None

def get_group_by_name(group_name: str) -> Optional[Dict]:
    """Get a specific group from database by name (for backward compatibility)"""
    try:
        client = get_supabase_client()
        group_response = client.table(GROUPS_TABLE).select("*").eq('name', group_name).execute()
        if not group_response.data:
            return None
        group_row = group_response.data[0]
        return get_group_by_id(group_row['id'])
    except Exception as e:
        print(f"Error getting group name={group_name} from database: {e}")
        return None

def create_group(group_name: str, user_id: int) -> bool:
    """Create a new group"""
    try:
        client = get_supabase_client()
        
        # Create group
        client.table(GROUPS_TABLE).insert({
            'name': group_name,
            'users': [user_id],
            'time_difference': 0,
            'bottles_to_show': 5,
            'poops_to_show': 1
        }).execute()
        
        # Invalidate cache to ensure the new group is immediately visible
        _invalidate_cache()
        
        return True
        
    except Exception as e:
        print(f"Error creating group {group_name}: {e}")
        return False

def update_group(group_id: int, group_data: Dict) -> bool:
    """Update group data"""
    try:
        client = get_supabase_client()
        
        # Ensure users are stored as integers
        users = group_data.get('users', [])
        int_users = []
        for user in users:
            try:
                int_users.append(int(user))
            except (ValueError, TypeError):
                print(f"Warning: Invalid user ID in group data: {user}")
                continue
        
        # Update group basic info
        client.table(GROUPS_TABLE).update({
            'users': int_users,
            'time_difference': group_data.get('time_difference', 0),
            'last_bottle': group_data.get('last_bottle'),
            'bottles_to_show': group_data.get('bottles_to_show', 5),
            'poops_to_show': group_data.get('poops_to_show', 1)
        }).eq('id', group_id).execute()
        
        # Clear existing entries and poop
        client.table(ENTRIES_TABLE).delete().eq('group_id', group_id).execute()
        client.table(POOP_TABLE).delete().eq('group_id', group_id).execute()
        client.table(USER_MESSAGES_TABLE).delete().eq('group_id', group_id).execute()
        
        # Insert new entries
        if group_data.get('entries'):
            entries_data = []
            for entry in group_data['entries']:
                entries_data.append({
                    'group_id': group_id,
                    'amount': entry['amount'],
                    'time': entry['time'].isoformat() if isinstance(entry['time'], datetime) else entry['time'],
                    'created_at': datetime.now().isoformat()
                })
            if entries_data:
                client.table(ENTRIES_TABLE).insert(entries_data).execute()
        
        # Insert new poop
        if group_data.get('poop'):
            poop_data = []
            for poop_entry in group_data['poop']:
                poop_data.append({
                    'group_id': group_id,
                    'time': poop_entry['time'].isoformat() if isinstance(poop_entry['time'], datetime) else poop_entry['time'],
                    'info': poop_entry.get('info'),
                    'created_at': datetime.now().isoformat()
                })
            if poop_data:
                client.table(POOP_TABLE).insert(poop_data).execute()
        
        # Insert user messages
        if group_data.get('user_messages'):
            messages_data = []
            for user_id_str, msg_data in group_data['user_messages'].items():
                # Convert string key back to int for database
                user_id_int = int(user_id_str)
                messages_data.append({
                    'group_id': group_id,
                    'user_id': user_id_int,
                    'main_message_id': msg_data['main_message_id'],
                    'main_chat_id': msg_data['main_chat_id']
                })
            if messages_data:
                client.table(USER_MESSAGES_TABLE).insert(messages_data).execute()
        
        # Invalidate cache to ensure all changes are immediately visible
        _invalidate_cache()
        
        return True
        
    except Exception as e:
        print(f"Error updating group {group_id}: {e}")
        return False

def add_entry_to_group(group_id: int, amount: int, time: datetime) -> bool:
    """Add a new bottle entry to a group by id"""
    try:
        client = get_supabase_client()
        client.table(ENTRIES_TABLE).insert({
            'group_id': group_id,
            'amount': amount,
            'time': time.isoformat() if isinstance(time, datetime) else time,
            'created_at': datetime.now().isoformat()
        }).execute()
        # Update last_bottle in group
        client.table(GROUPS_TABLE).update({
            'last_bottle': amount
        }).eq('id', group_id).execute()
        
        # Invalidate cache for this group's users
        _invalidate_cache()
        
        return True
    except Exception as e:
        print(f"Error adding entry to group id={group_id}: {e}")
        return False

def remove_last_entry_from_group(group_id: int) -> bool:
    """Remove the last bottle entry from a group"""
    try:
        client = get_supabase_client()
        
        # Get the last entry
        entries_response = client.table(ENTRIES_TABLE).select("*").eq('group_id', group_id).order('time', desc=True).limit(1).execute()
        
        if entries_response.data:
            # Delete the last entry
            client.table(ENTRIES_TABLE).delete().eq('id', entries_response.data[0]['id']).execute()
            
            # Update last_bottle if there are remaining entries
            remaining_entries = client.table(ENTRIES_TABLE).select("*").eq('group_id', group_id).order('time', desc=True).limit(1).execute()
            
            if remaining_entries.data:
                client.table(GROUPS_TABLE).update({
                    'last_bottle': remaining_entries.data[0]['amount']
                }).eq('id', group_id).execute()
            else:
                client.table(GROUPS_TABLE).update({
                    'last_bottle': None
                }).eq('id', group_id).execute()
        
        # Invalidate cache for this group's users
        _invalidate_cache()
        
        return True
        
    except Exception as e:
        print(f"Error removing last entry from group {group_id}: {e}")
        return False

def add_poop_to_group(group_id: int, time: datetime, info: Optional[str] = None) -> bool:
    """Add a new poop entry to a group by id"""
    try:
        client = get_supabase_client()
        client.table(POOP_TABLE).insert({
            'group_id': group_id,
            'time': time.isoformat() if isinstance(time, datetime) else time,
            'info': info,
            'created_at': datetime.now().isoformat()
        }).execute()
        
        # Invalidate cache for this group's users
        _invalidate_cache()
        
        return True
    except Exception as e:
        print(f"Error adding poop to group id={group_id}: {e}")
        return False

def set_user_message_info(group_id: int, user_id: int, message_id: int, chat_id: int) -> bool:
    """Set message info for a user in a group by id"""
    try:
        client = get_supabase_client()
        # Delete existing message info for this user
        client.table(USER_MESSAGES_TABLE).delete().eq('group_id', group_id).eq('user_id', user_id).execute()
        # Insert new message info
        client.table(USER_MESSAGES_TABLE).insert({
            'group_id': group_id,
            'user_id': user_id,
            'main_message_id': message_id,
            'main_chat_id': chat_id
        }).execute()
        
        # Invalidate cache for this user
        _invalidate_user_cache(user_id)
        
        return True
    except Exception as e:
        print(f"Error setting user message info for group id={group_id}, user {user_id}: {e}")
        return False

def get_user_message_info(group_id: int, user_id: int) -> tuple:
    """Get message info for a user in a group by id"""
    try:
        client = get_supabase_client()
        response = client.table(USER_MESSAGES_TABLE).select("*").eq('group_id', group_id).eq('user_id', user_id).execute()
        if response.data:
            msg_data = response.data[0]
            return msg_data['main_message_id'], msg_data['main_chat_id']
        return None, None
    except Exception as e:
        print(f"Error getting user message info for group id={group_id}, user {user_id}: {e}")
        return None, None

def clear_user_message_info(group_id: int, user_id: int) -> bool:
    """Clear message info for a user in a group by id"""
    try:
        client = get_supabase_client()
        client.table(USER_MESSAGES_TABLE).delete().eq('group_id', group_id).eq('user_id', user_id).execute()
        
        # Invalidate cache for this user
        _invalidate_user_cache(user_id)
        
        return True
    except Exception as e:
        print(f"Error clearing user message info for group id={group_id}, user {user_id}: {e}")
        return False

def cleanup_old_data() -> bool:
    """Clean up data older than 5 days"""
    try:
        client = get_supabase_client()
        today = date.today()
        
        # Get all entries and poop entries
        entries_response = client.table(ENTRIES_TABLE).select("*").execute()
        poop_response = client.table(POOP_TABLE).select("*").execute()
        
        # Filter entries to keep only last 5 days
        entries_to_delete = []
        for entry in entries_response.data:
            try:
                entry_date = parse_time(entry['time']).date()
                if (today - entry_date).days > 5:
                    entries_to_delete.append(entry['id'])
            except (ValueError, IndexError):
                pass
        
        # Filter poop to keep only last 5 days
        poop_to_delete = []
        for poop_entry in poop_response.data:
            try:
                poop_date = parse_time(poop_entry['time']).date()
                if (today - poop_date).days > 5:
                    poop_to_delete.append(poop_entry['id'])
            except (ValueError, IndexError):
                pass
        
        # Delete old entries
        if entries_to_delete:
            client.table(ENTRIES_TABLE).delete().in_('id', entries_to_delete).execute()
        
        # Delete old poop
        if poop_to_delete:
            client.table(POOP_TABLE).delete().in_('id', poop_to_delete).execute()
        
        if entries_to_delete or poop_to_delete:
            print(f"🧹 Database cleanup completed:")
            print(f"   • Bottle entries deleted: {len(entries_to_delete)}")
            print(f"   • Poop entries deleted: {len(poop_to_delete)}")
        
        return True
        
    except Exception as e:
        print(f"Error during database cleanup: {e}")
        return False

def update_group_name(group_id: int, new_name: str) -> bool:
    """Update just the group name in the database"""
    try:
        client = get_supabase_client()
        client.table(GROUPS_TABLE).update({
            'name': new_name
        }).eq('id', group_id).execute()
        
        # Invalidate cache to ensure the name change is immediately visible
        _invalidate_cache()
        
        return True
    except Exception as e:
        print(f"Error updating group name for group id={group_id}: {e}")
        return False

def cleanup_user_ids():
    """Clean up existing data by converting string user IDs to integers"""
    try:
        client = get_supabase_client()
        print("Starting user ID cleanup...")
        
        # Get all groups
        response = client.table(GROUPS_TABLE).select("id,users").execute()
        
        for group in response.data:
            group_id = group['id']
            users = group.get('users', [])
            
            # Check if any user IDs are strings
            needs_update = False
            int_users = []
            
            for user in users:
                if isinstance(user, str):
                    try:
                        int_users.append(int(user))
                        needs_update = True
                        print(f"Converting user ID from string '{user}' to int {int(user)} in group {group_id}")
                    except ValueError:
                        print(f"Warning: Invalid user ID '{user}' in group {group_id}, skipping")
                        continue
                else:
                    int_users.append(user)
            
            # Update group if needed
            if needs_update:
                client.table(GROUPS_TABLE).update({
                    'users': int_users
                }).eq('id', group_id).execute()
                print(f"Updated group {group_id} with integer user IDs: {int_users}")
        
        print("User ID cleanup completed!")
        return True
        
    except Exception as e:
        print(f"Error during user ID cleanup: {e}")
        return False 