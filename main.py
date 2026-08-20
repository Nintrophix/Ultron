"""
FRIDAY — voice-controlled desktop assistant.

Run this on Windows with:  python main.py
See README.md for one-time setup (Vosk model, API keys, WhatsApp QR, etc).
"""

import threading

from core.stt import ContinuousListener
from core.tts import speaker
from core.router import route
from gui.hud import HUD


def main():
    hud = HUD()

    def on_command(text: str):
        hud.set_text(f"> {text}")
        route(text)

    def on_state_change(state: str):
        hud.set_state(state)

    listener = ContinuousListener(on_command=on_command, on_state_change=on_state_change)

    t = threading.Thread(target=listener.run, daemon=True)
    t.start()

    speaker.say("FRIDAY online.")
    hud.run()  # blocks on the main thread (tkinter requirement)


if __name__ == "__main__":
    main()
