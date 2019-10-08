from .tell_os import is_macos

if is_macos():
    from typing import Optional
    from .abstract_desktop_monitor import AbstractDesktopMonitor
    from AppKit import NSWorkspace
    from database.sqlite_store import SqliteStore


    class MacOSDesktopMonitor(AbstractDesktopMonitor):
        def __init__(self, store: SqliteStore):
            super(MacOSDesktopMonitor, self).__init__(store)

        def get_active_pid(self) -> Optional[int]:
            return NSWorkspace.sharedWorkspace().activeApplication()['NSApplicationProcessIdentifier']
