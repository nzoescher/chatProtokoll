import socket
import struct
import time
from Packet import Packet
from Header import Header
from RoutingEintrag import RoutingEintrag


class Serializer:

    """
    Diese Klasse ist zuständig um Nachrichten und Files in bytes zu encoden bzw zu decoden
    """

    HEADER_FORMAT = "!BBH4s4sIQQ"
    HEADER_SIZE = struct.calcsize(HEADER_FORMAT)
    TABELLE_PAYLOAD_FORMAT = "!4sBB"

    @staticmethod
    def _unpack_header(header)-> Header:
        """
        Hilfsmethode, die den Header extrahiert

        :param header: Die rohen Header-Bytes (32 Byte)

        :return: Ein Header-Objekt mit allen entpackten Feldern
        """
        header_tuple = struct.unpack(Serializer.HEADER_FORMAT, header)

        source_ip = socket.inet_ntoa(header_tuple[3])
        dest_ip = socket.inet_ntoa(header_tuple[4])

        header_obj = Header(
            packet_type=header_tuple[0],
            ttl=header_tuple[1],
            message_id=header_tuple[2],
            source_ip=source_ip,
            dest_ip=dest_ip,
            payloadLength=header_tuple[5],
            packet_number=header_tuple[6],
            packet_count=header_tuple[7]
        )
        return header_obj

    @staticmethod
    def _pack_header(packet: Packet)-> bytes:
        """

        :param packet: Das Paket, das zu Bytes werden soll

        :return: das Paket in bytes
        """
        src_bytes = socket.inet_aton(packet.header.source_ip)
        dest_bytes = socket.inet_aton(packet.header.dest_ip)

        header_bytes = struct.pack(
            Serializer.HEADER_FORMAT,
            packet.header.packet_type,
            packet.header.ttl,
            packet.header.message_id,
            src_bytes,
            dest_bytes,
            packet.header.payloadLength,
            packet.header.packet_number,
            packet.header.packet_count,
        )

        return header_bytes


    @staticmethod
    def pack_message(packet: Packet)-> bytes:
        """
        Serialisiert ein Textnachricht-Paket (MSG/ACK/BYE) zu Bytes.

        :param packet: Das zu packende Paket
        :return: die Nachricht inkl. Header als bytes
        """
        header_bytes = Serializer._pack_header(packet)

        nachricht_bytes = packet.message.encode()

        kompletteNachricht = header_bytes + nachricht_bytes

        return kompletteNachricht

    @staticmethod
    def unpack_message(packed_bytes:bytes)->Packet:
        """
        Deserialisiert rohe Bytes zu einem Textnachricht-Paket.

        :param packed_bytes: Die rohen Bytes einer Nachricht

        :return: Ein Packet-Objekt mit Header und Nachricht als String
        """
        header_bytes = packed_bytes[:32]
        header_obj = Serializer._unpack_header(header_bytes)

        nachricht_bytes = packed_bytes[Serializer.HEADER_SIZE:]
        nachricht_string = nachricht_bytes.decode('utf-8')

        return Packet(header_obj, nachricht_string)

    @staticmethod
    def pack_routingtable(packet: Packet)-> bytes:
        """
       Serialisiert ein Routing-Tabellen-Paket zu Bytes.
        Jeder Eintrag wird als ip + hops + nameLen + name kodiert.

        :param packet: Packet-Objekt mit Header und Routing-Tabelle als dict in message

        :return: Die vollständige Routing-Tabelle inkl. Header als Bytes
        """
        header_bytes = Serializer._pack_header(packet)

        kompletteMessage = b""
        liste = packet.message
        for eintrag in liste.values():
            ip =socket.inet_aton(eintrag.ip)
            name_bytes = eintrag.id.encode('utf-8')

            nachrichten_bytes = struct.pack(
                Serializer.TABELLE_PAYLOAD_FORMAT,
                ip,
                eintrag.hop,
                len(name_bytes)
            )

            kompletteMessage += nachrichten_bytes + name_bytes

        return header_bytes + kompletteMessage

    @staticmethod
    def unpack_routingtable(packed_bytes: bytes)-> Packet:
        """
        Deserialisiert rohe Bytes zu einem Routing-Tabellen-Paket.
        Setzt next_hop auf die Absender-IP und last_seen auf den aktuellen Zeitstempel.

        :param packed_bytes: Die rohen Bytes des Routing-Pakets

        :return: Ein Packet-Objekt mit Header und Routing-Tabelle als dict in message
        """
        header_bytes = packed_bytes[:32]
        header_obj = Serializer._unpack_header(header_bytes)

        #Alles nach der Header Size also ab 33
        payload_bytes = packed_bytes[Serializer.HEADER_SIZE:]
        if len(payload_bytes) == 0:
            return Packet(header_obj, {})

        #dict
        tabelle = {}

        i = 0
        while i < len(payload_bytes):
            if len(payload_bytes) - i < 6:
                break

            ip, hop, nameLen = struct.unpack(Serializer.TABELLE_PAYLOAD_FORMAT, payload_bytes[i:i+6])
            name = payload_bytes[i+6:i+6+nameLen].decode('utf-8')
            i += 6 + nameLen
            ip = socket.inet_ntoa(ip)

            tabelle_obj = RoutingEintrag(
                identität= name,
                ip = ip,
                next_hop= header_obj.source_ip,
                hop= hop,
                last_seen= int(time.time())
            )

            tabelle[tabelle_obj.ip] = tabelle_obj

        return Packet(header_obj, tabelle)

    @staticmethod
    def packFile(packet: Packet)-> bytes:
        """
        Serialisiert eine File

        :param packet: Das Packet mit den Dateidaten
        :return: die rohen bytes dieses Paketes
        """
        header_bytes = Serializer._pack_header(packet)

        dateiname, dateidaten = packet.message
        packet_number = packet.header.packet_number

        if packet_number == 0:
            name_bytes = dateiname.encode("utf-8")
            payload = struct.pack(
                "!B",
                len(name_bytes)) + name_bytes + dateidaten
        else:
            payload = dateidaten

        return header_bytes + payload

    @staticmethod
    def unpackFile(packed_bytes: bytes)-> Packet:
        """
        Deserialisiert rohe Bytes zu einem Datei-Paket.
        Chunk 0 enthält (dateiname, dateidaten), alle weiteren Chunks (None, dateidaten).

        :param packed_bytes: Die rohen Bytes des Datei-Pakets
        :return: Ein Packet-Objekt mit Header und (dateiname, dateidaten) als Tuple in message
        """
        header_bytes = packed_bytes[:32]
        header_obj = Serializer._unpack_header(header_bytes)

        # Alles nach 32 Bytes
        payload_bytes = packed_bytes[Serializer.HEADER_SIZE:]

        if header_obj.packet_number == 0:
            nameLen = payload_bytes[0]
            name = payload_bytes[1:1+nameLen].decode('utf-8')
            dateidaten = payload_bytes[1+nameLen:]

            return Packet(header_obj, (name, dateidaten))

        else:
            return Packet(header_obj, (None, payload_bytes))
