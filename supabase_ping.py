import os
import sys
from supabase import create_client

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

try:
    supabase = create_client(url.strip(), key.strip())
    
    # We capture the response here to see if Supabase rejected the insert
    response = supabase.table("keep_alive").insert({"status": "ping"}).execute()
    
    # This will print the actual data Supabase saved
    print(f"Supabase Response Data: {response.data}")
    
    if len(response.data) == 0:
        print("Warning: The request succeeded but NO data was saved. Check RLS policies.")
    else:
        print("Success: Row confirmed in database.")

except Exception as e:
    print(f"Technical Error: {e}")
    sys.exit(1)