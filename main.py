import MessageHandler
from RoutingTabelle import RoutingTabelle
from SocketStarter import SocketStarter
import os
import logging

def main():

    # Routing Logger
    routing_logger = logging.getLogger("routing")
    routing_logger.setLevel(logging.DEBUG)
    routing_logger.propagate = False
    routing_logger.addHandler(logging.FileHandler("log/routing.log", mode="w", encoding="utf-8"))

    # ACK + Assembler Logger
    ack_logger = logging.getLogger("ack")
    ack_logger.setLevel(logging.DEBUG)
    ack_logger.propagate = False
    ack_logger.addHandler(logging.FileHandler("log/ack.log", mode="w",encoding="utf-8"))

    handler = MessageHandler.MessageHandler()
    starter = SocketStarter(handler)
    handler.socket_starter = starter

    dest_ip = "10.8.3.2"
    starter.send_own_node_at_start(dest_ip)

    print("Befehle: 'bye' zum Beenden, 'file <pfad> <ziel-ip>' zum Senden einer Datei, 'list' um Teilnehmer auszugeben")
    print("Nachrichten: '<ziel-ip> <nachricht>'\n")

    while True:
        text = input("> ")

        if text == "bye":
            handler.sendBye()
            starter.stop()
            break

        elif text == "list":
            RoutingTabelle.getInstance().getTeilnehmer()

        elif text.startswith("file "):
            teile = text.split(" ", 2)
            if len(teile) < 3:
                print("Format: file <pfad> <ziel-ip>")
                continue
            pfad = teile[1]
            dest_ip = teile[2]
            dateiname = os.path.basename(pfad)
            try:
                with open(pfad, "rb") as f:
                    datei_bytes = f.read()
                handler.sendFile(dateiname, datei_bytes, dest_ip)
                print(f"Datei '{dateiname}' wird gesendet...")
            except FileNotFoundError:
                print(f"Datei nicht gefunden: {pfad}")

        else:
            teile = text.split(" ", 1)
            if len(teile) < 2:
                print("Format: <ziel-ip> <nachricht>")
                continue
            dest_ip = teile[0]
            nachricht = teile[1]
            handler.sendMessage(nachricht, dest_ip)

if __name__ == "__main__":
    main()