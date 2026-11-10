# 🛠️ Fehlerbehebung & Wartung (Troubleshooting)

Häufige Fragen und schnelle Lösungen für das Google TV Kodi Mediacenter.

---

## 1. Kodi startet nicht / Zeigt nur grauen Bildschirm
* **Ursache:** Die Skin-Generator-Dateien von *Arctic Fuse 2* wurden nach einer Neuinstallation noch nicht initialisiert.
* **Lösung:**
  * Öffne ein Terminal auf deinem PC und verbinde dich per ADB:
    ```bash
    adb shell "am force-stop org.xbmc.kodi; am start -n org.xbmc.kodi/.Main"
    ```
  * Kodi liest beim Start die vorkonfigurierten XML-Dateien ein.

---

## 2. Ein Stream startet nicht / „xStream Scraper Fehler“
* **Ursache:** Die gewählte Hoster-Domain hat kurzzeitig gewechselt oder blockiert Anfragen.
* **Lösung:**
  * Der automatische Scraper testet gefundene Streams bereits vorab. Sollte ein Hoster trotzdem abbrechen:
  * Klicke länger auf den Film / die Folge (Kontextmenü) -> **„Abspielen mit...“** -> Wähle manuell einen anderen Anbieter (z. B. *VOE*, *Doodstream* oder *Streamcloud*).

---

## 3. „Weiterschauen“-Reihe auf der Startseite aktualisiert sich nicht
* **Lösung:**
  1. Gehe in der Seitenleiste auf **Add-ons & Live-TV** -> **TMDb Helper**.
  2. Wähle **Einstellungen** -> **Trakt**.
  3. Klicke auf **„Bibliothek / Listen jetzt synchronisieren“**.
  4. Gehe zurück auf die Startseite; die Widgets laden sich neu.

---

## 4. Tastenbelegung der Fernbedienung reagiert nicht wie gewünscht
* Falls die Tastenbelegung nach einem Kodi-Update auf den Standard zurückgesetzt wurde:
  * Führe folgenden Befehl aus:
    ```bash
    ./install.sh --keymaps-only
    ```
  * Oder starte Kodi einmal neu.

---

## 5. Live-TV Sender puffern oder brechen ab
* Die Live-TV-Sender stammen aus den offiziellen und gespiegelten VAVOO-Netzwerken.
* Falls ein Sender puffert, schalte kurz auf einen anderen Kanal und wieder zurück, um eine frische Mirror-Verbindung aufzubauen.
