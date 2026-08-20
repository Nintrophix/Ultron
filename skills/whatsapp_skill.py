"""
Drives WhatsApp Web through a persistent Chrome profile, so you scan the
QR code once (first run) and it stays logged in after that - no further
prompts. Keeps the browser open in the background between commands so
sending a message is fast (no fresh page load each time).
"""

import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

import config

_driver = None

SEARCH_BOX = (By.XPATH, '//div[@contenteditable="true"][@data-tab="3"]')
MESSAGE_BOX = (By.XPATH, '//div[@contenteditable="true"][@data-tab="10"]')
LAST_MSG_IN = (By.XPATH, '(//div[contains(@class,"message-in")])[last()]//span[@class="selectable-text"]')


def _get_driver():
    global _driver
    if _driver is not None:
        return _driver

    options = Options()
    options.add_argument(f"--user-data-dir={config.WHATSAPP_CHROME_PROFILE_DIR}")
    options.add_argument("--profile-directory=Default")
    options.add_argument("--start-minimized")
    _driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    _driver.get("https://web.whatsapp.com")

    # First run: give time to scan the QR code. Subsequent runs load instantly
    # from the saved session.
    WebDriverWait(_driver, 60).until(
        EC.presence_of_element_located((By.XPATH, '//div[@id="pane-side"]'))
    )
    return _driver


def _open_chat(contact: str):
    driver = _get_driver()
    search = WebDriverWait(driver, 10).until(EC.element_to_be_clickable(SEARCH_BOX))
    search.click()
    search.send_keys(Keys.CONTROL, "a")
    search.send_keys(contact)
    time.sleep(1.2)  # let search results render
    search.send_keys(Keys.ENTER)
    time.sleep(0.5)


def send_message(contact: str, message: str) -> bool:
    try:
        _open_chat(contact)
        driver = _get_driver()
        box = WebDriverWait(driver, 10).until(EC.element_to_be_clickable(MESSAGE_BOX))
        box.send_keys(message)
        box.send_keys(Keys.ENTER)
        return True
    except Exception as e:
        print(f"[whatsapp_skill] send_message error: {e}")
        return False


def get_last_message(contact: str) -> str:
    try:
        _open_chat(contact)
        driver = _get_driver()
        el = WebDriverWait(driver, 10).until(EC.presence_of_element_located(LAST_MSG_IN))
        return el.text
    except Exception as e:
        print(f"[whatsapp_skill] get_last_message error: {e}")
        return ""
