import socket
import threading
import time
from RoutingTabelle import RoutingTabelle
from Serializer import Serializer
import logging


class SocketStarter:
    def __init__(self, message_handler):

        self.running = True
        self.handler = message_handler

        self.sock_chat = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock_routing = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock_chat.bind(("0.0.0.0", 9999))
        self.sock_routing.bind(("0.0.0.0", 9998))

        self.chat_receive_thread = threading.Thread(target=self.receive_chat)
        self.routing_receive_thread = threading.Thread(target=self.receive_routing)
        self.routing_sender_thread = threading.Thread(target = self.send_routing_every5_sek)

        self.chat_receive_thread.start()
        self.routing_receive_thread.start()
        self.routing_sender_thread.start()

        self.lock = threading.Lock()

    def receive_chat(self):

        while self.running:
            try:
                data, addr = self.sock_chat.recvfrom(1600)
                packet_type = data[0]

                if packet_type == 0x02:
                    packet = Serializer.unpackFile(data)
                else:
                    packet = Serializer.unpack_message(data)

                self.handler.handle_inc_messages(packet)

            except OSError:
                break


    def receive_routing(self):
        while self.running:
            try:
                data, addr = self.sock_routing.recvfrom(1600)
                packet = Serializer.unpack_routingtable(data)
                self.handler.handle_inc_routing(packet)

            except OSError:
                break

    def send_chat(self, message:bytes):
        with self.lock:
            dest_ip = socket.inet_ntoa(message[8:12])
            self.sock_chat.sendto(message, (dest_ip, 9999))
            time.sleep(0.0005)

    def send_forward(self, message:bytes):
        threading.Thread(target=self.send_Chat_no_limit, args=(message,)).start()

    def send_Chat_no_limit(self, message: bytes):
        with self.lock:
            dest_ip = socket.inet_ntoa(message[8:12])
            self.sock_chat.sendto(message, (dest_ip, 9999))

    def send_routing(self,routing_message:bytes):
        dest_ip = socket.inet_ntoa((routing_message[8:12]))
        self.sock_routing.sendto(routing_message, (dest_ip,9998))

    def stop(self):
        self.running = False
        self.sock_chat.close()
        self.sock_routing.close()

    def send_routing_every5_sek(self):
        routingTabelle : RoutingTabelle = RoutingTabelle.getInstance()

        while self.running:
            nachbarn = routingTabelle.getNeighbors()

            if len(nachbarn) == 0:
                logging.getLogger("routing").debug("Routing-Tabelle ist leer — keine Nachbarn vorhanden")

            for nachbar in nachbarn:
                self.handler.sendRoutingTable(nachbar)

            routingTabelle.eigeneTabelle[routingTabelle.baseDaten.ip].last_seen = int(time.time())
            time.sleep(5)


    def send_own_node_at_start(self, dest_ip: str) -> None:
        self.handler.sendRoutingTable(dest_ip)




