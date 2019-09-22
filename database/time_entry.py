class TimeEntry(object):
    def __init__(self, from_timestamp: int, entry_type: str, origin: str, to_timestamp: int, gen: int):
        self.from_timestamp = from_timestamp
        self.to_timestamp = to_timestamp
        self.entry_type = entry_type
        self.origin = origin
        self.gen = gen

    def __str__(self):
        return f"{self.entry_type} {self.origin} {self.from_timestamp}->{self.to_timestamp} (gen {self.gen})"
