import time
import unittest

from Routing.RoutingEintrag import RoutingEintrag
from Routing.RoutingTabelle import RoutingTabelle
import socket


class MyTestCase(unittest.TestCase):
    eintrag1 = RoutingEintrag(
        identität="KnotenA",
        ip="192.168.1.2",
        next_hop="192.168.1.1",
        hop=3,
        last_seen=int(time.time())
    )


    eintrag2 = RoutingEintrag(
        identität="KnotenB",
        ip="192.168.1.3",
        next_hop="192.168.1.1",
        hop=2,
        last_seen=int(time.time())
    )

    eintrag3 = RoutingEintrag(
        identität="KnotenA",
        ip="192.168.1.2",
        next_hop="192.168.1.5",
        hop=1,
        last_seen=int(time.time())
    )

    eintrag4 = RoutingEintrag(
        identität="KnotenOwn",
        ip=socket.gethostbyname(socket.gethostname()),
        next_hop=socket.gethostbyname(socket.gethostname()),
        hop=0,
        last_seen=int(time.time()),
    )



    def test_check_timeouts(self):
        routingTabelle : RoutingTabelle = RoutingTabelle()
        nachbar_tabelle = {
            self.eintrag1.ip: self.eintrag1,
            self.eintrag2.ip: self.eintrag2,
        }
        # Erst eintrag1 und eintrag2 einfügen
        routingTabelle.update("192.168.1.1", nachbar_tabelle)

        routingTabelle.eigeneTabelle.get("192.168.1.3").last_seen = int(time.time() -100)

        routingTabelle.check_timeouts()

        self.assertEqual(len(routingTabelle.eigeneTabelle), 2)



    def test_eigene_ip(self):
        routingTabelle : RoutingTabelle = RoutingTabelle()

        nachbar_tabelle = {
            self.eintrag4.ip : self.eintrag4
        }

        routingTabelle.update("192.168.1.1", nachbar_tabelle)
        self.assertEqual(len(routingTabelle.eigeneTabelle), 1)




    def test_neuer_ubernommen(self):
        routingTabelle : RoutingTabelle = RoutingTabelle()
        nachbar_tabelle = {
            self.eintrag1.ip: self.eintrag1,
            self.eintrag2.ip: self.eintrag2,
        }
        # Erst eintrag1 und eintrag2 einfügen
        routingTabelle.update("192.168.1.1", nachbar_tabelle)
        self.assertEqual(len(routingTabelle.eigeneTabelle), 3)


    def test_doppelter_schlechter_nicht_ubernommen(self):
        routingTabelle : RoutingTabelle = RoutingTabelle()

        nachbar_tabelle = {
            self.eintrag1.ip: self.eintrag1,
            self.eintrag2.ip: self.eintrag2,
        }

        # Erst eintrag1 und eintrag2 einfügen
        routingTabelle.update("192.168.1.1", nachbar_tabelle)

        schlechter_eintrag = RoutingEintrag(
            identität="KnotenA",
            ip="192.168.1.2",
            next_hop="192.168.1.9",
            hop=10,
            last_seen=int(time.time())
        )

        nachbar_tabelle2 = {schlechter_eintrag.ip: schlechter_eintrag}
        routingTabelle.update("192.168.1.9", nachbar_tabelle2)

        # Alter next_hop soll noch stimmen
        self.assertEqual(routingTabelle.eigeneTabelle["192.168.1.2"].next_hop, "192.168.1.1")


    def test_kurzer_ubernommen(self):

        routingTabelle : RoutingTabelle = RoutingTabelle()
        nachbar_tabelle = {
            self.eintrag1.ip: self.eintrag1,
            self.eintrag2.ip: self.eintrag2,
        }
        # Erst eintrag1 und eintrag2 einfügen
        routingTabelle.update("192.168.1.1", nachbar_tabelle)
        # Jetzt eintrag3 mit kürzerem Weg
        nachbar_tabelle2 = {
            self.eintrag3.ip: self.eintrag3,
        }
        routingTabelle.update("192.168.1.5", nachbar_tabelle2)
        # Prüfen ob der kürzere Weg übernommen wurde
        self.assertEqual(routingTabelle.eigeneTabelle["192.168.1.2"].hop, 2)  # eintrag3.hop + 1


if __name__ == '__main__':
    unittest.main()
