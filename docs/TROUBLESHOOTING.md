# 🛠️ Fehlerbehebung, System-Interna & Wartung (Troubleshooting)

Diese Dokumentation erklärt die eingebauten Selbstheilungs-Mechanismen im Code sowie gezielte Lösungen für bekannte Android-TV-, Kodi-21- und Scraper-Probleme.

---

## 🧭 Schnellindex nach Fehlerbild

| Problem / Thema | Beteiligte Dateien & Mechanismen | Schnelle Lösung / Sprungziel |
| :--- | :--- | :--- |
| **[1. Stream startet nicht / Hoster gesperrt oder langsam](#1-stream-startet-nicht-ruckelt-oder-liefert-falsche-spracheton)** | `scraper.py` → `PlaybackWatcher`, `select_and_play()`<br>`streamHistory.py` → `stream_failures.json`, `stream_history.json`<br>`requestHandler.py` → Cloudflare DoH-Bypass | OSD-Button **`🔄` (Control `6009`)** drücken oder selben Titel erneut starten (automatische Stream-Rotation). |
| **[2. `Permission Denied` bei `./install.sh` (Android 11+ Sperre)](#2-permission-denied-beim-kopieren-von-add-ons-android-11-auto-update-lock)** | [`install.sh`](../install.sh) (Zeilen 109–118 & 203) | Durch Kodi-Auto-Updates mit `u0_a*`-Owner gesperrte Add-on-Ordner über Kodi deinstallieren; `install.sh` setzt danach `general.addonupdates = 1`. |
| **[3. Neue xStream-Seiten fehlen in den Scraper-Settings](#3-automatische-selbstheilung-des-scrapers-addontoolsrepair)** | [`xstreamscraper/.../addonTools.py`](../kodi/addons/script.module.xstreamscraper/resources/lib/addonTools.py) → `repair()` | Synchronisiert bei jedem Kodi-Start (`service.py`) per MD5-Hash die `pluginDB` von `plugin.video.xstream` mit `script.module.xstreamscraper`. |
| **[4. Unsichtbare Dialoge bei Pause / Puffer-Ruckler (Kodi 21)](#4-performance--kodi-21-tuning-advancedsettingsxml--guisettingsxml)** | [`userdata/advancedsettings.xml`](../kodi/userdata/advancedsettings.xml)<br>[`install.sh`](../install.sh) (Zeilen 193–224) | `smartredraw = false` verhindert unsichtbare Dialoge bei pausiertem Video; `install.sh` setzt in `guisettings.xml` 64 MB RAM-Cache (`filecache.memorysize = 64`) & 24p-Refresh-Sync. |
| **[5. Trakt-Widgets leer oder Tastenbelegung zurückgesetzt](#5-trakt-widgets-oder-tastenbelegung-aktualisieren)** | [`install.sh`](../install.sh) (`--keymaps-only`)<br>`plugin.video.themoviedb.helper` | `./install.sh --keymaps-only` bzw. Trakt-Sync in TMDb Helper anstoßen. |

---

## 1. 🔄 Stream startet nicht, ruckelt oder liefert falsche Sprache/Ton

### Was der Code bereits automatisch abfängt:
1. **Cloudflare DNS-over-HTTPS (DoH) Bypass ([`requestHandler.py`](../kodi/addons/plugin.video.xstream/resources/lib/handler/requestHandler.py), Zeilen 58 & 724–748):**
   Blockiert dein Internetanbieter (ISP) Streaming-Domains per DNS-Sperre (z. B. `serienstream` oder `aniworld`), löst `cRequestHandler.__doh_request()` die Domain automatisch über **`https://cloudflare-dns.com/dns-query`** (`application/dns-json`) auf (ausgenommen `api.themoviedb.org` und `image.tmdb.org`).
2. **10-Sekunden-Tiefentest & 5× Player-Failover ([`streamTest.py`](../kodi/addons/script.module.xstreamscraper/resources/lib/streamTest.py) & [`scraper.py`](../kodi/addons/script.module.xstreamscraper/resources/lib/scraper.py)):**
   * `streamTest.check()` prüft jeden Link für max. `10` Sekunden bis zum ersten echten HLS-Videosegment (`depth 0..3`).
   * Scheitert das Öffnen im Kodi-Player trotzdem, schließt `PlaybackWatcher` Kodis Fehlermeldung (`Dialog.Close(okdialog,true)`) und probiert automatisch bis zu **5 weitere Streams (`MAX_FAILOVERS = 5`)** durch.
3. **Automatische Stream-Rotation & 60-Minuten-Fehlersperre ([`streamHistory.py`](../kodi/addons/script.module.xstreamscraper/resources/lib/streamHistory.py)):**
   * **Stream hat schlechten Ton / Ruckler -> Einfach stoppen und nochmal anklicken:** Da `streamHistory.remember()` den zuletzt gespielten Stream in `userdata/addon_data/script.module.xstreamscraper/stream_history.json` einträgt und `fresh()` im Auto-Play bereits gespielte Streams überspringt, bekommst du beim erneuten Start desselben Titels automatisch einen **anderen Stream/Hoster**.
   * **Manueller Wechsel an exakt derselben Sekunde:** Drücke im laufenden Video **Steuerkreuz Oben (`▲`)** → **`🔄`-Button (Control `6009`)**. Dort siehst du alle Hoster mit TCP-Ping (`🟢 < 280ms`, `🟡 <= 650ms`, `🔴 > 650ms`) und kannst über Eintrag `0` (`⚡ Live-Speedtest`) die Top-5 vorab auf echte Auflösung (`1080p`/`720p`) testen.

### Wann man den Fehler-Cache zurücksetzen sollte
Da Timeouts einen Hoster in `stream_failures.json` für **60 Minuten (`FAILED_SECONDS = 3600`)** sperren, kann nach einem kurzen WLAN-Ausfall am Fernseher fast jeder Hoster als fehlerhaft markiert sein.
* **Lösung per ADB:**
  ```bash
  adb shell "rm -f /sdcard/Android/data/org.xbmc.kodi/files/.kodi/userdata/addon_data/script.module.xstreamscraper/stream_failures.json"
  ```

---

## 2. 🔒 `Permission Denied` beim Kopieren von Add-ons (Android 11+ Auto-Update-Lock)

### Technischer Hintergrund
Unter Android 11+ (Scoped Storage) gehören Dateien, die per `adb push` / `tar` über die ADB-Shell (`shell`-User) nach `/sdcard/Android/data/org.xbmc.kodi/files/.kodi/addons/` geschrieben werden, der Gruppe `sdcard_rw` / `ext_data_rw`.
Wenn Kodi jedoch ein Add-on (wie `plugin.video.themoviedb.helper`, `service.upnext` oder `script.skinvariables`) selbst über das offizielle Kodi-Repository aktualisiert, legt der Kodi-Prozess die neuen Dateien mit dem restriktiven App-Owner `u0_a...` und Berechtigung `700` an. Danach darf die ADB-Shell diese Dateien nicht mehr überschreiben!

### Wie [`install.sh`](../install.sh) das erkennt und verhindert:
1. **Vorab-Prüfung (Zeilen 109–118):** `install.sh` prüft vor dem Kopieren per `ls -ld`, ob `plugin.video.themoviedb.helper`, `service.upnext` oder `script.skinvariables` dem Owner `u0_a*` gehören, und gibt eine gezielte Warnung aus.
2. **Automatischer Update-Schutz in `guisettings.xml` (Zeile 203):** Bei jeder Installation setzt `install.sh` in Kodis `userdata/guisettings.xml` den Wert `<setting id="general.addonupdates">1</setting>` (*Nur benachrichtigen, nicht automatisch installieren*), damit Kodi die gepatchten Add-ons nicht überschreibt.
3. **Lösung, falls ein Ordner bereits gesperrt ist:** Deinstalliere das betroffene Add-on einmalig innerhalb der Kodi-Oberfläche (*Einstellungen → Add-ons → Meine Add-ons → Deinstallieren*) und führe direkt danach `./install.sh` aus.

---

## 3. 🔧 Automatische Selbstheilung des Scrapers (`addonTools.repair`)

Bei jedem Kodi-Start ([`kodi/addons/script.module.xstreamscraper/service.py`](../kodi/addons/script.module.xstreamscraper/service.py)) sowie bei jedem Aufruf von [`main.py`](../kodi/addons/script.module.xstreamscraper/main.py) läuft `addonTools.repair()` ([`addonTools.py`](../kodi/addons/script.module.xstreamscraper/resources/lib/addonTools.py), Zeilen 20–55):
* Vergleicht per **MD5-Hash** die Datei `userdata/addon_data/plugin.video.xstream/pluginDB` mit `userdata/addon_data/script.module.xstreamscraper/pluginDB`.
* Hat `plugin.video.xstream` beim Start neue Streaming-Seiten in seine `pluginDB` eingetragen, generiert `repair()` automatisch die `resources/settings.xml` des Scrapers neu (ignoriert dabei `vod_*`-Seiten).
* Beim allerersten Start (`firststart != "true"`) oder über *Add-ons → xStream Scraper → TMDB-HELPER einrichten* setzt `setup_tmdb_helper()` in `plugin.video.themoviedb.helper` automatisch:
  * `default_player_movies = "xstream.json play_movie"`
  * `default_player_episodes = "xstream.json play_episode"`

---

## 4. ⚡ Performance- & Kodi-21-Tuning (`advancedsettings.xml` & `guisettings.xml`)

### A. [`kodi/userdata/advancedsettings.xml`](../kodi/userdata/advancedsettings.xml)
| Tag | Wert | Warum dieser Wert im Code gesetzt ist |
| :--- | :--- | :--- |
| `<splash>` | `false` | Überspringt den Kodi-Startbildschirm für schnelleren Kaltstart. |
| `<algorithmdirtyregions>` | `3` | Rendert nur veränderte Bildschirmbereiche für flüssige 60fps-Navigation in Arctic Fuse 2. |
| `<smartredraw>` | **`false`** | **Wichtig:** Muss auf `false` stehen! Bei `true` rendert Kodi auf Android TV neu geöffnete Dialoge (wie den Stream-Wechsler `select_and_play` bei pausiertem Video) nicht neu, sodass das Auswahlfenster unsichtbar bleibt. |
| `<curlclienttimeout>` / `<curllowspeedtime>` | `10` | Bricht tote HTTP-Verbindungen von Kodis internem `curl`-Client nach 10 Sekunden ab (passend zu `streamTest.LIMIT = 10`). |
| `<dnslookupcache>` | `true` | Cacht aufgelöste Hoster-IPs im RAM. |

### B. Automatische Kodi-21-Optimierung in `guisettings.xml` ([`install.sh`](../install.sh), Zeilen 193–224)
Da Kodi 21 (Omega) die `<cache>`-Einstellungen aus `advancedsettings.xml` entfernt und nach `guisettings.xml` (`filecache.*`) verschoben hat, patcht `install.sh` die `guisettings.xml` auf dem Fernseher automatisch mit folgenden Werten:
* **`filecache.buffermode = 4`:** Puffert alle Netzwerk-Dateisysteme inkl. HTTP/HTTPS/HLS.
* **`filecache.memorysize = 64`:** Reserviert **64 MB RAM-Puffer** für ruckelfreies Streaming ohne den knappen Flash-Speicher von Google-TV-Boxen zu belasten.
* **`filecache.readfactor = 400`:** Füllt den Puffer mit 4× adaptiver Leserate vorab auf.
* **`videoplayer.adjustrefreshrate = 2`:** Passt die Bildwiederholrate des Fernsehers beim Start/Stop eines Videos automatisch an (`24p`/`50p`/`60p`).

---

## 5. 🔄 Trakt-Widgets oder Tastenbelegung aktualisieren

### Tastenbelegung nach manuellem Eingriff schnell wiederherstellen
Überträgt ausschließlich `player_controls.xml` und `secret_remote.xml` in wenigen Sekunden ohne kompletten Add-on-Transfer:
```bash
./install.sh --keymaps-only
```

### Aktuellen Stand vom Fernseher auf den PC sichern
Zieht `userdata/keymaps`, `userdata/addon_data` und `userdata/advancedsettings.xml` per ADB in einen Zeitstempel-Ordner unter `./backups/kodi_backup_YYYYMMDD_HHMMSS`:
```bash
./backup.sh
```

### Kodi per ADB sauber neu starten
```bash
adb shell "am force-stop org.xbmc.kodi; am start -n org.xbmc.kodi/.Main"
```
