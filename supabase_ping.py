import os
import sys
from supabase import create_client

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

if not url or not key:
    print("Error: Environment variables SUPABASE_URL or SUPABASE_KEY not found.")
    sys.exit(1)

try:
    # Ensure the URL is clean of whitespace and uses the correct .co extension
    supabase = create_client(url.strip(), key.strip())
    
    # Action: Insert a heartbeat row
    # This row will stay in your table permanently as an activity log
    response = supabase.table("keep_alive").insert({
        "status": "ping",
        "notes": "Automated GitHub Action Heartbeat"
    }).execute()
    
    print("Successfully logged heartbeat row to Supabase.")
    
except Exception as e:
    print(f"Connection Error: {e}")
    sys.exit(1)