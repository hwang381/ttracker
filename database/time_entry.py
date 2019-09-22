class TimeEntry(object):
    def __init__(self, from_timestamp: int, e_type: str, origin: str):
        self.from_timestamp = from_timestamp
        self.e_type = e_type
        self.origin = origin
