from contextlib import contextmanager
from typing import Callable, Optional
from .abstract_desktop_monitor import AbstractDesktopMonitor
import Xlib
import Xlib.display


@contextmanager
def window_obj(display, win_id):
    """Simplify dealing with BadWindow (make it either valid or None)"""
    window_obj = None
    if win_id:
        try:
            window_obj = display.create_resource_object('window', win_id)
        except Xlib.error.XError:
            pass
    yield window_obj


class LinuxDesktopMonitor(AbstractDesktopMonitor):
    def get_active_pid(self) -> Optional[int]:
        active_win_id = self.root_screen.get_full_property(self.NET_ACTIVE_WINDOW, Xlib.X.AnyPropertyType).value[0]
        with window_obj(self.display, active_win_id) as win_obj:
            if win_obj:
                pid = win_obj.get_full_property(self.NET_WM_PID, Xlib.X.AnyPropertyType).value[0]
                return pid

    def __init__(self, callback: Callable[[str], None]):
        super(LinuxDesktopMonitor, self).__init__(callback)
        self.display = Xlib.display.Display()
        self.NET_ACTIVE_WINDOW = self.display.intern_atom('_NET_ACTIVE_WINDOW')
        self.NET_WM_PID = self.display.intern_atom('_NET_WM_PID')
        self.root_screen = self.display.screen().root
