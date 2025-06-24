import os
from dotenv import load_dotenv

load_dotenv()

TEST_MODE = True

# Supabase Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Database table names
GROUPS_TABLE = "groups"
ENTRIES_TABLE = "entries"
POOP_TABLE = "poop"
USER_MESSAGES_TABLE = "user_messages"