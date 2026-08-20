"""
Discord skill - driven entirely through the desktop client's UI, never
through the account API with a user token. Automating a personal Discord
account via the client API/token is a "self-bot," which is against
Discord's Terms of Service and risks the account being disabled - UI
automation (simulating the clicks a human would make) avoids that.
"""

import time

from pywinauto.keyboard import send_keys

from skills._win_automation import find_window, window_exists, click_button_by_names, focus_window

CALL_WINDOW_TITLE = ".*Discord.*"
ACCEPT_NAMES = ["Accept", "Join Call", "Answer"]
DECLINE_NAMES = ["Decline", "Ignore", "Dismiss"]


def is_ringing() -> bool:
    win = find_window(CALL_WINDOW_TITLE)
    if not win or not win.exists():
        return False
    # A ringing call surfaces an Accept/Decline pair somewhere in the tree.
    try:
        return bool(win.child_window(title="Accept", control_type="Button").exists())
    except Exception:
        return False


def accept_call():
    win = find_window(CALL_WINDOW_TITLE)
    if win:
        click_button_by_names(win, ACCEPT_NAMES)


def reject_call():
    win = find_window(CALL_WINDOW_TITLE)
    if win:
        click_button_by_names(win, DECLINE_NAMES)


def call(contact_name: str) -> bool:
    """Focuses Discord, opens the DM with contact_name via the quick-switcher
    (Ctrl+K), and starts a call."""
    win = focus_window(CALL_WINDOW_TITLE)
    if not win:
        return False
    try:
        send_keys("^k")
        time.sleep(0.4)
        send_keys(contact_name.replace(" ", "{SPACE}"))
        time.sleep(0.6)
        send_keys("{ENTER}")
        time.sleep(0.6)
        # start a call in the now-open DM
        return click_button_by_names(win, ["Start Voice Call", "Call"])
    except Exception as e:
        print(f"[discord_skill] call error: {e}")
        return False
