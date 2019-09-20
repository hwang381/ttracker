from contextlib import contextmanager
from typing import Callable, Optional
import Xlib
import Xlib.display
import psutil


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


class X11DesktopAppChangeSource(object):
    def __init__(self, callback: Callable[[str], None]):
        self.display = Xlib.display.Display()
        self.NET_ACTIVE_WINDOW = self.display.intern_atom('_NET_ACTIVE_WINDOW')
        self.NET_WM_PID = self.display.intern_atom('_NET_WM_PID')
        self.rootScreen = self.display.screen().root
        self.rootScreen.change_attributes(event_mask=Xlib.X.PropertyChangeMask)
        self.last_seen_pid = None
        self.callback = callback

    def _get_active_win_pid(self) -> Optional[int]:
        active_win_id = self.rootScreen.get_full_property(self.NET_ACTIVE_WINDOW, Xlib.X.AnyPropertyType).value[0]
        with window_obj(self.display, active_win_id) as win_obj:
            if win_obj:
                pid = win_obj.get_full_property(self.NET_WM_PID, Xlib.X.AnyPropertyType).value[0]
                return pid

    def _process_active_win(self):
        active_win_pid = self._get_active_win_pid()
        if active_win_pid != self.last_seen_pid:
            process = psutil.Process(active_win_pid)
            self.callback(process.exe())
            self.last_seen_pid = active_win_pid

    def start(self):
        self._process_active_win()

        print('Starting to listen X11 desktop app change')
        while True:  # next_event() sleeps until we get an event
            event = self.display.next_event()
            if event.type != Xlib.X.PropertyNotify:
                continue
            if event.atom == self.NET_ACTIVE_WINDOW:
                self._process_active_win()
