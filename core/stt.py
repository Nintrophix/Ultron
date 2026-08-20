"""
Always-on offline speech recognition using Vosk.

Vosk streams partial results as you speak, so we can detect the wake word
("friday") with very low latency, then keep listening until the user goes
silent and treat that stretch of audio as the command.

Download a model once (see README) - the "small" English model is ~50MB
and is plenty fast for this use case; it runs entirely on-device so there's
no network latency on the hot path.
"""

import json
import queue
import time

import sounddevice as sd
import vosk

import config

vosk.SetLogLevel(-1)


class ContinuousListener:
    """
    Runs forever. Calls `on_command(text)` every time it hears the wake
    word followed by a spoken command.
    """

    def __init__(self, on_command, on_state_change=None):
        self.on_command = on_command
        self.on_state_change = on_state_change  # optional: fn(str) for GUI, e.g. "idle"/"listening"/"thinking"

        self._model = vosk.Model(config.VOSK_MODEL_PATH)
        self._rec = vosk.KaldiRecognizer(self._model, config.MIC_SAMPLE_RATE)
        self._audio_q: "queue.Queue[bytes]" = queue.Queue()

        self._armed = False          # True once wake word has been heard
        self._last_speech_time = 0.0
        self._buffer_text = ""

    def _audio_callback(self, indata, frames, time_info, status):
        self._audio_q.put(bytes(indata))

    def _set_state(self, state):
        if self.on_state_change:
            self.on_state_change(state)

    def run(self):
        self._set_state("idle")
        with sd.RawInputStream(
            samplerate=config.MIC_SAMPLE_RATE,
            blocksize=8000,
            dtype="int16",
            channels=1,
            callback=self._audio_callback,
        ):
            print("[FRIDAY] Listening for wake word...")
            while True:
                data = self._audio_q.get()

                if self._rec.AcceptWaveform(data):
                    result = json.loads(self._rec.Result())
                    text = result.get("text", "").strip()
                    self._handle_final(text)
                else:
                    partial = json.loads(self._rec.PartialResult())
                    ptext = partial.get("partial", "").strip()
                    self._handle_partial(ptext)

    def _handle_partial(self, ptext):
        if not self._armed and config.WAKE_WORD in ptext.lower():
            self._armed = True
            self._set_state("listening")
            self._last_speech_time = time.time()
        elif self._armed and ptext:
            self._last_speech_time = time.time()

        # silence timeout while armed but nothing finalized yet is handled
        # in _handle_final via the recognizer's own segmentation; Vosk
        # finalizes a result after a pause automatically.

    def _handle_final(self, text):
        if not text:
            return
        low = text.lower()

        if not self._armed:
            if config.WAKE_WORD in low:
                after = low.split(config.WAKE_WORD, 1)[1].strip()
                if after:
                    # wake word + command in the same breath
                    self._set_state("thinking")
                    self.on_command(after)
                    self._set_state("idle")
                else:
                    self._armed = True
                    self._set_state("listening")
            return

        # We were armed (wake word already heard) - this finalized text
        # is the command itself.
        self._armed = False
        self._set_state("thinking")
        self.on_command(low)
        self._set_state("idle")
