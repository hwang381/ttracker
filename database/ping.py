class Ping(object):
    def __init__(self, timestamp: int, ping_type: str, origin: str):
        self.timestamp = timestamp
        self.ping_type = ping_type
        self.origin = origin
