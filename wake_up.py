# wake_up_script.py
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

STREAMLIT_URL = os.environ.get("STREAMLIT_APP_URL")

def wake_up_app(url):
    options = Options()
    # Required for running in a headless environment like GitHub Actions
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--remote-debugging-pipe") 

    # Initializes Chrome driver with the necessary options
    driver = webdriver.Chrome(options=options)
    print(f"Attempting to visit: {url}")
    
    try:
        driver.get(url)
        
        # Wait up to 30 seconds for the "Wake Up" button to appear (if hibernating)
        wait = WebDriverWait(driver, 30) 
        button = wait.until(EC.presence_of_element_located((By.XPATH, "//button[contains(.,'Yes, get this app back up')]")))
        
        print("Hibernation button found. Clicking to wake up...")
        button.click()
        print("Button clicked. App should be starting up.")

        # Wait for the button to disappear, which signals the app is loading
        wait.until(EC.invisibility_of_element_located((By.XPATH, "//button[contains(.,'Yes, get this app back up')]")))
        
    except Exception as e:
        # This branch runs if the app is already awake (button not found) or if a general error occurred.
        print(f"App was likely already awake, or failed to wake. Error: {e}")
        
    finally:
        driver.quit()
        print("Script finished. Driver closed.")

if __name__ == "__main__":
    if STREAMLIT_URL:
        wake_up_app(STREAMLIT_URL)
    else:
        print("ERROR: STREAMLIT_APP_URL environment variable is not set.")