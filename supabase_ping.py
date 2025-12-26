import os
from supabase import create_client

# Load from environment variables (GitHub Secrets)
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

def keep_alive():
    try:
        # 1. Insert a dummy row (Assuming you have a 'keep_alive' table)
        # If you don't have a table, see the SQL note below.
        data, count = supabase.table("keep_alive").insert({"status": "ping"}).execute()
        print("Successfully inserted ping row.")

        # 2. Delete the row to keep the database clean
        # This deletes all rows where status is 'ping'
        supabase.table("keep_alive").delete().eq("status", "ping").execute()
        print("Successfully cleaned up ping rows.")
        
    except Exception as e:
        print(f"Error during keep-alive: {e}")

if __name__ == "__main__":
    keep_alive()