"""Click-through always-on-top overlay. Separate process window — no game hooks."""

from __future__ import annotations

import sys
import tkinter as tk


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
    def __init__(self, root: tk.Tk):
        self.win = tk.Toplevel(root)
        self.win.title("nightlord-detector overlay")
        self.win.geometry("520x180+40+40")
        self.win.configure(bg="#010101")
        self.win.attributes("-topmost", True)
        self.win.overrideredirect(True)
        try:
            self.win.attributes("-alpha", 0.82)
            self.win.wm_attributes("-transparentcolor", "#010101")
        except tk.TclError:
            pass

        self.label = tk.Label(
            self.win,
            text="Possible Nightlords:\nwaiting for Night 1...",
            justify="left",
            anchor="nw",
            font=("Consolas", 14, "bold"),
            fg="#F3E2B2",
            bg="#1A1208",
            padx=16,
            pady=12,
        )
        self.label.pack(fill="both", expand=True)
        self.win.after(200, self._clickthrough)

    def _clickthrough(self) -> None:
        try:
            self.win.update_idletasks()
            _apply_clickthrough(int(self.win.winfo_id()))
        except Exception:
            _apply_clickthrough(int(self.win.winfo_id()))

    def set_text(self, text: str) -> None:
        self.label.configure(text=text)

    def set_visible(self, visible: bool) -> None:
        if visible:
            self.win.deiconify()
            self.win.attributes("-topmost", True)
        else:
            self.win.withdraw()
