from typing import Callable, Optional
from .abstract_desktop_monitor import AbstractDesktopMonitor
from AppKit import NSWorkspace


class MacOSDesktopMonitor(AbstractDesktopMonitor):
    def __init__(self, callback: Callable[[str], None]):
        super(MacOSDesktopMonitor, self).__init__(callback)

    def get_active_pid(self) -> Optional[int]:
        return NSWorkspace.sharedWorkspace().activeApplication()['NSApplicationProcessIdentifier']
