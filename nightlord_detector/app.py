"""External Nightreign Deep of Night Nightlord detector."""

from __future__ import annotations

import argparse
import logging
import sys
import threading
import time
import tkinter as tk

from .capture import Roi, grab_roi, ocr_image
from .debug_console import DebugConsole
from .match import match_boss, rank_bosses
from .overlay import OverlayWindow
from .predict import format_overlay, predict

log = logging.getLogger("nightlord-detector")


class DetectorApp:
    def __init__(self, poll_hz: float = 2.0, monitor: int = 1, debug: bool = True):
        self.poll_hz = poll_hz
        self.monitor = monitor
        self.roi = Roi()
        self.scanning = True
        self.night1: str | None = None
        self.night2: str | None = None
        self.depth = "any"
        self.last_match_key: tuple[int, str] | None = None
        self._stop = threading.Event()

        self.root = tk.Tk()
        self.root.title("nightlord-detector")
        self.root.geometry("360x120+40+240")
        self.root.protocol("WM_DELETE_WINDOW", self.shutdown)

        ttk_label = tk.Label(
            self.root,
            text="nightlord-detector is running.\nF9 opens the debug console.",
            justify="left",
        )
        ttk_label.pack(padx=16, pady=16)

        self.overlay = OverlayWindow(self.root)
        self.debug = DebugConsole(
            self.root,
            on_assign_n1=self.assign_n1,
            on_assign_n2=self.assign_n2,
            on_depth=self.set_depth,
            on_reset=self.reset_run,
            on_roi=self.set_roi,
            on_toggle_scan=self.set_scanning,
            initial_roi=(self.roi.left, self.roi.top, self.roi.width, self.roi.height),
        )
        if not debug:
            self.debug.hide()

        self._bind_hotkeys()
        self._refresh_overlay()

        self.worker = threading.Thread(target=self._loop, name="ocr-loop", daemon=True)
        self.worker.start()

    def _bind_hotkeys(self) -> None:
        for w in (self.root, self.debug.win, self.overlay.win):
            w.bind_all("<F6>", lambda _e: self._hotkey_assign(1))
            w.bind_all("<F7>", lambda _e: self._hotkey_assign(2))
            w.bind_all("<F8>", lambda _e: self._toggle_overlay())
            w.bind_all("<F9>", lambda _e: self.debug.toggle())
            w.bind_all("<F10>", lambda _e: self.reset_run())

        try:
            from pynput import keyboard

            def on_press(key: object) -> None:
                mapping = {
                    keyboard.Key.f6: lambda: self.root.after(0, lambda: self._hotkey_assign(1)),
                    keyboard.Key.f7: lambda: self.root.after(0, lambda: self._hotkey_assign(2)),
                    keyboard.Key.f8: lambda: self.root.after(0, self._toggle_overlay),
                    keyboard.Key.f9: lambda: self.root.after(0, self.debug.toggle),
                    keyboard.Key.f10: lambda: self.root.after(0, self.reset_run),
                }
                action = mapping.get(key)
                if action:
                    action()

            self._listener = keyboard.Listener(on_press=on_press)
            self._listener.daemon = True
            self._listener.start()
            self._log("Global hotkeys armed via pynput.")
        except Exception as exc:  # noqa: BLE001
            self._listener = None
            self._log(f"pynput unavailable ({exc}); F-keys work when a detector window is focused.")

    def _toggle_overlay(self) -> None:
        visible = self.overlay.win.state() != "withdrawn"
        self.overlay.set_visible(not visible)

    def set_roi(self, left: float, top: float, width: float, height: float) -> None:
        self.roi = Roi(left, top, width, height)

    def set_scanning(self, enabled: bool) -> None:
        self.scanning = enabled
        self._log(f"Scanning {'on' if enabled else 'off'}.")

    def set_depth(self, depth: str) -> None:
        self.depth = depth
        self._log(f"Depth set to {depth}.")
        self._refresh_overlay()

    def assign_n1(self, key: str) -> None:
        self.night1 = key
        if self.night2 == key:
            self.night2 = None
        self._log(f"Night 1 = {key}")
        self._refresh_overlay()

    def assign_n2(self, key: str) -> None:
        self.night2 = key
        self._log(f"Night 2 = {key}")
        self._refresh_overlay()

    def reset_run(self) -> None:
        self.night1 = None
        self.night2 = None
        self.last_match_key = None
        self._log("Run reset.")
        self._refresh_overlay()

    def _hotkey_assign(self, night: int) -> None:
        raw = getattr(self, "_last_raw", "")
        match = match_boss(raw) if raw else None
        if not match:
            self._log(f"F{5 + night}: nothing to assign from current OCR.")
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
            self._log(f"Auto Night 1 from healthbar: {label} ({score:.0f})")
            return
        if self.night2 is None and key != self.night1:
            self.assign_n2(key)
            self._log(f"Auto Night 2 from healthbar: {label} ({score:.0f})")

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
                    ) or "(no text)"

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
                    self._log(f"Scan error: {exc}")
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
