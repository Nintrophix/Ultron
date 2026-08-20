"""
Anything the router's regex rules don't catch comes here. Two modes:

1. Plain question / open-ended request -> ask Claude, speak the answer.
2. "write/make/run some code that does X" -> ask Claude for a script,
   save it, execute it immediately (no confirmation, as requested), and
   speak a short summary of what happened.

NOTE ON RISK: this executes model-generated code on your machine with your
full user privileges and no confirmation step, by design. Keep an eye on
the console window where friday runs - stdout/stderr from every generated
script is printed there, and every command is logged to friday_log.txt.
"""

import re
import subprocess
import sys
import tempfile
import time
import pathlib

import anthropic

import config
from core.tts import speaker

_client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY) if config.ANTHROPIC_API_KEY else None

LOG_PATH = pathlib.Path("friday_log.txt")

CODE_TRIGGERS = ("write", "make", "code", "script", "program", "build", "generate")


def _log(line: str):
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {line}\n")


def handle(text: str):
    if _client is None:
        speaker.say("I don't have an Anthropic API key configured, so I can't handle open-ended requests.")
        return

    if any(word in text.lower() for word in CODE_TRIGGERS) and _looks_like_code_request(text):
        _handle_code_request(text)
    else:
        _handle_question(text)


def _looks_like_code_request(text: str) -> bool:
    return bool(re.search(r"\b(code|script|python|function|program)\b", text.lower()))


def _handle_question(text: str):
    speaker.say("One second.")
    try:
        resp = _client.messages.create(
            model=config.LLM_MODEL,
            max_tokens=300,
            system=(
                "You are FRIDAY, a terse voice assistant. Answer in 1-3 short "
                "spoken sentences. No markdown, no lists, plain spoken language."
            ),
            messages=[{"role": "user", "content": text}],
        )
        answer = "".join(b.text for b in resp.content if b.type == "text").strip()
        speaker.say(answer or "I don't have an answer for that.")
        _log(f"Q&A: {text!r} -> {answer!r}")
    except Exception as e:
        speaker.say("I couldn't reach the model.")
        print(f"[FRIDAY DEBUG] {e}")
        _log(f"Q&A ERROR: {e}")


def _handle_code_request(text: str):
    speaker.say("Writing that now.")
    try:
        resp = _client.messages.create(
            model=config.LLM_MODEL,
            max_tokens=config.LLM_MAX_TOKENS,
            system=(
                "You write short, self-contained Python 3 scripts for Windows. "
                "Respond with ONLY a single python code block, nothing else. "
                "The script must run non-interactively (no input()), print a "
                "brief result to stdout, and avoid destructive filesystem/network "
                "operations unless explicitly requested in the task."
            ),
            messages=[{"role": "user", "content": text}],
        )
        raw = "".join(b.text for b in resp.content if b.type == "text")
        code = _extract_code(raw)
        if not code:
            speaker.say("I couldn't produce runnable code for that.")
            return

        path = pathlib.Path(tempfile.gettempdir()) / f"friday_gen_{int(time.time())}.py"
        path.write_text(code, encoding="utf-8")
        _log(f"CODE REQUEST: {text!r}\n--- generated ---\n{code}\n-----------------")

        result = subprocess.run(
            [sys.executable, str(path)],
            capture_output=True,
            text=True,
            timeout=30,
        )
        output = (result.stdout or result.stderr or "").strip()
        summary = output.splitlines()[-1] if output else "Done, no output."
        speaker.say(f"Done. {summary[:200]}")
        _log(f"RESULT (exit {result.returncode}): {output}")

    except subprocess.TimeoutExpired:
        speaker.say("That script took too long and I stopped it.")
    except Exception as e:
        speaker.say("Something went wrong running that.")
        _log(f"CODE ERROR: {e}")


def _extract_code(raw: str) -> str:
    m = re.search(r"```(?:python)?\s*(.*?)```", raw, re.DOTALL)
    return m.group(1).strip() if m else raw.strip()


def suggest_reply(last_message: str) -> str:
    """Used by whatsapp_skill when the user says 'reply to X' with no
    dictated text - generates a short, neutral reply."""
    if _client is None or not last_message:
        return "Got it, thanks!"
    try:
        resp = _client.messages.create(
            model=config.LLM_MODEL,
            max_tokens=60,
            system="Write one short, casual WhatsApp reply. No quotes, no explanation.",
            messages=[{"role": "user", "content": f"Message received: {last_message}"}],
        )
        return "".join(b.text for b in resp.content if b.type == "text").strip()
    except Exception:
        return "Got it, thanks!"
