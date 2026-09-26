"""Second-window debug console for live OCR, assignment, and overlay placement."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable

from .config import OverlayLayout
from .i18n import t
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
        on_overlay_layout: Callable[[OverlayLayout], None],
        on_save_config: Callable[[], None],
        on_toggle_scan: Callable[[bool], None],
        initial_roi: tuple[float, float, float, float],
        initial_overlay: OverlayLayout,
    ):
        self.win = tk.Toplevel(root)
        self.win.geometry("760x820+580+40")
        self.win.configure(bg="#111111")
        self.win.protocol("WM_DELETE_WINDOW", self.win.withdraw)
        self._on_overlay_layout = on_overlay_layout
        self._on_assign_n1 = on_assign_n1
        self._on_assign_n2 = on_assign_n2

        pad = {"padx": 8, "pady": 4}

        self.lbl_live = ttk.Label(self.win)
        self.lbl_live.pack(anchor="w", **pad)
        self.ocr_var = tk.StringVar(value="")
        ttk.Label(self.win, textvariable=self.ocr_var, wraplength=720).pack(anchor="w", **pad)

        self.rank = tk.Text(self.win, height=6, width=94, bg="#1c1c1c", fg="#dddddd")
        self.rank.pack(fill="x", **pad)

        row = ttk.Frame(self.win)
        row.pack(fill="x", **pad)
        self.lbl_n1 = ttk.Label(row)
        self.lbl_n1.pack(side="left")
        self.n1 = ttk.Combobox(row, width=48, state="readonly")
        self.n1.pack(side="left", padx=6)
        self.n1.bind("<<ComboboxSelected>>", lambda _e: self._fire_n1(self._on_assign_n1))

        row2 = ttk.Frame(self.win)
        row2.pack(fill="x", **pad)
        self.lbl_n2 = ttk.Label(row2)
        self.lbl_n2.pack(side="left")
        self.n2 = ttk.Combobox(row2, width=48, state="readonly")
        self.n2.pack(side="left", padx=6)
        self.n2.bind("<<ComboboxSelected>>", lambda _e: self._fire_n2(self._on_assign_n2))

        row3 = ttk.Frame(self.win)
        row3.pack(fill="x", **pad)
        self.lbl_depth = ttk.Label(row3)
        self.lbl_depth.pack(side="left")
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
        self.btn_reset = ttk.Button(btns, command=on_reset)
        self.btn_reset.pack(side="left", padx=4)
        self.scan_var = tk.BooleanVar(value=True)
        self.chk_scan = ttk.Checkbutton(
            btns,
            variable=self.scan_var,
            command=lambda: on_toggle_scan(self.scan_var.get()),
        )
        self.chk_scan.pack(side="left", padx=4)
        self.btn_save = ttk.Button(btns, command=on_save_config)
        self.btn_save.pack(side="left", padx=4)

        self.lbl_overlay = ttk.Label(self.win)
        self.lbl_overlay.pack(anchor="w", **pad)
        self.lbl_overlay_help = ttk.Label(self.win, wraplength=720)
        self.lbl_overlay_help.pack(anchor="w", padx=8)
        self.overlay_values = tk.StringVar(value="")
        ttk.Label(self.win, textvariable=self.overlay_values).pack(anchor="w", padx=8)
        self.overlay_sliders: dict[str, tk.Scale] = {}
        overlay_specs = (
            ("x_offset", -800, 800, 1, initial_overlay.x_offset),
            ("margin_bottom", 0, 400, 1, initial_overlay.margin_bottom),
            ("width", 280, 1200, 1, initial_overlay.width),
            ("height", 48, 280, 1, initial_overlay.height),
        )
        for name, lo, hi, res, value in overlay_specs:
            slider = tk.Scale(
                self.win,
                from_=lo,
                to=hi,
                resolution=res,
                orient="horizontal",
                label=name,
                length=700,
                command=lambda _v: self._emit_overlay(),
            )
            slider.set(value)
            slider.pack(fill="x", padx=8)
            self.overlay_sliders[name] = slider
        self._emit_overlay()

        self.lbl_roi = ttk.Label(self.win)
        self.lbl_roi.pack(anchor="w", **pad)
        self.sliders: dict[str, tk.Scale] = {}
        names = ("left", "top", "width", "height")
        for name, value in zip(names, initial_roi):
            slider = tk.Scale(
                self.win,
                from_=0.0,
                to=1.0,
                resolution=0.01,
                orient="horizontal",
                label=f"roi_{name}",
                length=700,
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

        self.lbl_log = ttk.Label(self.win)
        self.lbl_log.pack(anchor="w", **pad)
        self.log = tk.Text(self.win, height=8, width=94, bg="#141414", fg="#c8f5c8")
        self.log.pack(fill="both", expand=True, **pad)

        self.lbl_hotkeys = ttk.Label(self.win)
        self.lbl_hotkeys.pack(anchor="w", **pad)

        self.apply_locale()

    def apply_locale(self) -> None:
        self.win.title(t("debug.title"))
        self.lbl_live.configure(text=t("debug.live_ocr"))
        if not self.ocr_var.get() or self.ocr_var.get().startswith("engine:"):
            if "raw:" not in self.ocr_var.get():
                self.ocr_var.set(t("debug.engine_starting"))
        self.lbl_n1.configure(text=t("debug.night1"))
        self.lbl_n2.configure(text=t("debug.night2"))
        self.lbl_depth.configure(text=t("debug.depth"))
        self.btn_reset.configure(text=t("debug.reset"))
        self.chk_scan.configure(text=t("debug.scan"))
        self.btn_save.configure(text=t("debug.save_layout"))
        self.lbl_overlay.configure(text=t("debug.overlay_pos"))
        self.lbl_overlay_help.configure(text=t("debug.overlay_help"))
        self.lbl_roi.configure(text=t("debug.roi"))
        self.lbl_log.configure(text=t("debug.log"))
        self.lbl_hotkeys.configure(text=t("debug.hotkeys"))

        tables = load_tables()
        n1_key = self._key(self.n1.get()) if getattr(self.n1, "get", None) else None
        n2_key = self._key(self.n2.get()) if self.n2.get() else None
        n1_values = [t("debug.auto")] + [f"{k} — {v['label']}" for k, v in tables["night1"].items()]
        n2_values = [t("debug.auto_unseen")] + [f"{k} — {v['label']}" for k, v in tables["night2"].items()]
        self.n1.configure(values=n1_values)
        self.n2.configure(values=n2_values)
        if n1_key:
            match = next((item for item in n1_values if item.startswith(n1_key + " ")), n1_values[0])
            self.n1.set(match)
        else:
            self.n1.set(t("debug.auto"))
        if n2_key:
            match = next((item for item in n2_values if item.startswith(n2_key + " ")), n2_values[0])
            self.n2.set(match)
        else:
            self.n2.set(t("debug.auto_unseen"))

    def current_overlay(self) -> OverlayLayout:
        return OverlayLayout(
            x_offset=int(self.overlay_sliders["x_offset"].get()),
            margin_bottom=int(self.overlay_sliders["margin_bottom"].get()),
            width=int(self.overlay_sliders["width"].get()),
            height=int(self.overlay_sliders["height"].get()),
        )

    def _emit_overlay(self) -> None:
        layout = self.current_overlay()
        self.overlay_values.set(
            f"OverlayLayout(x_offset={layout.x_offset}, margin_bottom={layout.margin_bottom}, "
            f"width={layout.width}, height={layout.height})"
        )
        self._on_overlay_layout(layout)

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
        shown = text if text else t("debug.no_text")
        self.ocr_var.set(t("debug.engine", engine=engine, text=shown))

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
