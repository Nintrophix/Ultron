# FRIDAY — voice-controlled desktop assistant

A hands-free assistant for Windows: wake word "FRIDAY", then speak a
command. No mouse, no keyboard, no confirmation prompts for normal
operation. Built entirely with local/offline components on the hot path
(wake word + speech-to-text + text-to-speech) so responses stay fast; the
LLM is only called for open-ended requests and code generation.

## 1. Install Python dependencies

Requires Python 3.10+ on Windows.

```
pip install -r requirements.txt
```

## 2. Download the offline speech model (one-time)

Download the small English Vosk model (~50MB):
https://alphacephei.com/vosk/models -> `vosk-model-small-en-us-0.15`

Unzip it somewhere, e.g. `C:\friday\vosk-model-small-en-us-0.15`, and set
`VOSK_MODEL_PATH` in `config.py` (or as an environment variable) to that
folder.

## 3. Set API keys (environment variables, or edit config.py directly)

| Variable | Used for |
|---|---|
| `ANTHROPIC_API_KEY` | open-ended Q&A and "write me code and run it" |
| `SPOTIFY_CLIENT_ID` / `SPOTIFY_CLIENT_SECRET` | Spotify playback (create an app at https://developer.spotify.com/dashboard, add `http://127.0.0.1:8888/callback` as a redirect URI) |

Spotify's first launch opens a browser for OAuth consent — that's a
one-time Spotify requirement, not something this app adds. After that,
the token is cached and it's silent.

## 4. WhatsApp (one-time QR scan)

First run opens a Chrome window to web.whatsapp.com using a dedicated,
persistent profile folder (`config.WHATSAPP_CHROME_PROFILE_DIR`). Scan the
QR code from your phone once. Every run after that reuses the saved
session — no repeat scans.

## 5. Android calls (ADB — recommended over Phone Link UI automation)

1. On your phone: Settings → About phone → tap "Build number" 7 times to
   unlock Developer options → enable **USB debugging**.
2. Install platform-tools (`adb`) and make sure it's on your PATH, or set
   `ADB_PATH` in config.py to the full path of `adb.exe`.
3. Connect via USB (or set up wireless debugging) and run `adb devices`
   once — accept the RSA key prompt that appears on the phone.

If no ADB device is available, the app falls back to UI automation on the
Microsoft Phone Link app for accept/reject (outbound dialing needs ADB).

## 6. Discord / Teams calls

These are automated by driving the desktop client's UI (simulated clicks
via Windows UI Automation) — **not** by using Discord's API with an
account token. Automating a personal Discord account through the API/a
token is a "self-bot," which is against Discord's Terms of Service and
risks the account being disabled; UI automation sidesteps that because
it's just clicking the same buttons a human would.

Button/control names can shift between app versions. If accept/decline
stops working, open a Python shell and run:

```python
from pywinauto import Desktop
Desktop(backend="uia").window(title_re=".*Discord.*").print_control_identifiers()
```

...to see the current control names, then update `ACCEPT_NAMES` /
`DECLINE_NAMES` in `skills/discord_skill.py` or `teams_skill.py`.

## 7. Add your apps and contacts

Edit `config.py`:
- `APPS` — spoken name → executable, for "open X"
- `CONTACTS` — spoken name → phone number, for "call X"

## 8. Run it

```
python main.py
```

Say **"FRIDAY"**, wait for the ring to brighten, then speak a command:

- "FRIDAY, open Chrome"
- "FRIDAY, open github.com"
- "FRIDAY, remind me to take a break in 20 minutes"
- "FRIDAY, set an alarm for 7 AM"
- "FRIDAY, play Midnight City on Spotify"
- "FRIDAY, pause"
- "FRIDAY, reply to Raj on WhatsApp saying I'm on my way"
- "FRIDAY, accept the call"
- "FRIDAY, call mom"
- "FRIDAY, write a script that renames all files in Downloads to lowercase and run it"

## Important notes on how this behaves

- **Zero confirmation prompts**, as requested — including for model-generated
  code, which runs immediately with your full user privileges. Everything it
  runs is logged to `friday_log.txt` in the project folder and printed to the
  console, so you have a record of exactly what executed.
- Speech recognition can mishear things, especially with background noise.
  Since there's no confirm step, a misheard "call mom" vs "call Tom" will
  just dial the wrong person — worth knowing going in.
- Run this from a normal (non-admin) terminal unless a specific skill needs
  elevation; running everything as admin would let generated code do more
  than it needs to.

## Extending it

Add new commands in `core/router.py` with the `@rule(r"...")` decorator, or
new integrations as a file in `skills/`. Anything not matched by a rule
automatically falls through to the LLM for a best-effort attempt.
