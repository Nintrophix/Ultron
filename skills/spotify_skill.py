import spotipy
from spotipy.oauth2 import SpotifyOAuth

import config

_sp = None


def _client():
    global _sp
    if _sp is None:
        _sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=config.SPOTIFY_CLIENT_ID,
            client_secret=config.SPOTIFY_CLIENT_SECRET,
            redirect_uri=config.SPOTIFY_REDIRECT_URI,
            scope=config.SPOTIFY_SCOPE,
            open_browser=True,   # only opens once, then token is cached
        ))
    return _sp


def _active_device_id():
    sp = _client()
    devices = sp.devices().get("devices", [])
    if not devices:
        return None
    # prefer an already-active device, else the first available
    for d in devices:
        if d.get("is_active"):
            return d["id"]
    return devices[0]["id"]


def play(query: str) -> bool:
    try:
        sp = _client()
        results = sp.search(q=query, type="track", limit=1)
        items = results.get("tracks", {}).get("items", [])
        if not items:
            return False
        uri = items[0]["uri"]
        device_id = _active_device_id()
        sp.start_playback(device_id=device_id, uris=[uri])
        return True
    except Exception as e:
        print(f"[spotify_skill] play error: {e}")
        return False


def control(cmd: str):
    try:
        sp = _client()
        device_id = _active_device_id()
        if cmd == "pause":
            sp.pause_playback(device_id=device_id)
        elif cmd == "resume":
            sp.start_playback(device_id=device_id)
        elif cmd.startswith("next") or cmd == "skip":
            sp.next_track(device_id=device_id)
        elif cmd.startswith("previous"):
            sp.previous_track(device_id=device_id)
    except Exception as e:
        print(f"[spotify_skill] control error: {e}")
