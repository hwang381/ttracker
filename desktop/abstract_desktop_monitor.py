import abc
import psutil
import time
from typing import Optional
from database.sqlite_store import SqliteStore
from database.ping import Ping
from utils.time import now_milliseconds


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
        self.store.desktop_ping(Ping(
            timestamp=now_milliseconds(),
            ping_type='desktop',
            origin=program_name
        ))

    def start(self):
        while True:
            self._ping()
            time.sleep(1)
