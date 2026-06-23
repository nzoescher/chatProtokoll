
class Packet:
    """
    Diese Klasse stellt ein Paket dar -> Header + Nachricht
    """

    def __init__(self,header, message ):
        self.header = header
        self.message = message


    def __str__(self):
        return f"{self.header}\nMessage: \"{self.message}\""
