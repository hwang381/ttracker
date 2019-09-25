class ExternalPing(object):
    def __init__(self,
                 timestamp: int,
                 ping_type: str,
                 origin: str,
                 gen: int
                 ):
        self.timestamp = timestamp
        self.ping_type = ping_type
        self.origin = origin
        self.gen = gen
