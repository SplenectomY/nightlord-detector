"""Click-through always-on-top overlay. Separate process window — no game hooks."""

from __future__ import annotations

import sys
import tkinter as tk

from .config import OverlayLayout


GWL_EXSTYLE = -20
WS_EX_LAYERED = 0x00080000
WS_EX_TRANSPARENT = 0x00000020
WS_EX_TOOLWINDOW = 0x00000080
HWND_TOPMOST = -1
SWP_NOMOVE = 0x0002
SWP_NOSIZE = 0x0001
SWP_SHOWWINDOW = 0x0040


def _apply_clickthrough(hwnd: int) -> None:
    if sys.platform != "win32":
        return
    import ctypes

    user32 = ctypes.windll.user32
    style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
    style |= WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_TOOLWINDOW
    user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)
    user32.SetWindowPos(hwnd, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW)


class OverlayWindow:
    def __init__(self, root: tk.Tk, layout: OverlayLayout | None = None):
        self.layout = layout or OverlayLayout()
        self.win = tk.Toplevel(root)
        self.win.title("nightlord-detector overlay")
        self.win.configure(bg="#010101")
        self.win.attributes("-topmost", True)
        self.win.overrideredirect(True)
        try:
            self.win.attributes("-alpha", 0.78)
            self.win.wm_attributes("-transparentcolor", "#010101")
        except tk.TclError:
            pass

        self.label = tk.Label(
            self.win,
            text="Possible Nightlords:\nwaiting for Night 1...",
            justify="center",
            anchor="s",
            font=("Consolas", 13, "bold"),
            fg="#F3E2B2",
            bg="#1A1208",
            padx=14,
            pady=6,
        )
        self.label.pack(fill="both", expand=True)
        self.win.after(50, self.apply_layout)
        self.win.after(200, self._clickthrough)

    def _clickthrough(self) -> None:
        try:
            self.win.update_idletasks()
            _apply_clickthrough(int(self.win.winfo_id()))
        except Exception:
            pass

    def apply_layout(self, layout: OverlayLayout | None = None) -> None:
        if layout is not None:
            self.layout = layout
        self.win.update_idletasks()
        screen_w = self.win.winfo_screenwidth()
        screen_h = self.win.winfo_screenheight()
        width = max(240, int(self.layout.width))
        height = max(48, int(self.layout.height))
        x = (screen_w - width) // 2 + int(self.layout.x_offset)
        y = screen_h - height - max(0, int(self.layout.margin_bottom))
        x = max(0, min(x, screen_w - width))
        y = max(0, min(y, screen_h - height))
        self.win.geometry(f"{width}x{height}+{x}+{y}")
        self.win.attributes("-topmost", True)

    def hardcoded_snippet(self) -> str:
        lay = self.layout
        return (
            f"OverlayLayout(x_offset={lay.x_offset}, margin_bottom={lay.margin_bottom}, "
            f"width={lay.width}, height={lay.height})"
        )

    def set_text(self, text: str) -> None:
        self.label.configure(text=text)

    def set_visible(self, visible: bool) -> None:
        if visible:
            self.win.deiconify()
            self.apply_layout()
        else:
            self.win.withdraw()
