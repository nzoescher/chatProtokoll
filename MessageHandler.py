from AckManager import AckManager
from Header import Header
from Packet import Packet
import socket
from RoutingTabelle import RoutingTabelle
from Serializer import Serializer
from Assembler import Assembler
from ChatWindow import ChatWindow
import logging


class MessageHandler:
    """
    Verarbeitet eingehende Pakete und koordiniert das Senden von Nachrichten, Dateien, ACKs und Routing-Updates.
    Steuereinheit zwischen Netzwerk und Logik
    """

    message_id_counter = 0
    ROUTING = 0x01
    FILE = 0x02
    MSG = 0x03
    ACK = 0x04
    BYE = 0x7F

    def __init__(self):
        self.socket_starter = None
        self.chat_window = ChatWindow()

    def handle_inc_messages(self, packet: Packet) -> None:
        """
        Leitet eingehendes MessagePacket(MSG, File, ACK) and die zuständige Methode weiter,
        die die eigentliche Implementierung übernimmt.

        :param packet: Das eingehende MessagePacket
        """
        if self.check_if_destination_is_me(packet):
            match packet.header.packet_type:
                case self.MSG:
                    self.handleText(packet)
                case self.FILE:
                    self.handleFILE(packet)
                case self.ACK:
                    self.handleACK(packet)

        else:
            self.handleForward(packet)

    def handle_inc_routing(self, packet: Packet) -> None:
        """
        Leitet eingehendes Routingpaket(Routing, BYE) and die zuständige Methode weiter,
        die die eigentliche Implementierung übernimmt.

        :param packet: Das eingehende Routingpaket
        """
        match packet.header.packet_type:
            case self.ROUTING:
                self.handleRoutingUpdate(packet)
            case self.BYE:
                self.handleBYE(packet)

    def handleText(self, packet):
        """
        Verarbeitet Paket so, dass Nachricht und Metadaten im Chat angezeigt werden können.

        :param packet: Paket dessen Text auszulesen ist
        """
        self.sendAck(packet.header.source_ip)
        text = Assembler.uniteMessages(packet)

        routingTabelle = RoutingTabelle.getInstance()

        username = routingTabelle.eigeneTabelle.get(packet.header.source_ip)

        if text is not None:
            self.chat_window.show(f"{username}: {text}")


    def handleFILE(self, packet) -> None:
        """
        Verarbeitet Paket so, dass Dateiname und Metadaten im Chat angezeigt werden können.

        :param packet: Paket dessen, Inhalt zu speichern ist.
        """
        self.sendAck(packet.header.source_ip)
        logging.debug(f"FILE Chunk empfangen: {packet.header.packet_number}/{packet.header.packet_count}")
        result = Assembler.uniteFile(packet)

        if result is not None:
            dateiname, dateidaten = result
            with open(f"empfangen_{dateiname}", "wb") as f:
                f.write(dateidaten)
            logging.info(f"Datei gespeichert: empfangen_{dateiname}")
            self.chat_window.show(f"{packet.header.source_ip}: [Datei] {dateiname}")

    def handleACK(self, packet: Packet) -> None:
        """
        Verarbeitet Ack, damit referenziertes Paket nicht nochmal gesendet wird

        :param packet: Paket, dass Ack und referenziertes Paket enthält
        """
        AckManager.confirm_ack(packet)

    def handleRoutingUpdate(self, packet: Packet) -> None:
        """
        Wandelt das Routingpaket so um, dass die RoutingTabelle aktualisiert werden kann.

        :param packet: Das Paket, das den Routingeintrag enthält

        """
        routingTabelle = RoutingTabelle.getInstance()
        routingTabelle.update(packet.header.source_ip, packet.message)
        logging.info(f"Routing-Update empfangen von {packet.header.source_ip} mit {len(packet.message)} Einträgen")

    def handleBYE(self, packet: Packet) -> None:
        """
        Wandelt das Bye Paket so um, dass es in der RoutingTabelle gelöscht werden kann.

        :param packet: Das Bye Paket
        """
        routingTabelle = RoutingTabelle.getInstance()
        eintrag = routingTabelle.eigeneTabelle.get(packet.header.source_ip)

        if eintrag:
            routingTabelle.isNextHop(eintrag)

        routingTabelle.delete(packet.header.source_ip)
        logging.info(f"BYE empfangen von {packet.header.source_ip} — Knoten wird aus Routing-Tabelle entfernt")

    def handleForward(self, packet: Packet) -> None:
        """
        Bereitet das Paket für forwarding vor, falls der TTL nicht unterschritten ist.

        :param packet: Das weiterzuleitende Paket (Kann Routing und Message sein)
        """

        if self.isTTLpositive(packet):
            packet.header.ttl -= 1
            packed_message: Packet

            if packet.header.packet_type in (self.MSG, self.ACK, self.FILE):
                packed_message = Serializer.pack_message(packet)
                self.socket_starter.send_forward(packed_message)

            else:
                packed_message = Serializer.pack_routingtable(packet)
                self.socket_starter.send_routing(packed_message)

            logging.debug(f"Paket {packet.header.message_id} wird weitergeleitet von {packet.header.source_ip} an {packet.header.dest_ip} (TTL: {packet.header.ttl})")

    def isTTLpositive(self, packet: Packet) -> bool:
        """
        Hilfsmethode die checkt, ob TTL unterschritten ist

        :param packet: Paket, dessen TTL zu überprüfen ist

        :return: True, wenn TTL NICHT unterschritten ist
        """
        if packet.header.ttl > 0:
            logging.debug(f"TTL geprüft: {packet.header.ttl} Hops verbleibend (Paket {packet.header.message_id})")
            return True

        else:
            logging.info(f"Paket {packet.header.message_id} verworfen — TTL abgelaufen (von {packet.header.source_ip} an {packet.header.dest_ip})")
            return False

    def check_if_destination_is_me(self, packet: Packet) -> bool:
        """
        Überprüft, ob Ziel des Pakets ich selber bin

        :param packet: Das Paket welches in dest_ip das eigentlich Ziel gespeichert hat

        :return:True, wenn paket an mich gerichtet ist

        """
        result : bool = packet.header.dest_ip == socket.gethostbyname(socket.gethostname())
        logging.debug(f"Ziel-IP {packet.header.dest_ip} stimmt {'überein' if result else 'nicht überein'} mit eigener IP")
        return result

    ###############################################
    ########## Sending ############################
    ###############################################

    def sendFile(self, file_name: str, datei_bytes: bytes, dest_ip: str)-> None:
        """
        Sendet die Datei, nachdem sie
        -> Vollständig gesplittet wurde
        -> Für jeden Chunk ein eigenes Paket gebaut wurde
        -> Alles in Bytes umgewandelt wurde

        :param file_name: Der Name der Datei, die übermittelt werden soll
        :param datei_bytes: Das eigentliche Paket in bytes
        :param dest_ip: Die IP-Adress wohin das Paket soll
        """
        messages: dict = Assembler.splitFile(file_name=file_name, datei_bytes=datei_bytes)
        for message in messages.keys():
            antwort_packet = Packet(
                header=Header(
                    packet_type=0x02,
                    ttl=16,
                    message_id=MessageHandler.message_id_counter,
                    source_ip=socket.gethostbyname(socket.gethostname()),
                    dest_ip=dest_ip,
                    payloadLength=0,
                    packet_number=message,
                    packet_count=len(messages)
                ),
                message=messages[message]
            )

            packed_message = Serializer.packFile(antwort_packet)
            antwort_packet.header.payloadLength = len(packed_message) - Serializer.HEADER_SIZE

            self.socket_starter.send_chat(packed_message)
            AckManager.addWaitingForAck(antwort_packet,self.socket_starter)

        MessageHandler.message_id_counter += 1

        logging.info(f"Datei '{file_name}' wird gesendet an {dest_ip} ({len(messages)} Chunks)")

    def sendAck(self, dest_ip: str):
        """
        Sendet Ack an IP

        :param dest_ip: Ip des Empfängers
        """

        antwort_packet = Packet(
            header=Header(
                packet_type=0x04,
                ttl=16,
                message_id=MessageHandler.message_id_counter,
                source_ip=socket.gethostbyname(socket.gethostname()),
                dest_ip=dest_ip,
                payloadLength=0,
                packet_number=0,
                packet_count=0
            ),
            message=""
        )
        packed_message = Serializer.pack_message(antwort_packet)
        self.socket_starter.send_forward(packed_message)

        logging.debug(f"ACK gesendet an {dest_ip} für Nachricht {MessageHandler.message_id_counter}")

    def sendRoutingTable(self, dest_ip: str):
        """
        Sendet eigene RoutingTabelle an IP

        :param dest_ip: IP des Empfängers
        """
        antwort_packet = Packet(
            header=Header(
                packet_type=0x01,
                ttl=16,
                message_id=MessageHandler.message_id_counter,
                source_ip=socket.gethostbyname(socket.gethostname()),
                dest_ip=dest_ip,
                payloadLength=len(RoutingTabelle.getInstance().eigeneTabelle) * 37,
                packet_number=0,
                packet_count=0
            ),
            message=RoutingTabelle.getInstance().eigeneTabelle
        )
        MessageHandler.message_id_counter += 1
        packed_message = Serializer.pack_routingtable(antwort_packet)
        self.socket_starter.send_routing(packed_message)

        logging.info(f"Routing-Tabelle gesendet an {dest_ip} mit {len(RoutingTabelle.getInstance().eigeneTabelle)} Einträgen")

    def sendMessage(self, text: str, dest_ip: str):
        """
        Sendet eine Textnachricht, nachdem
        -> gesplittet wurde
        ->Serialisiert wurde
        -> In Liste von noch zu bestätigten Acks gepackt wurde

        :param text: Zu sendende Nachricht
        :param dest_ip: IP des Empfängers
        """

        messages: dict = Assembler.splitMessages(text)

        for message in messages.keys():
            antwort_packet = Packet(
                header=Header(
                    packet_type=0x03,
                    ttl=16,
                    message_id=MessageHandler.message_id_counter,
                    source_ip=socket.gethostbyname(socket.gethostname()),
                    dest_ip=dest_ip,
                    payloadLength=len(messages[message].encode()),
                    packet_number=message,
                    packet_count=len(messages),
                ),
                message=messages[message]
            )

            packed_message = Serializer.pack_message(antwort_packet)
            self.socket_starter.send_chat(packed_message)
            AckManager.addWaitingForAck(antwort_packet,self.socket_starter)

        MessageHandler.message_id_counter += 1
        logging.info(f"Nachricht gesendet an {dest_ip} ({len(messages)} Chunks)")

    def sendBye(self )->None:
        """
        Sendet ein Bye an alle direkten Nachbarn (Hop =1)
        """

        routingTabelle = RoutingTabelle.getInstance()
        neighbors: list = routingTabelle.getNeighbors()
        logging.info(f"BYE gesendet an alle {len(neighbors)} Nachbarn")

        for neighbor in neighbors:
            antwort_packet = Packet(
                header=Header(
                    packet_type=0x7F,
                    ttl=16,
                    message_id=MessageHandler.message_id_counter,
                    source_ip=socket.gethostbyname(socket.gethostname()),
                    dest_ip=neighbor,
                    payloadLength=0,
                    packet_number=0,
                    packet_count=0
                ),
                message=""
            )
            MessageHandler.message_id_counter += 1
            packed_message = Serializer.pack_message(antwort_packet)
            self.socket_starter.send_chat(packed_message)
