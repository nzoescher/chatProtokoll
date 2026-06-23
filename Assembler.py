from packet_full.Packet import Packet
import logging

class Assembler:
    """
    Diese Klasse managed das Teilen und zusammenführen von Nachrichten
    """

    storage = {} #message_id -> packageNumber -> Text

    def __init__(self):
        pass

    @staticmethod
    def splitMessages(text :str)->dict[int,str]:
        """
        Teilt eine Nachricht die 1300 bytes überschreitet in mehrere Teile

        :param text: Der gesamte Text den es zu teilen gibt
        :return: dict mit Paketnummer als Key und Text-Chunk als Value
        """
        packets : dict = {}
        encoded_message = text.encode('utf-8')
        length = len(encoded_message)

        index = 0
        for i in range(0, length, 1300):
            chunk = encoded_message[i:i+1300].decode('utf-8')
            packets[index] = chunk
            index += 1

        return packets

    @staticmethod
    def uniteMessages(packet : Packet.Packet)-> str | None:
        """
        Fügt einzelne Pakete zu einer gesamten Nachricht zusammen

        :param packet: Das einzelne Paket welches die Nachricht beinhält

        :return: Die ursprüngliche Nachricht oder None, falls Nachricht noch nicht komplett
                zusammengefügt wurde
        """

        if packet.header.message_id not in Assembler.storage: #message_id -> packageNumber -> Text
            Assembler.storage[packet.header.message_id] = {}

        Assembler.storage[packet.header.message_id][packet.header.packet_number] = packet

        if len(Assembler.storage[packet.header.message_id]) == packet.header.packet_count:
            fertigerString : str = ""

            for key in sorted(Assembler.storage[packet.header.message_id]):
                 fertigerString += Assembler.storage[packet.header.message_id][key].message

            del Assembler.storage[packet.header.message_id]
            return fertigerString

        return None

    @staticmethod
    def uniteFile(packet : Packet.Packet)-> tuple[str , bytes] | None:
        """
        Fügt einzelne Pakete zu einer gesamten File zusammen

        :param packet: Das einzelne Paket welches die Filedaten beinhält

        :return: Die ursprüngliche File oder None, falls File noch nicht komplett
                zusammengefügt wurde
        """
        if packet.header.message_id not in Assembler.storage: #message_id -> packageNumber -> Text
            Assembler.storage[packet.header.message_id] = {}

        Assembler.storage[packet.header.message_id][packet.header.packet_number] = packet
        logging.getLogger("ack").debug(f"Storage size: {len(Assembler.storage[packet.header.message_id])}, packet_count: {packet.header.packet_count}")
        logging.getLogger("ack").debug(f"Chunk {packet.header.packet_number} gespeichert, Storage keys: {list(Assembler.storage[packet.header.message_id].keys())[:5]}")

        if len(Assembler.storage[packet.header.message_id]) == packet.header.packet_count:
            fertigeDatei : bytes = b""
            dateiname, _ = Assembler.storage[packet.header.message_id][0].message

            for key in sorted(Assembler.storage[packet.header.message_id]):
                _, daten = Assembler.storage[packet.header.message_id][key].message
                fertigeDatei += daten

            del Assembler.storage[packet.header.message_id]
            logging.getLogger("ack").info(f"Datei '{dateiname}' vollständig assembliert ({len(fertigeDatei)} Bytes)")
            return (dateiname, fertigeDatei)

        return None

    @staticmethod
    def splitFile(file_name: str, datei_bytes: bytes) -> dict[int, tuple[str | None, bytes]]:
        """
        Teilt eine Datei in mehrere Chunks auf.

        :param file_name: Der Name der File
        :param datei_bytes: Die eigentlichen Filedaten

        :return: dict mit Paketnummer als Key und Chunk als Value
        """
        packets = {}
        length = len(datei_bytes)
        name_length = len(file_name.encode('utf-8'))
        first_chunk_size = 1299 - name_length

        packets[0] = (file_name, datei_bytes[:first_chunk_size])
        index = 1

        for i in range(first_chunk_size, length, 1300):
            chunk = datei_bytes[i:i+1300]
            packets[index] = (None, chunk)
            index += 1

        logging.getLogger("ack").debug(f"Datei '{file_name}' aufgeteilt in {len(packets)} Chunks ({length} Bytes)")
        return packets














