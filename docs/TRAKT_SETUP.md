# 🎬 Trakt-Einrichtung & „Weiterschauen“ wie Netflix

Dieses Setup integriert [Trakt.tv](https://trakt.tv) nahtlos in Kodi, sodass dein Sehfortschritt, angefangene Filme & Serienfolgen sowie die jeweils nächsten Episoden automatisch in den Startseiten-Widgets synchronisiert werden.

---

## 1. Kostenloses Trakt-Konto erstellen
1. Falls noch nicht vorhanden, erstelle ein kostenloses Konto auf [trakt.tv](https://trakt.tv).
2. Dein Profil speichert automatisch, was du schaust, und synchronisiert diesen Status über all deine Geräte hinweg.

---

## 2. Trakt in Kodi aktivieren (Einmalig)

1. Navigiere in Kodi in der linken Seitenleiste auf **Add-ons & Live-TV**.
2. Scrolle zu **TMDb Helper** (oder öffne die Add-on-Einstellungen von *TheMovieDb Helper*).
3. Gehe zum Reiter **Trakt**.
4. Klicke auf **„Trakt-Konto autorisieren“** (Authorize Trakt).
5. Es erscheint ein Dialog mit einem **8-stelligen Code** und der URL [trakt.tv/activate](https://trakt.tv/activate).
6. Öffne [trakt.tv/activate](https://trakt.tv/activate) auf deinem Smartphone oder PC, gib den Code ein und bestätige den Zugriff.
7. Kodi bestätigt die erfolgreiche Verbindung sofort.

---

## 3. Wie die Startseiten-Widgets funktionieren

* **▶️ Weiterschauen (`sync_inprogress`):**
  * Sobald du einen Film oder eine Serie über den xStream-Scraper startest, injiziert der Scraper die offizielle TMDb-ID in den Kodi-Player.
  * Beim Pausieren oder Beenden des Videos wird dein Fortschritt (z. B. Minute 34 von 50) sekundengenau an Trakt übermittelt.
  * Das Widget zeigt das Film-/Serien-Poster mit dem roten Fortschrittsbalken. Ein Klick setzt das Video genau an dieser Stelle fort.

* **📺 Nächste Episoden (`sync_nextepisodes`):**
  * Wenn du eine Folge zu Ende geschaut hast (über 85 %), markiert Trakt diese Folge als „Gesehen“ und blendet automatisch die nächste Folge der Staffel im Widget ein.

---

## 4. Problembehebung (Troubleshooting)

* **Widgets bleiben nach Login leer:**
  * Öffne TMDb Helper -> Einstellungen -> Trakt -> **„Bibliothek / Listen jetzt synchronisieren“**.
  * Alternativ: Starte kurz eine Serie an und stoppe sie nach 1 Minute, damit Trakt den ersten Verlaufspunkt anlegt.
