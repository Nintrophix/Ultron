"""
Shared pywinauto helpers for driving desktop apps that don't expose a
scriptable API (Discord, Teams desktop clients).

These use the UI Automation backend and match controls by name/title
rather than screen coordinates, which survives window resizing and is
more robust than pixel-based clicking - but control names can still shift
between app versions. If a button stops being found, run:

    python -m pywinauto.actionlogger

or use `app.window(title_re=".*").print_control_identifiers()` from a
python shell to see the current control names on your installed version,
and update the NAME lists below.
"""

from pywinauto import Application, Desktop
from pywinauto.findwindows import ElementNotFoundError


def find_window(title_re: str, backend="uia"):
    try:
        return Desktop(backend=backend).window(title_re=title_re)
    except ElementNotFoundError:
        return None


def window_exists(title_re: str) -> bool:
    win = find_window(title_re)
    return bool(win and win.exists())


def click_button_by_names(window, candidate_names):
    """Try each candidate control name in turn; click the first that exists."""
    for name in candidate_names:
        try:
            btn = window.child_window(title=name, control_type="Button")
            if btn.exists():
                btn.click_input()
                return True
        except Exception:
            continue
    return False


def focus_window(title_re: str):
    win = find_window(title_re)
    if win and win.exists():
        win.set_focus()
        return win
    return None
