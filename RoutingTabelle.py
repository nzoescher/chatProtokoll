import time
from RoutingEintrag import RoutingEintrag
import logging

class RoutingTabelle:
    """
    Verwaltet die lokale Routing-Tabelle des Knotens.
    """

    _instanz = None

    def __init__(self):
        self.baseDaten = RoutingEintrag(
            identität="Headmaster",
            ip= "192.168.178.20",
            next_hop= "192.168.178.20",
            hop=0,
            last_seen=int(time.time()),
        )
        self.eigeneTabelle = dict()
        self.eigeneTabelle[self.baseDaten.ip] = self.baseDaten

    @staticmethod
    def getInstance():
        if RoutingTabelle._instanz is None:
            RoutingTabelle._instanz = RoutingTabelle()
        return RoutingTabelle._instanz

    def getTeilnehmer(self):

        for eintrag in self.eigeneTabelle:
            print (f"{self.eigeneTabelle[eintrag].ip} + {self.eigeneTabelle[eintrag].id}")

    def update(self, von_nachbar_ip, nachbar_tabelle: dict):
        """
        Aktualisiert die Tabelle mit Einträgen eines Nachbarn.

        :param von_nachbar_ip: IP des sendenden Nachbarn
        :param nachbar_tabelle: dict mit RoutingEintrag-Objekten
        """

        for nachbar_eintrag in nachbar_tabelle.values():

            #Check, ob eigene IP ist
            if nachbar_eintrag.ip == self.baseDaten.ip:
                continue

            #Überprüfen, ob TTL überschritten ist
            if nachbar_eintrag.hop > 16:
                continue

            # Neuer Eintrag — Route noch nicht bekannt, einfügen
            if nachbar_eintrag.ip not in self.eigeneTabelle:
                self.eigeneTabelle[nachbar_eintrag.ip] = RoutingEintrag(
                    identität=nachbar_eintrag.id,
                    ip=nachbar_eintrag.ip,
                    next_hop=von_nachbar_ip,
                    hop=nachbar_eintrag.hop + 1,
                    last_seen=int(time.time())
                )
                logging.getLogger("routing").debug(f"Neuer Eintrag: {nachbar_eintrag.ip} ({nachbar_eintrag.id}) via {von_nachbar_ip} mit {nachbar_eintrag.hop + 1} Hops")

            ## Bekannte Route — prüfen, ob neuer Weg kürzer ist
            else:
                if self.eigeneTabelle[nachbar_eintrag.ip].hop > nachbar_tabelle[nachbar_eintrag.ip].hop + 1:
                    self.eigeneTabelle[nachbar_eintrag.ip].hop = nachbar_eintrag.hop + 1
                    self.eigeneTabelle[nachbar_eintrag.ip].next_hop = von_nachbar_ip
                    self.eigeneTabelle[nachbar_eintrag.ip].last_seen = int(time.time())
                    logging.getLogger("routing").debug(f"Route aktualisiert: {nachbar_eintrag.ip} via {von_nachbar_ip} mit {nachbar_eintrag.hop + 1} Hops")

            self.check_timeouts()

    def check_timeouts(self):
        """
        Überprüft alle Einträge auf Timeout (30 Sek. ohne Kontakt).
        Abgelaufene Einträge sowie alle Routen über diese werden gelöscht.
        """
        for ip in list(self.eigeneTabelle.keys()):
            if self.is_timeouted(self.eigeneTabelle[ip].last_seen):
                self.isNextHop(self.eigeneTabelle[ip])
                self.delete(ip)
                logging.getLogger("routing").debug(f"Knoten {ip} wurde wegen Inaktivität gelöscht")

    def is_timeouted(self, letzte_aktualisierung: int):
        """
        Überprüft, ob erhaltener Zeitstempel länger als 30 Sekunden her ist

        :param letzte_aktualisierung: Zeitstempel, den es zu überprüfen gibt

        :return: True, wenn der Eintrag älter als 30 Sekunden ist
        """

        return letzte_aktualisierung + 30 < int(time.time())

    def delete(self, eintrag: str):
        """
       Löscht den Eintrag aus der RotingTabelle

       :param: eintrag: Der zu löschende Eintrag
       """

        if eintrag in self.eigeneTabelle:
            del self.eigeneTabelle[eintrag]

    def isNextHop(self, eintrag: RoutingEintrag):
        """
        Überprüft, ob ein Eintrag ein Zwischenknoten war

       :param: eintrag: Der zu überprüfende Eintrag
       """
        for ip in list(self.eigeneTabelle.keys()):
            if eintrag.ip == self.eigeneTabelle[ip].next_hop:
                self.delete(ip)
                logging.getLogger("routing").debug(f"Knoten mit IP:{ip} wurde gelöscht, da über inaktiven Knoten ging")

    def getNeighbors(self) -> list[str]:
        """
       Gibt alle Nachbarn zurück

       :return: Eine Liste von allen direkten Nachbarn
       """
        neighbors = []
        for eintrag in self.eigeneTabelle.values():
            if eintrag.hop == 1:
                neighbors.append(eintrag.ip)

        return neighbors

    def getOwn(self)-> str:

        for eintrag in self.eigeneTabelle.values():
            if eintrag.hop == 0:
                return eintrag.ip


    def match_username_to_ip(self, username: str)-> str | None:
        """
        Sucht für den usernamen die passende IP raus

        :param username: Der Username zu dem die IP rausgesucht werden soll

        :return: Die passende IP oder None
        """
        for eintrag in self.eigeneTabelle:
            if self.eigeneTabelle[eintrag].id == username:
                return self.eigeneTabelle[eintrag].ip
        return None

