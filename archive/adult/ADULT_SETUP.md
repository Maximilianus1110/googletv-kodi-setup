# 🔒 Erwachsenenbereich (+18 / AdultHideout), PIN-Schutz & Sitzungs-Logik

> [!NOTE]
> Wichtige Abweichungen zwischen der alten Kurz-Doku und dem tatsächlichen Code (z. B. Long-Press-Auslösung nach `~1 Sek.` statt `5 Sek.`, das zweigeteilte Timeout von **`10.0s` für das Hauptmenü** vs. **`300.0s` für Untermenüs** sowie **294 aktive** von 306 Seiten) sind in [**`docs/ABWEICHUNGEN_ALT_VS_CODE.md`**](ABWEICHUNGEN_ALT_VS_CODE.md) dokumentiert.

---

## 🧭 Funktions-Schnellindex

| Funktion | Auslöser | Beteiligte Dateien & Funktionen | Verhalten im Überblick |
| :--- | :--- | :--- | :--- |
| **[1. Zugangswege & PIN-Launcher (`0000`)](#1-zugangswege--der-pin-launcher-open_adultpy)** | **Zurück-Taste gedrückt halten (`longpress`)** oder Menüpunkt *„🔒 Archiv (+18 PIN)“* | [`userdata/keymaps/secret_remote.xml`](../kodi/userdata/keymaps/secret_remote.xml)<br>[`skin.arctic.fuse.2/shortcuts/open_adult.py`](../kodi/addons/skin.arctic.fuse.2/shortcuts/open_adult.py) | Fragt über `xbmcgui.Dialog().numeric()` den PIN **`0000`** ab, setzt `adulthideout_auth_ts` in `Window(10000)` und öffnet `plugin://plugin.video.adulthideout/`. |
| **[2. Zweistufige RAM-Sitzungsprüfung (`10s` vs. `300s`)](#2-zweistufige-ram-sitzungssteuerung-in-defaultpy-10s-root-vs-300s-untermen)** | Jeder Verzeichnis- oder Videoaufruf in `plugin.video.adulthideout` | [`plugin.video.adulthideout/default.py`](../kodi/addons/plugin.video.adulthideout/default.py) → `handle_routing()` (Zeilen 1001–1029) | Hauptmenü (`is_root`): Token nur **`10.0` Sek.** gültig.<br>Untermenüs (`mode=...`): Gleitendes **`300.0` Sek. (5 Min.)** Inaktivitätsfenster; jeder Klick erneuert den Zeitstempel. |
| **[3. Aktive Quellen & Python-Fallback-Core](#3-quellkatalog-294-aktive-von-306-seiten--python-core-fallback)** | Navigation & Stream-Auflösung im Add-on | [`plugin.video.adulthideout/default.py`](../kodi/addons/plugin.video.adulthideout/default.py) (Zeilen 39–56)<br>[`service.adulthideout.core/service.py`](../kodi/addons/service.adulthideout.core/service.py) | 294 ab Werk sichtbare Webseiten (11 veraltete Seiten per `FACTORY_DISABLED_MIGRATION_WEBSITES` deaktiviert, 1 Opt-In). Nativer Python-Fallback-Modus ohne externe Binärabhängigkeit. |
| **[4. Zero-Leak Tarnung](#4-tarnung--zero-leak-architektur)** | Automatisch | [`plugin.video.adulthideout/default.py`](../kodi/addons/plugin.video.adulthideout/default.py) (Zeile 996)<br>[`tmdbhelper/.../monitor/player.py`](../kodi/addons/plugin.video.themoviedb.helper/resources/tmdbhelper/lib/monitor/player.py) | `cacheToDisc=False` auf Verzeichnissen, keine TMDb-IDs (daher kein Trakt-Scrobbling und kein Auftauchen in *„Weiterschauen“*). |

---

## 1. 🔑 Zugangswege & der PIN-Launcher (`open_adult.py`)

* **Standard-PIN:** **`0000`** (vier Nullen, fest hinterlegt in [`open_adult.py`](../kodi/addons/skin.arctic.fuse.2/shortcuts/open_adult.py) Zeile 9 und [`default.py`](../kodi/addons/plugin.video.adulthideout/default.py) Zeile 1021).

### Weg A: Globaler Fernbedienungs-Shortcut (Long-Press Back)
* In [`kodi/userdata/keymaps/secret_remote.xml`](../kodi/userdata/keymaps/secret_remote.xml) ist global (`<global>`) hinterlegt:
  ```xml
  <back mod="longpress">RunScript(special://skin/shortcuts/open_adult.py)</back>
  ```
* **Auslösung:** Halte die **Zurück-Taste (`Back`)** für **ca. 0,5 bis 1,5 Sekunden** gedrückt (Kodis Standard-Schwelle für `mod="longpress"`).

### Weg B: Über das Untermenü
* Navigiere in das Untermenü von **Add-ons & Live-TV** ([`skinvariables-shortcut-homemenu.json`](../kodi/userdata/addon_data/script.skinvariables/nodes/skin.arctic.fuse.2/skinvariables-shortcut-homemenu.json), Zeilen 141–145) und wähle **„🔒 Archiv (+18 PIN)“** (`RunScript(special://skin/shortcuts/open_adult.py)`).

### Technischer Ablauf in [`open_adult.py`](../kodi/addons/skin.arctic.fuse.2/shortcuts/open_adult.py)
```python
pin = dialog.numeric(0, "PIN eingeben (0000)")
if pin == "0000":
    home_win = xbmcgui.Window(10000)
    home_win.setProperty('adulthideout_auth_ts', str(time.time()))
    xbmc.executebuiltin("ActivateWindow(videos, plugin://plugin.video.adulthideout/, return)")
elif pin:
    dialog.notification("Sicherheit", "Falscher PIN-Code", xbmcgui.NOTIFICATION_ERROR, 3000)
```
* **Wichtig:** `open_adult.py` prüft ein eventuell noch bestehendes `adulthideout_auth_ts`-Property **nicht**, sondern zeigt bei jedem Aufruf über Long-Press oder über den Menüpunkt *„🔒 Archiv (+18 PIN)“* immer zuerst die PIN-Abfrage an.

---

## 2. ⏱️ Zweistufige RAM-Sitzungssteuerung in `default.py` (`10s` Root vs. `300s` Untermenü)

Zusätzlich zum Shortcut-Skript ist der PIN-Schutz direkt in den zentralen Router `handle_routing()` von [`kodi/addons/plugin.video.adulthideout/default.py`](../kodi/addons/plugin.video.adulthideout/default.py) (Zeilen 1001–1029) eingebaut. Selbst wenn jemand versucht, `AdultHideout` direkt über *Alle Video-Add-ons* zu öffnen, greift diese Sperre.

### Exakte Code-Logik (`default.py`, Zeilen 1002–1029)
```python
home_win = xbmcgui.Window(10000)
auth_ts = home_win.getProperty('adulthideout_auth_ts')
now = time.time()

raw_query = sys.argv[2] if len(sys.argv) > 2 else ''
is_root = (not raw_query or raw_query == '?' or 'mode=' not in raw_query)

is_valid = False
if auth_ts:
    try:
        allowed_window = 10.0 if is_root else 300.0
        if (now - float(auth_ts)) < allowed_window:
            is_valid = True
    except Exception:
        pass
```

### Was diese Logik konkret bewirkt:
1. **Stufe 1 – Hauptverzeichnis (`is_root == True`, kein `mode=` in der Plugin-URL): `10.0` Sekunden gültig**
   * Wenn `open_adult.py` nach erfolgreicher PIN-Eingabe `adulthideout_auth_ts` setzt und unmittelbar danach `ActivateWindow(videos, plugin://plugin.video.adulthideout/, return)` aufruft, liegt die Differenz `now - auth_ts` bei wenigen Millisekunden (`< 10.0s`) → Das Hauptverzeichnis öffnet sich ohne doppelte PIN-Abfrage.
   * **Aber:** Verlässt du das Add-on oder kehrst nach mehr als **10 Sekunden** auf die oberste Hauptebene (`is_root`) zurück, ist `now - auth_ts >= 10.0`. Das Hauptmenü verlangt dann sofort wieder die Eingabe von **`0000`**!
2. **Stufe 2 – Alle Untermenüs, Suchen, Kategorien & Videos (`is_root == False`, URL enthält `mode=...`): `300.0` Sekunden (5 Minuten) gültig**
   * Solange du dich innerhalb der Webseiten, Kategorien, Suchergebnisse oder Videolisten bewegst (`mode=...`), gilt das **300-Sekunden-Fenster (5 Minuten)**.
   * Bei jeder gültigen Aktion aktualisiert Zeile 1029 den Zeitstempel im RAM (`home_win.setProperty('adulthideout_auth_ts', str(now))`), sodass die 5 Minuten erst ab dem letzten Klick im Untermenü ablaufen.
3. **Verhalten bei Kodi-Neustart:**
   * Da `adulthideout_auth_ts` ausschließlich als flüchtiges Property in `xbmcgui.Window(10000)` (RAM) lebt, wird die Sitzung beim Beenden oder Neustarten von Kodi sofort gelöscht.

---

## 3. 🌐 Quellkatalog (294 aktive von 306 Seiten) & Python-Core-Fallback

### Website-Module & Filterung in [`default.py`](../kodi/addons/plugin.video.adulthideout/default.py)
* Im Verzeichnis `kodi/addons/plugin.video.adulthideout/resources/websites/` sowie in `website_catalog.json` befinden sich insgesamt **306 Website-Scraper**.
* Davon sind in `default.py` (Zeilen 44–56) **11 Seiten** über `FACTORY_DISABLED_MIGRATION_WEBSITES` (`czechvideo`, `hentaimama`, `hqporner`, `ogporn`, `pervclips`, `retropornarchives`, `saintporn`, `swingerpornfun`, `vintagepornfun`, `vintageworldp`, `wowxxx`) ab Werk ausgeblendet.
* **1 weitere Seite** (`crazyshit`, Zeile 39: `OPT_IN_WEBSITE_SETTINGS`) wird nur angezeigt, wenn in den Add-on-Einstellungen explizit `show_crazyshit = true` aktiviert wird.
* Standardmäßig stehen im Hauptmenü somit **294 aktive Quellen** (inkl. globaler Suche, Content-Filtern wie `general`, `hentai`, `jav`, `live` und eigenem DNS-Retry-Handler [`dns_retry.py`](../kodi/addons/plugin.video.adulthideout/resources/lib/dns_retry.py)) bereit.

### Gepatchter Python-Fallback in [`service.adulthideout.core/service.py`](../kodi/addons/service.adulthideout.core/service.py)
* Damit auf Android TV / Google TV (ARM/ARM64) keine binären Inkompatibilitäten auftreten, läuft `service.adulthideout.core` als leichtgewichtiger Standby-Service (`[AdultHideoutCore] Service standby (native Python fallback mode active)`), während [`thumb_proxy.py`](../kodi/addons/plugin.video.adulthideout/resources/lib/thumb_proxy.py) (`ensure_embedded_image_proxy()`) den lokalen Thumbnail- und Header-Proxy direkt in Python bereitstellt.

---

## 4. 🕵️ Tarnung & Zero-Leak-Architektur

* **Kein Disk-Caching der Ordnerlisten:** Am Ende des Verzeichnisaufbaus ruft [`default.py`](../kodi/addons/plugin.video.adulthideout/default.py) (Zeile 996) `xbmcplugin.endOfDirectory(ADDON_HANDLE, succeeded=True, cacheToDisc=False)` auf.
* **Kein Trakt-Scrobbling & keine Startseiten-Spuren:** Da `AdultHideout`-Streams weder eine `tmdb_id` noch den `MediaType` `'movie'`/`'episode'` setzen, bricht `PlayerMonitor.get_playingitem()` in [`player.py`](../kodi/addons/plugin.video.themoviedb.helper/resources/tmdbhelper/lib/monitor/player.py) (Zeile 446: `if self.dbtype not in ('movie', 'episode'): return`) sowie `PlayerScrobbler.is_scrobbling` ([`scrobbler.py`](../kodi/addons/plugin.video.themoviedb.helper/resources/tmdbhelper/lib/monitor/scrobbler.py), Zeile 55: `if not self.tmdb_type: return`) sofort ab. Es werden niemals Daten an Trakt oder an die *„Weiterschauen“*-Widgets der Startseite gesendet.
