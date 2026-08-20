import time

from pywinauto.keyboard import send_keys

from skills._win_automation import find_window, click_button_by_names, focus_window

WINDOW_TITLE = ".*Microsoft Teams.*"
ACCEPT_NAMES = ["Accept", "Accept call"]
DECLINE_NAMES = ["Decline", "Decline call"]


def is_ringing() -> bool:
    win = find_window(WINDOW_TITLE)
    if not win or not win.exists():
        return False
    try:
        return bool(win.child_window(title="Accept", control_type="Button").exists())
    except Exception:
        return False


def accept_call():
    win = find_window(WINDOW_TITLE)
    if win:
        click_button_by_names(win, ACCEPT_NAMES)


def reject_call():
    win = find_window(WINDOW_TITLE)
    if win:
        click_button_by_names(win, DECLINE_NAMES)


def call(contact_name: str) -> bool:
    win = focus_window(WINDOW_TITLE)
    if not win:
        return False
    try:
        send_keys("^e")  # Teams' global search shortcut
        time.sleep(0.4)
        send_keys(contact_name.replace(" ", "{SPACE}"))
        time.sleep(0.8)
        send_keys("{ENTER}")
        time.sleep(0.8)
        return click_button_by_names(win, ["Call", "Audio call", "Video call"])
    except Exception as e:
        print(f"[teams_skill] call error: {e}")
        return False
