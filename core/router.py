"""
Routes a transcribed command string to the right skill.

Matching is deliberately simple (regex/keyword based) rather than a full
NLU stack, because it needs to respond fast and offline. Anything that
doesn't match a known pattern falls through to the LLM fallback, which can
answer questions, write code, and execute it.
"""

import re

from core.tts import speaker
from core import llm_fallback
from skills import (
    apps_skill,
    reminders_skill,
    spotify_skill,
    whatsapp_skill,
    discord_skill,
    teams_skill,
    phonelink_skill,
    system_skill,
)

# Each rule: (regex, handler(match) -> None)
RULES = []


def rule(pattern):
    def deco(fn):
        RULES.append((re.compile(pattern, re.IGNORECASE), fn))
        return fn
    return deco


# ---------------------------------------------------------------- apps ---
@rule(r"^open (?:the )?(?:app |application )?(.+)$")
def _open_app_or_link(m):
    target = m.group(1).strip()
    if target.startswith("http") or "." in target.split()[0]:
        apps_skill.open_link(target)
        speaker.say(f"Opening {target}")
    else:
        ok = apps_skill.open_app(target)
        speaker.say(f"Opening {target}" if ok else f"I don't have {target} mapped. Add it to config.APPS.")


@rule(r"^(?:go to|launch|start) (.+)$")
def _launch(m):
    _open_app_or_link(m)


@rule(r"^close (.+)$")
def _close_app(m):
    target = m.group(1).strip()
    ok = apps_skill.close_app(target)
    speaker.say(f"Closed {target}" if ok else f"Couldn't find {target} running.")


# ----------------------------------------------------------- reminders ---
@rule(r"^remind me to (.+?) (?:in|at) (.+)$")
def _remind(m):
    text, when = m.group(1), m.group(2)
    ok, when_str = reminders_skill.set_reminder(text, when)
    speaker.say(f"Reminder set: {text}, {when_str}" if ok else "Couldn't parse that time.")


@rule(r"^set an? alarm for (.+)$")
def _alarm(m):
    when = m.group(1)
    ok, when_str = reminders_skill.set_alarm(when)
    speaker.say(f"Alarm set for {when_str}" if ok else "Couldn't parse that time.")


@rule(r"^stop(?: the)? alarm$")
def _stop_alarm(m):
    reminders_skill.stop_alarm()
    speaker.say("Alarm stopped.")


# ------------------------------------------------------------- spotify ---
@rule(r"^play (.+?) on spotify$")
def _play_song(m):
    song = m.group(1)
    ok = spotify_skill.play(song)
    speaker.say(f"Playing {song}" if ok else f"Couldn't find {song} on Spotify.")

@rule(r"^play (.+)$")
def _play_song_default(m):
    _play_song(m)

@rule(r"^(pause|resume|next( song)?|previous( song)?|skip)( music)?$")
def _music_control(m):
    cmd = m.group(1).lower()
    spotify_skill.control(cmd)
    speaker.say("")  # silent ack, keep it snappy


# ------------------------------------------------------------ whatsapp ---
@rule(r"^(?:reply to|message|text) (.+?) on whatsapp(?: saying (.+))?$")
def _whatsapp_send(m):
    contact, message = m.group(1), m.group(2)
    if not message:
        # no dictated text -> generate a short contextual reply
        message = llm_fallback.suggest_reply(whatsapp_skill.get_last_message(contact))
    ok = whatsapp_skill.send_message(contact, message)
    speaker.say(f"Sent to {contact}" if ok else f"Couldn't message {contact}.")


# ----------------------------------------------------------- calls in ---
@rule(r"^(accept|answer)(?: the)? call$")
def _accept_call(m):
    platform = _find_ringing_platform()
    if platform:
        platform.accept_call()
        speaker.say("Call accepted.")
    else:
        speaker.say("I don't see an incoming call right now.")


@rule(r"^(reject|decline|hang up on)(?: the)? call$")
def _reject_call(m):
    platform = _find_ringing_platform()
    if platform:
        platform.reject_call()
        speaker.say("Call declined.")
    else:
        speaker.say("I don't see an incoming call right now.")


def _find_ringing_platform():
    for p in (discord_skill, teams_skill, phonelink_skill):
        if p.is_ringing():
            return p
    return None


# ---------------------------------------------------------- calls out ---
@rule(r"^call (.+?)(?: on (discord|teams|phone|whatsapp))?$")
def _call_out(m):
    name, platform = m.group(1), (m.group(2) or "phone").lower()
    handlers = {
        "discord": discord_skill.call,
        "teams": teams_skill.call,
        "phone": phonelink_skill.call,
    }
    fn = handlers.get(platform, phonelink_skill.call)
    ok = fn(name)
    speaker.say(f"Calling {name}" if ok else f"Couldn't place that call.")


# ------------------------------------------------------------- system ---
@rule(r"^(lock (?:the )?(?:pc|computer)|lock screen)$")
def _lock(m):
    system_skill.lock()

@rule(r"^volume (up|down|mute)$")
def _volume(m):
    system_skill.volume(m.group(1))
    speaker.say("")


# ---------------------------------------------------------------------- #
def route(text: str):
    text = text.strip().lower()
    if not text:
        return
    for pattern, handler in RULES:
        match = pattern.match(text)
        if match:
            try:
                handler(match)
            except Exception as e:
                speaker.say("That didn't work.")
                print(f"[ROUTER ERROR] {e}")
            return

    # No rule matched -> hand off to the LLM for open-ended requests,
    # including "write me code to do X and run it".
    llm_fallback.handle(text)
