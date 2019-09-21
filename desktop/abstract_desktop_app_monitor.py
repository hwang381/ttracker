import abc
from typing import Callable


class AbstractDesktopAppMonitor(abc.ABC):
    @abc.abstractmethod
    def set_callback(self, callback: Callable[[str], None]):
        pass

    @abc.abstractmethod
    def start(self):
        pass