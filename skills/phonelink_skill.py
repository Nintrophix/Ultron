"""
Android call control. ADB is the primary path - it's far more reliable
than clicking around Phone Link's UI, and works over USB or wireless
debugging. Requires:
  1. USB debugging enabled on the phone (Settings > Developer options)
  2. `adb devices` shows your phone as authorized (accept the one-time
     RSA key prompt on the phone the first time you connect)

Falls back to Phone Link UI automation for accept/reject if no ADB
device is found (e.g. phone only linked via Bluetooth/Wi-Fi through
Phone Link, not paired to adb).
"""

import subprocess

import config
from skills._win_automation import find_window, click_button_by_names

PHONE_LINK_TITLE = ".*Phone Link.*"


def _adb(*args) -> str:
    try:
        result = subprocess.run(
            [config.ADB_PATH, *args],
            capture_output=True, text=True, timeout=5,
        )
        return result.stdout
    except Exception as e:
        print(f"[phonelink_skill] adb error: {e}")
        return ""


def _adb_available() -> bool:
    out = _adb("devices")
    lines = [l for l in out.splitlines()[1:] if l.strip()]
    return any("device" in l and "unauthorized" not in l for l in lines)


def is_ringing() -> bool:
    if _adb_available():
        out = _adb("shell", "dumpsys", "telephony.registry")
        return "mCallState=1" in out
    win = find_window(PHONE_LINK_TITLE)
    if not win or not win.exists():
        return False
    try:
        return bool(win.child_window(title="Accept call", control_type="Button").exists())
    except Exception:
        return False


def accept_call():
    if _adb_available():
        _adb("shell", "input", "keyevent", "KEYCODE_CALL")
        return
    win = find_window(PHONE_LINK_TITLE)
    if win:
        click_button_by_names(win, ["Accept call", "Accept"])


def reject_call():
    if _adb_available():
        _adb("shell", "input", "keyevent", "KEYCODE_ENDCALL")
        return
    win = find_window(PHONE_LINK_TITLE)
    if win:
        click_button_by_names(win, ["Decline call", "Decline"])


def call(name_or_number: str) -> bool:
    number = name_or_number
    contact = config.CONTACTS.get(name_or_number.strip().lower())
    if contact and "phone" in contact:
        number = contact["phone"]

    if _adb_available():
        _adb("shell", "am", "start", "-a", "android.intent.action.CALL", "-d", f"tel:{number}")
        return True

    win = find_window(PHONE_LINK_TITLE)
    if win:
        # Fallback: Phone Link doesn't have a reliable "type a number and dial"
        # automation path across versions - ADB is strongly recommended for
        # outbound calls.
        print("[phonelink_skill] No adb device; outbound call via Phone Link UI is not implemented.")
    return False
