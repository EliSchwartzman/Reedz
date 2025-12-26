import os
import sys
from supabase import create_client

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

if not url or not key:
    print("Error: Environment variables not found.")
    sys.exit(1)

try:
    # Ensure the URL doesn't have accidental whitespace
    supabase = create_client(url.strip(), key.strip())
    
    # Attempt the ping
    supabase.table("keep_alive").insert({"status": "ping"}).execute()
    print("Successfully inserted ping row.")
    
    # Cleanup
    supabase.table("keep_alive").delete().eq("status", "ping").execute()
    print("Successfully cleaned up ping rows.")

except Exception as e:
    print(f"Connection Error: {e}")
    sys.exit(1)