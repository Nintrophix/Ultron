"""
Offline TTS. pyttsx3 wraps Windows SAPI5, which responds in tens of
milliseconds with no network round-trip - important for "quick responses".
"""

import threading
import queue

import pyttsx3

import config


class Speaker:
    def __init__(self):
        self._engine = pyttsx3.init()
        self._engine.setProperty("rate", config.TTS_RATE)
        self._engine.setProperty("volume", config.TTS_VOLUME)

        for voice in self._engine.getProperty("voices"):
            if config.TTS_VOICE_HINT.lower() in voice.name.lower():
                self._engine.setProperty("voice", voice.id)
                break

        self._q: "queue.Queue[str]" = queue.Queue()
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()

    def _worker(self):
        while True:
            text = self._q.get()
            if text is None:
                continue
            try:
                self._engine.say(text)
                self._engine.runAndWait()
            except Exception as e:
                print(f"[TTS error] {e}")

    def say(self, text: str):
        """Non-blocking: queues text and returns immediately."""
        print(f"[FRIDAY] {text}")
        self._q.put(text)

    def say_now(self, text: str):
        """Clears the queue first so this is spoken immediately - use for
        urgent things like 'incoming call'."""
        with self._q.mutex:
            self._q.queue.clear()
        self.say(text)


speaker = Speaker()
