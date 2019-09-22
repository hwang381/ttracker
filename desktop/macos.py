from typing import Callable
import time
import psutil
from .abstract_desktop_app_monitor import AbstractDesktopAppMonitor
from AppKit import NSWorkspace


class MacOSDesktopAppMonitor(AbstractDesktopAppMonitor):
    def __init__(self):
        self.last_seen_pid = None
        self.callback = None

    def set_callback(self, callback: Callable[[str], None]):
        self.callback = callback

    def _get_active_win_pid(self) -> int:
        return NSWorkspace.sharedWorkspace().activeApplication()['NSApplicationProcessIdentifier']

    def _process_active_win_pid(self):
        active_win_pid = self._get_active_win_pid()
        if active_win_pid != self.last_seen_pid:
            process = psutil.Process(active_win_pid)
            self.callback(process.exe())
            self.last_seen_pid = active_win_pid

    def start(self):
        if not self.callback:
            raise RuntimeError("callback is not set!")

        self._process_active_win_pid()

        print('Starting to monitor macOS desktop apps')
        while True:
            self._process_active_win_pid()
            time.sleep(1)
