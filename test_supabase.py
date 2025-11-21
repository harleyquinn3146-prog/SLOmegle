import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

print(f"URL: {url}")
# print(f"Key: {key}") # Don't print key

try:
    supabase: Client = create_client(url, key)
    print("Client created.")
    
    # Try a simple query
    response = supabase.table('user_settings').select("*").limit(1).execute()
    print("Query successful!")
    print(response)
except Exception as e:
    print(f"Error: {e}")
