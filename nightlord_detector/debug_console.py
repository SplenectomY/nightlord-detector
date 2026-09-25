"""Second-window debug console for live OCR and assignment."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable

from .predict import load_tables


class DebugConsole:
    def __init__(
        self,
        root: tk.Tk,
        on_assign_n1: Callable[[str], None],
        on_assign_n2: Callable[[str], None],
        on_depth: Callable[[str], None],
        on_reset: Callable[[], None],
        on_roi: Callable[[float, float, float, float], None],
        on_toggle_scan: Callable[[bool], None],
        initial_roi: tuple[float, float, float, float],
    ):
        self.win = tk.Toplevel(root)
        self.win.title("nightlord-detector debug")
        self.win.geometry("720x640+580+40")
        self.win.configure(bg="#111111")
        self.win.protocol("WM_DELETE_WINDOW", self.win.withdraw)

        tables = load_tables()
        n1_values = [f"{k} — {v['label']}" for k, v in tables["night1"].items()]
        n2_values = [f"{k} — {v['label']}" for k, v in tables["night2"].items()]

        pad = {"padx": 8, "pady": 4}

        ttk.Label(self.win, text="Live OCR / matcher").pack(anchor="w", **pad)
        self.ocr_var = tk.StringVar(value="engine: starting...")
        ttk.Label(self.win, textvariable=self.ocr_var, wraplength=680).pack(anchor="w", **pad)

        self.rank = tk.Text(self.win, height=8, width=90, bg="#1c1c1c", fg="#dddddd")
        self.rank.pack(fill="x", **pad)

        row = ttk.Frame(self.win)
        row.pack(fill="x", **pad)
        ttk.Label(row, text="Night 1").pack(side="left")
        self.n1 = ttk.Combobox(row, values=["(auto)"] + n1_values, width=48, state="readonly")
        self.n1.set("(auto)")
        self.n1.pack(side="left", padx=6)
        self.n1.bind("<<ComboboxSelected>>", lambda _e: self._fire_n1(on_assign_n1))

        row2 = ttk.Frame(self.win)
        row2.pack(fill="x", **pad)
        ttk.Label(row2, text="Night 2").pack(side="left")
        self.n2 = ttk.Combobox(row2, values=["(auto / unseen)"] + n2_values, width=48, state="readonly")
        self.n2.set("(auto / unseen)")
        self.n2.pack(side="left", padx=6)
        self.n2.bind("<<ComboboxSelected>>", lambda _e: self._fire_n2(on_assign_n2))

        row3 = ttk.Frame(self.win)
        row3.pack(fill="x", **pad)
        ttk.Label(row3, text="Depth").pack(side="left")
        self.depth = ttk.Combobox(
            row3,
            values=["any", "d1", "d2", "d3", "d4", "d5"],
            width=8,
            state="readonly",
        )
        self.depth.set("any")
        self.depth.pack(side="left", padx=6)
        self.depth.bind("<<ComboboxSelected>>", lambda _e: on_depth(self.depth.get()))

        btns = ttk.Frame(self.win)
        btns.pack(fill="x", **pad)
        ttk.Button(btns, text="Reset run", command=on_reset).pack(side="left", padx=4)
        self.scan_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            btns,
            text="Scan screen",
            variable=self.scan_var,
            command=lambda: on_toggle_scan(self.scan_var.get()),
        ).pack(side="left", padx=4)

        ttk.Label(self.win, text="Nameplate ROI (fractions of the monitor)").pack(anchor="w", **pad)
        self.sliders: dict[str, tk.Scale] = {}
        names = ("left", "top", "width", "height")
        for name, value in zip(names, initial_roi):
            slider = tk.Scale(
                self.win,
                from_=0.0,
                to=1.0,
                resolution=0.01,
                orient="horizontal",
                label=name,
                length=660,
                command=lambda _v, cb=on_roi: cb(
                    self.sliders["left"].get(),
                    self.sliders["top"].get(),
                    self.sliders["width"].get(),
                    self.sliders["height"].get(),
                ),
            )
            slider.set(value)
            slider.pack(fill="x", padx=8)
            self.sliders[name] = slider

        ttk.Label(self.win, text="Log").pack(anchor="w", **pad)
        self.log = tk.Text(self.win, height=10, width=90, bg="#141414", fg="#c8f5c8")
        self.log.pack(fill="both", expand=True, **pad)

        ttk.Label(
            self.win,
            text="F6 assign Night 1   F7 assign Night 2   F8 overlay   F9 debug   F10 reset",
        ).pack(anchor="w", **pad)

    def _key(self, value: str) -> str | None:
        if not value or value.startswith("("):
            return None
        return value.split(" — ", 1)[0]

    def _fire_n1(self, cb: Callable[[str], None]) -> None:
        key = self._key(self.n1.get())
        if key:
            cb(key)

    def _fire_n2(self, cb: Callable[[str], None]) -> None:
        key = self._key(self.n2.get())
        if key:
            cb(key)

    def set_ocr(self, engine: str, text: str) -> None:
        shown = text if text else "(empty)"
        self.ocr_var.set(f"engine: {engine}    raw: {shown}")

    def set_ranks(self, lines: str) -> None:
        self.rank.delete("1.0", "end")
        self.rank.insert("1.0", lines)

    def append_log(self, line: str) -> None:
        self.log.insert("end", line + "\n")
        self.log.see("end")

    def show(self) -> None:
        self.win.deiconify()
        self.win.lift()

    def hide(self) -> None:
        self.win.withdraw()

    def toggle(self) -> None:
        if self.win.state() == "withdrawn":
            self.show()
        else:
            self.hide()
