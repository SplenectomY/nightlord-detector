"""Click-through always-on-top overlay. Separate process window — no game hooks.

Anchored bottom-center, just above the physical screen edge, so it sits under the
Nightreign boss plate instead of over the class name / party list.
"""

from __future__ import annotations

import sys
import tkinter as tk

from .config import OverlayLayout, compute_overlay_rect, compute_roi_rect

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


TRANSPARENT = "#010101"
ROI_BORDER = "#FF2020"
ROI_BORDER_PX = 3


class RoiGuideWindow:
    """Hollow red rectangle over the OCR crop. Only shown while debug is open."""

    def __init__(self, root: tk.Tk):
        self.win = tk.Toplevel(root)
        self.win.title("nightlord-detector roi")
        self.win.configure(bg=TRANSPARENT)
        self.win.attributes("-topmost", True)
        self.win.overrideredirect(True)
        try:
            self.win.attributes("-transparentcolor", TRANSPARENT)
        except tk.TclError:
            pass

        self._left = 0.28
        self._top = 0.04
        self._width = 0.44
        self._height = 0.10
        self._visible = False

        self.top_bar = tk.Frame(self.win, bg=ROI_BORDER, height=ROI_BORDER_PX)
        self.top_bar.pack(side="top", fill="x")
        self.bottom_bar = tk.Frame(self.win, bg=ROI_BORDER, height=ROI_BORDER_PX)
        self.bottom_bar.pack(side="bottom", fill="x")
        self.left_bar = tk.Frame(self.win, bg=ROI_BORDER, width=ROI_BORDER_PX)
        self.left_bar.pack(side="left", fill="y")
        self.right_bar = tk.Frame(self.win, bg=ROI_BORDER, width=ROI_BORDER_PX)
        self.right_bar.pack(side="right", fill="y")
        self.hole = tk.Frame(self.win, bg=TRANSPARENT)
        self.hole.pack(fill="both", expand=True)

        self.win.withdraw()
        self.win.after(200, self._clickthrough)
        self.win.bind("<Map>", lambda _e: self.apply_roi() if self._visible else None)

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
            if self._visible:
                self.apply_roi()
        except Exception:
            pass

    def set_fractions(self, left: float, top: float, width: float, height: float) -> None:
        self._left, self._top, self._width, self._height = left, top, width, height
        if self._visible:
            self.apply_roi()

    def apply_roi(self) -> None:
        try:
            self.win.update_idletasks()
        except Exception:
            return
        screen_w, screen_h = _screen_size(
            self.win.winfo_screenwidth(),
            self.win.winfo_screenheight(),
        )
        x, y, width, height = compute_roi_rect(
            screen_w,
            screen_h,
            self._left,
            self._top,
            self._width,
            self._height,
        )
        border = ROI_BORDER_PX
        gx = max(0, x - border)
        gy = max(0, y - border)
        gw = min(screen_w - gx, width + 2 * border)
        gh = min(screen_h - gy, height + 2 * border)
        self.win.geometry(f"{gw}x{gh}+{gx}+{gy}")
        self.win.attributes("-topmost", True)
        hwnd = self._hwnd()
        if hwnd is not None:
            try:
                _move_hwnd(hwnd, gx, gy, gw, gh)
            except Exception:
                pass

    def set_visible(self, visible: bool) -> None:
        self._visible = visible
        if visible:
            self.win.deiconify()
            self.apply_roi()
            self.win.after(50, self._clickthrough)
        else:
            self.win.withdraw()
