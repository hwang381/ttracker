from typing import Callable

from .tell_wm import is_cocoa

if is_cocoa():
    from .abstract_app_change_source import AbstractDesktopAppChangeSource

    class CocoaDesktopAppChangeSource(AbstractDesktopAppChangeSource):
        def set_callback(self, callback: Callable[[str], None]):
            pass

        def start(self):
            print('Starting to listen Cocoa desktop app change')
