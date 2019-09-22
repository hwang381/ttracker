import abc
import psutil
import time
from typing import Optional
from database.sqlite_store import SqliteStore


class AbstractDesktopMonitor(abc.ABC):
    def __init__(self, store: SqliteStore):
        self.store = store

    @abc.abstractmethod
    def get_active_pid(self) -> Optional[int]:
        pass

    def _ping(self):
        active_pid = self.get_active_pid()
        process = psutil.Process(active_pid)
        program_name = process.exe()
        self.store.ping('desktop', program_name)

    def start(self):
        while True:
            self._ping()
            time.sleep(1)
