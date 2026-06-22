import time

from Packet import Packet
import threading
from Serializer import Serializer
from SocketStarter import SocketStarter
import logging


class AckManager:
    """
    Verwaltet ausstehende ACK-Bestätigungen und behandelt Timeouts sowie Wiederholungsversuche.
    """
    ackStorage = {}

    @staticmethod
    def addWaitingForAck(packet : Packet, socket_starter : SocketStarter) -> None:
        """
        Speichert ein gesendetes Paket und startet einen Timer-Thread der nach 1 Sekunde prüft, ob ein ACK empfangen wurde.

        :param packet: Das gesendete Paket das bestätigt werden muss
        :param socket_starter: Wird für erneutes Senden benötigt
        """

        message_id = packet.header.message_id
        packet_number = packet.header.packet_number

        AckManager.ackStorage[(message_id, packet_number)] = packet
        logging.debug(f"Warte auf ACK: Nachricht {message_id}, Chunk {packet_number}")
        threading.Thread(target=AckManager.checkIfAckWasReceived, args=(message_id, packet_number, socket_starter)).start()

    @staticmethod
    def confirm_ack(packet: Packet)-> None:
        """
         Entfernt ein bestätigtes Paket aus dem Storage.

         :param packet: Das empfangene ACK-Paket
         """
        message_id = packet.header.message_id
        packet_number = packet.header.packet_number

        #Doppelte ACKS?
        if (message_id,packet_number) in AckManager.ackStorage:
            del AckManager.ackStorage[(message_id, packet_number)]
            logging.debug(f"ACK bestätigt: Nachricht {message_id}, Chunk {packet_number}")

    @staticmethod
    def checkIfAckWasReceived(message_id: int, packet_number: int, socket_starter: SocketStarter) -> None:
        """
        Überprüft maximal 10 Sekunden lang, ob Ack angekommen ist.
        Wenn nicht, wird das Paket nochmal versendet.

        :param message_id: Die zu überprüfende message_id
        :param packet_number: Die zu überprüfende packet_number
        :param socket_starter: Wird für das erneute Versenden benötigt.
        """
        for _ in range(10):
            time.sleep(1)

            paket: Packet = AckManager.ackStorage.get((message_id, packet_number))
            if paket is None:
                break

            logging.warning(f"Kein ACK für Nachricht {message_id}, Chunk {packet_number} — erneutes Senden")

            if paket.header.packet_type == 0x02:
                packed = Serializer.packFile(paket)
            else:
                packed = Serializer.pack_message(paket)

            socket_starter.send_forward(packed)
        else:
            logging.error(f"Nachricht {message_id}, Chunk {packet_number} nach 10s aufgegeben")