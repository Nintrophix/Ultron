"""
FRIDAY — central configuration.

Fill in the values below. Anything marked REQUIRED must be set before the
assistant will work. Everything else has a sane default.
"""

import os


# Wake word / speech
WAKE_WORD = "friday"                 # word/phrase that triggers listening
VOSK_MODEL_PATH = os.environ.get(
    "VOSK_MODEL_PATH",
    # NOTE: relocate this folder outside OneDrive to avoid the cloud-sync
    # freeze issue - e.g. move it to C:\friday\vosk-model-small-en-in-0.4
    # and update this path to match. Left pointing at the bundled folder
    # for now so it runs as-is.
    r"C:\Users\krith\projects\ultron\vosk-model-small-en-in-0.4"
)
MIC_SAMPLE_RATE = 16000
SILENCE_TIMEOUT_SEC = 2.0            # how long to wait for silence = end of command


# Text-to-speech
TTS_RATE = 190                       # words per minute, higher = snappier
TTS_VOLUME = 1.0
TTS_VOICE_HINT = "zira"              # substring match against installed voice names
                                      # (Windows has "Microsoft Zira" - female voice, matches FRIDAY)


# Anthropic API (used for open-ended requests / "write me code and run it")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "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")
LLM_MODEL = "claude-sonnet-4-6"
LLM_MAX_TOKENS = 1024


# Known applications — map spoken name -> how to launch it.
# Add anything you want; value can be a full path, a bare exe name that's
# on PATH, or a shell command.
APPS = {
    "chrome":        "chrome.exe",
    "notepad":       "notepad.exe",
    "explorer":      "explorer.exe",
    "calculator":    "calc.exe",
    "spotify":       "spotify.exe",
    "discord":       "discord.exe",
    "teams":         "ms-teams.exe",
    "vs code":       "code.exe",
    "visual studio code": "code.exe",
    "word":          "winword.exe",
    "excel":         "excel.exe",
    "terminal":      "wt.exe",
    "cmd":           "cmd.exe",
    "phone link":    "ms-phone.exe",
    "task manager":  "taskmgr.exe",
    "settings":      "ms-settings:",
}


# Spotify (create an app at https://developer.spotify.com/dashboard)

SPOTIFY_CLIENT_ID = os.environ.get("SPOTIFY_CLIENT_ID", "e76f9438ea1c492eac32c61acfa3a317")
SPOTIFY_CLIENT_SECRET = os.environ.get("SPOTIFY_CLIENT_SECRET", "dc876fb8666d41f79f629767cc2e3dfb")
SPOTIFY_REDIRECT_URI = "http://127.0.0.1:8888/callback"
SPOTIFY_SCOPE = "user-modify-playback-state user-read-playback-state user-read-currently-playing"


# WhatsApp Web — persistent Chrome profile so you only scan the QR once

WHATSAPP_CHROME_PROFILE_DIR = os.environ.get(
    "WHATSAPP_CHROME_PROFILE_DIR",
    r"C:\friday\whatsapp_chrome_profile"
)


# ADB (Android calls via USB or wireless debugging)

ADB_PATH = os.environ.get("ADB_PATH", "adb")   # assumes adb is on PATH


# Contacts — spoken name -> phone number / platform handle, used for "call X"

CONTACTS = {
    # "mom": {"phone": "+15551234567"},
    # "raj": {"phone": "+919876543210", "discord": "raj#1234"},
}


# UI colors — FRIDAY palette (cool blue/cyan, Stark-HUD style)

COLORS = {
    "bg":         "#050609",
    "panel":      "#0a0d12",
    "red":        "#00c8ff",     # kept key name "red" so gui/hud.py needs no changes
    "red_bright": "#7fe9ff",
    "red_dark":   "#003a4d",
    "steel":      "#3a4a52",
    "steel_dark": "#1a2226",
    "text":       "#cdf3ff",
    "text_dim":   "#4a7a8a",
}
