# wake_up.py
import os
import time  # NEW: Import the time module for sleeping
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Retrieve the app URL from the GitHub Actions environment variable
STREAMLIT_URL = os.environ.get("STREAMLIT_APP_URL")

def wake_up_app(url):
    options = Options()
    # Configuration required for running Chrome in a headless (no-GUI) environment
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--remote-debugging-pipe") 

    driver = webdriver.Chrome(options=options)
    print(f"Attempting to visit: {url}")
    
    try:
        driver.get(url)
        
        # Wait up to 30 seconds for the Streamlit "wake up" button to appear
        wait = WebDriverWait(driver, 30) 
        button = wait.until(EC.presence_of_element_located((By.XPATH, "//button[contains(.,'Yes, get this app back up')]")))
        
        print("Hibernation button found. Clicking to wake up...")
        button.click()
        print("Button clicked. App should be starting up.")

        # Wait for the button to disappear, signaling the app is loading
        wait.until(EC.invisibility_of_element_located((By.XPATH, "//button[contains(.,'Yes, get this app back up')]")))
        
    except Exception as e:
        # If the button isn't found, the app was likely already awake.
        print(f"App was likely already awake, or failed to wake. Error: {e}")
        
    finally:
        # 🔑 KEY CHANGE: Add a sleep to increase the session duration 
        # This gives Streamlit's analytics time to fully register the user session.
        print("Pausing for 15 seconds to ensure session registration in analytics...")
        time.sleep(15) 
        
        driver.quit()
        print("Script finished. Driver closed.")

if __name__ == "__main__":
    if STREAMLIT_URL:
        wake_up_app(STREAMLIT_URL)
    else:
        print("ERROR: STREAMLIT_APP_URL environment variable is not set.")