"""
Automates the Home Assistant login process with Selenium.


"""
import os
import sys
import time
import datetime
import h5py

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- configuration -----------------------------------------------------------
HA_URL = os.getenv("HA_URL", "http://homeassistant.local:8123")
HA_USER = os.getenv("HA_USER")
HA_PASS = os.getenv("HA_PASS")

if not all([HA_USER, HA_PASS]):
    sys.exit("HA_USER and HA_PASS must be set as environment variables.")

# --- webdriver setup ---------------------------------------------------------
chrome_options = Options()
chrome_options.add_argument("--headless=new")   # comment out for a visible browser
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1920,1080")

driver = webdriver.Chrome(options=chrome_options)
wait = WebDriverWait(driver, 20)

def find_in_shadow(root, selector):
    """
    Locate an element inside a shadow root using a CSS selector.
    """
    return wait.until(lambda dr: root.find_element(By.CSS_SELECTOR, selector))

try:
    # Login to Home Assistant
    driver.get(f"{HA_URL}")
    user_selector = (
        "body > div.content > ha-authorize > div.card-content > ha-auth-flow > "
        "form > ha-auth-form > div > ha-auth-form-string:nth-child(1) > "
        "ha-auth-textfield > label > input"
    )
    pass_selector = (
        "body > div.content > ha-authorize > div.card-content > ha-auth-flow > "
        "form > ha-auth-form > div > ha-auth-form-string:nth-child(2) > "
        "ha-auth-textfield > label > input"
    )

    username_input = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, user_selector)))
    username_input.clear()
    username_input.send_keys(HA_USER)

    password_input = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, pass_selector)))
    password_input.clear()
    password_input.send_keys(HA_PASS)
    password_input.send_keys(Keys.RETURN)

    wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "body > home-assistant")))
    print(f"Logged in successfully to {HA_URL}")

    # Navigate to the Lovelace temperature dashboard
    temperature_url = f"{HA_URL}/lovelace/temperature"
    driver.get(temperature_url)
    wait.until(EC.url_contains("/lovelace/temperature"))
    print(f"Navigated to {temperature_url}")

    # Drill into nested shadow DOM to reach the statistic cards
    ha_root = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "body > home-assistant")))
    shadow1 = ha_root.shadow_root

    main_panel = find_in_shadow(shadow1, "home-assistant-main")
    shadow2 = main_panel.shadow_root

    drawer = find_in_shadow(shadow2, "ha-drawer")
    shadow3 = drawer

    lovelace_container = find_in_shadow(shadow3, "partial-panel-resolver > ha-panel-lovelace")
    shadow4 = lovelace_container.shadow_root

    hui_root = find_in_shadow(shadow4, "hui-root")
    shadow5 = hui_root.shadow_root

    view = find_in_shadow(shadow5, "div > hui-view-container > hui-view")
    masonry = find_in_shadow(view, "hui-masonry-view").shadow_root

    # Locate the "Outside Temperature Min Yesterday" statistic card
    min_stat_card = find_in_shadow(masonry, "div > div > hui-card:nth-child(1) > hui-statistic-card")
    min_shadow = min_stat_card.shadow_root
    min_info_host = find_in_shadow(min_shadow, "ha-card")
    min_info = find_in_shadow(min_info_host, "div.info")

    min_value = find_in_shadow(min_info, "span.value").text.strip()
    low_temp=float(min_value)

    min_unit  = find_in_shadow(min_info, "span.measurement").text.strip()
    print(f"Outside Temperature Min Yesterday: {min_value}{min_unit}")

    # Locate the "Outside Temperature Max Yesterday" statistic card
    max_stat_card = find_in_shadow(masonry, "div > div > hui-card:nth-child(2) > hui-statistic-card")
    max_shadow = max_stat_card.shadow_root
    max_info_host = find_in_shadow(max_shadow, "ha-card")
    max_info = find_in_shadow(max_info_host, "div.info")

    max_value = find_in_shadow(max_info, "span.value").text.strip()
    high_temp= float(max_value)
    max_unit  = find_in_shadow(max_info, "span.measurement").text.strip()
    print(f"Outside Temperature Max Yesterday: {max_value}{max_unit}")

    # store data in HDF5 file
    date_str = (datetime.date.today() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")

    with h5py.File("weather_ha.h5", "a") as f:
        # Top-level group is the date
        date_grp = f.require_group(date_str)
        # Subgroup is 'home_assistant'
        ha_grp = date_grp.require_group("home_assistant")
        # Datasets
        ha_grp["high_temp"] = high_temp
        ha_grp["low_temp"] = low_temp

    time.sleep(5)  # pause for headless debug
   

finally:
    driver.quit()