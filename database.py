import os
import json
import httpx
from datetime import datetime, date
from typing import Dict, List, Optional, Any
from config import SUPABASE_URL, SUPABASE_KEY, GROUPS_TABLE, ENTRIES_TABLE, POOP_TABLE, USER_MESSAGES_TABLE
from dateutil import parser as date_parser

# Initialize HTTP client for Supabase REST API
_http_client: httpx.AsyncClient = None

def get_http_client() -> httpx.AsyncClient:
    """Get or create HTTP client for Supabase REST API"""
    global _http_client
    if _http_client is None:
        _http_client = httpx.AsyncClient(
            base_url=f"{SUPABASE_URL}/rest/v1",
            headers={
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}",
                "Content-Type": "application/json",
                "Prefer": "return=representation"
            },
            timeout=30.0
        )
    return _http_client

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
        import asyncio
        return asyncio.run(_get_user_group_id_async(user_id))
    except Exception as e:
        print(f"Error getting group for user {user_id}: {e}")
        return None

async def _get_user_group_id_async(user_id: int) -> Optional[int]:
    """Async version of get_user_group_id"""
    try:
        client = get_http_client()
        # Users are stored as strings in the database to handle large Telegram IDs
        params = {"users": f"cs.[\"{user_id}\"]"}
        response = await client.get(f"/{GROUPS_TABLE}", params=params)
        response.raise_for_status()
        
        data = response.json()
        if data:
            return data[0]['id']
        return None
    except Exception as e:
        print(f"Error getting group for user {user_id}: {e}")
        return None

def get_group_data_for_user(user_id: int) -> Optional[Dict]:
    """Get only the data needed for a specific user's group"""
    try:
        import asyncio
        return asyncio.run(_get_group_data_for_user_async(user_id))
    except Exception as e:
        print(f"Error getting group data for user {user_id}: {e}")
        return None

async def _get_group_data_for_user_async(user_id: int) -> Optional[Dict]:
    """Async version of get_group_data_for_user"""
    try:
        group_id = await _get_user_group_id_async(user_id)
        if not group_id:
            return None
        
        client = get_http_client()
        
        # Get group basic info
        group_response = await client.get(f"/{GROUPS_TABLE}", params={"id": f"eq.{group_id}"})
        group_response.raise_for_status()
        group_data = group_response.json()
        
        if not group_data:
            return None
        
        group_row = group_data[0]
        
        # Get only recent entries (last 10) instead of all
        entries_response = await client.get(
            f"/{ENTRIES_TABLE}", 
            params={
                "group_id": f"eq.{group_id}",
                "order": "time.desc",
                "limit": "10"
            }
        )
        entries_response.raise_for_status()
        
        # Get only recent poop (last 5) instead of all
        poop_response = await client.get(
            f"/{POOP_TABLE}", 
            params={
                "group_id": f"eq.{group_id}",
                "order": "time.desc",
                "limit": "5"
            }
        )
        poop_response.raise_for_status()
        
        # Get user message info
        messages_response = await client.get(
            f"/{USER_MESSAGES_TABLE}", 
            params={
                "group_id": f"eq.{group_id}",
                "user_id": f"eq.{user_id}"
            }
        )
        messages_response.raise_for_status()
        
        # Format entries
        entries = []
        for entry in entries_response.json():
            entries.append({
                'amount': entry['amount'],
                'time': parse_time(entry['time'])
            })
        
        # Format poop
        poop = []
        for poop_entry in poop_response.json():
            poop.append({
                'time': parse_time(poop_entry['time']),
                'info': poop_entry.get('info')
            })
        
        # Format user messages
        user_messages = {}
        for msg in messages_response.json():
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
        import asyncio
        return asyncio.run(_get_group_stats_for_user_async(user_id, days))
    except Exception as e:
        print(f"Error getting stats for user {user_id}: {e}")
        return None

async def _get_group_stats_for_user_async(user_id: int, days: int = 5) -> Optional[Dict]:
    """Async version of get_group_stats_for_user"""
    try:
        group_id = await _get_user_group_id_async(user_id)
        if not group_id:
            return None
        
        client = get_http_client()
        
        # Get entries for the last N days only
        from datetime import timedelta
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        entries_response = await client.get(
            f"/{ENTRIES_TABLE}", 
            params={
                "group_id": f"eq.{group_id}",
                "time": f"gte.{cutoff_date}",
                "order": "time.desc"
            }
        )
        entries_response.raise_for_status()
        
        poop_response = await client.get(
            f"/{POOP_TABLE}", 
            params={
                "group_id": f"eq.{group_id}",
                "time": f"gte.{cutoff_date}",
                "order": "time.desc"
            }
        )
        poop_response.raise_for_status()
        
        # Format entries
        entries = []
        for entry in entries_response.json():
            entries.append({
                'amount': entry['amount'],
                'time': parse_time(entry['time'])
            })
        
        # Format poop
        poop = []
        for poop_entry in poop_response.json():
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
        import asyncio
        return asyncio.run(_get_all_groups_async())
    except Exception as e:
        print(f"Error getting groups from database: {e}")
        return {}

async def _get_all_groups_async() -> Dict[str, Dict]:
    """Async version of get_all_groups"""
    try:
        client = get_http_client()
        
        # Get all groups with a single query
        groups_response = await client.get(f"/{GROUPS_TABLE}")
        groups_response.raise_for_status()
        groups_data = groups_response.json()
        
        if not groups_data:
            return {}
        
        # Get all group IDs
        group_ids = [group['id'] for group in groups_data]
        
        # Get all entries for all groups in one query
        entries_response = await client.get(
            f"/{ENTRIES_TABLE}", 
            params={
                "group_id": f"in.({','.join(map(str, group_ids))})",
                "order": "time.desc"
            }
        )
        entries_response.raise_for_status()
        
        # Get all poop for all groups in one query
        poop_response = await client.get(
            f"/{POOP_TABLE}", 
            params={
                "group_id": f"in.({','.join(map(str, group_ids))})",
                "order": "time.desc"
            }
        )
        poop_response.raise_for_status()
        
        # Get all user messages for all groups in one query
        messages_response = await client.get(
            f"/{USER_MESSAGES_TABLE}", 
            params={
                "group_id": f"in.({','.join(map(str, group_ids))})"
            }
        )
        messages_response.raise_for_status()
        
        # Organize entries by group_id
        entries_by_group = {}
        for entry in entries_response.json():
            group_id = entry['group_id']
            if group_id not in entries_by_group:
                entries_by_group[group_id] = []
            entries_by_group[group_id].append({
                'amount': entry['amount'],
                'time': parse_time(entry['time'])
            })
        
        # Organize poop by group_id
        poop_by_group = {}
        for poop_entry in poop_response.json():
            group_id = poop_entry['group_id']
            if group_id not in poop_by_group:
                poop_by_group[group_id] = []
            poop_by_group[group_id].append({
                'time': parse_time(poop_entry['time']),
                'info': poop_entry.get('info')
            })
        
        # Organize user messages by group_id
        messages_by_group = {}
        for msg in messages_response.json():
            group_id = msg['group_id']
            if group_id not in messages_by_group:
                messages_by_group[group_id] = {}
            messages_by_group[group_id][str(msg['user_id'])] = {
                'main_message_id': msg['main_message_id'],
                'main_chat_id': msg['main_chat_id']
            }
        
        # Build final result
        groups = {}
        for group_row in groups_data:
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
        import asyncio
        return asyncio.run(_get_group_by_id_async(group_id))
    except Exception as e:
        print(f"Error getting group id={group_id} from database: {e}")
        return None

async def _get_group_by_id_async(group_id: int) -> Optional[Dict]:
    """Async version of get_group_by_id"""
    try:
        client = get_http_client()
        
        group_response = await client.get(f"/{GROUPS_TABLE}", params={"id": f"eq.{group_id}"})
        group_response.raise_for_status()
        group_data = group_response.json()
        
        if not group_data:
            return None
            
        group_row = group_data[0]
        
        entries_response = await client.get(
            f"/{ENTRIES_TABLE}", 
            params={
                "group_id": f"eq.{group_id}",
                "order": "time.desc"
            }
        )
        entries_response.raise_for_status()
        
        poop_response = await client.get(
            f"/{POOP_TABLE}", 
            params={
                "group_id": f"eq.{group_id}",
                "order": "time.desc"
            }
        )
        poop_response.raise_for_status()
        
        messages_response = await client.get(
            f"/{USER_MESSAGES_TABLE}", 
            params={"group_id": f"eq.{group_id}"}
        )
        messages_response.raise_for_status()
        
        entries = []
        for entry in entries_response.json():
            entries.append({
                'amount': entry['amount'],
                'time': parse_time(entry['time'])
            })
        
        poop = []
        for poop_entry in poop_response.json():
            poop.append({
                'time': parse_time(poop_entry['time']),
                'info': poop_entry.get('info')
            })
        
        user_messages = {}
        for msg in messages_response.json():
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
        import asyncio
        return asyncio.run(_get_group_by_name_async(group_name))
    except Exception as e:
        print(f"Error getting group name={group_name} from database: {e}")
        return None

async def _get_group_by_name_async(group_name: str) -> Optional[Dict]:
    """Async version of get_group_by_name"""
    try:
        client = get_http_client()
        group_response = await client.get(f"/{GROUPS_TABLE}", params={"name": f"eq.{group_name}"})
        group_response.raise_for_status()
        group_data = group_response.json()
        
        if not group_data:
            return None
            
        group_row = group_data[0]
        return await _get_group_by_id_async(group_row['id'])
    except Exception as e:
        print(f"Error getting group name={group_name} from database: {e}")
        return None

def create_group(group_name: str, user_id: int) -> bool:
    """Create a new group"""
    try:
        import asyncio
        return asyncio.run(_create_group_async(group_name, user_id))
    except Exception as e:
        print(f"Error creating group {group_name}: {e}")
        return False

async def _create_group_async(group_name: str, user_id: int) -> bool:
    """Async version of create_group"""
    try:
        client = get_http_client()
        
        # Create group - store user_id as string to handle large Telegram IDs
        group_data = {
            'name': group_name,
            'users': [str(user_id)],
            'time_difference': 3,
            'bottles_to_show': 5,
            'poops_to_show': 1
        }
        
        response = await client.post(f"/{GROUPS_TABLE}", json=group_data)
        response.raise_for_status()
        
        # Invalidate cache to ensure the new group is immediately visible
        _invalidate_cache()
        
        return True
        
    except Exception as e:
        print(f"Error creating group {group_name}: {e}")
        return False

def update_group(group_id: int, group_data: Dict) -> bool:
    """Update group data"""
    try:
        import asyncio
        return asyncio.run(_update_group_async(group_id, group_data))
    except Exception as e:
        print(f"Error updating group {group_id}: {e}")
        return False

async def _update_group_async(group_id: int, group_data: Dict) -> bool:
    """Async version of update_group"""
    try:
        client = get_http_client()
        
        # Ensure users are stored as strings to handle large Telegram IDs
        users = group_data.get('users', [])
        str_users = []
        for user in users:
            try:
                str_users.append(str(user))
            except (ValueError, TypeError):
                print(f"Warning: Invalid user ID in group data: {user}")
                continue
        
        # Update group basic info
        update_data = {
            'users': str_users,
            'time_difference': group_data.get('time_difference', 0),
            'last_bottle': group_data.get('last_bottle'),
            'bottles_to_show': group_data.get('bottles_to_show', 5),
            'poops_to_show': group_data.get('poops_to_show', 1)
        }
        
        response = await client.patch(f"/{GROUPS_TABLE}", params={"id": f"eq.{group_id}"}, json=update_data)
        response.raise_for_status()
        
        # Clear existing entries and poop
        await client.delete(f"/{ENTRIES_TABLE}", params={"group_id": f"eq.{group_id}"})
        await client.delete(f"/{POOP_TABLE}", params={"group_id": f"eq.{group_id}"})
        await client.delete(f"/{USER_MESSAGES_TABLE}", params={"group_id": f"eq.{group_id}"})
        
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
                await client.post(f"/{ENTRIES_TABLE}", json=entries_data)
        
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
                await client.post(f"/{POOP_TABLE}", json=poop_data)
        
        # Insert user messages
        if group_data.get('user_messages'):
            messages_data = []
            for user_id_str, msg_data in group_data['user_messages'].items():
                # Keep user_id as string for database
                messages_data.append({
                    'group_id': group_id,
                    'user_id': user_id_str,
                    'main_message_id': msg_data['main_message_id'],
                    'main_chat_id': msg_data['main_chat_id']
                })
            if messages_data:
                await client.post(f"/{USER_MESSAGES_TABLE}", json=messages_data)
        
        # Invalidate cache to ensure all changes are immediately visible
        _invalidate_cache()
        
        return True
        
    except Exception as e:
        print(f"Error updating group {group_id}: {e}")
        return False

def add_entry_to_group(group_id: int, amount: int, time: datetime) -> bool:
    """Add a new bottle entry to a group by id"""
    try:
        import asyncio
        return asyncio.run(_add_entry_to_group_async(group_id, amount, time))
    except Exception as e:
        print(f"Error adding entry to group id={group_id}: {e}")
        return False

async def _add_entry_to_group_async(group_id: int, amount: int, time: datetime) -> bool:
    """Async version of add_entry_to_group"""
    try:
        client = get_http_client()
        
        entry_data = {
            'group_id': group_id,
            'amount': amount,
            'time': time.isoformat() if isinstance(time, datetime) else time,
            'created_at': datetime.now().isoformat()
        }
        
        response = await client.post(f"/{ENTRIES_TABLE}", json=entry_data)
        response.raise_for_status()
        
        # Update last_bottle in group
        update_data = {'last_bottle': amount}
        await client.patch(f"/{GROUPS_TABLE}", params={"id": f"eq.{group_id}"}, json=update_data)
        
        # Invalidate cache for this group's users
        _invalidate_cache()
        
        return True
    except Exception as e:
        print(f"Error adding entry to group id={group_id}: {e}")
        return False

def remove_last_entry_from_group(group_id: int) -> bool:
    """Remove the last bottle entry from a group"""
    try:
        import asyncio
        return asyncio.run(_remove_last_entry_from_group_async(group_id))
    except Exception as e:
        print(f"Error removing last entry from group {group_id}: {e}")
        return False

async def _remove_last_entry_from_group_async(group_id: int) -> bool:
    """Async version of remove_last_entry_from_group"""
    try:
        client = get_http_client()
        
        # Get the last entry
        entries_response = await client.get(
            f"/{ENTRIES_TABLE}", 
            params={
                "group_id": f"eq.{group_id}",
                "order": "time.desc",
                "limit": "1"
            }
        )
        entries_response.raise_for_status()
        entries_data = entries_response.json()
        
        if entries_data:
            # Delete the last entry
            await client.delete(f"/{ENTRIES_TABLE}", params={"id": f"eq.{entries_data[0]['id']}"})
            
            # Update last_bottle if there are remaining entries
            remaining_response = await client.get(
                f"/{ENTRIES_TABLE}", 
                params={
                    "group_id": f"eq.{group_id}",
                    "order": "time.desc",
                    "limit": "1"
                }
            )
            remaining_response.raise_for_status()
            remaining_data = remaining_response.json()
            
            if remaining_data:
                update_data = {'last_bottle': remaining_data[0]['amount']}
            else:
                update_data = {'last_bottle': None}
            
            await client.patch(f"/{GROUPS_TABLE}", params={"id": f"eq.{group_id}"}, json=update_data)
        
        # Invalidate cache for this group's users
        _invalidate_cache()
        
        return True
        
    except Exception as e:
        print(f"Error removing last entry from group {group_id}: {e}")
        return False

def add_poop_to_group(group_id: int, time: datetime, info: Optional[str] = None) -> bool:
    """Add a new poop entry to a group by id"""
    try:
        import asyncio
        return asyncio.run(_add_poop_to_group_async(group_id, time, info))
    except Exception as e:
        print(f"Error adding poop to group id={group_id}: {e}")
        return False

async def _add_poop_to_group_async(group_id: int, time: datetime, info: Optional[str] = None) -> bool:
    """Async version of add_poop_to_group"""
    try:
        client = get_http_client()
        
        poop_data = {
            'group_id': group_id,
            'time': time.isoformat() if isinstance(time, datetime) else time,
            'info': info,
            'created_at': datetime.now().isoformat()
        }
        
        response = await client.post(f"/{POOP_TABLE}", json=poop_data)
        response.raise_for_status()
        
        # Invalidate cache for this group's users
        _invalidate_cache()
        
        return True
    except Exception as e:
        print(f"Error adding poop to group id={group_id}: {e}")
        return False

def set_user_message_info(group_id: int, user_id: int, message_id: int, chat_id: int) -> bool:
    """Set message info for a user in a group by id"""
    try:
        import asyncio
        return asyncio.run(_set_user_message_info_async(group_id, user_id, message_id, chat_id))
    except Exception as e:
        print(f"Error setting user message info for group id={group_id}, user {user_id}: {e}")
        return False

async def _set_user_message_info_async(group_id: int, user_id: int, message_id: int, chat_id: int) -> bool:
    """Async version of set_user_message_info"""
    try:
        client = get_http_client()
        
        # Delete existing message info for this user
        await client.delete(
            f"/{USER_MESSAGES_TABLE}", 
            params={
                "group_id": f"eq.{group_id}",
                "user_id": f"eq.{user_id}"
            }
        )
        
        # Insert new message info
        message_data = {
            'group_id': group_id,
            'user_id': user_id,
            'main_message_id': message_id,
            'main_chat_id': chat_id
        }
        
        response = await client.post(f"/{USER_MESSAGES_TABLE}", json=message_data)
        response.raise_for_status()
        
        # Invalidate cache for this user
        _invalidate_user_cache(user_id)
        
        return True
    except Exception as e:
        print(f"Error setting user message info for group id={group_id}, user {user_id}: {e}")
        return False

def get_user_message_info(group_id: int, user_id: int) -> tuple:
    """Get message info for a user in a group by id"""
    try:
        import asyncio
        return asyncio.run(_get_user_message_info_async(group_id, user_id))
    except Exception as e:
        print(f"Error getting user message info for group id={group_id}, user {user_id}: {e}")
        return None, None

async def _get_user_message_info_async(group_id: int, user_id: int) -> tuple:
    """Async version of get_user_message_info"""
    try:
        client = get_http_client()
        response = await client.get(
            f"/{USER_MESSAGES_TABLE}", 
            params={
                "group_id": f"eq.{group_id}",
                "user_id": f"eq.{user_id}"
            }
        )
        response.raise_for_status()
        data = response.json()
        
        if data:
            msg_data = data[0]
            return msg_data['main_message_id'], msg_data['main_chat_id']
        return None, None
    except Exception as e:
        print(f"Error getting user message info for group id={group_id}, user {user_id}: {e}")
        return None, None

def clear_user_message_info(group_id: int, user_id: int) -> bool:
    """Clear message info for a user in a group by id"""
    try:
        import asyncio
        return asyncio.run(_clear_user_message_info_async(group_id, user_id))
    except Exception as e:
        print(f"Error clearing user message info for group id={group_id}, user {user_id}: {e}")
        return False

async def _clear_user_message_info_async(group_id: int, user_id: int) -> bool:
    """Async version of clear_user_message_info"""
    try:
        client = get_http_client()
        await client.delete(
            f"/{USER_MESSAGES_TABLE}", 
            params={
                "group_id": f"eq.{group_id}",
                "user_id": f"eq.{user_id}"
            }
        )
        
        # Invalidate cache for this user
        _invalidate_user_cache(user_id)
        
        return True
    except Exception as e:
        print(f"Error clearing user message info for group id={group_id}, user {user_id}: {e}")
        return False

def cleanup_old_data() -> bool:
    """Clean up data older than 5 days"""
    try:
        import asyncio
        return asyncio.run(_cleanup_old_data_async())
    except Exception as e:
        print(f"Error during database cleanup: {e}")
        return False

async def _cleanup_old_data_async() -> bool:
    """Async version of cleanup_old_data"""
    try:
        client = get_http_client()
        today = date.today()
        
        # Get all entries and poop entries
        entries_response = await client.get(f"/{ENTRIES_TABLE}")
        entries_response.raise_for_status()
        
        poop_response = await client.get(f"/{POOP_TABLE}")
        poop_response.raise_for_status()
        
        # Filter entries to keep only last 5 days
        entries_to_delete = []
        for entry in entries_response.json():
            try:
                entry_date = parse_time(entry['time']).date()
                if (today - entry_date).days > 5:
                    entries_to_delete.append(entry['id'])
            except (ValueError, IndexError):
                pass
        
        # Filter poop to keep only last 5 days
        poop_to_delete = []
        for poop_entry in poop_response.json():
            try:
                poop_date = parse_time(poop_entry['time']).date()
                if (today - poop_date).days > 5:
                    poop_to_delete.append(poop_entry['id'])
            except (ValueError, IndexError):
                pass
        
        # Delete old entries
        if entries_to_delete:
            await client.delete(f"/{ENTRIES_TABLE}", params={"id": f"in.({','.join(map(str, entries_to_delete))})"})
        
        # Delete old poop
        if poop_to_delete:
            await client.delete(f"/{POOP_TABLE}", params={"id": f"in.({','.join(map(str, poop_to_delete))})"})
        
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
        import asyncio
        return asyncio.run(_update_group_name_async(group_id, new_name))
    except Exception as e:
        print(f"Error updating group name for group id={group_id}: {e}")
        return False

async def _update_group_name_async(group_id: int, new_name: str) -> bool:
    """Async version of update_group_name"""
    try:
        client = get_http_client()
        update_data = {'name': new_name}
        response = await client.patch(f"/{GROUPS_TABLE}", params={"id": f"eq.{group_id}"}, json=update_data)
        response.raise_for_status()
        
        # Invalidate cache to ensure the name change is immediately visible
        _invalidate_cache()
        
        return True
    except Exception as e:
        print(f"Error updating group name for group id={group_id}: {e}")
        return False

def cleanup_user_ids():
    """Clean up existing data by converting string user IDs to integers"""
    try:
        import asyncio
        return asyncio.run(_cleanup_user_ids_async())
    except Exception as e:
        print(f"Error during user ID cleanup: {e}")
        return False

async def _cleanup_user_ids_async():
    """Async version of cleanup_user_ids"""
    try:
        client = get_http_client()
        print("Starting user ID cleanup...")
        
        # Get all groups
        response = await client.get(f"/{GROUPS_TABLE}", params={"select": "id,users"})
        response.raise_for_status()
        
        for group in response.json():
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
                update_data = {'users': int_users}
                await client.patch(f"/{GROUPS_TABLE}", params={"id": f"eq.{group_id}"}, json=update_data)
                print(f"Updated group {group_id} with integer user IDs: {int_users}")
        
        print("User ID cleanup completed!")
        return True
        
    except Exception as e:
        print(f"Error during user ID cleanup: {e}")
        return False 