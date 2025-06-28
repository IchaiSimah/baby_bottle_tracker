import os
from dotenv import load_dotenv

load_dotenv()

TEST_MODE = False

# SQLite Database Configuration
DATABASE_PATH = os.getenv("DATABASE_PATH", "data/baby_bottle_tracker.db")

# Database table names
GROUPS_TABLE = "groups"
ENTRIES_TABLE = "entries"
POOP_TABLE = "poop"
USER_MESSAGES_TABLE = "user_messages"
