class Ping(object):
    def __init__(self, timestamp: int, ping_type: str, origin: str):
        self.timestamp = timestamp
        self.ping_type = ping_type
        self.origin = origin

    def __str__(self):
        return f"{self.ping_type} type from {self.origin} @{self.timestamp}"
