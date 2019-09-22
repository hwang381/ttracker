import abc
import psutil
import time
from typing import Callable, Optional


class AbstractDesktopMonitor(abc.ABC):
    def __init__(self, callback: Callable[[str], None]):
        self.last_seen_pid = None
        self.callback = callback

    @abc.abstractmethod
    def get_active_pid(self) -> Optional[int]:
        pass

    def _process(self):
        active_pid = self.get_active_pid()
        if active_pid != self.last_seen_pid:
            process = psutil.Process(active_pid)
            program_name = process.exe()
            self.callback(program_name)
            self.last_seen_pid = active_pid

    def start(self):
        self._process()

        print('Starting to monitor desktop app')
        while True:
            time.sleep(1)
            self._process()
