class TimeEntry(object):
    def __init__(self, from_timestamp: int, entry_type: str, origin: str, to_timestamp: int):
        self.from_timestamp = from_timestamp
        self.to_timestamp = to_timestamp
        self.e_type = entry_type
        self.origin = origin
