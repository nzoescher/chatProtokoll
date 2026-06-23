class Header:

    """
    Diese Klasse stellt die einzelnen Bestandteile einer Nachricht dar
    """
    def __init__(self, packet_type, ttl, message_id, source_ip, dest_ip, payloadLength, packet_number, packet_count):
        self.packet_type = packet_type
        self.ttl = ttl
        self.message_id = message_id
        self.source_ip = source_ip
        self.dest_ip = dest_ip
        self.payloadLength = payloadLength
        self.packet_number = packet_number
        self.packet_count = packet_count

    def __str__(self):
        return (f"Header [Type: {self.packet_type}, TTL: {self.ttl}, ID: {self.message_id} | "
                f"Src: {self.source_ip} -> Dst: {self.dest_ip}]")


