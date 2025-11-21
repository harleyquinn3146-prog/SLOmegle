import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
DB_TYPE = os.getenv("DB_TYPE", "sqlite").lower()

# Admin user IDs (comma-separated in .env, e.g., "123456789,987654321")
ADMIN_IDS = [int(id.strip()) for id in os.getenv("ADMIN_IDS", "").split(",") if id.strip()]

BAD_WORDS = ["badword1", "badword2", "spam", "scam"]

INTERESTS = ["Anime", "Tech", "Gaming", "Movies", "Music", "Random"]
