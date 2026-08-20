"""
Small always-on-top HUD in FRIDAY's blue/cyan palette: a pulsing ring that
speeds up while "thinking" and a status line showing the last heard
command and response. Runs on the main thread; other threads push state
updates through a thread-safe queue.
"""

import queue
import tkinter as tk

import config

C = config.COLORS


class HUD:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("FRIDAY")
        self.root.geometry("340x340+40+40")
        self.root.configure(bg=C["bg"])
        self.root.attributes("-topmost", True)
        self.root.overrideredirect(True)  # borderless
        self.root.attributes("-alpha", 0.92)

        self.canvas = tk.Canvas(self.root, width=340, height=260, bg=C["bg"], highlightthickness=0)
        self.canvas.pack()

        self.status_var = tk.StringVar(value="IDLE")
        self.status_label = tk.Label(
            self.root, textvariable=self.status_var, fg=C["red_bright"], bg=C["bg"],
            font=("Consolas", 12, "bold")
        )
        self.status_label.pack(pady=(0, 4))

        self.text_var = tk.StringVar(value="")
        self.text_label = tk.Label(
            self.root, textvariable=self.text_var, fg=C["text"], bg=C["bg"],
            font=("Consolas", 9), wraplength=320, justify="left"
        )
        self.text_label.pack()

        # allow dragging the borderless window
        self.root.bind("<ButtonPress-1>", self._start_move)
        self.root.bind("<B1-Motion>", self._do_move)
        self._drag = {"x": 0, "y": 0}

        self._angle = 0
        self._pulse_speed = 2
        self._state = "idle"
        self._queue: "queue.Queue" = queue.Queue()

        self._draw_ring()
        self._animate()
        self.root.after(100, self._poll_queue)

    def _start_move(self, event):
        self._drag["x"], self._drag["y"] = event.x, event.y

    def _do_move(self, event):
        x = self.root.winfo_x() + event.x - self._drag["x"]
        y = self.root.winfo_y() + event.y - self._drag["y"]
        self.root.geometry(f"+{x}+{y}")

    def _draw_ring(self):
        self.canvas.delete("ring")
        cx, cy, r = 170, 130, 90
        color = C["red_bright"] if self._state != "idle" else C["red"]
        width = 4 if self._state == "listening" else 2
        self.canvas.create_oval(cx - r, cy - r, cx + r, cy + r, outline=C["steel_dark"], width=1, tags="ring")
        extent = 300 if self._state == "thinking" else 360
        self.canvas.create_arc(
            cx - r, cy - r, cx + r, cy + r,
            start=self._angle, extent=extent,
            outline=color, width=width, style="arc", tags="ring",
        )
        # inner core
        core_r = 30 + (6 if self._state == "listening" else 0)
        self.canvas.create_oval(
            cx - core_r, cy - core_r, cx + core_r, cy + core_r,
            fill=C["red_dark"], outline=color, width=2, tags="ring",
        )

    def _animate(self):
        speed = {"idle": 1, "listening": 4, "thinking": 8}.get(self._state, 1)
        self._angle = (self._angle + speed) % 360
        self._draw_ring()
        self.root.after(30, self._animate)

    def _poll_queue(self):
        try:
            while True:
                kind, value = self._queue.get_nowait()
                if kind == "state":
                    self._state = value
                    self.status_var.set(value.upper())
                elif kind == "text":
                    self.text_var.set(value)
        except queue.Empty:
            pass
        self.root.after(100, self._poll_queue)

    # thread-safe setters, call these from any thread
    def set_state(self, state: str):
        self._queue.put(("state", state))

    def set_text(self, text: str):
        self._queue.put(("text", text))

    def run(self):
        self.root.mainloop()
