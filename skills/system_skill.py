import ctypes

from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume


def lock():
    ctypes.windll.user32.LockWorkStation()


def _volume_interface():
    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    return cast(interface, POINTER(IAudioEndpointVolume))


def volume(direction: str):
    vol = _volume_interface()
    if direction == "mute":
        vol.SetMute(1, None)
        return
    current = vol.GetMasterVolumeLevelScalar()
    step = 0.1 if direction == "up" else -0.1
    vol.SetMasterVolumeLevelScalar(max(0.0, min(1.0, current + step)), None)
