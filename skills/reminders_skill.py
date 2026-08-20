import threading
import time

import dateparser
from apscheduler.schedulers.background import BackgroundScheduler

try:
    import winsound
except ImportError:
    winsound = None  # non-Windows dev/testing

from core.tts import speaker

_scheduler = BackgroundScheduler()
_scheduler.start()

_alarm_ringing = threading.Event()


def _parse_when(when_text: str):
    dt = dateparser.parse(
        when_text,
        settings={"PREFER_DATES_FROM": "future", "RELATIVE_BASE": None},
    )
    return dt


def set_reminder(text: str, when_text: str):
    dt = _parse_when(when_text)
    if not dt:
        return False, ""
    _scheduler.add_job(_fire_reminder, "date", run_date=dt, args=[text])
    return True, dt.strftime("%A %I:%M %p")


def _fire_reminder(text: str):
    speaker.say_now(f"Reminder: {text}")


def set_alarm(when_text: str):
    dt = _parse_when(when_text)
    if not dt:
        return False, ""
    _scheduler.add_job(_fire_alarm, "date", run_date=dt)
    return True, dt.strftime("%I:%M %p")


def _fire_alarm():
    _alarm_ringing.set()
    speaker.say_now("Alarm. Say 'stop alarm' to dismiss.")

    def _loop():
        while _alarm_ringing.is_set():
            if winsound:
                winsound.Beep(880, 400)
            time.sleep(0.3)

    threading.Thread(target=_loop, daemon=True).start()


def stop_alarm():
    _alarm_ringing.clear()
