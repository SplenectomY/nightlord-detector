"""External Nightreign Deep of Night Nightlord detector."""

from __future__ import annotations

import argparse
import logging
import sys
import threading
import time
import tkinter as tk
from tkinter import ttk

from .capture import Roi, configure_tesseract, grab_roi, ocr_image
from .config import AppConfig, OverlayLayout, load_config, save_config
from .debug_console import DebugConsole
from .i18n import LOCALES, current_locale, locale_label, set_locale, t
from .match import match_boss, rank_bosses
from .overlay import OverlayWindow
from .predict import format_overlay, predict

log = logging.getLogger("nightlord-detector")


class DetectorApp:
    def __init__(self, poll_hz: float = 2.0, monitor: int = 1, debug: bool = True):
        self.poll_hz = poll_hz
        self.monitor = monitor
        self.cfg = load_config()
        self.roi = Roi(self.cfg.roi_left, self.cfg.roi_top, self.cfg.roi_width, self.cfg.roi_height)
        self.scanning = True
        self.night1: str | None = None
        self.night2: str | None = None
        self.depth = "any"
        self.last_match_key: tuple[int, str] | None = None
        self._stop = threading.Event()
        found = configure_tesseract()
        set_locale(self.cfg.language)

        self.root = tk.Tk()
        self.root.title(t("app.title"))
        self.root.geometry("420x170+40+240")
        self.root.protocol("WM_DELETE_WINDOW", self.shutdown)
        self._hotkey_lock = threading.Lock()
        self._last_hotkey_at = 0.0

        lang_row = tk.Frame(self.root)
        lang_row.pack(fill="x", padx=16, pady=(14, 4))
        self.lbl_language = tk.Label(lang_row, text=t("app.language"))
        self.lbl_language.pack(side="left")
        self.language = ttk.Combobox(
            lang_row,
            values=[f"{code} — {label}" for code, label in LOCALES],
            width=28,
            state="readonly",
        )
        self.language.set(f"{current_locale()} — {locale_label(current_locale())}")
        self.language.pack(side="left", padx=8)
        self.language.bind("<<ComboboxSelected>>", lambda _e: self.set_language(self.language.get().split(" — ", 1)[0]))

        self.status = tk.Label(self.root, text=t("app.status"), justify="left")
        self.status.pack(anchor="w", padx=16, pady=(4, 12))

        self.overlay = OverlayWindow(self.root, self.cfg.overlay)
        self.debug = DebugConsole(
            self.root,
            on_assign_n1=self.assign_n1,
            on_assign_n2=self.assign_n2,
            on_depth=self.set_depth,
            on_reset=self.reset_run,
            on_roi=self.set_roi,
            on_overlay_layout=self.set_overlay_layout,
            on_save_config=self.persist_config,
            on_toggle_scan=self.set_scanning,
            initial_roi=(self.roi.left, self.roi.top, self.roi.width, self.roi.height),
            initial_overlay=self.cfg.overlay or OverlayLayout(),
        )
        if not debug:
            self.debug.hide()

        self._bind_hotkeys()
        self._refresh_overlay()
        if found:
            self.root.after(0, lambda: self._log(t("log.tesseract", path=found)))
        else:
            self.root.after(0, lambda: self._log(t("log.no_tesseract")))

        self.worker = threading.Thread(target=self._loop, name="ocr-loop", daemon=True)
        self.worker.start()

    def _bind_hotkeys(self) -> None:
        # pynput sees F-keys even when the game is focused. Tk bind_all also
        # fires when one of our windows is focused, so using both made F9
        # toggle the debug console open then immediately closed.
        try:
            from pynput import keyboard

            def on_press(key: object) -> None:
                mapping = {
                    keyboard.Key.f6: lambda: self.root.after(0, lambda: self._guarded_hotkey(lambda: self._hotkey_assign(1))),
                    keyboard.Key.f7: lambda: self.root.after(0, lambda: self._guarded_hotkey(lambda: self._hotkey_assign(2))),
                    keyboard.Key.f8: lambda: self.root.after(0, lambda: self._guarded_hotkey(self._toggle_overlay)),
                    keyboard.Key.f9: lambda: self.root.after(0, lambda: self._guarded_hotkey(self.debug.toggle)),
                    keyboard.Key.f10: lambda: self.root.after(0, lambda: self._guarded_hotkey(self.reset_run)),
                }
                action = mapping.get(key)
                if action:
                    action()

            self._listener = keyboard.Listener(on_press=on_press)
            self._listener.daemon = True
            self._listener.start()
            self._log(t("log.hotkeys_global"))
            return
        except Exception as exc:  # noqa: BLE001
            self._listener = None
            self._log(t("log.hotkeys_tk", exc=exc))

        self.root.bind_all("<F6>", lambda _e: self._guarded_hotkey(lambda: self._hotkey_assign(1)))
        self.root.bind_all("<F7>", lambda _e: self._guarded_hotkey(lambda: self._hotkey_assign(2)))
        self.root.bind_all("<F8>", lambda _e: self._guarded_hotkey(self._toggle_overlay))
        self.root.bind_all("<F9>", lambda _e: self._guarded_hotkey(self.debug.toggle))
        self.root.bind_all("<F10>", lambda _e: self._guarded_hotkey(self.reset_run))

    def _guarded_hotkey(self, action: object) -> None:
        now = time.monotonic()
        with self._hotkey_lock:
            if now - self._last_hotkey_at < 0.28:
                return
            self._last_hotkey_at = now
        action()  # type: ignore[operator]

    def _toggle_overlay(self) -> None:
        visible = self.overlay.win.state() != "withdrawn"
        self.overlay.set_visible(not visible)

    def set_roi(self, left: float, top: float, width: float, height: float) -> None:
        self.roi = Roi(left, top, width, height)
        self.cfg.roi_left, self.cfg.roi_top, self.cfg.roi_width, self.cfg.roi_height = left, top, width, height

    def set_overlay_layout(self, layout: OverlayLayout) -> None:
        self.cfg.overlay = layout
        self.overlay.apply_layout(layout)

    def persist_config(self) -> None:
        path = save_config(self.cfg)
        snippet = self.overlay.hardcoded_snippet()
        self._log(t("log.saved", path=path))
        self._log(t("log.hardcode", snippet=snippet))

    def set_language(self, code: str) -> None:
        chosen = set_locale(code)
        self.cfg.language = chosen
        save_config(self.cfg)
        self.root.title(t("app.title"))
        self.lbl_language.configure(text=t("app.language"))
        self.status.configure(text=t("app.status"))
        self.language.set(f"{chosen} — {locale_label(chosen)}")
        self.debug.apply_locale()
        self._refresh_overlay()
        self._log(t("log.language", label=locale_label(chosen)))

    def set_scanning(self, enabled: bool) -> None:
        self.scanning = enabled
        self._log(t("log.scanning_on") if enabled else t("log.scanning_off"))

    def set_depth(self, depth: str) -> None:
        self.depth = depth
        self._log(t("log.depth", depth=depth))
        self._refresh_overlay()

    def assign_n1(self, key: str) -> None:
        self.night1 = key
        if self.night2 == key:
            self.night2 = None
        self._log(t("log.n1", key=key))
        self._refresh_overlay()

    def assign_n2(self, key: str) -> None:
        self.night2 = key
        self._log(t("log.n2", key=key))
        self._refresh_overlay()

    def reset_run(self) -> None:
        self.night1 = None
        self.night2 = None
        self.last_match_key = None
        self._log(t("log.reset"))
        self._refresh_overlay()

    def _hotkey_assign(self, night: int) -> None:
        # Use the latest OCR snapshot stored on the instance.
        raw = getattr(self, "_last_raw", "")
        match = match_boss(raw) if raw else None
        if not match:
            self._log(t("log.assign_empty", key=5 + night))
            return
        if night == 1:
            self.assign_n1(match.key)
        else:
            self.assign_n2(match.key)

    def _maybe_auto_assign(self, night_hint: int, key: str, label: str, score: float) -> None:
        ident = (night_hint, key)
        if ident == self.last_match_key:
            return
        self.last_match_key = ident
        if self.night1 is None:
            self.assign_n1(key)
            self._log(t("log.auto_n1", label=label, score=f"{score:.0f}"))
            return
        if self.night2 is None and key != self.night1:
            self.assign_n2(key)
            self._log(t("log.auto_n2", label=label, score=f"{score:.0f}"))

    def _refresh_overlay(self) -> None:
        prediction = predict(self.night1, self.night2, self.depth)
        self.overlay.set_text(format_overlay(prediction))

    def _log(self, line: str) -> None:
        log.info(line)
        stamp = time.strftime("%H:%M:%S")
        self.root.after(0, lambda: self.debug.append_log(f"[{stamp}] {line}"))

    def _loop(self) -> None:
        interval = 1.0 / max(self.poll_hz, 0.2)
        while not self._stop.is_set():
            started = time.time()
            if self.scanning:
                try:
                    image = grab_roi(self.roi, self.monitor)
                    engine, text = ocr_image(image)
                    self._last_raw = text
                    match = match_boss(text) if text else None
                    ranks = rank_bosses(text) if text else []
                    rank_text = "\n".join(
                        f"{m.score:5.1f}  N{m.night}  {m.key:12}  {m.label}  via '{m.alias}'"
                        for m in ranks
                    ) or t("debug.no_text")

                    def publish() -> None:
                        self.debug.set_ocr(engine, text)
                        self.debug.set_ranks(rank_text)

                    self.root.after(0, publish)
                    if match and match.score >= 86:
                        self.root.after(
                            0,
                            lambda m=match: self._maybe_auto_assign(m.night, m.key, m.label, m.score),
                        )
                except Exception as exc:  # noqa: BLE001
                    self._log(t("log.scan_error", exc=exc))
            remaining = interval - (time.time() - started)
            if remaining > 0:
                self._stop.wait(remaining)

    def run(self) -> None:
        self.root.mainloop()

    def shutdown(self) -> None:
        self._stop.set()
        listener = getattr(self, "_listener", None)
        if listener is not None:
            try:
                listener.stop()
            except Exception:
                pass
        self.root.destroy()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Nightreign Deep of Night Nightlord overlay")
    parser.add_argument("--debug", action="store_true", default=True, help="Open the debug console (default on).")
    parser.add_argument("--no-debug", action="store_true", help="Start with the debug console hidden.")
    parser.add_argument("--hz", type=float, default=2.0, help="Screen poll rate. Keep this low.")
    parser.add_argument("--monitor", type=int, default=1, help="mss monitor index (1 = first display).")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    app = DetectorApp(poll_hz=args.hz, monitor=args.monitor, debug=not args.no_debug)
    app.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
