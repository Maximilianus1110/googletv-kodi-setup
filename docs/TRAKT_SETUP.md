# 🎬 Trakt-Integration, Scrobbling & „Weiterschauen“-Mechanik

> [!NOTE]
> Abweichungen zur früheren Kurz-Dokumentation (z. B. die tatsächliche Gesehen-Schwelle von **80 %** statt 85 % im Code) sind in [**`docs/ABWEICHUNGEN_ALT_VS_CODE.md`**](ABWEICHUNGEN_ALT_VS_CODE.md) aufgeführt.

---

## 🧭 Funktions-Schnellindex

| Funktion | Beteiligte Dateien & Klassen | Verhalten im Überblick |
| :--- | :--- | :--- |
| **[1. Trakt-Autorisierung & Token-Sicherung](#1-trakt-konto-verbinden--automatische-token-bernahme-bei-updates)** | `plugin.video.themoviedb.helper/settings.xml`<br>`script.module.tmdbhelper.sync.trakt/settings.xml`<br>[`install.sh`](../install.sh) (Zeilen 97–191) | Einmalige OAuth-Kopplung über `trakt.tv/activate`. `install.sh` sichert bestehende Tokens vor jedem Update und spielt sie automatisch wieder ein. |
| **[2. TMDb-Metadaten-Injektion durch den Scraper](#2-metadaten-injektion-beim-abspielen-_listitem-in-scraperpy)** | [`xstreamscraper/.../scraper.py`](../kodi/addons/script.module.xstreamscraper/resources/lib/scraper.py) → `_search_and_play()`, `_listitem()`<br>[`tmdbhelper/.../monitor/player.py`](../kodi/addons/plugin.video.themoviedb.helper/resources/tmdbhelper/lib/monitor/player.py) → `PlayerItem` | Der Scraper injiziert `tmdb_id`, `tvshow.tmdb`, `imdb`, `season`, `episode` und `mediatype` direkt in Kodis `VideoInfoTag`, damit TMDb Helper den Stream erkennt. |
| **[3. Live-Scrobbling & 80-%-Gesehen-Schwelle](#3-live-scrobbling-zeitmessung--die-80--gesehen-schwelle)** | [`tmdbhelper/.../monitor/player.py`](../kodi/addons/plugin.video.themoviedb.helper/resources/tmdbhelper/lib/monitor/player.py) → `PlayerMonitor`<br>[`tmdbhelper/.../monitor/scrobbler.py`](../kodi/addons/plugin.video.themoviedb.helper/resources/tmdbhelper/lib/monitor/scrobbler.py) → `PlayerScrobbler` | Übermittelt Start, Pause und Stop an Trakt. Ab **80 % Fortschritt** (`>= 0.8`) wird die Folge/der Film als „Gesehen“ synchronisiert und die Widget-Oberfläche aktualisiert. |
| **[4. Personalisierte Trakt-Widgets auf der Startseite](#4-die-trakt-widgets-auf-der-startseite--in-den-men-hubs)** | [`skinvariables-shortcut-homemenu.json`](../kodi/userdata/addon_data/script.skinvariables/nodes/skin.arctic.fuse.2/skinvariables-shortcut-homemenu.json)<br>[`skinvariables-shortcut-sidemenu.json`](../kodi/userdata/addon_data/script.skinvariables/nodes/skin.arctic.fuse.2/skinvariables-shortcut-sidemenu.json) | 5 Trakt-gestützte Reihen auf der Startseite (`sync_inprogress`, `sync_nextepisodes`, `sync_watchlist`, `trakt_becauseyouwatched` für Filme & Serien). |

---

## 1. 🔑 Trakt-Konto verbinden & Automatische Token-Übernahme bei Updates

### Einmalige Einrichtung in Kodi
1. Falls noch nicht vorhanden, erstelle ein kostenloses Konto auf **[trakt.tv](https://trakt.tv)**.
2. Öffne in Kodi die Einstellungen von **TMDb Helper** (*Add-ons* → *Video-Add-ons* → *TMDb Helper* → *Einstellungen* → Reiter **Trakt**).
3. Wähle **„Trakt-Konto autorisieren…“**.
4. Gib den angezeigten Code auf **[trakt.tv/activate](https://trakt.tv/activate)** ein und bestätige.

### Wie [`install.sh`](../install.sh) deine Trakt-Sitzung bei Updates schützt (Zeilen 97–191)
Die OAuth-Zugangsdaten werden an zwei Stellen in `userdata/addon_data/` gespeichert:
1. `plugin.video.themoviedb.helper/settings.xml` (Tag `<setting id="trakt_token">...</setting>`)
2. `script.module.tmdbhelper.sync.trakt/settings.xml` (OAuth-Credentials des ausgelagerten Trakt-Sync-Moduls)

Wenn du `./install.sh` ausführst, liest das Skript **vor** dem Überschreiben der Konfigurationsdateien beide Tokens per `adb shell` / `adb pull` vom Fernseher aus und injiziert sie nach dem Entpacken des neuen Setups automatisch wieder in die Ziel-Dateien. Du musst dich nach einem Setup-Update also **nicht** erneut bei Trakt anmelden.

---

## 2. 🏷️ Metadaten-Injektion beim Abspielen (`_listitem` in `scraper.py`)

Da Streams von Hostern wie VOE, Filemoon oder VAVOO reine `.m3u8`- oder `.mp4`-URLs ohne eigene Metadaten sind, wüsste Kodi normalerweise nicht, welcher Film oder welche Serienfolge gerade läuft.

### Technischer Ablauf im Code
1. **Abruf der offiziellen TMDb-Metadaten (`_search_and_play` in [`scraper.py`](../kodi/addons/script.module.xstreamscraper/resources/lib/scraper.py), Zeilen 716–728):**
   Der Scraper ruft `get_details(_type, _id)` (`https://api.themoviedb.org/3/{tv|movie}/{id}?api_key=...&language=de`, 14 Tage lokal gecacht) ab und baut das Dictionary `media_meta`:
   ```python
   media_meta = {
       'type': _type,          # 'tv' oder 'movie'
       'tmdb_id': _id,         # offizielle TMDb-ID
       'season': season,       # Staffelnummer (int)
       'episode': episode,     # Episodennummer (int)
       'title': name,          # Deutscher Titel / Serienname
       'year': releaseDate[:4],
       'imdb': data.get('imdb_id')
   }
   ```
2. **Befüllen des `VideoInfoTag` (`_listitem`, Zeilen 795–840):**
   Vor dem Aufruf von `xbmcplugin.setResolvedUrl()` schreibt `_listitem()` alle Identifikatoren direkt in das `ListItem`:
   * `info_tag.setMediaType('episode' if is_tv else 'movie')`
   * `info_tag.setUniqueID(str(meta['tmdb_id']), 'tmdb')`
   * Bei Serien zusätzlich: `info_tag.setUniqueID(str(meta['tmdb_id']), 'tvshow.tmdb')`, `info_tag.setSeason(int(season))`, `info_tag.setEpisode(int(episode))`, `info_tag.setTvShowTitle(meta['title'])`
   * `info_tag.setIMDBNumber(str(meta['imdb']))` (sofern vorhanden)
3. **Auslesen durch TMDb Helper (`PlayerItem.meta` in [`player.py`](../kodi/addons/plugin.video.themoviedb.helper/resources/tmdbhelper/lib/monitor/player.py), Zeilen 44–65):**
   Sobald das Video startet (`onAVStarted`), liest `PlayerItem` genau diese `UniqueID.tvshow.tmdb` / `UniqueID.tmdb`, `Season`, `Episode` und `MediaType` aus `getVideoInfoTag()` aus, setzt die Home-Window-Properties `TMDbHelper.Player.playing.tmdb_id`, `playing.season`, `playing.episode` und initialisiert den Trakt-Scrobbler (`PlayerScrobblerFactory`).

---

## 3. ⏱️ Live-Scrobbling, Zeitmessung & die 80-%-Gesehen-Schwelle

### Technischer Ablauf im Code ([`player.py`](../kodi/addons/plugin.video.themoviedb.helper/resources/tmdbhelper/lib/monitor/player.py) & [`scrobbler.py`](../kodi/addons/plugin.video.themoviedb.helper/resources/tmdbhelper/lib/monitor/scrobbler.py))

1. **Start nach Resume-Seek (`get_playingitem` in [`player.py`](../kodi/addons/plugin.video.themoviedb.helper/resources/tmdbhelper/lib/monitor/player.py), Zeilen 439 & 470–472):**
   * `self.scrobbler = PlayerScrobblerFactory(total_time=self.getTotalTime())` erzeugt für jeden aktivierten Sync-Provider (Trakt & Kodi-Library) eine `PlayerProviderScrobbler`-Instanz.
   * `self.wait_for_seek(10)` wartet nach Videostart `10` Sekunden (und solange `Player.Seeking` aktiv ist), damit ein eventueller Resume-Sprung abgeschlossen ist, bevor `self.scrobbler_start()` den Startpunkt an Trakt meldet (`scrobble('start')`).
2. **Interne Stoppuhr & Synchronisationspunkte (`PlayerScrobbler` in [`scrobbler.py`](../kodi/addons/plugin.video.themoviedb.helper/resources/tmdbhelper/lib/monitor/scrobbler.py), Zeilen 69–165):**
   * `PlayerScrobbler` führt über `self.start_time = set_timestamp(-value)` eine eigene fortlaufende Zeitmessung und gleicht diese über `update_time()` bei jedem `onPlayBackPaused`, `onPlayBackResumed`, `onPlayBackSeek`, im Vollbild-Poller (`on_fullscreen` → `scrobbler_sync`) sowie bei `onPlayBackStopped`/`onPlayBackEnded` mit `self.getTime()` des Players ab.
   * **Schutz bei vorzeitigem Episodenwechsel (Abspann-Autoplay):** Wechselt Kodi nach dem 15-Sekunden-Abspann-Countdown direkt auf Folge `N+1`, erkennt `PlayerMonitor.scrobbler_update()` (`player.py` Zeile 287: `if self.previous_item and self.current_item and self.current_item != self.previous_item: return`), dass der Player bereits die neue Datei geladen hat, und überschreibt den Fortschritt der beendeten Folge **nicht** mit `0.0s` der neuen Folge.
3. **Ab wann gilt ein Film / eine Folge als „Gesehen“ vs. „Angefangenes Video“?**
   * **Unter 80 % Fortschritt (`progress < 80`):**
     Wird das Video pausiert oder gestoppt, sendet Trakt den exakten prozentualen Fortschritt. Der Titel erscheint mit Fortschrittsbalken in der Reihe **„▶️ Weiterschauen“ (`sync_inprogress`)** und kann beim nächsten Klick nahtlos fortgesetzt werden.
   * **Ab exakt 80 % Fortschritt (`progress >= 80` / `getTime() / getTotalTime() >= 0.8`):**
     * Bereits während das Video noch im Vollbild läuft, prüft `PlayerMonitor.scrobbler_sync()` (`player.py` Zeile 277) regelmäßig `if (self.getTime() / self.getTotalTime()) < 0.8: return`.
     * Sobald **80 %** erreicht sind (oder das Video bei `>= 80 %` gestoppt wird), ruft `PlayerScrobbler.sync()` / `stop()` (`scrobbler.py` Zeilen 149 & 164) `self.scrobble('stop')` auf und triggert `self.playback_refresh.refresh(sync=self.progress >= 80)`.
     * Dadurch wird die Episode bei Trakt sofort als **Gesehen** verbucht, die lokalen Widget-Caches werden invalidiert und in **„📺 Nächste Episoden“ (`sync_nextepisodes`)** rückt automatisch Folge `N+1` nach.
4. **Zusätzlicher Schutz durch `service.upnext` (`markWatchedEarly = true`):**
   * Beim Übergang über das UpNext-Popup sendet [`playbackmanager.py`](../kodi/addons/service.upnext/resources/lib/playbackmanager.py) (Zeile 150) zusätzlich das interne Signal `NEXTUPWATCHEDSIGNAL`.
   * Für lokale Kodi-Bibliothekseinträge (die standardmäßig erst ab 90 % `playcountminimumpercent` als gesehen zählen) prüft `check_previous_watched()` (`playbackmanager.py` Zeilen 313–344) **10 Sekunden (`WATCHED_CHECK_DELAY = 10`)** nach dem Start der neuen Folge, ob Kodi den `playcount` erhöht hat, und setzt ihn andernfalls per JSON-RPC (`VideoLibrary.SetEpisodeDetails`) nach.

---

## 4. 📺 Die Trakt-Widgets auf der Startseite & in den Menü-Hubs

In [`skinvariables-shortcut-homemenu.json`](../kodi/userdata/addon_data/script.skinvariables/nodes/skin.arctic.fuse.2/skinvariables-shortcut-homemenu.json) und [`skinvariables-shortcut-sidemenu.json`](../kodi/userdata/addon_data/script.skinvariables/nodes/skin.arctic.fuse.2/skinvariables-shortcut-sidemenu.json) sind folgende Trakt-Pfade vorkonfiguriert:

| Widget-Titel | Bereich | Interner Plugin-Pfad | Darstellung | Funktion |
| :--- | :--- | :--- | :--- | :--- |
| **▶️ Weiterschauen** | `Entdecken` (Startseite) | `plugin://plugin.video.themoviedb.helper/?info=sync_inprogress&widget=true` | `Landscape` | Angefangene Filme & Serienfolgen (`< 80 %`) mit Fortschrittsbalken und Resume-Punkt. |
| **📺 Nächste Episoden** | `Entdecken` (Startseite) | `plugin://plugin.video.themoviedb.helper/?info=sync_nextepisodes&tmdb_type=tv&widget=true` | `Landscape` | Die jeweils nächste ungesehene Episode (`N+1`) aller von dir begonnenen Serien. |
| **📌 Meine Trakt Watchlist** | `Entdecken`, `Filme`, `Serien` | `plugin://plugin.video.themoviedb.helper/?info=sync_watchlist&tmdb_type={both\|movie\|tv}&widget=true` | `Poster` | Deine persönliche Merkliste aus Trakt (auf der Startseite kombiniert `both`, in den Hubs getrennt nach `movie` bzw. `tv`). |
| **💡 Filme für dich (Weil du geschaut hast)** | `Entdecken`, `Filme` | `plugin://plugin.video.themoviedb.helper/?info=trakt_becauseyouwatched&tmdb_type=movie&widget=true` | `Poster` | Dynamische Empfehlungen basierend auf deinen zuletzt auf Trakt gesehenen Filmen. |
| **🎯 Serien für dich (Weil du geschaut hast)** | `Entdecken`, `Serien` | `plugin://plugin.video.themoviedb.helper/?info=trakt_becauseyouwatched&tmdb_type=tv&widget=true` | `Poster` | Dynamische Empfehlungen basierend auf deinen zuletzt auf Trakt gesehenen Serien. |
