import abc
import psutil
import time
import requests
import logging
from typing import Optional


CONSECUTIVE_FAULTED_PINGS_TOLERANCE = 10
CONSECUTIVE_FAULTED_PINGS_EXCEEDED_MSG = \
    "Consecutive faulted pings tolerance has been exceeded, exiting.\n " \
    "Please contact developer"


class AbstractDesktopMonitor(abc.ABC):
    def __init__(self):
        self.consecutive_faulted_pings = 0

    @abc.abstractmethod
    def get_active_pid(self) -> Optional[int]:
        pass

    def _ping(self):
        active_pid = None
        try:
            active_pid = self.get_active_pid()
        except Exception as e:
            logging.error(f"Faulted when trying to get active pid")
            logging.error(str(e))
            self.consecutive_faulted_pings += 1
            if self.consecutive_faulted_pings >= CONSECUTIVE_FAULTED_PINGS_TOLERANCE:
                logging.error(CONSECUTIVE_FAULTED_PINGS_EXCEEDED_MSG)
                raise RuntimeError(CONSECUTIVE_FAULTED_PINGS_EXCEEDED_MSG)

        if active_pid:
            self.consecutive_faulted_pings = 0
            process = psutil.Process(active_pid)
            program_name = process.exe()
            requests.post('http://localhost:16789/api/ping/desktop', json={
                'program': program_name
            })

    def start(self):
        while True:
            self._ping()
            time.sleep(1)
