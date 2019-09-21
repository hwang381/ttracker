import math
import time


def now_milliseconds() -> int:
    return math.floor(time.time() * 1000)
