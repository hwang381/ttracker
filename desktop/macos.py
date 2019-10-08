from .tell_os import is_macos

if is_macos():
    from typing import Optional
    from .abstract_desktop_monitor import AbstractDesktopMonitor
    from AppKit import NSWorkspace

    class MacOSDesktopMonitor(AbstractDesktopMonitor):
        def get_active_pid(self) -> Optional[int]:
            return NSWorkspace.sharedWorkspace().activeApplication()['NSApplicationProcessIdentifier']
