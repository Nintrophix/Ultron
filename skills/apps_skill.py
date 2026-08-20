import os
import subprocess
import webbrowser

import psutil

import config


def open_app(name: str) -> bool:
    name = name.strip().lower()
    target = config.APPS.get(name)
    if not target:
        # last resort: try the spoken name directly as an executable
        target = name if name.endswith(".exe") else f"{name}.exe"
    try:
        if target.startswith("ms-"):
            os.startfile(target)  # windows URI-scheme apps like ms-settings:
        else:
            subprocess.Popen(target, shell=True)
        return True
    except Exception as e:
        print(f"[apps_skill] open_app error: {e}")
        return False


def open_link(url: str) -> bool:
    if not url.startswith("http"):
        url = "https://" + url
    try:
        webbrowser.open(url)
        return True
    except Exception as e:
        print(f"[apps_skill] open_link error: {e}")
        return False


def close_app(name: str) -> bool:
    name = name.strip().lower()
    found = False
    for proc in psutil.process_iter(["name"]):
        pname = (proc.info["name"] or "").lower()
        if name in pname:
            try:
                proc.terminate()
                found = True
            except Exception:
                pass
    return found
