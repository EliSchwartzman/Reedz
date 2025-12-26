import os
from supabase import create_client

# Explicitly pulling from environment variables
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

# Safety check: print helpful error if variables are missing
if not url or not key:
    raise ValueError("Missing SUPABASE_URL or SUPABASE_KEY environment variables")

supabase = create_client(url, key)

def keep_alive():
    try:
        # Action: Insert a dummy row
        # Ensure you created the 'keep_alive' table in Supabase first
        supabase.table("keep_alive").insert({"status": "ping"}).execute()
        print("Successfully inserted ping row.")

        # Action: Delete the row to clean up
        supabase.table("keep_alive").delete().eq("status", "ping").execute()
        print("Successfully cleaned up ping rows.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    keep_alive()