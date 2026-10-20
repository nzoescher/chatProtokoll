# RN Chat Server

Dezentrales Peer-to-Peer-Chat-System über **UDP/IPv4**, entwickelt im Rahmen des Rechnernetze-Praktikums an der **HAW Hamburg** (Praktikumsgruppe 1).

Jeder Knoten ist gleichzeitig Client und Router: Es gibt keinen zentralen Server. Nachrichten und Dateien werden über ein eigenes binäres Protokoll versendet und per Distance-Vector-Routing durch das Netz zum Ziel weitergeleitet.

## Funktionen

- **Textnachrichten (MSG)** – UTF-8-kodierte Nachrichten an beliebige erreichbare Knoten
- **Dateiübertragung (FILE)** – Dateien werden in Chunks (max. 1300 Byte Payload) aufgeteilt und beim Empfänger wieder zusammengesetzt, auch wenn Pakete in falscher Reihenfolge ankommen
- **Distance-Vector-Routing** – Knoten tauschen alle 5 Sekunden ihre Routingtabellen mit direkten Nachbarn aus und lernen so Routen zu entfernten Knoten
- **Zuverlässigkeit über ACKs** – jedes MSG-/FILE-Paket wird bestätigt; fehlende ACKs führen nach 1 s zur erneuten Übertragung, nach 10 s zum Abbruch
- **Heartbeat & Timeout** – die periodischen Routing-Pakete dienen als Lebenszeichen; Nachbarn ohne Signal für 30 s gelten als ausgefallen
- **Geordneter Verbindungsabbau (BYE)** – Nachbarn entfernen den Knoten und alle Routen über ihn
- **Schleifenverhinderung** – TTL (Startwert 16) wird pro Hop verringert
- **Senderate-Begrenzung** – max. 1 eigenes Paket pro Millisekunde
- **GUI** – grafisches Chatfenster
- **Logging** – Protokollierung des Netzwerkverkehrs

## Protokoll im Überblick

| Parameter | Wert |
|---|---|
| Transport | UDP über IPv4 |
| Port Nachrichten (MSG, FILE, ACK) | 9999 |
| Port Routing (ROUTING, BYE) | 9998 |
| Header | 32 Byte, fix, Big Endian |
| Max. Payload | 1300 Byte |
| TTL | 16 Hops |

**Header-Aufbau:**

| Offset | Größe | Feld |
|---|---|---|
| 0 | 1 Byte | Type |
| 1 | 1 Byte | TTL |
| 2 | 2 Byte | Nachrichten-ID |
| 4 | 4 Byte | Quell-IP |
| 8 | 4 Byte | Ziel-IP |
| 12 | 4 Byte | Payload-Länge |
| 16 | 8 Byte | Paketnummer |
| 24 | 8 Byte | Gesamt-Paketanzahl |

**Pakettypen:**

| Typ | Wert | Beschreibung |
|---|---|---|
| ROUTING | `0x01` | Routingtabellen-Update / Heartbeat |
| FILE | `0x02` | Datei-Chunk (Chunk 0 enthält den Dateinamen) |
| MSG | `0x03` | Textnachricht |
| ACK | `0x04` | Empfangsbestätigung (ohne Payload) |
| BYE | `0x7F` | Geordneter Verbindungsabbau |

Die vollständige Spezifikation steht im Protokolldokument der Gruppe.
