import MessageHandler
from RoutingTabelle import RoutingTabelle
from SocketStarter import SocketStarter
import os

def main():
    handler = MessageHandler.MessageHandler()
    starter = SocketStarter(handler)
    handler.socket_starter = starter
    starter.send_own_node_at_start()


    dest_ip = "141.22.90.8"

    print("Befehle: 'bye' zum Beenden, 'file <dateiname>' zum Senden einer Datei, 'list' um Teilnehmer auszugeben")
    print("Alles andere wird als Nachricht gesendet.\n")

    while True:
        text = input("> ")

        if text == "bye":
            handler.sendBye()
            starter.stop()
            break

        if text =="list":
            RoutingTabelle.getInstance().getTeilnehmer()

        elif text.startswith("file "):
            pfad = text[5:]
            dateiname = os.path.basename(pfad)
            try:
                with open(pfad, "rb") as f:
                    datei_bytes = f.read()
                handler.sendFile(dateiname, datei_bytes, dest_ip)
                print(f"Datei '{dateiname}' wird gesendet...")
            except FileNotFoundError:
                print(f"Datei nicht gefunden: {pfad}")

        else:
            handler.sendMessage(text, dest_ip)

if __name__ == "__main__":
    main()