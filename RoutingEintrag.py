class RoutingEintrag:

    """
    Diese Klasse stellt einen einzelnen Routingeintrag dar.
    identität, ip, next_hop, hop, last_seen
    """
    def __init__(self, identität, ip, next_hop, hop, last_seen)-> None:
        self.id = identität
        self.ip = ip
        self.next_hop = next_hop
        self.hop = hop
        self.last_seen = last_seen



    def __str__(self):
        return f"{self.id} + {self.ip}"
