import abc
import psutil
import time
import requests
from typing import Optional


class AbstractDesktopMonitor(abc.ABC):
    @abc.abstractmethod
    def get_active_pid(self) -> Optional[int]:
        pass

    def _ping(self):
        active_pid = self.get_active_pid()
        process = psutil.Process(active_pid)
        program_name = process.exe()
        requests.post('http://localhost:16789/api/ping/desktop', json={
            'program': program_name
        })

    def start(self):
        while True:
            self._ping()
            time.sleep(1)
