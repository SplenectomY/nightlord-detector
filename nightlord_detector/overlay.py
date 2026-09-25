"""Click-through always-on-top overlay. Separate process window — no game hooks.

Anchored bottom-center, just above the physical screen edge, so it sits under the
Nightreign boss plate instead of over the class name / party list.
"""

from __future__ import annotations

import sys
import tkinter as tk

from .config import OverlayLayout, compute_overlay_rect

GWL_EXSTYLE = -20
WS_EX_LAYERED = 0x00080000
WS_EX_TRANSPARENT = 0x00000020
WS_EX_TOOLWINDOW = 0x00000080
HWND_TOPMOST = -1
SWP_SHOWWINDOW = 0x0040
SM_CXSCREEN = 0
SM_CYSCREEN = 1


def _screen_size(fallback_w: int, fallback_h: int) -> tuple[int, int]:
    if sys.platform == "win32":
        try:
            import ctypes

            user32 = ctypes.windll.user32
            try:
                user32.SetProcessDPIAware()
            except Exception:
                pass
            w = int(user32.GetSystemMetrics(SM_CXSCREEN))
            h = int(user32.GetSystemMetrics(SM_CYSCREEN))
            if w > 0 and h > 0:
                return w, h
        except Exception:
            pass
    return max(1, fallback_w), max(1, fallback_h)


def _apply_clickthrough(hwnd: int) -> None:
    if sys.platform != "win32":
        return
    import ctypes

    user32 = ctypes.windll.user32
    style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
    style |= WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_TOOLWINDOW
    user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)


def _move_hwnd(hwnd: int, x: int, y: int, width: int, height: int) -> None:
    if sys.platform != "win32":
        return
    import ctypes

    ctypes.windll.user32.SetWindowPos(
        hwnd,
        HWND_TOPMOST,
        int(x),
        int(y),
        int(width),
        int(height),
        SWP_SHOWWINDOW,
    )


class OverlayWindow:
    def __init__(self, root: tk.Tk, layout: OverlayLayout | None = None):
        self.layout = layout or OverlayLayout()
        self.win = tk.Toplevel(root)
        self.win.title("nightlord-detector overlay")
        self.win.configure(bg="#010101")
        self.win.attributes("-topmost", True)
        self.win.overrideredirect(True)
        try:
            self.win.attributes("-alpha", 0.88)
            self.win.wm_attributes("-transparentcolor", "#010101")
        except tk.TclError:
            pass

        self.label = tk.Label(
            self.win,
            text="Possible Nightlords:\nwaiting for Night 1...",
            justify="center",
            anchor="center",
            font=("Segoe UI", 12, "bold"),
            fg="#E8D7A4",
            bg="#120E08",
            padx=16,
            pady=4,
        )
        self.label.pack(fill="both", expand=True)
        self.apply_layout()
        self.win.after(50, self.apply_layout)
        self.win.after(200, self._clickthrough)
        self.win.bind("<Map>", lambda _e: self.apply_layout())

    def _hwnd(self) -> int | None:
        try:
            self.win.update_idletasks()
            return int(self.win.winfo_id())
        except Exception:
            return None

    def _clickthrough(self) -> None:
        hwnd = self._hwnd()
        if hwnd is None:
            return
        try:
            _apply_clickthrough(hwnd)
            self.apply_layout()
        except Exception:
            pass

    def apply_layout(self, layout: OverlayLayout | None = None) -> None:
        if layout is not None:
            self.layout = layout
        try:
            self.win.update_idletasks()
        except Exception:
            return
        screen_w, screen_h = _screen_size(
            self.win.winfo_screenwidth(),
            self.win.winfo_screenheight(),
        )
        x, y, width, height = compute_overlay_rect(screen_w, screen_h, self.layout)
        self.win.geometry(f"{width}x{height}+{x}+{y}")
        self.win.attributes("-topmost", True)
        hwnd = self._hwnd()
        if hwnd is not None:
            try:
                _move_hwnd(hwnd, x, y, width, height)
            except Exception:
                pass

    def hardcoded_snippet(self) -> str:
        lay = self.layout
        return (
            f"OverlayLayout(x_offset={lay.x_offset}, margin_bottom={lay.margin_bottom}, "
            f"width={lay.width}, height={lay.height})"
        )

    def set_text(self, text: str) -> None:
        self.label.configure(text=text)
        self.win.attributes("-topmost", True)

    def set_visible(self, visible: bool) -> None:
        if visible:
            self.win.deiconify()
            self.apply_layout()
        else:
            self.win.withdraw()
