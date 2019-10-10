from .tell_os import is_win

if is_win():
    from typing import Optional
    from .abstract_desktop_monitor import AbstractDesktopMonitor
    import win32gui
    import win32process

    class WindowsDesktopMonitor(AbstractDesktopMonitor):
        def get_active_pid(self) -> Optional[int]:
            win = win32gui.GetForegroundWindow()
            _, process_id = win32process.GetWindowThreadProcessId(win)
            return process_id
